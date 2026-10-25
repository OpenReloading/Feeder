# BOM: 9mm case feeder (default configuration)

Default: split body, Pololu 2693 metal hub, simple PWM speed controller, no microcontroller. Sizes marked unverified come from seller listings: measure on delivery and adjust `feeder/config.py`.

## Printed parts

| Part | Qty |
|---|---|
| `slip_clutch_carrier_metal_hub` | 1 |
| `slip_clutch_hub_gauge` | 1 |
| `slip_clutch_drive_ring` | 1 |
| `slip_clutch_disc` | 1 |
| `slip_clutch_knob` | 1 |
| `slip_clutch_cap` | 1 |
| `case_plate_9mm_luger` | 1 |
| `body_core` | 1 (split `arcs`, default) |
| `body_wall_0`, `body_wall_1`, `body_wall_2` | 1 each (split `arcs`) |
| `body_half_0`, `body_half_1` | 1 each, instead of core and walls (split `halves`) |
| `body` | 1, instead of core and walls (split `one_piece`, 233.0 mm plate) |
| `body_extender` | 1, optional, 60 mm more wall over a 200 deg arc on the low side, leaning 25 deg toward the bowl axis |
| `body_track_gate` | 1 |
| `body_exit_insert` | 1 |
| `drop_tube` | 1 |
| `mount_yoke` | 1 |
| `mount_clamp` | 1 |
| `mount_rod_end_adjust`, `mount_rod_end_fixed` | 1 each, adjustable link |
| `mount_link_45`, `mount_link_50`, `mount_link_55` | 1 each, optional fixed links |
| `electronics_box` or `electronics_box_left` | 1, right or left of the tube as the user sees it |
| `electronics_lid` | 1 |

Other calibers: plate, exit insert and drop tube come per plate set from `build/plates/<set>/` (README, Plate sets). The rest stays.

## Drive and clutch

| Item | Qty | Used in | Note |
|---|---|---|---|
| Worm gear motor 5840-31ZY, 12 V, 8 mm D shaft, 1240 winding, 590:1 (6.5 rpm no load, 5 rpm at the suggested load) | 1 | body core | slowest variant. Runs at about 10 to 30 % PWM duty. Gearbox limit 3.92 Nm ([microdcmotors](https://microdcmotors.com/product/12v-24v-high-torque-low-speed-dc-motor-with-encoder-self-locking-model-nfp-5840-31zy-en)). May not start below 10 to 15 % duty (unverified) |
| Pololu 2693 aluminium hub, 8 mm bore, M3 holes | 1 | carrier | sold in pairs, includes its set screws. Option: `GENERIC_8MM_FLANGE` with 2 x ISO 4762 M3 x 12 and 2 x ISO 4032 M3 nuts |
| Compression spring Gutekunst VD-127E-01 | 6 | disc | |
| Split key ring 25 mm | 1 | case plate eye | one per plate, to lift it off |
| ISO 4762 M3 x 10 | 3 | hub to carrier | |
| ISO 4017 M5 x 16 | 1 | knob | |
| CNC Kitchen heat-set insert M5 x 9.5 | 1 | carrier | |
| ISO 10642 M4 x 10 | 4 | motor to body core | |

## Body

| Item | Qty | Used in | Note |
|---|---|---|---|
| CNC Kitchen heat-set insert M3 x 5.7 | 9 | body core, wall joints | split `arcs`. `halves`: 6 in the seam posts of half 1. `one_piece`: none |
| ISO 4762 M3 x 12 | 9 | wall to core | split `arcs`. `halves`: 6 across the seam posts. `one_piece`: none |
| ISO 10642 M3 x 12 | 4 | extender to wall | only with the extender, from inside the bowl, head flush |
| ISO 4032 M3 nut | 4 | extender to wall | only with the extender, captive in the ribs outside the sleeve |
| CNC Kitchen heat-set insert M5 x 9.5 | 4 | body core, mount | |

## Tilt mount

| Item | Qty | Used in | Note |
|---|---|---|---|
| ISO 4762 M5 x 12 | 4 | yoke to body core inserts | |
| ISO 4762 M6 x 45 | 2 | link pins A and B | |
| ISO 7089 M6 washer | 4 | link pins | |
| DIN 985 M6 nylon lock nut | 2 | link pins | |
| DIN 976-1 M6 threaded rod | 60 mm | adjustable link | cut from a 1 m rod |
| ISO 4032 M6 nut | 4 | adjustable link: captive, jam, two on the adjust end | |
| ISO 4762 M5 x 35 | 2 | tube clamp | |
| ISO 7089 M5 washer | 2 | tube clamp, under the screw heads | spreads the clamp load on the plastic |
| ISO 4032 M5 nut | 2 | tube clamp | |
| ISO 4017 M10 x 55 | 1 | pivot | |
| ISO 7089 M10 washer | 2 | pivot | |
| DIN 985 M10 nylon lock nut | 1 | pivot, sets the pivot friction | |
| Tube 25 mm, round or square | 1 | stand | length to the bench, `mount.tube_shape` |

## Drop tube and sensor

| Item | Qty | Used in | Note |
|---|---|---|---|
| Inductive sensor LJ18A3-8-Z/AX, M18x1, NPN NC, 6 to 36 V (unverified) | 1 | drop tube, tube-full | body (65 mm long) and lock nuts unverified (24 AF x 4) |
| Lock nut M18 x 1 | 2 | sensor in the drop tube | one each side of the printed plate, supplied with the sensor. 24 AF x 4 unverified |
| Clear PVC hose 14 mm ID x 18 mm OD | length to the press | drop tube barb | unverified |

## Electronics

| Item | Qty | Note |
|---|---|---|
| 12 V DC power supply, 3 A | 1 | motor and sensor |
| DC motor PWM speed controller, 12 V, with a minimum-duty trim | 1 | sets the plate speed. Set the trim so the motor still starts at the lowest knob setting |
| 12 V off-delay timer relay module (output holds for the set delay after the input drops, a returning input resets it), normally open contact in the motor line | 1 | input from the sensor output. The NC sensor conducts while no brass is in front of it, so the relay holds and the motor runs. Brass in front for longer than the delay (set about 2 s), a broken wire or no sensor power stops the motor. Each falling case blinks the sensor for about 0.1 s, which the delay ignores. Module type, input current and delay mode unverified: check against the sensor output |

## Electronics box

| Item | Qty | Used in | Note |
|---|---|---|---|
| ISO 4762 M5 x 35 | 2 | box clamp on the tube | |
| ISO 7089 M5 washer | 2 | box clamp, under the screw heads | |
| ISO 4032 M5 nut | 2 | box clamp | |
| CNC Kitchen heat-set insert M3 x 5.7 | 8 | 4 box corner posts, 4 relay standoffs | |
| ISO 4762 M3 x 8 | 8 | 4 lid to box, 4 relay to its standoffs | |
| Toggle switch MTS-102, 6 mm panel hole | 1 | power, front face | rating for 12 V DC 3 A unverified |
| DC panel jack DC-022B, 5.5 x 2.1 mm, 11 mm panel hole | 1 | 12 V in, front face | hole size unverified |
| GX12 2-pin panel socket and plug | 1 | motor, side face | 12 mm hole unverified |
| GX12 3-pin panel socket and plug | 1 | sensor, side face | 12 mm hole unverified. The pin counts differ so the motor plug cannot go in the sensor socket |
| Panel nut, PWM knob | 1 | potentiometer in the lid | supplied with the potentiometer, size unverified |
| Panel nut, toggle switch | 1 | toggle switch in the lid | supplied with the switch, size unverified |
| Panel nut, DC jack | 1 | DC jack in the lid | supplied with the jack, size unverified |
| Panel nut, GX12 2-pin socket | 1 | motor socket in the side face | supplied with the socket, size unverified |
| Panel nut, GX12 3-pin socket | 1 | sensor socket in the side face | supplied with the socket, size unverified |

The PWM controller hangs on its knob potentiometer nut in the lid (7.2 mm hole, unverified, the pot must be on the board or on a lead). The timer relay module sits on four standoffs on the back wall, 44 x 24 mm hole spacing (`electronics.relay_holes`, unverified: measure on delivery). Hole sizes are in `electronics.front_holes` and `electronics.side_holes`.

Without a motor driver there is no current limit, and the motor's stall torque is far above the gearbox limit: the clutch (0.84 to 2.10 Nm, estimate) is the only torque limit, below the gearbox limit of 3.92 Nm and above the plate drag of 0.27 Nm at 38 deg (estimate).
