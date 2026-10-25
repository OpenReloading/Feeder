# BOM: 9mm case feeder (default configuration)

Default: split body, Pololu 2693 metal hub, 7 A PWM speed controller, no microcontroller. Sizes marked unverified come from seller listings: measure on delivery and adjust `feeder/config.py`.

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
| `drop_hose_adapter` | 1 |
| `drop_spacer`, `drop_angled` | 1 each, optional, chain between the drop tube and the hose adapter (`drop_chain.parts`) |
| `body_exit_insert_blank` | 1, optional, closes the exit instead of the exit insert |
| `mount_yoke` | 1 |
| `mount_clamp` | 1 |
| `mount_rod_end_adjust`, `mount_rod_end_fixed` | 1 each, adjustable link |
| `mount_link_45`, `mount_link_50`, `mount_link_55` | 1 each, optional fixed links |
| `electronics_box` or `electronics_box_left` | 1, right or left of the tube as the user sees it |
| `electronics_lid` | 1 |

Other calibers: plate, exit insert, drop tube and its chain parts come per plate set from `build/plates/<set>/` (README, Plate sets). The rest stays.

## Drive and clutch

| Item | Qty | Used in | Note |
|---|---|---|---|
| Worm gear motor 5840-31ZY, 12 V, 8 mm D shaft, 1240 winding, 590:1 (6.5 rpm no load, 5 rpm at the suggested load) | 1 | body core | slowest variant. Runs at about 10 to 30 % PWM duty. Gearbox limit 3.92 Nm ([microdcmotors](https://microdcmotors.com/product/12v-24v-high-torque-low-speed-dc-motor-with-encoder-self-locking-model-nfp-5840-31zy-en)). May not start below 10 to 15 % duty (unverified). Stall current at most 2.60 A, no-load at most 200 mA, suggested load at most 0.70 A at 12 V, the figure that sizes the supply, fuse and controller below |
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
| Clear PVC hose 14 mm ID x 18 mm OD | length to the press | hose adapter barb | unverified |

## Electronics

| Item | Qty | Note |
|---|---|---|
| 12 V DC power supply, 5 A, 5.5 x 2.1 mm plug, centre positive | 1 | motor, relay and sensor: 2.6 A at motor stall plus about 0.1 A for relay and sensor (estimate). Rating from the label, unverified |
| [DC motor PWM speed controller, 12 to 30 V, rated 7 A, peak 10 A, 50 x 32 mm, B100K potentiometer](https://scccltd.com/products/12v-30v-10a-pwm-dc-motor-speed-controller) | 1 | sets the plate speed, above the 2.6 A motor stall current. No reverse polarity protection (listing), hence the series diode. No current limit, so the clutch is the only torque limit. Minimum-duty trim, mounting holes and height not in the listing, unverified. Set the trim so the motor still starts at the lowest knob setting |
| [Littelfuse 02183.15MXP, 5 x 20 mm time-lag fuse, 3.15 A](https://cpc.farnell.com/littelfuse/02183-15mxp/fuse-5x20mm-time-delay-3-15a/dp/FF02791) | 1 | above the motor stall current and below the 5 A supply, so a short trips it and a stall does not. 250 V AC rated (listing), DC rating unverified |
| Inline fuse holder for 5 x 20 mm fuses, 0.75 mm² leads | 1 | in the +12 V line after the switch, lies in its cradle on the back wall of the box, tied down with 2 cable ties. About 12 mm across and 52 mm long (`electronics.fuse_holder`, unverified: measure on delivery). Rating unverified: it must list at least 5 A |
| [Vishay SB560-E3/54 Schottky diode, 5 A, 60 V, DO-201AD](https://azcus.digikey.com/en/products/detail/vishay-general-semiconductor-diodes-division/SB560-E3-54/1023528) | 2 | D1 in series in the +12 V line, blocks a reversed supply (0.65 V drop at 5 A, listing). D2 across the motor plug, cathode to motor +, clamps the kick when the relay contact opens |
| Flexible wire 0.75 mm², red and black | 1 m each | supply, controller and motor lines in the box. Current rating unverified: the 3.15 A fuse protects it |
| Motor cable, 2 cores 0.75 mm² | length to the motor | box to motor, soldered to the motor terminals and the GX12 plug. Current rating unverified |
| 5-way lever splice connector, 0.2 to 4 mm² | 2 | the +12 V and 0 V joins (XP and XN of the wiring), each in its cradle on the back wall, tied down with a cable tie. About 30 x 19 x 9 mm with the levers shut (`electronics.splice`, listing values, unverified: measure on delivery); the levers need 12 mm free above it (estimate, unverified) |
| Cable ties, 2.5 x 100 mm | 1 pack of at least 10 | fuse holder (2), splice connectors (2), the wires at each GX12 socket (1 each), and the loops. The tunnels in the box are 3.5 x 1.5 mm (`electronics.tie_slot`), unverified for thick ties |
| Wire end ferrule 0.75 mm², DIN 46228-1 | 6 | screw terminals of the controller (4) and the relay contact (2). Sleeve length unverified: fit to the terminal |
| Wire end ferrule 0.34 mm², DIN 46228-1 | 3 | relay supply and input screw terminals. Sleeve length unverified: fit to the terminal |
| [DROK delay relay module SKU 200391, 6 to 30 V, LCD, 71 x 39 x 25 mm](https://m.media-amazon.com/images/I/91rcHqMUeoL.pdf) | 1 | off-delay timer, one dry relay contact (30 V DC 10 A) in the motor + line, the second contact terminal is the other end of that line. Set mode P8 (signal holding: the relay stays on while the trigger is present, and drops OP after it disappears, a returning trigger clears the timing) and OP to about 2 s. The NC sensor pulls the low-level trigger input (0.0 to 0.2 V) to 0 V while no brass is in front of it, so the relay holds and the motor runs. Brass in front for longer than OP, a broken wire or no sensor power stops the motor. Each falling case blinks the sensor for about 0.1 s, which OP ignores. Isolated input, 15 mA idle and 50 mA working current from the supply. Trigger input current and mounting hole spacing are not in the sheet, unverified. The sensor's on-state voltage must stay below 0.2 V: check it before the first run (Wiring page). This module is adjustable and switches either line, so it suits the topology; a module with a bare transistor output that can only switch the 0 V line does not |

## Electronics box

| Item | Qty | Used in | Note |
|---|---|---|---|
| ISO 4762 M5 x 35 | 2 | box clamp on the tube | |
| ISO 7089 M5 washer | 2 | box clamp, under the screw heads | |
| ISO 4032 M5 nut | 2 | box clamp | |
| CNC Kitchen heat-set insert M3 x 5.7 | 8 | 4 box corner posts, 4 relay standoffs | |
| ISO 4762 M3 x 8 | 8 | 4 lid to box, 4 relay to its standoffs | |
| [E-Switch 100SP1T1B1M1QEH toggle switch, SPDT used as on-off, 1/4-40 bushing](https://configured-product-images.s3.amazonaws.com/Datasheets/100.pdf) | 1 | power, front face, 6.6 mm panel hole | 5 A resistive at 28 V DC (datasheet, silver contacts). The motor is an inductive load, derate: it carries at most the 2.7 A stall plus relay and sensor. Nut size unverified |
| [Switchcraft L722A DC panel jack, 2.1 mm centre pin, 5.5 mm barrel](https://media.e-sonic.com/productfiles/mf-sc/plf6.pdf) | 1 | 12 V in, front face, 8.2 mm panel hole (.313 in hole, panel up to .125 in, longer .319 in bushing) | 5 A at 12 V DC resistive (datasheet). Body size unverified |
| GX12 2-pin panel socket and plug | 1 | motor, side face | 12 mm hole unverified. Body and solder cups reach 30 mm behind the inner face of the wall (`electronics.socket_depth`, unverified: no drawing found, seller listings say about 30 mm overall): measure on delivery |
| GX12 3-pin panel socket and plug | 1 | sensor, side face | 12 mm hole unverified, same 30 mm depth. The pin counts differ so the motor plug cannot go in the sensor socket |
| Panel nut, PWM knob | 1 | potentiometer in the lid | supplied with the potentiometer, size unverified |
| Panel nut, toggle switch | 1 | toggle switch in the lid | supplied with the switch, size unverified |
| Panel nut, DC jack | 1 | DC jack in the lid | supplied with the jack, size unverified |
| Panel nut, GX12 2-pin socket | 1 | motor socket in the side face | supplied with the socket, size unverified |
| Panel nut, GX12 3-pin socket | 1 | sensor socket in the side face | supplied with the socket, size unverified |

The PWM controller hangs on its knob potentiometer nut in the lid (7.2 mm hole, unverified, the pot must be on the board or on a lead). The timer relay module (71 x 39 mm board, 25 mm high with its LCD and terminals, `electronics.relay_board`) sits on four standoffs on the back wall, 64 x 32 mm hole spacing (`electronics.relay_holes`, an estimate, unverified: measure on delivery). The box is 96 x 54 x 120 mm inside. The side sockets stand one above the other in the front band between the relay and the lid, 19.5 and 45 mm above the box floor (`electronics.socket_z`), because their bodies and solder cups reach 30 mm into the box: they clear the relay and the DC jack, and a free run of 30 mm behind each is kept for a service loop (`electronics.service_loop`). A tie pad on the side wall behind each socket anchors its wires. The fuse holder and the two splice connectors lie in cradles on the back wall above the relay, open toward the lid. Hole sizes are in `electronics.front_holes` and `electronics.side_holes`.

The lid carries an engraved map of the plugs and the supply jack: SENSOR 1 BN, 2 BU, 3 BK; MOTOR 1 +, 2 -; 12V IN with the centre pin marked TIP +; SPEED at the knob and POWER at the switch. The pins and the polarity come from the wiring data (`feeder/wiring.py`), so the lid and the wiring page cannot disagree. The box and the lid have a 1.5 mm chamfer on their outside edges.

The controller has no current limit and the motor's stall torque is far above the gearbox limit: the clutch (0.84 to 2.10 Nm, estimate) is the only torque limit, below the gearbox limit of 3.92 Nm and above the plate drag of 0.27 Nm at 38 deg (estimate).
