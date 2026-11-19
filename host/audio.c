/* audio.c: opt-in capture of the core's audio (ABI 5). Off by default: the callbacks then only count nothing and keep
 * nothing. Armed with azh_audio_capture(path), the samples go to that file as raw interleaved int16 stereo (host byte
 * order, little endian on every supported machine) and azh_audio_info reports how many stereo frames were written. */
#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "azh_internal.h"

#if defined(__BYTE_ORDER__) && defined(__ORDER_LITTLE_ENDIAN__) && __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "audio.c writes int16 samples in host order and the file format is little endian"
#endif

#define AUDIO_BUF_BYTES 65536u

static FILE *cap_file;              /* NULL: capture is off */
static char cap_buf[AUDIO_BUF_BYTES];
static int64_t cap_frames;          /* stereo frames written since the capture was armed (kept after it is closed) */
static int cap_failed;              /* a write failed: azh_audio_info reports AZH_E_IO */

/* the core's callbacks run inside retro_run, on the run thread (asserted by the callers in frame.c), so no lock:
 * arming and reading happen between runs */
void azh__audio_push(const int16_t *lr, size_t frames)
{
    assert(frames < ((size_t)1 << 40));
    assert(azh__in_run_thread() != 0);
    if (cap_file == NULL || lr == NULL || frames == 0u) {
        return;
    }
    if (fwrite(lr, 4u, frames, cap_file) != frames) {
        cap_failed = 1;
        return;
    }
    cap_frames += (int64_t)frames;
}

void azh__audio_close(void)
{
    assert(cap_frames >= 0);
    if (cap_file != NULL) {
        if (fclose(cap_file) != 0) {
            cap_failed = 1;
        }
        cap_file = NULL;
    }
}

int azh_audio_capture(const char *path)
{
    assert(azh_g.phase >= AZH_PH_NONE && azh_g.phase <= AZH_PH_DEAD);
    assert(cap_frames >= 0);
    if (path == NULL || *path == '\0') {
        if (azh_g.phase == AZH_PH_NONE) {
            return azh_fail(AZH_E_ORDER, "azh_audio_capture: needs azh_open first");
        }
        azh__audio_close();         /* stopping works in every phase after open, a failed first frame included */
        return cap_failed != 0 ? azh_fail(AZH_E_IO, "the audio file could not be written") : AZH_OK;
    }
    if (strlen(path) >= AZH_PATH_MAX) {
        return azh_fail(AZH_E_ARG, "azh_audio_capture: path too long");
    }
    if (azh_g.phase != AZH_PH_OPEN && azh_g.phase != AZH_PH_BOOTED) {
        return azh_fail(AZH_E_ORDER, "azh_audio_capture: needs azh_open first, and a host that has not failed to boot");
    }
    azh__audio_close();
    cap_frames = 0;
    cap_failed = 0;
    cap_file = fopen(path, "wb");
    if (cap_file == NULL) {
        cap_failed = 1;
        return azh_fail(AZH_E_IO, "cannot open the audio file %s", path);
    }
    if (setvbuf(cap_file, cap_buf, _IOFBF, sizeof cap_buf) != 0) {
        azh__audio_close();
        cap_failed = 1;
        return azh_fail(AZH_E_IO, "cannot buffer the audio file %s", path);
    }
    azh_log(AZH_LOG_INFO, "audio capture to %s", path);
    return AZH_OK;
}

int azh_audio_info(int64_t *frames_out, int32_t *rate_out)
{
    double rate;

    assert(cap_frames >= 0);
    if (frames_out == NULL || rate_out == NULL) {
        return azh_fail(AZH_E_ARG, "azh_audio_info: NULL out");
    }
    if (azh_g.phase != AZH_PH_BOOTED) {
        return azh_fail(AZH_E_ORDER, "azh_audio_info: needs a successful azh_boot");
    }
    if (cap_file != NULL && fflush(cap_file) != 0) {
        cap_failed = 1;
    }
    if (cap_failed != 0) {
        return azh_fail(AZH_E_IO, "the audio file could not be written");
    }
    rate = azh_g.av.timing.sample_rate;
    assert(rate >= 0.0 && rate < 1e6);      /* also false for NaN, so the cast below is defined */
    *frames_out = cap_frames;
    *rate_out = (int32_t)(rate + 0.5);
    return AZH_OK;
}
