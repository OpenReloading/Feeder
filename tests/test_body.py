import itertools
import math
from dataclasses import replace

import pytest
from build123d import Box, Cylinder, Pos, Rot, extrude
from shapely.geometry import Point
from shapely.geometry import Polygon as ShapelyPolygon
from test_mount import _unsupported

from feeder import assembly, printing
from feeder.config import CFG, GENERIC_8MM_FLANGE
from feeder.lib import fasteners
from feeder.lib.features import d_bore
from feeder.parts import body as b
from feeder.parts import case_plate as cp
from feeder.parts import layout
from feeder.parts import slip_clutch as sc

B, T, E, M, MH, FIT = CFG.body, CFG.track, CFG.exit, CFG.motor, CFG.metal_hub, CFG.print.fit
MW = CFG.print.min_wall
CAL = layout.caliber()


@pytest.fixture(scope="module")
def parts():
    return {name: build() for name, build in b.PARTS.items()}


def test_track_gap_stays_under_the_rim_thickness():
    z = layout.levels()
    lowest = z.plate_bottom - layout.seat_drop() - z.deck_top  # ring cone at full clearance
    highest = z.plate_bottom - z.deck_top  # cone without clearance
    half_flat = CFG.case_plate.flatness / 2
    assert lowest - half_flat > 0  # the plate does not drag on the deck
    assert highest + half_flat < CAL.rim_t_min  # no rim wedges between plate and deck


def test_exit_insert_and_wall_seams_keep_the_minimum_wall():
    length, r0, r1 = b.opening()
    assert layout.bowl_r() - FIT - r1 >= MW  # the opening's outer edge is an arc under the band
    assert b.seam_lap() >= MW


def test_countersink_is_widest_at_the_surface():
    tool = fasteners.countersink(M.mount_screw_size, M.mount_screw_length, B.floor_t)
    head_r = fasteners.countersunk_screw(M.mount_screw_size, M.mount_screw_length).screw_data["dk"] / 2
    top = tool & Pos(0, 0, -0.05) * Box(30, 30, 0.1)
    assert top.bounding_box().size.X / 2 >= head_r


def test_insert_recess_keeps_the_deck():
    assert E.seat_t + FIT <= B.deck_t - MW
    assert E.seat_w >= MW


def test_gate_sits_behind_the_band_face_with_a_lead_in():
    assert T.gate_setback >= 2 * FIT  # band and gate each shift by a fit against the wall
    assert T.gate_chamfer >= T.gate_setback + 2 * FIT  # the 45 deg chamfer spans the step from the gate face
    assert T.band_t / 2 - FIT >= MW / 2 and T.gate_lap >= 2 * MW  # lap halves and overlap


def test_opening_takes_every_pocket_and_case():
    length, r0, r1 = b.opening()
    r, d = layout.pocket_circle_r(), layout.pocket_d()
    assert r0 < r - d / 2 and r1 > r + d / 2
    assert length > CAL.case_length + d  # case drops before the far edge
    assert r1 + E.wall < layout.bowl_r()
    assert b.bore_d() >= CAL.rim_d + 0.4
    assert E.wall >= CFG.print.min_wall


def test_exit_insert_fills_its_shaft_and_sits_on_the_deck(parts):
    z = layout.levels()
    core, ins = parts["body_core"], parts["body_exit_insert"]
    slab = Pos(0, 0, (z.bottom + z.deck_bottom) / 2) * Box(400, 400, 1)
    shaft = slab & b._exit_cut(CFG) & Cylinder(layout.bowl_r() - FIT, 1000)
    gap = shaft - ins - b._funnel(CFG, 0.0)  # what of the shaft is neither insert nor case path
    perimeter = sum(e.length for e in b._exit_outline(CFG, 0.0).edges())
    assert gap.volume < perimeter * FIT * 1.1  # only the fit ring round the block, 1 mm slab
    assert (core & ins).volume < 1e-3
    seat = Pos(0, 0, z.deck_top - E.seat_t - 0.05) * Box(400, 400, 0.1)
    assert (core & seat & Pos(0, 0, -0.1) * ins).volume > 1  # lowered 0.1, the ledge meets the recess floor round the shaft
    assert ins.bounding_box().min.Z < z.bottom  # funnel end and spigot below the body
    shaft_plan = ShapelyPolygon([(v.X, v.Y) for v in b._exit_outline(CFG, 0.0).vertices()]).buffer(1e-3)
    verts, _ = ins.tessellate(0.05)
    assert all(shaft_plan.contains(Point(v.X, v.Y)) for v in verts if v.Z < z.deck_top - E.seat_t - 1e-3)  # it drops in from above


def test_exit_outlet_is_below_the_body_and_clear_of_the_motor():
    o, d = b.outlet()
    end = o + d * E.spigot_len
    assert end.Z < layout.levels().bottom
    assert math.hypot(end.X, end.Y) > M.gearbox_l  # past the gearbox at any motor angle


def test_seams_stay_off_the_exit_and_the_low_side():
    for a in b._seam_angles(CFG):
        for avoid in (b.EXIT_ANGLE, b.EXIT_ANGLE + 180):
            assert abs((a - avoid + 180) % 360 - 180) > b.exit_half_angle() + B.joint_exit_margin


def test_wall_screws_are_standard_and_engage_the_inserts():
    size, length = B.joint_screw_size, B.joint_screw_length
    assert length in fasteners.socket_screw_lengths(size)
    ins = CFG.fasteners.inserts[size]
    engaged = length - B.wall_t - B.seam_key - FIT
    assert engaged >= CFG.fasteners.min_engagement * fasteners.nominal_d(size)
    assert engaged <= ins.hole_depth
    z = layout.levels()
    assert z.deck_bottom - z.bottom >= ins.od + 2 * ins.min_wall  # insert fits under the deck


def test_motor_screws_are_standard_and_fit_the_gearbox_thread():
    size, length = M.mount_screw_size, M.mount_screw_length
    assert length in fasteners.countersunk_screw_lengths(size)
    engaged = length - B.floor_t
    assert fasteners.nominal_d(size) <= engaged <= M.mount_thread_depth  # 1 d in metal


def test_mount_inserts_fit_under_the_deck():
    z = layout.levels()
    ins = CFG.fasteners.inserts[CFG.mount.bolt_size]
    assert z.deck_bottom - z.bottom >= ins.hole_depth + CFG.print.min_wall
    for x, y in b.mount_bolts():
        assert layout.cup_r() + B.cup_wall + ins.od < math.hypot(x, y) < layout.bowl_r() - B.skirt_t - ins.od


def test_deck_bridges_between_the_ribs():
    r = b._skirt_r(CFG) - B.skirt_t  # widest gap, at the skirt
    assert 2 * math.pi * r / B.rib_count - B.rib_t <= CFG.print.bridge


def test_can_tunnel_prints_under_a_solid_block(parts):
    z = layout.levels()
    _, _, w = b._can_extent(CFG)
    assert w - 2 * B.can_relief <= CFG.print.bridge  # flat tunnel top
    above = Rot(Z=M.angle) * (b._can_block(CFG) - b.can_tunnel(CFG))
    above &= Pos(0, 0, z.bottom + B.can_relief) * Box(1000, 1000, z.deck_bottom - z.bottom - B.can_relief, align=sc.BOTTOM)
    missing = above - parts["body_core"]
    assert (missing.volume if missing.solids() else 0.0) < 1e-3  # solid all the way from the tunnel top to the deck


SPLITS = ("arcs", "halves", "one_piece")
GAP = 0.5  # mm, largest gap a mating pair may show: fits and hole clearances, no part floats


def _cfg(split):
    return replace(CFG, body=replace(B, split=split))


CONFIGS = {  # the body splits, then the default body with a printed fixed link and with the generic flange hub
    **{split: _cfg(split) for split in SPLITS},
    "fixed_link_50": replace(CFG, mount=replace(CFG.mount, link=50.0)),
    "generic_hub": b.with_hub(CFG, GENERIC_8MM_FLANGE),
}


@pytest.fixture(scope="module", params=CONFIGS)
def assembled(request):
    cfg = CONFIGS[request.param]
    return cfg, {p.name: p for p in assembly.placed(cfg)}


def test_variant_body_parts_are_single_valid_solids_that_fit_the_bed(assembled):
    cfg, placed = assembled
    for name, build in b.parts(cfg).items():
        part = placed[name].shape
        assert part.is_valid and len(part.solids()) == 1, name
        assert printing.fits(printing.on_bed(name, part, cfg), cfg), name


def _mates(cfg) -> dict[str, tuple[str, ...]]:
    """Each part and the parts it sits on: it must come within GAP of at least one of them."""
    split = cfg.body.split
    main = {"arcs": ("body_core",), "halves": ("body_half_0", "body_half_1"), "one_piece": ("body",)}[split]
    walls = {"arcs": tuple(f"body_wall_{i}" for i in range(B.wall_segments)), "halves": main, "one_piece": main}[split]
    out = {
        "motor_shaft": ("motor",),
        **{n: ("motor",) for n in main},
        **{f"body_wall_{i}": ("body_core",) for i in range(B.wall_segments) if split == "arcs"},
        **({"body_extender": walls} if B.extender_h else {}),
        "body_track_gate": ("body_exit_insert",),
        "body_exit_insert": main,
        "pololu_hub": ("motor_shaft",),
        "slip_clutch_carrier_metal_hub": ("pololu_hub",),
        "slip_clutch_drive_ring": ("slip_clutch_carrier_metal_hub",),
        "slip_clutch_disc": ("slip_clutch_drive_ring",),
        "slip_clutch_knob": ("slip_clutch_carrier_metal_hub",),
        f"case_plate_{CFG.case_plate.caliber}": ("slip_clutch_drive_ring",),
        "slip_clutch_cap": (f"case_plate_{CFG.case_plate.caliber}",),
        "drop_tube": ("body_exit_insert",),
        "mount_yoke": main,
        "mount_clamp": ("mount_yoke",),
        assembly.link_name(assembly.body_tilt(cfg), cfg): ("mount_yoke", "mount_clamp"),
        "stand_tube": ("mount_clamp",),
        "electronics_box": ("stand_tube",),
        "electronics_lid": ("electronics_box",),
        "timer_relay": ("electronics_box",),
        "gx12_2_pin_socket": ("electronics_box",),
        "gx12_3_pin_socket": ("electronics_box",),
        "pwm_knob": ("electronics_lid",),
        "toggle_switch": ("electronics_lid",),
        "dc_jack": ("electronics_lid",),
        "pwm_controller": ("pwm_knob",),
        "level_sensor": ("drop_tube",),
    }
    if split == "halves":
        out["body_half_1"] = ("body_half_0",)
    return out


def test_no_part_floats(assembled):
    cfg, placed = assembled
    mates = _mates(cfg)
    assert set(mates) | {"motor"} == {n for n, p in placed.items() if not p.tool}  # every part but the base has a mate listed
    for name, others in mates.items():
        gap = min(placed[name].shape.distance_to(placed[o].shape) for o in others)
        assert gap <= GAP, f"{name} is {gap:.2f} mm from {others}"


def test_assembly_has_no_interference(assembled):
    _, placed = assembled
    solids = {n: p.shape for n, p in placed.items() if not p.tool}
    for (na, pa), (nb, pb) in itertools.combinations(solids.items(), 2):
        ba, bb = pa.bounding_box(), pb.bounding_box()
        if any(getattr(ba.max, a) <= getattr(bb.min, a) or getattr(bb.max, a) <= getattr(ba.min, a) for a in "XYZ"):
            continue
        overlap = pa & pb
        volume = overlap.volume if overlap.solids() else 0.0
        assert volume < 1e-3, f"{na} overlaps {nb} by {volume:.4f} mm3"


def _lift_path(shape, up: float = 150.0):
    """The top faces of `shape` swept straight up: a part with no overhang lifts out through it."""
    top = shape.bounding_box().max.Z
    return [extrude(f, up) for f in shape.faces() if abs(f.center().Z - top) < 1e-6 and f.normal_at().Z > 0.99]


def test_gate_and_exit_insert_lift_out_of_the_core(assembled):
    _, placed = assembled
    off_first = {"body_track_gate": ("case_plate", "slip_clutch_cap"), "body_exit_insert": ("case_plate", "slip_clutch_cap", "body_track_gate")}
    for name, gone in off_first.items():
        path = _lift_path(placed[name].shape)
        assert path, name
        for other, p in placed.items():
            if p.tool or other == name or other.startswith(gone):
                continue
            for prism in path:
                common = prism & p.shape
                volume = common.volume if common.solids() else 0.0
                assert volume < 1e-3, f"{other} is in the way of {name} by {volume:.4f} mm3"


def test_halves_seam_screws_pass_both_posts():
    cfg = _cfg("halves")
    h0, h1 = b.half(0, cfg), b.half(1, cfg)
    head, ins = b.post_lengths(cfg)
    insert = cfg.fasteners.inserts[B.joint_screw_size]
    engage = B.joint_screw_length - head - FIT
    assert CFG.fasteners.min_engagement * fasteners.nominal_d(B.joint_screw_size) <= engage <= insert.hole_depth  # tip ends in the insert hole
    r = layout.bowl_r(cfg) + B.wall_t + (insert.od + 2 * insert.min_wall) / 2
    d = fasteners.nominal_d(B.joint_screw_size)
    for ang, s0 in ((B.halves_seam, 1), (B.halves_seam + 180, -1)):  # s0: side of half 0 in the post frame
        for z in b.post_screw_z(cfg):
            centre = s0 * (FIT / 2 + head - B.joint_screw_length / 2)  # head on the outer face of the half 0 post
            screw = Rot(Z=ang) * Pos(r, centre, z) * Rot(X=90) * Cylinder(d / 2, B.joint_screw_length)
            for h in (h0, h1):
                assert screw.distance_to(h) < 1 and _overlap_volume(screw, h) < 1e-3, (ang, z)  # in the holes of both halves
    assert layout.levels(cfg).bottom + b.post_h(cfg) < layout.levels(cfg).wall_top - B.extender_lap  # posts stay under the extender sleeve


def test_extender_is_an_open_arc_over_the_low_side_that_holds_level_brass_at_the_steepest_tilt():
    ext = b.extender()
    a0, a1 = b.extender_span()
    assert ext.is_valid and len(ext.solids()) == 1
    assert (a0 + a1) / 2 == 270 and a1 - a0 < 180  # centred on the low side, the high side stays open
    assert ext.bounding_box().max.Y < 0
    R, z = layout.bowl_r(), layout.levels()
    tan = math.tan(math.radians(CFG.mount.tilt_range[1]))
    level = z.wall_top + B.extender_h - R * tan  # level brass surface at y = 0, from the extender top on the low side
    for ang in range(360):
        y = R * math.sin(math.radians(ang))
        if b.wall_top_at(y) + y * tan < level - 1e-6:  # the wall alone would let the brass over
            assert a0 <= ang <= a1, ang
    assert b.rim_top(270) == pytest.approx(z.wall_top + B.extender_h)
    assert b.rim_top(90) == pytest.approx(b.wall_low())  # open high side
    assert b.rim_top(90, extender=False) == b.rim_top(90)
    assert B.extender_lap >= 15


def _overlap_volume(a, c):
    common = a & c
    return common.volume if common.solids() else 0.0


def test_halves_seam_misses_the_exit_motor_screws_mount_inserts_tabs_and_can_tunnel():
    cfg = _cfg("halves")
    a = math.radians(B.halves_seam)
    n = (-math.sin(a), math.cos(a))
    dist = lambda x, y: abs(x * n[0] + y * n[1])  # noqa: E731
    head_r = fasteners.countersunk_screw(M.mount_screw_size, M.mount_screw_length).screw_data["dk"] / 2
    assert all(dist(x, y) > head_r + FIT for x, y in layout.motor_screws(cfg))  # each screw whole in one half
    ins = cfg.fasteners.inserts[CFG.mount.bolt_size]
    assert all(dist(x, y) > ins.od / 2 + ins.min_wall for x, y in b.mount_bolts(cfg))
    x0, length, w = b._can_extent(cfg)
    can = math.radians(M.angle)
    corners = [(t * math.cos(can) - s * w / 2 * math.sin(can), t * math.sin(can) + s * w / 2 * math.cos(can)) for t in (x0, x0 + length) for s in (-1, 1)]
    sides = {math.copysign(1, x * n[0] + y * n[1]) for x, y in corners}
    assert len(sides) == 1 and all(dist(x, y) > MW for x, y in corners)  # whole tunnel in one half: cut lengthwise, its ceiling hangs free
    for ang in (b.EXIT_ANGLE,):
        off = (ang - B.halves_seam) % 180
        assert min(off, 180 - off) > b.exit_half_angle(cfg) + 5, ang


def test_wall_top_is_open_on_the_high_side_and_holds_level_brass():
    z, R = layout.levels(), layout.bowl_r()
    assert b.wall_top_at(-R) == pytest.approx(z.wall_top)
    assert b.wall_top_at(R) == pytest.approx(max(b.wall_low(), z.wall_top - 2 * R * math.tan(math.radians(b.wall_slant()))))
    assert b.wall_low() >= z.plate_top + CAL.case_length  # a case standing on the plate stays in
    t = math.radians(CFG.mount.tilt_range[0])  # flattest tilt: the level brass surface leans least in the body frame
    world = lambda y, zz: y * math.sin(t) + zz * math.cos(t)  # noqa: E731
    ring = b._wall_ring(CFG)
    for y in range(-120, 121, 20):
        assert world(y, b.wall_top_at(y)) >= world(-R, z.wall_top) - 1e-6  # brass level with the low-side top stays in
        x = math.sqrt(R ** 2 - y ** 2) + B.wall_t / 2
        top = (ring & Pos(x, y, 0) * Box(0.5, 0.1, 1000)).bounding_box().max.Z  # a thin probe: the top falls 0.84 mm per mm of y at the wall slant
        assert top == pytest.approx(b.wall_top_at(y), abs=0.2), y  # the wall solid follows the profile


def test_bowl_holds_the_design_fill():
    cp_, (lo, hi) = CFG.case_plate, CFG.mount.tilt_range
    z = layout.levels()
    assert layout.capacity(cp_.tilt) >= cp_.fill_cases  # default tilt, no extender
    assert layout.capacity(cp_.tilt, rim=lambda a: b.rim_top(a, extender=False)) == layout.capacity(cp_.tilt)  # the wall top profile gives the level plane
    assert layout.capacity(hi, rim=b.rim_top) >= cp_.fill_cases  # steepest tilt with the extender
    assert all(layout.capacity(t, rim=b.rim_top) >= layout.capacity(t) for t in (lo, cp_.tilt, hi))  # the extender never holds less
    assert layout.capacity(45, 70) < cp_.fill_cases < layout.capacity(40, 95)  # the estimate's scale: 70 mm was too low


def test_extender_is_screwed_to_the_wall_through_the_sleeve_lap():
    size, length = B.joint_screw_size, b.extender_wall_screw_length()
    nut = fasteners.nut_data(size)
    assert length in fasteners.countersunk_screw_lengths(size)
    assert length - 2 * B.wall_t - FIT >= nut["m"] + CFG.fasteners.coarse_pitch[size]  # through the nut with a thread to spare
    head = fasteners.countersunk_screw(size, length).screw_data["dk"] / 2 + CFG.fasteners.head_fit - fasteners.clearance_d(size) / 2
    assert B.wall_t - head >= MW / 2  # countersink depth leaves wall behind it
    screws = b.extender_wall_screws()
    assert len(screws) == B.extender_wall_screws
    R = layout.bowl_r()
    a0, a1 = b.extender_span()
    seams = b._seam_angles(CFG) if B.split == "arcs" else []
    head_r = fasteners.countersunk_screw(size, length).screw_data["dk"] / 2 + CFG.fasteners.head_fit
    clear = math.degrees((head_r + B.seam_key + FIT) / R)  # the countersink stays off the arc ends and the wall seam laps
    for ang, z in screws:
        top = b.wall_top_at(R * math.sin(math.radians(ang)))
        assert top - B.extender_lap + 4 <= z <= top - 4  # inside the sleeve lap
        assert a0 + clear <= ang <= a1 - clear  # on the arc, off its ends
        for seam in seams:
            assert abs((ang - seam + 180) % 360 - 180) > clear


def test_extender_sits_on_the_wall_top_and_prints_on_its_flat_top():
    ring = b._wall_ring(CFG)
    ext = b.extender()
    assert (ext & ring).volume < 1e-3
    assert (Pos(0, 0, -0.1) * ext & ring).volume > 10  # lowered 0.1 it meets the wall top
    bed = printing.on_bed("body_extender", ext)
    assert printing.fits(bed)
    assert _unsupported(Pos(0, 0, -0.013) * bed) == []


def test_generic_hub_keeps_the_outlet_where_it_is_under_the_body():
    cfg = b.with_hub(CFG, GENERIC_8MM_FLANGE)
    assert layout.levels(cfg).deck_top > layout.levels(CFG).deck_top  # the taller hub raises the deck
    assert b.outlet(cfg)[0].Z == pytest.approx(b.outlet(CFG)[0].Z)
    assert b.with_hub(CFG, CFG.metal_hub) == CFG  # the default hub changes nothing
