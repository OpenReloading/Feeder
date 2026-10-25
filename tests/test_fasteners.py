"""Bought fasteners: the assembly places every one the BOM lists, each in its holes."""

import re
from dataclasses import replace
from pathlib import Path

import pytest
from build123d import Pos
from test_body import CONFIGS

from feeder import assembly, export, guide
from feeder.config import CFG, GENERIC_8MM_FLANGE
from feeder.parts import layout

GAP = 0.5  # mm, as in test_body: hole clearances and fits
BOM = Path(__file__).parent.parent / "bom" / "case_feeder_9mm.md"
ENVELOPES = ("level_sensor", "timer_relay", "pwm_controller", "pwm_knob", "toggle_switch", "dc_jack", "gx12_2_pin_socket", "gx12_3_pin_socket")  # bought electronics: nuts and screws must not cut them either


def test_fastener_counts_match_the_bom():
    bom: dict = {}
    for item, qty in re.findall(rf"^\| ((?:{guide.FASTENER_PREFIX})[ ,][^|]+?) \| (\d+) \|", BOM.read_text(), re.M):
        bom[item] = bom.get(item, 0) + int(qty)
    placed: dict = {}
    for f in assembly.fasteners_in_body(CFG):
        placed[f.name] = placed.get(f.name, 0) + len(f.at)
    assert placed == bom


def test_drop_tube_twists_on_without_a_screw_or_insert():
    on_tube = [f.name for f in assembly.fasteners_in_body(CFG) if f.host == "drop_tube"]
    assert on_tube == [f"Lock nut {CFG.drop_tube.sensor_thread}"]  # the sensor nut only
    assert "DIN 464" not in BOM.read_text()
    assert "thumb" not in BOM.read_text().lower()


def _counts(cfg, host: str | None = None) -> dict:
    out: dict = {}
    for f in assembly.fasteners_in_body(cfg):
        if host in (None, f.host):
            out[f.name] = out.get(f.name, 0) + len(f.at)
    return out


@pytest.mark.parametrize("tilt", CFG.mount.fixed_tilts)
def test_fixed_link_replaces_the_rod_nuts_and_sets_the_tilt(tilt):
    cfg = replace(CFG, mount=replace(CFG.mount, link=tilt))
    link = f"mount_link_{tilt:.0f}"
    adjustable = _counts(CFG, "mount_tilt_link")
    fixed = _counts(cfg, link)
    assert assembly.body_tilt(cfg) == tilt
    assert link in {p.name for p in assembly.placed(cfg)} and "mount_tilt_link" not in {p.name for p in assembly.placed(cfg)}  # noqa: PT018
    assert {f.host for f in assembly.fasteners_in_body(cfg)} <= {p.name for p in assembly.placed(cfg)}
    assert fixed == {k: v for k, v in adjustable.items() if k != "ISO 4032 M6 nut"}  # the pins and their washers and nuts stay
    assert adjustable["ISO 4032 M6 nut"] == 4 and not [f for f in assembly.fasteners_in_body(cfg) if f.name == "ISO 4032 M6 nut"]  # noqa: PT018


def test_default_link_is_the_adjustable_one_at_the_plate_tilt():
    assert CFG.mount.link == "adjustable" and assembly.body_tilt(CFG) == layout.tilt()  # noqa: PT018
    assert "mount_tilt_link" in {p.name for p in assembly.placed(CFG)}


def test_link_angle_must_be_a_printed_fixed_link():
    with pytest.raises(ValueError, match="fixed_tilts"):
        assembly.body_tilt(replace(CFG, mount=replace(CFG.mount, link=47.0)))


def test_generic_hub_takes_two_screws_with_nuts_under_the_flange():
    cfg = replace(CFG, metal_hub=GENERIC_8MM_FLANGE)
    hub = _counts(cfg, "slip_clutch_carrier_metal_hub")
    default = _counts(CFG, "slip_clutch_carrier_metal_hub")
    assert hub["ISO 4762 M3 x 12"] == 2 and hub["ISO 4032 M3 nut"] == 2  # README: 2 x ISO 4762 M3 x 12 with ISO 4032 M3 nuts  # noqa: PT018
    assert default["ISO 4762 M3 x 10"] == 3 and "ISO 4032 M3 nut" not in default  # tapped holes  # noqa: PT018
    assert {k: v for k, v in hub.items() if not k.startswith(("ISO 4762 M3", "ISO 4032"))} == {k: v for k, v in default.items() if not k.startswith("ISO 4762 M3")}


def _apart(ba, bb, gap=0.0) -> bool:
    return any(getattr(ba.max, a) + gap < getattr(bb.min, a) or getattr(bb.max, a) + gap < getattr(ba.min, a) for a in "XYZ")


@pytest.mark.parametrize("name", CONFIGS)
def test_fasteners_sit_in_their_holes_without_cutting_printed_parts(name):
    # nominal shank, head, nut and insert outer diameters: a misplaced fastener cuts solid material or floats
    cfg = CONFIGS[name]
    placed = assembly.placed(cfg)
    names = {p.name for p in placed}
    printed = [(p.name, p.shape, p.shape.bounding_box()) for p in placed if (not p.bought or p.name in ENVELOPES) and not p.tool]
    fs = assembly.fasteners_in_body(cfg)
    solids = [(f, loc * f.shape) for f in fs for loc in f.at]
    boxes = [s.bounding_box() for _, s in solids]
    for i, (f, solid) in enumerate(solids):
        assert f.host in names, f
        box = boxes[i]
        near = [(n, s) for n, s, b in printed if not _apart(box, b, GAP)]
        for n, s in near:
            if _apart(box, s.bounding_box()):
                continue
            common = solid & s
            volume = common.volume if common.solids() else 0.0
            assert volume < 1e-3, f"{f.name} on {f.host} cuts {n} by {volume:.4f} mm3"
        near += [(g.name, s) for j, (g, s) in enumerate(solids) if j != i and not _apart(box, boxes[j], GAP)]  # a nut on its washer
        assert min((solid.distance_to(s) for _, s in near), default=GAP + 1) <= GAP, f"{f.name} on {f.host} floats"


def test_every_electronics_envelope_has_its_nuts():
    # sensor: two lock nuts, one each side of the plate; each panel part: one panel nut on its host's inner face
    placed = {p.name: p for p in assembly.placed(CFG)}
    assert set(ENVELOPES) <= set(placed) and all(placed[n].bought for n in ENVELOPES)  # noqa: PT018
    nuts = {(f.name, f.host): len(f.at) for f in assembly.fasteners_in_body(CFG) if f.kind == "nut"}
    assert nuts[(f"Lock nut {CFG.drop_tube.sensor_thread}", "drop_tube")] == 1 and nuts[(f"Lock nut {CFG.drop_tube.sensor_thread}", "level_sensor")] == 1  # noqa: PT018
    for _, pp in CFG.electronics.panel_parts:
        assert sum(n for (name, _), n in nuts.items() if name == f"Panel nut, {pp.label}") == 1, pp.label


def test_viewer_matrices_place_fasteners_like_the_cad():
    for f in assembly.fasteners_in_body(CFG):
        for loc in f.at:
            m = export._matrix(loc)  # column-major
            for p in ((0, 0, 0), (1, 2, 3)):
                q = (loc * Pos(*p)).position
                got = [sum(m[c * 4 + r] * v for c, v in enumerate((*p, 1))) for r in range(3)]
                assert got == pytest.approx((q.X, q.Y, q.Z), abs=1e-4), f.name
