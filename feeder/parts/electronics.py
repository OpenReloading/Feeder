"""Electronics box beside the stand tube, below the tilt clamp, its front toward the user (the low side).

- Box: upright, open at the front. Timer relay on standoffs with heat-set inserts on the back wall, motor and
  sensor sockets low in the side face away from the tube, heat-set inserts in the corner posts for the lid. The
  box has its own slit clamp on the tube, standing off its side wall, so there is no collar: the slit and the 2
  clamp screws at the back, heads outward, nuts toward the wall. `electronics_box` stands to the right of the
  tube as the user sees it, `electronics_box_left` is its mirror.
- Lid: front plate with the PWM knob (the PWM board hangs on its pot nut), toggle switch and DC jack in a column,
  screwed to the corner posts. The cables are long enough to open it. One lid fits both boxes.

Modelled in the box frame: x = 0 at the middle of the box, z = 0 at the box bottom, the front toward -y, the tube
at `tube_at`. `box_frame` puts the tube on the clamp axis. The box prints on its back wall, the lid flat.
"""

import math  # noqa: I001

from build123d import Box, Circle, Cylinder, Location, Part, Plane, Polygon, Pos, Rot, extrude

from feeder.config import CFG, Config, PanelPart
from feeder.lib import fasteners
from feeder.lib.cache import per_config
from feeder.lib.features import teardrop
from feeder.parts import mount
from feeder.parts.slip_clutch import BOTTOM


def height(cfg: Config = CFG) -> float:
    return cfg.electronics.box_inner[2] + 2 * cfg.electronics.box_wall


def box_frame(tilt: float, cfg: Config = CFG, left: bool = False) -> Location:
    """Box frame in the body frame: the box top `box_gap` below the tilt clamp, the tube of the box on the clamp axis."""
    tx, ty = tube_at(cfg)
    return mount.clamp_frame(tilt, cfg) * Pos(0, 0, -cfg.electronics.box_gap - height(cfg)) * Pos(tx if left else -tx, -ty, 0)


def outline(cfg: Config = CFG) -> dict:
    """Outer x half width of the box, y of its back face (`y1`, 0) and of its front rim (`y0`)."""
    e = cfg.electronics
    return {"x": e.box_inner[0] / 2 + e.box_wall, "y0": -e.box_wall - e.box_inner[1], "y1": 0.0}


def tube_gap(cfg: Config = CFG) -> float:
    """Gap between the clamp block and the side wall, where the clamp screws end beyond their nuts."""
    mt, w = cfg.mount, mount.clamp_width(cfg)
    tip = mount.clamp_bolt_length(cfg) - (w - mount.clamp_cb_depth(cfg) + fasteners.washer_data(mt.clamp_size)["h"])
    return math.ceil(tip) + 1


def tube_at(cfg: Config = CFG) -> tuple[float, float]:
    """(x, y) of the tube axis in the box frame of the right-hand box: the clamp block stands `tube_gap` off the side
    wall, its slit and screws toward the back, its rear flush with the back face of the box."""
    return -outline(cfg)["x"] - tube_gap(cfg) - mount.clamp_width(cfg) / 2, outline(cfg)["y1"] - mount.clamp_layout(cfg)["y_max"]


def tube_frame(cfg: Config = CFG) -> Location:
    """Clamp frame in the box frame: the same axes, so the slit and the screws are at the back."""
    tx, ty = tube_at(cfg)
    return Pos(tx, ty, 0)


def post_w(cfg: Config = CFG) -> float:
    ins = cfg.fasteners.inserts[cfg.electronics.lid_screw_size]
    return ins.od + 2 * ins.min_wall


def lid_screws(cfg: Config = CFG) -> list[tuple[float, float]]:
    """(x, z) of the lid screws, on the corner posts."""
    e, o = cfg.electronics, outline(cfg)
    c = e.box_wall + post_w(cfg) / 2
    return [(sx * (o["x"] - c), z) for sx in (-1, 1) for z in (c, height(cfg) - c)]


def lid_screw_length(cfg: Config = CFG) -> float:
    e = cfg.electronics
    return fasteners.pick_length(fasteners.socket_screw_lengths(e.lid_screw_size), e.lid_t + cfg.fasteners.min_engagement * fasteners.nominal_d(e.lid_screw_size))


def clamp_screw_z(cfg: Config = CFG) -> list[float]:
    """z of the clamp screws, in the clamp block at the top of the box."""
    h, n, c = height(cfg), cfg.mount.clamp_screws, cfg.electronics.clamp_h
    return [h - c + c * (i + 0.5) / n for i in range(n)]


def relay_screws(cfg: Config = CFG) -> list[tuple[float, float]]:
    """(x, z) of the relay standoffs, in the lower half of the box."""
    e = cfg.electronics
    hx, hz = e.relay_holes
    zc = e.box_wall + e.box_inner[2] / 4
    return [(sx * hx / 2, zc + sz * hz / 2) for sx in (-1, 1) for sz in (-1, 1)]


def relay_screw_length(cfg: Config = CFG) -> float:
    e = cfg.electronics
    return fasteners.pick_length(fasteners.socket_screw_lengths(e.lid_screw_size), e.relay_pcb_t + cfg.fasteners.min_engagement * fasteners.nominal_d(e.lid_screw_size))


def standoff_d(cfg: Config = CFG) -> float:
    return post_w(cfg)


def panel_holes(cfg: Config = CFG) -> list[tuple[str, float, Location]]:
    """(name, diameter, mouth) of each panel hole, +z of the mouth into the box: the lid column at x = 0 from the
    top down, the sockets side by side low in the +x face."""
    e, o = cfg.electronics, outline(cfg)
    iz, wt = e.box_inner[2], e.box_wall
    out = []
    for i, (name, d) in enumerate(e.front_holes):
        z = wt + iz * (1 - (i + 1) / (len(e.front_holes) + 1))
        out.append((name, d, Pos(0, o["y0"] - e.lid_t, z) * Rot(X=-90)))
    for i, (name, d) in enumerate(e.side_holes):
        y = o["y0"] + e.box_inner[1] * (i + 0.5) / len(e.side_holes)
        out.append((name, d, Pos(o["x"], y, wt + iz / 6) * Rot(Y=-90)))
    return out


def panel_fits(cfg: Config = CFG) -> list[tuple]:
    """(name, PanelPart, mouth, panel thickness) of each panel part, mouth as in `panel_holes`."""
    e = cfg.electronics
    parts = dict(e.panel_parts)
    return [(name, parts[name], loc, e.lid_t if i < len(e.front_holes) else e.box_wall) for i, (name, _, loc) in enumerate(panel_holes(cfg))]


def panel_envelope(pp: PanelPart) -> Part:
    """Envelope of a panel part in its panel frame (see `PanelPart`)."""
    bx, by, bl = pp.body
    shape = Cylinder(pp.thread_d / 2, pp.thread_l, align=BOTTOM) + Pos(0, 0, pp.thread_l) * Box(bx, by, bl, align=BOTTOM)
    fd, fh = pp.front
    return shape + Pos(0, 0, -fh) * Cylinder(fd / 2, fh, align=BOTTOM) if fh else shape


def pwm_board(cfg: Config = CFG) -> Part:
    """PWM controller envelope, box frame: centred on the knob, its front against the back of the potentiometer."""
    e = cfg.electronics
    _, pot, loc, _ = panel_fits(cfg)[0]
    w, h, d = e.pwm_board
    return loc * Pos(0, 0, pot.thread_l + pot.body[2]) * Box(w, h, d, align=BOTTOM)


def relay_board(cfg: Config = CFG) -> Part:
    """Timer relay envelope, box frame: the board on its standoffs, relay and terminals on its front."""
    e, o = cfg.electronics, outline(cfg)
    back = o["y1"] - e.box_wall - e.standoff_h
    zc = e.box_wall + e.box_inner[2] / 4
    w, h = e.relay_board
    px, pz, ph = e.relay_parts
    pcb = Pos(0, back - e.relay_pcb_t / 2, zc) * Box(w, e.relay_pcb_t, h)
    for x, z in relay_screws(cfg):  # mounting holes: the screws pass through the board
        pcb -= Pos(x, back + 1, z) * Rot(X=-90) * fasteners.clearance_hole(e.lid_screw_size, e.relay_pcb_t + 2)
    return pcb + Pos(0, back - e.relay_pcb_t - ph / 2, zc) * Box(px, ph, pz)


def _side_hole(d: float, depth: float) -> Part:
    """Socket hole along +z: teardrop roof toward -y (up when the box prints on its back wall), cut flat 1 above
    the circle, a bridge of 3 mm or less that the panel nut still covers."""
    hole = teardrop(d, depth) & Pos(depth / 2, 0, 0) * Box(depth, 2 * d, d + 2)
    return Rot(Y=-90) * Rot(X=90) * hole


def _roofed_bore(d: float, h: float) -> Part:
    """The tube bore with a 45 deg roof toward the front of the box (-y), which is up while the box prints on its back wall."""
    r = d / 2
    return extrude(Circle(r) + Polygon((r / math.sqrt(2), -r / math.sqrt(2)), (-r / math.sqrt(2), -r / math.sqrt(2)), (0, -r * math.sqrt(2)), align=None), h)


@per_config
def box(cfg: Config = CFG) -> Part:
    e, o = cfg.electronics, outline(cfg)
    h, wt, p = height(cfg), e.box_wall, post_w(cfg)
    ix, iy, iz = e.box_inner
    body = Pos(0, (o["y0"] + o["y1"]) / 2, 0) * Box(2 * o["x"], o["y1"] - o["y0"], h, align=BOTTOM)
    body -= Pos(0, o["y0"] - 1 + (iy + 1) / 2, wt) * Box(ix, iy + 1, iz, align=BOTTOM)
    back = o["y1"] - wt
    for x, z in lid_screws(cfg):  # corner posts from the back wall to the rim, inserts from the rim
        body += Pos(x, (o["y0"] + back) / 2, z) * Box(p, back - o["y0"], p)
        body -= Pos(x, o["y0"], z) * Rot(X=90) * fasteners.insert_hole(e.lid_screw_size)
    for x, z in relay_screws(cfg):
        body += Pos(x, back + 1, z) * Rot(X=90) * Cylinder(standoff_d(cfg) / 2, e.standoff_h + 1, align=BOTTOM)
        hole_d = cfg.fasteners.inserts[e.lid_screw_size].hole_d
        body -= Pos(x, back - e.standoff_h, z) * Rot(X=-90) * Cylinder(hole_d / 2, e.relay_hole_depth, align=BOTTOM)
    c = e.clamp_h  # the clamp block at the top, on the tube, joined to the side wall by a web in front of the screws
    L, tf, mw = mount.clamp_layout(cfg), tube_frame(cfg), cfg.print.min_wall
    tx, ty = tube_at(cfg)
    body += tf * Pos(0, (L["y_min"] + L["y_max"]) / 2, h - c) * Box(mount.clamp_width(cfg), L["y_max"] - L["y_min"], c, align=BOTTOM)
    web_x0, web_x1 = tx + mount.clamp_width(cfg) / 2 - 1, -o["x"] + 1
    web_y0, web_y1 = ty + L["y_min"], ty + L["y_s"] - (L["y_max"] - L["y_s"] - 2 * mw) - mw
    body += Pos(0, 0, h - c) * extrude(Polygon((web_x0, web_y0), (web_x1, web_y0), (web_x1, web_y1), (web_x0, web_y1 - (web_x1 - web_x0)), align=None), c)  # back end at 45 deg, from the wall
    body -= tf * Pos(0, 0, h - c) * mount.tube_clamp_cuts(c, 0, [z - (h - c) for z in clamp_screw_z(cfg)], cfg, lying=True)
    body -= tf * Pos(0, 0, h - c - 1) * _roofed_bore(mount.bore(cfg), c + 2)
    for _, d, loc in panel_holes(cfg)[len(e.front_holes):]:
        body -= loc * Pos(0, 0, -1) * _side_hole(d, wt + 2)
    return body


@per_config
def lid(cfg: Config = CFG) -> Part:
    e, o = cfg.electronics, outline(cfg)
    h = height(cfg)
    body = Pos(0, o["y0"] - e.lid_t / 2, h / 2) * Box(2 * o["x"], e.lid_t, h)
    for x, z in lid_screws(cfg):
        body -= Pos(x, o["y0"] - e.lid_t - 1, z) * Rot(X=90) * fasteners.clearance_hole(e.lid_screw_size, e.lid_t + 2)
    for _, d, loc in panel_holes(cfg)[: len(e.front_holes)]:
        body -= loc * Pos(0, 0, -1) * Cylinder(d / 2, e.lid_t + 2, align=BOTTOM)
    return body


@per_config
def box_left(cfg: Config = CFG) -> Part:
    """The box to the left of the tube: the mirror of `box`."""
    return box(cfg).mirror(Plane.YZ)


PARTS = {"electronics_box": box, "electronics_box_left": box_left, "electronics_lid": lid}
