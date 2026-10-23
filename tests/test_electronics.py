"""Electronics box: below the tilt clamp at every tilt, lid off from below, panel holes clear of each other."""

import math

from feeder import assembly
from feeder.config import CFG
from feeder.lib import fasteners
from feeder.parts import electronics as el
from feeder.parts import mount as m

E, MW = CFG.electronics, CFG.print.min_wall
OWN = ("stand_tube", "mount_clamp", "electronics_box", "electronics_lid")  # vertical in the world with the box


def test_tilting_parts_and_their_fasteners_stay_above_the_box_at_every_tilt():
    lo, hi = m.tilt_span()
    for tilt in (lo, (lo + hi) / 2, hi):
        inv = m.clamp_frame(tilt).inverse()
        shapes = [(p.name, p.shape) for p in assembly.placed(tilt=tilt) if p.name not in OWN]
        shapes += [(f.name, loc * f.shape) for f in assembly.fasteners_in_body(tilt=tilt) if f.host not in OWN for loc in f.at]
        for name, shape in shapes:
            assert (inv * shape).bounding_box().min.Z > -E.box_gap, (tilt, name)


def test_lid_and_its_screws_come_off_downward_beside_the_tube():
    r = CFG.mount.tube_d / 2
    assert el.outline()["y1"] < -r
    head = fasteners.socket_screw(E.lid_screw_size, 10).screw_data["dk"] / 2
    for x, y in el.lid_screws():
        assert math.hypot(x, y) - r >= head + MW  # a driver from below passes the tube


def test_lid_screws_reach_into_the_inserts():
    ins = CFG.fasteners.inserts[E.lid_screw_size]
    thread = el.lid_screw_length() - E.lid_t
    assert CFG.fasteners.min_engagement * fasteners.nominal_d(E.lid_screw_size) <= thread <= ins.hole_depth - 0.5


def test_panel_holes_leave_room_for_their_nuts():
    room = 3.0  # mm round each hole for the panel nut, unverified
    ix, iy, iz = E.box_inner
    o, p = el.outline(), el.post_w()
    yc = (o["y0"] + o["y1"]) / 2
    holes = el.panel_holes()
    for i, (name, d, loc) in enumerate(holes):
        c = loc.position
        across, half = (abs(c.X), ix / 2) if i < len(E.front_holes) else (abs(c.Y - yc), iy / 2)
        assert across + d / 2 + room <= half - p, name  # clear of the corner posts
        assert d / 2 + room <= iz / 2, name
        for name2, d2, loc2 in holes[i + 1:]:
            assert (c - loc2.position).length >= (d + d2) / 2 + 2 * room, (name, name2)
