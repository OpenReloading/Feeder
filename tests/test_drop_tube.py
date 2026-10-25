import math

import pytest
from build123d import Box, Cylinder, Pos, Rot
from test_mount import _overlap, _unsupported

from feeder import printing
from feeder.config import CFG
from feeder.parts import body as b
from feeder.parts import drop_tube as dt
from feeder.parts import electronics as el
from feeder.parts import layout
from feeder.parts import mount as m
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


def test_male_end_is_the_exit_spigots_form(part):
    assert K.r_spigot - K.r_bore >= CFG.print.min_wall  # the wall left round the tube bore
    assert K.male_z >= K.boss_top  # the lugs clear the sensor boss
    assert part.bounding_box().max.Z == pytest.approx(K.tip)  # noqa: SIM300
    assert K.tip - K.male_z == E.spigot_len
    slab = Pos(0, 0, K.male_z + D.lug_z + D.lug_h + D.lug_tip + 1) * Box(80, 80, 0.2)  # past the lugs
    assert (part & slab).bounding_box().size.X / 2 == pytest.approx(K.r_spigot, abs=0.01)  # noqa: SIM300


def test_sensor_window_is_as_thin_as_configured(part):
    probe = Pos(30, 0, K.sensor_z) * Box(60, 0.02, 0.02)
    hits = (probe & part).solids()
    assert len(hits) == 1  # the plate hole is open, only the window is hit
    bb = hits[0].bounding_box()
    assert bb.min.X == pytest.approx(K.r_bore, abs=0.01)  # noqa: SIM300
    assert bb.max.X - bb.min.X == pytest.approx(D.window_t, abs=0.01)  # noqa: SIM300


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


LUGS = b.spigot_lugs()


def _lugs(dz: float = 0.0, turn: float = 0.0):
    """The spigot's lugs in the tube frame: `dz` along the drop (0 hangs in the notch, the tube lifted off it by `dz`),
    `turn` deg about the axis from the stop."""
    return Rot(Z=turn) * Pos(0, 0, dz) * LUGS


def _clear(dz: float, turn: float, part) -> bool:
    return _volume(part & _lugs(dz, turn)) < EPS


SLOT, STOP = dt.slot_angles()
LIFT = D.lock_lift


def test_lugs_hang_in_the_notches_and_cannot_be_pulled_off(part):
    assert _clear(0.02, STOP, part)
    assert not _clear(-0.05, STOP, part)  # the notch floor carries the lug, the tube cannot sink further
    assert not _clear(LIFT - 0.1, SLOT / 2, part)  # nor anywhere on the way to the slot, the groove floor holds it


def test_stop_holds_the_window_within_a_third_of_a_millimetre(part):
    probes = []
    for sign in (1, -1):
        lo, hi = 0.0, 10.0
        for _ in range(7):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if _clear(0.02, sign * mid, part) else (lo, mid)
        probes.append(lo)
    assert all(p > 0 for p in probes)  # the lugs are not jammed
    assert math.radians(sum(probes)) * K.window_x <= 0.3  # the notch walls fit the lugs, so the window cannot wander


def test_notch_detent_and_the_turn_between_slot_and_stop(part):
    assert _volume(part & _lugs(LIFT + FIT / 2, STOP)) < EPS  # lifted out of the notch
    for turn in (STOP + (SLOT - STOP) * i / 6 for i in range(7)):
        assert _clear(LIFT + FIT / 2, turn, part), turn  # and free to turn all the way to the slots
    beyond = math.copysign(8.0, -SLOT)  # past the stop: the notch end is a wall at any lift
    assert not _clear(LIFT + FIT / 2, beyond, part)
    assert not _clear(0.02, math.copysign(8.0, SLOT), part)  # in the notch, turning needs the lift
    assert not _clear(0.02, beyond, part)


def test_lugs_slide_in_through_the_slots_only(part):
    for dz in range(-8, int(LIFT + FIT / 2) + 1):
        assert _clear(dz, SLOT, part), dz
    assert _clear(LIFT + FIT / 2, SLOT, part)
    assert not _clear(0.5, SLOT + 180, part)  # wide lug on the narrow slot: the tube goes on one way only
    assert not _clear(0.5, SLOT + 90, part)  # no slot elsewhere
    assert not _clear(0.5, SLOT + 20, part)


def test_land_between_slot_and_notch_holds_on_every_plate_set():
    for s in layout.plate_sets():
        rs = b.bore_d(s) / 2 + s.exit.wall
        land = abs(math.radians(SLOT - STOP)) * rs - (s.drop_tube.lug_w[0] + 2 * s.print.fit)
        assert land >= s.print.min_wall, s
        assert s.drop_tube.lug_w[0] > s.drop_tube.lug_w[1]
        assert s.drop_tube.lug_h + s.print.fit + s.exit.wall >= s.print.min_wall + s.drop_tube.lug_h  # wall left outside the groove
        assert s.drop_tube.lug_z + s.drop_tube.lock_lift < s.exit.spigot_len  # the lock stays inside the socket


def test_hanging_tube_clears_the_exit_insert_and_turns_clear_of_the_body(part):
    ins = dt.placement() * Pos(0, 0, 0) * part
    assert _volume(ins & b.exit_insert()) < EPS
    core = b.core()
    pl = dt.placement()
    for a in (SLOT, SLOT / 2, 0.0):
        for dz in (0.0, -LIFT - FIT / 2):  # hanging and pushed on
            moved = pl * Pos(0, 0, dz) * Rot(Z=-a) * part
            assert _volume(moved & core) < EPS, (a, dz)


@pytest.mark.parametrize("left", [False, True], ids=["right", "left"])
def test_tube_with_its_sensor_goes_on_and_turns_clear_of_the_mount_and_the_box(part, left):
    pl, (lo, hi) = dt.placement(), m.tilt_span()
    box = el.box_left() if left else el.box()
    sensor = Pos(K.window_x, 0, K.sensor_z) * Rot(Y=90) * Cylinder(D.sensor_thread_d / 2, D.sensor_length, align=sc.BOTTOM)  # stays in the tube when it turns off
    carried = part + sensor
    for tilt in (lo, (lo + hi) / 2, hi):
        others = [b.core(), m.clamp_in_body(m.PARTS["mount_clamp"](), tilt), m.yoke_in_body(m.PARTS["mount_yoke"]()), el.box_frame(tilt, left=left) * box]
        for u in (1.0, 0.5, 0.0):  # from the slots to the stop
            for below in (0.0, 40.0, 100.0):  # sliding on from below, the sensor boss sweeps the drop path
                moved = pl * Pos(0, 0, below - LIFT - FIT / 2) * Rot(Z=-SLOT * u) * carried
                assert all(_overlap(moved, o) < EPS for o in others), (tilt, u, below)


def test_socket_and_lugs_print_without_supports(part):
    flags = _unsupported(Pos(0, 0, -0.013) * part, step=0.5)  # the nut slot ceiling and the flat sensor hole roof (short bridges) lie above the boss start
    assert [f for f in flags if f[0] < K.sensor_z - K.half_h] == []
    lugs = printing.on_bed("body_exit_insert", b.exit_insert())
    assert _unsupported(Pos(0, 0, -0.013) * lugs, step=0.5) == []  # lugs with a 45 deg underside on the spigot that leans 30 deg in print


def test_exit_spigot_radius_matches_the_socket():
    pl = dt.placement()
    slab = pl * (Pos(0, 0, D.lug_z + D.lug_h + D.lug_tip + 1) * Box(80, 80, 0.2))  # past the lugs
    section = b.exit_insert() & slab
    assert section.bounding_box().size.X / 2 == pytest.approx(K.r_spigot, abs=0.01)  # noqa: SIM300


def test_sensor_envelope_runs_through_both_lock_nuts_and_out_of_the_plate():
    assert D.sensor_thread_d < D.sensor_hole_d  # through the plate hole
    assert D.sensor_length >= K.plate_x - K.window_x + D.nut_t  # past the outer nut
    assert K.slot_h >= D.nut_t + 2 * FIT  # inner nut free in its slot
    # sensor frame: face on the window outer face, axis along the drop tube +x at the sensor height
    f = dt.sensor_frame()
    local = dt.placement().location.inverse() * f
    assert (local.position.X, local.position.Y, local.position.Z) == pytest.approx((K.window_x, 0, K.sensor_z), abs=1e-6)  # noqa: SIM300
