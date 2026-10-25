# Feeder

Parametric brass and bullet collator for reloading, built in [build123d](https://github.com/gumyr/build123d) with metric DIN/ISO hardware. Every part is generated from `feeder/config.py` and exported as STL and STEP.

Status: early development. Parts are UNTESTED until printed.

## Setup

Requirements: [Dev Container CLI](https://github.com/devcontainers/cli) and podman (or Docker without `--docker-path podman`).

```
devcontainer up --docker-path podman --workspace-folder .
```

## Build and test

Run in the container (prefix `devcontainer exec --docker-path podman --workspace-folder .`):

| Command | Result |
|---|---|
| `.venv/bin/python build.py` | builds every part into `build/<name>.stl` and `.step`, then runs the tests |
| `.venv/bin/python build.py --no-test` | builds only |
| `.venv/bin/python build.py --assembly` | also `build/assembly/`: `feeder.step` (part tree), `feeder.3mf` and `viewer.html` (3D assembly steps with every fastener) |
| `.venv/bin/python build.py --variants` | also `build/variants/<split>/` for each `body.split`: body parts and plate, with an `assembly/` folder |
| `.venv/bin/python build.py --plates` | also `build/plates/<set>/` for each plate set: plate, exit insert and drop tube |
| `.venv/bin/python build.py --configurator` | also `build/configurator/`: the print files of every option combination (body split, plate set, extender, tilt link, tube shape, hub) as `<hash>.stl`, identical parts stored once, and `manifest.json` with the part files and BOM rows per choice |
| `.venv/bin/python -m pytest -q` | tests only. `-n 4 --dist loadfile` runs the test files on 4 cores |

## Build guide site

The build guide is a MkDocs site with the [BuildGuide](https://github.com/OpenReloading/BuildGuide) plugin (`mkdocs.yml`, pages in `guide/`): introduction and BOM checklist from `feeder/guide.py`, the assembly viewer, tilt and capacity from this README. Nothing generated is committed. In the container:

```
.venv/bin/pip install -r requirements-guide.txt
.venv/bin/python build.py --no-test --guide   # build/guide/buildguide.json, guide/generated/assembly/
.venv/bin/mkdocs build --strict               # site/
```

`.github/workflows/pages.yml` runs the tests, builds the guide and deploys `site/` to GitHub Pages on every push to `main` (pull requests build only).

The configurator page (`guide/configurator.md`, `guide/javascripts/configurator.js`) picks the options, lists the parts and the BOM for the choice and zips the print files in the browser. It reads `build/configurator/` through `hooks/configurator_files.py`: run `build.py --no-test --configurator` before `mkdocs build` to see it locally. A push to `main` builds those files in CI; other builds and local builds without them show a notice instead.

`build/<name>.stl` and `.step` are in the modelled orientation (assembly frame for the body). `build/print/<name>.stl` is each part as it goes on the bed (`feeder/printing.py`): flipped where it prints upside down, turned across the bed diagonal where it is wider than the bed.

## Configuration

All dimensions and options are in `feeder/config.py` (frozen dataclasses, instance `CFG`). Fastener head sizes, nominal lengths and ISO 273 clearances come from bd_warehouse.

| Section | Contents |
|---|---|
| `print` | sliding fit gap, minimum wall, longest bridge, PLA density and fill (for the mount balance) |
| `fasteners` | heat-set insert holes (CNC Kitchen), thread pitches, head fit, minimum thread engagement |
| `printer` | bed size and edge margin. The plate and band diameter follow from the bed |
| `calibers` | rim diameter, minimum rim thickness and case length per caliber (C.I.P. TDCC) |
| `motor` | 5840-31ZY output shaft, boss, mounting screws, gearbox and can envelope, direction of the can, mass range |
| `case_plate` | caliber or caliber group, notches or holes, pocket clearance and pitch, plate height over case length, chamfers, pickup channels, ribs or ridges (`ribs`), pull eye, design fill, item and orientation (`item`, `orient`) with the tilt of each (`tilts`), rotation direction (the cap thread hand follows it and the wiring has one motor polarity: set it here and print the matching plate and cap, do not swap the motor leads), drag estimate |
| `body` | split (`arcs`, `halves`, `one_piece`), floor, wall height, deck, cup, ribs, skirt, wall joint screws and keys, seam post screws, wall extender, motor can tunnel |
| `track` | gap from plate to deck, band ring, gate setback, chamfer and lap |
| `exit` | drop opening length over case length, funnel lean and length, bore clearance, spigot, ledge in the deck recess |
| `plate_seat` | interface of every collator plate: hex drive, plate thickness at the hub, lead-in, cap recess gap, tallest plate |
| `drive_ring` | wear ring on the clutch cone: cone, floor, flange, disc gap, cap thread (3 starts, 45 deg flanks) |
| `cap` | twist cap: diameter, top, knob gap, grips, hand torque and friction estimates |
| `spring` | clutch spring (Gutekunst VD-127E-01) |
| `metal_hub` | Pololu 2693 aluminium hub (default) or `GENERIC_8MM_FLANGE`, an 8 mm flange coupling with nuts under the flange (unverified) |
| `electronics` | electronics box: gap below the clamp, inner size, wall, clamp, lid screws, relay holes and standoffs, panel hole sizes, envelopes of the panel parts and modules (unverified) |
| `clutch` | slip clutch geometry, height gauge, screws, friction and torque limits |
| `drop_tube` | bayonet (lug size, twist, notch lift), M18x1 sensor (length, thread), lock nut and window sizes, hose sizes and barb |
| `drop_chain` | optional chain parts (`parts`), spacer length, bend angle and leg length of the angled piece |
| `mount` | tilt mount: body inserts, tube (round or square, 25 mm), tilt range 40 to 60 deg, M10 pivot, tilt link pins and rod, fixed link angles, body mass and load limits, unmodelled mass |

## Parts

Full hardware list for the default 9mm case feeder: `bom/case_feeder_9mm.md`.

| Part | Hardware |
|---|---|
| `slip_clutch_carrier_metal_hub` | Pololu 2693 hub with its 2 M3 set screws, 3 x ISO 4762 M3 x 10, CNC Kitchen M5 x 9.5 insert. `GENERIC_8MM_FLANGE`: 2 x ISO 4762 M3 x 12 with ISO 4032 M3 nuts |
| `slip_clutch_hub_gauge` | none. Fork as thick as the floor gap under the hub boss, with a handle up past the deck: lay it on the cup floor around the shaft, push the hub down onto it, tighten the hub set screws, slide it out by the handle (away from the shaft, about 21 mm) and lift it out. The plate then sits at its design height above the track. Prints fork down |
| `slip_clutch_drive_ring` | none. Sits on the clutch cone with disc, springs and knob inside and stays there when plates are changed. Reprint it when the cone or floor wears. Prints flange down |
| `slip_clutch_cap` | none. Twists onto the ring thread by hand (right-hand for the default counter-clockwise plate) and clamps the plate. Prints top down |
| `slip_clutch_disc` | 6 Gutekunst VD-127E-01 springs |
| `slip_clutch_knob` | ISO 4017 M5 x 16 |
| `case_plate_9mm_luger` | 25 mm split key ring. 240.2 mm, 34 notches open to the rim, 7.09 mm high on a 256 mm bed. The band closes each notch, so the pocket is rim + 3 mm measured to the band. A shallow pickup channel (1.5 mm deep at the pocket, 25 mm long) leads into each pocket, 6 half-round radial ribs stir the pile (`case_plate.ribs` `per_pocket`: a ridge between every two pockets instead), the ring in the eye beside the cap lifts the plate. Drops over the ring hex onto its flange, 6 mm thick at the hub, cap recess above. `case_plate.notches` False: closed round holes for an A/B test |
| `body_core` | 4 x ISO 10642 M4 x 10 (motor, from inside the cup), 9 x CNC Kitchen M3 x 5.7 inserts (wall joints), 4 x CNC Kitchen M5 x 9.5 inserts (mount). Deck and band in one piece: the band is a C ring on the deck round the plate, 3.5 mm thick, up to the longest case plus 3.5 mm above the deck. It closes the plate notches, so cases slide on it and on the deck, never on the wall seams. Its gap over the exit takes the gate. Prints bottom down |
| `body_wall_0` to `body_wall_2` | 3 x ISO 4762 M3 x 12 each, into the core inserts. Lap joints at the seams, key ribs in the core skirt. The wall top is full height (125 mm above the plate bottom, `body.wall_h`) on the low side and falls at 40 deg toward the high side, not below one case length above the plate (`body.heap_angle`, `body.wall_slant`): brass lies level in the world, so at 40 deg tilt, the flattest, it stays below that line and the high side is open down to one case length above the plate |
| `body_extender` | none. Optional, 60 mm more wall (`body.extender_h`, 0 for none) over a 150 deg arc centred on the low side (`body.extender_arc`), flat top at the wall slant, the high side stays open. The sleeve slides 15 mm down over the outside of the wall top. 4 x ISO 10642 M3 x 12 from inside the bowl, head flush in the wall, through wall and sleeve into ISO 4032 M3 nuts captive in ribs outside the sleeve. Prints on its flat top, turned on the bed to fit |
| `body_track_gate` | none. Band sector in the band gap, on the exit insert. Its face is 0.5 mm behind the band face, the band ends have a 1 mm 45 deg lead-in, so cases pass the seams in either direction. The band ends lap 6 mm behind its ends, so it lifts out but cannot move inward. Prints top down |
| `body_exit_insert` | none. Wear part: drop opening, funnel (30 deg lean toward the bowl centre) and spigot with the 2 bayonet lugs of the drop tube in a block that fills a vertical shaft through the core, so it drops in from above. Its 3 mm ledge rests in a 2 mm deck recess round the shaft, the gate and the plate keep it down. Prints top down |
| `body_exit_insert_blank` | none. Optional: closes the exit, the insert's block and ledge with no opening, funnel or spigot (a second exit position, if one is ever added, not in the default assembly). Prints top down |
| `drop_tube` | Bayonet socket over the exit spigot, no screw: two lugs on the spigot (wide on the sensor side, narrow opposite) enter slots from the mouth, turn 60 deg along a groove and drop 1 mm into a notch at the stop (clockwise seen from below). Window, nut slot and plate for an M18x1 inductive sensor (LJ18A3-8-Z/AX default) with 2 M18x1 lock nuts (24 AF x 4, unverified, measure on delivery); the assembly draws the sensor (65 mm, unverified) between them. The lower end is the exit spigot's form (male, `drop_tube.male`): the next part chains on it. The bore only steps outward along the path. Prints socket down, no supports (brim advised). No spring outlet |
| `drop_hose_adapter` | none. Ends the chain: the same socket and bayonet as the drop tube, barb for a clear PVC hose, 14 mm ID x 18 mm OD (unverified), the tube bore through it. Prints socket down, no supports |
| `drop_spacer` | none. Optional: socket, 30 mm of straight tube (`drop_chain.spacer_len`) and the male form, the bore of the drop tube |
| `drop_angled` | none. Optional: socket, a 30 deg bend sideways to the lugs, away from the body (`drop_chain.angle`), 25 mm legs (`drop_chain.leg_len`) and the male form. Prints socket down, the lugs still print without supports at the bend |
| `electronics_box`, `electronics_box_left`, `electronics_lid` | Upright box beside the stand tube, 10 mm below the tilt clamp, its front with the controls toward the user and clear of the drop path: right of the tube, or left as the mirror image, 96 x 54 x 120 mm inside (wide x deep x tall). Its own slit clamp holds the tube (2 x ISO 4762 M5 x 35 on ISO 7089 washers into ISO 4032 nuts) and stands off the side wall, joined to it by a web in front of the screws. DROK timer relay module on 4 standoffs on the back wall. PWM knob, toggle switch and DC jack in a column in the lid, GX12 motor (2-pin) and sensor (3-pin) sockets one above the other low in the side face, in front of the relay because their bodies and solder cups reach 30 mm into the box (unverified), each with a free run of 30 mm behind it for a service loop and a tie pad on the wall for its wires. A cradle for the fuse holder and two for the splice connectors stand on the back wall, open toward the lid, each with a cable-tie tunnel (3.5 x 1.5 mm) under it. The lid has the pin map engraved in its outer face, read from the wiring data: right of the column SPEED, POWER and 12V IN with TIP +, left of it SENSOR 1 BN, 2 BU, 3 BK and MOTOR 1 +, 2 -. Box and lid have a 1.5 mm chamfer on the outside edges. The assembly shows the bought electronics as envelopes with their nuts, no wires: M18 sensor with 2 lock nuts, relay and PWM controller modules, switch, jack, knob and both GX12 sockets with a panel nut each; their sizes are seller values, unverified. The lid comes off forward: 4 x ISO 4762 M3 x 8 into CNC Kitchen M3 x 5.7 inserts in the corner posts. Panel hole sizes and relay hole spacing are seller values, unverified. The box prints on its back wall, the lid flat |

Body splits (`body.split`), each fits a 256 mm bed:

| Split | Parts | Plate | Joint |
|---|---|---|---|
| `arcs` (default) | `body_core` and 3 `body_wall_*` | 240.2 mm, 34 pockets | 9 x M3 x 12 into core inserts, lap joints |
| `halves` | `body_half_0`, `body_half_1`, cut through the shaft at 35 deg (`body.halves_seam`), clear of the exit, the motor screws, the mount inserts and the motor can tunnel | 240.2 mm, 34 pockets | per seam a post outside the wall with 3 x M3 x 12 into CNC Kitchen M3 x 5.7 inserts (6 of each), 3 motor screws hold half 0 and 1 holds half 1 to the gearbox. Each half prints across the bed diagonal |
| `one_piece` | `body` | 233.0 mm, 33 pockets | none |

Plates, gate and exit insert follow the bowl, so a `one_piece` body needs its own. With `halves` the motor and the clutch stay concentric only as well as the halves are screwed together: tighten the post screws with both halves flat on a table.

Slip torque with 6 springs: 0.84 to 2.10 Nm (estimate), the only torque limit for the gearbox. Plate drag under 250 cases: 0.24 Nm at 45 deg, 0.27 Nm at 38 deg (estimate, `layout.plate_drag_torque`).

The knob screw is tightened once at assembly, until the knob sits on the clutch. The spring length, and with it the slip torque, then never changes.

Plate change, no tools: twist the cap off, lift the plate off the ring hex, drop the next plate on, twist the cap on firmly by hand. It holds the plate down against the brass on the low side (`slip_clutch.cap_clamp_force`).

## Plate sets

One body and band take every plate: the exit shaft in the core holds any set's exit insert, the wall and band suit the longest case. A plate change for another caliber group swaps the plate, exit insert and drop tube (`build.py --plates`). No tools: twist the cap off, lift the plate and the gate out, twist the drop tube off the spigot, lift the insert out. Set `case_plate.caliber` to a group or to one case of `calibers.table` (C.I.P. sheet values, rimmed rim thickness from SAAMI). The exit opening is not adjustable: each plate set has its own exit insert, a slide would add a part and a lock for no gain.

| Set (`case_plate.caliber`) | Item | Orient | Cases | Plate height | Pocket | Pockets | 45 deg capacity | Drop bore |
|---|---|---|---|---|---|---|---|---|
| `9mm_luger` (default, one case) | case | base down | 9mm Luger | 7.09 | 12.96 | 34 | 406 | 10.56 |
| `pocket_pistol` | case | base down | .25 ACP, .32 ACP, .380 ACP | 6.06 | 12.53 | 36 | 499 | 10.13 |
| `small_pistol` | case | base down | 9mm Makarov, 9mm Luger, .45 GAP, 9x21 | 7.22 | 14.94 | 29 | 255 | 12.54 |
| `large_pistol` | case | base down | .40 S&W, .357 SIG, .45 ACP, .38 Super, 7.62x25, 10mm Auto | 8.60 | 15.19 | 29 | 200 | 12.79 |
| `revolver` | case | base down | .38 Special, .357 Magnum, .44 Special, .44 Magnum, .45 Colt | 11.46 | 16.06 | 27 | 127 | 13.66 |

A group plate gives its smallest case up to 2.3 mm more play than a one-case plate, so more cases may go in upside down (untested). A one-case plate (any key of `calibers.table`) is the tight option. Capacity counts the group's largest case. Rifle cases and bullets need another exit and are not built.

What a set delivers is `case_plate.item` (`case`, later `bullet`) and `case_plate.orient` (`base_down`: mouth up at the exit). The plate, the exit insert and the tilt preset are selected from them, and only the pairs in `case_plate.tilts` are built (`case`/`base_down` at 45 deg): any other pair raises an error that names them. Orientation stays a property of the pocket and ridge geometry and the tilt, there is no flip module.

## Drop tube attachment

The drop tube twists onto the exit spigot, no screw and no tool (`drop_tube`, `exit.spigot_len`). Decision: a bayonet instead of a DIN 464 thumb screw on a boss.

- Hose pull and vibration: the tube hangs on the notch floors, so its weight and an axial hose pull load the lugs against a 45 deg floor, the strong direction. Sideways hose pull is carried by the spigot over the full socket depth. To turn the tube off, lift it 1 mm (`lock_lift`) out of the notch first, which a shaking or pulled hose does not do on its own. Strength and hold are estimates until a print is tried.
- Sensor window: the stop at the end of the 60 deg turn fixes the tube's azimuth, with the lug-to-notch fit (`print.fit`) as the only play, at most 0.3 mm at the window (checked in `tests/test_drop_tube.py`). The wide and the narrow lug make the tube fit one way only, sensor on the +x side of the body.
- To fit: hold the socket 60 deg counterclockwise (seen from below) of its final position, push it up over the spigot until the lugs reach the groove, turn it clockwise until it stops and drops into the notch.

## Drop tube chain

Parts chain on the drop tube instead of more openings in the bowl: one drop opening is active, and what differs between presses and uses lies below the spigot. Every part of the chain (`drop_chain`) has the drop tube's socket and bayonet at its mouth and the exit spigot's male form (same lugs and outline) at its other end, so the spacer and the angled piece chain in any order. The drop tube, the spacer and the angled piece end in the male form, the hose adapter ends the chain with the barb. `drop_chain.parts` lists the optional parts between the drop tube and the hose adapter, in order: `()` is the default assembly, `("spacer", "angled")` puts both in the assembly. An unknown name raises an error that names the supported ones.

- Bore: every part keeps the drop tube bore (`test_drop_chain`), so it never narrows along the path. A part with another bore, or an offset piece, takes the same two forms.
- Sensor window: the wide lug and the stop carry +x through the chain, the drop tube stays the first tube and the sensor is not in the way (`test_drop_chain`).
- Fit: each part hangs on the notch floors of the part before it, turn on and off as in "Drop tube attachment".
- Press adapters (#7) attach at the end of this chain.

## Hose and sensor

- Lay the hose downhill all the way to the press, with no loops or rising sections. A 9mm case (21.6 mm diagonal) cannot turn over in the 14 mm hose or the 10.9 mm bore.
- The sensor sees the case through the 1.0 mm `drop_tube.window_t` wall. With a brass correction factor of 0.3 to 0.5 the LJ18A3-8 switches at 1.9 to 3.2 mm (estimate). A case lies 1.45 to 1.90 mm from the sensor face. Test with real cases before printing more. If it misses cases, set `window_t` to 0.6 or use a longer-range M18 sensor.
- Each falling case passes the sensor in about 0.1 s. Use an off-delay timer relay (BOM) so the motor stops only on a full tube, not on each case.

## Tilt mount

Yoke on the 4 M5 inserts of the body core, M10 pivot axis parallel to x, tube clamp on a vertical 25 mm tube (`mount.tube_shape` round or square). A tilt link joins a fork under the yoke (pin A) and a fork on the low side of the clamp block (pin B). The weight keeps the link in compression at every tilt, empty or full (`test_mount`, centre of mass from the CAD volumes). The nylon nut on the pivot bolt sets the pivot friction. `test_mount` also checks a 50 N push anywhere on the rim (`mount.push`) against the printed layer strength.

Two links on the same pins (`mount.link_a`, `mount.link_b`). The link gets 1.1 to 1.2 mm shorter per degree steeper, so 0.1 mm of hole or print error moves the tilt by 0.1 deg at most:

| Link | Parts | Tilt |
|---|---|---|
| adjustable | `mount_rod_end_adjust` on pin A, `mount_rod_end_fixed` on pin B, M6 threaded rod. Fixed end: captive nut in the outer face, jam nut in the window. Adjust end: a nut each side of its wall. To change the tilt, loosen the two adjust end nuts, run them along the rod, tighten them against the wall | 40 to 60 deg, stepless (`mount.tilt_range`) |
| fixed | `mount_link_45`, `mount_link_50`, `mount_link_55`, one printed bar per angle (`mount.fixed_tilts`). Swap the bar to change the tilt. `mount.link` set to one of these angles builds the assembly with that bar, without rod ends, rod and rod nuts, at that tilt | the angle in its name |

<!-- --8<-- [start:tilt] -->
Tilt choice. The best angle for 9mm on this feeder is UNTESTED. Start at 45 and go steeper only for the reason in the table:

| Tilt | When | 9mm capacity, wall / with extender | Link pin to pin |
|---|---|---|---|
| 45 deg | default, start here | 406 / 534 | 91.4 mm |
| 50 deg | cases still go in upside down at 45 | 325 / 574 | 85.6 mm |
| 55 deg | still upside down at 50 | 254 / 626 | 79.7 mm |
| 60 deg | last resort, extender needed for the design fill | 193 / 516 | 73.8 mm |
| 40 deg | most capacity, range end of this mount | 504 / 504 | 97.1 mm |

Capacity: cases under a level brass surface as high as the lowest rim point allows (the wall top, or the extender top over its arc), loose packing 0.55 of the case envelope (`layout.capacity`, estimate). Fill at most 250 9mm cases (1 kg, `case_plate.fill_cases`, `case_plate.drag_mass`) at any tilt: the clutch, cap and mount load checks assume no more. The extender keeps 250 cases in at 60 deg, it is not for a larger fill. Above 55 deg it is the low side that limits the capacity, below it the open high side: the extender adds little at 40 deg.
<!-- --8<-- [end:tilt] -->

| Part | Hardware |
|---|---|
| `mount_yoke` | 4 x ISO 4762 M5 x 12 into the body's CNC Kitchen M5 x 9.5 inserts |
| `mount_clamp` | 2 x ISO 4762 M5 x 35 on 2 x ISO 7089 M5 washers, 2 x ISO 4032 M5 nuts |
| pivot (both parts) | ISO 4017 M10 x 55, 2 x ISO 7089 M10 washers (same sizes as DIN 125 A), DIN 985 M10 nut |
| link pins A and B | 2 x ISO 4762 M6 x 45, 4 x ISO 7089 M6 washers, 2 x DIN 985 M6 nuts |
| adjustable link | DIN 976-1 M6 threaded rod cut to 60 mm, 4 x ISO 4032 M6 nuts |

Check the tilt with a phone inclinometer laid on the empty case plate, along the slope. The wall top is not parallel to the plate (it falls toward the high side).

Print the yoke with the flat mating face on the bed, the clamp upright, links and rod ends flat. The clamp bore is closed at the top (25 mm bridge) and stops the tube. The fork ears on the clamp are 45 deg triangles, so they print without supports. The printed pin and pivot holes under load are UNTESTED.

## Simulation

`sim/` simulates brass on the turning plate in MuJoCo (`pip install -e .[sim]`, already in `requirements.txt`) and estimates cases per hour, pocket fill, case orientation at the exit and plate torque for a tilt and plate speed. It runs slower than real time (about 3 to 4 s of computing per simulated second with 250 cases), so a sweep takes hours. In the container:

| Command | Result |
|---|---|
| `.venv/bin/python -m sim run --tilt 45 --rpm 1.5` | one point after one warm-up turn, metrics as JSON |
| `.venv/bin/python -m sim sweep --tilt 38,45,52,62 --rpm 0.75,1.5,3,6.5` | grid into `build/sim/sweep.csv`; a stopped sweep resumes, at most 6 workers |
| `.venv/bin/python -m sim sweep --plate 9mm_luger,small_pistol --case 9mm_luger --out build/sim/pockets.csv` | one case size on several plate sets (`--plate` takes `case_plate.caliber` values, `--case` a `calibers.table` key) |
| `.venv/bin/python -m sim plot` | `build/sim/sweep.png`: cases per hour, fill with its 95 % interval, torque |
| `.venv/bin/python -m sim calibrate measured.csv` | fits friction and case centre of mass to hardware runs (columns `tilt`, `rpm`, `cases_per_h`, `base_down_share`) into `build/sim/calibration.csv` |

`valid` is false when a case went through the deck outside the opening (`lost`, with where in `lost_at`): a model fault, so `plot` leaves the point out. `spilled` counts cases over the wall (`spilled_at`), `overfill` the cases that found no room below the wall top on their way back. The extender is fitted (`extender`) when `--cases` is more than the wall holds at the tilt (`layout.capacity`). `deepest_mm`, `deepest_pair` and `deep_share` (share of checks with a contact overlap above 1.5 mm) show how far the soft contacts give.
`wrong_upper` is the upper bound on cases leaving mouth down or sideways.

Approximations, so take the numbers as trends until calibrated:

- The plate collider is a convex decomposition of the CAD plate (CoACD): hulls reach up to 0.26 mm into the pockets (`sim.pocket_hull_threshold`) and up to 0.8 mm into the air elsewhere (`sim.hull_threshold`).
- Deck, band, gate and wall are boxes round the bowl (`sim.segments`).
- A case is a capsule against other cases, with flat end discs against the feeder.
- One friction value (`case_plate.drag_mu`) for every contact. Case mass and centre of mass (`sim.case_mass`, `sim.com_ratio`) are estimates, unverified.

Results (250 9mm cases, 9mm plate, wall 125, about 3 counted turns per point, one seed). Cases per hour and pocket fill:

| Tilt | 0.75 rpm | 1.5 rpm | 3 rpm | 6.5 rpm |
|---|---|---|---|---|
| 38 deg | 885, 59 % | 1,920, 63 % | 2,700, 45 % | 6,500, 49 % |
| 45 deg | 1,005, 67 % | 1,920, 63 % | 2,640, 43 % | 3,770, 28 % |
| 52 deg | 660, 44 % | 1,320, 44 % | 1,920, 31 % | 2,860, 22 % |
| 62 deg (extender) | 375, 25 % | 510, 17 % | 660, 11 % | 520, 4 % |

- Wall falling at 15 deg: every point is valid, and every case left base down, about 600 exits in all. Plate torque peaks at 0.72 Nm, below the low slip estimate of 0.84 Nm.
- Case centre of mass at 0.33 and 0.39 of the length from the base (38 and 45 deg, 1.5 and 3 rpm) moves the rate between 1,200 and 3,780 per hour, still all base down. The farther the centre of mass from the base, the lower the fill.
- 9mm cases on the small_pistol plate (larger pockets) at 45 deg: 1,650 per hour at 1.5 rpm and 2,400 at 3 rpm, all base down.

The results above and in the three bullets are from the wall that fell at 15 deg. With the wall top falling at 40 deg toward the open high side (`body.heap_angle` 0) and the extender as an open arc, 250 cases, one seed, no case spilled and all left base down:

| Tilt | 1.5 rpm | 3 rpm |
|---|---|---|
| 40 deg | 1,590, 52 % | 2,820, 46 % |
| 45 deg | 1,920, 63 % | 2,460, 40 % |
| 60 deg (extender) | 690, 23 % | 1,140, 19 % |

## License

MIT, see `LICENSE`.
