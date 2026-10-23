"""Base-down case plate.

Notches open to the rim carry the cases up to the exit. The track band closes them, so the pocket is measured
to the band. The plate is about as tall as a case's centre of mass is high: a base-down case sits low and rides
along, a mouth-down case sits high, tips at the tilt and falls back into the pile. A shallow pickup channel leads
from the centre into each pocket, broad half-round radial ribs stir the pile, two upright tabs beside the cap lift
the plate. The centre drops over the drive ring hex onto its flange and the cap clamps it
(`slip_clutch.plate_seat_cut`). `case_plate.notches` False gives closed round holes for an A/B test.

CSG only (cylinders, cones, boxes, booleans), so the plate can be ported to OpenSCAD.
Frame: z = 0 at the plate bottom, axis on the shaft. Print bottom down.
"""

import math

from build123d import Align, Box, Cone, Cylinder, Part, Pos, Rot

from feeder.config import CFG, Config
from feeder.parts import layout
from feeder.parts import slip_clutch as sc

BOTTOM = sc.BOTTOM


def pocket_angles(cfg: Config = CFG) -> list[float]:
    """Pocket centre angles, deg. Half a pitch off +y, so the exit sees a pocket edge, not a land."""
    n = layout.pocket_count(cfg)
    return [90 + 360 * (i + 0.5) / n for i in range(n)]


def _pocket(cfg: Config, h: float) -> Part:
    """Pocket at the origin, +x radially out: round hole with chamfers, open to the rim when notched."""
    cp = cfg.case_plate
    r, c, cb = layout.pocket_d(cfg) / 2, cp.top_chamfer, cp.bottom_chamfer
    tool = Cylinder(r, h, align=BOTTOM)
    tool += Pos(0, 0, h - c) * Cone(r, r + c, c, align=BOTTOM)
    tool += Cone(r + cb, r, cb, align=BOTTOM)
    if cp.notches:
        out = r + cp.wall_gap + 5  # past the plate rim
        tool += Box(out, 2 * r, h, align=(Align.MIN, Align.CENTER, Align.MIN))
        for sy in (-1, 1):  # 45 deg chamfers on the notch sides, top and bottom
            tool += Pos(out / 2, sy * r, h) * Rot(X=45) * Box(out, c * math.sqrt(2), c * math.sqrt(2))
            tool += Pos(out / 2, sy * r, 0) * Rot(X=45) * Box(out, cb * math.sqrt(2), cb * math.sqrt(2))
    return tool


def _channel(cfg: Config, h: float) -> Part:
    """Pickup channel at the pocket origin, +x radially out: floor `channel_depth` below the top face at the
    pocket centre, rising to the top face `channel_len` further in. Narrower than the pocket by 1, so its sides
    do not touch the pocket wall tangentially."""
    cp = cfg.case_plate
    slope = math.degrees(math.atan(cp.channel_depth / cp.channel_len))
    length = math.hypot(cp.channel_len, cp.channel_depth)
    box = Box(length, layout.pocket_d(cfg) - 1, 50, align=(Align.MAX, Align.CENTER, Align.MIN))
    return Pos(0, 0, h - cp.channel_depth) * Rot(Y=slope) * box


def _inner_r(cfg: Config) -> float:
    """Ribs and lift tabs start outside the cap recess."""
    return cfg.cap.d / 2 + cfg.plate_seat.cap_gap + cfg.print.min_wall


def _rib(cfg: Config, h: float) -> Part:
    """Half-round rib on the top face along +x, from outside the cap to the channels."""
    cp = cfg.case_plate
    r0 = _inner_r(cfg)
    r1 = layout.pocket_circle_r(cfg) - layout.pocket_d(cfg) / 2 - cp.channel_len - cp.top_chamfer
    rib = Pos(r0, 0, h + cp.rib_h - cp.rib_r) * Rot(Y=90) * Cylinder(cp.rib_r, r1 - r0, align=BOTTOM)
    return rib & Pos(0, 0, h - 1) * Box(1000, 1000, 100, align=BOTTOM)  # never below the top face less 1


def lift_tab_top(cfg: Config = CFG) -> float:
    """Lift tab top above the plate bottom: level with the cap top, so the tabs stand no higher than the cap."""
    z = sc.levels(cfg)
    return z.cap_top - z.plate_bottom


def _lift_tab(cfg: Config, h: float) -> Part:
    cp = cfg.case_plate
    return Pos(_inner_r(cfg), 0, h - 1) * Box(cp.lift_len, cp.lift_t, lift_tab_top(cfg) - h + 1, align=(Align.MIN, Align.CENTER, Align.MIN))


def plate(cfg: Config = CFG) -> Part:
    cp = cfg.case_plate
    h = layout.plate_h(cfg)
    r = layout.pocket_circle_r(cfg)
    body = Cylinder(layout.plate_r(cfg), h, align=BOTTOM)
    for k in range(cp.rib_count):
        body += Rot(Z=90 + 360 * (k + 0.5) / cp.rib_count) * _rib(cfg, h)
    for k in range(cp.lift_tabs):
        body += Rot(Z=90 + 360 * k / cp.lift_tabs) * _lift_tab(cfg, h)
    body -= sc.plate_seat_cut(h, cfg)
    for a in pocket_angles(cfg):
        tool = _pocket(cfg, h) + (_channel(cfg, h) if cp.channel_len else Part())
        body -= Rot(Z=a) * Pos(r, 0) * tool
    return body


PARTS = {f"case_plate_{CFG.case_plate.caliber}": plate}
