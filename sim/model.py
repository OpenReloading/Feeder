"""MuJoCo model of the feeder in the body frame (z up the plate axis, exit at +y), gravity tilted by `tilt`.

- Static: deck with the drop opening, band with its gap, gate in the gap, wall up to the slanted wall top, all
  boxes round the bowl (`sim.segments`).
- Plate: the printed plate's convex decomposition (CoACD, cached in build/sim/cache), so pockets, pickup channels,
  chamfers and ribs are the CAD's within about 1 mm, plus the cap. A hinge on z, driven by a velocity actuator.
- Cases: a capsule for case to case contacts, flat discs at both ends that only touch the feeder, so a case
  stands on its base or mouth. Centre of mass `sim.com_ratio` of the length from the base (local -z).
"""

import hashlib
import math
from pathlib import Path

import coacd
import numpy as np
from build123d import Align, Cylinder, Polygon, Pos, extrude

from feeder.config import CFG, Config
from feeder.parts import body as b
from feeder.parts import case_plate, layout
from feeder.parts import slip_clutch as sc

MM = 1e-3
EXIT = b.EXIT_ANGLE
CACHE = Path(__file__).parent.parent / "build" / "sim" / "cache"


def _decompose(part, threshold: float) -> list[tuple[np.ndarray, np.ndarray]]:
    """CoACD without its remesh: the CAD tessellation is already closed, and the remesh's voxel grid (50 per part)
    put hull bumps 1.3 mm above the plate top."""
    verts, tris = part.tessellate(0.05)
    return coacd.run_coacd(coacd.Mesh(np.array([(p.X, p.Y, p.Z) for p in verts]), np.array(tris)), threshold=threshold,
                           max_convex_hull=-1, preprocess_mode="off")


def _rotated(hulls: list, deg: float) -> list:
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    rot = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    return [(v @ rot.T, f) for v, f in hulls]


def plate_hulls(cfg: Config = CFG) -> list[tuple[np.ndarray, np.ndarray]]:
    """Convex hulls (vertices in mm, faces) of the plate, plate bottom at z = 0, cached by mesh and threshold.

    The pocket ring is decomposed one pitch at a time (a sector from pocket centre to pocket centre, so one whole
    land) and repeated, with its own threshold: in a whole-plate decomposition the hulls took the 1.5 mm pocket
    clearance and no case fitted a pocket."""
    pl = case_plate.plate(cfg)
    n, a0 = layout.pocket_count(cfg), case_plate.pocket_angles(cfg)[0]
    pitch = 360 / n
    r_cut = layout.pocket_circle_r(cfg) - layout.pocket_d(cfg) / 2 - 3
    big = 2 * layout.plate_r(cfg)
    h = pl.bounding_box().max.Z + 2
    inner = pl & Pos(0, 0, -1) * Cylinder(r_cut, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    ring = pl - inner
    wedge = extrude(Polygon((0, 0), (big * math.cos(math.radians(a0)), big * math.sin(math.radians(a0))),
                            (big * math.cos(math.radians(a0 + pitch)), big * math.sin(math.radians(a0 + pitch))), align=None), h)
    sector = ring & Pos(0, 0, -1) * wedge
    if abs(ring.volume - n * sector.volume) > 1e-3 * ring.volume:
        raise ValueError("pocket ring is not periodic: decompose the whole ring instead")
    t, tp = cfg.sim.hull_threshold, cfg.sim.pocket_hull_threshold
    key = hashlib.sha1(f"{pl.volume:.4f} {sector.volume:.4f} {inner.volume:.4f} {n} {t} {tp} off".encode()).hexdigest()[:16]
    path = CACHE / f"plate_{key}.npz"
    if not path.exists():
        land = _decompose(sector, tp)
        parts = _decompose(inner, t) + [hull for k in range(n) for hull in _rotated(land, k * pitch)]
        CACHE.mkdir(parents=True, exist_ok=True)
        np.savez(path, **{f"v{i}": pv for i, (pv, _) in enumerate(parts)}, **{f"f{i}": pf for i, (_, pf) in enumerate(parts)})
    data = np.load(path)
    return [(data[f"v{i}"], data[f"f{i}"]) for i in range(len(data.files) // 2)]


def _box(name: str, ra: float, rb: float, za: float, zb: float, ang: float, half: float, rgba: str) -> str:
    """Box over the annular sector ra..rb, za..zb at `ang` deg, `half` deg each way, wide enough to close at rb."""
    a = math.radians(ang)
    rm, hw = (ra + rb) / 2, rb * math.sin(math.radians(half)) + 0.2
    return (f'<geom name="{name}" type="box" size="{(rb - ra) / 2 * MM} {hw * MM} {(zb - za) / 2 * MM}" '
            f'pos="{rm * math.cos(a) * MM} {rm * math.sin(a) * MM} {(za + zb) / 2 * MM}" euler="0 0 {ang}" rgba="{rgba}"/>')


def _off(ang: float) -> float:
    return abs((ang - EXIT + 180) % 360 - 180)


def opening(cfg: Config = CFG) -> tuple[float, float, float]:
    """Drop opening as (half angle deg, inner r, outer r), mm."""
    length, r0, r1 = b.opening(cfg)
    return math.degrees(length / 2 / layout.pocket_circle_r(cfg)), r0, r1


def wall_top(y: float, extender: bool, cfg: Config = CFG) -> float:
    """Wall top at `y`, raised by the wall extender (its top falls at the wall slant from `extender_h` above the
    full wall top)."""
    top = b.wall_top_at(y, cfg)
    if not extender:
        return top
    z, R = layout.levels(cfg), layout.bowl_r(cfg)
    return max(top, z.wall_top + cfg.body.extender_h - (y + R) * math.tan(math.radians(b.wall_slant(cfg))))


def mjcf(tilt: float, n_cases: int, cfg: Config = CFG, com_ratio: float | None = None, mu: float | None = None,
         extender: bool = False, case: str | None = None) -> str:
    s, cp = cfg.sim, cfg.case_plate
    com_ratio = s.com_ratio if com_ratio is None else com_ratio
    mu = cp.drag_mu if mu is None else mu
    z, R = layout.levels(cfg), layout.bowl_r(cfg)
    r_band, band_top = layout.band_inner_r(cfg), b.band_top(cfg)
    a_in = b._gap_angles(cfg)[0]
    half, r0, r1 = opening(cfg)
    deck_t, step = cfg.body.deck_t, 360 / s.segments
    static = [f'<geom name="deck_in" type="cylinder" size="{(r0 - 3) * MM} {deck_t / 2 * MM}" pos="0 0 {(z.deck_top - deck_t / 2) * MM}"/>']
    for i in range(s.segments):
        ang = (i + 0.5) * step
        static.append(_box(f"deck_a{i}", r0 - 3, r0, z.deck_top - deck_t, z.deck_top, ang, step / 2, "0.6 0.6 0.6 1"))
        if _off(ang) > half:
            static.append(_box(f"deck_b{i}", r0, r1, z.deck_top - deck_t, z.deck_top, ang, step / 2, "0.6 0.6 0.6 1"))
        static.append(_box(f"deck_c{i}", r1, R + 4, z.deck_top - deck_t, z.deck_top, ang, step / 2, "0.6 0.6 0.6 1"))
        if _off(ang) > a_in:
            static.append(_box(f"band{i}", r_band, R, z.deck_top, band_top, ang, step / 2, "0.85 0.5 0.2 1"))
        else:
            static.append(_box(f"gate{i}", r_band + cfg.track.gate_setback, R, z.deck_top, band_top, ang, step / 2, "0.66 0.55 0.88 1"))
        top = wall_top(R * math.sin(math.radians(ang)), extender, cfg)
        static.append(_box(f"wall{i}", R, R + cfg.body.wall_t, band_top, top, ang, step / 2, "0.7 0.7 0.7 0.15"))

    hulls = plate_hulls(cfg)
    assets = [f'<mesh name="h{i}" vertex="{" ".join(f"{c * MM:.6g}" for c in v.ravel())}" face="{" ".join(map(str, f.ravel()))}"/>'
              for i, (v, f) in enumerate(hulls)]
    zc = sc.levels(cfg)
    cap_a, cap_b = zc.cap_face - zc.floor_top, zc.cap_top - zc.floor_top
    plate = [f'<geom name="plate{i}" type="mesh" mesh="h{i}" pos="0 0 {z.plate_bottom * MM}" rgba="0.85 0.8 0.65 1"/>' for i in range(len(hulls))]
    plate.append(f'<geom name="cap" type="cylinder" size="{cfg.cap.d / 2 * MM} {(cap_b - cap_a) / 2 * MM}" pos="0 0 {(cap_a + cap_b) / 2 * MM}" rgba="0.2 0.45 0.6 1"/>')

    cal = cfg.calibers.table[case] if case else layout.caliber(cfg)
    rc, L, m = cal.rim_d / 2, cal.case_length, s.case_mass
    com = L / 2 - com_ratio * L  # below the middle, toward the base
    ixx, izz = m * (3 * (rc * MM) ** 2 + (L * MM) ** 2) / 12, m * (rc * MM) ** 2 / 2
    disc = 0.5  # disc half height
    cases = [f'<body name="c{i}" pos="0 0 {(1 + i) * MM * 30}"><freejoint/>'
             f'<inertial pos="0 0 {-com * MM}" mass="{m}" diaginertia="{ixx} {ixx} {izz}"/>'
             f'<geom class="case" type="capsule" size="{rc * MM} {(L / 2 - rc) * MM}"/>'
             f'<geom class="disc" type="cylinder" size="{(rc - 0.5) * MM} {disc * MM}" pos="0 0 {(L / 2 - disc) * MM}"/>'
             f'<geom class="disc" type="cylinder" size="{(rc - 0.5) * MM} {disc * MM}" pos="0 0 {(disc - L / 2) * MM}"/></body>'
             for i in range(n_cases)]
    g, t = 9.81, math.radians(tilt)
    nl = "\n"
    return f"""<mujoco model="feeder">
<option timestep="{s.timestep}" integrator="implicitfast" solver="PGS" iterations="{s.iterations}" tolerance="1e-5" gravity="0 {-g * math.sin(t)} {-g * math.cos(t)}"/>
<default>
  <geom friction="{mu} 0.005 0.0001" solref="{2.5 * s.timestep} 1" contype="1" conaffinity="3"/>
  <default class="case"><geom contype="1" conaffinity="1" rgba="0.8 0.65 0.3 1"/></default>
  <default class="disc"><geom contype="2" conaffinity="0" rgba="0.6 0.45 0.2 1"/></default>
</default>
<asset>{nl.join(assets)}</asset>
<worldbody>
{nl.join(static)}
<body name="plate"><joint name="hinge" type="hinge" axis="0 0 1"/>
<inertial pos="0 0 {z.plate_bottom * MM}" mass="0.3" diaginertia="0.002 0.002 0.004"/>
{nl.join(plate)}
</body>
{nl.join(cases)}
</worldbody>
<contact><exclude body1="world" body2="plate"/></contact>
<actuator><velocity name="drive" joint="hinge" kv="200"/></actuator>
</mujoco>"""
