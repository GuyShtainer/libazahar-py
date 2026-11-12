"""The only place that knows the test app's control and log formats (docs/plans/phase-b.md section 3)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_testapp  # noqa: E402  (B's PNG decoder, imported, never copied)

FRAME_KEYS = ("f", "v", "s", "t", "k", "tx", "ty", "td", "cx", "cy")


def write_control(seed_dir: Path, **keys: object) -> Path:
    """Write <seed_dir>/testapp/control.txt with one key=value line per key; returns its path."""
    folder = Path(seed_dir) / "testapp"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "control.txt"
    lines = ["# written by tests/gate_c.py"] + [f"{key}={value}" for key, value in keys.items()]
    path.write_text("\n".join(lines) + "\n")
    return path


def parse_line(line: str) -> dict | None:
    """One complete log line to a dict: per-frame lines get kind 'frame' (int fields, k parsed as hex), event lines
    get kind '<name>' with their int fields; the start line and anything unknown give None."""
    parts = line.split()
    if not parts or parts[0] == "start":
        return None
    fields = {}
    for token in parts:
        if "=" in token:
            key, _, value = token.partition("=")
            fields[key] = value
    try:
        if parts[0].startswith("f="):
            row = {key: int(fields[key], 16 if key == "k" else 10) for key in FRAME_KEYS}
            row["kind"] = "frame"
            return row
        row = {key: int(value) for key, value in fields.items() if key in ("f", "v")}
        row["kind"] = parts[0]
        return row if "v" in row else None
    except (KeyError, ValueError):
        return None


def parse_log(path: Path) -> tuple[list[dict], list[dict]]:
    """Read a log file: (frames, events), complete lines only (a half-written last line is ignored)."""
    text = Path(path).read_text(errors="replace")
    complete = text[: text.rfind("\n") + 1]
    frames, events = [], []
    for line in complete.splitlines():
        row = parse_line(line)
        if row is not None:
            (frames if row["kind"] == "frame" else events).append(row)
    return frames, events


def read_png(path: Path) -> tuple[int, int, bytes]:
    """(width, height, rgba bytes) of a PNG written by the host."""
    return check_testapp.read_png_rgba(str(path))
