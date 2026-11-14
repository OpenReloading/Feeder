"""Side view of the introduction page: drawn from the assembly at its tilt, each number on a leader to its part."""

import re
from itertools import combinations

import pytest
from shapely.geometry import LineString, Point

from feeder import side_view


@pytest.fixture(scope="module")
def view():
    return side_view.view()


def test_view_is_the_assembly_at_45_deg_with_the_exit_on_the_high_side(view):
    assert view.tilt == 45
    # x to the right, y down: the cut plate rises to the right over 175 mm
    assert view.cuts["plate"].bounds == pytest.approx((-102.1, -102.1, 72.8, 72.8), abs=0.5)
    left, top, _, bottom = view.cuts["drop"].bounds
    assert left > 60 and top < -60 and bottom > 30  # noqa: PT018  from the high side of the bowl down past the shaft
    # under the plate: farther along (1, 1), the way down out of the bowl
    assert sum(view.outlines["motor"].centroid.coords[0]) > sum(view.cuts["plate"].centroid.coords[0]) + 30
    left, _, right, bottom = view.outlines["tube"].bounds
    assert right - left == pytest.approx(25.0, abs=0.5)  # the 25 mm stand tube is upright
    assert bottom > view.box[1] + view.box[3]  # and runs out of the drawing
    assert view.outlines["extender"].intersection(view.outlines["body"]).area < 1  # the body hides the rest of it


def test_each_number_has_a_leader_to_its_part_and_none_cross(view):
    shapes = {(group, what): (view.outlines if what == "outline" else view.cuts)[group] for group, what, _ in side_view.LAYERS}
    front = {group: shapes[group, what] for group, what, _ in side_view.LAYERS}
    leaders = [LineString([end, number]) for _, end, number in view.callouts]
    assert not any(a.intersects(b) for a, b in combinations(leaders, 2))
    solid = [shapes[group, what] for group, what, cls in side_view.LAYERS if cls != "behind"]  # numbers may stand in the bowl
    left, top, width, height = view.box
    for (callout, end, number), leader in zip(view.callouts, leaders, strict=True):
        assert front[callout.group].distance(Point(end)) < 0.01, callout.name
        # a number is 15 mm high and two digits wide
        assert all(shape.distance(Point(number)) > 10 for shape in solid), callout.name
        assert all(other.distance(Point(number)) > 10 for other in leaders if other is not leader), callout.name
        assert left + 10 < number[0] < left + width - 10 and top + 10 < number[1] < top + height - 10, callout.name  # noqa: PT018


def test_figure_gives_every_numbered_part_as_text(view, monkeypatch):
    monkeypatch.setattr(side_view, "view", lambda cfg: view)
    html = side_view.side_view_html()
    legend = re.findall(r"<li>(\d\d) ([^<]+)</li>", html)
    assert re.findall(r"<text [^>]*>(\d\d)</text>", html) == [number for number, _ in legend] == [f"{i:02d}" for i in range(1, 10)]
    alt = re.search(r'role="img" aria-label="([^"]+)"', html)
    assert alt and all(name.lower() in alt.group(1) for _, name in legend)  # noqa: PT018
