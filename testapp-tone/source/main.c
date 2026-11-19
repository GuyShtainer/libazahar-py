// SPDX-License-Identifier: GPL-3.0-or-later
// Tone test app: a stereo sine through libctru ndsp, started at frame 60: 440 Hz at amplitude 12000 on the left,
// 660 Hz at amplitude 6000 on the right, so a swapped or duplicated channel is visible. Logs once a second to
// sdmc:/tone/log.txt. Never exits on its own: the host stops it by frame count.
#include <3ds.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>

enum {
    START_FRAME = 60,
    RATE = 32728,
    BUF_SAMPLES = 4096,      // stereo frames per wave buffer (~125 ms)
    NBUF = 4,
};

static ndspWaveBuf g_wb[NBUF];
static s16 *g_pcm;
static double g_phase_l;
static double g_phase_r;
static unsigned g_queued;
static unsigned g_done;

static void fill(int i)
{
    s16 *p = g_pcm + (size_t)i * BUF_SAMPLES * 2;
    const double step_l = 2.0 * M_PI * 440.0 / (double)RATE;
    const double step_r = 2.0 * M_PI * 660.0 / (double)RATE;
    for (int n = 0; n < BUF_SAMPLES; n++) {
        p[2 * n] = (s16)(sin(g_phase_l) * 12000.0);
        p[2 * n + 1] = (s16)(sin(g_phase_r) * 6000.0);
        g_phase_l += step_l;
        g_phase_r += step_r;
        if (g_phase_l > 2.0 * M_PI) {
            g_phase_l -= 2.0 * M_PI;
        }
        if (g_phase_r > 2.0 * M_PI) {
            g_phase_r -= 2.0 * M_PI;
        }
    }
    DSP_FlushDataCache(p, BUF_SAMPLES * 2 * sizeof(s16));
}

static void queue(int i)
{
    fill(i);
    g_wb[i].data_vaddr = g_pcm + (size_t)i * BUF_SAMPLES * 2;
    g_wb[i].nsamples = BUF_SAMPLES;
    g_wb[i].looping = false;
    g_wb[i].status = NDSP_WBUF_FREE;
    ndspChnWaveBufAdd(0, &g_wb[i]);
    g_queued++;
}

static void logline(unsigned frame, int inited, Result rc)
{
    FILE *f = fopen("sdmc:/tone/log.txt", "a");
    if (f == NULL) {
        return;
    }
    fprintf(f, "frame=%u ndsp_started=%d ndspInit_rc=0x%08lX ok=%d queued=%u done=%u\n", frame, inited,
            (unsigned long)rc, rc == 0, g_queued, g_done);
    fclose(f);
}

int main(void)
{
    unsigned frame = 0;
    int inited = 0;
    Result rc = 0xFFFFFFFFu;     // not tried yet

    gfxInitDefault();
    mkdir("sdmc:/tone", 0777);
    g_pcm = linearAlloc((size_t)NBUF * BUF_SAMPLES * 2 * sizeof(s16));

    while (aptMainLoop()) {
        if (frame == START_FRAME) {
            rc = ndspInit();
            if (R_SUCCEEDED(rc) && g_pcm != NULL) {
                float mix[12];
                memset(mix, 0, sizeof mix);
                mix[0] = 1.0f;
                mix[1] = 1.0f;
                ndspSetOutputMode(NDSP_OUTPUT_STEREO);
                ndspChnReset(0);
                ndspChnSetInterp(0, NDSP_INTERP_LINEAR);
                ndspChnSetRate(0, (float)RATE);
                ndspChnSetFormat(0, NDSP_FORMAT_STEREO_PCM16);
                ndspChnSetMix(0, mix);
                memset(g_wb, 0, sizeof g_wb);
                for (int i = 0; i < NBUF; i++) {
                    queue(i);
                }
                inited = 1;
            }
        }
        if (inited) {
            for (int i = 0; i < NBUF; i++) {
                if (g_wb[i].status == NDSP_WBUF_DONE) {
                    g_done++;
                    queue(i);
                }
            }
        }
        if (frame % 60 == 0) {
            logline(frame, inited, rc);
        }
        frame++;
        gspWaitForVBlank();
        gfxSwapBuffers();
    }
    return 0;
}
