"""Build guide data for the BuildGuide MkDocs plugin (https://github.com/OpenReloading/BuildGuide): introduction
BOM checklist and wiring board of the configured feeder. Printed parts and fasteners come from the part builders and the
assembly, the other bought parts from the BOM file."""

import re
from pathlib import Path

from feeder import assembly, export
from feeder.config import CFG, Config
from feeder.wiring import WIRING_PARTS, WIRING_STEPS

BOM = Path(__file__).resolve().parent.parent / "bom" / "case_feeder_9mm.md"
CONFIGURATOR = BOM.parent.parent / "guide" / "configurator.md"
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


def _viewer_steps(cfg: Config) -> list[tuple[str, str]]:
    """The assembly steps the viewer shows: those that have parts."""
    steps = export._steps(cfg)
    return [steps[s] for s in export.used_steps(assembly.placed(cfg))]


def steps_markdown(cfg: Config = CFG) -> str:
    """The assembly step titles as a numbered Markdown list, for the guide's introduction."""
    return "".join(f"{i}. {title}\n" for i, (title, _) in enumerate(_viewer_steps(cfg), 1))


def steps_detail_markdown(cfg: Config = CFG) -> str:
    """The assembly steps with their text as a numbered Markdown list, for the printed assembly page."""
    return "".join(f"{i}. **{title}**: {text}\n" for i, (title, text) in enumerate(_viewer_steps(cfg), 1))


def assembly_row_markdown(cfg: Config = CFG) -> str:
    """The assembly row of the introduction's "What you get" list, with the number of assembly steps."""
    return f"1. [Assembly](assembly.md): {len(_viewer_steps(cfg))} steps in the viewer, and the assembled feeder as STEP and 3MF.\n"


def plate_groups_markdown(page: Path = CONFIGURATOR) -> str:
    """The plate groups of the configurator page's plate options as a Markdown table (Group, Calibers)."""
    group = re.search(r'<optgroup label="Plate groups">(.*?)</optgroup>', page.read_text(encoding="utf-8"), re.S)
    rows = re.findall(r"<option[^>]*>([^:<]+): ([^<]+)</option>", group.group(1) if group else "")
    return "| Group | Calibers |\n|---|---|\n" + "".join(f"| {name} | {calibers.replace('&amp;', '&')} |\n" for name, calibers in rows)


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
