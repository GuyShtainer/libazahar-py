"""A gymnasium-style environment around the test app. Run from the repo root: python examples/gym_env.py

This example is outside the 1.0 promise: its names can change in any release, and nothing in the package imports
it. gymnasium is optional and is imported only here; without it the class refuses to build, with a plain line saying
how to install it (``pip install gymnasium``).

- Observation: the top screen, a (240, 400, 3) uint8 array (the alpha channel is dropped).
- Action: Discrete(4): 0 holds nothing, 1 holds A, 2 holds B, 3 holds START, for ``frameskip`` frames.
- Reward: read from guest memory with ``emu.memory``. The test app keeps a 32-byte record (``testapp/README.md``);
  its keys word at offset 12 is the buttons the app saw this frame. Reward is 1.0 when that word has the A bit, else
  0.0, so the reward proves the held button reached the guest.
- ``reset`` loads a saved state (made at the first reset when you pass none) and releases every held input, so each
  episode starts from the same frame with nothing held.
- Needs our core (guest memory); on Azahar's own core ``Emulator.memory`` raises NeedsLazpyCore.
"""
import re
import shutil
import sys
from pathlib import Path

from libazahar import Buttons, Circle, Emulator, Touch

try:
    import gymnasium
    from gymnasium import spaces
    import numpy
except ImportError:
    gymnasium = spaces = numpy = None

INSTALL_HINT = "install gymnasium to use this example: pip install gymnasium"
RECORD_MAGIC = 0x4C415A52           # "LAZR", the first word of the test app's record
KEYS_OFFSET = 12                    # the record's keys word (testapp/source/record.h)
FRAME_OFFSET = 4                    # the record's frame counter
ACTIONS = (0, Buttons.A, Buttons.B, Buttons.START)
BASE = gymnasium.Env if gymnasium is not None else object


class TestAppEnv(BASE):
    """gymnasium's API (reset, step, observation_space, action_space) over one headless instance of the test app."""

    __test__ = False                # not a pytest class, whatever the name
    metadata = {"render_modes": []}

    def __init__(self, app, workdir, *, state=None, boot_frames=60, frameskip=4, max_steps=200):
        """``state`` is a state made from this app; None saves one after ``boot_frames`` frames, at the first reset."""
        if gymnasium is None:
            raise ImportError(INSTALL_HINT)
        super().__init__()
        self.observation_space = spaces.Box(0, 255, (240, 400, 3), dtype=numpy.uint8)
        self.action_space = spaces.Discrete(len(ACTIONS))
        self._boot_frames, self._frameskip, self._max_steps = boot_frames, frameskip, max_steps
        self._steps = 0
        self._state = Path(state) if state is not None else None
        self._emu = Emulator(app, workdir)
        try:
            self._record = self._find_record()
        except BaseException:
            self._emu.close()           # do not leave the emulator running when the constructor fails
            raise

    def _find_record(self):
        """The record's guest address, from the app's start line."""
        self._emu.run(self._boot_frames)
        start = (self._emu.sd / "testapp/log.txt").read_text()
        found = re.search(r"^start addr_global=0x([0-9a-f]+)", start, re.M)
        if found is None:
            raise RuntimeError("the test app wrote no start line in its log")
        return int(found.group(1), 16)

    def _observe(self):
        top, _ = self._emu.screens()
        return numpy.array(top)[:, :, :3]               # a copy: the screens are views that the next shot changes

    def _reward(self):
        memory = self._emu.memory
        if memory.u32(self._record) != RECORD_MAGIC:
            raise RuntimeError("the guest record has the wrong magic: the app is not the test app")
        return 1.0 if memory.u32(self._record + KEYS_OFFSET) & Buttons.A else 0.0

    def reset(self, *, seed=None, options=None):
        """Load the state, release every held input, return (observation, info)."""
        super().reset(seed=seed)
        if self._state is None:
            self._state = self._emu.workdir / "gym-state"
            self._emu.save_state(self._state)
        self._emu.load_state(self._state)
        self._emu.set_input(buttons=0, touch=Touch.up, circle=Circle(0, 0))
        self._emu.run(1)                                # one frame, so the app sees the released input
        self._steps = 0
        return self._observe(), {"frame": self._emu.memory.u32(self._record + FRAME_OFFSET)}

    def step(self, action):
        """Hold the action's button for ``frameskip`` frames; returns (obs, reward, terminated, truncated, info)."""
        if not self.action_space.contains(action):
            raise ValueError(f"action {action!r} is not in {self.action_space}")
        self._emu.run(self._frameskip, inputs=[(1, int(ACTIONS[int(action)]))])
        self._steps += 1
        info = {"frame": self._emu.memory.u32(self._record + FRAME_OFFSET)}
        return self._observe(), self._reward(), False, self._steps >= self._max_steps, info

    def close(self):
        """Close the emulator."""
        self._emu.close()


def main():
    if gymnasium is None:
        sys.exit(INSTALL_HINT)
    from gymnasium.utils.env_checker import check_env
    work = Path("runs/gym_env")
    shutil.rmtree(work, ignore_errors=True)
    env = TestAppEnv("build/testapp.3dsx", work)
    try:
        check_env(env)
        obs, _ = env.reset(seed=0)
        total = 0.0
        for _ in range(200):
            obs, reward, terminated, truncated, _ = env.step(env.action_space.sample())
            total += reward
            if terminated or truncated:
                obs, _ = env.reset()
    finally:
        env.close()
    if obs.shape != (240, 400, 3) or total <= 0:
        sys.exit(f"gym_env failed: observation {obs.shape}, total reward {total}")
    print("gym_env ok")


if __name__ == "__main__":
    main()
