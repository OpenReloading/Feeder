"""Every plate set on the one body: plate, exit insert and drop tube of each group plate and of the
configured plate. The other test modules check the configured plate in detail."""

import math
from dataclasses import replace

import pytest
import trimesh
from build123d import Box, Pos, export_stl
from shapely.geometry import Point
from shapely.geometry import Polygon as ShapelyPolygon

import build
from feeder import printing
from feeder.config import CFG
from feeder.parts import body as b
from feeder.parts import case_plate as cp
from feeder.parts import drop_tube as dt
from feeder.parts import layout

SETS = layout.plate_sets()
IDS = [s.case_plate.caliber for s in SETS]
MW, FIT, EPS = CFG.print.min_wall, CFG.print.fit, 1e-3


def _volume(shape) -> float:
    return shape.volume if shape.solids() else 0.0


@pytest.fixture(scope="module")
def core():
    return b.core()


@pytest.fixture(scope="module", params=SETS, ids=IDS)
def plate_set(request):
    s = request.param
    return s, {"plate": cp.plate(s), "insert": b.exit_insert(s), "tube": dt.placement(s) * dt.drop_tube(s)}


def test_parts_are_single_valid_solids(plate_set):
    _, parts = plate_set
    for name, part in parts.items():
        assert part.is_valid and len(part.solids()) == 1, name  # noqa: PT018


def test_group_plate_height_and_pockets_suit_every_case(plate_set):
    s, _ = plate_set
    h, d, r, n = layout.plate_h(s), layout.pocket_d(s), layout.pocket_circle_r(s), layout.pocket_count(s)
    cals = layout.calibers(s)
    for c in cals:
        assert 0.33 <= h / c.case_length <= 0.40, c  # near each case's estimated centre of mass
        assert h < c.case_length / 2  # a mouth-down case stands mostly above the plate
        assert c.rim_d < d < 2 * c.rim_d  # one case per pocket
    assert d - min(c.rim_d for c in cals) <= s.case_plate.pocket_clearance + 2.3  # the smallest rim's extra play
    assert 2 * r * math.sin(math.pi / n) - d - 2 * s.case_plate.top_chamfer >= MW
    assert 2 * (r - s.case_plate.channel_len) * math.sin(math.pi / n) - (d - 1) >= MW
    z = layout.levels(s)
    assert z.plate_bottom - z.deck_top + s.case_plate.flatness / 2 < layout.caliber(s).rim_t_min  # no rim under the plate


def test_set_declares_a_supported_item_and_orientation(plate_set):
    s, _ = plate_set
    assert (s.case_plate.item, s.case_plate.orient) in s.case_plate.tilts
    assert layout.tilt(s) == s.case_plate.tilts[s.case_plate.item, s.case_plate.orient]


@pytest.mark.parametrize("s", SETS, ids=IDS)
def test_unsupported_orientation_names_the_supported_ones(s):
    bad = replace(s, case_plate=replace(s.case_plate, orient="mouth_down"))
    msg = "case/base_down"
    for build_part in (cp.plate, b.exit_insert, layout.tilt):
        with pytest.raises(ValueError, match=msg):
            build_part(bad)


def test_exit_takes_the_set_and_fits_the_body_shaft(plate_set, core):
    s, parts = plate_set
    length, r0, r1 = b.opening(s)
    r, d = layout.pocket_circle_r(s), layout.pocket_d(s)
    assert r0 < r - d / 2 and r1 > r + d / 2  # noqa: PT018
    assert length > layout.caliber(s).case_length + d
    assert layout.bowl_r(s) - FIT - r1 >= MW  # the opening's outer edge is an arc under the band
    assert b.bore_d(s) >= layout.caliber(s).rim_d + 0.4
    ins = parts["insert"]
    assert _volume(core & ins) < EPS
    z = layout.levels(s)
    shaft_plan = ShapelyPolygon([(v.X, v.Y) for v in b._exit_outline(s, 0.0).vertices()]).buffer(EPS)
    verts, _ = ins.tessellate(0.05)
    assert all(shaft_plan.contains(Point(v.X, v.Y)) for v in verts if v.Z < z.deck_top - s.exit.seat_t - EPS)  # it drops in from above  # noqa: SIM300


def test_drop_tube_passes_every_case(plate_set, core):
    s, parts = plate_set
    assert _volume(parts["tube"] & parts["insert"]) < EPS
    assert _volume(parts["tube"] & core) < EPS
    hose = s.drop_tube.hose_id
    for c in layout.calibers(s):
        assert hose > c.rim_d + 0.4  # the case runs down the hose
        assert math.hypot(c.rim_d, c.case_length) > hose  # and cannot turn over in it
    k = dt.dims(s)
    assert k.tip - k.sensor_z >= layout.caliber(s).case_length + s.drop_tube.sensor_margin  # sensor clears the last case
    slab = Pos(0, 0, 5) * Box(80, 80, 0.2)
    assert (parts["tube"] & dt.placement(s) * slab).volume > 0


@pytest.mark.parametrize("s", SETS, ids=IDS)
def test_set_parts_fit_the_printer_and_are_watertight(s, tmp_path):
    for name, builder in build.plate_set_parts(s):
        part = builder(s)
        assert printing.fits(printing.on_bed(name, part, s), s), name
        export_stl(part, str(tmp_path / "part.stl"))
        assert trimesh.load(tmp_path / "part.stl").is_watertight, name
