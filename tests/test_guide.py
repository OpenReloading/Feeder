"""Build guide data: the BOM checklist carries every BOM row and the configured parts."""

from pathlib import Path

import build
from feeder import guide

README = Path(__file__).parent.parent / "README.md"


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
    text = README.read_text(encoding="utf-8")
    assert text.index("--8<-- [start:tilt]") < text.index("Tilt choice.") < text.index("--8<-- [end:tilt]")


def test_steps_markdown_numbers_every_assembly_step():
    lines = guide.steps_markdown().splitlines()
    assert lines and all(line.startswith(f"{i}. ") for i, line in enumerate(lines, 1))


def test_wiring_board_ends_exist_and_the_motor_runs_through_the_relay():
    board = guide.wiring_board()
    terminals = {f"{k}:{t}" for k, p in board["parts"].items() for side in p["ports"].values() for t in side}
    wires = [c for step in board["steps"] for c in step["connections"]]
    assert len({c["no"] for c in wires}) == len(wires)
    assert all(c["a"] in terminals and c["b"] in terminals and c["color"] in board["colors"] for c in wires)
    ends = {frozenset((c["a"], c["b"])) for c in wires}
    assert {frozenset(("U1:M+", "K1:COM")), frozenset(("K1:NO", "X1:S1")), frozenset(("X2:S3", "K1:IN"))} <= ends
