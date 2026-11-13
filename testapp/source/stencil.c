// SPDX-License-Identifier: GPL-3.0-or-later
#include "stencil.h"

#include <3ds.h>
#include <assert.h>
#include <citro3d.h>
#include <stdio.h>
#include <string.h>

#include "sdlog.h"
#include "vshader_shbin.h"

enum {
    LAZ_ST_W = 128,
    LAZ_ST_H = 128,
    LAZ_ST_QX0 = 10,   // the quad: 100 x 80 logical pixels
    LAZ_ST_QY0 = 20,
    LAZ_ST_QW = 100,
    LAZ_ST_QH = 80,
    LAZ_ST_WORDS = LAZ_ST_W * LAZ_ST_H,
    LAZ_ST_VERTS = 6,
    LAZ_ST_DEPTH_QUAD = 0x4001FF,
    LAZ_ST_DEPTH_CLEAR = 0xFFFFFE,
    LAZ_ST_LINE = 256,
};

typedef struct {
    float x, y, z;
} vertex;

static C3D_RenderTarget *g_target;
static DVLB_s *g_dvlb;
static shaderProgram_s g_program;
static int g_uloc_projection;
static C3D_Mtx g_projection;
static vertex *g_vbo;
static u32 *g_dst;
static int g_c3d_up, g_shader_up;

static int init(void)
{
    if (!C3D_Init(C3D_DEFAULT_CMDBUF_SIZE)) {
        return -1;
    }
    g_c3d_up = 1;
    g_dvlb = DVLB_ParseFile((u32 *)vshader_shbin, vshader_shbin_size);
    if (g_dvlb == NULL) {
        return -1;
    }
    shaderProgramInit(&g_program);
    if (R_FAILED(shaderProgramSetVsh(&g_program, &g_dvlb->DVLE[0]))) {
        return -1;
    }
    g_shader_up = 1;
    g_uloc_projection = shaderInstanceGetUniformLocation(g_program.vertexShader, "projection");
    if (g_uloc_projection < 0) {
        return -1;
    }
    Mtx_Identity(&g_projection);
    g_vbo = linearAlloc(sizeof(vertex) * LAZ_ST_VERTS * 2);
    g_dst = linearAlloc(sizeof(u32) * LAZ_ST_WORDS);
    if (g_vbo == NULL || g_dst == NULL) {
        return -1;
    }
    g_target = C3D_RenderTargetCreate(LAZ_ST_W, LAZ_ST_H, GPU_RB_RGBA8, GPU_RB_DEPTH24_STENCIL8);
    return g_target == NULL ? -1 : 0;
}

// Two triangles covering the pixel rect (px0,py0)-(px1,py1) of the 128 x 128 viewport at clip depth z.
static vertex *fill_quad(vertex *v, float px0, float py0, float px1, float py1, float z)
{
    const float x0 = px0 / 64.0f - 1.0f, x1 = px1 / 64.0f - 1.0f;
    const float y0 = 1.0f - py0 / 64.0f, y1 = 1.0f - py1 / 64.0f;
    const vertex q[LAZ_ST_VERTS] = {{x0, y0, z}, {x1, y0, z}, {x1, y1, z}, {x0, y0, z}, {x1, y1, z}, {x0, y1, z}};
    memcpy(v, q, sizeof(q));
    return v;
}

// Shared draw state; `stencil_ops` 0 = REPLACE 0x80 on an ALWAYS test, 1 = EQUAL 0 test with INCR, 2 = stencil off.
static void draw_verts(vertex *v, int stencil_ops)
{
    C3D_BindProgram(&g_program);
    C3D_AttrInfo *attr = C3D_GetAttrInfo();
    AttrInfo_Init(attr);
    AttrInfo_AddLoader(attr, 0, GPU_FLOAT, 3);
    AttrInfo_AddFixed(attr, 1);
    C3D_FixedAttribSet(1, 1.0f, 0.5f, 0.0f, 1.0f);
    C3D_BufInfo *buf = C3D_GetBufInfo();
    BufInfo_Init(buf);
    BufInfo_Add(buf, v, sizeof(vertex), 1, 0x0);
    C3D_TexEnv *env = C3D_GetTexEnv(0);
    C3D_TexEnvInit(env);
    C3D_TexEnvSrc(env, C3D_Both, GPU_PRIMARY_COLOR, 0, 0);
    C3D_TexEnvFunc(env, C3D_Both, GPU_REPLACE);
    C3D_CullFace(GPU_CULL_NONE);
    C3D_DepthTest(true, GPU_ALWAYS, GPU_WRITE_ALL);
    if (stencil_ops == 0) {
        C3D_StencilTest(true, GPU_ALWAYS, 0x80, 0xFF, 0xFF);
        C3D_StencilOp(GPU_STENCIL_KEEP, GPU_STENCIL_KEEP, GPU_STENCIL_REPLACE);
    } else if (stencil_ops == 1) {
        C3D_StencilTest(true, GPU_EQUAL, 0x00, 0xFF, 0xFF);
        C3D_StencilOp(GPU_STENCIL_KEEP, GPU_STENCIL_KEEP, GPU_STENCIL_INCR);
    } else {
        C3D_StencilTest(false, GPU_ALWAYS, 0x00, 0xFF, 0xFF);
    }
    C3D_FVUnifMtx4x4(GPU_VERTEX_SHADER, g_uloc_projection, &g_projection);
    C3D_DrawArrays(GPU_TRIANGLES, 0, LAZ_ST_VERTS);
}

// Variant b's dummy pass: a small triangle pair drawn into the target with no clear, so it is a framebuffer already.
static void dummy_draw(void)
{
    C3D_FrameBegin(C3D_FRAME_SYNCDRAW);
    C3D_FrameDrawOn(g_target);
    draw_verts(fill_quad(g_vbo + LAZ_ST_VERTS, 0.0f, 0.0f, 16.0f, 16.0f, -0.5f), 2);
    C3D_FrameEnd(0);
    C3D_FrameSync();
}

// z in clip space for a 24-bit depth code (the default depth map is scale -1, offset 0)
static float clip_z(uint32_t code)
{
    return -(float)code / 16777215.0f;
}

// 32-bit clear to depth fffffe / stencil 00, one quad, GX TextureCopy of the depth buffer, wait, invalidate.
static void fill_draw_copy(int stencil_ops)
{
    const u32 size = (u32)(LAZ_ST_WORDS * sizeof(u32));
    C3D_FrameBegin(C3D_FRAME_SYNCDRAW);
    C3D_RenderTargetClear(g_target, C3D_CLEAR_ALL, 0, LAZ_ST_DEPTH_CLEAR);
    C3D_FrameDrawOn(g_target);
    draw_verts(fill_quad(g_vbo, (float)LAZ_ST_QX0, (float)LAZ_ST_QY0, (float)(LAZ_ST_QX0 + LAZ_ST_QW),
                         (float)(LAZ_ST_QY0 + LAZ_ST_QH), clip_z(LAZ_ST_DEPTH_QUAD)),
               stencil_ops);
    C3D_FrameEnd(0);
    C3D_FrameSync();
    memset(g_dst, 0xEE, size);
    (void)GSPGPU_FlushDataCache(g_dst, size);
    (void)GX_TextureCopy((u32 *)g_target->frameBuf.depthBuf, 0, g_dst, 0, size, 8);
    gspWaitForPPF();
    (void)GSPGPU_InvalidateDataCache(g_dst, size);
}

// word index of pixel (x, y) in 8 x 8 tiles with Morton order inside the tile (x bits on the even positions)
static uint32_t tiled_index(uint32_t x, uint32_t y)
{
    uint32_t m = 0;
    for (uint32_t b = 0; b < 3; b++) {
        m |= ((x >> b) & 1u) << (2u * b);
        m |= ((y >> b) & 1u) << (2u * b + 1u);
    }
    return ((y >> 3) * (LAZ_ST_W / 8u) + (x >> 3)) * 64u + m;
}

static void report(char label, int stencil_ops)
{
    const uint32_t want = stencil_ops == 1 ? 0x01u : 0x80u;
    uint32_t n_want = 0, n00 = 0, nff = 0, n_other = 0, dq = 0, dbad = 0;
    uint32_t x0 = 0xFFFFu, y0 = 0xFFFFu, x1 = 0, y1 = 0;
    char line[LAZ_ST_LINE];
    for (uint32_t y = 0; y < LAZ_ST_H; y++) {
        for (uint32_t x = 0; x < LAZ_ST_W; x++) {
            const u32 w = g_dst[tiled_index(x, y)];
            const uint32_t s = w >> 24, d = w & 0xFFFFFFu;
            if (s == want) {
                n_want++;
                x0 = x < x0 ? x : x0;
                y0 = y < y0 ? y : y0;
                x1 = x > x1 ? x : x1;
                y1 = y > y1 ? y : y1;
            } else if (s == 0x00u) {
                n00++;
            } else if (s == 0xFFu) {
                nff++;
            } else {
                n_other++;
            }
            if (d == LAZ_ST_DEPTH_QUAD) {
                dq++;
            } else if (d != LAZ_ST_DEPTH_CLEAR) {
                dbad++;
            }
        }
    }
    if (n_want == 0) {
        x0 = y0 = x1 = y1 = 0;
    }
    const int len = snprintf(line, sizeof(line), "stencil v=%c n%02x=%u n00=%u nff=%u nother=%u bbox=%u,%u,%u,%u dq=%u dbad=%u\n",
                             label, (unsigned)want, (unsigned)n_want, (unsigned)n00, (unsigned)nff, (unsigned)n_other,
                             (unsigned)x0, (unsigned)y0, (unsigned)x1, (unsigned)y1, (unsigned)dq, (unsigned)dbad);
    if (len > 0 && len < (int)sizeof(line)) {
        (void)sdlog_line(line, len);  // a failed log write is seen as a missing line by the checker
    }
}

int stencil_run(uint32_t mode)
{
    assert(mode >= 1 && mode <= 4);
    const int ops = mode >= 3 ? 1 : 0;
    const int variant_b = (mode == 2 || mode == 4);
    if (init() != 0) {
        (void)sdlog_line("stencil init failed\n", 20);
        return -1;
    }
    if (variant_b) {
        dummy_draw();
    }
    fill_draw_copy(ops);
    report(variant_b ? 'b' : 'a', ops);
    if (!variant_b) {
        fill_draw_copy(ops);
        report('d', ops);
    }
    return 0;
}

void stencil_idle_frame(void)
{
    if (g_c3d_up) {
        C3D_FrameBegin(C3D_FRAME_SYNCDRAW);
        C3D_FrameEnd(0);
    }
}

void stencil_exit(void)
{
    if (g_vbo != NULL) {
        linearFree(g_vbo);
        g_vbo = NULL;
    }
    if (g_dst != NULL) {
        linearFree(g_dst);
        g_dst = NULL;
    }
    if (g_shader_up) {
        shaderProgramFree(&g_program);
        DVLB_Free(g_dvlb);
        g_shader_up = 0;
    }
    if (g_c3d_up) {
        C3D_Fini();
        g_c3d_up = 0;
    }
}
