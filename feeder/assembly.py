"""The assembled feeder: every part placed in the body frame with the body tilted by `tilt`, for the assembly
exports, the viewer and the assembly checks. Bought parts (motor, hub, tube) are envelopes, fasteners nominal
cylinders and hex prisms.

The mount clamp and the stand tube stay vertical in the world, so in the body frame they turn by -tilt about
the pivot. The tilt link runs between its pins at the tilt.
"""

import math
from dataclasses import dataclass

from build123d import Box, Cone, Cylinder, Part, Plane, Pos, Rot

from feeder.config import CFG, Config
from feeder.lib import fasteners
from feeder.lib.features import d_bore, hex_prism
from feeder.parts import body, case_plate, drop_tube, electronics, layout, mount
from feeder.parts import slip_clutch as sc

B = sc.BOTTOM


@dataclass(frozen=True)
class Placed:
    name: str  # printed parts: the build name
    shape: Part
    kind: str  # material group in the viewer
    step: int  # assembly step in the viewer
    explode: tuple = (0.0, 0.0, 1.0)  # direction the part moves away in the exploded view
    bought: bool = False
    tool: bool = False  # shown only in its own step


def motor_envelope(cfg: Config = CFG) -> Part:
    """Gearbox under the cup floor, can toward `motor.angle`, can axis up to 8.5 above the gearbox face
    (seller drawings, unverified)."""
    m = cfg.motor
    z0 = layout.levels(cfg).bottom
    gb = Pos(m.gearbox_l / 2 - m.shaft_from_end, 0, z0) * Box(m.gearbox_l, m.gearbox_w, m.gearbox_t, align=fasteners.DOWN)
    can = Pos(m.gearbox_l - m.shaft_from_end, 0, z0 + 8.5 - m.can_d / 2) * Rot(Y=90) * Cylinder(m.can_d / 2, m.can_l, align=B)
    return Rot(Z=m.angle) * (gb + can)


def cap_angle(cfg: Config = CFG) -> float:
    """Rotation of the cap at its clamp face where its thread meshes with the ring. Both threads start at angle 0 at
    their lower ends, the cap's `cap_face - hex_top` higher, so its teeth sit half a pitch from the ring's there."""
    dr, z = cfg.drive_ring, sc.levels(cfg)
    hand = 1 if sc.thread_hand(cfg) == "right" else -1
    return (hand * 360 * (z.cap_face - z.hex_top) / sc.thread_lead(cfg) + 180 / dr.thread_starts) % (360 / dr.thread_starts)


def cap_on_ring(cfg: Config = CFG) -> Part:
    """Cap in the clutch frame at its clamp face, turned to mesh with the ring."""
    return Pos(0, 0, sc.levels(cfg).cap_face) * Rot(Z=cap_angle(cfg)) * sc.cap(cfg)


def _hub(cfg: Config) -> Part:
    mh = cfg.metal_hub
    hub = Cylinder(mh.boss_d / 2, mh.boss_h, align=B) + Pos(0, 0, mh.boss_h) * Cylinder(mh.flange_d / 2, mh.flange_t, align=B)
    hub -= Cylinder(mh.bore_d / 2, mh.boss_h + mh.flange_t, align=B)
    for p in sc._around(mh.hole_count, mh.hole_pcd / 2):
        hub -= Pos(0, 0, mh.boss_h + mh.flange_t) * p * Cylinder(fasteners.nominal_d(mh.hole_size) / 2, mh.flange_t, align=fasteners.DOWN)
    return Pos(0, 0, sc.levels(cfg).hub_bottom) * hub


def stand_tube(tilt: float, cfg: Config = CFG, stub: float = 100.0) -> Part:
    """`stub` mm of the stand tube up to the clamp's closed top, in the body frame."""
    mt = cfg.mount
    h = stub + mt.clamp_h - mt.clamp_wall
    tube = Cylinder(mt.tube_d / 2, h, align=B) if mt.tube_shape == "round" else Box(mt.tube_d, mt.tube_d, h, align=B)
    return mount.clamp_in_body(Pos(0, 0, -stub) * tube, tilt, cfg)


def placed(cfg: Config = CFG, tilt: float | None = None) -> list[Placed]:
    """Every part of the feeder in the body frame, in assembly order."""
    tilt = cfg.case_plate.tilt if tilt is None else tilt
    m, c = cfg.motor, cfg.clutch
    zc, z = sc.levels(cfg), layout.levels(cfg)
    off = Pos(0, 0, -zc.floor_top)  # clutch frame to body frame
    down = (0.0, 0.0, -1.0)
    out = [
        Placed("motor", motor_envelope(cfg), "motor", 0, bought=True),
        Placed("motor_shaft", off * (Pos(0, 0, zc.boss_face) * d_bore(m.shaft_d, m.shaft_across_flat, m.shaft_length)
                                     + Pos(0, 0, zc.gearbox_face) * Cylinder(m.boss_d / 2, m.boss_h, align=B)), "steel", 0, bought=True),
    ]
    split = cfg.body.split
    kinds = {"body_core": ("body", 1), "body": ("body", 1), "body_track_gate": ("gate", 3), "body_exit_insert": ("exit", 3)}
    for name, build in body.parts(cfg).items():
        kind, step = kinds.get(name, ("wall", 2) if name.startswith("body_wall") else ("body", 1) if name.startswith("body_half") else ("extender", 15))
        out.append(Placed(name, build(cfg), kind, step))
    out += [
        Placed("pololu_hub", off * _hub(cfg), "alu", 4, bought=True),
        Placed("slip_clutch_hub_gauge", sc.hub_gauge(cfg), "tool", 4, tool=True),
        Placed("slip_clutch_carrier_metal_hub", off * sc.carrier(cfg), "pla", 5),
        Placed("slip_clutch_drive_ring", off * Pos(0, 0, zc.ring_bottom) * sc.drive_ring(cfg), "ring", 6),
        Placed("slip_clutch_disc", off * Pos(0, 0, zc.ring_floor) * sc.disc(cfg), "pla2", 7),
        Placed("slip_clutch_knob", off * Pos(0, 0, zc.top) * sc.knob(cfg), "pla3", 8),
    ]
    out.append(Placed(f"case_plate_{cfg.case_plate.caliber}", Pos(0, 0, z.plate_bottom) * case_plate.plate(cfg), "plate", 9))
    out.append(Placed("slip_clutch_cap", off * cap_on_ring(cfg), "cap", 10))
    _, d = body.outlet(cfg)
    out.append(Placed("drop_tube", drop_tube.placement(cfg) * drop_tube.drop_tube(cfg), "drop", 11, explode=(d.X, d.Y, d.Z)))
    out += [
        Placed("mount_yoke", mount.yoke_in_body(mount.yoke(cfg), cfg), "yoke", 12, explode=down),
        Placed("mount_clamp", mount.clamp_in_body(mount.clamp(cfg), tilt, cfg), "clamp", 13, explode=down),
        Placed("stand_tube", stand_tube(tilt, cfg), "tube", 13, explode=down, bought=True),
        Placed("mount_tilt_link", mount.link_in_body(mount.adjustable_link(tilt, cfg), tilt, cfg), "link", 14, explode=(1.0, 0.0, 0.0)),
        Placed("electronics_box", electronics.box_frame(tilt, cfg) * electronics.box(cfg), "elec", 16, explode=down),
        Placed("electronics_lid", electronics.box_frame(tilt, cfg) * electronics.lid(cfg), "lid", 16, explode=down),
    ]
    if split == "halves":  # the two halves part sideways in the exploded view
        a = math.radians(cfg.body.halves_seam)
        n = (-math.sin(a), math.cos(a), 0.0)
        out = [Placed(p.name, p.shape, p.kind, p.step, (n if p.name.endswith("0") else tuple(-v for v in n)), p.bought, p.tool)
               if p.name.startswith("body_half") else p for p in out]
    return out


@dataclass(frozen=True)
class Fastener:
    """Bought fasteners of one kind on one host part, drawn at nominal size."""
    name: str  # BOM item
    kind: str  # material group in the viewer
    shape: Part  # local frame: seated at z = 0, it goes in along -z
    at: tuple  # Locations in the body frame
    host: str  # placed part it goes in with
    seq: int  # 0: pressed into the host before assembly, 1: screws and the washers under their heads, 2: nuts and their washers


def _shank(size: str, length: float) -> Part:
    return Cylinder(fasteners.nominal_d(size) / 2, length, align=fasteners.DOWN)


def _socket_screw(size: str, length: float) -> Part:
    h = fasteners.socket_screw(size, length).screw_data
    return Cylinder(h["dk"] / 2, h["k"], align=B) + _shank(size, length)


def _hex_screw(size: str, length: float) -> Part:
    h = fasteners.hex_screw(size, length).screw_data
    return hex_prism(h["s"], h["k"]) + _shank(size, length)


def _countersunk_screw(size: str, length: float) -> Part:
    r, rk = fasteners.nominal_d(size) / 2, fasteners.countersunk_screw(size, length).screw_data["dk"] / 2
    return _shank(size, length) + Cone(r, rk, rk - r, align=fasteners.DOWN)  # 90 deg head, length includes it


def _nut(size: str, af: float, m: float) -> Part:
    return hex_prism(af, m) - Cylinder(fasteners.nominal_d(size) / 2, m, align=B)


def _washer(size: str) -> Part:
    w = fasteners.washer_data(size)
    return Cylinder(w["d2"] / 2, w["h"], align=B) - Cylinder(w["d1"] / 2, w["h"], align=B)


def _insert(size: str, cfg: Config) -> Part:
    """Tube as wide as its hole: a misplaced insert cuts the host."""
    ins = cfg.fasteners.inserts[size]
    return Cylinder(ins.hole_d / 2, ins.length, align=fasteners.DOWN) - Cylinder(fasteners.nominal_d(size) / 2, ins.length, align=fasteners.DOWN)


def _insert_name(size: str, cfg: Config) -> str:
    return f"CNC Kitchen heat-set insert {size} x {cfg.fasteners.inserts[size].length:g}"


def _nut_name(size: str) -> str:
    return f"ISO 4032 {size} nut"


def _half(x: float, y: float, cfg: Config) -> int:
    """Body half that holds the point (x, y), split `halves`."""
    a = math.radians(cfg.body.halves_seam)
    return 0 if -x * math.sin(a) + y * math.cos(a) > 0 else 1


def _pin_stack(size: str, length: float, face: float, nut_af: float, nut_h: float, head: str) -> list[tuple]:
    """Bolt along x through ears whose outer faces are at +-`face`, head at -x, washer on both sides and a DIN 985
    nut: (name, kind, shape, location about the pin centre, seq)."""
    wh = fasteners.washer_data(size)["h"]
    bolt = (f"ISO 4017 {size} x {length:g}", "screw", _hex_screw(size, length)) if head == "hex" else (f"ISO 4762 {size} x {length:g}", "screw", _socket_screw(size, length))
    washer = (f"ISO 7089 {size} washer", "washer", _washer(size))
    return [
        (*bolt, Pos(-face - wh, 0, 0) * Rot(Y=-90), 1),
        (*washer, Pos(-face, 0, 0) * Rot(Y=-90), 1),
        (*washer, Pos(face, 0, 0) * Rot(Y=90), 2),
        (f"DIN 985 {size} nylon lock nut", "nut", _nut(size, nut_af, nut_h), Pos(face + wh, 0, 0) * Rot(Y=90), 2),
    ]


def fasteners_in_body(cfg: Config = CFG, tilt: float | None = None) -> list[Fastener]:
    """Every bought screw, bolt, nut, washer and heat-set insert, body frame, grouped by name, host and seq."""
    tilt = cfg.case_plate.tilt if tilt is None else tilt
    b, m, c, mt, mh, f = cfg.body, cfg.motor, cfg.clutch, cfg.mount, cfg.metal_hub, cfg.print.fit
    z, zc = layout.levels(cfg), sc.levels(cfg)
    off = Pos(0, 0, -zc.floor_top)
    main = {"arcs": "body_core", "one_piece": "body"}.get(b.split)
    items = []  # (name, kind, shape, location, host, seq)

    def body_host(x: float, y: float) -> str:
        return main or f"body_half_{_half(x, y, cfg)}"

    def insert(size: str, loc, host: str):
        items.append((_insert_name(size, cfg), "insert", _insert(size, cfg), loc, host, 0))

    def screw(size: str, length: float, loc, host: str, seq: int = 1):
        items.append((f"ISO 4762 {size} x {length:g}", "screw", _socket_screw(size, length), loc, host, seq))

    for x, y in layout.motor_screws(cfg):
        items.append((f"ISO 10642 {m.mount_screw_size} x {m.mount_screw_length:g}", "screw", _countersunk_screw(m.mount_screw_size, m.mount_screw_length), Pos(x, y, z.floor_top), body_host(x, y), 1))
    for x, y in body.mount_bolts(cfg):
        insert(mt.bolt_size, Pos(x, y, z.bottom) * Rot(X=180), body_host(x, y))
        screw(mt.bolt_size, mount.yoke_bolt_length(cfg), mount.yoke_frame(cfg) * Pos(x, y, mt.yoke_t - mount.yoke_cb_depth(cfg)), "mount_yoke")
    if b.split == "arcs":
        seams, span, jz = body._seam_angles(cfg), 360 / b.wall_segments, body._joint_z(cfg)
        for ang in body.joint_angles(cfg):
            insert(b.joint_screw_size, Rot(Z=ang) * Pos(body.joint_insert_r(cfg), 0, jz) * Rot(Y=90), "body_core")
            wall = next(i for i, a0 in enumerate(seams) if 0 < (ang - a0) % 360 < span)
            screw(b.joint_screw_size, b.joint_screw_length, Rot(Z=ang) * Pos(layout.bowl_r(cfg) + b.wall_t, 0, jz) * Rot(Y=90), f"body_wall_{wall}")
    seam_ends = [(b.halves_seam, 1), (b.halves_seam + 180, -1)]  # seam angle, side of half 0 in the post frame
    head = body.post_lengths(cfg)[0]
    if b.split == "halves":
        for ang, s in seam_ends:
            for zz in body.post_screw_z(cfg):
                screw(b.joint_screw_size, b.joint_screw_length, Rot(Z=ang) * Pos(body.post_axis_r(cfg), s * (f / 2 + head), zz) * Rot(X=-90 * s), "body_half_0")
                insert(b.joint_screw_size, Rot(Z=ang) * Pos(body.post_axis_r(cfg), -s * f / 2, zz) * Rot(X=-90 * s), "body_half_1")
    if b.extender_h:
        for ang, zz in body.extender_screw_z(cfg):
            s = dict(seam_ends)[ang]
            screw(b.joint_screw_size, b.joint_screw_length, Rot(Z=ang) * Pos(body.extender_post_axis_r(cfg), s * (f / 2 + head), zz) * Rot(X=-90 * s), "body_extender_0")
            insert(b.joint_screw_size, Rot(Z=ang) * Pos(body.extender_post_axis_r(cfg), -s * f / 2, zz) * Rot(X=-90 * s), "body_extender_1")
        size, length = b.joint_screw_size, body.extender_wall_screw_length(cfg)
        nut = fasteners.nut_data(size)
        for ang, zz in body.extender_wall_screws(cfg):  # countersunk from inside the bowl into a nut captive in the extender
            host = f"body_extender_{_half(math.cos(math.radians(ang)), math.sin(math.radians(ang)), cfg)}"
            items.append((_nut_name(size), "nut", _nut(size, nut["s"], nut["m"]), body.extender_nut_seat(ang, zz, cfg), host, 0))
            items.append((f"ISO 10642 {size} x {length:g}", "screw", _countersunk_screw(size, length), body.extender_screw_seat(ang, zz, cfg), host, 1))
    carrier = "slip_clutch_carrier_metal_hub"
    nut = fasteners.nut_data(mh.hole_size)
    for p in sc._around(mh.screws, mh.hole_pcd / 2):
        screw(mh.hole_size, mh.screw_length, off * p * Pos(0, 0, zc.base_top), carrier)
        if not mh.threaded:  # nut under the flange
            items.append((_nut_name(mh.hole_size), "nut", _nut(mh.hole_size, nut["s"], nut["m"]), off * p * Pos(0, 0, zc.hub_bottom + mh.boss_h) * Rot(X=180), carrier, 2))
    insert(c.knob_screw_size, off * Pos(0, 0, zc.top), carrier)
    k = fasteners.hex_screw(c.knob_screw_size, c.knob_screw_length).screw_data["k"]
    items.append((f"ISO 4017 {c.knob_screw_size} x {c.knob_screw_length:g}", "screw", _hex_screw(c.knob_screw_size, c.knob_screw_length), off * Pos(0, 0, zc.top + c.knob_t - k), "slip_clutch_knob", 1))
    d = cfg.drop_tube
    mouth = drop_tube.placement(cfg).location * drop_tube.screw_mouth(cfg)
    insert(d.screw_size, mouth, "drop_tube")
    k = drop_tube.dims(cfg)
    lift = d.screw_length - (k.r_socket + k.screw_boss_t - k.r_spigot)  # tip on the spigot, head off the boss
    thumb = _shank(d.screw_size, d.screw_length) + Cylinder(d.collar_d / 2, d.head_h - d.knurl_h, align=B) + Pos(0, 0, d.head_h - d.knurl_h) * Cylinder(d.knurl_d / 2, d.knurl_h, align=B)
    items.append((f"DIN 464 {d.screw_size} x {d.screw_length:g} thumb screw", "screw", thumb, mouth * Pos(0, 0, lift), "drop_tube", 1))
    # clamp and box collar screws along x: washer and head in the -x counterbore, nut in the +x pocket
    L, w = mount.clamp_layout(cfg), mount.clamp_width(cfg)
    wh, nut = fasteners.washer_data(mt.clamp_size)["h"], fasteners.nut_data(mt.clamp_size)
    box = electronics.box_frame(tilt, cfg)
    for frame, zs, host in ((mount.clamp_frame(tilt, cfg), mount.clamp_screw_z(cfg), "mount_clamp"), (box, electronics.collar_screw_z(cfg), "electronics_box")):
        for zz in zs:
            seat = frame * Pos(-w / 2 + mount.clamp_cb_depth(cfg), L["y_s"], zz) * Rot(Y=-90)
            items.append((f"ISO 7089 {mt.clamp_size} washer", "washer", _washer(mt.clamp_size), seat, host, 1))
            screw(mt.clamp_size, mount.clamp_bolt_length(cfg), seat * Pos(0, 0, wh), host)
            items.append((_nut_name(mt.clamp_size), "nut", _nut(mt.clamp_size, nut["s"], nut["m"]), frame * mount.clamp_nut_pocket(zz, cfg) * Pos(0, 0, -nut["m"]), host, 2))
    e = cfg.electronics
    for x, y in electronics.lid_screws(cfg):
        insert(e.lid_screw_size, box * Pos(x, y, 0) * Rot(X=180), "electronics_box")
        screw(e.lid_screw_size, electronics.lid_screw_length(cfg), box * Pos(x, y, -e.lid_t) * Rot(X=180), "electronics_lid")
    py, pz = mount.pivot_point(cfg)
    pivot = _pin_stack(mt.pivot_size, mount.pivot_bolt_length(cfg), mount.ear_gap(cfg) / 2 + mt.ear_t, mt.pivot_nut_af, mt.pivot_nut_h, "hex")
    items += [(n, kd, sh, Pos(0, py, pz) * loc, "mount_clamp", sq) for n, kd, sh, loc, sq in pivot]
    pins = _pin_stack(mt.link_pin_size, mount.link_pin_length(cfg), mount.link_gap(cfg) / 2 + mt.ear_t, mt.link_nut_af, mt.link_nut_h, "socket")
    for y, zz in mount.link_pin_centres(tilt, cfg):
        items += [(n, kd, sh, Pos(0, y, zz) * loc, "mount_tilt_link", sq) for n, kd, sh, loc, sq in pins]
    nut = fasteners.nut_data(mt.link_rod_size)
    for loc in mount.rod_nuts(tilt, cfg):
        items.append((_nut_name(mt.link_rod_size), "nut", _nut(mt.link_rod_size, nut["s"], nut["m"]), loc, "mount_tilt_link", 0))
    groups: dict = {}
    for name, kind, shape, loc, host, seq in items:
        groups.setdefault((name, host, seq), (kind, shape, []))[2].append(loc)
    return [Fastener(name, kind, shape, tuple(locs), host, seq) for (name, host, seq), (kind, shape, locs) in groups.items()]


def pivot_axis(tilt: float, cfg: Config = CFG) -> tuple[float, float, float]:
    """Stand tube axis in the body frame."""
    py, pz = mount.pivot_point(cfg)
    v = Plane(Pos(0, py, pz) * Rot(X=-tilt) * Pos(0, 0, -mount.clamp_pivot_z(cfg))).z_dir
    return v.X, v.Y, v.Z
