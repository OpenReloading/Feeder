"""Build guide data: the BOM checklist carries every BOM row and the configured parts."""

from pathlib import Path

import build
from feeder import assembly, guide
from feeder.config import CFG

DESIGN = Path(__file__).parent.parent / "docs" / "design.md"


def test_bom_checklist_has_every_part_once_with_unique_ids():
    printed = [name for name, _ in build.iter_parts()]
    items = guide.bom_items(printed)
    assert len({i["id"] for i in items}) == len(items)
    parts = {i["part"]: i for i in items}
    assert all(parts[name]["group"] == "Printed parts" for name in printed)
    for section, cells in guide.bom_rows():
        if section != "Printed parts":
            item = parts[guide._plain(cells[0])]  # bought parts and fasteners of the BOM file
            if item["group"] != "Fasteners":
                assert item["qty"] == guide._qty(cells[1]), cells[0]


def test_tilt_section_markers_for_the_guide_page():
    text = DESIGN.read_text(encoding="utf-8")
    assert text.index("--8<-- [start:tilt]") < text.index("Tilt choice.") < text.index("--8<-- [end:tilt]")
    assert text.index("Tilt choice.") < text.index("--8<-- [start:tilt-table]") < text.index("| 45 deg |") < text.index("--8<-- [end:tilt-table]") < text.index("--8<-- [end:tilt]")


def test_steps_markdown_numbers_every_assembly_step():
    lines = guide.steps_markdown().splitlines()
    assert lines and all(line.startswith(f"{i}. ") for i, line in enumerate(lines, 1))  # noqa: PT018


def test_steps_detail_markdown_gives_every_step_its_text():
    titles, details = guide.steps_markdown().splitlines(), guide.steps_detail_markdown().splitlines()
    assert len(details) == len(titles)
    assert all(d.startswith(t.replace(". ", ". **", 1) + "**: ") and len(d) > len(t) + 6 for t, d in zip(titles, details, strict=True))


def test_assembly_eyebrow_counts_the_steps():
    assert f">{len(guide.steps_markdown().splitlines())} steps<" in guide.assembly_eyebrow_markdown()


def test_fasteners_table_has_every_fastener_of_the_assembly_in_its_step():
    rows = [line.strip("|").split(" | ") for line in guide.fasteners_markdown().splitlines()[2:]]
    titles = guide.steps_markdown().splitlines()
    counts: dict = {}
    for f in assembly.fasteners_in_body(CFG):
        counts[f.name] = counts.get(f.name, 0) + len(f.at)
    got: dict = {}
    for _, hardware, step in rows:
        n, name = hardware.split(" x ", 1)
        got[name] = got.get(name, 0) + int(n)
        assert step.strip() in titles
    assert got == counts


def test_wiring_board_ends_exist_and_the_motor_runs_through_the_relay():
    board = guide.wiring_board()
    terminals = {f"{k}:{t}" for k, p in board["parts"].items() for side in p["ports"].values() for t in side}
    wires = [c for step in board["steps"] for c in step["connections"]]
    assert len({c["no"] for c in wires}) == len(wires)
    assert all(c["a"] in terminals and c["b"] in terminals and c["color"] in board["colors"] for c in wires)
    ends = {frozenset((c["a"], c["b"])) for c in wires}
    assert {frozenset(("U1:M+", "K1:OUT1")), frozenset(("K1:OUT2", "X1:S1")), frozenset(("X2:S3", "K1:IN"))} <= ends


def test_wiring_has_fuse_series_diode_and_flyback_diode_after_the_relay_contact():
    wires = [c for step in guide.wiring_board()["steps"] for c in step["connections"]]
    ends = {frozenset((c["a"], c["b"])) for c in wires}
    assert {frozenset(("Q1:ON", "F1:1")), frozenset(("F1:2", "D1:A")), frozenset(("D1:K", "XP:1"))} <= ends  # supply side, in series
    assert {frozenset(("D2:K", "K1:OUT2")), frozenset(("K1:OUT2", "X1:S1")), frozenset(("D2:A", "U1:M-")), frozenset(("U1:M-", "X1:S2"))} <= ends  # motor side of the contact


def test_assembly_row_counts_the_assembly_steps():
    assert f": {len(guide.steps_markdown().splitlines())} steps " in guide.assembly_row_markdown()


def test_guide_steps_are_the_viewer_steps():
    steps, used = guide.export._steps(guide.CFG), guide.export.used_steps(guide.assembly.placed(guide.CFG))
    assert len(used) < len(steps)  # the default leaves out the optional drop tube chain
    assert [line.split(". ", 1)[1] for line in guide.steps_markdown().splitlines()] == [steps[s][0] for s in used]


def test_plate_groups_table_has_each_group_of_the_configurator_options():
    rows = guide.plate_groups_markdown().splitlines()[2:]
    assert [r.split(" | ")[0].strip("| ") for r in rows] == [g.replace("_", " ") for g in guide.CFG.calibers.groups]
    assert sum(r.count(",") + 1 for r in rows) == len(guide.CFG.calibers.table)
