"""run(..., audio=True) on the tone app: silence before frame 60, then 440 Hz stereo at the core's rate."""
from __future__ import annotations

from pathlib import Path

import pytest

from dsp_component import write_component
from libazahar import Emulator

try:
    import numpy as np
except ImportError:                                   # the zero-crossing fallback below
    np = None

pytestmark = pytest.mark.slow

REPO = Path(__file__).resolve().parents[2]
TONE = REPO / "build" / "testapp-tone.3dsx"
START_FRAME = 60                                      # the app starts its sound at this guest frame
FRAMES = 240
GUEST_FPS = 59.83                                     # the 3DS screen's frame rate


@pytest.fixture
def tone_app() -> Path:
    if not TONE.is_file():
        pytest.skip(f"needs {TONE}: run make testapp-tone")
    return TONE


def _rows(audio):
    """(left, right) lists of ints from either audio form."""
    if hasattr(audio, "ndim") and audio.ndim == 2:
        return audio[:, 0].astype(int).tolist(), audio[:, 1].astype(int).tolist()
    return list(audio[0::2]), list(audio[1::2])


def _frequency(left, rate):
    """The tone's frequency in Hz: the FFT peak with numpy, else rising zero crossings."""
    if np is not None:
        x = np.asarray(left, dtype=np.float64)
        spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
        return float(np.argmax(spec)) * rate / len(x)
    crossings = sum(1 for a, b in zip(left, left[1:]) if a < 0 <= b)
    return crossings * rate / len(left)


def test_tone_is_captured(tone_app, workdir):
    seed = workdir / "seed"
    write_component(seed)
    emu = Emulator(tone_app, workdir / "run", sd_seed=seed)
    try:
        before = emu.run(START_FRAME, audio=True)         # guest frames 0..59: nothing plays yet
        rest = emu.run(FRAMES, audio=True)
        plain = emu.run(10)
    finally:
        emu.close()
    rate = rest.audio_rate
    assert abs(rate - 32728) < 50

    pre_l, pre_r = _rows(before.audio)
    assert not any(pre_l) and not any(pre_r)

    left, right = _rows(rest.audio)
    assert left == right                                      # the app plays the same sample on both sides
    # FRAMES guest frames should hold FRAMES * rate / 59.83 stereo frames, within one guest frame's worth. Measured: the
    # sound starts about 1.6 guest frames after the app calls its sound start (the DSP needs a moment to begin mixing, and
    # the measured steady rate is 59.83 frames per second), so the count is short by that start lag and never longer.
    one_frame = rate / GUEST_FPS
    expected = FRAMES * one_frame
    assert expected - 3 * one_frame <= len(left) <= expected + one_frame
    peak = max(abs(v) for v in left)
    assert 8000 < peak < 16000
    assert abs(_frequency(left, rate) - 440.0) <= 0.02 * 440.0
    assert plain.audio is None and plain.audio_rate == 0


def test_no_component_file_gives_silence(tone_app, workdir):
    emu = Emulator(tone_app, workdir / "run")
    try:
        res = emu.run(FRAMES, audio=True)
        log = (emu.sd / "tone" / "log.txt").read_text(errors="replace").splitlines()
    finally:
        emu.close()
    left, right = _rows(res.audio)
    assert not any(left) and not any(right)
    assert log
    for line in log:
        fields = dict(tok.split("=", 1) for tok in line.split())
        assert fields["ndsp_started"] == "0"
    started = [dict(t.split("=", 1) for t in ln.split()) for ln in log if int(ln.split()[0].split("=")[1]) >= START_FRAME]
    assert started and all(int(f["ndspInit_rc"], 16) != 0 for f in started)
