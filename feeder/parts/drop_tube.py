"""Drop tube: continues the exit insert's spigot to a clear PVC hose, with a port for a tube-full sensor.

- Bayonet socket over the spigot (fit `print.fit`): each of the spigot's two lugs enters an axial slot from the mouth,
  turns `twist` along a groove and drops `lock_lift` into a notch at the stop. The stop fixes the sensor window; the
  tube hangs on the notch floor, so gravity and hose pull hold it, and lifting the tube out of the notch turns it off.
  A stop shoulder at the spigot end closes the socket.
- Straight section with the sensor boss. The sensor sits in a plate between two M18x1 lock nuts: the
  inner nut in a slot loaded from the side, the outer nut on the plate. A `window_t` wall closes the bore.
- Barb for the hose, the bore of the tube continues through it.

Frame: print orientation, socket mouth on the bed at z = 0, +z along the case path, sensor on +x, the wide lug's
slot on +x. `placement` puts it on the body's spigot (hanging in the notch). The inner diameter never shrinks along
the path: spigot bore, tube bore (wider by two fits), hose.
"""

from dataclasses import dataclass

import math

from build123d import Align, Axis, Box, Cone, Cylinder, Location, Part, Plane, Polygon, Pos, Rot, extrude, revolve

from feeder.config import CFG, Config
from feeder.lib.cache import per_config
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
    r_groove: float  # outer wall of the slots, groove and notch
    floor_z: float  # groove floor at the lug root radius, the lug hangs `lock_lift` below it in the notch
    roof_z: float  # top of the groove at its outer wall


def dims(cfg: Config = CFG) -> Dims:
    e, d, f = cfg.exit, cfg.drop_tube, cfg.print.fit
    r_spigot = body.bore_d(cfg) / 2 + e.wall
    r_socket = r_spigot + f
    r_groove = r_spigot + d.lug_h + f
    floor_z = d.lug_z + d.lock_lift
    depth = e.spigot_len + f + d.lock_lift  # the tube hangs `lock_lift` + a fit off the shoulder
    socket_top = depth + e.wall
    r_bore = body.bore_d(cfg) / 2 + f
    window_x = r_bore + d.window_t
    slot_h = d.nut_t + 2 * f
    plate_x = window_x + slot_h + d.plate_t
    half_h = d.nut_af / 2 + cfg.fasteners.head_fit + d.boss_wall
    sensor_z = socket_top + half_h + (plate_x - r_bore)  # the 45 deg underside of the boss starts at the socket top
    boss_top = sensor_z + half_h
    return Dims(
        r_spigot=r_spigot,
        r_socket=r_socket,
        r_socket_out=r_groove + e.wall,
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
        tip=math.ceil(max(boss_top + d.barb_len, sensor_z + layout.caliber(cfg).case_length + d.sensor_margin) * 10) / 10,  # long cases: longer tube under the barb, up to the next 0.1 mm so rounding never eats the sensor margin
        r_groove=r_groove,
        floor_z=floor_z,
        roof_z=floor_z + d.lug_h + d.lug_tip + 2 * f,
    )


def bore_profile(cfg: Config = CFG) -> list[tuple[float, float]]:
    """(z where it starts, inner diameter) along the case path: spigot bore, tube bore, hose."""
    k = dims(cfg)
    return [(0.0, body.bore_d(cfg)), (k.depth, 2 * k.r_bore), (k.tip, cfg.drop_tube.hose_id)]


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


def _plan(angle: float, length: float, width: float) -> Part:
    """Tall slab along the azimuth `angle` deg from the axis, `width` across."""
    return Rot(Z=angle) * Box(length, width, 40, align=(Align.MIN, Align.CENTER, Align.CENTER))


def slot_angles(cfg: Config = CFG) -> tuple[float, float]:
    """(slot azimuth, stop azimuth) of the wide lug's L slot in the tube frame, deg. The narrow lug's lies 180 deg on."""
    return cfg.drop_tube.twist_dir * cfg.drop_tube.twist, 0.0


def _bayonet(k: Dims, cfg: Config) -> Part:
    """What the socket wall gives up for the lugs: per lug an axial slot from the mouth, a groove over the twist with a
    45 deg floor and a 45 deg roof (both print without support) and a notch below the floor at the stop. The
    groove is the lug's underside and top shifted over the lug's travel, one fit of play all round."""
    d, f = cfg.drop_tube, cfg.print.fit
    r_in, r_out = k.r_socket - 0.3, k.r_groove
    zf = k.floor_z
    pts = [(r_in, zf + r_in - k.r_spigot), (r_out, zf + r_out - k.r_spigot), (r_out, k.roof_z), (r_in, k.roof_z + r_out - r_in)]
    ring = revolve(Plane.XZ * Polygon(*pts, align=None), axis=Axis.Z)
    notch = Pos(0, 0, -d.lock_lift) * ring
    far = 2 * r_out
    cut = None
    for turn, w in zip((0, 180), d.lug_w):
        a_in, a_stop = (a + turn for a in slot_angles(cfg))
        wc = w + 2 * f
        rays = [(far * math.cos(math.radians(a)), far * math.sin(math.radians(a))) for a in (a_in, a_stop)]
        sweep = extrude(Polygon((0, 0), *rays, align=None), 20, both=True)
        plan = sweep + _plan(a_in, far, wc) + _plan(a_stop, far, wc)
        slot = Pos(0, 0, -1) * Cylinder(r_out, k.roof_z + 1, align=BOTTOM) & _plan(a_in, far, wc)
        piece = (ring & plan) + (notch & _plan(a_stop, far, wc)) + slot
        cut = piece if cut is None else cut + piece
    return cut


@per_config
def drop_tube(cfg: Config = CFG) -> Part:
    d, f = cfg.drop_tube, cfg.print.fit
    k = dims(cfg)
    part = Cylinder(k.r_socket_out, k.socket_top, align=BOTTOM)
    part += Cylinder(k.r_tube, k.tip - d.barb_len, align=BOTTOM)
    part += _boss(k, cfg)
    part += _barb(k, cfg)

    part -= Cylinder(k.r_socket, k.depth, align=BOTTOM)
    part -= Pos(0, 0, k.depth) * Cone(k.r_socket, k.r_bore, k.r_socket - k.r_bore, align=BOTTOM)  # 45 deg stop shoulder, prints without supports
    part -= Pos(0, 0, k.depth - 1) * Cylinder(k.r_bore, k.tip - k.depth + 2, align=BOTTOM)
    nut_slot = Box(k.slot_h, 2 * k.half_h + 2, d.nut_af + 2 * cfg.fasteners.head_fit, align=(Align.MIN, Align.CENTER, Align.CENTER))
    part -= Pos(k.window_x, 0, k.sensor_z) * nut_slot
    roof = d.nut_af / 2 - cfg.print.min_wall  # teardrop cut flat inside the nut flats, the nut covers the whole hole
    r = d.sensor_hole_d / 2
    hole = teardrop(d.sensor_hole_d, d.plate_t + 2) & Pos(0, 0, -r) * Box(d.plate_t + 2, 2 * r, r + roof, align=(Align.MIN, Align.CENTER, Align.MIN))
    part -= Pos(k.window_x + k.slot_h - 1, 0, k.sensor_z) * hole
    part -= _bayonet(k, cfg)
    return part


PARTS = {"drop_tube": drop_tube}
