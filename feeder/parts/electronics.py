"""Electronics box on the stand tube, below the tilt clamp, on the exit side.

- Box: upright, open at the front (away from the tube). Back wall against the collar, timer relay on standoffs
  with heat-set inserts inside it, motor and sensor sockets low in the +x face. Heat-set inserts in the corner
  posts take the lid.
- Collar: slit collar on the tube at the box top, clamp screws on the side away from the box. Screws from inside
  the box through the back wall into its inserts.
- Lid: front plate with the PWM knob (the PWM board hangs on its pot nut), toggle switch and DC jack in a column,
  screwed to the corner posts. The cables are long enough to open it.

Modelled in the box frame: tube axis on z, z = 0 at the box bottom, the box toward -y. `box_frame` turns it to the
exit side. The box prints on its back wall, the collar upright, the lid flat.
"""

from build123d import Box, Cylinder, Location, Part, Pos, Rot

from feeder.config import CFG, Config
from feeder.lib import fasteners
from feeder.lib.cache import per_config
from feeder.lib.features import teardrop
from feeder.parts import mount
from feeder.parts.slip_clutch import BOTTOM


def height(cfg: Config = CFG) -> float:
    return cfg.electronics.box_inner[2] + 2 * cfg.electronics.box_wall


def box_frame(tilt: float, cfg: Config = CFG) -> Location:
    """Box frame in the body frame: the box top `box_gap` below the tilt clamp, the box on the exit side (+y)."""
    return mount.clamp_frame(tilt, cfg) * Pos(0, 0, -cfg.electronics.box_gap - height(cfg)) * Rot(Z=180)


def collar_face(cfg: Config = CFG) -> float:
    """y of the collar face toward the box: the clamp wall plus room for the collar screw inserts."""
    ins = cfg.fasteners.inserts[cfg.electronics.collar_screw_size]
    return mount.clamp_layout(cfg)["y_min"] - ins.hole_depth


def outline(cfg: Config = CFG) -> dict:
    """Outer x half width of the box, y of its back face (`y1`, on the collar) and of its front rim (`y0`)."""
    e = cfg.electronics
    y1 = collar_face(cfg)
    return {"x": e.box_inner[0] / 2 + e.box_wall, "y0": y1 - e.box_wall - e.box_inner[1], "y1": y1}


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


def collar_screw_z(cfg: Config = CFG) -> list[float]:
    """z of the collar's clamp screws and of the screws that hold it to the box."""
    h, n, c = height(cfg), cfg.mount.clamp_screws, cfg.electronics.collar_h
    return [h - c + c * (i + 0.5) / n for i in range(n)]


def collar_screw_length(cfg: Config = CFG) -> float:
    e = cfg.electronics
    return fasteners.pick_length(fasteners.socket_screw_lengths(e.collar_screw_size), e.box_wall + cfg.fasteners.min_engagement * fasteners.nominal_d(e.collar_screw_size))


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


def _side_hole(d: float, depth: float) -> Part:
    """Socket hole along +z: teardrop roof toward -y (up when the box prints on its back wall), cut flat 1 above
    the circle, a bridge of 3 mm or less that the panel nut still covers."""
    hole = teardrop(d, depth) & Pos(depth / 2, 0, 0) * Box(depth, 2 * d, d + 2)
    return Rot(Y=-90) * Rot(X=90) * hole


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
    for z in collar_screw_z(cfg):  # through the back wall into the collar
        body -= Pos(0, o["y1"] + 1, z) * Rot(X=-90) * fasteners.clearance_hole(e.collar_screw_size, wt + 2)
    for _, d, loc in panel_holes(cfg)[len(e.front_holes):]:
        body -= loc * Pos(0, 0, -1) * _side_hole(d, wt + 2)
    return body


@per_config
def collar(cfg: Config = CFG) -> Part:
    """Slit collar on the tube, box frame: from `collar_face` to the clamp's +y side, at the box top."""
    e, L = cfg.electronics, mount.clamp_layout(cfg)
    h, c, y0 = height(cfg), e.collar_h, collar_face(cfg)
    body = Pos(0, (y0 + L["y_max"]) / 2, h - c) * Box(mount.clamp_width(cfg), L["y_max"] - y0, c, align=BOTTOM)
    body -= Pos(0, 0, h - c) * mount.tube_clamp_cuts(c, 0, [z - (h - c) for z in collar_screw_z(cfg)], cfg)
    ins = cfg.fasteners.inserts[e.collar_screw_size]
    for z in collar_screw_z(cfg):  # horizontal insert holes, teardrop roof up (the collar prints upright)
        body -= Pos(0, y0, z) * Rot(Z=90) * teardrop(ins.hole_d, ins.hole_depth)
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


PARTS = {"electronics_box": box, "electronics_collar": collar, "electronics_lid": lid}
