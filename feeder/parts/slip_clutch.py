"""Slip clutch between the motor's D shaft and the collator plate.

The printed drive ring sits with its 45 deg female cone on the carrier's male cone. The pressure disc,
keyed to the carrier hex, presses the ring floor. The ring slips on both faces, takes the wear and stays on
the clutch when plates are changed. Springs between the knob and the disc set the clamp force. The knob's
M5 screw runs into an insert in the carrier top and bottoms the knob once at assembly, so the slip torque
never changes. The plate drops onto the ring flange over the ring hex, the cap twists onto the ring thread
and clamps the plate. Plate changes never touch disc, springs or knob.

Hub: printed carrier bolted onto a Pololu 2693 aluminium hub (set screws on the D flat).

Frame: z = 0 at the bottom of the carrier, +z up the shaft, flat of the D shaft facing +x.
"""

import copy  # noqa: I001
import math
from dataclasses import dataclass

from bd_warehouse.thread import Thread
from build123d import Align, Box, Compound, Cone, Cylinder, Part, Pos, RegularPolygon, Rot, extrude

from feeder.config import CFG, Config
from feeder.lib.cache import per_config
from feeder.lib import fasteners
from feeder.lib.features import hex_corner_r, hex_prism

BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@dataclass(frozen=True)
class Levels:
    """Derived z levels in the carrier frame."""

    hub_bottom: float  # lowest rotating part
    floor_top: float  # body floor top, below the hub
    gearbox_face: float  # motor mounting face, below the floor
    boss_face: float  # stationary motor boss face, inside the floor hole
    shaft_tip: float
    base_top: float  # top of the clutch base, below the ring
    ring_bottom: float
    ring_floor: float  # ring floor top, where the disc bears
    plate_bottom: float  # flange top, the plate seat
    hex_top: float
    cap_face: float  # plate top at the hub, where the cap clamps
    ring_top: float  # thread top
    cone_top: float
    top: float  # carrier top, knob stop
    knob_top: float
    cap_top: float


def levels(cfg: Config = CFG) -> Levels:
    m, c, ps, mh, dr = cfg.motor, cfg.clutch, cfg.plate_seat, cfg.metal_hub, cfg.drive_ring
    metal_h = mh.flange_t + mh.boss_h
    hub_bottom = -metal_h
    base_top = c.carrier_base_t
    floor_top = hub_bottom - c.floor_gap
    gearbox_face = floor_top - cfg.body.floor_t
    boss_face = gearbox_face + m.boss_h
    ring_bottom = base_top + dr.base_gap
    ring_floor = ring_bottom + dr.floor_h
    plate_bottom = ring_bottom + dr.flange_t
    cap_face = plate_bottom + ps.hub_h
    hex_top = cap_face - dr.top_margin
    top = ring_floor + c.key_h
    knob_top = top + c.knob_t
    return Levels(
        hub_bottom=hub_bottom,
        floor_top=floor_top,
        gearbox_face=gearbox_face,
        boss_face=boss_face,
        shaft_tip=boss_face + m.shaft_length,
        base_top=base_top,
        ring_bottom=ring_bottom,
        ring_floor=ring_floor,
        plate_bottom=plate_bottom,
        hex_top=hex_top,
        cap_face=cap_face,
        ring_top=hex_top + dr.thread_len,
        cone_top=ring_floor - c.clamp_margin,
        top=top,
        knob_top=knob_top,
        cap_top=knob_top + cfg.cap.knob_gap + cfg.cap.top_t,
    )


def _tan(cfg: Config) -> float:
    return math.tan(math.radians(cfg.drive_ring.cone_half_angle))


def male_cone_r(z: float, cfg: Config = CFG) -> float:
    """Radius of the male cone at height z: the ring cone less the fit."""
    return cfg.drive_ring.cone_d / 2 - cfg.print.fit - (z - levels(cfg).ring_bottom) * _tan(cfg)


def female_cone_h(cfg: Config = CFG) -> float:
    """The female cone ends a minimum wall below the floor top, so the floor has no feather edge at its hole."""
    return cfg.drive_ring.floor_h - cfg.print.min_wall


def floor_hole_r(cfg: Config = CFG) -> float:
    """Ring floor hole: the female cone at its top, straight up from there."""
    return cfg.drive_ring.cone_d / 2 - female_cone_h(cfg) * _tan(cfg)


def tube_bore_r(cfg: Config = CFG) -> float:
    return cfg.clutch.disc_d / 2 + cfg.drive_ring.disc_gap


def thread_root_r(cfg: Config = CFG) -> float:
    """Ring thread root, also the tube outside."""
    dr = cfg.drive_ring
    return dr.thread_d / 2 - dr.thread_depth


def thread_clearance(cfg: Config = CFG) -> float:
    """Radial offset of the cap thread: one sliding fit normal to the flanks."""
    return cfg.print.fit / math.sin(math.radians(cfg.drive_ring.thread_angle / 2))


def cap_crest_r(cfg: Config = CFG) -> float:
    """Narrowest radius of the cap: its thread crest."""
    return cfg.drive_ring.thread_d / 2 + thread_clearance(cfg) - cfg.drive_ring.thread_depth


def thread_hand(cfg: Config = CFG) -> str:
    """Right-hand for a counter-clockwise plate: brass drag on the cap turns it clockwise on the ring, which tightens it.
    Cap inertia at 1 to 2 rpm is far below the thread friction, so starts and stops do not turn it either way."""
    return "right" if cfg.case_plate.direction > 0 else "left"


def thread_lead(cfg: Config = CFG) -> float:
    return cfg.drive_ring.thread_pitch * cfg.drive_ring.thread_starts


def spring_working_length(cfg: Config = CFG) -> float:
    c = cfg.clutch
    return (c.key_h - c.disc_t) + c.spring_pocket_depth_disc + c.spring_pocket_depth_knob


def clamp_force(springs: int, cfg: Config = CFG) -> float:
    s = cfg.spring
    return springs * s.rate * (s.free_length - spring_working_length(cfg))


def friction_radius_sum(cfg: Config = CFG) -> float:
    """Torque per unit friction and clamp force, mm: cone face (mean radius / sin a) plus disc face (mean radius)."""
    dr, c = cfg.drive_ring, cfg.clutch
    r_bottom = dr.cone_d / 2
    r_top = r_bottom - min(female_cone_h(cfg), dr.floor_h - c.clamp_margin) * _tan(cfg)
    cone = (r_bottom + r_top) / 2 / math.sin(math.radians(dr.cone_half_angle))
    disc = (floor_hole_r(cfg) + c.disc_d / 2) / 2  # ring floor annulus under the disc
    return cone + disc


def slip_torque(springs: int, mu: float, cfg: Config = CFG) -> float:
    """Nm."""
    return mu * clamp_force(springs, cfg) * friction_radius_sum(cfg) / 1000


def cap_clamp_force(cfg: Config = CFG) -> float:
    """N the cap presses on the plate at `cap.hand_torque`: thread at its mean radius (lead and flank friction)
    plus the clamp face, from the plate hole corners to the cap rim."""
    cp, dr = cfg.cap, cfg.drive_ring
    r_m = dr.thread_d / 2 - dr.thread_depth / 2
    lead = math.atan(thread_lead(cfg) / (2 * math.pi * r_m))
    flank = math.atan(cp.mu / math.cos(math.radians(dr.thread_angle / 2)))
    r_face = (hex_corner_r(cfg.plate_seat.drive_af + 2 * cfg.print.fit) + cp.d / 2) / 2
    return cp.hand_torque * 1000 / (r_m * math.tan(lead + flank) + cp.mu * r_face)


def cap_holding_torque(cfg: Config = CFG) -> float:
    """Nm to turn the cap off at the `cap_clamp_force` clamp: thread friction at the low estimate `cap.mu_low`, on the
    thread alone (the face friction on the plate, which turns with the ring, is left out)."""
    cp, dr = cfg.cap, cfg.drive_ring
    r_m = dr.thread_d / 2 - dr.thread_depth / 2
    lead = math.atan(thread_lead(cfg) / (2 * math.pi * r_m))
    flank = math.atan(cp.mu_low / math.cos(math.radians(dr.thread_angle / 2)))
    return cap_clamp_force(cfg) * r_m * math.tan(flank - lead) / 1000


def _around(count: int, radius: float, start: float = 0.0):
    for i in range(count):
        a = math.radians(start + 360 * i / count)
        yield Pos(radius * math.cos(a), radius * math.sin(a))


def _thread(cfg: Config, external: bool) -> Part:
    """Multi-start trapezoidal thread, built per start like bd_warehouse TrapezoidalThread, which fixes the depth
    at half the pitch and so leaves no crest at 45 deg flanks."""
    dr = cfg.drive_ring
    d = dr.thread_d if external else dr.thread_d + 2 * thread_clearance(cfg)
    L, c = dr.thread_len, dr.thread_depth
    shoulder = c * math.tan(math.radians(dr.thread_angle / 2))
    root, crest = (d / 2 - c, d / 2) if external else (d / 2, d / 2 - c)
    start = Thread(
        apex_radius=crest, apex_width=dr.thread_pitch / 2 - shoulder, root_radius=root, root_width=dr.thread_pitch / 2 + shoulder,
        pitch=thread_lead(cfg), length=L, hand=thread_hand(cfg), end_finishes=("raw", "raw"),
    )
    thread = Part(Compound([copy.copy(start).move(Rot(Z=i * 360 / dr.thread_starts)) for i in range(dr.thread_starts)]))
    # 45 deg chamfer ends from the root to the crest, own cut: bd_warehouse "chamfer" leaves open STL edges
    if external:
        keep = Cylinder(root, L, align=BOTTOM) + Cone(root, crest, c, align=BOTTOM) + Pos(0, 0, c) * Cylinder(crest, L - 2 * c, align=BOTTOM)
        return thread & (keep + Pos(0, 0, L - c) * Cone(crest, root, c, align=BOTTOM))
    e, g = 0.4, 0.1  # past the 0.2 thread interference and inside the crest: 0.3 left a zero-area bore face that does not mesh
    h = c + e + g
    cut = Cone(root + e, crest - g, h, align=BOTTOM) + Pos(0, 0, L - h) * Cone(crest - g, root + e, h, align=BOTTOM)
    return (thread & Cylinder(d, L, align=BOTTOM)) - cut


@per_config
def drive_ring(cfg: Config = CFG) -> Part:
    """Wear ring, ring frame z = 0 at the ring bottom. Print flange down."""
    dr, ps = cfg.drive_ring, cfg.plate_seat
    z = levels(cfg)
    seat, hex_top, top = z.plate_bottom - z.ring_bottom, z.hex_top - z.ring_bottom, z.ring_top - z.ring_bottom
    body = Cylinder(dr.flange_d / 2, dr.flange_t, align=BOTTOM)
    body += Pos(0, 0, seat) * hex_prism(ps.drive_af, hex_top - seat - ps.lead_in)
    body += Pos(0, 0, hex_top - ps.lead_in) * extrude(RegularPolygon(ps.drive_af / 2, 6, major_radius=False), ps.lead_in, taper=45)
    body += Pos(0, 0, hex_top) * Cylinder(thread_root_r(cfg), top - hex_top, align=BOTTOM)
    body += Pos(0, 0, hex_top) * _thread(cfg, external=True)
    body -= Cone(dr.cone_d / 2, floor_hole_r(cfg), female_cone_h(cfg), align=BOTTOM)
    body -= Pos(0, 0, female_cone_h(cfg)) * Cylinder(floor_hole_r(cfg), dr.floor_h - female_cone_h(cfg), align=BOTTOM)
    body -= Pos(0, 0, dr.floor_h) * Cylinder(tube_bore_r(cfg), top - dr.floor_h, align=BOTTOM)
    return body


@per_config
def cap(cfg: Config = CFG) -> Part:
    """Cap, frame z = 0 at its clamp face. Modelled face down, print top down."""
    cp, dr = cfg.cap, cfg.drive_ring
    z = levels(cfg)
    h = z.cap_top - z.cap_face
    root_r = dr.thread_d / 2 + thread_clearance(cfg)
    body = Cylinder(cp.d / 2, h, align=BOTTOM)
    for p in _around(cp.grip_count, cp.d / 2):
        body -= p * Cylinder(cp.grip_d / 2, h, align=BOTTOM)
    body -= Cylinder(root_r, h - cp.top_t, align=BOTTOM)
    return body + _thread(cfg, external=False)


def plate_seat_cut(plate_height: float, cfg: Config = CFG) -> Part:
    """Tool the plate subtracts at its centre, z = 0 at the plate bottom: hex hole over the ring hex with a
    lead-in at the bottom, and the cap recess above `hub_h` in a thicker plate."""
    ps, f = cfg.plate_seat, cfg.print.fit
    af = ps.drive_af + 2 * f
    tool = hex_prism(af, max(plate_height, ps.hub_h))
    tool += extrude(RegularPolygon(af / 2 + ps.lead_in, 6, major_radius=False), ps.lead_in, taper=45)
    if plate_height > ps.hub_h:
        tool += Pos(0, 0, ps.hub_h) * Cylinder(cfg.cap.d / 2 + ps.cap_gap, plate_height - ps.hub_h, align=BOTTOM)
    return tool


def _upper(cfg: Config) -> Part:
    """Base, male cone and hex key."""
    c = cfg.clutch
    z = levels(cfg)
    base_r = male_cone_r(z.base_top, cfg)
    body = Cylinder(base_r, z.base_top, align=BOTTOM)
    body += Pos(0, 0, z.base_top) * Cone(base_r, male_cone_r(z.cone_top, cfg), z.cone_top - z.base_top, align=BOTTOM)
    body += Pos(0, 0, z.cone_top) * hex_prism(c.key_af, z.top - z.cone_top)
    body -= Pos(0, 0, z.top) * fasteners.insert_hole(c.knob_screw_size)
    return body


@per_config
def carrier(cfg: Config = CFG) -> Part:
    """Printed carrier for the Pololu 2693 hub."""
    c, mh = cfg.clutch, cfg.metal_hub
    z = levels(cfg)
    body = _upper(cfg)
    # every other hub hole, starting at 0 deg where a hex corner lies, so the counterbores cut corners, not flats
    for p in _around(mh.screws, mh.hole_pcd / 2):
        body -= p * Pos(0, 0, z.base_top) * fasteners.clearance_hole(mh.hole_size, z.base_top)
        body -= p * Pos(0, 0, z.top) * fasteners.socket_head_counterbore(mh.hole_size, mh.screw_length, z.top - z.base_top)
    if z.shaft_tip > 0:
        body -= Cylinder(mh.bore_d / 2 + cfg.print.fit, z.shaft_tip + c.shaft_tip_gap, align=BOTTOM)
    return body


def _pocket_r(cfg: Config) -> float:
    return cfg.spring.bore_d / 2


@per_config
def disc(cfg: Config = CFG) -> Part:
    c = cfg.clutch
    body = Cylinder(c.disc_d / 2, c.disc_t, align=BOTTOM)
    body -= hex_prism(c.key_af + 2 * cfg.print.fit, c.disc_t)
    for p in _around(c.spring_pockets, c.spring_pcd / 2):
        body -= p * Pos(0, 0, c.disc_t) * Cylinder(_pocket_r(cfg), c.spring_pocket_depth_disc, align=fasteners.DOWN)
    return body


@per_config
def knob(cfg: Config = CFG) -> Part:
    c = cfg.clutch
    body = Cylinder(c.knob_d / 2, c.knob_t, align=BOTTOM)
    for p in _around(c.knob_grip_count, c.knob_d / 2):
        body -= p * Cylinder(c.knob_grip_d / 2, c.knob_t, align=BOTTOM)
    body -= Pos(0, 0, c.knob_t) * fasteners.clearance_hole(c.knob_screw_size, c.knob_t)
    body -= Pos(0, 0, c.knob_t) * fasteners.hex_head_pocket(c.knob_screw_size, c.knob_screw_length)
    for p in _around(c.spring_pockets, c.spring_pcd / 2):
        body -= p * Cylinder(_pocket_r(cfg), c.spring_pocket_depth_knob, align=BOTTOM)
    return body


def gauge_slide(cfg: Config = CFG) -> float:
    """How far the hub gauge slides along +x until its prong tips clear the hub flange and it lifts out."""
    mh = cfg.metal_hub
    return mh.boss_d / 2 + 1 + mh.flange_d / 2 + cfg.print.fit


@per_config
def hub_gauge(cfg: Config = CFG) -> Part:
    """Fork as thick as the floor gap under the hub boss, open toward -x around the shaft, a handle up past the deck
    beside the hub flange, `gauge_grip` above the plate bottom. Lay it on the cup floor, push the hub down onto it, tighten the set screws, slide it out
    along +x by `gauge_slide` and lift it out: the plate then sits at its design height above the track.
    Body frame, z = 0 on the cup floor. Prints fork down."""
    c, m, mh, f = cfg.clutch, cfg.motor, cfg.metal_hub, cfg.print.fit
    reach, w, t = mh.boss_d / 2 + 1, mh.boss_d + 4, 2 * cfg.print.min_wall
    x_h = mh.flange_d / 2 + 1  # handle face beside the flange
    body = Pos((x_h + t - reach) / 2, 0) * Box(x_h + t + reach, w, c.floor_gap, align=BOTTOM)
    zc = levels(cfg)
    body += Pos(x_h + t / 2, 0) * Box(t, w, zc.plate_bottom - zc.floor_top + c.gauge_grip, align=BOTTOM)
    slot = m.shaft_d + 2 * f
    body -= Pos(-reach / 2, 0) * Box(reach, slot, c.floor_gap, align=BOTTOM)
    return body - Cylinder(slot / 2, c.floor_gap, align=BOTTOM)


PARTS = {
    "slip_clutch_carrier_metal_hub": carrier,
    "slip_clutch_drive_ring": drive_ring,
    "slip_clutch_disc": disc,
    "slip_clutch_knob": knob,
    "slip_clutch_cap": cap,
    "slip_clutch_hub_gauge": hub_gauge,
}
