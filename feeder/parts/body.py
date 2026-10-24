"""Case feeder body: round core, wall arcs, track band and gate, exit insert.

- Core: open cup around the clutch with the motor under its floor (countersunk M4 from inside the cup),
  a flat deck out to the wall, radial ribs down to one flat bottom plane, an outer skirt, M5 inserts for
  the mount. It fits the bed, so motor, clutch and bowl stay concentric.
- Wall arcs around the core skirt, on the same bottom plane: a key rib on the inside at each screw slots
  into a groove in the core skirt, an M3 screw through rib and wall into a radial heat-set insert, a lap
  joint at the seams (`body.split` "arcs"). "halves": core and wall cut in two through `halves_seam`, a seam rib
  under the deck on each half, M3 screws across the seam through posts outside the wall, each motor screw holds
  one half to the gearbox. "one_piece": core and wall are one part.
- Wall top: full height on the low side, falling toward the open high side (`wall_slant`), not below one case
  length above the plate.
- Wall extender (optional): one arc over the low side above the wall top, a sleeve over the outside of the wall top holds it.
- Track band: C ring on the core's deck round the plate, printed with the core. Its gap is over the exit.
- Track gate: band sector in the band gap, on the exit insert. Its face sits behind the band face, the band ends
  have a lead-in chamfer and lap behind the gate ends, so it lifts out but cannot move inward.
- Exit insert: wear part with the drop opening and the funnel to the drop tube. A block that fills a vertical
  shaft in the core, so it drops in from above, and rests on a ledge in a deck recess round the shaft. With the
  plate and the gate off it lifts out, no tools.

- Motor can: a solid block under the deck with a tunnel (45 deg flanks, a flat top that bridges), so no rib
  starts in mid-air over the can.

Frame: `layout` body frame (z = 0 at the cup floor top, +y toward the exit). Core and walls print bottom down.
Band, gate and exit insert print top down. Skirt, no brim: a brim takes the band past the bed.
"""

import math

from build123d import Align, Box, Circle, Cylinder, Part, Plane, Polygon, Pos, Rot, Vector, extrude, loft
from shapely.geometry import MultiPoint
from shapely.geometry.polygon import orient

from feeder.config import CFG, Config
from feeder.lib.cache import per_config
from feeder.lib import fasteners
from feeder.lib.features import hex_corner_r, hex_prism, teardrop, teardrop_cone
from feeder.parts import layout
from feeder.parts import slip_clutch as sc

BOTTOM = sc.BOTTOM
EXIT_ANGLE = 90.0


def _ring(r_in: float, r_out: float, z0: float, h: float) -> Part:
    ring = Cylinder(r_out, h, align=BOTTOM)
    if r_in > 0:
        ring -= Cylinder(r_in, h, align=BOTTOM)
    return Pos(0, 0, z0) * ring


def _wedge(a0: float, a1: float, r: float, z0: float, h: float) -> Part:
    """Prism over the angles a0..a1 deg, out to radius r."""
    steps = max(2, math.ceil((a1 - a0) / 10))
    arc = [(r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)), r * math.sin(math.radians(a0 + (a1 - a0) * i / steps))) for i in range(steps + 1)]
    r_corner = r / math.cos(math.radians((a1 - a0) / steps / 2))  # polygon chords stay outside the circle
    pts = [(0, 0)] + [(x * r_corner / r, y * r_corner / r) for x, y in arc]
    return Pos(0, 0, z0) * extrude(Polygon(*pts, align=None), h)


def _sector(r_in: float, r_out: float, z0: float, h: float, a0: float, a1: float) -> Part:
    return _ring(r_in, r_out, z0, h) & _wedge(a0, a1, r_out + 1, z0, h)


def opening(cfg: Config = CFG) -> tuple[float, float, float]:
    """Drop opening: (length along travel at the pocket circle, inner radius, outer radius). An annular sector, so
    the outer edge of a long opening stays under the band."""
    e = cfg.exit
    r, d = layout.pocket_circle_r(cfg), layout.pocket_d(cfg)
    return e.open_ratio * layout.caliber(cfg).case_length, r - d / 2 - e.inner_margin, r + d / 2 + e.outer_margin


def exit_half_angle(cfg: Config = CFG) -> float:
    """Half the angle of the gate, deg: the band gap takes any plate's insert."""
    return max(math.degrees((opening(s)[0] / 2 + s.exit.end_margin) / layout.pocket_circle_r(s)) for s in layout.plate_sets(cfg))


def bore_d(cfg: Config = CFG) -> float:
    return layout.caliber(cfg).rim_d + cfg.exit.bore_clearance


def _lean_dir(cfg: Config) -> Vector:
    a = math.radians(cfg.exit.lean)
    return Vector(0, -math.sin(a), -math.cos(a))  # down and toward the bowl centre


def outlet(cfg: Config = CFG) -> tuple[Vector, Vector]:
    """Start of the spigot (centre of the funnel outlet) and the drop direction."""
    _, r0, r1 = opening(cfg)
    d = _lean_dir(cfg)
    return Vector(0, (r0 + r1) / 2, layout.levels(cfg).deck_top) + d * cfg.exit.funnel_len, d


def _opening_plan(cfg: Config, grow: float):
    """The opening in plan, grown by `grow`: annular sector round +y."""
    length, r0, r1 = opening(cfg)
    half = (length / 2 + grow) / layout.pocket_circle_r(cfg)
    far = 2 * (r1 + grow)
    wedge = Polygon((0, 0), (far * math.cos(math.pi / 2 - half), far * math.sin(math.pi / 2 - half)),
                    (far * math.cos(math.pi / 2 + half), far * math.sin(math.pi / 2 + half)), align=None)
    return (Circle(r1 + grow) - Circle(r0 - grow)) & wedge


def _funnel(cfg: Config, grow: float, up: float = 0.0) -> Part:
    """Funnel from the opening at the deck top to the outlet, then the spigot, grown by `grow`.
    `up` extends the top straight up, for cutting tools."""
    e = cfg.exit
    z = layout.levels(cfg)
    top = Pos(0, 0, z.deck_top) * _opening_plan(cfg, grow)
    o, d = outlet(cfg)
    r = bore_d(cfg) / 2 + grow
    solid = loft([top, Plane(origin=o, z_dir=-d) * Circle(r)])
    solid += Plane(origin=o, z_dir=d) * Cylinder(r, e.spigot_len, align=BOTTOM)
    if up > 0:
        solid += extrude(top, up)
    return solid


@per_config
def exit_insert(cfg: Config = CFG) -> Part:
    e, f = cfg.exit, cfg.print.fit
    z = layout.levels(cfg)
    length, r0, r1 = opening(cfg)
    body = Pos(0, 0, z.bottom) * extrude(_exit_outline(cfg, -f), z.deck_top - z.bottom)  # fills the shaft up to one flat top (prints top down)
    body += Pos(0, 0, z.deck_top - e.seat_t) * extrude(_exit_outline(cfg, e.seat_w - f), e.seat_t)  # ledge in the deck recess
    body = body & Cylinder(layout.bowl_r(cfg) - f, 1000)
    body += _funnel(cfg, e.wall) - Pos(0, 0, z.bottom) * Box(1000, 1000, 1000, align=BOTTOM)  # funnel end and spigot below the body
    body -= _funnel(cfg, 0.0)
    return body


_outline_pts: dict = {}


def _funnel_plan(cfg: Config) -> list[tuple[float, float]]:
    """Plan points of every plate's funnel and spigot with wall and fit."""
    key = repr(cfg)
    if key not in _outline_pts:
        pts = []
        for s in layout.plate_sets(cfg):
            verts, _ = _funnel(s, s.exit.wall + s.print.fit).tessellate(0.05)
            pts += [(v.X, v.Y) for v in verts]
        _outline_pts[key] = pts
    return _outline_pts[key]


def _exit_outline(cfg: Config, grow: float) -> Polygon:
    """Plan outline of every plate's funnel and spigot (with its wall and a fit), swept outward past the bowl radius,
    grown by `grow`: each insert drops into one vertical shaft over this outline (cut at the bowl radius), so nothing
    of it lies outside in plan and no sliver of skirt is left beyond it."""
    pts = list(_funnel_plan(cfg))
    pts += [(x, y + cfg.exit.wall + 2 * cfg.print.fit + 10) for x, y in pts]
    hull = orient(MultiPoint(pts).convex_hull.buffer(grow, join_style="mitre"))  # counter-clockwise: extrudes up
    return Polygon(*list(hull.exterior.coords)[:-1], align=None)


def _exit_cut(cfg: Config) -> Part:
    """What the core and walls give up for the exit insert: a vertical shaft over the funnel outline up to the deck
    top, inside the bowl radius, the funnel below and the recess its ledge rests in."""
    z, e = layout.levels(cfg), cfg.exit
    prism = Pos(0, 0, z.bottom - 1) * extrude(_exit_outline(cfg, 0.0), z.deck_top - z.bottom + 1)
    prism = (prism + Pos(0, 0, z.deck_top - e.seat_t) * extrude(_exit_outline(cfg, e.seat_w), e.seat_t + 1)) & Cylinder(layout.bowl_r(cfg), 1000)
    for s in layout.plate_sets(cfg):
        prism += _funnel(s, s.exit.wall + s.print.fit)
    return prism


def _exit_sleeve(cfg: Config) -> Part:
    """Wall round the exit cut from the bottom plane to the deck, so the deck edge round the cut is carried."""
    z = layout.levels(cfg)
    sleeve = Pos(0, 0, z.bottom) * extrude(_exit_outline(cfg, 2 * cfg.print.min_wall), z.deck_bottom - z.bottom)
    return sleeve & Cylinder(_skirt_r(cfg), 1000)


def band_top(cfg: Config = CFG) -> float:
    """Band and gate top: above the longest upright case of any plate."""
    return layout.levels(cfg).deck_top + max(layout.caliber(s).case_length for s in layout.plate_sets(cfg)) + cfg.track.band_above


def _lap_r(cfg: Config) -> float:
    """Radius of the lap between band ends and gate ends: the band's inner half reaches to the gate."""
    return layout.band_inner_r(cfg) + cfg.track.band_t / 2


def _gap_angles(cfg: Config) -> tuple[float, float]:
    """Half angles of the band gap: (inner half, outer half). The gate fills it with a fit."""
    t, f = cfg.track, cfg.print.fit
    a, d = exit_half_angle(cfg), math.degrees(f / layout.band_inner_r(cfg))
    return a + d, a + math.degrees(t.gate_lap / _lap_r(cfg)) + d


def _band(cfg: Config) -> Part:
    """C ring on the deck round the plate, part of the core: closes the plate notches, so cases slide on one smooth
    ring and never on the wall seams. The gap over the exit takes the gate."""
    t, f = cfg.track, cfg.print.fit
    z = layout.levels(cfg)
    r_in, r_out, h = layout.band_inner_r(cfg), layout.bowl_r(cfg) - f, band_top(cfg) - z.deck_top
    a_in, a_out = _gap_angles(cfg)
    body = _ring(r_in, r_out, z.deck_top, h) - _wedge(EXIT_ANGLE - a_in, EXIT_ANGLE + a_in, r_out + 1, z.deck_top, h)
    body -= _sector(_lap_r(cfg), r_out + 1, z.deck_top, h, EXIT_ANGLE - a_out, EXIT_ANGLE + a_out)
    c = t.gate_chamfer
    for s in (-1, 1):  # 45 deg lead-in on the inner edge of each band end
        tri = Polygon((r_in + c, 0), (r_in - c, 0), (r_in - c, 2 * s * c), align=None)
        body -= Rot(Z=EXIT_ANGLE + s * a_in) * Pos(0, 0, z.deck_top) * extrude(tri, h, dir=(0, 0, 1))
    return body


@per_config
def track_gate(cfg: Config = CFG) -> Part:
    """Band sector over the exit on the deck and the exit insert, its face `gate_setback` behind the band face. Its outer ends
    lap behind the band ends. Prints top down."""
    t, f = cfg.track, cfg.print.fit
    z = layout.levels(cfg)
    r_out, h = layout.bowl_r(cfg) - f, band_top(cfg) - z.deck_top
    a = exit_half_angle(cfg)
    a_lap = _gap_angles(cfg)[1] - math.degrees(f / layout.band_inner_r(cfg))
    body = _sector(layout.band_inner_r(cfg) + t.gate_setback, r_out, z.deck_top, h, EXIT_ANGLE - a, EXIT_ANGLE + a)
    return body + _sector(_lap_r(cfg) + f, r_out, z.deck_top, h, EXIT_ANGLE - a_lap, EXIT_ANGLE + a_lap)


def _seam_angles(cfg: Config) -> list[float]:
    b = cfg.body
    return [b.seam_start + 360 * i / b.wall_segments for i in range(b.wall_segments)]


def joint_angles(cfg: Config = CFG) -> list[float]:
    """Wall screw angles: evenly spread in each segment, moved off the exit."""
    b = cfg.body
    span = 360 / b.wall_segments
    keep = exit_half_angle(cfg) + b.joint_exit_margin
    out = []
    for a0 in _seam_angles(cfg):
        for k in range(b.joint_screws):
            ang = a0 + span * (k + 0.5) / b.joint_screws
            off = (ang - EXIT_ANGLE + 180) % 360 - 180
            if abs(off) < keep:
                ang = EXIT_ANGLE + math.copysign(keep, off if off else 1)
            out.append(ang)
    return out


def mount_bolts(cfg: Config = CFG) -> list[tuple[float, float]]:
    """(x, y) of the mount inserts in the bottom plane."""
    mt = cfg.mount
    return [(sx * mt.bolt_x, y) for y in mt.bolt_y for sx in (-1, 1)]


def _skirt_r(cfg: Config) -> float:
    return layout.bowl_r(cfg) - cfg.print.fit


def joint_insert_r(cfg: Config = CFG) -> float:
    """Radius of the wall joint insert mouths: the floor of the core skirt groove."""
    return _skirt_r(cfg) - cfg.body.seam_key - cfg.print.fit


def _joint_z(cfg: Config) -> float:
    z = layout.levels(cfg)
    return (z.bottom + z.deck_bottom) / 2


@per_config
def core(cfg: Config = CFG) -> Part:
    b, m, f = cfg.body, cfg.motor, cfg.print.fit
    z = layout.levels(cfg)
    rc, r_skirt = layout.cup_r(cfg), _skirt_r(cfg)
    h_under = z.deck_bottom - z.bottom
    body = _ring(0, rc + b.cup_wall, z.bottom, b.floor_t)
    body += _ring(rc, rc + b.cup_wall, z.bottom, z.deck_top - z.bottom)
    body += _ring(rc, r_skirt, z.deck_bottom, b.deck_t)
    body += _ring(r_skirt - b.skirt_t, r_skirt, z.bottom, h_under)
    rib_r0, rib_r1 = rc + b.cup_wall / 2, r_skirt - b.skirt_t / 2  # ends inside cup and skirt: a rib face on a cylinder leaves a non-manifold mesh edge
    for i in range(b.rib_count):
        body += Rot(Z=360 * (i + 0.5) / b.rib_count) * Pos((rib_r0 + rib_r1) / 2, 0, z.bottom) * Box(rib_r1 - rib_r0, b.rib_t, h_under, align=BOTTOM)
    ins = cfg.fasteners.inserts[b.joint_screw_size]
    groove_w, groove_d = b.key_w + 2 * f, b.seam_key + f
    boss_w, boss_r = groove_w + 2 * ins.min_wall, groove_d + ins.hole_depth + ins.min_wall
    for ang in joint_angles(cfg) if b.split == "arcs" else []:
        boss = Pos(r_skirt - boss_r / 2, 0, z.bottom) * Box(boss_r, boss_w, h_under, align=BOTTOM)
        groove = Pos(r_skirt - groove_d / 2, 0, z.bottom) * Box(groove_d, groove_w, h_under, align=BOTTOM)
        hole = Pos(joint_insert_r(cfg) - ins.hole_depth, 0, _joint_z(cfg)) * teardrop(ins.hole_d, ins.hole_depth)
        body += Rot(Z=ang) * boss
        body -= Rot(Z=ang) * (groove + hole)
    mt = cfg.mount
    mins = cfg.fasteners.inserts[mt.bolt_size]
    for x, y in mount_bolts(cfg):
        body += Pos(x, y, z.bottom) * Cylinder(mins.od / 2 + mins.min_wall, h_under, align=BOTTOM)
        body -= Pos(x, y, z.bottom) * Rot(X=180) * fasteners.insert_hole(mt.bolt_size)
    # motor: boss and shaft through the floor, countersunk screws from the cup
    body -= Pos(0, 0, z.bottom) * Cylinder(m.boss_d / 2 + f, b.floor_t, align=BOTTOM)
    for x, y in layout.motor_screws(cfg):
        body -= Pos(x, y, z.floor_top) * fasteners.countersink(m.mount_screw_size, m.mount_screw_length, b.floor_t)
    body += _exit_sleeve(cfg)
    body += Rot(Z=m.angle) * _can_block(cfg)
    body -= Rot(Z=m.angle) * can_tunnel(cfg)
    body += _band(cfg)
    body -= _exit_cut(cfg)
    return body


def _can_extent(cfg: Config) -> tuple[float, float, float]:
    """(start along the can direction, length, width) of the space the motor can needs under the core."""
    m, b = cfg.motor, cfg.body
    return m.gearbox_l - m.shaft_from_end, m.can_l + 2 * b.cup_clearance, m.can_d + 2 * b.cup_clearance


def _can_block(cfg: Config) -> Part:
    """Solid under the deck over the can, outside the cup, so the tunnel ceiling has material all round."""
    b = cfg.body
    z = layout.levels(cfg)
    x0, length, w = _can_extent(cfg)
    block = Pos(x0 + length / 2, 0, z.bottom) * Box(length, w + 2 * b.skirt_t, z.deck_bottom - z.bottom, align=BOTTOM)
    return block - Pos(0, 0, z.floor_top) * Cylinder(layout.cup_r(cfg), z.deck_top - z.floor_top, align=BOTTOM)


def can_tunnel(cfg: Config = CFG) -> Part:
    """Tunnel for the can along +x: 45 deg flanks up to a flat top `can_relief` above the bottom plane."""
    h = cfg.body.can_relief
    x0, length, w = _can_extent(cfg)
    profile = Polygon((-w / 2, 0), (w / 2, 0), (w / 2 - h, h), (h - w / 2, h), align=None)
    return extrude(Plane(origin=(x0, 0, layout.levels(cfg).bottom), x_dir=(0, 1, 0), z_dir=(1, 0, 0)) * profile, length)


def wall_slant(cfg: Config = CFG) -> float:
    """Deg the wall top falls toward the high side (+y): the brass surface is level in the world, at the flattest
    tilt it falls at the tilt angle in the body frame, minus `heap_angle` for heaping."""
    return max(0.0, cfg.mount.tilt_range[0] - cfg.body.heap_angle)


def wall_low(cfg: Config = CFG) -> float:
    """Lowest wall top: one case length above the plate top of any plate, so cases on it stay in at the high side."""
    return max(layout.levels(s).plate_top + layout.caliber(s).case_length for s in layout.plate_sets(cfg))


def wall_top_at(y: float, cfg: Config = CFG) -> float:
    """Wall top height at `y`: full height on the low side, falling toward the high side, not below `wall_low`."""
    z = layout.levels(cfg)
    R = layout.bowl_r(cfg)
    return min(z.wall_top, max(wall_low(cfg), z.wall_top - (y + R) * math.tan(math.radians(wall_slant(cfg)))))


def _below_wall_top(cfg: Config, dz: float = 0.0, size: float = 2000.0) -> Part:
    """Everything below the wall top profile raised by `dz`."""
    z = layout.levels(cfg)
    R = layout.bowl_r(cfg)
    down = (Align.CENTER, Align.CENTER, Align.MAX)
    plane = Pos(0, -R, z.wall_top + dz) * Rot(X=-wall_slant(cfg)) * Box(size, size, size, align=down)
    return (plane + Pos(0, 0, wall_low(cfg) + dz) * Box(size, size, size, align=down)) & Pos(0, 0, z.wall_top + dz) * Box(size, size, size, align=down)


def seam_lap(cfg: Config = CFG) -> float:
    """Thickness of each half of the lap joint at a wall seam, the fit gap between them."""
    return (cfg.body.wall_t - cfg.print.fit) / 2


@per_config
def wall(index: int, cfg: Config = CFG) -> Part:
    """Wall arc `index`, counter-clockwise from `body.seam_start`."""
    b, f = cfg.body, cfg.print.fit
    z = layout.levels(cfg)
    R = layout.bowl_r(cfg)
    a0 = _seam_angles(cfg)[index]
    a1 = a0 + 360 / b.wall_segments
    body = _sector(R, R + b.wall_t, z.bottom, z.wall_top - z.bottom, a0, a1)
    key = math.degrees(b.seam_key / R)
    lap = seam_lap(cfg)
    body += _sector(R + b.wall_t - lap, R + b.wall_t, z.bottom, z.wall_top - z.bottom, a1, a1 + key)  # outer lap over the next arc
    gap = math.degrees(f / R)
    body -= _sector(R + lap, R + b.wall_t + 1, z.bottom, z.wall_top - z.bottom, a0 - 1, a0 + key + gap)
    for ang in joint_angles(cfg):
        if 0 < (ang - a0) % 360 < a1 - a0:
            body += Rot(Z=ang) * Pos(R - b.seam_key / 2, 0, z.bottom) * Box(b.seam_key, b.key_w, z.deck_bottom - z.bottom, align=BOTTOM)
            body -= Rot(Z=ang) * Pos(R - b.seam_key, 0, _joint_z(cfg)) * teardrop(fasteners.clearance_d(b.joint_screw_size), b.wall_t + b.seam_key)
    body -= _exit_cut(cfg)
    if b.extender_h:
        body -= _extender_wall_holes(cfg)
    return body & _below_wall_top(cfg)


def _wall_ring(cfg: Config) -> Part:
    z = layout.levels(cfg)
    R = layout.bowl_r(cfg)
    ring = _ring(R, R + cfg.body.wall_t, z.bottom, z.wall_top - z.bottom)
    ring += _ring(R - cfg.print.fit, R, z.bottom, z.deck_top - z.bottom)  # closes the fit gap to the core skirt and deck
    a, h = _gap_angles(cfg)[1], band_top(cfg) - z.deck_top
    ring += _ring(R - cfg.print.fit, R, z.deck_top, h) - _wedge(EXIT_ANGLE - a, EXIT_ANGLE + a, R + 1, z.deck_top, h)  # and to the band, the gate keeps its fit
    if cfg.body.extender_h:
        ring -= _extender_wall_holes(cfg)
    return (ring - _exit_cut(cfg)) & _below_wall_top(cfg)


@per_config
def body_one_piece(cfg: Config = CFG) -> Part:
    return core(cfg) + _wall_ring(cfg)


def _side(index: int, cfg: Config, size: float = 1000.0) -> Part:
    """Half space on side `index` (0: +normal, 1: -normal) of the seam plane through `halves_seam`, half a fit
    off the plane."""
    s = 1 if index == 0 else -1
    return Rot(Z=cfg.body.halves_seam) * Pos(0, s * (cfg.print.fit + size) / 2, 0) * Box(size, size, size)


def post_h(cfg: Config = CFG) -> float:
    """Seam post height from the bottom plane, below the wall top and the extender sleeve at both seam ends (the extender spans the low side only)."""
    b = cfg.body
    ins = cfg.fasteners.inserts[b.joint_screw_size]
    R = layout.bowl_r(cfg)
    a = math.radians(b.halves_seam)
    t = max(post_lengths(cfg)) + cfg.print.fit
    corners = [s * (r * math.sin(a) + u * math.cos(a)) for s in (-1, 1) for r in (R, R + b.wall_t + ins.od + 2 * ins.min_wall) for u in (-t, t)]
    top = min(wall_top_at(y, cfg) for y in corners)  # the wall top only falls or rises with y, so the corners bound it
    return top - (b.extender_lap + cfg.print.fit if b.extender_h else 0) - layout.levels(cfg).bottom


def post_lengths(cfg: Config = CFG) -> tuple[float, float]:
    """Post length across the seam on the head side (half 0) and the insert side (half 1)."""
    b = cfg.body
    ins = cfg.fasteners.inserts[b.joint_screw_size]
    return b.joint_screw_length - ins.length, ins.hole_depth + ins.min_wall


def post_screw_z(cfg: Config = CFG) -> list[float]:
    b = cfg.body
    bottom = layout.levels(cfg).bottom
    return [bottom + post_h(cfg) * (i + 0.5) / b.post_screws for i in range(b.post_screws)]


def post_axis_r(cfg: Config = CFG) -> float:
    ins = cfg.fasteners.inserts[cfg.body.joint_screw_size]
    return layout.bowl_r(cfg) + cfg.body.wall_t + (ins.od + 2 * ins.min_wall) / 2


def _posts(index: int, cfg: Config) -> Part:
    """Seam posts of half `index` outside the wall at both seam ends, with the M3 screw holes across the seam:
    clearance on half 0, heat-set insert on half 1."""
    b, f = cfg.body, cfg.print.fit
    z = layout.levels(cfg)
    ins = cfg.fasteners.inserts[b.joint_screw_size]
    R = layout.bowl_r(cfg)
    w = ins.od + 2 * ins.min_wall
    r_axis = post_axis_r(cfg)
    length = post_lengths(cfg)[index]
    out = None
    for k, ang in enumerate((b.halves_seam, b.halves_seam + 180)):
        s = (1 if index == 0 else -1) * (1 if k == 0 else -1)  # local y of this half at this seam end
        post = Pos(R + b.wall_t / 2 + (w + b.wall_t / 2) / 2, s * (f / 2 + length / 2), z.bottom) * Box(w + b.wall_t / 2, length, post_h(cfg), align=BOTTOM)
        for zz in post_screw_z(cfg):
            if index == 0:  # from the outer face toward the seam
                post -= Pos(r_axis, s * (f / 2 + length), zz) * Rot(Z=-90 * s) * teardrop(fasteners.clearance_d(b.joint_screw_size), length)
            else:  # from the seam face into the post
                post -= Pos(r_axis, s * f / 2, zz) * Rot(Z=90 * s) * teardrop(ins.hole_d, ins.hole_depth)
        post = Rot(Z=ang) * post
        out = post if out is None else out + post
    return out


@per_config
def half(index: int, cfg: Config = CFG) -> Part:
    """Body half `index`: core and wall on one side of the seam plane, a seam rib under the deck, seam posts."""
    b, m = cfg.body, cfg.motor
    z = layout.levels(cfg)
    s = 1 if index == 0 else -1
    rc, r_skirt = layout.cup_r(cfg), _skirt_r(cfg)
    rib = Rot(Z=b.halves_seam) * Pos(0, s * (cfg.print.fit + b.rib_t) / 2, z.bottom) * Box(2 * r_skirt, b.rib_t, z.deck_bottom - z.bottom, align=BOTTOM)
    rib &= _ring(rc + b.cup_wall / 2, r_skirt - b.skirt_t / 2, z.bottom, z.deck_bottom - z.bottom)  # ends inside cup and skirt
    body = (body_one_piece(cfg) + rib - Rot(Z=m.angle) * can_tunnel(cfg) - _exit_cut(cfg)) & _side(index, cfg)
    return body + _posts(index, cfg)


def extender_reach(cfg: Config = CFG) -> float:
    """How far from the low side wall (in y) the extender stands: out to where brass level at the steepest tilt, up
    at the extender top on the low side, falls below the wall top."""
    steepest, slant = (math.tan(math.radians(a)) for a in (cfg.mount.tilt_range[1], wall_slant(cfg)))
    return cfg.body.extender_h / (steepest - slant)


def extender_half_angle(cfg: Config = CFG) -> float:
    """Deg either side of the low side (-y) that the extender spans."""
    return math.degrees(math.acos(max(-1.0, 1 - extender_reach(cfg) / layout.bowl_r(cfg))))


@per_config
def extender(cfg: Config = CFG) -> Part:
    """Wall extender, one arc over the low side: wall above the wall top up to a flat top `extender_h` above it,
    falling at the wall slant, sleeve down over the outside of the wall. Prints on its flat top."""
    b, f = cfg.body, cfg.print.fit
    z = layout.levels(cfg)
    R = layout.bowl_r(cfg)
    tall = z.wall_top + b.extender_h - z.bottom + 100  # only the slanted top cuts it
    top = Pos(0, -R, z.wall_top + b.extender_h) * Rot(X=-wall_slant(cfg)) * Box(2000, 2000, 2000, align=(Align.CENTER, Align.CENTER, Align.MAX))
    body = (_ring(R, R + 2 * b.wall_t + f, z.bottom, tall) & top) - _below_wall_top(cfg)
    body += (_ring(R + b.wall_t + f, R + 2 * b.wall_t + f, z.bottom, tall) & _below_wall_top(cfg)) - _below_wall_top(cfg, -b.extender_lap)
    half = extender_half_angle(cfg)
    body = (body & _wedge(-90 - half, -90 + half, R + 2 * b.wall_t + f + 1, z.bottom, tall)) + (_extender_ribs(cfg) & top)
    return body - _extender_nut_holes(cfg)


def extender_wall_screws(cfg: Config = CFG) -> list[tuple[float, float]]:
    """(angle, z) of each screw that holds the extender to the wall: evenly over the middle half of the arc, at the
    middle of the sleeve lap."""
    b = cfg.body
    n, R, half = b.extender_wall_screws, layout.bowl_r(cfg), extender_half_angle(cfg)
    angles = [-90 + half * (j - (n - 1) / 2) / max(n - 1, 1) for j in range(n)]  # over the middle half of the arc, clear of the seam posts
    return [(a, wall_top_at(R * math.sin(math.radians(a)), cfg) - b.extender_lap / 2) for a in angles]


def extender_wall_screw_length(cfg: Config = CFG) -> float:
    """Shortest ISO 10642 that passes wall, sleeve and nut with one thread to spare, head flush in the wall."""
    b = cfg.body
    size = b.joint_screw_size
    need = 2 * b.wall_t + cfg.print.fit + fasteners.nut_data(size)["m"] + cfg.fasteners.coarse_pitch[size]
    return min(length for length in fasteners.countersunk_screw_lengths(size) if length >= need)


def extender_screw_seat(ang: float, z: float, cfg: Config = CFG):
    """Countersunk head seat on the wall's inner face, +z into the bowl."""
    return Rot(Z=ang) * Pos(layout.bowl_r(cfg), 0, z) * Rot(Y=-90)


def extender_nut_seat(ang: float, z: float, cfg: Config = CFG):
    """Nut face flush with the rib's outer face, +z toward the bowl."""
    b = cfg.body
    r = layout.bowl_r(cfg) + 2 * b.wall_t + cfg.print.fit + fasteners.nut_data(b.joint_screw_size)["m"]
    return Rot(Z=ang) * Pos(r, 0, z) * Rot(Y=-90)


def _extender_wall_holes(cfg: Config) -> Part:
    """Countersunk holes in the wall for the extender screws, teardrop roof up: the wall prints upright."""
    b = cfg.body
    size = b.joint_screw_size
    head_d = fasteners.countersunk_screw(size, extender_wall_screw_length(cfg)).screw_data["dk"] + 2 * cfg.fasteners.head_fit + 1  # 0.5 into the bowl
    hole_d = fasteners.clearance_d(size)
    out = None
    for ang, z in extender_wall_screws(cfg):
        hole = Rot(Z=ang) * Pos(layout.bowl_r(cfg) - 0.5, 0, z) * (teardrop(hole_d, b.wall_t + 1.5) + teardrop_cone(head_d, hole_d, (head_d - hole_d) / 2))
        out = hole if out is None else out + hole
    return out


def _extender_ribs(cfg: Config) -> Part:
    """Ribs outside the sleeve from each wall screw up to the flat top, so they print without overhang."""
    b = cfg.body
    nut = fasteners.nut_data(b.joint_screw_size)
    w = hex_corner_r(nut["s"]) * 2 + 2 * cfg.print.min_wall
    r0 = layout.bowl_r(cfg) + 2 * b.wall_t + cfg.print.fit
    top = layout.levels(cfg).wall_top + b.extender_h
    out = None
    for ang, z in extender_wall_screws(cfg):
        rib = Rot(Z=ang) * Pos(r0 - 1 + (nut["m"] + 1) / 2, 0, z - w / 2) * Box(nut["m"] + 1, w, top - z + w / 2 + 2 * layout.bowl_r(cfg), align=BOTTOM)  # the slanted top cuts it
        out = rib if out is None else out + rib
    return out


def _extender_nut_holes(cfg: Config) -> Part:
    """Screw hole through sleeve and rib, hex pocket for the captive nut."""
    b, f = cfg.body, cfg.print.fit
    size = b.joint_screw_size
    nut = fasteners.nut_data(size)
    out = None
    for ang, z in extender_wall_screws(cfg):
        hole = Rot(Z=ang) * Pos(layout.bowl_r(cfg) + b.wall_t, 0, z) * Rot(X=180) * teardrop(fasteners.clearance_d(size), b.wall_t + f + nut["m"] + 1)  # roof down: prints top down
        hole += extender_nut_seat(ang, z, cfg) * Pos(0, 0, -1) * hex_prism(nut["s"] + 2 * cfg.fasteners.head_fit, nut["m"] + 1)
        out = hole if out is None else out + hole
    return out


def parts(cfg: Config = CFG) -> dict:
    b = cfg.body
    out = {"body_track_gate": track_gate, "body_exit_insert": exit_insert}
    if b.split == "arcs":
        out["body_core"] = core
        for i in range(b.wall_segments):
            out[f"body_wall_{i}"] = lambda cfg=cfg, i=i: wall(i, cfg)
    elif b.split == "halves":
        for i in range(2):
            out[f"body_half_{i}"] = lambda cfg=cfg, i=i: half(i, cfg)
    else:
        out["body"] = body_one_piece
    if b.extender_h:
        out["body_extender"] = extender
    return out


PARTS = parts(CFG)
