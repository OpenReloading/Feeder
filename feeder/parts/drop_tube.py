"""Drop tube: continues the exit insert's spigot to a clear PVC hose, with a port for a tube-full sensor.

- Socket over the spigot (fit `print.fit`) with a stop shoulder at the spigot end and one thumb screw into a
  heat-set insert pressing on the spigot, so the exit insert comes out with no tools.
- Straight section with the sensor boss. The sensor sits in a plate between two M18x1 lock nuts: the
  inner nut in a slot loaded from the side, the outer nut on the plate. A `window_t` wall closes the bore.
- Barb for the hose, the bore of the tube continues through it.

Frame: print orientation, socket mouth on the bed at z = 0, +z along the case path, sensor on +x, screw
boss on -x (the thumb screw head stays clear of the body bottom for the fingers). `placement` puts it on the
body's spigot. The inner diameter never shrinks along the path: spigot bore, tube bore (wider by two fits), hose.
"""

from dataclasses import dataclass  # noqa: I001

from build123d import Align, Box, Cone, Cylinder, Location, Part, Plane, Polygon, Pos, RegularPolygon, Rot, extrude

from feeder.config import CFG, Config
from feeder.lib.cache import per_config
from feeder.lib import fasteners
from feeder.lib.features import teardrop
from feeder.parts import body, layout
from feeder.parts import slip_clutch as sc

BOTTOM = sc.BOTTOM


@dataclass(frozen=True)
class Dims:
    r_spigot: float  # outer radius of the exit insert spigot
    r_socket: float  # socket inner radius
    r_socket_out: float
    depth: float  # socket cavity depth, spigot end butts on the shoulder
    socket_top: float
    r_bore: float  # tube bore radius
    r_tube: float
    r_barb: float  # barb tube outer radius
    window_x: float  # outer face of the window
    slot_h: float  # nut slot height along the sensor axis
    plate_x: float  # outer face of the sensor plate
    half_h: float  # boss half height and half width
    sensor_z: float
    boss_top: float
    tip: float  # outlet end
    screw_z: float
    screw_boss_t: float  # from the socket cavity wall to the boss face
    screw_boss_r: float


def dims(cfg: Config = CFG) -> Dims:
    e, d, f = cfg.exit, cfg.drop_tube, cfg.print.fit
    ins = cfg.fasteners.inserts[d.screw_size]
    r_spigot = body.bore_d(cfg) / 2 + e.wall
    r_socket = r_spigot + f
    depth = e.spigot_len + f
    socket_top = depth + e.wall
    r_bore = body.bore_d(cfg) / 2 + f
    window_x = r_bore + d.window_t
    slot_h = d.nut_t + 2 * f
    plate_x = window_x + slot_h + d.plate_t
    half_h = d.nut_af / 2 + cfg.fasteners.head_fit + d.boss_wall
    sensor_z = socket_top + half_h + (plate_x - r_bore)  # the 45 deg underside of the boss starts at the socket top
    boss_top = sensor_z + half_h
    boss_t = ins.hole_depth + cfg.print.min_wall / 2
    return Dims(
        r_spigot=r_spigot,
        r_socket=r_socket,
        r_socket_out=r_socket + e.wall,
        depth=depth,
        socket_top=socket_top,
        r_bore=r_bore,
        r_tube=r_bore + e.wall,
        r_barb=(d.hose_id + d.barb_grip) / 2,
        window_x=window_x,
        slot_h=slot_h,
        plate_x=plate_x,
        half_h=half_h,
        sensor_z=sensor_z,
        boss_top=boss_top,
        tip=max(boss_top + d.barb_len, sensor_z + layout.caliber(cfg).case_length + d.sensor_margin),  # long cases: longer tube under the barb
        screw_z=depth / 2,
        screw_boss_t=boss_t,
        screw_boss_r=(ins.hole_d / 2 + ins.min_wall) * 2**0.5,
    )


def bore_profile(cfg: Config = CFG) -> list[tuple[float, float]]:
    """(z where it starts, inner diameter) along the case path: spigot bore, tube bore, hose."""
    k = dims(cfg)
    return [(0.0, body.bore_d(cfg)), (k.depth, 2 * k.r_bore), (k.tip, cfg.drop_tube.hose_id)]


def screw_mouth(cfg: Config = CFG) -> Location:
    """Set screw insert mouth on the boss face, +z out of the hole, drop tube frame."""
    k = dims(cfg)
    return Pos(-k.r_socket - k.screw_boss_t, 0, k.screw_z) * Rot(Y=-90)


def sensor_frame(cfg: Config = CFG) -> Location:
    """Sensing face of the sensor against the window, body frame, +z out along the sensor axis (drop tube +x)."""
    return placement(cfg).location * Pos(dims(cfg).window_x, 0, dims(cfg).sensor_z) * Rot(Y=90)


def placement(cfg: Config = CFG) -> Plane:
    """Socket mouth on the start of the spigot, +z down the drop, sensor sideways (+x)."""
    o, d = body.outlet(cfg)
    return Plane(origin=o, x_dir=(1, 0, 0), z_dir=d)


def _boss(k: Dims, cfg: Config) -> Part:
    """From the axis out to the sensor plate, 45 deg undersides toward +x and toward the sides beyond the tube.
    Solid behind the window outside the bore, so the `window_t` wall is only as wide as the bore."""
    low = k.sensor_z - k.half_h - (k.plate_x - k.r_bore)
    pts = [(0, low), (k.r_bore, low), (k.plate_x, k.sensor_z - k.half_h), (k.plate_x, k.boss_top), (0, k.boss_top)]
    boss = extrude(Plane.XZ * Polygon(*pts, align=None), k.half_h, both=True)
    wing = low + k.half_h - k.r_tube
    sides = [(-k.r_tube, low), (k.r_tube, low), (k.half_h, wing), (k.half_h, k.boss_top), (-k.half_h, k.boss_top), (-k.half_h, wing)]
    return boss & extrude(Plane.YZ * Polygon(*sides, align=None), k.plate_x)


def _barb(k: Dims, cfg: Config) -> Part:
    d = cfg.drop_tube
    h, pitch = d.barb_ridge_h, d.barb_ridge_pitch
    solid = Pos(0, 0, k.tip - d.barb_len) * Cylinder(k.r_barb, d.barb_len, align=BOTTOM)
    for i in range(d.barb_ridges):
        top = k.tip - i * pitch
        solid += Pos(0, 0, top - (pitch - h)) * Cone(k.r_barb + h, k.r_barb, pitch - h, align=BOTTOM)
        solid += Pos(0, 0, top - pitch) * Cone(k.r_barb, k.r_barb + h, h, align=BOTTOM)
    return solid


@per_config
def drop_tube(cfg: Config = CFG) -> Part:
    d, f = cfg.drop_tube, cfg.print.fit  # noqa: F841
    k = dims(cfg)
    ins = cfg.fasteners.inserts[d.screw_size]
    part = Cylinder(k.r_socket_out, k.socket_top, align=BOTTOM)
    part += Cylinder(k.r_tube, k.tip - d.barb_len, align=BOTTOM)
    part += _boss(k, cfg)
    part += _barb(k, cfg)
    diamond = Plane(origin=(0, 0, k.screw_z), x_dir=(0, 1, 0), z_dir=(-1, 0, 0)) * RegularPolygon(k.screw_boss_r, 4)
    part += extrude(diamond, k.r_socket + k.screw_boss_t)

    part -= Cylinder(k.r_socket, k.depth, align=BOTTOM)
    part -= Pos(0, 0, k.depth) * Cone(k.r_socket, k.r_bore, k.r_socket - k.r_bore, align=BOTTOM)  # 45 deg stop shoulder, prints without supports
    part -= Pos(0, 0, k.depth - 1) * Cylinder(k.r_bore, k.tip - k.depth + 2, align=BOTTOM)
    nut_slot = Box(k.slot_h, 2 * k.half_h + 2, d.nut_af + 2 * cfg.fasteners.head_fit, align=(Align.MIN, Align.CENTER, Align.CENTER))
    part -= Pos(k.window_x, 0, k.sensor_z) * nut_slot
    roof = d.nut_af / 2 - cfg.print.min_wall  # teardrop cut flat inside the nut flats, the nut covers the whole hole
    r = d.sensor_hole_d / 2
    hole = teardrop(d.sensor_hole_d, d.plate_t + 2) & Pos(0, 0, -r) * Box(d.plate_t + 2, 2 * r, r + roof, align=(Align.MIN, Align.CENTER, Align.MIN))
    part -= Pos(k.window_x + k.slot_h - 1, 0, k.sensor_z) * hole
    part -= screw_mouth(cfg) * fasteners.insert_hole(d.screw_size)
    part -= screw_mouth(cfg) * Pos(0, 0, -ins.hole_depth) * fasteners.clearance_hole(d.screw_size, k.screw_boss_t - ins.hole_depth + 1)
    return part


PARTS = {"drop_tube": drop_tube}
