"""Tilt mount: yoke on the body inserts, tube clamp, M10 pivot, a tilt link pinned at both ends.

- Yoke: plate bolted to the 4 M5 inserts in the body's bottom plane (ISO 4762 from below), two ears that carry
  the M10 pivot (axis parallel to x, below the plane) and a fork on the low side for link pin A.
- Clamp: one-piece slit clamp on a vertical tube (round or square) with a closed top as tube stop, a tongue
  between the yoke ears on the pivot and a fork on the low side of the block for link pin B.
- Tilt link between pins A and B (ISO 4762 M6 with DIN 985 nuts): pivot, A and B form a triangle, so the body
  is held both ways and cannot lift off. Adjustable: two printed rod ends on an M6 threaded rod (DIN 976-1),
  the adjust end between two nuts (stepless over `tilt_range`), the fixed end on a captive nut and a jam nut.
  Fixed: one printed link per angle in `fixed_tilts`, same pins.
- Pivot hardware: ISO 4017 M10, 2 washers (ISO 7089, same sizes as DIN 125 A), DIN 985 nut.

Gravity turns the body toward a steeper tilt at every tilt of the range (centre of mass on the low side of the
pivot), so the link is always in compression and the pin play sits on one side.
The yoke is modelled in print orientation (mating face on the bed), the clamp upright (block bottom on the bed),
links and rod ends flat (pin axis along z, link axis along +y from pin A at the origin). `yoke_in_body`,
`clamp_in_body` and `link_in_body` place them in the body frame.
"""

import math

from build123d import Box, Circle, Cylinder, Location, Part, Plane, Polygon, Pos, Rectangle, Rot, Vector, extrude

from feeder.config import CFG, Config
from feeder.lib.cache import per_config
from feeder.lib import fasteners
from feeder.lib.features import teardrop
from feeder.parts import body as body_part
from feeder.parts import layout
from feeder.parts import slip_clutch as sc

BOTTOM = sc.BOTTOM
G = layout.G
YZ = Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))  # local (x, y, z) = world (y, z, x)


def _rot(y: float, z: float, deg: float) -> tuple[float, float]:
    a = math.radians(deg)
    return y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)


def _pitch(size: str, cfg: Config) -> float:
    return cfg.fasteners.coarse_pitch[size]


def ear_r(cfg: Config = CFG) -> float:
    """Yoke ear end radius: the pivot washer fits inside it."""
    return fasteners.washer_data(cfg.mount.pivot_size)["d2"] / 2


def pivot_d(cfg: Config = CFG) -> float:
    return fasteners.clearance_d(cfg.mount.pivot_size, "Close")


def ear_gap(cfg: Config = CFG) -> float:
    """Slot between the ears: tongue plus an axial gap of 2 fits at each side."""
    return cfg.mount.tongue_t + 4 * cfg.print.fit


def pivot_point(cfg: Config = CFG) -> tuple[float, float]:
    """(y, z) of the pivot axis in the body frame."""
    return cfg.mount.pivot_y, layout.levels(cfg).bottom - cfg.mount.pivot_depth


def underside_to_pivot(cfg: Config = CFG) -> float:
    return cfg.mount.pivot_depth - cfg.mount.yoke_t


def tilt_span(cfg: Config = CFG) -> tuple[float, float]:
    """Tilt range plus margin, deg."""
    lo, hi = cfg.mount.tilt_range
    return lo - cfg.mount.tilt_margin, hi + cfg.mount.tilt_margin


def pivot_bolt_length(cfg: Config = CFG) -> float:
    """ISO 4017 length: washer, ear, tongue with gaps, ear, washer, nylon nut and one pitch beyond it."""
    mt = cfg.mount
    h = fasteners.washer_data(mt.pivot_size)["h"]
    stack = 2 * h + 2 * mt.ear_t + ear_gap(cfg) + mt.pivot_nut_h + _pitch(mt.pivot_size, cfg)
    return fasteners.pick_length(fasteners.hex_screw_lengths(mt.pivot_size), stack)


def yoke_cb_depth(cfg: Config = CFG) -> float:
    return fasteners.socket_screw(cfg.mount.bolt_size, 10).screw_data["k"] + cfg.fasteners.head_fit


def yoke_bolt_length(cfg: Config = CFG) -> float:
    """ISO 4762 length: through the plate under the head, then at least min_engagement x d into the insert."""
    mt = cfg.mount
    need = mt.yoke_t - yoke_cb_depth(cfg) + cfg.fasteners.min_engagement * fasteners.nominal_d(mt.bolt_size)
    return fasteners.pick_length(fasteners.socket_screw_lengths(mt.bolt_size), need)


def bore(cfg: Config = CFG) -> float:
    """Clamp bore diameter or side."""
    return cfg.mount.tube_d + 2 * cfg.print.fit


def clamp_width(cfg: Config = CFG) -> float:
    return bore(cfg) + 2 * cfg.mount.clamp_wall


def clamp_cb_depth(cfg: Config = CFG) -> float:
    """Counterbore for the head on an ISO 7089 washer, the washer spreads the clamp load on the plastic."""
    size = cfg.mount.clamp_size
    return fasteners.socket_screw(size, 20).screw_data["k"] + fasteners.washer_data(size)["h"] + cfg.fasteners.head_fit


def clamp_bolt_length(cfg: Config = CFG) -> float:
    """ISO 4762 length: from the head seat on the washer across the clamp, nut recessed flush, one pitch beyond it."""
    mt = cfg.mount
    need = clamp_width(cfg) - clamp_cb_depth(cfg) + fasteners.washer_data(mt.clamp_size)["h"] + _pitch(mt.clamp_size, cfg)
    return fasteners.pick_length(fasteners.socket_screw_lengths(mt.clamp_size), need)


def _nut_corner_r(size: str, cfg: Config) -> float:
    return (fasteners.nut_data(size)["s"] + 2 * cfg.fasteners.head_fit) / math.sqrt(3)


# statics ---------------------------------------------------------------------------------------------------


def com(cfg: Config = CFG) -> tuple[float, float]:
    """Centre of mass (y, z), body frame: on the shaft axis at the plate top."""
    return 0.0, layout.levels(cfg).plate_top


def weight_arm(tilt: float, cfg: Config = CFG) -> float:
    """Horizontal distance mm from the pivot to the centre of mass, + toward the high side."""
    (py, pz), (cy, cz) = pivot_point(cfg), com(cfg)
    return _rot(cy - py, cz - pz, tilt)[0]


def weight_moment(tilt: float, cfg: Config = CFG) -> float:
    """Nm of the weight about the pivot, + turns the body toward a flatter tilt, - toward a steeper one."""
    return cfg.mount.body_mass * G * weight_arm(tilt, cfg) / 1000


# tilt link. Pin A in the body frame rel. pivot, pin B in the clamp (world) frame rel. pivot ---------------------


def pin_a(tilt: float, cfg: Config = CFG) -> tuple[float, float]:
    """Pin A, world (y, z) rel. pivot at `tilt`."""
    return _rot(*cfg.mount.link_a, tilt)


def link_length(tilt: float, cfg: Config = CFG) -> float:
    """Pin to pin, mm. Shorter at a steeper tilt."""
    (ay, az), (by, bz) = pin_a(tilt, cfg), cfg.mount.link_b
    return math.hypot(ay - by, az - bz)


def link_lever(tilt: float, cfg: Config = CFG) -> float:
    """mm from the pivot to the link line."""
    (ay, az), (by, bz) = pin_a(tilt, cfg), cfg.mount.link_b
    return abs(ay * bz - az * by) / link_length(tilt, cfg)


def link_force(tilt: float, cfg: Config = CFG) -> float:
    """N along the link from the weight moment."""
    return abs(weight_moment(tilt, cfg)) * 1000 / link_lever(tilt, cfg)


def link_pin_d(cfg: Config = CFG) -> float:
    return fasteners.clearance_d(cfg.mount.link_pin_size, "Close")


def link_w(cfg: Config = CFG) -> float:
    """Link and rod end width: the rod end window takes a turning nut, with two walls each side."""
    n = fasteners.nut_data(cfg.mount.link_rod_size)
    return 2 * n["s"] / math.sqrt(3) + 2 * cfg.print.fit + 4 * cfg.print.min_wall


def link_gap(cfg: Config = CFG) -> float:
    """Slot between the fork ears: link plus an axial gap of 2 fits at each side."""
    return cfg.mount.link_t + 4 * cfg.print.fit


def fork_r(cfg: Config = CFG) -> float:
    """Fork ear radius round a link pin: the clamp ears are 45 deg triangles with the pin this far from their tip,
    so the washer and a wall round the hole fit between the flanks."""
    return math.sqrt(2) * max(fasteners.washer_data(cfg.mount.link_pin_size)["d2"] / 2, link_pin_d(cfg) / 2 + cfg.print.min_wall)


def link_pin_length(cfg: Config = CFG) -> float:
    """ISO 4762 length: washer, ear, link with gaps, ear, washer, nylon nut and one pitch beyond it."""
    mt = cfg.mount
    size = mt.link_pin_size
    stack = 2 * fasteners.washer_data(size)["h"] + 2 * mt.ear_t + link_gap(cfg) + mt.link_nut_h + _pitch(size, cfg)
    return fasteners.pick_length(fasteners.socket_screw_lengths(size), stack)


def _nut_m(cfg: Config) -> float:
    return fasteners.nut_data(cfg.mount.link_rod_size)["m"]


def rod_end_dims(cfg: Config = CFG) -> dict:
    """Rod end lengths along the link from its pin: `window` start and length, `wall` thickness, `reach` to the
    wall outer face. Adjust end: two nuts on the rod either side of its wall, the window takes the inner nut and
    the rod travel over `tilt_range`. Fixed end: a captive nut in a pocket on the outer face, a jam nut inside."""
    mt, mw, f = cfg.mount, cfg.print.min_wall, cfg.print.fit
    m, p = _nut_m(cfg), _pitch(mt.link_rod_size, cfg)
    lo, hi = mt.tilt_range
    travel = link_length(lo, cfg) - link_length(hi, cfg)
    y0 = link_pin_d(cfg) / 2 + 2 * mw
    adjust = {"window": y0, "length": 2 * f + m + p + travel + 2 * f, "wall": mt.link_wall}
    fixed = {"window": y0, "length": 2 * f + m + p + 2 * f, "wall": m + 2 * mw}
    for d in (adjust, fixed):
        d["reach"] = d["window"] + d["length"] + d["wall"]
    return {"adjust": adjust, "fixed": fixed}


def link_min_length(cfg: Config = CFG) -> float:
    """Shortest pin to pin length of the adjustable link: both rod ends and the outer nut between them."""
    d = rod_end_dims(cfg)
    return d["adjust"]["reach"] + _nut_m(cfg) + 2 * cfg.print.fit + d["fixed"]["reach"]


def rod_length(cfg: Config = CFG) -> float:
    """DIN 976-1 threaded rod, cut to length: one pitch past the jam nut in the fixed end, one pitch past the inner
    nut of the adjust end at the longest link."""
    d = rod_end_dims(cfg)
    m, p = _nut_m(cfg), _pitch(cfg.mount.link_rod_size, cfg)
    gap = link_length(cfg.mount.tilt_range[0], cfg) - d["adjust"]["reach"] - d["fixed"]["reach"]
    return math.ceil(2 * (m + p) + d["fixed"]["wall"] + gap + d["adjust"]["wall"])


# placement ----------------------------------------------------------------------------------------------------


def yoke_frame(cfg: Config = CFG) -> Location:
    return Pos(0, 0, layout.levels(cfg).bottom) * Rot(Y=180)


def yoke_in_body(part: Part, cfg: Config = CFG) -> Part:
    return yoke_frame(cfg) * part


def clamp_pivot_z(cfg: Config = CFG) -> float:
    """Pivot height in the clamp frame (z = 0 at the block bottom): pin B sits a fork radius plus a wall above the
    block bottom."""
    return fork_r(cfg) + 2 * cfg.print.min_wall - cfg.mount.link_b[1]


def brace_top(cfg: Config = CFG) -> float:
    """Top of the tongue brace in the clamp frame: under the yoke ear circles with an axial gap of 2 fits."""
    return clamp_pivot_z(cfg) - ear_r(cfg) - 2 * cfg.print.fit


def clamp_frame(tilt: float, cfg: Config = CFG) -> Location:
    """Clamp frame in the body frame with the body tilted by `tilt` deg."""
    py, pz = pivot_point(cfg)
    return Pos(0, py, pz) * Rot(X=-tilt) * Pos(0, 0, -clamp_pivot_z(cfg))


def clamp_in_body(part: Part, tilt: float, cfg: Config = CFG) -> Part:
    return clamp_frame(tilt, cfg) * part


def link_pin_centres(tilt: float, cfg: Config = CFG) -> list[tuple[float, float]]:
    """(y, z) of pins A and B in the body frame at `tilt`, pin axes along x."""
    py, pz = pivot_point(cfg)
    ay, az = cfg.mount.link_a
    by, bz = _rot(*cfg.mount.link_b, -tilt)
    return [(py + ay, pz + az), (py + by, pz + bz)]


def link_frame(tilt: float, cfg: Config = CFG) -> Location:
    """Link frame (pin A at the origin, link along +y, pin axis z) between the pins at `tilt`, body frame."""
    (ay, az), (by, bz) = link_pin_centres(tilt, cfg)
    u = Vector(0, by - ay, bz - az).normalized()
    x = u.cross(Vector(1, 0, 0))
    return Plane(origin=(-cfg.mount.link_t / 2, ay, az), x_dir=x, z_dir=(1, 0, 0)).location


def link_in_body(part: Part, tilt: float, cfg: Config = CFG) -> Part:
    return link_frame(tilt, cfg) * part


# yoke ---------------------------------------------------------------------------------------------------------


def _fork(cfg: Config, y: float, height: float) -> Part:
    """Two ears at +-x for a link pin, from z = 0 up to the pin at `height`, at `y` (print frame)."""
    mt = cfg.mount
    r = fork_r(cfg)
    ex = link_gap(cfg) / 2 + mt.ear_t / 2
    out = None
    for sx in (-1, 1):
        ear = Pos(sx * ex, y, 0) * Box(mt.ear_t, 2 * r, height, align=BOTTOM) + Pos(sx * ex, y, height) * Rot(Y=90) * Cylinder(r, mt.ear_t)
        out = ear if out is None else out + ear
    return out


@per_config
def yoke(cfg: Config = CFG) -> Part:
    mt, mw = cfg.mount, cfg.print.min_wall
    py, _ = pivot_point(cfg)
    length = yoke_bolt_length(cfg)
    cb_r = fasteners.socket_screw(mt.bolt_size, length).screw_data["dk"] / 2 + cfg.fasteners.head_fit
    half_x = max(mt.bolt_x + cb_r + 2 * mw, link_gap(cfg) / 2 + mt.ear_t)
    ya = py + mt.link_a[0]
    y_hi, y_lo = py + ear_r(cfg), min(min(mt.bolt_y) - cb_r - 2 * mw, ya - fork_r(cfg))
    t = mt.yoke_t
    body = Pos(0, (y_hi + y_lo) / 2, 0) * Box(2 * half_x, y_hi - y_lo, t, align=BOTTOM)
    pz = mt.pivot_depth  # pivot height in print coordinates
    ex = ear_gap(cfg) / 2 + mt.ear_t / 2
    for sx in (-1, 1):
        ear = Pos(sx * ex, py, 0) * Box(mt.ear_t, 2 * ear_r(cfg), pz, align=BOTTOM)
        ear += Pos(sx * ex, py, pz) * Rot(Y=90) * Cylinder(ear_r(cfg), mt.ear_t)
        body += ear
    body -= Pos(-half_x, py, pz) * teardrop(pivot_d(cfg), 2 * half_x)
    za = mt.pivot_depth - mt.link_a[1]  # pin A height in print coordinates
    body += _fork(cfg, ya, za)
    body -= Pos(-half_x, ya, za) * teardrop(link_pin_d(cfg), 2 * half_x)
    for x, y in body_part.mount_bolts(cfg):  # a symmetric pattern, so the flip into the body frame keeps it
        body -= Pos(x, y, t) * fasteners.clearance_hole(mt.bolt_size, t)
        body -= Pos(x, y, t) * fasteners.socket_head_counterbore(mt.bolt_size, length, yoke_cb_depth(cfg))
    return body


# clamp --------------------------------------------------------------------------------------------------------


def clamp_layout(cfg: Config = CFG) -> dict:
    """y positions in the clamp frame (y = 0 on the tube axis and under the pivot). Screws and slit on +y, the
    fork for pin B on -y."""
    mt, mw = cfg.mount, cfg.print.min_wall
    b = bore(cfg)
    head_r = max(fasteners.socket_screw(mt.clamp_size, 20).screw_data["dk"], fasteners.washer_data(mt.clamp_size)["d2"]) / 2
    cb_r = head_r + cfg.fasteners.head_fit
    screw_r = max(cb_r, _nut_corner_r(mt.clamp_size, cfg))
    y_s = b / 2 + cb_r + 2 * mw
    return {"y_min": -(b / 2 + mt.clamp_wall), "y_s": y_s, "y_max": y_s + screw_r + 2 * mw, "cb_r": cb_r}


def clamp_screw_z(cfg: Config = CFG) -> list[float]:
    mt = cfg.mount
    return [mt.clamp_h * (i + 0.5) / mt.clamp_screws for i in range(mt.clamp_screws)]


def clamp_nut_pocket(z: float, cfg: Config = CFG) -> Location:
    """Nut pocket mouth on the +x face of the clamp, a flat up, +z out of the pocket."""
    return Pos(clamp_width(cfg) / 2, clamp_layout(cfg)["y_s"], z) * Rot(Y=90) * Rot(Z=90)


@per_config
def clamp(cfg: Config = CFG) -> Part:
    mt = cfg.mount
    L = clamp_layout(cfg)
    h, w, cap = mt.clamp_h, clamp_width(cfg), mt.clamp_wall
    body = Pos(0, (L["y_min"] + L["y_max"]) / 2, 0) * Box(w, L["y_max"] - L["y_min"], h, align=BOTTOM)
    # tongue: stem, round end on the pivot
    zp, tw = clamp_pivot_z(cfg), mt.tongue_w
    body += Pos(0, 0, h) * Box(mt.tongue_t, tw, zp - h, align=BOTTOM)
    body += Pos(0, 0, zp) * Rot(Y=90) * Cylinder(tw / 2, mt.tongue_t)
    # brace: a web from the block edges up the stem's x faces, below the yoke ears, against a sideways push
    web = Polygon((-w / 2, h), (w / 2, h), (mt.tongue_t / 2, brace_top(cfg)), (-mt.tongue_t / 2, brace_top(cfg)), align=None)
    body += extrude(Plane.XZ * web, tw / 2, both=True)
    body -= Pos(-w, 0, zp) * teardrop(pivot_d(cfg), 2 * w)
    # fork for pin B on the -y face: 45 deg flanks above and below the pin, so the ears print upright
    yb, zb = mt.link_b[0], zp + mt.link_b[1]
    r, yf = fork_r(cfg), L["y_min"] + 1
    reach = yf - (yb - r)
    ear = Polygon((yf, zb + reach), (yb - r, zb), (yf, zb - reach), align=None)
    ex = link_gap(cfg) / 2 + mt.ear_t / 2
    for sx in (-1, 1):
        body += Pos(sx * ex, 0, 0) * (YZ * extrude(ear, mt.ear_t / 2, both=True)) & Box(1000, 1000, h, align=BOTTOM)  # both: the side does not depend on the winding
    body -= Pos(-w, yb, zb) * teardrop(link_pin_d(cfg), 2 * w)
    return body - tube_clamp_cuts(h, cap, clamp_screw_z(cfg), cfg)


def tube_clamp_cuts(h: float, cap: float, screw_z: list[float], cfg: Config = CFG, top_down: bool = False) -> Part:
    """What a slit tube clamp `h` tall on z = 0 cuts: the tube bore (closed `cap` at the top, through if 0), the
    slit on the +y side and the clamp screws along x at `screw_z` (head counterbore at -x, nut pocket at +x with a
    flat up). `top_down`: hole roofs point -z, for a part that prints top down."""
    mt = cfg.mount
    L, b, w = clamp_layout(cfg), bore(cfg), clamp_width(cfg)
    bore_h = h - cap + 1 if cap else h + 2
    out = Pos(0, 0, -1) * (Cylinder(b / 2, bore_h, align=BOTTOM) if mt.tube_shape == "round" else Box(b, b, bore_h, align=BOTTOM))
    out += Pos(0, (L["y_max"] + 1) / 2, -1) * Box(mt.clamp_slit, L["y_max"] + 1, bore_h, align=BOTTOM)
    out += Pos(0, (L["y_max"] + 1 + b / 2) / 2, -1) * Box(mt.clamp_slit, L["y_max"] + 1 - b / 2, h + 2, align=BOTTOM)
    roof = Rot(X=180) if top_down else Pos()
    for z in screw_z:
        out += Pos(-w / 2, L["y_s"], z) * roof * teardrop(fasteners.clearance_d(mt.clamp_size), w)
        out += Pos(-w / 2, L["y_s"], z) * roof * teardrop(2 * L["cb_r"], clamp_cb_depth(cfg))
        out += clamp_nut_pocket(z, cfg) * fasteners.nut_pocket(mt.clamp_size)
    return out


# links --------------------------------------------------------------------------------------------------------


def _bar(cfg: Config, length: float) -> Part:
    """Flat bar from the pin at the origin along +y, round end at the pin, thickness `link_t`."""
    w = link_w(cfg)
    return extrude(Circle(w / 2) + Pos(0, length / 2) * Rectangle(w, length), cfg.mount.link_t)


@per_config
def fixed_link(tilt: float, cfg: Config = CFG) -> Part:
    """Printed link for one tilt: two pin holes `link_length(tilt)` apart, round ends."""
    L = link_length(tilt, cfg)
    t = cfg.mount.link_t
    body = _bar(cfg, L) + Pos(0, L, 0) * extrude(Circle(link_w(cfg) / 2), t)
    for y in (0.0, L):
        body -= Pos(0, y, 0) * Cylinder(link_pin_d(cfg) / 2, t, align=BOTTOM)
    return body


def _rod_end(cfg: Config, kind: str) -> Part:
    mt, f = cfg.mount, cfg.print.fit
    d = rod_end_dims(cfg)[kind]
    t = mt.link_t
    window_w = link_w(cfg) - 4 * cfg.print.min_wall
    body = _bar(cfg, d["reach"])
    body -= Cylinder(link_pin_d(cfg) / 2, t, align=BOTTOM)
    body -= Pos(0, d["window"] + d["length"] / 2, 0) * Box(window_w, d["length"], t, align=BOTTOM)
    body -= Pos(0, d["window"] + d["length"], t / 2) * Rot(Z=90) * teardrop(fasteners.clearance_d(mt.link_rod_size), d["wall"])
    if kind == "fixed":  # captive nut pocket in the outer face, a flat up: a short bridge, a corner up would leave 30 deg roof flanks
        body -= Pos(0, d["reach"], t / 2) * Rot(X=-90) * fasteners.nut_pocket(mt.link_rod_size)
    return body


@per_config
def rod_end_adjust(cfg: Config = CFG) -> Part:
    return _rod_end(cfg, "adjust")


@per_config
def rod_end_fixed(cfg: Config = CFG) -> Part:
    return _rod_end(cfg, "fixed")


@per_config
def adjustable_link(tilt: float, cfg: Config = CFG) -> Part:
    """Adjust end on pin A, fixed end on pin B (turned end for end), the rod between them, link frame."""
    L = link_length(tilt, cfg)
    d = rod_end_dims(cfg)
    t = cfg.mount.link_t
    fixed_end = Pos(0, L, 0) * Rot(Z=180) * rod_end_fixed(cfg)
    m, p = _nut_m(cfg), _pitch(cfg.mount.link_rod_size, cfg)
    y0 = L - d["fixed"]["window"] - d["fixed"]["length"] + m + p  # rod tip one pitch past the jam nut on the fixed end's wall
    rod = Pos(0, y0, t / 2) * Rot(X=90) * Cylinder(fasteners.nominal_d(cfg.mount.link_rod_size) / 2, rod_length(cfg), align=BOTTOM)
    return rod_end_adjust(cfg) + fixed_end + rod


def rod_nuts(tilt: float, cfg: Config = CFG) -> list[Location]:
    """The 4 nuts on the link rod, body frame at `tilt`, +z the side each nut goes on from: adjust end between two
    nuts on its wall, fixed end on the captive nut in its pocket and the jam nut inside its window."""
    d, t, L, m = rod_end_dims(cfg), cfg.mount.link_t, link_length(tilt, cfg), _nut_m(cfg)
    a, f = d["adjust"], d["fixed"]
    fixed_end = Pos(0, L, 0) * Rot(Z=180)
    local = [
        Pos(0, a["window"] + a["length"], t / 2) * Rot(X=90),  # inner nut, in the window
        Pos(0, a["reach"], t / 2) * Rot(X=-90),  # outer nut
        fixed_end * Pos(0, f["reach"], t / 2) * Rot(X=-90) * Pos(0, 0, -m),  # captive, in the pocket
        fixed_end * Pos(0, f["window"] + f["length"], t / 2) * Rot(X=90),  # jam nut
    ]
    return [link_frame(tilt, cfg) * loc for loc in local]


def parts(cfg: Config = CFG) -> dict:
    out = {"mount_yoke": yoke, "mount_clamp": clamp, "mount_rod_end_adjust": rod_end_adjust, "mount_rod_end_fixed": rod_end_fixed}
    for tilt in cfg.mount.fixed_tilts:
        out[f"mount_link_{tilt:.0f}"] = lambda cfg=cfg, tilt=tilt: fixed_link(tilt, cfg)
    return out


PARTS = parts(CFG)
