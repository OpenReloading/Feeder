"""Electronics box: below the tilt clamp at every tilt, upright on the exit side, screws reach their inserts,
panel parts clear of each other and of the relay."""

import pytest
from build123d import Cylinder, Pos

from feeder import assembly
from feeder.config import CFG
from feeder.lib import fasteners
from feeder.parts import electronics as el
from feeder.parts import mount as m

E, MW = CFG.electronics, CFG.print.min_wall
OWN = ("stand_tube", "mount_clamp", "electronics_box", "electronics_collar", "electronics_lid", "timer_relay", "pwm_controller",
       "pwm_knob", "toggle_switch", "dc_jack", "gx12_2_pin_socket", "gx12_3_pin_socket")  # vertical in the world with the box


def test_tilting_parts_and_their_fasteners_stay_above_the_box_at_every_tilt():
    lo, hi = m.tilt_span()
    for tilt in (lo, (lo + hi) / 2, hi):
        inv = m.clamp_frame(tilt).inverse()
        shapes = [(p.name, p.shape) for p in assembly.placed(tilt=tilt) if p.name not in OWN]
        shapes += [(f.name, loc * f.shape) for f in assembly.fasteners_in_body(tilt=tilt) if f.host not in OWN for loc in f.at]
        for name, shape in shapes:
            assert (inv * shape).bounding_box().min.Z > -E.box_gap, (tilt, name)


def test_box_stands_upright_on_the_exit_side_and_sticks_out_less_than_it_is_tall():
    ix, iy, iz = E.box_inner
    assert iy < ix < iz
    tilt = CFG.case_plate.tilt
    centre = (m.clamp_frame(tilt).inverse() * el.box_frame(tilt) * Pos(0, (el.outline()["y0"] + el.outline()["y1"]) / 2, 0)).position
    assert centre.Y > CFG.mount.tube_d / 2  # in the clamp frame +y is the exit side


@pytest.mark.parametrize("size, length, grip, depth", [
    (E.lid_screw_size, el.lid_screw_length(), E.lid_t, CFG.fasteners.inserts[E.lid_screw_size].hole_depth),
    (E.collar_screw_size, el.collar_screw_length(), E.box_wall, CFG.fasteners.inserts[E.collar_screw_size].hole_depth),
    (E.lid_screw_size, el.relay_screw_length(), E.relay_pcb_t, E.relay_hole_depth),
])
def test_screws_reach_into_their_inserts_without_bottoming_out(size, length, grip, depth):
    thread = length - grip
    assert CFG.fasteners.min_engagement * fasteners.nominal_d(size) <= thread <= depth - 0.5


def test_relay_insert_holes_stay_closed_at_the_back():
    assert E.relay_hole_depth <= E.standoff_h + E.box_wall - MW


def test_panel_holes_leave_room_for_their_nuts():
    room = 3.0  # mm round each hole for the panel nut, unverified
    ix, iy, iz = E.box_inner
    p, sd = el.post_w(), el.standoff_d()
    holes = el.panel_holes()
    o = el.outline()
    for i, (name, d, loc) in enumerate(holes):
        c = loc.position
        if i < len(E.front_holes):  # lid column: clear of the posts at the top and bottom
            assert E.box_wall + p + d / 2 + room <= c.Z <= E.box_wall + iz - p - d / 2 - room, name
        else:  # side face: clear of the lid, the back wall and the bottom corner post, socket body beside the relay
            assert o["y0"] + d / 2 + room <= c.Y <= o["y1"] - E.box_wall - d / 2 - room, name
            assert c.Z - d / 2 - room >= E.box_wall + p, name
            x_relay = max(abs(x) for x, _ in el.relay_screws()) + sd / 2
            assert ix / 2 - x_relay >= 12, name  # GX12 socket body behind the panel (unverified)
        for name2, d2, loc2 in holes[i + 1:]:
            assert (c - loc2.position).length >= (d + d2) / 2 + 2 * room, (name, name2)


def test_relay_fits_between_the_posts_and_below_the_pwm_board():
    p, sd = el.post_w(), el.standoff_d()
    ix, _, iz = E.box_inner
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
        assert pp.body[2] > 0 and pp.nut_af > pp.thread_d, name


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
