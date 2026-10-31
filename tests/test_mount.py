import itertools
import math
from dataclasses import replace

import numpy as np
import pytest
import trimesh
from build123d import Box, CenterOf, Compound, Cylinder, GeomType, Plane, Pos, Rot
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

from feeder import assembly
from feeder.assembly import motor_envelope
from feeder.assembly import stand_tube as assembly_stand_tube
from feeder.config import CFG
from feeder.lib import fasteners
from feeder.parts import body as b
from feeder.parts import case_plate as cp
from feeder.parts import drop_tube as dt
from feeder.parts import layout
from feeder.parts import mount as m
from feeder.parts import slip_clutch as sc

MT, M, FIT, MW = CFG.mount, CFG.motor, CFG.print.fit, CFG.print.min_wall
G = m.G


@pytest.fixture(scope="module")
def parts():
    return {name: build() for name, build in m.PARTS.items()}


DROP_TUBE = 150.0  # mm of drop tube kept free beyond the spigot end, long enough to pass the clamp


@pytest.fixture(scope="module")
def fixed():
    o, d = b.outlet()
    path = Plane(origin=o, z_dir=d) * Cylinder(b.bore_d() / 2 + CFG.exit.wall, CFG.exit.spigot_len + DROP_TUBE, align=sc.BOTTOM)
    drop_tube = dt.placement() * dt.drop_tube()
    return {"core": b.core(), "exit_insert": b.exit_insert(), "motor": motor_envelope(), "drop_path": path, "drop_tube": drop_tube}


def _overlap(pa, pb):
    ba, bb = pa.bounding_box(), pb.bounding_box()
    if any(getattr(ba.max, a) <= getattr(bb.min, a) or getattr(bb.max, a) <= getattr(ba.min, a) for a in "XYZ"):
        return 0.0
    common = pa & pb
    return common.volume if common.solids() else 0.0


def _hardware(tilt, size):
    """Placed fasteners of `size` on the mount, body frame: the pivot (M10) or the link pins and rod nuts (M6)."""
    return {f"{f.name} {i}": loc * f.shape for f in assembly.fasteners_in_body(CFG, tilt) if f" {size} " in f"{f.name} " for i, loc in enumerate(f.at)}


def test_mount_parts_are_single_valid_solids(parts):
    for name, part in parts.items():
        assert part.is_valid, name
        assert len(part.solids()) == 1, name


def test_screw_lengths_are_standard_and_engage():
    ins = CFG.fasteners.inserts[MT.bolt_size]
    length = m.yoke_bolt_length()
    assert length in fasteners.socket_screw_lengths(MT.bolt_size)
    engaged = length - (MT.yoke_t - m.yoke_cb_depth())
    assert CFG.fasteners.min_engagement * fasteners.nominal_d(MT.bolt_size) <= engaged <= ins.hole_depth
    assert MT.yoke_t - m.yoke_cb_depth() >= MW  # floor under the head
    assert m.pivot_bolt_length() in fasteners.hex_screw_lengths(MT.pivot_size)
    assert m.clamp_bolt_length() in fasteners.socket_screw_lengths(MT.clamp_size)
    assert m.link_pin_length() in fasteners.socket_screw_lengths(MT.link_pin_size)


def test_pivot_and_link_pins_pass_their_stack_with_a_pitch_beyond_the_nut():
    w = fasteners.washer_data(MT.pivot_size)["h"]
    stack = 2 * w + 2 * MT.ear_t + m.ear_gap() + MT.pivot_nut_h
    assert m.pivot_bolt_length() >= stack + CFG.fasteners.coarse_pitch[MT.pivot_size]
    w = fasteners.washer_data(MT.link_pin_size)["h"]
    stack = 2 * w + 2 * MT.ear_t + m.link_gap() + MT.link_nut_h
    assert m.link_pin_length() >= stack + CFG.fasteners.coarse_pitch[MT.link_pin_size]


def test_clamp_bolt_ends_beyond_the_recessed_nut():
    nut = fasteners.nut_data(MT.clamp_size)
    washer = fasteners.washer_data(MT.clamp_size)
    under_head = m.clamp_width() - m.clamp_cb_depth() + washer["h"]  # head sits on the washer in the counterbore
    assert m.clamp_bolt_length() - under_head >= CFG.fasteners.coarse_pitch[MT.clamp_size]
    assert m.clamp_layout()["cb_r"] > washer["d2"] / 2
    assert m.clamp_cb_depth() + nut["m"] < m.clamp_width()  # pockets do not meet


def test_pivot_hole_and_washer_clearances(parts):
    w = fasteners.washer_data(MT.pivot_size)
    d = fasteners.nominal_d(MT.pivot_size)
    assert d < m.pivot_d() <= d + 2 * FIT * 2  # close fit, a printed hole still takes the bolt
    assert w["d2"] / 2 <= m.ear_r()  # washer inside the ear outline
    assert m.ear_r() - m.pivot_d() / 2 * math.sqrt(2) >= MW  # wall above the 45 deg roof of the hole
    assert m.ear_gap() == pytest.approx(MT.tongue_t + 4 * FIT)
    hw = _hardware(layout.tilt(), MT.pivot_size)
    yoke, clamp = m.yoke_in_body(parts["mount_yoke"]), m.clamp_in_body(parts["mount_clamp"], layout.tilt())
    for name, solid in hw.items():
        for pname, part in (("yoke", yoke), ("clamp", clamp)):
            assert _overlap(solid, part) < 1e-3, f"{name} in {pname}"


def test_link_fork_holds_the_washer_and_a_wall_round_the_pin():
    w = fasteners.washer_data(MT.link_pin_size)
    d = fasteners.nominal_d(MT.link_pin_size)
    assert d < m.link_pin_d() <= d + 2 * FIT * 2
    assert m.fork_r() / math.sqrt(2) >= w["d2"] / 2  # the washer between the 45 deg flanks of a clamp ear
    assert m.fork_r() / math.sqrt(2) - m.link_pin_d() / 2 >= MW
    assert m.link_gap() == pytest.approx(MT.link_t + 4 * FIT)


@pytest.fixture(scope="module")
def tilting(parts):
    """(volume mm3, centroid, optional) of each printed part that tilts with the body, in the body frame."""
    z, zc = layout.levels(), sc.levels()
    off = -zc.floor_top  # carrier frame to body frame
    optional = [build() for name, build in b.PARTS.items() if name.startswith("body_extender")]
    solids = [build() for name, build in b.PARTS.items() if not name.startswith("body_extender")]
    solids += [Pos(0, 0, z.plate_bottom) * cp.plate(), dt.placement() * dt.drop_tube(), m.yoke_in_body(parts["mount_yoke"])]
    solids += [
        Pos(0, 0, off) * sc.carrier(),
        Pos(0, 0, zc.ring_bottom + off) * sc.drive_ring(),
        Pos(0, 0, zc.ring_floor + off) * sc.disc(),
        Pos(0, 0, zc.top + off) * sc.knob(),
        Pos(0, 0, zc.cap_face + off) * sc.cap(),
    ]
    return [(s.volume, s.center(CenterOf.MASS), False) for s in solids] + [(s.volume, s.center(CenterOf.MASS), True) for s in optional]


def _weight_moment(tilting, tilt, fill, motor_mass, brass, extender):
    """Nm about the pivot, + toward a flatter tilt: printed parts at `fill`, the motor envelope, the unmodelled
    mass at the bowl rim on the exit side (its worst place) and `brass` kg on the low side of the plate."""
    z = layout.levels()
    motor = motor_envelope().center(CenterOf.MASS)
    masses = [(v * 1e-6 * CFG.print.density * fill, c.Y, c.Z) for v, c, opt in tilting if extender or not opt]
    masses += [(motor_mass, motor.Y, motor.Z), (MT.unmodelled_mass, layout.bowl_r(), z.bottom)]
    masses += [(brass, -layout.pocket_circle_r(), z.plate_top + 10)]
    py, pz = m.pivot_point()
    return sum(kg * G * m._rot(y - py, zz - pz, tilt)[0] / 1000 for kg, y, zz in masses)


def test_weight_always_turns_the_body_steeper_so_the_link_stays_in_compression(tilting):
    # one load direction: the pins always bear on the same side of their holes, so the play does not move the tilt
    lo, hi = m.tilt_span()
    for tilt in (lo + (hi - lo) * i / 10 for i in range(11)):
        for fill, motor, brass, ext in itertools.product(CFG.print.fill, M.mass, (0.0, CFG.case_plate.drag_mass), (False, True)):
            assert _weight_moment(tilting, tilt, fill, motor, brass, ext) < 0, (tilt, fill, motor, brass, ext)
    assert all(m.link_length(t) > m.link_length(t + 1) for t in range(round(lo), round(hi)))  # steeper: shorter link
    assert lo <= layout.tilt() <= hi


def test_link_sets_the_tilt_to_a_tenth_of_a_degree_per_tenth_of_a_millimetre():
    lo, hi = m.tilt_span()
    for t in range(round(lo), round(hi)):
        assert m.link_length(t) - m.link_length(t + 1) >= 1.0, t  # mm per deg: hole and print errors of 0.1 mm move it 0.1 deg at most
        assert m.link_lever(t) >= 0.5 * math.hypot(*MT.link_a)  # far from the toggle (link through the pivot)


def test_link_and_pivot_loads():
    lo, hi = m.tilt_span()
    f = max(m.link_force(lo + (hi - lo) * i / 20) for i in range(21))
    weight = MT.body_mass * G
    d = fasteners.nominal_d(MT.link_pin_size)
    assert f / MT.stress_area[MT.link_rod_size] <= MT.bolt_yield / 10  # rod in compression, factor 10 on yield
    assert f / (d * MT.link_t) <= MT.bearing_limit  # link and rod end holes
    assert f / (d * 2 * MT.ear_t) <= MT.bearing_limit  # fork ears
    pivot = weight + f  # conservative sum
    d = fasteners.nominal_d(MT.pivot_size)
    assert pivot / (2 * MT.stress_area[MT.pivot_size]) <= 0.6 * MT.bolt_yield / 10  # double shear
    assert pivot / (d * MT.tongue_t) <= MT.bearing_limit  # tongue hole is the weaker bearing
    assert pivot / (d * 2 * MT.ear_t) <= MT.bearing_limit


def _rim():
    """Rim top points (x, y, z), body frame, every 15 deg: the outer top edge of the extender over its arc (it leans in), the wall top elsewhere."""
    bd = CFG.body
    span = b.extender_span() if bd.extender_h else (1, 0)
    pts = []
    for a in range(0, 360, 15):
        on_arc = any(span[0] <= a + k <= span[1] for k in (0, 360))
        ro = b.rim_r(a) + (2 * bd.wall_t + FIT if on_arc else bd.wall_t)
        pts.append((ro * math.cos(math.radians(a)), ro * math.sin(math.radians(a)), b.rim_top(a)))
    return pts


def _world(x, y, z, tilt):
    """Body frame point to the world frame rel. the pivot."""
    py, pz = m.pivot_point()
    return np.array([x, *m._rot(y - py, z - pz, tilt)])


def _body_loads(tilt, at, force):
    """(point, force) pairs on the tilting body in the world frame rel. the pivot: `force` (N) at `at`, the
    weight, and the link force at pin A that balances them about the pivot axis."""
    loads = [(at, np.array(force, float)), (_world(0, *m.com(), tilt), np.array([0, 0, -MT.body_mass * G]))]
    (ay, az), (by, bz) = m.pin_a(tilt), MT.link_b
    u = np.array([0, ay - by, az - bz]) / m.link_length(tilt)  # B to A: a compressed link pushes A this way
    a = np.array([0, ay, az])
    f = -sum(np.cross(r, F)[0] for r, F in loads) / np.cross(a, u)[0]
    return loads + [(a, f * u)], f  # noqa: RUF005


def _section(loads, c):
    """Moment about `c` and force carried by a section that holds the body loads."""
    return sum(np.cross(r - c, F) for r, F in loads), sum(F for _, F in loads)


def _rect_stress(moment, force, dx, dy):
    """Equivalent stress sqrt(s^2 + 3 t^2) on a solid dx by dy section normal to z: bending, axial, torsion."""
    s = 6 * abs(moment[0]) / (dx * dy**2) + 6 * abs(moment[1]) / (dy * dx**2) + abs(force[2]) / (dx * dy)
    lo, hi = sorted((dx, dy))
    t = abs(moment[2]) * (3 + 1.8 * lo / hi) / (hi * lo**2)  # rectangle in torsion, Roark
    return math.hypot(s, math.sqrt(3) * t)


def _peak_stresses(clamp):
    """Highest equivalent stress (MPa) in the tongue stem and at the yoke ear root for `MT.push` at any rim
    point in 8 horizontal directions and straight down, over the tilt span."""
    lo, hi = m.tilt_span()
    zp, er, et = m.clamp_pivot_z(), m.ear_r(), MT.ear_t
    ex = m.ear_gap() / 2 + et / 2
    sections = []
    for zc in np.linspace(MT.clamp_h + 0.5, zp - m.pivot_d() / 2 - 0.5, 16):  # from the block top to the pivot hole
        box = (clamp & Pos(0, 0, zc) * Box(1000, 1000, 0.1)).bounding_box()
        assert box.size.Y == pytest.approx(MT.tongue_w, abs=0.01), zc  # a full rectangle: stem and brace  # noqa: SIM300
        sections.append((zc - zp, box.size.X, box.size.Y))
    dirs = [(math.cos(k * math.pi / 4), math.sin(k * math.pi / 4), 0) for k in range(8)] + [(0, 0, -1)]
    stem = ear = 0.0
    for tilt in (lo + (hi - lo) * i / 8 for i in range(9)):
        _, f0 = _body_loads(tilt, np.zeros(3), (0, 0, 0))
        assert f0 == pytest.approx(m.link_force(tilt), rel=1e-6)  # same statics as the link check
        root = np.array([0, *m._rot(0, MT.pivot_depth, tilt)])  # ear root on the yoke plate, conservative
        for p in _rim():
            for d in dirs:
                loads, _ = _body_loads(tilt, _world(*p, tilt), MT.push * np.array(d))
                for zc, dx, dy in sections:
                    stem = max(stem, _rect_stress(*_section(loads, np.array([0, 0, zc])), dx, dy))
                mw, fw = _section(loads, root)
                mb = np.array([mw[0], *m._rot(mw[1], mw[2], -tilt)])  # body axes
                fb = np.array([fw[0], *m._rot(fw[1], fw[2], -tilt)])
                s = abs(mb[0]) * er / (2 * et * (2 * er) ** 3 / 12)  # about x: two ears side by side
                s += abs(mb[1]) * (ex + et / 2) / (2 * (2 * er * et**3 / 12 + 2 * er * et * ex**2))  # about y: ear pair
                s += abs(fb[2]) / (2 * et * 2 * er)
                t = 1.5 * abs(mb[2]) / (2 * ex) / (et * 2 * er)  # torsion as opposed shear in the two ears
                ear = max(ear, math.hypot(s, math.sqrt(3) * t))
    return stem, ear


def test_tongue_stem_and_yoke_ears_hold_a_push_at_the_rim(parts):
    # stem and yoke ears print upright, so they bend across the layers
    assert MT.tongue_w < m.bore()  # the stem stays clear of the slit, so the clamp still closes
    stem, ear = _peak_stresses(parts["mount_clamp"])
    assert stem <= MT.layer_limit, stem
    assert ear <= MT.layer_limit, ear


def test_adjustable_link_covers_the_tilt_range():
    lo, hi = MT.tilt_range
    d = m.rod_end_dims()
    nut, p = fasteners.nut_data(MT.link_rod_size)["m"], CFG.fasteners.coarse_pitch[MT.link_rod_size]
    assert m.link_min_length() <= m.link_length(hi)  # the rod ends and the outer nut fit at the steepest tilt
    # rod tip in the adjust end, from the inner face of its wall: past the inner nut at the flattest tilt, inside
    # the window at the steepest
    for tilt, low in ((lo, True), (hi, False)):
        gap = m.link_length(tilt) - d["adjust"]["reach"] - d["fixed"]["reach"]
        tip = m.rod_length() - (nut + p) - d["fixed"]["wall"] - gap - d["adjust"]["wall"]
        if low:
            assert tip >= nut + p - 1e-6, tilt
        else:
            assert tip <= d["adjust"]["length"] - 2 * FIT + 1e-6, tilt
    window_w = m.link_w() - 4 * MW
    assert window_w >= 2 * fasteners.nut_data(MT.link_rod_size)["s"] / math.sqrt(3) + 2 * FIT  # a nut turns in the window
    assert MT.link_wall >= 2 * MW and d["fixed"]["wall"] - nut >= 2 * MW  # noqa: PT018
    pocket = fasteners.nut_data(MT.link_rod_size)["s"] + 2 * CFG.fasteners.head_fit  # flat up and down in the link thickness
    assert (MT.link_t - pocket) / 2 >= MW


def test_fixed_links_are_in_the_range_and_their_pins_are_the_link_length_apart(parts):
    lo, hi = MT.tilt_range
    assert layout.tilt() in MT.fixed_tilts
    for tilt in MT.fixed_tilts:
        assert lo <= tilt <= hi
        link = parts[f"mount_link_{tilt:.0f}"]
        holes = [e for e in link.edges() if e.geom_type == GeomType.CIRCLE and e.radius == pytest.approx(m.link_pin_d() / 2)]
        ys = sorted({round(e.arc_center.Y, 3) for e in holes})
        assert ys[-1] - ys[0] == pytest.approx(m.link_length(tilt), abs=1e-3)


def test_link_pins_meet_the_fork_holes_at_every_tilt(parts):
    # from the solids: the link placed by its own frame must put its holes on the fork holes
    lo, hi = MT.tilt_range  # the adjustable link covers the range, not the margin
    yoke = m.yoke_in_body(parts["mount_yoke"])
    for tilt in (lo, layout.tilt(), hi):
        pins = Compound(list(_hardware(tilt, MT.link_pin_size).values()))
        assert _overlap(pins, yoke) < 1e-3 and _overlap(pins, m.clamp_in_body(parts["mount_clamp"], tilt)) < 1e-3, tilt  # noqa: PT018
        assert _overlap(pins, m.link_in_body(m.adjustable_link(tilt), tilt)) < 1e-3, tilt
        bare = Cylinder(fasteners.nominal_d(MT.link_pin_size) / 2 - 0.05, 4 * MT.ear_t)  # pin through the middle of the link
        py, pz = m.pivot_point()
        for y, z in (MT.link_a, m._rot(*MT.link_b, -tilt)):
            assert _overlap(Pos(0, py + y, pz + z) * Rot(Y=90) * bare, m.link_in_body(m.adjustable_link(tilt), tilt)) < 1e-3, tilt


def test_clamp_fits_a_square_and_a_round_tube():
    for shape in ("round", "square"):
        cfg = replace(CFG, mount=replace(MT, tube_shape=shape))
        part = m.clamp(cfg)
        assert part.is_valid and len(part.solids()) == 1, shape  # noqa: PT018
        assert part.bounding_box().size.Z <= CFG.printer.bed_z  # noqa: SIM300


def test_assembly_has_no_interference_at_the_default_tilt(parts, fixed):
    tilt = layout.tilt()
    mount = {
        "yoke": m.yoke_in_body(parts["mount_yoke"]),
        "clamp": m.clamp_in_body(parts["mount_clamp"], tilt),
        "link": m.link_in_body(m.adjustable_link(tilt), tilt),
        **_hardware(tilt, MT.link_pin_size),
        **_hardware(tilt, MT.pivot_size),
    }
    for (na, pa), (nb, pb) in itertools.chain(itertools.product(mount.items(), fixed.items()), itertools.combinations(mount.items(), 2)):
        volume = _overlap(pa, pb)
        assert volume < 1e-3, f"{na} overlaps {nb} by {volume:.4f} mm3"


def test_clamp_and_links_clear_the_yoke_and_body_over_the_tilt_range(parts, fixed):
    lo, hi = m.tilt_span()
    yoke = m.yoke_in_body(parts["mount_yoke"])
    cases = [(lo + (hi - lo) * i / 8, m.adjustable_link) for i in range(9)]
    cases += [(t, lambda t, cfg=CFG: parts[f"mount_link_{t:.0f}"]) for t in MT.fixed_tilts]
    for tilt, build in cases:
        clamp = m.clamp_in_body(parts["mount_clamp"], tilt)
        link = m.link_in_body(build(tilt), tilt)
        for name, other in (("yoke", yoke), *fixed.items()):
            assert _overlap(clamp, other) < 1e-3, f"clamp overlaps {name} at {tilt:.1f} deg"
            assert _overlap(link, other) < 1e-3, f"link overlaps {name} at {tilt:.1f} deg"
        assert _overlap(link, clamp) < 1e-3, f"link overlaps the clamp at {tilt:.1f} deg"
        assert _overlap(link, assembly_stand_tube(tilt)) < 1e-3, tilt


def _layer(mesh, z):
    section = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if section is None:
        return MultiPolygon()
    planar, _ = section.to_2D(to_2D=np.eye(4), check=False)
    return unary_union(planar.polygons_full)


def _unsupported(part, step=1.0, tol=0.05):
    """(z, span) of regions that a layer adds beyond 45 deg of the layer below and that are not a short bridge
    (supported along most of their outline and at most `print.bridge` across). Part in print orientation."""
    verts, tris = part.tessellate(0.02)
    mesh = trimesh.Trimesh(np.array([(v.X, v.Y, v.Z) for v in verts]), np.array(tris))
    out = []
    z = step
    while z < mesh.bounds[1][2]:
        below, here = _layer(mesh, z - step), _layer(mesh, z)
        new = here.difference(below.buffer(step * math.tan(math.radians(45)) + tol))
        for piece in getattr(new, "geoms", [new]):
            if piece.area < 0.5:
                continue
            x0, y0, x1, y1 = piece.bounds
            span = max(x1 - x0, y1 - y0)
            held = piece.boundary.intersection(below.buffer(step + tol + 1.0)).length / piece.boundary.length
            if span > CFG.print.bridge or held < 0.8:
                out.append((round(z, 1), round(span, 1), round(held, 2)))
        z += step
    return out


def test_parts_print_without_supports(parts):
    for name, part in parts.items():
        assert _unsupported(part) == [], name


def test_support_check_catches_a_fork_ear_without_its_lower_flank():
    clamp = m.clamp()
    zb = m.clamp_pivot_z() + MT.link_b[1]
    face, tip = m.clamp_layout()["y_min"], MT.link_b[0] - m.fork_r()
    under = Pos(0, (face + tip) / 2, 0) * Box(m.link_gap() + 2 * MT.ear_t + 2, face - tip, zb, align=sc.BOTTOM)
    assert _unsupported(clamp - under) != []
