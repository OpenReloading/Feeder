"""Build guide data: the BOM checklist carries every BOM row and the configured parts."""

import re
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
    assert lines and all(line.startswith(f"{i}. ") for i, line in enumerate(lines, 1))  # noqa: PT018


def test_wiring_board_ends_exist_and_the_motor_runs_through_the_relay():
    board = guide.wiring_board()
    terminals = {f"{k}:{t}" for k, p in board["parts"].items() for side in p["ports"].values() for t in side}
    wires = [c for step in board["steps"] for c in step["connections"]]
    assert len({c["no"] for c in wires}) == len(wires)
    assert all(c["a"] in terminals and c["b"] in terminals and c["color"] in board["colors"] for c in wires)
    ends = {frozenset((c["a"], c["b"])) for c in wires}
    assert {frozenset(("U1:M+", "K1:OUT1")), frozenset(("K1:OUT2", "X1:S1")), frozenset(("X2:S3", "K1:IN"))} <= ends


def test_no_wiring_step_tells_the_builder_to_reverse_the_motor():
    text = " ".join(f"{t} {n}" for _, t, n, _ in guide.WIRING_STEPS).lower()
    assert not re.search(r"swap|revers\w* (the )?(motor|leads|polarity of the motor)|wrong way|opposite way", text)


def test_wiring_has_fuse_series_diode_and_flyback_diode_after_the_relay_contact():
    wires = [c for step in guide.wiring_board()["steps"] for c in step["connections"]]
    ends = {frozenset((c["a"], c["b"])) for c in wires}
    assert {frozenset(("Q1:ON", "F1:1")), frozenset(("F1:2", "D1:A")), frozenset(("D1:K", "XP:1"))} <= ends  # supply side, in series
    assert {frozenset(("D2:K", "X1:S1")), frozenset(("K1:OUT2", "X1:S1")), frozenset(("D2:A", "X1:S2"))} <= ends  # motor side of the contact


def test_bom_protects_the_motor_stall_current_and_every_electronics_row_has_a_source_or_is_unverified():
    rows = guide.bom_rows()
    text = " ".join(" ".join(cells) for _, cells in rows)
    assert "Stall current at most 2.60 A" in text
    electronics = {guide._plain(cells[0]): " ".join(cells) for section, cells in rows if section == "Electronics"}
    for word in ("5 A", "fuse", "Schottky", "Flexible wire", "Motor cable", "ferrule"):
        assert any(word in name for name in electronics), word
    assert all("http" in row or "unverified" in row for row in electronics.values())


def test_wiring_page_checks_the_sensor_type_by_continuity_before_wiring():
    page = (Path(__file__).parent.parent / "guide" / "wiring.md").read_text(encoding="utf-8")
    assert page.index("## Check the sensor on delivery") < page.index("data-buildguide")
    assert "continuity" in page
