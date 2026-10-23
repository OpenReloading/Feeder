import pytest
from build123d import Box, Cylinder, Pos

from feeder.config import CFG
from feeder.lib import fasteners
from feeder.parts import body as b
from feeder.parts import drop_tube as dt
from feeder.parts import layout
from feeder.parts import slip_clutch as sc

D, E, FIT = CFG.drop_tube, CFG.exit, CFG.print.fit
K = dt.dims()
CAL = layout.caliber()
EPS = 1e-3


@pytest.fixture(scope="module")
def part():
    return dt.drop_tube()


def _volume(shape) -> float:
    return shape.volume if shape.solids() else 0.0


def _cyl(r: float, z0: float, z1: float):
    return Pos(0, 0, z0) * Cylinder(r, z1 - z0, align=sc.BOTTOM)


def test_drop_tube_is_a_single_valid_solid(part):
    assert part.is_valid
    assert len(part.solids()) == 1


def test_boss_wings_rise_from_the_tube():
    assert K.half_h > K.r_tube  # the 45 deg wing flanks run outward and up


def test_bore_never_steps_inward_along_the_path():
    profile = dt.bore_profile()
    diameters = [d for _, d in profile]
    assert diameters[0] == pytest.approx(b.bore_d())
    assert diameters == sorted(diameters)
    assert D.hose_id >= b.bore_d()
    assert D.hose_id < D.hose_od


def test_printed_bore_matches_the_profile(part):
    r = K.r_bore
    for z in (K.depth + K.r_socket - K.r_bore + 0.5, K.sensor_z, K.boss_top + 0.5, K.tip - 0.5):  # above the 45 deg shoulder cone
        assert _volume(part & _cyl(r - 0.01, z - 0.2, z + 0.2)) < EPS  # nothing inside the bore
        ring = _cyl(r + 0.05, z - 0.2, z + 0.2) - _cyl(r - 0.01, z - 0.3, z + 0.3)
        assert _volume(part & ring) > EPS  # and the wall starts at it
    assert 2 * r >= b.bore_d() + 2 * FIT - EPS


def test_socket_bore_is_a_sliding_fit_on_the_spigot_with_a_stop(part):
    assert K.r_socket - K.r_spigot == pytest.approx(FIT)
    assert _volume(part & _cyl(K.r_socket - 0.01, 0, K.depth)) < EPS
    assert _volume(part & (_cyl(K.r_socket + 0.05, 0, K.depth) - _cyl(K.r_socket + 0.01, 0, K.depth))) > EPS
    assert K.depth >= E.spigot_len + FIT  # the spigot end clears the shoulder
    assert K.r_bore > b.bore_d() / 2  # the shoulder face of the spigot end opens outward into the tube


def test_barb_is_thick_enough_and_fits_its_length(part):
    assert K.r_barb - K.r_bore >= CFG.print.min_wall
    assert D.barb_ridges * D.barb_ridge_pitch <= D.barb_len
    assert K.r_barb == pytest.approx((D.hose_id + D.barb_grip) / 2)
    assert part.bounding_box().max.Z == pytest.approx(K.tip)


def test_sensor_window_is_as_thin_as_configured(part):
    probe = Pos(30, 0, K.sensor_z) * Box(60, 0.02, 0.02)
    hits = (probe & part).solids()
    assert len(hits) == 1  # the plate hole is open, only the window is hit
    bb = hits[0].bounding_box()
    assert bb.min.X == pytest.approx(K.r_bore, abs=0.01)
    assert bb.max.X - bb.min.X == pytest.approx(D.window_t, abs=0.01)


def test_sensor_clears_the_last_dropped_case():
    assert K.tip - K.sensor_z >= CAL.case_length + D.sensor_margin
    assert K.sensor_z - K.half_h - (K.plate_x - K.r_bore) >= K.socket_top - EPS  # boss sits above the socket


def test_sensor_hole_nuts_and_plate_fit_the_m18_sensor(part):
    assert D.sensor_hole_d >= D.sensor_thread_d + 0.5
    assert 2 * K.half_h >= D.nut_af + 2 * CFG.fasteners.head_fit + 2 * D.boss_wall - EPS  # plate covers the outer nut
    assert D.plate_t >= CFG.print.min_wall
    assert K.slot_h == pytest.approx(D.nut_t + 2 * FIT)
    nut = Pos(K.window_x + K.slot_h / 2, 0, K.sensor_z) * Box(D.nut_t, D.nut_af - 0.2, D.nut_af - 0.2)
    assert _volume(part & nut) < EPS  # the inner nut sits free in its slot
    assert _volume(part & (Pos(K.plate_x - D.plate_t / 2, 0, K.sensor_z) * Box(D.plate_t - 0.1, D.nut_af, D.nut_af))) > EPS  # the plate carries the outer nut


def test_thumb_screw_presses_on_the_spigot_before_its_head_meets_the_boss():
    size, length = D.screw_size, D.screw_length
    ins = CFG.fasteners.inserts[size]
    assert ins.length >= CFG.fasteners.min_engagement * fasteners.nominal_d(size)
    assert K.screw_boss_t - ins.hole_depth >= 0.4  # at least one perimeter between insert hole and socket
    assert K.screw_boss_r / 2**0.5 >= ins.hole_d / 2 + ins.min_wall - EPS
    lift = length - K.screw_boss_t - FIT  # head off the boss with the tip on the spigot
    assert E.wall / 2 <= lift < length - ins.length  # the spigot may give half its wall, the thread stays in the insert
    assert D.knurl_d > D.collar_d > fasteners.nominal_d(size) and D.head_h > D.knurl_h


def test_exit_spigot_radius_matches_the_socket():
    pl = dt.placement()
    slab = pl * (Pos(0, 0, 5) * Box(80, 80, 0.2))
    section = b.exit_insert() & slab
    assert section.bounding_box().size.X / 2 == pytest.approx(K.r_spigot, abs=0.01)


def test_drop_tube_clears_the_exit_insert_and_the_body(part):
    pl = dt.placement()
    placed = pl * part
    bt = placed.bounding_box()
    for name, build in b.PARTS.items():
        other = build()
        bo = other.bounding_box()
        if any(getattr(bt.max, a) <= getattr(bo.min, a) or getattr(bo.max, a) <= getattr(bt.min, a) for a in "XYZ"):
            continue
        assert _volume(placed & other) < EPS, name
