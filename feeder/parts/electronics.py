"""Electronics box beside the stand tube, below the tilt clamp, its front toward the user (the low side).

- Box: upright, open at the front. Timer relay on standoffs with heat-set inserts on the back wall, motor and
  sensor sockets low in the side face away from the tube, heat-set inserts in the corner posts for the lid. The
  box has its own slit clamp on the tube, standing off its side wall, so there is no collar: the slit and the 2
  clamp screws at the back, heads outward, nuts toward the wall. `electronics_box` stands to the right of the
  tube as the user sees it, `electronics_box_left` is its mirror.
- Lid: front plate with the PWM knob (the PWM board hangs on its pot nut), toggle switch and DC jack in a column,
  screwed to the corner posts. The cables are long enough to open it. One lid fits both boxes. The text engraved in
  its outer face (names, plug pins and jack polarity from `feeder.wiring`) names no side, so it reads right on both.
- Finish: edges that touch the bed are chamfered, the others filleted. The side sockets stand in the front band
  (the relay is behind it), each with a free straight run behind it for a service loop and a tie pad on the wall
  for its wires. A fuse holder cradle and two splice connector cradles stand on the back wall above the relay,
  open toward the lid, with a tie tunnel under each.

Modelled in the box frame: x = 0 at the middle of the box, z = 0 at the box bottom, the front toward -y, the tube
at `tube_at`. `box_frame` puts the tube on the clamp axis. The box prints on its back wall, the lid flat.
"""

import math  # noqa: I001

from build123d import Align, Axis, Box, Circle, Compound, Cylinder, FontStyle, Location, Part, Plane, Polygon, Pos, Rot, Text, extrude

from feeder import wiring
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


def relay_front(cfg: Config = CFG) -> float:
    """y of the front of the relay module, behind it the back wall."""
    e = cfg.electronics
    return outline(cfg)["y1"] - e.box_wall - e.standoff_h - e.relay_pcb_t - e.relay_parts[2]


def panel_holes(cfg: Config = CFG) -> list[tuple[str, float, Location]]:
    """(name, diameter, mouth) of each panel hole, +z of the mouth into the box: the lid column at x = 0 from the
    top down, the sockets one above the other in the +x face, in the band between the relay and the lid."""
    e, o = cfg.electronics, outline(cfg)
    iz, wt = e.box_inner[2], e.box_wall
    out = []
    for i, (name, d) in enumerate(e.front_holes):
        z = wt + iz * (1 - (i + 1) / (len(e.front_holes) + 1))
        out.append((name, d, Pos(0, o["y0"] - e.lid_t, z) * Rot(X=-90)))
    for (name, d), z in zip(e.side_holes, e.socket_z, strict=True):
        out.append((name, d, Pos(o["x"], (o["y0"] + relay_front(cfg)) / 2, z) * Rot(Y=-90)))
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


def service_loops(cfg: Config = CFG) -> list[Part]:
    """Free run of `service_loop` behind each side socket, straight on its axis, as wide as its body: the wires from
    the solder cups lie folded there, long enough to pull the socket out of the wall for service."""
    e = cfg.electronics
    out = []
    parts = dict(e.panel_parts)
    for name, _, mouth in panel_holes(cfg)[len(e.front_holes):]:
        pp = parts[name]
        out.append(mouth * Pos(0, 0, pp.thread_l + pp.body[2] + e.service_loop / 2) * Box(pp.body[0], pp.body[1], e.service_loop))
    return out


def tie_pads(cfg: Config = CFG) -> list[tuple[float, float, float]]:
    """(x, y, z) of the tie tunnel of each tie pad: on the +x inner wall just behind its socket (+y), at its height."""
    e, o = cfg.electronics, outline(cfg)
    out = []
    parts = dict(e.panel_parts)
    for name, _, mouth in panel_holes(cfg)[len(e.front_holes):]:
        y_hi = mouth.position.Y + parts[name].body[1] / 2 + e.tie_gap  # clear of the socket body, the pad starts here (toward the lid)
        out.append((o["x"] - e.box_wall - e.tie_gap - e.tie_slot[1] / 2, y_hi + e.tie_gap + e.tie_slot[0] / 2, mouth.position.Z))
    return out


def _tie_pad(cfg: Config, x: float, y: float, z: float) -> Compound:
    """Pad on the +x wall, 45 deg underneath toward the back (it prints with the back wall down): a tunnel along z
    for a cable tie, with `tie_gap` of material round it."""
    e, o = cfg.electronics, outline(cfg)
    tw, tt = e.tie_slot
    d = e.tie_gap + tt + e.tie_gap  # pad depth from the wall
    wall = o["x"] - e.box_wall
    y_hi, y_lo = y - tw / 2 - e.tie_gap, y + tw / 2 + e.tie_gap + d
    pad = Pos(0, 0, z) * extrude(Polygon((wall + 1, y_hi), (wall - d, y_hi), (wall - d, y_lo - d), (wall, y_lo), (wall + 1, y_lo), align=None), e.pad_len / 2, both=True)
    pad -= Pos(x, y, z) * Box(tt, tw, e.pad_len + 2)
    return pad


def fuse_cradle_size(cfg: Config = CFG) -> tuple[float, float, float]:
    """(length along x, height from the back wall, width along z) of the fuse holder cradle."""
    e = cfg.electronics
    dh, lh = e.fuse_holder
    r = dh / 2 + cfg.print.fit
    return lh, e.tie_gap + e.tie_slot[1] + e.tie_gap + r, 2 * (r + e.tie_gap)


def splice_cradle_size(cfg: Config = CFG) -> tuple[float, float, float]:
    """(length along x, height from the back wall, width along z) of one splice connector cradle."""
    e, mw = cfg.electronics, cfg.print.min_wall
    sl, sw, sh = e.splice
    return sl + 2 * cfg.print.fit + 2 * mw, e.tie_gap + e.tie_slot[1] + e.tie_gap + sh, sw + 2 * cfg.print.fit + 2 * mw


def splice_at(cfg: Config = CFG) -> list[float]:
    """x of the two splice connector cradles (+12 V and 0 V), side by side."""
    return [sx * (splice_cradle_size(cfg)[0] / 2 + cfg.electronics.tie_gap) for sx in (-1, 1)]


def cradle_bodies(cfg: Config = CFG) -> tuple[Part, Part]:
    """(solid to add, volume to cut) of the fuse holder and splice cradles on the back wall, box frame. The holder lies
    in a groove cut to its half height, the connectors in rectangular pockets: both open toward the lid, so they
    print without supports. Each has a tie tunnel along z under it."""
    e, o = cfg.electronics, outline(cfg)
    back, (tw, tt) = o["y1"] - e.box_wall, e.tie_slot
    zf, zs = e.cradle_z
    lx, hh, wz = fuse_cradle_size(cfg)
    r = e.fuse_holder[0] / 2 + cfg.print.fit
    add = Pos(0, back - hh / 2, zf) * Box(lx, hh, wz)
    cut = Pos(0, back - hh, zf) * Rot(Y=90) * Cylinder(r, lx + 2)  # lower half is the groove
    for sx in (-1, 1):  # a tie near each end of the holder
        cut += Pos(sx * (lx / 2 - e.tie_gap - tw), back - e.tie_gap - tt / 2, zf) * Box(tw, tt, wz + 2)
    sl, hs, sz = splice_cradle_size(cfg)
    for x in splice_at(cfg):
        add += Pos(x, back - hs / 2, zs) * Box(sl, hs, sz)
        floor = e.tie_gap + tt + e.tie_gap
        cut += Pos(x, back - floor - (hs - floor + 1) / 2, zs) * Box(sl - 2 * cfg.print.min_wall, hs - floor + 1, sz - 2 * cfg.print.min_wall)
        cut += Pos(x, back - e.tie_gap - tt / 2, zs) * Box(tw, tt, sz + 2)
    return add, cut


def lid_lines(cfg: Config = CFG) -> dict[str, list[str]]:
    """Text of the lid by wiring part: its title, the plug pins of a socket (from the plug step of the wiring data), the
    centre polarity of the jack (from its description)."""
    e = cfg.electronics
    lines = {ref: [title] for ref, title in e.lid_titles}
    for ref, rows in wiring.plug_pins().items():
        lines[ref] += [f"{n} {signal}" for n, signal in rows]
    for ref in e.front_refs:
        if "centre pin" in wiring.WIRING_PARTS[ref]["sub"]:  # the supply jack
            lines[ref].append(f"TIP {wiring.centre_polarity(ref)}")
    return lines


def lid_labels(cfg: Config = CFG) -> list[tuple[str, float, float, bool]]:
    """(text, x, z, left aligned) of each line of the lid text, lid frame as the box frame. The controls' names stand
    right of the middle column, level with their holes. The socket pins stand left of it, each block centred level
    with its socket and moved up where it would run into the block below. Viewed from the front (-y) +x is right."""
    e = cfg.electronics
    lines, out = lid_lines(cfg), []
    holes = panel_holes(cfg)
    for ref, hole in zip(e.front_refs, holes[: len(e.front_holes)], strict=True):
        out += [(text, e.label_gap, hole[2].position.Z + ((len(lines[ref]) - 1) / 2 - i) * e.label_pitch, True) for i, text in enumerate(lines[ref])]
    top = -math.inf  # z of the top line of the block below
    for ref, hole in zip(e.side_refs, holes[len(e.front_holes):], strict=True):
        n = len(lines[ref])
        z = max(hole[2].position.Z, top + e.label_pitch + e.label_block_gap + (n - 1) / 2 * e.label_pitch)
        out += [(text, -e.label_gap, z + ((n - 1) / 2 - i) * e.label_pitch, False) for i, text in enumerate(lines[ref])]
        top = z + (n - 1) / 2 * e.label_pitch
    return out


def lid_text(cfg: Config = CFG) -> list[Part]:
    """The text lines as solids in the box frame: from the outer face of the lid, `label_depth` into it and 1 mm out."""
    e, o = cfg.electronics, outline(cfg)
    face = Plane(origin=(0, o["y0"] - e.lid_t, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))  # reads right viewed from the front
    out = []
    for text, x, z, left in lid_labels(cfg):
        line = Text(text, e.label_size, font=e.label_font, font_style=FontStyle.BOLD, align=(Align.MIN if left else Align.MAX, Align.CENTER))
        out.append(face * Pos(x, z, -e.label_depth) * extrude(line, e.label_depth + 1))
    return out


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
    body = body.chamfer(e.edge_r, None, body.edges().filter_by(Axis.Y) + body.faces().sort_by(Axis.Y)[-1].edges())  # the back face is on the bed
    body -= Pos(0, o["y0"] - 1 + (iy + 1) / 2, wt) * Box(ix, iy + 1, iz, align=BOTTOM)
    back = o["y1"] - wt
    for x, z in lid_screws(cfg):  # corner posts from the back wall to the rim, inserts from the rim
        body += Pos(x, (o["y0"] + back) / 2, z) * Box(p, back - o["y0"], p)
        body -= Pos(x, o["y0"], z) * Rot(X=90) * fasteners.insert_hole(e.lid_screw_size)
    for x, z in relay_screws(cfg):
        body += Pos(x, back + 1, z) * Rot(X=90) * Cylinder(standoff_d(cfg) / 2, e.standoff_h + 1, align=BOTTOM)
        hole_d = cfg.fasteners.inserts[e.lid_screw_size].hole_d
        body -= Pos(x, back - e.standoff_h, z) * Rot(X=-90) * Cylinder(hole_d / 2, e.relay_hole_depth, align=BOTTOM)
    add, cut = cradle_bodies(cfg)
    body = body + add - cut
    for x, y, z in tie_pads(cfg):
        body += _tie_pad(cfg, x, y, z)
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
    body = body.chamfer(e.edge_r, None, body.edges().filter_by(Axis.Y) + body.faces().sort_by(Axis.Y)[0].edges())  # the outer face is on the bed
    for text in lid_text(cfg):
        body -= text
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
