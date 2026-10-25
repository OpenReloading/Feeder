"""Build guide data for the BuildGuide MkDocs plugin (https://github.com/OpenReloading/BuildGuide): introduction
BOM checklist and wiring board of the configured feeder. Printed parts and fasteners come from the part builders and the
assembly, the other bought parts from the BOM file."""

import re
from pathlib import Path

from feeder import assembly, export
from feeder.config import CFG, Config

BOM = Path(__file__).resolve().parent.parent / "bom" / "case_feeder_9mm.md"
FASTENER_PREFIX = "ISO|DIN|CNC Kitchen|Panel nut|Lock nut"  # BOM rows that the assembly places as fasteners
FASTENER = re.compile(rf"^({FASTENER_PREFIX})[ ,]")
LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")


def _plain(cell: str) -> str:
    return LINK.sub(r"\1", cell).replace("`", "").strip()


def bom_rows(path: Path = BOM) -> list[tuple[str, list[str]]]:
    """(section heading, cells) of every table row of the BOM file, headers left out."""
    section, out = "", []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        elif line.startswith("|") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells[0] not in ("Item", "Part"):
                out.append((section, cells))
    return out


def _qty(cell: str) -> int | str:
    return int(cell) if cell.isdigit() else _plain(cell)


def bom_items(printed: list[str], cfg: Config = CFG, path: Path = BOM) -> list[dict]:
    """Checklist rows: the `printed` part names, the fasteners of `cfg`, then the other bought parts of the BOM file."""
    rows = bom_rows(path)
    printed_notes = {name: re.sub(r"^1( each)?,? *", "", _plain(cells[1])).strip("()") for section, cells in rows if section == "Printed parts" for name in re.findall(r"`([^`]+)`", cells[0])}
    used_in: dict = {}
    for _, cells in rows:
        if FASTENER.match(cells[0]) and len(cells) > 2:
            used_in.setdefault(cells[0], []).append(_plain(cells[2]))
    items = [dict(group="Printed parts", part=name, spec=printed_notes.get(name, ""), qty=1) for name in printed]  # noqa: C408
    counts: dict = {}
    for f in assembly.fasteners_in_body(cfg):
        counts[f.name] = counts.get(f.name, 0) + len(f.at)
    items += [dict(group="Fasteners", part=name, spec=", ".join(used_in.get(name, [])), qty=n) for name, n in counts.items()]  # noqa: C408
    for section, cells in rows:
        if section == "Printed parts" or cells[0] in counts:
            continue
        link = LINK.search("|".join(cells))
        item = dict(group=section, part=_plain(cells[0]), spec=". ".join(_plain(c) for c in cells[2:] if _plain(c)), qty=_qty(cells[1]))  # noqa: C408
        items.append(item | ({"link": link.group(2)} if link else {}))
    ids: dict = {}
    for item in items:
        slug = re.sub(r"[^a-z0-9]+", "-", item["part"].lower()).strip("-")
        ids[slug] = ids.get(slug, 0) + 1
        item["id"] = slug if ids[slug] == 1 else f"{slug}-{ids[slug]}"
    return items


def steps_markdown(cfg: Config = CFG) -> str:
    """The assembly step titles as a numbered Markdown list, for the guide's introduction."""
    return "".join(f"{i}. {title}\n" for i, (title, _) in enumerate(export._steps(cfg), 1))


def _part(kind: str, name: str, sub: str, at: tuple, size: tuple, **ports) -> dict:
    return {"kind": kind, "name": name, "sub": sub, "at": list(at), "size": list(size), "ports": ports}


# Electronics box wiring, not to scale. Sockets (GX12, 3-pin for the sensor, 2-pin for the motor): P = plug
# pin outside, S = solder cup of the same pin inside.
WIRING_PARTS = {
    "B1": _part("sensor", "B1 sensor, NPN NC", "", (620, 20), (150, 60), bottom=["BN", "BU", "BK"]),
    "M1": _part("box", "M1 motor, 12 V", "", (810, 20), (120, 60), bottom=["+", "-"]),
    "X2": _part("socket", "X2 sensor socket", "", (620, 220), (150, 60), top=["P1", "P2", "P3"], bottom=["S1", "S2", "S3"]),
    "X1": _part("socket", "X1 motor socket", "", (810, 220), (120, 60), top=["P1", "P2"], bottom=["S1", "S2"]),
    "Q1": _part("box", "Q1 power switch", "front face", (70, 220), (100, 60), right=["COM", "ON"]),
    "J1": _part("box", "J1 12 V in", "DC jack, front face", (70, 440), (100, 70), right=["+", "-"]),
    "XP": _part("join", "XP +12 V", "", (230, 240), (150, 30), bottom=["1", "2", "3", "4"]),
    "XN": _part("join", "XN 0 V", "", (420, 240), (150, 30), bottom=["1", "2", "3", "4"]),
    "U1": _part("box", "U1 PWM controller", "knob in the front face", (260, 420), (130, 110), left=["V+", "V-"], right=["M+", "M-"]),
    "K1": _part("box", "K1 timer relay", "off-delay, about 2 s", (580, 420), (150, 110), left=["VCC", "GND", "IN"], right=["COM", "NO", "NC"]),
}

# (step id, title, note, [(no, a, b, colour)])
WIRING_STEPS = [
    ("A", "Power in", "Unplug the 12 V supply before you touch a terminal.",
     [("1", "J1:+", "Q1:COM", "RD"), ("2", "Q1:ON", "XP:1", "RD"), ("3", "J1:-", "XN:1", "BK")]),
    ("B", "PWM controller", "Turn the knob to the lowest setting before the first power-up.",
     [("4", "XP:2", "U1:V+", "RD"), ("5", "XN:2", "U1:V-", "BK")]),
    ("C", "Timer relay supply", "",
     [("6", "XP:3", "K1:VCC", "RD"), ("7", "XN:3", "K1:GND", "BK")]),
    ("D", "Sensor socket", "The sensor output pulls the relay input to 0 V while no brass is in front of it. "
     "Check the relay module takes a low input (unverified).",
     [("8", "XP:4", "X2:S1", "BN"), ("9", "XN:4", "X2:S2", "BU"), ("10", "X2:S3", "K1:IN", "BK")]),
    ("E", "Motor line", "The motor runs only while the relay holds. The cap thread follows the plate direction, so "
     "the motor turns one way only: set `case_plate.direction` in the configuration and print the matching plate and cap.",
     [("11", "U1:M+", "K1:COM", "RD"), ("12", "K1:NO", "X1:S1", "RD"), ("13", "U1:M-", "X1:S2", "BK")]),
    ("F", "Plugs", "Solder the sensor cable and the motor leads to the plugs: brown, blue, black to pins 1, 2, 3; "
     "motor + to pin 1.",
     [("14", "B1:BN", "X2:P1", "BN"), ("15", "B1:BU", "X2:P2", "BU"), ("16", "B1:BK", "X2:P3", "BK"),
      ("17", "M1:+", "X1:P1", "RD"), ("18", "M1:-", "X1:P2", "BK")]),
]


def wiring_board() -> dict:
    """Wiring board of the electronics box in the BuildGuide board format."""
    return {
        "title": "Wiring",
        "label": "Electronics box wiring",
        "size": [1000, 600],
        "prefix": "wire",
        "legend": ["Red = +12 V, black = 0 V, sensor cores in their own colours", "Green = selected connection"],
        "colors": {
            "RD": {"line": "#dc2626", "outline": "#7f1d1d"},
            "BK": {"line": "#1f2937", "outline": "#000000"},
            "BN": {"line": "#92400e", "outline": "#451a03"},
            "BU": {"line": "#2563eb", "outline": "#1e3a8a"},
        },
        "kinds": {
            "box": {"fill": "#f1f5f9", "stroke": "#17202a"},
            "socket": {"fill": "#1f2937", "stroke": "#1f2937"},
            "sensor": {"fill": "#e8f5ec", "stroke": "#15803d", "pins": {"BN": "#92400e", "BU": "#2563eb", "BK": "#111827"}},
            "join": {"fill": "#f1f5f9", "stroke": "#64748b"},
        },
        "rules": {"perTerminal": 2, "exempt": {"kinds": ["join"]}},
        "areas": {"box": {"title": "Electronics box", "at": [40, 170], "size": [920, 410], "color": "#475569"}},
        "parts": WIRING_PARTS,
        "steps": [{"id": i, "title": t, **({"note": n} if n else {}),
                   "connections": [{"no": no, "a": a, "b": b, "color": c} for no, a, b, c in wires]}
                  for i, t, n, wires in WIRING_STEPS],
    }


def guide_data(printed: list[str], cfg: Config = CFG) -> dict:
    """Guide data in the BuildGuide data format, `printed` the part names build.py exports for `cfg`."""
    return {
        "storage": "feeder-buildguide",
        "bom": {
            "note": "Default configuration: body in arcs, Pololu 2693 hub, adjustable tilt link, wall extender. Sizes marked unverified come from seller listings.",
            "export": "feeder-bom.csv",
            "linkLabel": "Source",
            "items": bom_items(printed, cfg),
        },
        "boards": {"wiring": wiring_board()},
    }
