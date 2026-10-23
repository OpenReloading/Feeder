"""Simulation: the model has the CAD's opening and plate, and a short run keeps every case in the bowl."""

import math

import mujoco

from feeder.config import CFG
from feeder.parts import case_plate, layout
from sim import model as sm
from sim.run import run, wilson


def test_model_has_the_drop_opening_and_the_plate_hulls():
    m = mujoco.MjModel.from_xml_string(sm.mjcf(45.0, 3))
    half, r0, r1 = sm.opening()
    names = [m.geom(i).name for i in range(m.ngeom)]
    step = 360 / CFG.sim.segments
    open_segs = [i for i in range(CFG.sim.segments) if sm._off((i + 0.5) * step) <= half]
    assert open_segs and all(f"deck_b{i}" not in names for i in open_segs)
    assert sum(n.startswith("plate") for n in names) == len(sm.plate_hulls())
    assert r1 - r0 > layout.caliber().rim_d  # a case fits through


def _one_case_through_the_exit(base_down: bool) -> float | None:
    """One upright case in the pocket three pitches before the exit, plate at 6 rpm for one second: the angle (deg)
    where its centre first crosses the deck, None when it stays above."""
    m = mujoco.MjModel.from_xml_string(sm.mjcf(45.0, 1))
    d = mujoco.MjData(m)
    q = m.jnt_qposadr[m.body("c0").jntadr[0]]
    a = math.radians(case_plate.pocket_angles()[0] - 3 * 360 / layout.pocket_count())
    r, zc = layout.pocket_circle_r(), layout.levels().deck_top + layout.caliber().case_length / 2 + 0.3
    d.qpos[q:q + 7] = [r * math.cos(a) * sm.MM, r * math.sin(a) * sm.MM, zc * sm.MM, *([1, 0, 0, 0] if base_down else [0, 1, 0, 0])]
    d.ctrl[0] = CFG.case_plate.direction * 6 * 2 * math.pi / 60
    while d.time < 1.0:
        mujoco.mj_step(m, d, nstep=10)
        p = d.qpos[q:q + 3] / sm.MM
        if p[2] < layout.levels().deck_top:
            return math.degrees(math.atan2(p[1], p[0]))
    return None


def test_base_down_case_rides_its_pocket_and_drops_through_the_opening():
    ang = _one_case_through_the_exit(True)
    assert ang is not None and abs(ang - sm.EXIT) <= sm.opening()[0]


def test_mouth_down_case_tips_out_before_the_exit():
    assert _one_case_through_the_exit(False) is None


def test_extender_raises_the_wall_by_its_height_on_the_low_side():
    R = layout.bowl_r()
    assert math.isclose(sm.wall_top(-R, True) - sm.wall_top(-R, False), CFG.body.extender_h)
    assert all(sm.wall_top(y, True) >= sm.wall_top(y, False) for y in (-R, 0, R))


def test_case_option_sets_the_case_size_on_any_plate():
    m = mujoco.MjModel.from_xml_string(sm.mjcf(45.0, 1, case="45_acp"))
    cal = CFG.calibers.table["45_acp"]
    size = m.geom_size[[i for i in range(m.ngeom) if m.geom_bodyid[i] == m.body("c0").id][0]]
    assert math.isclose(size[0] / sm.MM, cal.rim_d / 2) and math.isclose((size[1] + size[0]) / sm.MM, cal.case_length / 2)


def test_wilson_interval_holds_the_share():
    lo, hi = wilson(30, 100)
    assert lo < 0.3 < hi and 0 < lo and hi < 1


def test_short_run_keeps_the_cases_and_the_plate_speed():
    r = run(45.0, 6.0, n_cases=30, seconds=3.0)
    assert r["lost"] == 0 and r["spilled"] == 0
    assert math.isfinite(r["torque_max"]) and r["torque_max"] > 0
    assert abs(r["speed_ratio"] - 1) < 0.05
    assert r["deepest_mm"] < 3  # contact penetration stays below a case wall plus the hull error
