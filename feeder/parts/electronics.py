"""Electronics box on the stand tube, below the tilt clamp.

- Box: open at the bottom, a slit collar on the tube at its +y side with the tilt clamp's screws, so it stays
  put when the body tilts. Toggle switch, PWM knob and DC jack in the -y face, motor and sensor connectors in
  the +x face, a zip-tie tab beside them for the cables. Heat-set inserts in the corner posts take the lid.
- Lid: flat plate under the box, zip-tie slots for the modules, screws from below, so it comes off with
  nothing above in the way.

Modelled in the box frame: z = 0 on the box rim (lid top), the box top at `height`, the tube axis on z. The box
prints top down, the lid flat. `box_frame` places both in the body frame.
"""

from build123d import Box, Location, Part, Pos, Rot

from feeder.config import CFG, Config
from feeder.lib import fasteners
from feeder.lib.features import teardrop
from feeder.parts import mount
from feeder.parts.slip_clutch import BOTTOM


def height(cfg: Config = CFG) -> float:
    return cfg.electronics.box_inner[2] + cfg.electronics.box_wall


def box_frame(tilt: float, cfg: Config = CFG) -> Location:
    """Box frame in the body frame: the box top `box_gap` below the tilt clamp."""
    return mount.clamp_frame(tilt, cfg) * Pos(0, 0, -cfg.electronics.box_gap - height(cfg))


def outline(cfg: Config = CFG) -> dict:
    """Outer x half width and y range of the box shell: its +y face on the collar's -y face."""
    e = cfg.electronics
    y1 = mount.clamp_layout(cfg)["y_min"]
    return {"x": e.box_inner[0] / 2 + e.box_wall, "y0": y1 - e.box_inner[1] - 2 * e.box_wall, "y1": y1}


def post_w(cfg: Config = CFG) -> float:
    ins = cfg.fasteners.inserts[cfg.electronics.lid_screw_size]
    return ins.od + 2 * ins.min_wall


def lid_screws(cfg: Config = CFG) -> list[tuple[float, float]]:
    """(x, y) of the lid screws, on the corner posts."""
    e, o = cfg.electronics, outline(cfg)
    c = e.box_wall + post_w(cfg) / 2
    return [(sx * (o["x"] - c), y) for sx in (-1, 1) for y in (o["y0"] + c, o["y1"] - c)]


def lid_screw_length(cfg: Config = CFG) -> float:
    e = cfg.electronics
    return fasteners.pick_length(fasteners.socket_screw_lengths(e.lid_screw_size), e.lid_t + cfg.fasteners.min_engagement * fasteners.nominal_d(e.lid_screw_size))


def collar_screw_z(cfg: Config = CFG) -> list[float]:
    h, n = height(cfg), cfg.mount.clamp_screws
    return [h * (i + 0.5) / n for i in range(n)]


def panel_holes(cfg: Config = CFG) -> list[tuple[str, float, Location]]:
    """(name, diameter, mouth) of each panel hole: on the outer face, +x of the mouth into the box, evenly along
    the face at half the inner height."""
    e, o = cfg.electronics, outline(cfg)
    z = e.box_inner[2] / 2
    out = []
    for i, (name, d) in enumerate(e.front_holes):
        x = e.box_inner[0] * ((i + 1) / (len(e.front_holes) + 1) - 0.5)
        out.append((name, d, Pos(x, o["y0"], z) * Rot(Z=90)))
    for i, (name, d) in enumerate(e.side_holes):
        y = o["y0"] + e.box_wall + e.box_inner[1] * (i + 1) / (len(e.side_holes) + 1)
        out.append((name, d, Pos(o["x"], y, z) * Rot(Z=180)))
    return out


def _panel_hole(d: float, depth: float) -> Part:
    """Teardrop cut flat 1 above the circle, roof toward -z (the box prints top down): a bridge of 3 mm or less
    that the panel nut still covers."""
    return Rot(X=180) * (teardrop(d, depth) & Pos(depth / 2, 0, 0) * Box(depth, 2 * d, d + 2))


def _tie_slot(cfg: Config, depth: float) -> Part:
    w, t = cfg.electronics.tie_slot
    return Box(t, w, depth, align=BOTTOM)


def box(cfg: Config = CFG) -> Part:
    e, o = cfg.electronics, outline(cfg)
    L, h, wt, p = mount.clamp_layout(cfg), height(cfg), e.box_wall, post_w(cfg)
    ix, iy, iz = e.box_inner
    yc = (o["y0"] + o["y1"]) / 2
    body = Pos(0, yc, 0) * Box(2 * o["x"], o["y1"] - o["y0"], h, align=BOTTOM)
    body -= Pos(0, yc, -1) * Box(ix, iy, iz + 1, align=BOTTOM)
    for x, y in lid_screws(cfg):  # corner posts, inserts from the rim
        body += Pos(x, y, 0) * Box(p, p, iz, align=BOTTOM)
    body += Pos(0, (L["y_min"] + L["y_max"]) / 2, 0) * Box(mount.clamp_width(cfg), L["y_max"] - L["y_min"], h, align=BOTTOM)
    ys = [loc.position.Y for _, _, loc in panel_holes(cfg)[len(e.front_holes):]]
    tab = Pos(o["x"] - 1 + (e.anchor_l + 1) / 2, sum(ys) / len(ys), h - wt) * Box(e.anchor_l + 1, max(ys) - min(ys) + e.tie_pitch, wt, align=BOTTOM)
    for y in ys:
        tab -= Pos(o["x"] + e.anchor_l / 2 + 1, y, h - wt - 1) * _tie_slot(cfg, wt + 2)
    body += tab
    body -= mount.tube_clamp_cuts(h, 0, collar_screw_z(cfg), cfg, top_down=True)
    for _, d, loc in panel_holes(cfg):
        body -= loc * Pos(-1, 0, 0) * _panel_hole(d, wt + 2)
    for x, y in lid_screws(cfg):
        body -= Pos(x, y, 0) * Rot(X=180) * fasteners.insert_hole(e.lid_screw_size)
    return body


def lid(cfg: Config = CFG) -> Part:
    e, o = cfg.electronics, outline(cfg)
    ix, iy, _ = e.box_inner
    yc = (o["y0"] + o["y1"]) / 2
    body = Pos(0, yc, -e.lid_t) * Box(2 * o["x"], o["y1"] - o["y0"], e.lid_t, align=BOTTOM)
    for x, y in lid_screws(cfg):
        body -= Pos(x, y, 1) * fasteners.clearance_hole(e.lid_screw_size, e.lid_t + 2)
    n = int((ix - 2 * post_w(cfg)) // e.tie_pitch) + 1
    for row in (-1, 1):
        for i in range(n):
            x = e.tie_pitch * (i - (n - 1) / 2)
            body -= Pos(x, yc + row * iy / 4, -e.lid_t - 1) * _tie_slot(cfg, e.lid_t + 2)
    return body


PARTS = {"electronics_box": box, "electronics_lid": lid}
