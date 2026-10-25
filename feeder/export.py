"""Assembly exports: one STEP with a labelled part tree (FreeCAD, Fusion), one 3MF with every part placed, and an
offline viewer page (feeder/viewer.html with the models inlined)."""

import base64
import json
import math
import tempfile
import urllib.request
from pathlib import Path

from build123d import Color, Compound, Mesher, export_step, export_stl

from feeder import assembly
from feeder.config import CFG, Config  # noqa: F401
from feeder.parts import case_plate, layout, mount
from feeder.parts import slip_clutch as sc

THREE = [  # three.js r128, the version the viewer is written for
    "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js",
    "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/STLLoader.js",
    "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js",
]
COLORS = {  # STEP and 3MF colours by viewer kind, RGB 0..1
    "motor": (0.29, 0.32, 0.35), "steel": (0.49, 0.52, 0.55), "body": (0.56, 0.6, 0.59), "wall": (0.56, 0.6, 0.59),
    "extender": (0.56, 0.6, 0.59), "gate": (0.66, 0.55, 0.88), "exit": (0.75, 0.28, 0.45), "alu": (0.77, 0.79, 0.82), "tool": (0.9, 0.77, 0.23),
    "pla": (0.16, 0.54, 0.49), "ring": (0.48, 0.37, 0.66), "plate": (0.85, 0.79, 0.64), "pla2": (0.75, 0.38, 0.25),
    "pla3": (0.29, 0.37, 0.56), "cap": (0.18, 0.44, 0.62), "drop": (0.25, 0.6, 0.42), "yoke": (0.66, 0.34, 0.29),
    "clamp": (0.36, 0.44, 0.69), "link": (0.79, 0.64, 0.15), "tube": (0.65, 0.68, 0.71), "screw": (0.2, 0.22, 0.24),
    "nut": (0.42, 0.45, 0.48), "washer": (0.62, 0.65, 0.68), "insert": (0.72, 0.58, 0.3), "elec": (0.3, 0.33, 0.38),
    "lid": (0.45, 0.5, 0.56), "panel": (0.12, 0.13, 0.15), "board": (0.1, 0.45, 0.25), "sensor": (0.75, 0.62, 0.2),
}


def _steps(cfg: Config) -> list[tuple[str, str]]:
    """Assembly steps by `Placed.step`, text for the viewer."""
    mt, n = cfg.mount, cfg.clutch.springs_fitted
    split = cfg.body.split
    body_step = {
        "arcs": ("Body core on the motor", "Heat-set inserts into the bottom plane and the skirt first. Countersunk screws from inside the cup, through the floor into the gearbox face."),
        "halves": ("Body halves on the motor", "Heat-set inserts into the bottom plane and the seam posts of half 1 first. Set both halves on the gearbox face, screw them together across each seam post, then the countersunk screws from inside the cup into the gearbox."),
        "one_piece": ("Body on the motor", "Heat-set inserts into the bottom plane first. Countersunk screws from inside the cup, through the floor into the gearbox face."),
    }[split]
    spring_len = sc.spring_working_length(cfg)
    return [
        ("Motor", "Worm gear motor 5840-31ZY with its boss and 8 mm D shaft, drawn as an envelope."),
        body_step,
        ("Wall arcs", f"{cfg.body.wall_segments} arcs, screwed through their key ribs into the core's inserts. Key ribs slot into the skirt grooves, lap joints at the seams."),
        ("Exit insert and gate", "Exit insert from above into its shaft, its ledge in the deck recess: drop opening, funnel and spigot. Gate into the band gap, its ends behind the band ends. To swap the insert: cap, plate and gate off, drop tube twisted off the spigot, lift it out."),
        ("Metal hub with the hub gauge", "Lay the gauge on the cup floor around the shaft, handle away from the set screws. Push the Pololu 2693 hub down onto it, tighten its 2 set screws on the D flat, slide the gauge out by its handle away from the shaft and lift it out."),
        ("Carrier on the hub flange", "Heat-set insert into the carrier top first. Screws into every other hub hole."),
        ("Drive ring", "Onto the carrier cone. It stays on the clutch when plates change."),
        (f"Pressure disc and {n} springs", f"Disc keyed to the carrier hex, bearing on the ring floor inside the ring. Gutekunst VD-127E-01 springs in the disc pockets, free length {cfg.spring.free_length} mm."),
        ("Knob and its screw", f"Tighten once at assembly until the knob sits on the carrier top: springs at {spring_len:.1f} mm, clamp {sc.clamp_force(n, cfg):.1f} N. Plate changes never touch it."),
        ("Case plate", f"{layout.plate_r(cfg) * 2:.1f} mm, {layout.pocket_count(cfg)} notches, closed by the band. Drops over the ring hex onto the flange; lift it by the key ring."),
        ("Cap", f"Twist on by hand until it sits on the plate: about {sc.cap_clamp_force(cfg):.0f} N clamp at 1 Nm (estimate) holds the plate against the brass on the low side. Twist off to change plates."),
        ("Drop tube", f"Inner M18 x 1 lock nut into the slot from the side first. No screw: hold the socket {cfg.drop_tube.twist:.0f} deg counterclockwise (seen from below) of its final position, push it up over the exit spigot until the lugs reach the groove, then turn it clockwise until it stops and drops into the notch, sensor window square. To take it off, lift it out of the notch, turn it back and pull."),
        ("Drop tube chain (optional)", f"Spacer ({cfg.drop_chain.spacer_len:.0f} mm) and angled piece ({cfg.drop_chain.angle:.0f} deg) go on the male end of the part before them the way the drop tube goes on the exit spigot: hold the socket {cfg.drop_tube.twist:.0f} deg counterclockwise (seen from below) of its final position, push it up over the lugs, turn it clockwise until it stops and drops into the notch. They keep the sensor side of the drop tube on +x."),
        ("Hose adapter", "Same bayonet on the last male end. Push the clear hose over its barb."),
        ("Yoke", "Screws from below into the heat-set inserts in the body's bottom plane."),
        ("Clamp on the 25 mm tube", "Slit clamp: screws on washers in the counterbores, nuts in the pockets. Tongue between the yoke ears on the pivot bolt, a washer on each side, the nylon nut sets the pivot friction."),
        ("Tilt link", f"Pin A in the yoke fork, pin B in the clamp fork, a washer on each side and a nylon nut each. Adjustable link: fixed rod end on a captive M6 nut and a jam nut, adjust end between two nuts on a {mount.rod_length(cfg):.0f} mm M6 threaded rod, {mt.tilt_range[0]:.0f} to {mt.tilt_range[1]:.0f} deg. Or one printed fixed link per angle ({', '.join(f'{t:.0f}' for t in mt.fixed_tilts)} deg) on the same pins."),
        ("Wall extender (optional)", f"One open arc of {cfg.body.extender_arc:.0f} deg over the low side, {cfg.body.extender_h:.0f} mm more wall, top at the wall slant. The sleeve slides {cfg.body.extender_lap:.0f} mm down over the outside of the wall top. A nut into each rib pocket first, then countersunk screws from inside the bowl through wall and sleeve into the rib nuts. The high side stays open."),
        ("Electronics box", f"Heat-set inserts into the corner posts and the relay standoffs first. The box clamps the stand tube {cfg.electronics.box_gap:.0f} mm below the tilt clamp, beside it with its front toward the user: right or left of the tube, the left box is the mirror image. Screws on washers in the counterbores from the outside, nuts in the pockets from the gap at the wall. Timer relay module onto its standoffs, screws into the inserts. GX12 sockets into the side face, each with its panel nut inside. Fuse holder into its cradle on the back wall and the two splice connectors into theirs, a cable tie through the tunnel under each. Tie the wires of each socket to the pad behind it and leave a loop of about {cfg.electronics.service_loop:.0f} mm free behind the socket."),
        ("Lid with the controls", "PWM knob, toggle switch and DC jack into the lid from the front, each with its panel nut on the inside. The text engraved in the lid is the pin map of the plugs and the polarity of the jack. The PWM controller hangs on the back of the knob potentiometer. Lid on the box, screws from the front. The cables are long enough to open it."),
        ("Level sensor", "Sensor from the outside through the plate hole and the inner lock nut until its face touches the window wall, outer lock nut on the plate. Plug it into the GX12 3-pin socket."),
    ]


def _matrix(loc) -> list[float]:
    """Location as a column-major 4x4 matrix (three.js Matrix4.fromArray)."""
    t = loc.wrapped.Transformation()
    rows = [[t.Value(r, c) for c in range(1, 5)] for r in range(1, 4)] + [[0.0, 0.0, 0.0, 1.0]]
    return [round(rows[r][c], 5) for c in range(4) for r in range(4)]


def _fastener_text(fs: list, step_of: dict) -> dict:
    """'n x name' per viewer step, in assembly order."""
    out: dict = {}
    for f in sorted(fs, key=lambda f: f.seq):
        counts = out.setdefault(step_of[f.host], {})
        counts[f.name] = counts.get(f.name, 0) + len(f.at)
    return {s: [f"{n} x {name}" for name, n in c.items()] for s, c in out.items()}


def _libs(cache: Path) -> str:
    """three.js inlined from a local cache (filled on the first run), so the page works offline. Without network
    and cache the page loads them from the CDN."""
    cache.mkdir(parents=True, exist_ok=True)
    tags = []
    for url in THREE:
        f = cache / url.rsplit("/", 1)[1]
        if not f.exists():
            try:
                f.write_bytes(urllib.request.urlopen(url, timeout=30).read())
            except OSError:
                tags.append(f'<script src="{url}"></script>')
                continue
        tags.append("<script>\n" + f.read_text(encoding="utf-8").replace("</script", "<\\/script") + "\n</script>")
    return "\n".join(tags)


def export_assembly(cfg: Config, out: Path, title: str, inline_libs: bool = True) -> list[Path]:
    """Write feeder.step, feeder.3mf and viewer.html for `cfg` to `out`. `inline_libs` False: the page loads
    three.js from the CDN."""
    out.mkdir(parents=True, exist_ok=True)
    tilt = assembly.body_tilt(cfg)
    placed, fs = assembly.placed(cfg, tilt), assembly.fasteners_in_body(cfg, tilt)
    solids = []
    for p in placed:
        if not p.tool:
            p.shape.label, p.shape.color = p.name, Color(*COLORS[p.kind])
            solids.append(p.shape)
    for f in fs:
        for loc in f.at:
            s = loc * f.shape
            s.label, s.color = f.name, Color(*COLORS[f.kind])
            solids.append(s)
    export_step(Compound(label=title, children=solids), out / "feeder.step")
    mesher = Mesher()
    for s in solids:
        mesher.add_shape(s, linear_deflection=0.05, angular_deflection=0.3, part_number=s.label)
    mesher.write(out / "feeder.3mf")

    # viewer: steps that have parts, renumbered
    steps = _steps(cfg)
    used = sorted({p.step for p in placed})
    index = {s: i for i, s in enumerate(used)}
    step_of = {p.name: index[p.step] for p in placed}
    names = [p.name for p in placed]
    models, parts, fasteners = {}, [], []

    def stl(key: str, shape) -> None:
        f = Path(tmp) / f"{key}.stl"
        export_stl(shape, str(f), tolerance=0.05, angular_tolerance=0.3)
        models[key] = base64.b64encode(f.read_bytes()).decode()

    with tempfile.TemporaryDirectory() as tmp:
        for p in placed:
            stl(p.name, p.shape)
            parts.append(dict(name=p.name, kind=p.kind, step=index[p.step], dir=list(p.explode), tool=p.tool))  # noqa: C408
        for i, f in enumerate(fs):  # one mesh per group, instanced along its locations
            stl(f"fastener_{i}", f.shape)
            fasteners.append(dict(model=f"fastener_{i}", kind=f.kind, host=names.index(f.host), seq=f.seq,  # noqa: C408
                                  lift=round(f.shape.bounding_box().size.Z + 10, 1), m=[_matrix(loc) for loc in f.at]))
    ftext = _fastener_text(fs, step_of)
    pc = layout.pocket_circle_r(cfg)
    ang = [a for a in case_plate.pocket_angles(cfg) if abs((a - 270 + 180) % 360 - 180) <= 80][::2]
    z, zc, n = layout.levels(cfg), sc.levels(cfg), cfg.clutch.springs_fitted
    info = dict(  # noqa: C408
        eyebrow=f"Feeder · 9mm case feeder · body {cfg.body.split.replace('_', ' ')}",
        intro=f"{title}. Tilted view: as mounted, tube vertical.",
        labels={"body": {"arcs": "Body core", "halves": "Body halves", "one_piece": "Body"}[cfg.body.split]},
        steps=[dict(t=steps[s][0], d=steps[s][1], f=ftext.get(index[s], [])) for s in used],  # noqa: C408
        spring_step=step_of["slip_clutch_disc"], case_step=step_of[f"case_plate_{cfg.case_plate.caliber}"],
        parts=parts, fasteners=fasteners, tilt=tilt, tilt_range=list(cfg.mount.tilt_range), pivot=list(mount.pivot_point(cfg)),
        tube_axis=list(assembly.pivot_axis(tilt, cfg)),
        cases=dict(rim_d=layout.caliber(cfg).rim_d, length=layout.caliber(cfg).case_length, z0=z.deck_top, r=pc,  # noqa: C408
                   xy=[[pc * math.cos(math.radians(a)), pc * math.sin(math.radians(a))] for a in ang]),
        springs=dict(count=n, pcd=cfg.clutch.spring_pcd, od=cfg.spring.od, free=cfg.spring.free_length, rate=cfg.spring.rate,  # noqa: C408
                     working=sc.spring_working_length(cfg), bottom=zc.ring_floor + cfg.clutch.disc_t - cfg.clutch.spring_pocket_depth_disc - zc.floor_top),
        slip=[round(sc.slip_torque(n, mu, cfg), 2) for mu in cfg.clutch.friction_mu], clamp=round(sc.clamp_force(n, cfg), 1),
        plate_d=round(layout.plate_r(cfg) * 2, 1), pockets=layout.pocket_count(cfg), drag=round(layout.plate_drag_torque(cfg), 2),
        cap_n=round(sc.cap_clamp_force(cfg), 1),
    )
    data = f"<script>\nwindow.FEEDER_INFO = {json.dumps(info)};\nwindow.FEEDER_MODELS = {json.dumps(models)};\n</script>"
    page = (Path(__file__).parent / "viewer.html").read_text(encoding="utf-8")
    page = page.replace("<!-- LIBS -->", _libs(out.parent / ".three") if inline_libs else "\n".join(f'<script src="{u}"></script>' for u in THREE)).replace("<!-- DATA -->", data)
    (out / "viewer.html").write_text(page, encoding="utf-8")
    return [out / "feeder.step", out / "feeder.3mf", out / "viewer.html"]
