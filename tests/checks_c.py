"""Pure check functions of step C's gate over parsed logs and summaries (step D reuses them)."""
import math
import re
import struct
from pathlib import Path

HID_MASK = 0x0FFF      # libctru A..Y; ZL and ZR (bits 14, 15) reach the guest through ir:rst
IRRST_MASK = 0xC000


def f32(value: float) -> float:
    """Round a Python float to float32."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


def touch_expected(x: int, y: int) -> tuple[int, int]:
    """What the guest logs (tx, ty) for a touch at bottom pixel (x, y): the float32 chain of phase-c.md section 2."""
    px = ((2 * (x + 40) + 1) * 32767) // 400 - 32767
    py = ((2 * (y + 240) + 1) * 32767) // 480 - 32767
    nx = int(f32(f32((px + 32767) / 65534.0) * 400.0))
    ny = int(f32(f32((py + 32767) / 65534.0) * 480.0))
    tx = f32((nx - 40) / 320.0)
    ty = f32((ny - 240) / 240.0)
    return int(f32(tx * 320.0)) & 0xFFFF, int(f32(ty * 240.0)) & 0xFFFF


def circle_expected(c: int) -> int:
    """The guest's steady circle-pad value for a record value c (roundf: halves away from zero)."""
    scaled = f32(f32(c / 32767.0) * 154.0)
    return int(math.copysign(math.floor(abs(scaled) + 0.5), scaled))


def parse_summary(line: str) -> dict:
    """One azhost batch summary line to a dict: ints and floats converted, msg unescaped (\\n, \\\\)."""
    head, _, rest = line.partition(' msg="')
    out: dict = {}
    for key, value in re.findall(r"(\w+)=(\S+)", head):
        try:
            out[key] = int(value)
        except ValueError:
            try:
                out[key] = float(value)
            except ValueError:
                out[key] = value
    text = rest[:-1] if rest.endswith('"') else rest
    out["msg"] = re.sub(r"\\(.)", lambda m: "\n" if m.group(1) == "n" else m.group(1), text)
    return out


def parse_layout(text: str) -> tuple[int, dict[str, tuple[int, int]]]:
    """Output of `azhost layout`: (abi, {name: (offset, size)})."""
    lines = text.splitlines()
    rows = {}
    for line in lines[1:]:
        name, offset, size = line.split()
        rows[name] = (int(offset), int(size))
    return int(lines[0].split("=")[1]), rows


def read_map(path: Path, layout: dict[str, tuple[int, int]]) -> dict:
    """host.map fields at the offsets `azhost layout` printed, plus 'pixels' (the whole pixel area)."""
    data = Path(path).read_bytes()
    out: dict = {}
    for name, (offset, size) in layout.items():
        if not name.startswith("map.") or name.endswith("__size__") or name == "map.pixels":
            continue
        field = name[4:]
        if field in ("message", "dims", "magic"):
            out[field] = data[offset:offset + size]
        else:
            out[field] = int.from_bytes(data[offset:offset + size], "little", signed=True)
    out["message"] = out["message"][: out["msg_len"]].decode("utf-8", "replace")
    out["dims"] = struct.unpack("<4I", out["dims"])
    offset, size = layout["map.pixels"]
    out["pixels"] = data[offset:offset + size]
    return out


def boot_offsets(summaries: list[dict], last_lines: dict[int, dict]) -> list[int]:
    """c per batch: the batch's last absolute frame minus the v of its last log line (batches 1-based)."""
    offsets = []
    for index, summary in enumerate(summaries, start=1):
        line = last_lines.get(index)
        if line is not None and "v" in line:
            offsets.append(int(summary["last"]) - line["v"])
    return offsets


def _extract(line: dict, kind: str) -> tuple:
    if kind == "hid":
        return (line["k"] & HID_MASK,)
    if kind == "irrst":
        return (line["k"] & IRRST_MASK,)
    if kind == "touch":
        return (line["tx"], line["ty"], 1) if line["td"] else (-1, -1, 0)
    return (line["cx"], line["cy"])


def change_offsets(lines: list[dict], plan: list[tuple[int, tuple]], kind: str, c_min: int) -> list:
    """For each planned change (planned host frame p, expected value tuple) the offset o_rel = v + c_min - p of the
    first log line, searched from the previous change's line on, that shows the expected value (None if never)."""
    offsets: list = []
    start = 0
    for planned, expected in plan:
        found = None
        for index in range(start, len(lines)):
            if _extract(lines[index], kind) == expected:
                found = index
                break
        if found is None:
            offsets.append(None)
            continue
        offsets.append(lines[found]["v"] + c_min - planned)
        start = found
    return offsets


def offsets_ok(offsets: list) -> tuple[bool, int, dict]:
    """The offset rule (phase-2.md P1): none missing or negative, all in {m, m+1} for the smallest m, m at most 2,
    the commoner value at least 90 % of the changes. Returns (ok, m, counts)."""
    if not offsets or any(o is None for o in offsets):
        return False, -1, {}
    m = min(offsets)
    counts = {value: offsets.count(value) for value in sorted(set(offsets))}
    ok = m >= 0 and m <= 2 and set(counts) <= {m, m + 1} and max(counts.values()) * 10 >= len(offsets) * 9
    return ok, m, counts


def bit_runs(lines: list[dict], bit: int, c_min: int) -> list[tuple[int, int]]:
    """Runs of one k bit being set: [(first host frame = v + c_min, number of lines)]."""
    runs: list[tuple[int, int]] = []
    inside = False
    for line in lines:
        held = (line["k"] >> bit) & 1 == 1
        if held and not inside:
            runs.append((line["v"] + c_min, 1))
        elif held:
            runs[-1] = (runs[-1][0], runs[-1][1] + 1)
        inside = held
    return runs
