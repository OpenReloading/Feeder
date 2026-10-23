import itertools
import math
from dataclasses import replace

import pytest
from build123d import Cylinder, Pos, RegularPolygon, Rot

from feeder import assembly
from feeder.config import CFG, GENERIC_8MM_FLANGE
from feeder.lib import fasteners
from feeder.lib.features import d_bore, hex_corner_r
from feeder.parts import layout
from feeder.parts import slip_clutch as sc

C, M, MH, PS, DR, FIT, MW = CFG.clutch, CFG.motor, CFG.metal_hub, CFG.plate_seat, CFG.drive_ring, CFG.print.fit, CFG.print.min_wall
HUB_OPTIONS, HUB_IDS = [MH, GENERIC_8MM_FLANGE], ["pololu_2693", "generic_8mm_flange"]
LOW, HIGH = C.friction_mu


@pytest.fixture(scope="module")
def parts():
    return {name: build() for name, build in sc.PARTS.items()}


def test_parts_are_single_valid_solids(parts):
    for name, part in parts.items():
        assert part.is_valid, name
        assert len(part.solids()) == 1, name
        assert part.volume > 0, name


@pytest.mark.parametrize("direction", [1, -1])
def test_threaded_parts_mesh_for_the_3mf_export(direction):
    """Every face triangulates at the assembly 3MF settings: sliver faces at the thread ends do not."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopLoc import TopLoc_Location

    cfg = replace(CFG, case_plate=replace(CFG.case_plate, direction=direction))
    for part in (sc.cap(cfg), sc.drive_ring(cfg)):
        BRepMesh_IncrementalMesh(part.wrapped, 0.05, True, 0.3, True)
        assert all(BRep_Tool.Triangulation_s(f.wrapped, TopLoc_Location()) is not None for f in part.faces())


def test_hub_sits_on_the_flat_and_clears_the_floor():
    z = sc.levels()
    assert z.hub_bottom - z.boss_face >= M.shaft_length - M.flat_length  # above the round shaft section
    assert z.floor_top < z.hub_bottom


def test_hub_gauge_carries_the_hub_fits_the_cup_and_slides_out_from_under_it():
    placed = {p.name: p.shape for p in assembly.placed()}
    gauge, hub = placed["slip_clutch_hub_gauge"], placed["pololu_hub"]
    fixed = [placed[n] for n in ("body_core", "pololu_hub", "motor_shaft")]
    assert gauge.distance_to(hub) < 1e-6  # the boss rests on the fork
    assert gauge.bounding_box().max.Z >= layout.levels().deck_top + C.gauge_grip - 1  # handle up past the deck
    s = sc.gauge_slide()
    path = [Pos(s * i / 4, 0, 0) for i in range(5)] + [Pos(s, 0, dz) for dz in (5, 20, 40)]
    for loc in path:
        moved = loc * gauge
        for other in fixed:
            common = moved & other
            assert (common.volume if common.solids() else 0.0) < 1e-3, loc


def test_countersunk_motor_screws_fit_the_floor():
    head = fasteners.countersunk_screw(M.mount_screw_size, fasteners.countersunk_screw_lengths(M.mount_screw_size)[0]).screw_data
    assert CFG.body.floor_t - head["k"] >= CFG.print.min_wall


@pytest.mark.parametrize("mh", HUB_OPTIONS, ids=HUB_IDS)
def test_metal_hub_screws_are_standard_and_hold_the_carrier(mh):
    size, length = mh.hole_size, mh.screw_length
    assert length in fasteners.socket_screw_lengths(size)
    below = length - C.carrier_base_t - mh.flange_t  # screw beyond the flange
    if mh.threaded:
        assert min(length - C.carrier_base_t, mh.flange_t) >= CFG.fasteners.min_engagement * fasteners.nominal_d(size)
    else:
        nut = fasteners.hex_nut(size).nut_data
        assert below >= nut["m"] + CFG.fasteners.coarse_pitch[size]  # nut fully on with a thread to spare
        assert mh.hole_pcd / 2 - hex_corner_r(nut["s"]) >= mh.boss_d / 2  # nut turns beside the boss
    assert below < mh.boss_h + C.floor_gap  # tip stays above the floor
    assert mh.hole_pcd / 2 - mh.boss_d / 2 > fasteners.clearance_d(size) / 2  # tip passes beside the boss


@pytest.mark.parametrize("mh", HUB_OPTIONS, ids=HUB_IDS)
def test_hub_screws_match_the_hub_hole_pattern(mh):
    assert mh.hole_count % mh.screws == 0


def test_generic_hub_carrier_builds():
    part = sc.carrier(replace(CFG, metal_hub=GENERIC_8MM_FLANGE))
    assert part.is_valid and len(part.solids()) == 1


def test_hex_corners_point_at_the_hub_screws():
    corner = max(RegularPolygon(C.key_af / 2, 6, major_radius=False).vertices(), key=lambda v: v.X)
    assert math.degrees(math.atan2(corner.Y, corner.X)) == pytest.approx(0, abs=1e-6)


def test_knob_screw_is_standard_and_engages_without_bottoming():
    size, length = C.knob_screw_size, C.knob_screw_length
    assert length in fasteners.hex_screw_lengths(size)
    insert = CFG.fasteners.inserts[size]
    engaged = length - (C.knob_t - fasteners.hex_screw(size, length).screw_data["k"])
    assert engaged >= CFG.fasteners.min_engagement * fasteners.nominal_d(size)
    assert engaged <= insert.hole_depth
    z = sc.levels()
    below = max(z.shaft_tip + C.shaft_tip_gap, z.base_top)
    assert z.top - insert.hole_depth - below >= CFG.print.min_wall
    assert C.key_af / 2 - insert.hole_d / 2 >= insert.min_wall


@pytest.mark.parametrize("mh", HUB_OPTIONS, ids=HUB_IDS)
def test_metal_counterbores_keep_walls_to_the_knob_insert(mh):
    head_r = fasteners.socket_screw(mh.hole_size, mh.screw_length).screw_data["dk"] / 2 + CFG.fasteners.head_fit
    insert = CFG.fasteners.inserts[C.knob_screw_size]
    assert mh.hole_pcd / 2 - head_r - insert.hole_d / 2 >= insert.min_wall


def test_walls_around_key_and_spring_pockets():
    pocket_r = CFG.spring.bore_d / 2
    assert C.spring_pcd / 2 - pocket_r - hex_corner_r(C.key_af + 2 * FIT) >= CFG.print.min_wall
    assert C.disc_d / 2 - (C.spring_pcd / 2 + pocket_r) >= CFG.print.min_wall
    assert C.knob_d / 2 - C.knob_grip_d / 2 - (C.spring_pcd / 2 + pocket_r) >= CFG.print.min_wall
    assert C.disc_t - C.spring_pocket_depth_disc >= CFG.print.min_wall


def test_cone_does_not_wedge_and_seats_within_the_margins():
    assert math.tan(math.radians(DR.cone_half_angle)) > HIGH
    drop = layout.seat_drop()  # the ring sits this much lower than nominal on the cone fit
    assert drop < C.clamp_margin  # and still clears the male cone top
    assert drop < DR.base_gap
    assert hex_corner_r(C.key_af + 2 * FIT) < sc.floor_hole_r()  # the disc bears on the whole floor annulus


def test_drive_ring_walls_and_thread():
    z = sc.levels()
    assert sc.thread_root_r() - sc.tube_bore_r() >= MW  # tube wall under the thread
    assert PS.drive_af / 2 - sc.tube_bore_r() >= MW
    assert PS.drive_af - 2 * PS.lead_in > DR.thread_d  # the plate hole passes over the thread
    assert DR.flange_d / 2 - hex_corner_r(PS.drive_af + 2 * FIT) - PS.lead_in >= MW  # plate seat beyond the hole corners
    assert DR.flange_t >= MW and z.ring_floor - z.plate_bottom >= MW  # flange, floor above the cone
    assert DR.floor_h - sc.female_cone_h() >= MW - 1e-9  # floor at its hole edge
    assert z.hex_top - PS.lead_in > z.plate_bottom
    assert z.ring_top < z.top  # the knob, wider than the tube bore, sits above the tube
    assert sc.tube_bore_r() > C.disc_d / 2 and C.disc_t + z.ring_floor <= z.ring_top


def test_cap_passes_the_knob_and_clamps_the_plate_without_play():
    z = sc.levels()
    assert sc.cap_crest_r() - C.knob_d / 2 >= 2 * FIT  # the cap thread crest slides over the knob
    assert z.cap_face == pytest.approx(z.plate_bottom + PS.hub_h)  # the cap face sits on the plate top
    assert z.cap_face - z.hex_top >= CFG.case_plate.flatness / 2  # and stops on the plate, never on the hex
    assert z.ring_top - z.cap_face >= DR.thread_len - DR.top_margin  # thread engaged over the top margin
    assert z.cap_top - z.cap_face - CFG.cap.top_t > z.knob_top - z.cap_face  # ceiling over the knob
    assert CFG.cap.d / 2 - CFG.cap.grip_d / 2 - hex_corner_r(PS.drive_af + 2 * FIT) >= MW  # clamp face between the grips and hole
    assert z.cap_top - z.plate_bottom >= PS.max_height  # the cap stands above the tallest plate


def test_cap_holds_the_plate_against_tipping():
    lo = CFG.mount.tilt_range[0] - CFG.mount.tilt_margin  # flattest tilt: largest normal load
    moment = layout.tipping_moment(lo)
    r_face = hex_corner_r(PS.drive_af + 2 * FIT)  # inner edge of the cap face, the shortest lever
    reaction = moment * 1000 / (DR.flange_d / 2 + r_face)  # plate tips about the low flange edge, the cap holds the high side
    # the reaction tips the cap about its low face edge (arm 2 r_face) against the preload on the axis (arm r_face)
    assert sc.cap_clamp_force() >= 1.5 * 2 * reaction
    assert sc.clamp_force(C.springs_fitted) * sc.floor_hole_r() / 1000 >= moment  # springs keep the ring on the cone


def test_cap_thread_self_locks_and_tightens_with_the_plate():
    r_m = DR.thread_d / 2 - DR.thread_depth / 2
    lead = math.degrees(math.atan(sc.thread_lead() / (2 * math.pi * r_m)))
    assert lead < math.degrees(math.atan(LOW / math.cos(math.radians(DR.thread_angle / 2))))
    assert sc.thread_hand() == "right"  # counter-clockwise plate
    flipped = replace(CFG, case_plate=replace(CFG.case_plate, direction=-1))
    assert sc.thread_hand(flipped) == "left"


def test_spring_works_between_solid_and_free_length():
    length = sc.spring_working_length()
    assert CFG.spring.solid_length < length < CFG.spring.free_length
    assert sc.clamp_force(1) <= CFG.spring.max_force


def test_metal_hub_clutch_is_a_backstop_above_the_current_limit():
    n = C.springs_fitted
    assert sc.slip_torque(n, LOW) >= C.backstop_margin * CFG.electronics.current_limit_torque
    assert sc.slip_torque(n, HIGH) <= M.gearbox_torque_limit
    flattest = replace(CFG, case_plate=replace(CFG.case_plate, tilt=CFG.mount.tilt_range[0] - CFG.mount.tilt_margin))
    assert CFG.electronics.current_limit_torque >= C.backstop_margin * layout.plate_drag_torque(flattest)
    assert sc.slip_torque(n, LOW) >= C.backstop_margin * layout.plate_drag_torque(flattest)


def test_cap_thread_meshes_with_the_ring():
    assert assembly.cap_angle()[1] < 1e-6


def _plate_stub(z):
    outer = CFG.cap.d  # any radius beyond the recess
    plate = Cylinder(outer, PS.max_height, align=sc.BOTTOM) - sc.plate_seat_cut(PS.max_height)
    return Pos(0, 0, z.plate_bottom) * plate


def _motor_side(z):
    shaft = Pos(0, 0, z.boss_face) * d_bore(M.shaft_d, M.shaft_across_flat, M.shaft_length)
    boss = Pos(0, 0, z.gearbox_face) * Cylinder(M.boss_d / 2, M.boss_h, align=sc.BOTTOM)
    floor = Pos(0, 0, z.gearbox_face) * (
        Cylinder(CFG.cap.d, CFG.body.floor_t, align=sc.BOTTOM) - Cylinder(M.boss_d / 2 + FIT, CFG.body.floor_t, align=sc.BOTTOM)
    )
    return {"shaft": shaft, "boss": boss, "floor": floor}


def _metal_hub(z):
    hub = Pos(0, 0, z.hub_bottom) * Cylinder(MH.boss_d / 2, MH.boss_h, align=sc.BOTTOM)
    hub += Pos(0, 0, z.hub_bottom + MH.boss_h) * Cylinder(MH.flange_d / 2, MH.flange_t, align=sc.BOTTOM)
    return hub - Pos(0, 0, z.hub_bottom) * Cylinder(MH.bore_d / 2, MH.boss_h + MH.flange_t, align=sc.BOTTOM)


def test_assembly_has_no_interference(parts):
    z = sc.levels()
    stack = {
        "clutch": parts["slip_clutch_carrier_metal_hub"],
        "ring": Pos(0, 0, z.ring_bottom) * parts["slip_clutch_drive_ring"],
        "disc": Pos(0, 0, z.ring_floor) * parts["slip_clutch_disc"],
        "knob": Pos(0, 0, z.top) * parts["slip_clutch_knob"],
        "cap": assembly.cap_on_ring(),
        "plate": _plate_stub(z),
        **_motor_side(z),
        "metal_hub": _metal_hub(z),
    }
    for (a, pa), (b, pb) in itertools.combinations(stack.items(), 2):
        overlap = pa & pb
        volume = overlap.volume if overlap.solids() else 0.0
        assert volume < 1e-6, f"{a} overlaps {b} by {volume:.4f} mm3"
