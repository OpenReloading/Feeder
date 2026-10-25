"""Every dimension (mm, N, Nm) and option of the feeder.

Part modules read only from here. Standard fastener data (head sizes, nominal lengths,
ISO 273 clearances) comes from bd_warehouse via `feeder.lib.fasteners`, not from this file.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Print:
    fit: float = 0.15  # radial gap of a sliding fit
    min_wall: float = 1.6  # 4 perimeters with a 0.4 nozzle
    bridge: float = 30.0  # longest unsupported span a printed ceiling may have (hole ceilings, bore caps)
    density: float = 1.24  # g/cm3, PLA, unverified
    fill: tuple = (0.5, 0.8)  # printed mass over solid mass (walls plus infill), low and high estimate


@dataclass(frozen=True)
class Insert:
    """Heat-set insert, CNC Kitchen poster "Dimensions & Design Guidelines"
    (https://cdn.shopify.com/s/files/1/0654/4821/4767/files/Poster_Dimensions-Guidlines.pdf)."""

    length: float
    od: float
    hole_d: float
    min_wall: float

    @property
    def hole_depth(self) -> float:
        return self.length + 1.0  # poster: blind hole at least L + 1


@dataclass(frozen=True)
class Fasteners:
    inserts: dict = field(default_factory=lambda: {
        "M3": Insert(length=5.7, od=4.6, hole_d=4.0, min_wall=1.6),
        "M5": Insert(length=9.5, od=7.1, hole_d=6.5, min_wall=2.6),
    })
    coarse_pitch: dict = field(default_factory=lambda: {"M3": 0.5, "M4": 0.7, "M5": 0.8, "M6": 1.0, "M8": 1.25, "M10": 1.5})  # ISO 261
    head_fit: float = 0.2  # radial gap around a captured hex head
    min_engagement: float = 1.5  # thread engagement as a multiple of the nominal diameter


@dataclass(frozen=True)
class Motor:
    """5840-31ZY worm gear motor. NFP 5840-31ZY-EN and Daiwei 634JSX-31ZY drawings
    (https://microdcmotors.com/product/12v-24v-high-torque-low-speed-dc-motor-with-encoder-self-locking-model-nfp-5840-31zy-en,
    https://www.daiweimotor.com/pro_detail/20.html). Owner caliper check pending."""

    shaft_d: float = 8.0
    shaft_across_flat: float = 7.0
    shaft_length: float = 15.0  # from the boss face
    flat_length: float = 13.0  # measured from the shaft tip
    boss_d: float = 19.0  # drawings give 18.5 to 19
    boss_h: float = 2.0  # drawings give 1.5 to 2
    mass: tuple = (0.32, 0.5)  # kg, seller "about 350 g", other sellers 320 to 500, unverified
    gearbox_torque_limit: float = 3.92  # Nm, 40 kg.cm, gearbox limit of the 1240 winding (https://microdcmotors.com/product/12v-24v-high-torque-low-speed-dc-motor-with-encoder-self-locking-model-nfp-5840-31zy-en)
    mount_screw_size: str = "M4"  # 4 tapped holes in the gearbox face
    mount_thread_depth: float = 6.0  # NFP drawing, Daiwei gives 7
    mount_screw_length: float = 10.0  # ISO 10642, through the floor into the gearbox thread
    mount_across: float = 28.0  # hole pairs across the gearbox width
    mount_near: float = 11.0  # near hole pair from the shaft toward the gearbox free end
    mount_far: float = 29.0  # far hole pair from the shaft toward the can
    gearbox_l: float = 58.0
    gearbox_w: float = 40.0
    gearbox_t: float = 27.0  # drawings give 26.8 to 27
    shaft_from_end: float = 20.0  # shaft axis from the gearbox free end, Probots gives 20.5
    can_d: float = 36.0  # NFP gives 31, a Probots drawing 36: the larger one for clearance
    can_l: float = 72.5  # 57 can plus 15.5 covered encoder
    angle: float = 180.0  # deg about the shaft: direction the can points, 0 = +x


@dataclass(frozen=True)
class Printer:
    bed_x: float = 256.0  # Bambu Lab X1, P1 and P2 class, owner default
    bed_y: float = 256.0
    bed_z: float = 256.0
    margin: float = 3.0  # kept free at each bed edge for skirt and brim


@dataclass(frozen=True)
class Caliber:
    """Case dimensions from the C.I.P. TDCC sheets."""

    rim_d: float
    rim_t_min: float  # rim thickness, smallest case
    case_length: float  # maximum


@dataclass(frozen=True)
class Calibers:
    # C.I.P. TDCC Tab IV, cartridge column: R1, e min, L3. Sheets under https://bobp.cip-bobp.org/uploads/tdcc/tab-iv/
    # Rimmed cases: C.I.P. leaves e blank, e min from ANSI/SAAMI Z299.3-2022
    # (https://saami.org/wp-content/uploads/2025/05/SAAMI-Z299.3-2022-Centerfire-Pistol-Revolver-Approved-12-13-2022.pdf)
    table: dict = field(default_factory=lambda: {
        "25_acp": Caliber(rim_d=7.65, rim_t_min=0.75, case_length=15.55),  # tabivcal-en-page4.pdf
        "32_acp": Caliber(rim_d=9.10, rim_t_min=0.80, case_length=17.20),  # tabivcal-en-page12.pdf
        "380_acp": Caliber(rim_d=9.53, rim_t_min=0.80, case_length=17.33),  # tabivcal-en-page24.pdf
        "9mm_makarov": Caliber(rim_d=9.95, rim_t_min=1.00, case_length=18.10),  # tabivcal-en-page23.pdf
        "9mm_luger": Caliber(rim_d=9.96, rim_t_min=0.90, case_length=19.15),  # tabivcal-en-page28.pdf
        "9x21": Caliber(rim_d=9.96, rim_t_min=0.90, case_length=21.15),  # tabivcal-en-page20.pdf
        "45_gap": Caliber(rim_d=11.94, rim_t_min=0.89, case_length=19.30),  # 45-gap-en.pdf
        "40_sw": Caliber(rim_d=10.77, rim_t_min=1.14, case_length=21.59),  # tabivcal-en-page66.pdf
        "357_sig": Caliber(rim_d=10.77, rim_t_min=1.14, case_length=21.97),  # tabivcal-en-page53.pdf
        "38_super": Caliber(rim_d=10.31, rim_t_min=1.02, case_length=22.86),  # tabivcal-en-page61.pdf
        "45_acp": Caliber(rim_d=12.19, rim_t_min=0.89, case_length=22.81),  # 45-auto-en-1.pdf
        "10mm_auto": Caliber(rim_d=10.80, rim_t_min=1.14, case_length=25.20),  # 10-mm-auto-en.pdf (rev 12-05-30)
        "7_62x25": Caliber(rim_d=9.95, rim_t_min=1.00, case_length=25.00),  # tabivcal-en-page9.pdf
        "38_special": Caliber(rim_d=11.18, rim_t_min=1.22, case_length=29.34),  # tabivcal-en-page57.pdf, SAAMI p48
        "44_special": Caliber(rim_d=13.06, rim_t_min=1.24, case_length=29.46),  # tabivcal-en-page74.pdf, SAAMI p56
        "357_magnum": Caliber(rim_d=11.18, rim_t_min=1.24, case_length=32.77),  # 357-magnum-en.pdf, SAAMI p45
        "44_magnum": Caliber(rim_d=13.06, rim_t_min=1.24, case_length=32.64),  # 44-rem-mag-200922-en.pdf, SAAMI p55
        "45_colt": Caliber(rim_d=13.00, rim_t_min=1.24, case_length=32.64),  # tabivcal-en-page78.pdf, SAAMI p59
    })
    # Group plates: the fewest groups (4) that cover the table, each case within 0.34 to 0.40 of its length at the
    # group plate height and at most 2.3 mm rim spread (the smallest rim gets that much more play)
    groups: dict = field(default_factory=lambda: {
        "pocket_pistol": ("25_acp", "32_acp", "380_acp"),
        "small_pistol": ("9mm_makarov", "9mm_luger", "45_gap", "9x21"),
        "large_pistol": ("40_sw", "357_sig", "45_acp", "38_super", "7_62x25", "10mm_auto"),
        "revolver": ("38_special", "357_magnum", "44_special", "44_magnum", "45_colt"),
    })


@dataclass(frozen=True)
class CasePlate:
    """Base-down case plate. Notches open to the rim, closed by the track band. Mouth-down cases sit high, tip at
    the tilt and fall back. Base-down cases ride to the exit. Start values, tune on hardware."""

    caliber: str = "9mm_luger"  # a case in calibers.table (a plate for it alone) or a group in calibers.groups
    pocket_clearance: float = 3.0  # pocket = rim + this, measured to the band. 12 or 15 mm for 9mm: hardware test
    height_ratio: float = 0.37  # plate height over case length, near the estimated centre of mass (0.33 to 0.39). Group plates: the height closest to it for the shortest and longest case
    pocket_pitch: float = 1.6  # pocket spacing over pocket diameter
    notches: bool = True  # False: closed round holes inside a plate rim (A/B option)
    rim_wall: float = 2.4  # holes only: plate outside the pockets
    top_chamfer: float = 1.0  # pocket entry
    bottom_chamfer: float = 0.5  # pocket bottom edge, so a case base does not hang on it
    channel_len: float = 25.0  # pickup channel on the top face, from each pocket toward the centre
    channel_depth: float = 1.5  # at the pocket, rising to the top face at the inner end. Shallow: the pocket wall still holds upright cases
    ribs: str = "low"  # "low": rib_count broad half-round ribs stir the pile. "per_pocket": a ridge between every two pockets, rising toward them (A/B test)
    rib_count: int = 6
    rib_r: float = 5.0  # rib radius
    rib_h: float = 3.0  # rib height above the top face
    ridge_h: float = 6.0  # per_pocket ridge height above the top face at its outer end
    ridge_w: float = 3.0
    pull_len: float = 10.0  # eye beside the cap recess for a split key ring: pull the plate off the ring hex by it
    pull_t: float = 5.0
    pull_h: float = 7.0  # eye top above the top face
    pull_hole_d: float = 3.0  # for the ring wire, up to about 2 mm
    wall_gap: float = 1.25  # radial gap from plate to track band, room for a large printed plate that is not round
    flatness: float = 0.3  # peak to valley of a printed plate bottom that is not flat, half each way
    drag_mass: float = 1.0  # kg brass on the plate at the design fill, the most the load checks allow
    fill_cases: int = 250  # design fill, about drag_mass of 9mm
    packing: float = 0.55  # loose cases over their envelope volume, low estimate (random cylinders about 0.55 to 0.65, unverified)
    drag_mu: float = 0.3  # brass on printed plastic, estimate
    tilt: float = 45.0  # deg from horizontal, start value, tune on hardware
    direction: int = 1  # +1 counter-clockwise seen from above, -1 clockwise


@dataclass(frozen=True)
class Body:
    floor_t: float = 5.0  # body floor between gearbox face and hub, holds the countersunk motor screws
    # "arcs": round core and `wall_segments` wall arcs. "halves": core and wall cut in two through `seam_start`,
    # joined by posts outside the wall, each half prints across the bed diagonal. Both keep the largest plate.
    # "one_piece": one part, plate smaller by the wall.
    split: str = "arcs"
    wall_segments: int = 3  # arcs only
    wall_t: float = 3.6  # each half of the seam lap joint stays over print.min_wall
    wall_h: float = 125.0  # above the plate bottom, the same for every plate: holds the design fill up to 55 deg with the 9mm plate (layout.capacity), the extender only for 60, tune on hardware
    heap_angle: float = 0.0  # deg brass may heap above level toward the high side. Wall top falls at mount.tilt_range[0] minus this toward the high side: 0 is the flattest tilt, no spills in the simulation at 40 and 45 deg with 250 cases. More keeps a flatter, taller high side
    deck_t: float = 4.0  # flat deck the case bases slide on, out to the wall
    cup_wall: float = 3.0
    cup_clearance: float = 2.0  # radial, around the rotating clutch and the motor screw heads
    rib_count: int = 32  # under the deck, down to the bottom plane
    rib_t: float = 2.4
    skirt_t: float = 2.4
    joint_screw_size: str = "M3"
    joint_screw_length: float = 12.0  # ISO 4762, through wall and key rib into the insert
    joint_screws: int = 3  # per wall segment into the core rim
    seam_key: float = 2.0  # length of the lap at each wall seam and depth of the key rib at each wall screw
    key_w: float = 7.0  # key rib on the wall inside, slots into a groove in the core skirt around the screw
    joint_exit_margin: float = 5.0  # deg, wall screws stay this far beyond the exit insert edge
    seam_start: float = 0.0  # deg of the first wall seam, seams stay off the exit (+y) and the low side (-y)
    halves_seam: float = 35.0  # deg, halves: seam plane through the shaft, clear of the can tunnel (along motor.angle), motor screws, exit and mount
    post_screws: int = 3  # halves: ISO 4762 M3 (joint_screw_size, joint_screw_length) per seam post into a heat-set insert
    extender_h: float = 60.0  # wall extender above the wall top, one open arc over the low side, optional part. 0: none
    extender_arc: float = 150.0  # deg, arc centred on the low side (-y): at least the 125 deg where level brass at the steepest tilt stands above the wall top (test_body), 150 fits the bed turned on its slanted flat top, 160 does not (printing.fits)
    extender_lap: float = 15.0  # extender sleeve down over the outside of the wall top
    extender_wall_screws: int = 4  # over the arc: ISO 10642 M3 from inside the bowl through wall and sleeve into an ISO 4032 nut captive in a rib on the sleeve
    can_relief: float = 10.0  # flat top of the can tunnel above the bottom plane, the can rises up to 8.5 (seller drawings)


@dataclass(frozen=True)
class Mount:
    """Tilt mount. Yoke on the body's heat-set inserts (flat bottom plane, low (-y) side, clear of the motor
    can and the exit funnel), M10 pivot axis parallel to x below the plane, tube clamp with a tongue between
    the yoke ears, a tilt link pinned to a fork on the yoke (A) and a fork on the clamp (B). The body tilts
    about the pivot, +y rises."""

    bolt_size: str = "M5"
    bolt_x: float = 25.0  # bolts at +-x
    bolt_y: tuple = (-55.0, -95.0)
    tube_shape: str = "round"  # "round" or "square" (owner: 25 mm tube)
    tube_d: float = 25.0  # round diameter or square side
    body_mass: float = 3.25  # kg at the plate top for the load checks: CAD estimate up to 2.84 (fill 0.8, 0.5 kg motor, unmodelled mass, 1 kg brass) plus 0.38 for the wall extender (the open arc weighs 0.22)
    unmodelled_mass: float = 0.15  # kg screws, inserts, sensor, cables, hose end, estimate, counted at the exit side
    tilt_range: tuple = (40.0, 60.0)  # deg from horizontal (owner), the adjustable link covers it
    tilt_margin: float = 2.0  # deg beyond the range that clearances still cover
    pivot_size: str = "M10"
    pivot_y: float = -38.0  # clears the gearbox half width (20) plus the ear radius
    pivot_depth: float = 60.0  # below the bottom plane, keeps the computed centre of mass on the low side of the pivot at every tilt (test_mount)
    yoke_t: float = 8.0
    ear_t: float = 8.0
    tongue_t: float = 22.0  # along the pivot axis. With `tongue_w` the stem holds `push` within `layer_limit`, torsion from a sideways push at the low rim governs (test_mount)
    tongue_w: float = 24.0  # stem and round end across the pivot axis, below the clamp bore so the stem does not bridge the slit
    pivot_nut_h: float = 10.0  # DIN 985 M10 height and across flats (https://www.pgb-europe.com/en-gb/172168/hexagon-selflocking-nut-din-985-m10-a2-25pc)
    pivot_nut_af: float = 17.0
    link_a: tuple = (-55.0, 40.0)  # pin A (y, z) in the body frame rel. the pivot, under the yoke on the low side
    link_b: tuple = (-32.0, -95.0)  # pin B (y, z) rel. the pivot with the tube vertical, on the clamp. About 1.1 mm of link per deg
    link_t: float = 14.0  # link and rod end thickness along the pins, a wall over the captive nut pocket
    link_wall: float = 4.0  # adjust end wall between its two nuts
    link_pin_size: str = "M6"  # ISO 4762 pins, ISO 7089 washers, DIN 985 nuts
    link_nut_h: float = 6.0  # DIN 985 M6 height and across flats (https://www.fasteners.eu/standards/DIN/985/), unverified
    link_nut_af: float = 10.0
    link_rod_size: str = "M6"  # DIN 976-1 threaded rod, ISO 4032 nuts
    fixed_tilts: tuple = (45.0, 50.0, 55.0)  # printed fixed links: 45 the start value, 50 and 55 steeper
    link: str | float = "adjustable"  # the assembled link: "adjustable" (rod ends and rod) or the angle of a printed fixed link from `fixed_tilts`, which then sets the assembly tilt
    clamp_size: str = "M5"
    clamp_wall: float = 6.0  # around the tube bore, also the closed top that stops the tube
    clamp_h: float = 40.0
    clamp_slit: float = 2.0
    clamp_screws: int = 2
    stress_area: dict = field(default_factory=lambda: {"M6": 20.1, "M10": 58.0})  # mm2, tensile stress area As, ISO 898-1
    bolt_yield: float = 640.0  # MPa, class 8.8 (ISO 898-1)
    bearing_limit: float = 10.0  # MPa on a printed hole wall, unverified, tune on hardware
    push: float = 50.0  # N, a hand push at the bowl rim top, sideways or toward the tube, estimate
    layer_limit: float = 10.0  # MPa bending stress across printed layers, unverified, tune on hardware


@dataclass(frozen=True)
class Track:
    """Deck that the case bases slide on, band round the plate (both part of the core), gate over the exit."""

    gap: float = 0.3  # plate bottom above the deck with the ring cone at full clearance (`layout.seat_drop`)
    band_t: float = 3.5  # band ring on the deck round the plate: closes the plate notches, cases never touch the wall seams. Thick enough that the exit opening and its wall fit under it
    band_above: float = 3.5  # band top above an upright case on the deck
    gate_setback: float = 0.5  # gate face behind the band face, more than the 2 fits of band and gate against the wall
    gate_chamfer: float = 1.0  # 45 deg lead-in on the band ends at the gate, either rotation direction
    gate_lap: float = 6.0  # band ends lap behind the gate ends, so the gate cannot move inward


@dataclass(frozen=True)
class Exit:
    """Drop opening in a replaceable insert at the top of the track: the case head drops first into an
    angled funnel and stays base-down. The insert's ledge in the deck recess locates it, the gate and the plate
    above keep it down, so it needs no screws."""

    open_ratio: float = 1.8  # opening length along travel over case length, longer lets the plate turn faster
    inner_margin: float = 3.0  # opening reaches this far inside the pocket
    outer_margin: float = 0.6  # leaves min_wall at the opening's outer corners inside the bowl radius
    bore_clearance: float = 0.6  # funnel outlet and tube bore over the rim diameter
    lean: float = 30.0  # deg from the shaft axis toward the bowl centre, 15 deg off vertical at 45 deg tilt
    funnel_len: float = 33.0  # below the deck, along the lean: puts the drop tube socket under the body bottom
    end_margin: float = 8.0  # insert beyond the opening at each end
    seat_t: float = 2.0  # the insert's ledge sits this deep in a deck recess round the shaft
    seat_w: float = 3.0  # ledge width round the shaft, the insert rests on it
    wall: float = 2.4
    spigot_len: float = 15.0  # straight outlet the drop tube slides over, same bore, so the path has no step


@dataclass(frozen=True)
class PlateSeat:
    """Interface between the clutch and every collator plate. Fixed for all plates.
    The plate drops onto the drive ring's flange over its hex, the cap twists on above it."""

    drive_af: float = 62.0  # ring hex across flats: drives and centres the plate, over the thread diameter
    hub_h: float = 6.0  # plate thickness at the hub, from the flange to the cap face
    lead_in: float = 1.0  # 45 deg chamfer on the ring hex top and the plate hole bottom
    cap_gap: float = 1.0  # radial gap around the cap in plates thicker than hub_h
    max_height: float = 25.0  # tallest plate the cap must still stand above


@dataclass(frozen=True)
class DriveRing:
    """Wear ring on the clutch cone that carries the plate and stays on the clutch when plates are changed.
    Female cone on the carrier cone (friction face 1), floor top under the pressure disc (friction face 2),
    tube around the disc, flat flange as the plate seat, hex drive, multi-start thread for the cap."""

    cone_d: float = 48.0  # female cone diameter at the ring bottom
    cone_half_angle: float = 45.0  # deg, above about 27 deg the cone cannot wedge at mu 0.5
    floor_h: float = 6.0  # cone height: the floor top, where the disc bears, above the ring bottom
    base_gap: float = 1.0  # ring bottom above the carrier base, so only the cone carries it
    flange_t: float = 2.0
    flange_d: float = 78.0  # beyond the hex corners, the plate bottom rests on it
    disc_gap: float = 1.0  # radial, tube bore around the pressure disc
    top_margin: float = 0.4  # hex top below the cap face, so the cap clamps the plate, over half the plate flatness
    thread_d: float = 58.0
    thread_pitch: float = 2.5  # between adjacent starts
    thread_starts: int = 3  # lead 7.5 mm, 4 starts (lead 10) drops the cap clamp force below the tipping test
    thread_angle: float = 90.0  # deg included, flanks 45 deg off horizontal: prints without supports both ways up
    thread_depth: float = 0.9  # radial, under half the pitch so crest and root keep a flat
    thread_len: float = 6.0  # 0.8 turn of the lead


@dataclass(frozen=True)
class Cap:
    """Printed cap on the drive ring thread: closed top over the knob, bottom face clamps the plate.
    Hand twist, no tool. Thread hand follows `case_plate.direction`, so brass drag tightens it."""

    d: float = 88.0
    top_t: float = 2.0
    knob_gap: float = 1.0  # above the knob top
    grip_count: int = 16  # scallops around the rim
    grip_d: float = 6.0
    hand_torque: float = 1.0  # Nm, hand-tight twist, estimate, unverified
    mu: float = 0.5  # thread and face friction, high estimate: least clamp force per torque


@dataclass(frozen=True)
class Spring:
    """Compression spring between knob and pressure disc: Gutekunst VD-127E-01, stainless 1.4310
    (https://www.federnshop.com/de/produkte/druckfedern/vd-127e-01.html)."""

    od: float = 8.00
    bore_d: float = 8.8  # smallest bore the catalogue allows (Dh)
    free_length: float = 12.8
    solid_length: float = 5.02
    rate: float = 2.743  # N/mm
    max_force: float = 21.34  # Fn


@dataclass(frozen=True)
class MetalHub:
    """Pololu 2693 aluminium mounting hub for 8 mm shafts, M3 holes
    (https://www.pololu.com/file/0J1331/pololu-universal-aluminum-mounting-hub-for-8mm-shaft-m3-holes-dimensions.pdf).
    The boss points down to the motor, the carrier sits on the flange."""

    flange_d: float = 25.4
    flange_t: float = 5.0
    boss_d: float = 14.0
    boss_h: float = 4.2
    bore_d: float = 8.0
    hole_pcd: float = 19.05
    hole_count: int = 6
    hole_size: str = "M3"
    threaded: bool = True  # tapped holes. False: clearance holes and an ISO 4032 nut under the flange
    screws: int = 3  # of the hub's holes, at the hex corners
    screw_length: float = 10.0  # ISO 4762


# Generic 8 mm aluminium flange coupling, about 0.73 EUR on AliExpress (listing 1005011663803929,
# drawing in the listing images, unverified, measure on delivery): 4 clearance holes, nuts under the flange.
GENERIC_8MM_FLANGE = MetalHub(
    flange_d=32.0, flange_t=3.0, boss_d=16.0, boss_h=10.0, bore_d=8.0, hole_pcd=24.0, hole_count=4,
    hole_size="M3", threaded=False, screws=2, screw_length=12.0,
)


@dataclass(frozen=True)
class PanelPart:
    """Bought panel part as an envelope in the panel frame: z = 0 on the outer face, +z into the box. Threaded
    barrel from the outer face to `thread_l`, panel nut on the inner face, body behind the barrel, front piece
    (lever, knob, flange) outside. Seller values, unverified: measure on delivery."""

    label: str
    thread_d: float  # nominal thread diameter, the barrel and the panel nut bore
    thread_l: float  # barrel length from the outer face: panel plus nut must fit on it
    nut_af: float
    nut_t: float
    body: tuple  # across x, across y, depth behind the barrel (the panel frame x and y)
    front: tuple = (0.0, 0.0)  # diameter and height outside the panel


@dataclass(frozen=True)
class Electronics:
    """The box beside the stand tube below the tilt clamp: upright, controls in the front
    lid toward the user (the low side), its own slit clamp on the tube (the tilt clamp's screws). Panel hole and module sizes
    from seller listings, unverified: measure on delivery."""

    box_gap: float = 10.0  # below the tilt clamp
    box_inner: tuple = (96.0, 54.0, 120.0)  # x across, y away from the tube, z along it: PWM board on its knob in the upper lid, timer relay on the back wall below, estimate
    box_wall: float = 2.4  # thin enough for the panel threads (6 mm and longer, unverified)
    lid_t: float = 3.0
    lid_screw_size: str = "M3"  # ISO 4762 through the lid into heat-set inserts in the box corners
    clamp_h: float = 40.0  # slit clamp on the tube in the box side wall, at the box top
    relay_holes: tuple = (64.0, 32.0)  # timer relay module (DROK 200391) mounting holes, x and z spacing: not in the seller sheet, estimate for a 71 x 39 board, unverified, measure on delivery
    relay_pcb_t: float = 1.6
    standoff_h: float = 8.0  # relay board above the back wall, room for its solder joints
    relay_hole_depth: float = 7.7  # insert hole in the standoff, 1 deeper than usual so the M3 x 8 does not bottom out
    front_holes: tuple = (("PWM knob", 7.2), ("toggle switch", 6.6), ("DC jack", 8.2))  # lid, top to bottom: pot M7, E-Switch 100SP1T1B1M1QEH 1/4-40 (hole 6.35 mm per DigiKey, plus print clearance), Switchcraft L722A .313 in hole (plus print clearance)
    side_holes: tuple = (("motor", 12.2), ("sensor", 12.2))  # +x face, low: GX12 2-pin (motor) and 3-pin (sensor), 12 mm (unverified). Different pin counts: the motor plug cannot go in the sensor socket
    # Envelopes of the panel parts by hole name. Toggle switch E-Switch 100SP1T1B1M1QEH: 1/4-40 bushing, actuator 10.41
    # long (https://www.digikey.com/en/products/detail/e-switch/100SP1T1B1M1QEH/378819), bushing length .240 in, 5 A
    # resistive at 28 V DC (https://configured-product-images.s3.amazonaws.com/Datasheets/100.pdf), body and nut size
    # estimated. Potentiometer: body 17 x 9.5 (https://www.piekarz.pl/en/10065-potentiometer-spike-wh148-1a-2-15v-b50k),
    # knob 15 mm shaft and 16 knob estimated. DC jack Switchcraft L722A: .313 in hole, panel up to .125 in, longer
    # bushing .319 in, 5 A at 12 V DC resistive (https://media.e-sonic.com/productfiles/mf-sc/plf6.pdf), body and nut size
    # estimated. GX12 and all other panel nuts: no drawing found, estimates, unverified. The jack barrel is the hole (8.2)
    # less the 0.2 clearance of the other holes. The GX12 body ends 12 behind the inner face of the panel, the depth
    # `test_panel_holes_leave_room` assumes.
    panel_parts: tuple = (
        ("PWM knob", PanelPart("PWM knob", 7.0, 7.0, 10.0, 2.0, (17.0, 17.0, 9.5), (16.0, 15.0))),
        ("toggle switch", PanelPart("toggle switch", 6.35, 6.1, 9.5, 2.0, (13.0, 7.9, 20.0), (3.0, 10.4))),
        ("DC jack", PanelPart("DC jack", 7.95, 8.1, 11.0, 2.0, (12.0, 11.0, 14.0))),
        ("motor", PanelPart("GX12 2-pin socket", 12.0, 8.5, 15.0, 2.0, (13.0, 13.0, 5.9), (16.0, 2.5))),
        ("sensor", PanelPart("GX12 3-pin socket", 12.0, 8.5, 15.0, 2.0, (13.0, 13.0, 5.9), (16.0, 2.5))),
    )
    pwm_board: tuple = (50.0, 50.0, 13.6)  # PWM controller (listing: 50 x 32 PCB, height unverified; kept at 50 x 50 for the knob and terminals): across x, along z (about 25 round its knob), depth with parts on the board (estimate, unverified)
    relay_board: tuple = (71.0, 39.0)  # timer relay module PCB over its holes: across x, along z (DROK 200391 sheet, 7.1 x 3.9 x 2.5 cm: https://m.media-amazon.com/images/I/91rcHqMUeoL.pdf)
    relay_parts: tuple = (56.0, 24.0, 23.4)  # display, relay and terminal blocks between the mounting screw heads: across x, along z, height above the PCB (25 mm module height less the PCB, estimate, unverified)


@dataclass(frozen=True)
class Clutch:
    floor_gap: float = 1.0  # running gap between the hub and the body floor
    shaft_tip_gap: float = 0.5  # bore depth beyond the shaft tip
    clamp_margin: float = 0.4  # male cone ends this far below the ring floor top
    carrier_base_t: float = 4.0  # carrier base on the metal hub, clamped by the hub screws
    gauge_grip: float = 15.0  # hub height gauge: handle top above the plate bottom (deck height), to grip it
    key_af: float = 20.0  # hex that keys the pressure disc
    key_h: float = 11.5  # above the ring floor top
    disc_d: float = 50.0
    disc_t: float = 6.5
    knob_d: float = 54.0  # the cap thread crest passes over it
    knob_t: float = 10.0
    knob_grip_count: int = 12  # scallops around the knob rim
    knob_grip_d: float = 6.0
    spring_pockets: int = 6
    springs_fitted: int = 6
    spring_pcd: float = 36.0
    spring_pocket_depth_disc: float = 1.5
    spring_pocket_depth_knob: float = 1.5
    knob_screw_size: str = "M5"
    knob_screw_length: float = 16.0  # ISO 4017
    friction_mu: tuple = (0.2, 0.5)  # PLA/PETG/ASA on the same, low and high estimate, unverified
    backstop_margin: float = 1.25  # metal-hub clutch slips only above this times the plate drag (the controller has no current limit, the clutch is the only torque limit)


@dataclass(frozen=True)
class DropTube:
    """Bayonet socket over the exit spigot (two lugs on the spigot, an L slot with a notch at the stop in the socket wall),
    straight section with a port for an M18x1 inductive tube-full sensor
    (LJ18A3-8-Z/AX, NPN NC, 8 mm rated), barb for a clear PVC hose. The bore only steps outward along the path.
    Sensor, nut and hose sizes are typical kit values, unverified, measure on delivery."""

    lug_h: float = 1.2  # radial height of a spigot lug, with a 45 deg underside that prints without support (print tolerance estimate, unverified: try it on a print)
    lug_tip: float = 1.2  # flat axial width of a lug behind its 45 deg underside
    lug_z: float = 4.0  # underside root of the lugs from the start of the spigot
    lug_w: tuple = (4.4, 3.0)  # tangential widths of the wide lug (sensor side) and the narrow lug (opposite), the wide one does not fit the narrow slot (strength estimate: 10 N on one lug is about 1.4 MPa, unverified)
    twist: float = 60.0  # deg from the entry slots to the stop, leaves a land over min_wall between slot and notch on the smallest spigot
    twist_dir: int = -1  # -1: the tube turns clockwise seen from the hose end to lock, like a right-hand thread (+1 the other way)
    lock_lift: float = 1.0  # the tube hangs this far below its groove floor, in a notch at the stop: lift it out of the notch to turn it off
    sensor_thread: str = "M18 x 1"
    sensor_thread_d: float = 18.0  # M18x1 sensor body, unverified, measure on delivery
    sensor_length: float = 65.0  # LJ18A3-8-Z/BX listing 6.5 cm, the -Z/AX listing says 70 (https://market.samm.com/en/lj18a3-8-z-bx-inductive-proximity-sensor-en, https://www.phippselectronics.com/product/inductive-proximity-npn-sensor-lj18a3-8-z-ax/), unverified, measure on delivery
    sensor_hole_d: float = 19.0  # ISO 273 fine series clearance for M18
    nut_af: float = 24.0  # M18x1 lock nut across flats, unverified, measure on delivery
    nut_t: float = 4.0  # lock nut thickness, unverified, measure on delivery
    window_t: float = 1.0  # printed wall between the sensor face and the bore
    sensor_margin: float = 10.0  # sensor axis above the outlet end by one case length plus this
    boss_wall: float = 3.2  # legs beside the nut slot
    plate_t: float = 4.0  # printed plate between the two lock nuts
    hose_id: float = 14.0  # clear PVC hose 14 x 18 mm, unverified, owner buys, a 9mm case (21.6 diagonal) cannot turn in it
    hose_od: float = 18.0
    barb_grip: float = 0.8  # barb diameter over the hose inner diameter
    barb_ridge_h: float = 0.4  # radial, 45 deg back face prints without support
    barb_ridge_pitch: float = 5.0
    barb_ridges: int = 2
    barb_len: float = 18.0


@dataclass(frozen=True)
class Sim:
    """MuJoCo model of brass on the plate (`sim/`). Case values are estimates, unverified: fit them to hardware
    runs with `python -m sim calibrate`. Friction is `case_plate.drag_mu` for every contact."""

    case_mass: float = 0.004  # kg, fired 9mm Luger brass, estimate
    com_ratio: float = 0.36  # centre of mass height over case length from the base, estimate (the plate height assumes 0.33 to 0.39)
    timestep: float = 0.002  # s, contact time constant 2.5 steps
    iterations: int = 20  # PGS solver: Newton's dense solve was 20x slower on a 250 case pile
    hull_threshold: float = 0.01  # CoACD concavity of the plate inside the pocket ring: 93 hulls, up to 0.8 mm into the air
    pocket_hull_threshold: float = 0.03  # same for one pocket pitch of the ring (relative to its size): 14 hulls, up to 0.26 mm
    warmup_revs: float = 1.0  # plate turns before counting, the pile settles into its running shape
    segments: int = 180  # deck, band, gate and wall boxes round the bowl


@dataclass(frozen=True)
class Config:
    print: Print = Print()
    fasteners: Fasteners = Fasteners()
    printer: Printer = Printer()
    calibers: Calibers = Calibers()
    motor: Motor = Motor()
    case_plate: CasePlate = CasePlate()
    body: Body = Body()
    track: Track = Track()
    exit: Exit = Exit()
    mount: Mount = Mount()
    plate_seat: PlateSeat = PlateSeat()
    drive_ring: DriveRing = DriveRing()
    cap: Cap = Cap()
    spring: Spring = Spring()
    metal_hub: MetalHub = MetalHub()
    electronics: Electronics = Electronics()
    clutch: Clutch = Clutch()
    drop_tube: DropTube = DropTube()
    sim: Sim = Sim()


CFG = Config()
