"""One simulated operating point: plate at `rpm`, body at `tilt`, `n_cases` kept in the bowl.

A case that crosses the deck plane inside the drop opening is an exit: its orientation is read at that moment
(base down when its mouth points up the plate axis). Where it crossed is its last position above the deck, as
below the deck the tilt pulls it sideways before the next check. It goes back on top of the pile, so the fill stays. A case
below the deck anywhere else is lost (a tunnelling fault of the model) and one past the wall is spilled. Nothing
is counted during the warm-up turns.

The wall extender is fitted when the fill is above the wall's capacity at the tilt (`layout.capacity`), as the
README tells users. A case goes back below the wall top; when the pile leaves no room there it counts as
`overfill` and is dropped on top anyway.

`start` is how the run begins: "settled" (the pile lies on the plate), "dumped" (it falls the height of the wall onto the
plate along gravity, as poured in from above), "tilt_change" (it settles at the far end of the mount's tilt range, then
the tilt goes to `tilt` in `CHANGE_S`) or "dumped_tilt_change" (dumped at the far end, then the tilt change). A spill
counts from the first step, the pile settling and the tilt change included.
"""

import math
import time
from dataclasses import replace

import mujoco
import numpy as np

from feeder.config import CFG, Config
from feeder.parts import layout
from feeder.parts import slip_clutch as sc
from sim.model import EXIT, MM, G, mjcf, opening, wall_top

START = ("settled", "dumped", "tilt_change", "dumped_tilt_change")
CHANGE_S = 1.0  # s the tilt takes to go from the far end of the range to `tilt`: the link is swapped or the body pushed, not run along the rod
CHUNK = 0.05  # s between checks
DEEP = 1.5  # mm, contact overlap counted in `deep_share`: the pocket clearance per side


def wilson(k: int, n: int, zq: float = 1.96) -> tuple[float, float]:
    """95 % confidence interval of a share k / n."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    c = zq * math.sqrt(p * (1 - p) / n + zq * zq / (4 * n * n)) / (1 + zq * zq / n)
    mid = (p + zq * zq / (2 * n)) / (1 + zq * zq / n)
    return max(0.0, mid - c), min(1.0, mid + c)


def run(tilt: float, rpm: float, n_cases: int = 250, revs: float = 3.0, cfg: Config = CFG, com_ratio: float | None = None,  # noqa: C901, PLR0912, PLR0913, PLR0915
        mu: float | None = None, seed: int = 1, seconds: float | None = None, extender: bool | None = None,
        plate: str | None = None, case: str | None = None, start: str = "settled") -> dict:
    """Simulate and return the metrics. `seconds` replaces warm-up and `revs` by a plain run (smoke tests).
    `extender` None fits it when `n_cases` is above the wall's capacity at the steeper of `tilt` and the tilt the run
    starts at. `plate` is a plate set (`case_plate.caliber`), `case` a key of `calibers.table` (default: the plate's
    envelope case), `start` one of `START`."""
    if start not in START:
        raise ValueError(f"start {start!r} is not one of {START}")
    if plate:
        cfg = replace(cfg, case_plate=replace(cfg.case_plate, caliber=plate))
    s = cfg.sim
    lo, hi = cfg.mount.tilt_range
    tilt_from = (lo if abs(tilt - lo) > abs(tilt - hi) else hi) if "tilt_change" in start else tilt
    if extender is None:
        extender = layout.capacity(max(tilt, tilt_from), cfg=cfg) < n_cases
    model = mujoco.MjModel.from_xml_string(mjcf(tilt, n_cases, cfg, com_ratio, mu, extender, case))
    data = mujoco.MjData(model)
    rng = np.random.default_rng(seed)
    z, R = layout.levels(cfg), layout.bowl_r(cfg)
    half, r0, r1 = opening(cfg)
    pt = z.plate_top
    qa = np.array([model.jnt_qposadr[model.body(f"c{i}").jntadr[0]] for i in range(n_cases)])
    va = np.array([model.jnt_dofadr[model.body(f"c{i}").jntadr[0]] for i in range(n_cases)])
    hinge = model.jnt_dofadr[model.joint("hinge").id]
    hinge_q = model.jnt_qposadr[model.joint("hinge").id]

    def place(i: int, x: float, y: float, zz: float):
        q = rng.normal(size=4)
        data.qpos[qa[i]:qa[i] + 7] = [x * MM, y * MM, zz * MM, *(q / np.linalg.norm(q))]
        data.qvel[va[i]:va[i] + 6] = 0

    cell = 22.0  # a case fits a 22 mm cell in any orientation (diagonal 21.6), so the start lattice has no overlap
    grid = np.arange(-R, R + 1, cell)
    spots = [(x, y) for x in grid for y in grid if cfg.cap.d / 2 + cell / 2 < math.hypot(x, y) < layout.plate_r(cfg) - cell / 2]
    for i in range(n_cases):
        x, y = spots[i % len(spots)]
        fall = (z.wall_top - pt if "dumped" in start else 40) + cell * (i // len(spots))
        place(i, x, y + (fall * math.tan(math.radians(tilt_from)) if "dumped" in start else 0), pt + fall)  # dumped: from up the gravity line, so it lands on the spot

    def respawn(i: int) -> bool:
        """On top of the pile on the low side, above the highest case near the spot so nothing overlaps, and below
        the wall top. False when no spot has room (overfill): then on top of the pile."""
        p = data.qpos[qa[:, None] + np.arange(3)] / MM
        for _ in range(20):
            a, r = math.radians(270 + rng.uniform(-60, 60)), rng.uniform(cfg.cap.d / 2 + 15, layout.plate_r(cfg) - 15)
            x, y = r * math.cos(a), r * math.sin(a)
            near = np.hypot(p[:, 0] - x, p[:, 1] - y) < 2 * cell
            zz = max(pt + 40, (p[near, 2].max() if near.any() else 0) + cell)
            if zz < wall_top(y, extender, cfg) - cell:
                place(i, x, y, zz)
                return True
        place(i, x, y, zz)
        return False

    mujoco.mj_forward(model, data)
    w = cfg.case_plate.direction * rpm * 2 * math.pi / 60
    warm = 0.0 if seconds else s.warmup_revs * 60 / rpm
    total = seconds if seconds else warm + revs * 60 / rpm
    data.ctrl[0] = w

    def tilt_to(deg: float):
        model.opt.gravity[:] = [0, -G * math.sin(math.radians(deg)), -G * math.cos(math.radians(deg))]

    tilt_to(tilt_from)
    m = dict(exits=0, base_down=0, mouth_down=0, sideways=0, lost=0, spilled=0, overfill=0)  # noqa: C408
    torque, speed, deepest, deepest_pair, lost_at, spilled_at, deep_checks = [], [], 0.0, "", [], [], 0
    turn0 = None
    entered = np.zeros(n_cases, dtype=bool)
    above = data.qpos[qa[:, None] + np.arange(3)] / MM
    n_step = round(CHUNK / s.timestep)
    travel = rpm * 6 * CHUNK  # deg the plate turns between checks
    t0 = time.time()
    while data.time < total:
        if "tilt_change" in start:
            tilt_to(tilt_from + (tilt - tilt_from) * min(1.0, max(0.0, (data.time - warm) / CHANGE_S)))
        mujoco.mj_step(model, data, nstep=n_step)
        counting = data.time >= warm
        if counting:
            if turn0 is None:
                turn0 = data.qpos[hinge_q]
            torque.append(abs(data.actuator_force[0]))
            speed.append(data.qvel[hinge])
            if data.ncon:
                c = min(data.contact[:data.ncon], key=lambda c: c.dist)
                deep_checks += -c.dist / MM > DEEP
                if -c.dist / MM > deepest:
                    deepest, deepest_pair = -c.dist / MM, f"{model.geom(c.geom1).name or model.body(model.geom_bodyid[c.geom1]).name}/{model.geom(c.geom2).name or model.body(model.geom_bodyid[c.geom2]).name}"
        p = data.qpos[qa[:, None] + np.arange(3)] / MM
        r = np.hypot(p[:, 0], p[:, 1])
        entered |= r < R  # a dumped case starts outside the bowl, on the gravity line down to its spot
        out = ((p[:, 2] < z.deck_top) | (r > R + cfg.body.wall_t + 2)) & entered
        for i in np.flatnonzero(out):
            ang = math.degrees(math.atan2(above[i, 1], above[i, 0]))
            ra = math.hypot(above[i, 0], above[i, 1])
            inside = abs((ang - EXIT + 180) % 360 - 180) <= half + travel and r0 - 1 <= ra <= r1 + 1
            if r[i] > R + cfg.body.wall_t + 2:
                m["spilled"] += 1
                spilled_at.append(f"{ang:.0f}@{above[i, 2]:.0f}")
            elif counting:
                if not inside:
                    m["lost"] += 1
                    lost_at.append(f"{ang:.0f}@{ra:.0f}")
                else:
                    mat = np.zeros(9)
                    mujoco.mju_quat2Mat(mat, data.qpos[qa[i] + 3:qa[i] + 7])
                    up = mat[8]  # case axis (base to mouth) on the plate axis
                    m["exits"] += 1
                    m["base_down" if up > 0.5 else "mouth_down" if up < -0.5 else "sideways"] += 1
            if not respawn(i) and counting:
                m["overfill"] += 1
        above = data.qpos[qa[:, None] + np.arange(3)] / MM  # every case is above the deck now, respawned ones too
    wall = time.time() - t0
    counted = total - warm
    turns = abs(data.qpos[hinge_q] - turn0) / (2 * math.pi)  # measured: the velocity drive droops a little at low rpm
    passes = round(turns * layout.pocket_count(cfg))
    lo, hi = wilson(m["base_down"], passes)
    wrong = m["mouth_down"] + m["sideways"]
    tq = np.array(torque) if torque else np.zeros(1)
    slip = sc.slip_torque(cfg.clutch.springs_fitted, cfg.clutch.friction_mu[0], cfg)
    return dict(
        valid=m["lost"] == 0, plate=cfg.case_plate.caliber, case=case or "", start=start, tilt=tilt, rpm=rpm, cases=n_cases, extender=extender, com_ratio=com_ratio if com_ratio is not None else s.com_ratio,
        mu=mu if mu is not None else cfg.case_plate.drag_mu, seed=seed, turns=round(turns, 2), **m,
        cases_per_h=round(m["base_down"] / counted * 3600, 1), fill=round(m["base_down"] / passes, 4) if passes else 0.0,
        fill_lo=round(lo, 4), fill_hi=round(hi, 4),
        wrong_upper=round((3 / m["exits"] if m["exits"] else 1.0) if wrong == 0 else wilson(wrong, m["exits"])[1], 4),
        torque_mean=round(float(tq.mean()), 3), torque_p95=round(float(np.percentile(tq, 95)), 3), torque_max=round(float(tq.max()), 3),
        slip_share=round(float(np.mean(tq > slip)), 4), speed_ratio=round(float(np.mean(speed)) / w, 3) if speed else 0.0,
        deepest_mm=round(deepest, 2), deepest_pair=deepest_pair, deep_share=round(deep_checks / max(1, len(torque)), 4),
        lost_at=" ".join(lost_at), spilled_at=" ".join(spilled_at[:50]), rtf=round(total / wall, 3),
    )
