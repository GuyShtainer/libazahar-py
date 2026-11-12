// SPDX-License-Identifier: GPL-3.0-or-later
#include "scene3d.h"

#include <3ds.h>
#include <assert.h>
#include <citro2d.h>
#include <citro3d.h>
#include <math.h>
#include <string.h>

#include "draw2d.h"
#include "font.h"
#include "vshader_shbin.h"

typedef struct {
    float x, y, z;
} vertex;

enum { LAZ_TRI_VERTS = 3, LAZ_VBO_COUNT = 2 };

static C3D_RenderTarget *g_top;
static C3D_RenderTarget *g_bottom;
static DVLB_s *g_dvlb;
static shaderProgram_s g_program;
static int g_uloc_projection;
static C3D_Mtx g_projection;
static vertex *g_vbo;  // two triangles in linear memory, used on alternate frames
static int g_c3d_up, g_c2d_up, g_shader_up;

static u32 rgb32(uint32_t rgb)
{
    return C2D_Color32((u8)(rgb >> 16), (u8)(rgb >> 8), (u8)rgb, 0xFF);
}

static int shader_init(void)
{
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
    assert(g_uloc_projection >= 0);
    if (g_uloc_projection < 0) {
        return -1;
    }
    Mtx_OrthoTilt(&g_projection, 0.0, 400.0, 0.0, 240.0, 0.0, 1.0, true);
    g_vbo = linearAlloc(sizeof(vertex) * LAZ_TRI_VERTS * LAZ_VBO_COUNT);
    return g_vbo == NULL ? -1 : 0;
}

int scene3d_init(void)
{
    if (!C3D_Init(C3D_DEFAULT_CMDBUF_SIZE)) {
        return -1;
    }
    g_c3d_up = 1;
    if (!C2D_Init(C2D_DEFAULT_MAX_OBJECTS)) {
        return -1;
    }
    g_c2d_up = 1;
    g_top = C2D_CreateScreenTarget(GFX_TOP, GFX_LEFT);
    g_bottom = C2D_CreateScreenTarget(GFX_BOTTOM, GFX_LEFT);
    if (g_top == NULL || g_bottom == NULL) {
        return -1;
    }
    return shader_init();
}

void scene3d_begin(void)
{
    // SYNCDRAW without NONBLOCK blocks until the frame can start, so it always returns true
    const bool started = C3D_FrameBegin(C3D_FRAME_SYNCDRAW);
    assert(started);
    (void)started;
}

uint32_t scene3d_vblank(void)
{
    return (uint32_t)C3D_FrameCounter(0);
}

void scene3d_end(void)
{
    C3D_FrameEnd(0);
}

// The flat-coloured triangle: bind our own state each frame, because citro2d rebinds its own.
static void draw_triangle(uint32_t frame)
{
    assert(g_vbo != NULL && g_uloc_projection >= 0);
    vertex *tri = g_vbo + (frame % LAZ_VBO_COUNT) * LAZ_TRI_VERTS;
    const float angle = (float)(frame % 3600u) * 0.05f;
    for (int i = 0; i < LAZ_TRI_VERTS; i++) {
        const float a = angle + (float)i * 2.0943951f;
        tri[i].x = 200.0f + 70.0f * cosf(a);
        tri[i].y = 120.0f + 70.0f * sinf(a);
        tri[i].z = 0.5f;
    }
    C3D_BindProgram(&g_program);
    C3D_AttrInfo *attr = C3D_GetAttrInfo();
    AttrInfo_Init(attr);
    AttrInfo_AddLoader(attr, 0, GPU_FLOAT, 3);
    AttrInfo_AddFixed(attr, 1);
    C3D_FixedAttribSet(1, 1.0f, 0.5f, 0.0f, 1.0f);
    C3D_BufInfo *buf = C3D_GetBufInfo();
    BufInfo_Init(buf);
    BufInfo_Add(buf, tri, sizeof(vertex), 1, 0x0);
    C3D_TexEnv *env = C3D_GetTexEnv(0);
    C3D_TexEnvInit(env);
    C3D_TexEnvSrc(env, C3D_Both, GPU_PRIMARY_COLOR, 0, 0);
    C3D_TexEnvFunc(env, C3D_Both, GPU_REPLACE);
    C3D_DepthTest(false, GPU_ALWAYS, GPU_WRITE_COLOR);
    C3D_CullFace(GPU_CULL_NONE);
    C3D_FVUnifMtx4x4(GPU_VERTEX_SHADER, g_uloc_projection, &g_projection);
    C3D_DrawArrays(GPU_TRIANGLES, 0, LAZ_TRI_VERTS);
}

static void draw_markers_c2d(int top)
{
    const laz_marker *m = draw_markers(top);
    for (int i = 0; i < LAZ_MARKER_COUNT; i++) {
        C2D_DrawRectSolid((float)m[i].x, (float)m[i].y, 0.0f, (float)LAZ_MARKER_SIZE, (float)LAZ_MARKER_SIZE,
                          rgb32(m[i].rgb));
    }
}

static void draw_counter_c2d(uint32_t value)
{
    const u32 white = rgb32(0xFFFFFFu);
    for (int d = LAZ_COUNTER_DIGITS - 1; d >= 0; d--) {
        const int digit = (int)(value % 10u);
        value /= 10u;
        for (int row = 0; row < LAZ_GLYPH_H; row++) {
            for (int col = 0; col < LAZ_GLYPH_W; col++) {
                if (font_pixel(digit, col, row)) {
                    C2D_DrawRectSolid((float)(LAZ_COUNTER_X + d * LAZ_COUNTER_STRIDE + col),
                                      (float)(LAZ_COUNTER_Y + row), 0.0f, 1.0f, 1.0f, white);
                }
            }
        }
    }
}

void scene3d_draw(uint32_t frame)
{
    assert(g_top != NULL && g_bottom != NULL);
    const u32 bg = rgb32(LAZ_BG_RGB);
    C2D_TargetClear(g_top, bg);
    C2D_TargetClear(g_bottom, bg);
    C3D_FrameDrawOn(g_top);
    draw_triangle(frame);
    C2D_Prepare();
    C2D_SceneBegin(g_top);
    draw_markers_c2d(1);
    draw_counter_c2d(frame);
    C2D_SceneBegin(g_bottom);
    draw_markers_c2d(0);
    C2D_Flush();
}

void scene3d_exit(void)
{
    if (g_vbo != NULL) {
        linearFree(g_vbo);
        g_vbo = NULL;
    }
    if (g_shader_up) {
        shaderProgramFree(&g_program);
        DVLB_Free(g_dvlb);
        g_shader_up = 0;
    }
    if (g_c2d_up) {
        C2D_Fini();
        g_c2d_up = 0;
    }
    if (g_c3d_up) {
        C3D_Fini();
        g_c3d_up = 0;
    }
}
