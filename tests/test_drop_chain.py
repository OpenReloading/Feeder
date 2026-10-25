"""Parts that chain on the drop tube's male end: the bore never narrows below the drop tube bore, every part hangs on
the one before it the way the drop tube hangs on the exit spigot, and the first tube's sensor window stays."""

import itertools
from dataclasses import replace

import pytest
from build123d import Cylinder, Location, Pos
from test_mount import _overlap, _unsupported

from feeder import assembly, printing
from feeder.config import CFG
from feeder.parts import body as b
from feeder.parts import drop_chain as dc
from feeder.parts import drop_tube as dt
from feeder.parts import electronics as el
from feeder.parts import mount as m
from feeder.parts import slip_clutch as sc

K, C, MW, EPS = dt.dims(), CFG.drop_chain, CFG.print.min_wall, 1e-3
FULL = replace(CFG, drop_chain=replace(C, parts=("spacer", "angled")))
NAMES = ("drop_spacer", "drop_angled", "drop_hose_adapter")


@pytest.fixture(scope="module")
def parts():
    return {n: build() for n, build in dc.PARTS.items()}


def _cyl(r: float, z0: float, z1: float):
    return Pos(0, 0, z0) * Cylinder(r, z1 - z0, align=sc.BOTTOM)


def _volume(shape) -> float:
    return shape.volume if shape.solids() else 0.0


def test_parts_are_single_valid_solids(parts):
    assert set(parts) == set(NAMES)
    for name, part in parts.items():
        assert part.is_valid, name
        assert len(part.solids()) == 1, name


def _axes(name: str) -> list[tuple[Location, float, float]]:
    """(frame, z0, z1) of each straight bore section of a part, above its socket shoulder."""
    z0 = K.depth + K.r_socket - K.r_bore + 0.5
    if name == "drop_spacer":
        return [(Pos(0, 0, 0), z0, K.socket_top + C.spacer_len + CFG.exit.spigot_len - 0.5)]
    if name == "drop_hose_adapter":
        return [(Pos(0, 0, 0), z0, K.socket_top + CFG.drop_tube.barb_len - 0.5)]
    z, leg2 = dc._bend(CFG)
    return [(Pos(0, 0, 0), z0, z - K.r_bore), (leg2, K.r_bore, C.leg_len + CFG.exit.spigot_len - 0.5)]


@pytest.mark.parametrize("name", NAMES)
def test_bore_keeps_the_drop_tube_bore(parts, name):
    """Nothing inside the drop tube bore, and the wall starts at it: the bore is no narrower and no wider."""
    for frame, z0, z1 in _axes(name):
        for i in range(5):
            z = z0 + (z1 - z0) * i / 4
            inside = frame * _cyl(K.r_bore - 0.01, z - 0.2, z + 0.2)
            ring = frame * (_cyl(K.r_bore + 0.05, z - 0.2, z + 0.2) - _cyl(K.r_bore - 0.01, z - 0.3, z + 0.3))
            assert _volume(parts[name] & inside) < EPS, (name, z)
            assert _volume(parts[name] & ring) > EPS, (name, z)


def test_walls_hold_everywhere(parts):
    assert K.r_spigot - K.r_bore >= MW  # male end
    assert K.r_tube - K.r_bore >= MW
    assert K.r_barb - K.r_bore >= MW
    assert CFG.drop_tube.barb_ridges * CFG.drop_tube.barb_ridge_pitch <= CFG.drop_tube.barb_len
    assert K.r_barb == pytest.approx((CFG.drop_tube.hose_id + CFG.drop_tube.barb_grip) / 2)
    assert parts["drop_hose_adapter"].bounding_box().max.Z == pytest.approx(K.socket_top + CFG.drop_tube.barb_len)  # noqa: SIM300


def test_the_form_is_the_same_at_both_ends_of_every_part(parts):
    """The male end matches the exit spigot (same lugs and outline, wide lug on +x) and the socket is the drop tube's."""
    for name, z in (("drop_spacer", K.socket_top + C.spacer_len), ("drop_angled", None)):
        part = parts[name]
        frame = Pos(0, 0, z) if z is not None else dc.male_frames()[name.removeprefix("drop_")]
        lugs = frame * b.spigot_lugs()
        assert _volume(part & lugs) > EPS  # the lugs are part of it
        slab = frame * (Pos(0, 0, CFG.drop_tube.lug_z + CFG.drop_tube.lug_h + CFG.drop_tube.lug_tip + 1) * Cylinder(K.r_spigot + 1, 0.2))
        assert (part & slab).bounding_box().size.X / 2 == pytest.approx(K.r_spigot, abs=0.01), name  # noqa: SIM300
        wide = frame * Pos(K.r_spigot + CFG.drop_tube.lug_h / 2, 0, CFG.drop_tube.lug_z + CFG.drop_tube.lug_h)
        narrow = frame * Pos(-(K.r_spigot + CFG.drop_tube.lug_h / 2), 0, CFG.drop_tube.lug_z + CFG.drop_tube.lug_h)
        assert part.is_inside(wide.position), name
        assert part.is_inside(narrow.position), name


def test_chain_hangs_part_on_part_and_the_window_stays():
    chain = dc.frames(FULL)
    assert [n for n, _ in chain] == ["drop_spacer", "drop_angled", "drop_hose_adapter"]
    assert dt.dims(FULL) == K  # the first tube does not depend on the chain: its window and sensor stay
    x = dt.placement().x_dir
    placed = [(dt.placement().location, dt.drop_tube())] + [(f, dc.PARTS[n](FULL)) for n, f in chain]
    for (f0, p0), (f1, p1) in itertools.pairwise(placed):
        assert _volume(f0 * p0 & f1 * p1) < EPS  # not into each other when hanging
        assert _volume(f0 * p0 & f1 * Pos(0, 0, 0.05) * p1) > EPS  # the lugs carry it: it cannot sink further
        dx = (f1 * Pos(1, 0, 0)).position - f1.position
        assert pytest.approx((x.X, x.Y, x.Z), abs=1e-6) == (dx.X, dx.Y, dx.Z)  # +x, the sensor side, carries through


def test_default_assembly_has_the_hose_adapter_and_no_optional_part():
    names = {p.name for p in assembly.placed()}
    assert "drop_hose_adapter" in names
    assert not names & {"drop_spacer", "drop_angled", "body_exit_insert_blank"}
    full = {p.name for p in assembly.placed(FULL)}
    assert {"drop_spacer", "drop_angled", "drop_hose_adapter"} <= full


def test_unknown_chain_part_names_the_supported_ones():
    with pytest.raises(ValueError, match="spacer, angled"):
        dc.frames(replace(CFG, drop_chain=replace(C, parts=("offset",))))


@pytest.mark.parametrize("left", [False, True], ids=["right", "left"])
def test_full_chain_clears_the_body_mount_box_and_sensor(left):
    lo, hi = m.tilt_span()
    box = el.box_left() if left else el.box()
    sensor = dt.sensor_frame(FULL) * Cylinder(CFG.drop_tube.sensor_thread_d / 2, CFG.drop_tube.sensor_length, align=sc.BOTTOM)
    chain = [f * dc.PARTS[n](FULL) for n, f in dc.frames(FULL)]
    for tilt in (lo, (lo + hi) / 2, hi):
        others = [b.core(), m.clamp_in_body(m.PARTS["mount_clamp"](), tilt), m.yoke_in_body(m.PARTS["mount_yoke"]()), el.box_frame(tilt, left=left) * box]
        for part in chain:
            assert all(_overlap(part, o) < EPS for o in [*others, sensor]), tilt


@pytest.mark.parametrize("name", NAMES)
def test_chain_parts_print_without_supports(parts, name):
    assert _unsupported(Pos(0, 0, -0.013) * parts[name], step=0.5) == []
    assert printing.fits(printing.on_bed(name, parts[name]))


def test_angled_piece_tilt_is_within_what_the_lugs_print():
    assert 0 < C.angle <= 35
