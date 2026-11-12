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

Other calibers: plate, exit insert, drop tube and its chain parts come per plate set from `build/plates/<set>/` (`docs/design.md`, Plate sets). The rest stays.

## Drive and clutch

| Item | Qty | Used in | Note |
|---|---|---|---|
| Worm gear motor 5840-31ZY, 12 V, 8 mm D shaft, 1240 winding, 590:1 (6.5 rpm no load, 5 rpm at the suggested load) | 1 | body core | slowest variant. Runs at about 10 to 30 % PWM duty. Gearbox limit 3.92 Nm ([microdcmotors](https://microdcmotors.com/product/12v-24v-high-torque-low-speed-dc-motor-with-encoder-self-locking-model-nfp-5840-31zy-en)). May not start below 10 to 15 % duty (unverified). Stall current at most 2.60 A, no-load at most 200 mA, suggested load at most 0.70 A at 12 V, the figure that sizes the supply, fuse and controller below. Either variant fits, the body clears the covered encoder (`motor.can_l`). Without encoder: the motor cable goes to its two terminals. With encoder (the linked listing): its terminals sit under the encoder cover, so use the two motor leads of its connector and leave the encoder leads free; which leads those are is not in the listing, unverified: find them on delivery. The direction of the output for + on a given terminal is unverified: check it at the first power-up (Wiring page) |
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
| 12 V DC power supply, 3 to 5 A, 5.5 x 2.1 mm plug, centre positive, for example [Mean Well GST60A12-P1J](https://www.meanwell.com/Upload/PDF/GST60A/GST60A-SPEC.PDF) | 1 | an enclosed desktop mains adapter with short-circuit and overload protection: the box is printed and the fuse alone does not protect a short against every supply. Motor, relay and sensor: 2.6 A at motor stall plus about 0.1 A for relay and sensor (estimate), so 3 A is enough for the 1240 winding. Never open the adapter, and never use a battery instead. Tag the adapter lead "12 V FEEDER": the press drive's 24 V adapter has the same 5.5 x 2.1 mm plug, and on the feeder it runs the plate at twice the speed |
| [DC motor PWM speed controller, 12 to 30 V, rated 7 A, peak 10 A, 50 x 32 mm, B100K potentiometer](https://scccltd.com/products/12v-30v-10a-pwm-dc-motor-speed-controller) | 1 | sets the plate speed, above the 2.6 A motor stall current. No reverse polarity protection (listing), hence the series diode. No current limit, so the clutch is the only torque limit. Minimum-duty trim, mounting holes and height not in the listing, unverified. Set the trim so the motor still starts at the lowest knob setting |
| [Littelfuse 0218001.MXP, 5 x 20 mm time-lag fuse, 1 A](https://www.littelfuse.com/~/media/electronics/datasheets/fuses/littelfuse_fuse_218_datasheet.pdf.pdf) | 1 | sized for the 1240 winding: at least 1.25 times the 0.78 A load and at most the 2.60 A stall over 2.1. It holds 150 % (data sheet), opens on a stall at full knob (260 %) within 120 s, and on a short behind it if the supply holds its limit (105 to 150 % of its rating): within 10 s for a 3 A supply (315 to 450 %), within 3 s for a 5 A supply (525 to 750 %). An adapter with hiccup protection may cut out first and leave the fuse whole: unplug the supply before you look for a fault. The stall figure is the seller's, so tell the winding apart before the first run, without stalling the motor: its stall torque is far above the gearbox limit, and the 1 A fuse can open within the test. Motor unplugged, meter on its lowest resistance range: touch the probes together and note the reading, then read across the two motor terminals (encoder variant: its two motor leads) at three shaft positions, take the middle reading and subtract the probe reading. About 4.6 Ω (12 V over 2.60 A) is the 1240 winding: T 1 A. About 1.7 Ω (12 V over 7.0 A) is the 1280 winding (1.6 A load): fit 3.15 A (02183.15MXP). Both from the seller's stall figures, estimate. Any other reading: apply the rule with 12 V over the reading as the stall current. The fuse sees the PWM duty times the motor current, so between about 40 and 85 % duty a stall heats the winding and no fuse value opens: the clutch check stays the real protection. 250 V AC rated, breaks 35 A, no DC rating, so a mains adapter only, never a battery |
| Inline fuse holder for 5 x 20 mm fuses, 0.75 mm² leads | 1 | in the +12 V line after the switch, lies in its cradle on the back wall of the box, tied down with 2 cable ties. About 12 mm across and 52 mm long (`electronics.fuse_holder`, unverified: measure on delivery). Rating unverified: it must list at least 5 A |
| [Vishay SB560-E3/54 Schottky diode, 5 A, 60 V, DO-201AD](https://azcus.digikey.com/en/products/detail/vishay-general-semiconductor-diodes-division/SB560-E3-54/1023528) | 2 | D1 in series in the +12 V line, blocks a reversed supply (0.65 V drop at 5 A, listing). D2 across the motor line after the relay contact, at K1: cathode lead in K1 OUT2, anode lead on wire 17 to U1 M- (Wiring page, step E), so the lid opens on wires only; it clamps the kick when the relay contact opens. Its 1.22 to 1.32 mm leads ([data sheet](https://www.vishay.com/docs/88721/sb520.pdf)) do not fit a GX12 solder cup. D2 needs the 5 A part: with the relay closed it carries much of the motor current in the PWM off time, beside the controller's own freewheel diode |
| Flexible wire 0.75 mm², red and black | 1 m each | supply and controller supply lines in the box (wires 1 to 7). Current rating unverified: the fuse protects it |
| Flexible wire 0.34 mm², red, black, brown and blue | 1 m each | relay supply, sensor socket and motor lines in the box (wires 8 to 15 and 17): the GX12 solder cups take nothing thicker. Current rating unverified: the 1 A fuse protects it |
| Motor cable, round, 2 cores 0.34 mm², at most 5 mm across | length to the motor | box to motor, soldered to the motor terminals and the GX12 plug: 0.8 mm solder cups and a 5.0 mm cable entry. Drop over 1.5 m: 0.11 V at the suggested load, 0.41 V at stall (estimate). Current rating unverified: the 1 A fuse protects it |
| 5-way lever splice connector, 0.2 to 4 mm² | 2 | the +12 V and 0 V joins (XP and XN of the wiring), each in its cradle on the back wall, tied down with a cable tie. About 30 x 19 x 9 mm with the levers shut (`electronics.splice`, listing values, unverified: measure on delivery); the levers need 12 mm free above it (estimate, unverified) |
| Cable ties, 2.5 x 100 mm | 1 pack of at least 10 | fuse holder (2), splice connectors (2), the wires at each GX12 socket (1 each), and the loops. The tunnels in the box are 3.5 x 1.5 mm (`electronics.tie_slot`), unverified for thick ties |
| Wire end ferrule 0.75 mm², DIN 46228-1 | 2 | supply terminals of the controller. Sleeve length unverified: fit to the terminal |
| Wire end ferrule 0.34 mm², DIN 46228-1 | 7 | motor terminals of the controller (2), relay contact (2), relay supply (2) and wire 17 from D2 in U1 M- (1); the cathode lead of D2 goes in bare beside the ferrule at K1 OUT2. Sleeve length unverified: fit to the terminal |
| 3-pin lead for the relay module's trigger header | 1 | the low-level trigger wire is wire 12, soldered to cup 3 of the sensor socket; the other two wires stay free, ends insulated. Header pitch and whether the module ships with the lead: unverified, check on delivery |
| Resistor 10 kΩ, 0.25 W | 1 | for the sensor check on delivery only (Wiring page), not built in. Any through-hole part |
| Heat shrink tube, 2:1, 3 mm and 8 mm | 20 cm each | 3 mm over each GX12 solder cup, the motor terminals, the cathode lead of D2, and its anode lead with the joint to wire 17; 8 mm over D1 and its two joints (DO-201AD body about 5.3 mm across, unverified) |
| Electronics solder with flux core | a few grams | GX12 cups, D1 joints, the D2 anode joint, motor terminals. Any rosin core solder, unverified |
| [DROK delay relay module SKU 200391, 6 to 30 V, LCD, 71 x 39 x 25 mm](https://m.media-amazon.com/images/I/91rcHqMUeoL.pdf) | 1 | off-delay timer, one dry relay contact (30 V DC 10 A) in the motor + line, the second contact terminal is the other end of that line. Set mode P8 (signal holding: the relay stays on while the trigger is present, and drops OP after it disappears, a returning trigger clears the timing) and OP to 0.5 s, in the 0.1 s unit: in the OP setting the pause button switches the unit, set the display to 000.5 (in the 1 s unit a 5 is 5 s). 0.5 s is longer than one passing case, shorter than the free drop path above the sensor takes to fill at the case rate (the 9mm plate passes 3.7 pockets per second at 6.5 rpm). The NC sensor pulls the low-level trigger input (0.0 to 0.2 V) to 0 V while no brass is in front of it, so the relay holds and the motor runs. Brass in front for longer than OP, a broken wire or no sensor power stops the motor. Each falling case blinks the sensor for about 0.1 s, which OP ignores. The trigger input is a 3-pin header (high-level trigger, signal ground, low-level trigger), not a screw terminal. In mode P8 the module's button counts as a trigger and starts the motor. Isolated input, 15 mA idle and 50 mA working current from the supply. Trigger input current and mounting hole spacing are not in the sheet, unverified. A sensor that leaks in its off state can hold the input and keep the motor running: test the sensor at the relay input before the first run (Wiring page). This module is adjustable and switches either line, so it suits the topology; a module with a bare transistor output that can only switch the 0 V line does not |

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
| GX12 2-pin panel socket and plug | 1 | motor, side face | 5 A per contact, solder cup mouth 0.8 mm, cable entry 5.0 mm ([one maker's drawing](https://www.kinghelm.net/upload/file/20231129/KH-GX12-5P.pdf); the part is generic, measure the cups on delivery), so 0.34 mm² wire. 12 mm hole unverified. Body and solder cups reach 30 mm behind the inner face of the wall (`electronics.socket_depth`, unverified: no drawing found, seller listings say about 30 mm overall): measure on delivery |
| GX12 3-pin panel socket and plug | 1 | sensor, side face | 12 mm hole unverified, same 30 mm depth. The pin counts differ so the motor plug cannot go in the sensor socket |
| Panel nut, PWM knob | 1 | potentiometer in the lid | supplied with the potentiometer, size unverified |
| Panel nut, toggle switch | 1 | toggle switch in the lid | supplied with the switch, size unverified |
| Panel nut, DC jack | 1 | DC jack in the lid | supplied with the jack, size unverified |
| Panel nut, GX12 2-pin socket | 1 | motor socket in the side face | supplied with the socket, size unverified |
| Panel nut, GX12 3-pin socket | 1 | sensor socket in the side face | supplied with the socket, size unverified |

The PWM controller hangs on its knob potentiometer nut in the lid (7.2 mm hole, unverified, the pot must be on the board or on a lead). The timer relay module (71 x 39 mm board, 25 mm high with its LCD and terminals, `electronics.relay_board`) sits on four standoffs on the back wall, 64 x 32 mm hole spacing (`electronics.relay_holes`, an estimate, unverified: measure on delivery). The box is 96 x 54 x 120 mm inside. The side sockets stand one above the other in the front band between the relay and the lid, 19.5 and 45 mm above the box floor (`electronics.socket_z`), because their bodies and solder cups reach 30 mm into the box: they clear the relay and the DC jack, and a free run of 30 mm behind each is kept for a service loop (`electronics.service_loop`). A tie pad on the side wall behind each socket anchors its wires. The fuse holder and the two splice connectors lie in cradles on the back wall above the relay, open toward the lid. Hole sizes are in `electronics.front_holes` and `electronics.side_holes`.

The lid carries an engraved map of the plugs and the supply jack: SENSOR 1 BN, 2 BU, 3 BK; MOTOR 1 +, 2 -; 12V IN with the centre pin marked TIP +; SPEED at the knob and POWER at the switch. The pins and the polarity come from the wiring data (`feeder/wiring.py`), so the lid and the wiring page cannot disagree. The box and the lid have a 1.5 mm chamfer on their outside edges.

The controller has no current limit and the motor's stall torque is far above the gearbox limit: the clutch (0.84 to 2.10 Nm, estimate) is the only torque limit, below the gearbox limit of 3.92 Nm and above the plate drag of 0.27 Nm at 38 deg (estimate).
