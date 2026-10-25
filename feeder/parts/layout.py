"""Derived sizes and levels shared by the plate, body, track and exit.

Body frame: origin on the shaft axis at the cup floor top (the clutch's `floor_top`), +z up the shaft,
+y toward the exit, which is the high side when the feeder is tilted about x.
"""

import math
from dataclasses import dataclass, replace

from feeder.config import CFG, Caliber, Config
from feeder.lib import fasteners
from feeder.parts import slip_clutch as sc

G = 9.81  # m/s2


def calibers(cfg: Config = CFG) -> list[Caliber]:
    """The cases the plate takes: its group's, or the one case."""
    c = cfg.calibers
    return [c.table[k] for k in c.groups.get(cfg.case_plate.caliber, (cfg.case_plate.caliber,))]


def caliber(cfg: Config = CFG) -> Caliber:
    """The plate's envelope case: largest rim, thinnest rim, longest case."""
    cs = calibers(cfg)
    return Caliber(rim_d=max(c.rim_d for c in cs), rim_t_min=min(c.rim_t_min for c in cs), case_length=max(c.case_length for c in cs))


def plate_sets(cfg: Config = CFG) -> list[Config]:
    """One config per plate the body takes: the configured plate and every group. Body and band are sized
    for all of them, the plate, exit insert and drop tube belong to one."""
    names = dict.fromkeys((cfg.case_plate.caliber, *cfg.calibers.groups))
    return [replace(cfg, case_plate=replace(cfg.case_plate, caliber=n)) for n in names]


def check_orientation(cfg: Config = CFG) -> None:
    """Plate, exit insert and tilt are built for the (item, orient) in `case_plate.tilts` only."""
    cp = cfg.case_plate
    if (cp.item, cp.orient) not in cp.tilts:
        ok = ", ".join(f"{i}/{o}" for i, o in cp.tilts)
        raise ValueError(f"plate set {cp.caliber!r}: item/orient {cp.item}/{cp.orient} is not supported, supported: {ok}")


def tilt(cfg: Config = CFG) -> float:
    """Tilt preset of the plate set's item and orientation, deg from horizontal."""
    check_orientation(cfg)
    return cfg.case_plate.tilts[cfg.case_plate.item, cfg.case_plate.orient]


def bed_d(cfg: Config = CFG) -> float:
    """Largest round part that fits the bed."""
    p = cfg.printer
    return min(p.bed_x, p.bed_y) - 2 * p.margin


def bowl_r(cfg: Config = CFG) -> float:
    """Bowl inner radius. Split body: the band fills the bowl and must fit the bed. One piece: the wall must."""
    b = cfg.body
    return bed_d(cfg) / 2 - (b.wall_t if b.split == "one_piece" else 0)


def band_inner_r(cfg: Config = CFG) -> float:
    """Inner face of the track band, which closes the plate notches."""
    return bowl_r(cfg) - cfg.print.fit - cfg.track.band_t


def plate_r(cfg: Config = CFG) -> float:
    return band_inner_r(cfg) - cfg.case_plate.wall_gap


def pocket_d(cfg: Config = CFG) -> float:
    return caliber(cfg).rim_d + cfg.case_plate.pocket_clearance


def plate_h(cfg: Config = CFG) -> float:
    ls = [c.case_length for c in calibers(cfg)]
    best = 2 * cfg.case_plate.height_ratio / (1 / min(ls) + 1 / max(ls))  # equal ratio error for the shortest and longest
    return max(cfg.plate_seat.hub_h, best)


def pocket_circle_r(cfg: Config = CFG) -> float:
    """Notches: the pocket reaches the band. Holes: the plate rim stays outside."""
    cp = cfg.case_plate
    return (band_inner_r(cfg) if cp.notches else plate_r(cfg) - cp.rim_wall) - pocket_d(cfg) / 2


def pocket_count(cfg: Config = CFG) -> int:
    cp = cfg.case_plate
    return math.floor(2 * math.pi * pocket_circle_r(cfg) / (pocket_d(cfg) * cp.pocket_pitch))


def plate_drag_torque(cfg: Config = CFG) -> float:
    """Nm to turn the plate under the brass: the pile rests on the low side at about the pocket circle."""
    cp = cfg.case_plate
    return cp.drag_mu * cp.drag_mass * G * math.cos(math.radians(tilt(cfg))) * pocket_circle_r(cfg) / 1000


def cap_drag_torque(cfg: Config = CFG) -> float:
    """Nm the brass turns the cap with, an upper bound: the whole design fill rests on the cap wall at its rim radius,
    as `plate_drag_torque` has it rest on the plate at the pocket circle. It loosens the cap when the plate turns
    against the thread hand."""
    cp = cfg.case_plate
    return cp.drag_mu * cp.drag_mass * G * math.cos(math.radians(tilt(cfg))) * cfg.cap.d / 2 / 1000


def tipping_moment(tilt: float, cfg: Config = CFG) -> float:
    """Nm that tips the plate about the low edge of the ring flange: the brass normal load at the pocket circle.
    The plate weight, which resists, is left out."""
    cp = cfg.case_plate
    arm = pocket_circle_r(cfg) - cfg.drive_ring.flange_d / 2
    return cp.drag_mass * G * math.cos(math.radians(tilt)) * arm / 1000


def capacity(tilt: float, wall_h: float | None = None, cfg: Config = CFG, rim=None, rim_r=None) -> int:
    """Cases the bowl holds at `tilt` with brass level at the lowest the rim lets it stand: bowl volume under that level
    surface less the cap, over the case envelope at `case_plate.packing`. The rim is the body wall, `wall_h` above the
    plate top (default), level with its top on the low side; or `rim(ang)`, the rim top (z) at body-frame angle `ang` deg
    (`body.rim_top`), at radius `rim_r(ang)` (`body.rim_r`, default the bowl radius: a leaning extender edge sits
    further in): the surface then stands as high as no rim point is below it."""
    z = levels(cfg)
    tan = math.tan(math.radians(tilt))
    if rim is None:
        wall_h = z.wall_top - z.plate_top if wall_h is None else wall_h
        level = z.plate_top + wall_h - bowl_r(cfg) * tan  # level surface height at y = 0
    else:
        level = min(rim(a) + (rim_r(a) if rim_r else bowl_r(cfg)) * math.sin(math.radians(a)) * tan for a in range(360))
    R, cal, n = bowl_r(cfg), caliber(cfg), 200
    cap_r, cap_h = cfg.cap.d / 2, sc.levels(cfg).cap_top - sc.levels(cfg).plate_bottom - plate_h(cfg)
    step, vol = 2 * R / n, 0.0
    for i in range(n):
        for j in range(n):
            x, y = -R + (i + 0.5) * step, -R + (j + 0.5) * step
            if x * x + y * y < R * R:
                depth = max(0.0, level - y * tan - z.plate_top)
                vol += depth - (min(depth, cap_h) if x * x + y * y < cap_r ** 2 else 0.0)
    case = math.pi * (cal.rim_d / 2) ** 2 * cal.case_length
    return math.floor(vol * step * step * cfg.case_plate.packing / case)


def seat_drop(cfg: Config = CFG) -> float:
    """The plate sits this much below its nominal level when the ring cone fit takes up its clearance."""
    return cfg.print.fit / math.tan(math.radians(cfg.drive_ring.cone_half_angle))


@dataclass(frozen=True)
class Levels:
    bottom: float  # flat bottom plane of the body: cup floor bottom, rib and skirt ends
    floor_top: float  # cup floor top, z = 0
    deck_bottom: float
    deck_top: float  # case bases slide here
    plate_bottom: float
    plate_top: float
    wall_top: float


def levels(cfg: Config = CFG) -> Levels:
    z = sc.levels(cfg)
    t, b = cfg.track, cfg.body
    plate_bottom = z.plate_bottom - z.floor_top
    deck_top = plate_bottom - seat_drop(cfg) - t.gap
    plate_top = plate_bottom + plate_h(cfg)
    return Levels(
        bottom=-b.floor_t,
        floor_top=0.0,
        deck_bottom=deck_top - b.deck_t,
        deck_top=deck_top,
        plate_bottom=plate_bottom,
        plate_top=plate_top,
        wall_top=plate_bottom + b.wall_h,
    )


def motor_screws(cfg: Config = CFG) -> list[tuple[float, float]]:
    """(x, y) of the gearbox face screws in the body frame."""
    m = cfg.motor
    a = math.radians(m.angle)
    out = []
    for along in (-m.mount_near, m.mount_far):  # along the gearbox toward the can
        for across in (-m.mount_across / 2, m.mount_across / 2):
            out.append((along * math.cos(a) - across * math.sin(a), along * math.sin(a) + across * math.cos(a)))  # noqa: PERF401
    return out


def cup_r(cfg: Config = CFG) -> float:
    """Open cup around the clutch, wide enough to reach the motor screw heads from above and to clear the drive ring flange."""
    b = cfg.body
    carrier_r = sc.male_cone_r(sc.levels(cfg).base_top, cfg)
    length = fasteners.countersunk_screw_lengths(cfg.motor.mount_screw_size)[0]
    head_r = fasteners.countersunk_screw(cfg.motor.mount_screw_size, length).screw_data["dk"] / 2
    screw_r = max(math.hypot(x, y) for x, y in motor_screws(cfg)) + head_r
    return max(carrier_r, screw_r, cfg.drive_ring.flange_d / 2) + b.cup_clearance  # the ring flange turns over the cup
