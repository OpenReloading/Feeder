"""Electronics box: below the tilt clamp at every tilt, beside the tube with its front toward the user and clear of the
drop path, screws reach their inserts, panel parts clear of each other and of the relay."""

import pytest
from build123d import Box, Cylinder, Plane, Pos, Rot, Vector

from feeder import assembly, guide, wiring
from feeder.config import CFG
from feeder.lib import fasteners
from feeder.parts import body as b
from feeder.parts import electronics as el
from feeder.parts import mount as m
from feeder.parts.slip_clutch import BOTTOM

E, MW = CFG.electronics, CFG.print.min_wall
OWN = ("stand_tube", "mount_clamp", "electronics_box", "electronics_lid", "timer_relay", "pwm_controller",
       "pwm_knob", "toggle_switch", "dc_jack", "gx12_2_pin_socket", "gx12_3_pin_socket")  # vertical in the world with the box


def test_tilting_parts_and_their_fasteners_stay_above_the_box_at_every_tilt():
    lo, hi = m.tilt_span()
    for tilt in (lo, (lo + hi) / 2, hi):
        inv = m.clamp_frame(tilt).inverse()
        shapes = [(p.name, p.shape) for p in assembly.placed(tilt=tilt) if p.name not in OWN]
        shapes += [(f.name, loc * f.shape) for f in assembly.fasteners_in_body(tilt=tilt) if f.host not in OWN for loc in f.at]
        for name, shape in shapes:
            assert (inv * shape).bounding_box().min.Z > -E.box_gap, (tilt, name)  # noqa: SIM300


@pytest.mark.parametrize("left", [False, True], ids=["right", "left"])
def test_box_stands_beside_the_tube_with_its_front_toward_the_user_and_clear_of_the_drop_path(left):
    ix, iy, iz = E.box_inner
    assert iy < ix < iz
    o, d = b.outlet()
    path = Plane(origin=o, z_dir=d) * Cylinder(b.bore_d() / 2 + CFG.exit.wall, CFG.exit.spigot_len + 150.0)  # the drop tube and 150 mm of hose
    lo, hi = m.tilt_span()
    for tilt in (lo, (lo + hi) / 2, hi):
        into_clamp = m.clamp_frame(tilt).inverse() * el.box_frame(tilt, left=left)
        shape = el.box_left() if left else el.box()
        assert (el.box_frame(tilt, left=left) * shape).distance_to(path) > 20, tilt
        assert (into_clamp * Pos(0, el.outline()["y0"], 0)).position.Y < 0, tilt  # the front rim lies on the low side (-y)
        assert ((into_clamp * Pos(0, 0, 0)).position.X < 0) == left, tilt  # right of the tube as the user sees it is +x


@pytest.mark.parametrize("size, length, grip, depth", [  # noqa: PT006
    (E.lid_screw_size, el.lid_screw_length(), E.lid_t, CFG.fasteners.inserts[E.lid_screw_size].hole_depth),
    (E.lid_screw_size, el.relay_screw_length(), E.relay_pcb_t, E.relay_hole_depth),
])
def test_screws_reach_into_their_inserts_without_bottoming_out(size, length, grip, depth):
    thread = length - grip
    assert CFG.fasteners.min_engagement * fasteners.nominal_d(size) <= thread <= depth - 0.5


def test_relay_insert_holes_stay_closed_at_the_back():
    assert E.relay_hole_depth <= E.standoff_h + E.box_wall - MW


def test_panel_holes_leave_room_for_their_nuts():
    room = 3.0  # mm round each hole for the panel nut, unverified
    ix, iy, iz = E.box_inner  # noqa: RUF059
    p = el.post_w()
    holes = el.panel_holes()
    o = el.outline()
    for i, (name, d, loc) in enumerate(holes):
        c = loc.position
        if i < len(E.front_holes):  # lid column: clear of the posts at the top and bottom
            assert E.box_wall + p + d / 2 + room <= c.Z <= E.box_wall + iz - p - d / 2 - room, name
        else:  # side face: clear of the lid, the back wall and the bottom corner post, socket body beside the relay
            assert o["y0"] + d / 2 + room <= c.Y <= o["y1"] - E.box_wall - d / 2 - room, name
            assert c.Z - d / 2 - room >= E.box_wall + p, name
            assert c.Y + d / 2 + room <= el.relay_front(), name  # in the front band: the socket body behind the panel reaches past the relay in x
        for name2, d2, loc2 in holes[i + 1:]:
            assert (c - loc2.position).length >= (d + d2) / 2 + 2 * room, (name, name2)


def test_relay_fits_between_the_posts_and_below_the_pwm_board():
    p, sd = el.post_w(), el.standoff_d()
    ix, _, iz = E.box_inner  # noqa: RUF059
    xs, zs = [x for x, _ in el.relay_screws()], [z for _, z in el.relay_screws()]
    assert max(xs) + sd / 2 <= ix / 2 - p
    knob_z = el.panel_holes()[0][2].position.Z
    assert max(zs) + sd / 2 < knob_z - 25  # the PWM board hangs about 25 mm round its knob (unverified)


def test_every_panel_hole_has_a_part_whose_barrel_fits_and_carries_its_nut():
    holes = dict(E.front_holes + E.side_holes)
    assert dict(E.panel_parts).keys() == holes.keys()
    for name, pp, _, t in el.panel_fits():
        assert holes[name] - pp.thread_d >= 0.2 - 1e-9, name  # print clearance of the other holes
        assert t + pp.nut_t <= pp.thread_l, name  # the nut sits on the thread
        assert pp.body[2] > 0 and pp.nut_af > pp.thread_d, name  # noqa: PT018


def test_panel_nuts_sit_on_the_inner_face_of_their_panel():
    box = el.box_frame(CFG.case_plate.tilt)
    nuts = {f.name: f for f in assembly.fasteners_in_body() if f.name.startswith("Panel nut")}
    for name, pp, mouth, t in el.panel_fits():
        f = nuts[f"Panel nut, {pp.label}"]
        assert f.host == ("electronics_lid" if name in dict(E.front_holes) else "electronics_box")
        want = (box * mouth * Pos(0, 0, t)).position
        assert (f.at[0].position - want).length < 1e-6, name


def test_relay_screws_pass_the_board_holes():
    relay, o = el.relay_board(), el.outline()
    for x, z in el.relay_screws():
        probe = Pos(x, o["y1"] - E.box_wall - E.standoff_h - E.relay_pcb_t / 2, z) * Cylinder(fasteners.nominal_d(E.lid_screw_size) / 2, E.relay_pcb_t, rotation=(90, 0, 0))
        common = probe & relay
        assert (common.volume if common.solids() else 0.0) < 1e-3


def _common(a, b):
    c = a & b
    return c.volume if c.solids() else 0.0


def test_bought_modules_and_panel_parts_do_not_overlap_in_the_box():
    shapes = {"timer_relay": el.relay_board(), "pwm_controller": el.pwm_board()}
    shapes |= {pp.label: loc * el.panel_envelope(pp) for _, pp, loc, _ in el.panel_fits()}
    names = list(shapes)
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            assert _common(shapes[first], shapes[second]) < 1e-3, (first, second)


def _cavity():
    o = el.outline()
    ix, _, iz = E.box_inner
    return Pos(0, (o["y0"] + o["y1"] - E.box_wall) / 2, E.box_wall + iz / 2) * Box(ix, o["y1"] - E.box_wall - o["y0"], iz)


def _modules():
    shapes = {"timer_relay": el.relay_board(), "pwm_controller": el.pwm_board()}
    return shapes | {pp.label: loc * el.panel_envelope(pp) for _, pp, loc, _ in el.panel_fits()}


def test_side_sockets_have_their_depth_behind_the_wall_and_clear_the_box_and_the_modules():
    box, modules = el.box(), _modules()
    for name, pp, mouth, t in el.panel_fits()[len(E.front_holes):]:
        assert pp.thread_l + pp.body[2] - t >= E.socket_depth - 1e-9, name  # body and solder cups reach this far behind the inner face
        env = mouth * el.panel_envelope(pp)
        assert _common(env & _cavity(), box) < 1e-3, name  # posts, pads, cradles
        for other, shape in modules.items():
            if other == pp.label:
                continue
            assert _common(env, shape) < 1e-3, (name, other)


def test_service_loop_runs_stay_free():
    box, modules = el.box(), _modules()
    loops = el.service_loops()
    assert len(loops) == len(E.side_holes)
    for i, loop in enumerate(loops):
        assert max(loop.bounding_box().size.X, loop.bounding_box().size.Y, loop.bounding_box().size.Z) >= E.service_loop - 1e-6
        assert _common(loop, box) < 1e-3, i
        assert _common(loop, _cavity()) > 0.99 * loop.volume, i  # inside the box
        assert all(_common(loop, shape) < 1e-3 for shape in modules.values()), i
        assert all(_common(loop, other) < 1e-3 for other in loops[i + 1:]), i


def _tunnels():
    """(centre, length along z, half sizes across x and y) of every tie tunnel, right-hand box."""
    back = el.outline()["y1"] - E.box_wall
    tw, tt = E.tie_slot
    zf, zs = E.cradle_z
    lx, _, wz = el.fuse_cradle_size()
    under = back - E.tie_gap - tt / 2
    out = [(Vector(x, y, z), E.pad_len, (tt / 2, tw / 2)) for x, y, z in el.tie_pads()]  # on the wall: tie thickness across x, width along y
    out += [(Vector(sx * (lx / 2 - E.tie_gap - tw), under, zf), wz, (tw / 2, tt / 2)) for sx in (-1, 1)]  # under the cradles: width along x
    out += [(Vector(x, under, zs), el.splice_cradle_size()[2], (tw / 2, tt / 2)) for x in el.splice_at()]
    return out


@pytest.mark.parametrize("left", [False, True], ids=["right", "left"])
def test_every_tie_tunnel_is_open_through_and_has_material_round_it(left):
    box, s, g = (el.box_left(), -1, E.tie_gap / 2) if left else (el.box(), 1, E.tie_gap / 2)
    for centre, length, (hx, hy) in _tunnels():
        c = Vector(s * centre.X, centre.Y, centre.Z)
        for dz in (0, length / 2 - 0.3, -length / 2 + 0.3, length / 2 + 0.5, -length / 2 - 0.5):
            assert not box.is_inside(c + Vector(0, 0, dz)), (tuple(centre), dz)  # a tie goes through and comes out both ends
        for dx, dy in ((hx + g, 0), (-(hx + g), 0), (0, hy + g), (0, -(hy + g))):
            assert box.is_inside(c + Vector(s * dx, dy, 0)), (tuple(centre), dx, dy)  # tie_gap of material on every side


def test_tie_tunnel_matches_the_config_size():
    assert E.tie_slot == (3.5, 1.5)  # issue: about 3.5 x 1.5 mm, for a 2.5 mm tie


def test_every_socket_has_a_tie_pad_behind_it_and_clear_of_its_body():
    pads = el.tie_pads()
    assert len(pads) == len(E.side_holes)
    for (_, y, z), (_, _, mouth, _) in zip(pads, el.panel_fits()[len(E.front_holes):], strict=True):
        assert y > mouth.position.Y + 6.5  # behind (+y) the 13 mm body
        assert abs(z - mouth.position.Z) < 1e-6  # at its height


@pytest.mark.parametrize("left", [False, True], ids=["right", "left"])
def test_outside_edges_are_chamfered(left):
    box, s, o = (el.box_left(), -1, el.outline()) if left else (el.box(), 1, el.outline())
    r = E.edge_r
    assert 1 <= r <= 2
    probes = [  # (outside the chamfer, inside the solid), at the back face rim and along an edge parallel to y
        ((0, o["y1"] - 0.3, 0.3), (0, o["y1"] - r - 0.2, r + 0.2)),
        ((s * (o["x"] - 0.3), -20.0, 0.3), (s * (o["x"] - r - 0.2), -20.0, r + 0.2)),
    ]
    for gone, kept in probes:
        assert not box.is_inside(Vector(*gone)), gone
        assert box.is_inside(Vector(*kept)), kept


def test_lid_outside_edges_are_chamfered_and_the_lid_is_shared():
    o, r, lid = el.outline(), E.edge_r, el.lid()
    y = o["y0"] - E.lid_t
    assert not lid.is_inside(Vector(0, y + 0.3, 0.3))
    assert lid.is_inside(Vector(0, y + r + 0.2, r + 0.2))
    assert not lid.is_inside(Vector(o["x"] - 0.3, y + 1.5, 0.3))
    assert lid.is_inside(Vector(o["x"] - r - 0.2, y + 1.5, r + 0.2))
    assert "electronics_lid_left" not in el.PARTS  # one lid fits both boxes


def test_lid_text_comes_from_the_wiring_data():
    lines = el.lid_lines()
    board = guide.wiring_board()
    plug = [c for step in board["steps"] if step["id"] == "F" for c in step["connections"]]  # the plug step of the guide
    assert len(plug) == 5
    for c in plug:
        (ref, pin), signal = (c["b"].split(":"), c["a"].split(":")[1]) if c["b"].startswith("X") else (c["a"].split(":"), c["b"].split(":")[1])
        assert f"{pin.removeprefix('P')} {signal}" in lines[ref], c
    assert set(lines) == {r for r, _ in E.lid_titles} == set(E.front_refs) | set(E.side_refs)
    assert "J1" in E.front_refs
    assert wiring.centre_polarity("J1") in "".join(lines["J1"])


def test_lid_text_names_no_side():
    text = " ".join(" ".join(v) for v in el.lid_lines().values()).lower()
    assert "left" not in text  # the box is mirrored for the other side, the lid is not
    assert "right" not in text


def test_lid_text_is_engraved_in_the_outer_face_and_clear_of_holes_screws_and_edges():
    o, h = el.outline(), el.height()
    lid, texts = el.lid(), el.lid_text()
    assert len(texts) == len(el.lid_labels()) == sum(len(v) for v in el.lid_lines().values())
    assert 0 < E.label_depth <= E.lid_t - MW  # a wall of at least min_wall stays behind the engraving
    plate = Pos(0, o["y0"] - E.lid_t / 2, h / 2) * Box(2 * o["x"], E.lid_t, h)
    holes = [loc * Pos(0, 0, -1) * Cylinder(d / 2 + 1, E.lid_t + 2, align=BOTTOM) for _, d, loc in el.panel_holes()[: len(E.front_holes)]]
    head = fasteners.socket_screw(E.lid_screw_size, el.lid_screw_length()).screw_data["dk"]
    holes += [Pos(x, o["y0"] - E.lid_t, z) * Rot(X=90) * Cylinder(head / 2 + 1, E.lid_t + 2, align=BOTTOM) for x, z in el.lid_screws()]
    for text in texts:
        assert text.volume > 0.5 * E.label_depth  # the font was found: a missing font gives no solid
        assert _common(text, plate) > 0.5 * text.volume * E.label_depth / (E.label_depth + 1)  # the depth that is in the lid
        assert _common(text, lid) < 1e-3  # and it is cut out of it
        bb = text.bounding_box()
        x0, x1, z0, z1 = bb.min.X, bb.max.X, bb.min.Z, bb.max.Z
        edge = E.edge_r + 1  # clear of the chamfers
        assert x0 > edge - o["x"]
        assert x1 < o["x"] - edge
        assert z0 > edge
        assert z1 < h - edge
        assert all(_common(text, hole) < 1e-3 for hole in holes)
    assert all(_common(a, b) < 1e-3 for i, a in enumerate(texts) for b in texts[i + 1:])  # lines do not touch


def test_lid_text_is_big_enough_to_print_and_read():
    cap = el.lid_text()[0].bounding_box().size.Z
    assert cap >= 4.0  # mm cap height, with 0.6 mm deep strokes on a 0.4 mm nozzle
    assert E.label_pitch >= cap * 1.5


def test_text_in_the_lid_columns_does_not_cross_the_middle_line():
    for text in el.lid_text():
        bb = text.bounding_box()
        x0, x1, gap = bb.min.X, bb.max.X, E.label_gap - 1e-6
        assert x0 > gap or x1 < -gap


def test_fuse_holder_lies_in_its_pocket_with_its_ties_and_clear_of_the_modules():
    dh, lh = E.fuse_holder
    back = el.outline()["y1"] - E.box_wall
    lx, hh, wz = el.fuse_cradle_size()
    zf, _ = E.cradle_z
    holder = Pos(0, back - hh, zf) * Rot(Y=90) * Cylinder(dh / 2, lh)  # axis on the top of the cradle: half in the groove
    box = el.box()
    assert lh <= lx
    assert _common(holder, box) < 1e-3  # fits the groove
    assert _common(holder, Pos(0, back - hh / 2, zf) * Box(lx, hh, wz)) > 0.45 * holder.volume  # half of it lies in the groove: the ties hold it there
    assert all(_common(holder, shape) < 1e-3 for shape in _modules().values())


def test_splice_connectors_fit_their_pockets_with_clear_space_above():
    sl, sw, sh = E.splice
    back = el.outline()["y1"] - E.box_wall
    _, hs, _ = el.splice_cradle_size()
    zs = E.cradle_z[1]
    box, modules = el.box(), _modules()
    keep = []
    for x in el.splice_at():
        conn = Pos(x, back - hs + sh / 2, zs) * Box(sl, sh, sw)
        above = Pos(x, back - hs - E.splice_clear / 2, zs) * Box(sl, E.splice_clear, sw)  # the open levers
        assert _common(conn, box) < 1e-3
        assert _common(above, box) < 1e-3
        assert _common(above, _cavity()) > 0.99 * above.volume
        assert all(_common(above, shape) < 1e-3 for shape in modules.values())
        keep.append(conn + above)
    assert _common(*keep) < 1e-3  # side by side
    assert abs(sum(el.splice_at())) < 1e-9  # symmetric: the same on both boxes
    assert zs - el.splice_cradle_size()[2] / 2 > E.cradle_z[0] + el.fuse_cradle_size()[2] / 2  # above the fuse holder cradle


@pytest.mark.parametrize("left", [False, True], ids=["right", "left"])
def test_both_sides_carry_every_finishing_feature_mirrored(left):
    box, s = (el.box_left(), -1) if left else (el.box(), 1)
    o = el.outline()
    for name, _, mouth in el.panel_holes()[len(E.front_holes):]:
        c = mouth.position
        assert not box.is_inside(Vector(s * (o["x"] - E.box_wall / 2), c.Y, c.Z)), name  # socket hole in the wall on its own side
        assert box.is_inside(Vector(-s * (o["x"] - E.box_wall / 2), c.Y, c.Z)), name
    back = o["y1"] - E.box_wall
    zf, zs = E.cradle_z
    assert box.is_inside(Vector(0, back - 1, zf))  # fuse cradle base
    assert all(box.is_inside(Vector(x * s, back - 1, zs)) for x in el.splice_at())
    for _, y, z in el.tie_pads():
        assert box.is_inside(Vector(s * (o["x"] - E.box_wall - 0.5), y, z))  # pad root on the wall


def test_the_two_socket_blocks_of_text_read_as_two_lists():
    left = [(z, text) for text, x, z, _ in el.lid_labels() if x < 0]
    motor = next(z for z, text in left if text == "MOTOR")
    last_sensor = min(z for z, text in left if text in ("1 BN", "2 BU", "3 BK", "SENSOR"))
    assert last_sensor - motor >= E.label_pitch + E.label_block_gap - 1e-6  # more than a line step between the lists
