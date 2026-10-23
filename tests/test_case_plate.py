import math
from dataclasses import replace

import pytest
from build123d import Box, Pos, Rot

from feeder.config import CFG
from feeder.parts import case_plate as cp
from feeder.parts import layout
from feeder.parts import slip_clutch as sc

P, PS = CFG.case_plate, CFG.plate_seat
HOLES = replace(CFG, case_plate=replace(P, notches=False))


@pytest.fixture(scope="module")
def plate():
    return cp.plate()


def test_plate_is_a_single_valid_solid(plate):
    assert plate.is_valid
    assert len(plate.solids()) == 1
    holes = cp.plate(HOLES)
    assert holes.is_valid and len(holes.solids()) == 1


def test_pockets_hold_one_case_with_walls_between():
    cal = layout.caliber()
    d, r, n = layout.pocket_d(), layout.pocket_circle_r(), layout.pocket_count()
    assert cal.rim_d < d < 2 * cal.rim_d  # one case, never two side by side
    chord = 2 * r * math.sin(math.pi / n)
    assert chord - d - 2 * P.top_chamfer >= CFG.print.min_wall
    assert r + d / 2 == pytest.approx(layout.band_inner_r())  # notches: the band closes the pocket
    assert layout.pocket_count() > layout.pocket_count(HOLES)  # notches put the pockets further out
    assert layout.pocket_circle_r(HOLES) + d / 2 + P.rim_wall <= layout.plate_r(HOLES) and P.rim_wall >= CFG.print.min_wall


def test_plate_height_keeps_mouth_down_cases_high():
    h, length = layout.plate_h(), layout.caliber().case_length
    assert h >= PS.hub_h
    assert h < length / 2  # a mouth-down case stands mostly above the plate and tips out


def _top_at(part, r: float, angle: float) -> float:
    """Highest material on a vertical line at radius r and angle deg."""
    probe = Rot(Z=angle) * Pos(r, 0, 0) * Box(0.2, 0.2, 100)
    return (part & probe).bounding_box().max.Z


def test_channels_lead_into_the_pockets_and_keep_the_pocket_wall(plate):
    h, d, r, n = layout.plate_h(), layout.pocket_d(), layout.pocket_circle_r(), layout.pocket_count()
    assert P.channel_depth <= h / 4  # three quarters of the pocket wall still holds an upright case
    inner = r - P.channel_len
    assert 2 * inner * math.sin(math.pi / n) - (d - 1) >= CFG.print.min_wall  # channels stay apart at their inner end
    a = cp.pocket_angles()[0]
    for x in (d / 2 + 2, P.channel_len / 2):  # floor rises toward the centre
        assert _top_at(plate, r - x, a) == pytest.approx(h - P.channel_depth * (1 - x / P.channel_len), abs=0.05)
    assert _top_at(plate, r - P.channel_len - 2, a) == pytest.approx(h, abs=0.01)


def test_ribs_and_lift_tabs_sit_between_cap_and_channels(plate):
    h = layout.plate_h()
    recess = CFG.cap.d / 2 + PS.cap_gap
    assert cp._inner_r(CFG) - recess >= CFG.print.min_wall  # the cap twists off past them
    rib_end = layout.pocket_circle_r() - layout.pocket_d() / 2 - P.channel_len - P.top_chamfer
    assert rib_end - cp._inner_r(CFG) >= 30  # ribs long enough to stir
    assert cp._inner_r(CFG) + P.lift_len < rib_end
    zc = sc.levels()
    assert cp.lift_tab_top() == pytest.approx(zc.cap_top - zc.plate_bottom)  # no higher than the cap
    assert plate.bounding_box().max.Z == pytest.approx(cp.lift_tab_top(), abs=0.01)
    rib_angle = 90 + 360 * 0.5 / P.rib_count
    assert _top_at(plate, (cp._inner_r(CFG) + rib_end) / 2, rib_angle) == pytest.approx(h + P.rib_h, abs=0.05)
    assert plate.bounding_box().min.Z == pytest.approx(0, abs=1e-6)  # nothing under the plate


def test_plate_fits_inside_the_band():
    assert layout.plate_r() + P.wall_gap <= layout.band_inner_r()
    assert layout.band_inner_r() + CFG.track.band_t + CFG.print.fit <= layout.bowl_r() + 1e-9
