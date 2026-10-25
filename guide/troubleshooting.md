---
title: Troubleshooting
---

# Troubleshooting

Find the symptom, try the first fix, then the next. Config values are in `feeder/config.py`; rebuild the changed parts with `build.py`.

| Symptom | Likely cause | Fix |
|---|---|---|
| Cases leave mouth down | tilt too flat, so mouth-down cases stay in the pockets | Fit the next steeper tilt link (`mount.fixed_tilts`: 45, 50, 55) or set the adjustable link steeper. Above 55 deg fit the wall extender |
| Cases fly over the wall | fill above about 250 9mm cases, or tilt above 55 deg without the wall extender | Take brass off down to 250 cases. Above 55 deg fit the wall extender: it leans inward, 60 mm above the wall on the low side. The wall is never lower than 45 mm above the plate and 51 mm at the high end |
| Cases leave mouth down at every tilt | pocket too wide for the case | Smaller `case_plate.pocket_clearance`, or the plate set that matches the caliber |
| Pockets pass the exit empty | too little brass on the plate, or the tilt too steep | Add brass up to about 250 9mm cases. Go one tilt step flatter: at 62 deg the simulated rate is a quarter to a third of the rate at 45 deg |
| Few cases per hour | plate too slow | Turn the PWM knob up. The simulated rate at 45 deg rises from about 1,000 per hour at 0.75 rpm to 1,900 at 1.5 rpm |
| Cases ride past the exit | plate set for another caliber, cases sit too high in the pockets | Fit the plate set that matches the caliber |
| Plate stops, motor keeps turning | clutch slips: too much brass or a jam | Clear the jam. If it slips with a normal fill, tighten the knob to the stop and check that all `clutch.springs_fitted` springs are in |
| Motor stalls or strains on a jam | clutch holds too much | Fit fewer springs (`clutch.springs_fitted`). The gearbox has no other protection |
| Cases jam at the exit | exit insert or gate not seated, or a case on its side | Seat the exit insert on its ledge and the gate between the band ends. Check the plate set matches the caliber |
| Two cases arrive at the exit together, or one stands upright on a pocket | a case stands on a pocket or is stacked above one | Set `track.wiper_h` (start value 1.5) and print the core again: a fixed arm over the plate before the exit knocks the case back. Fit it only if a print shows the fault |
| Cases jam in the hose | hose rises or loops | Lay the hose downhill all the way, with no loops |
| Motor never stops with a full tube | sensor too far from the brass | Screw the sensor in until its face touches the window, then tighten the lock nut. Fallback: thinner window (`drop_tube.window_t` 0.6) |
| Motor stops and starts with every case | timer delay too short | Set a longer OP on the timer relay module, so only a full tube stops the motor |
| Motor does not start at low speed | PWM duty too low to start the gearbox | Turn the knob up until it starts, then back down to the lowest speed that still runs |
| Feeder turns on the stand tube | clamp loose | Tighten both clamp screws (on their washers) |
