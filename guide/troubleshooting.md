---
title: Troubleshooting
---

# Troubleshooting

Find the symptom, try the first fix, then the next. Config values are in `feeder/config.py`; rebuild the changed parts with `build.py`. Switch POWER off before you reach into the bowl or clear a jam: a still plate starts again by itself ([safety and first run](safety.md)).

| Symptom | Likely cause | Fix |
|---|---|---|
| Cases leave mouth down | tilt too flat, so mouth-down cases stay in the pockets | Fit the next steeper tilt link (`mount.fixed_tilts`: 45, 50, 55) or set the adjustable link steeper. Above 55 deg fit the wall extender |
| Cases fly over the wall | fill above 1 kg of brass (about 250 9mm cases), or tilt above 55 deg without the wall extender | Take brass off down to 1 kg. Above 55 deg fit the wall extender: it leans inward, 60 mm above the wall on the low side. The wall is never lower than 45 mm above the plate and 51 mm at the high end |
| Cases leave mouth down at every tilt | pocket too wide for the case | Smaller `case_plate.pocket_clearance`, or the plate set that matches the caliber |
| Pockets pass the exit empty | too little brass on the plate, or the tilt too steep | Add brass up to 1 kg (about 250 9mm cases). Go one tilt step flatter: at 62 deg the simulated rate is a quarter to a third of the rate at 45 deg |
| Few cases per hour | plate too slow | Turn the PWM knob up. The simulated rate at 45 deg rises from about 1,000 per hour at 0.75 rpm to 1,900 at 1.5 rpm |
| Cases ride past the exit | plate set for another caliber, cases sit too high in the pockets | Fit the plate set that matches the caliber |
| Plate stops, motor keeps turning | clutch slips: too much brass or a jam | Switch POWER off, then clear the jam. Do not leave the feeder running unattended: a jam does not stop the motor. If it slips with a normal fill, tighten the knob to the stop and check that all `clutch.springs_fitted` springs are in |
| Motor stalls or strains on a jam | clutch holds too much | Fit fewer springs (`clutch.springs_fitted`). The gearbox has no other protection |
| Cases jam at the exit | exit insert or gate not seated, or a case on its side | Switch POWER off first. Seat the exit insert on its ledge and the gate between the band ends. Check the plate set matches the caliber |
| Plate drags on the deck, or a case rim wedges under the plate | plate too low or too high over the deck: the hub was set with the untrimmed gauge, or the plate is warped, or the motor shaft has play | Switch the power switch off and unplug the 12 V supply first: the feeder starts by itself when the tube-full sensor clears. Then take cap, plate, knob, springs and disc off, repeat the trial fit of the assembly step "Drive ring and plate gap trial fit" and add the trim it gives to `clutch.gauge_trim`. If the highest and lowest of the four readings differ by more than the allowed range (0.15 to 0.75 mm for 9mm, so 0.6 mm), no trim fits them all: lay the plate on a flat surface and print it again if it rocks, clean the ring flange, and rock the plate rim up and down by hand to find shaft play |
| Two cases arrive at the exit together, or one stands upright on a pocket | a case stands on a pocket or is stacked above one | Set `track.wiper_h` (start value 1.5) and print the core again: a fixed arm over the plate before the exit knocks the case back. Fit it only if a print shows the fault |
| Cases jam in the hose | hose rises or loops | Switch POWER off first. Lay the hose downhill all the way, with no loops |
| Motor never stops with a full tube, or the stop test fails | sensor too far from the brass, sensor of the wrong type or leaking, timer relay not in mode P8, or relay contact stuck | Switch POWER off and do not run the feeder until the stop test passes. Screw the sensor in until its face touches the window, then tighten the lock nut. Fallback: thinner window (`drop_tube.window_t` 0.6). Check the sensor as on the [wiring](wiring.md) page and the module mode (P8). If both are right, replace the timer relay module |
| Motor stops and starts with every case | timer delay too short | Set a longer OP on the timer relay module, so only a full tube stops the motor |
| Motor does not start at low speed | PWM duty too low to start the gearbox | Turn the knob up until it starts, then back down to the lowest speed that still runs |
| Feeder turns on the stand tube | clamp loose | Tighten both clamp screws (on their washers) |
