---
title: Safety and first run
---

# Safety and first run

Read this before the first power-up. The feeder has no emergency stop, and a plate that stands still can start again by itself.

## How to stop it

Switch POWER off on the lid, or pull the 12 V plug out of the jack. Either stops the motor at once, and the worm gear holds the plate.

A still plate is not a switched-off feeder. The motor stops when the tube is full and starts again by itself as soon as the press takes a case. The lid has no power light yet. Until it has one: at the first power-up (first-run step 2), mark the lever position in which the plate turns as ON on the lid. If you are not sure, pull the plug.

Switch POWER off before you reach into the bowl, clear a jam, take the cap off, change the plate or the tilt, or open the box.

## Every session

- Only empty brass without a live primer goes into the bowl (fired cases with the spent primer are fine): no loaded rounds, no live primers, no powder.
- Keep powder, primers and loaded rounds off and away from the feeder. The motor has brushes, and the switch and the relay make and break 12 V inside the box: sparks, heat and static can set off primers and powder ([SAAMI on primers](https://saami.org/wp-content/uploads/2025/08/Info-Doc-Primers-11-8-2022.pdf), [SAAMI on smokeless powder](https://saami.org/wp-content/uploads/2025/08/Info-Doc-Smokeless-Powder-11-8-2022.pdf)).
- Cases can pick up static charge in the plastic bowl and the clear hose, and the hose does not conduct, so they can reach the press charged, next to its primer feed. Ground the press electrically (protective earth). Before each session, wipe primer dust off the press and the loading area next to it with a damp cloth or sponge, and rinse the cloth or sponge after each use, as the SAAMI primer leaflet asks.
- Fill at most 1 kg of brass (about 250 9mm cases) on any plate set. The clutch, cap and mount checks assume no more.
- Keep your fingers out of the bowl while the plate turns. The plate notches shear past the band, the gate and the drop opening. The clutch limits the force, it does not stop the motor.
- Never leave the feeder running unattended, and switch it off when you leave the bench. Only a full tube stops the motor: a jam in the bowl or at the exit does not, and the clutch then slips without end and warms up inside the cap.
- Fired brass carries lead residue. Wash your hands after handling it, and do not eat or drink at the bench ([OSHA fact sheet](https://www.osha.gov/sites/default/files/publications/OSHA3772.pdf)).

## Test the stop before each session

The stop is the only thing that ends a run on its own, and a faulty sensor or a stuck relay contact leaves the motor running with nothing to show it.

1. With the hose on the press and the press not taking cases, switch POWER on and watch the first fill.
2. When the cases stand in front of the sensor window, the plate must stop within the relay delay (OP on the timer relay, about 2 s).
3. Take cases out at the press until the plate starts again. If it does not start with the tube empty above the sensor, treat it as a failed test.

If the plate does not stop, or does not start again, switch POWER off and do not run the feeder until the cause is fixed ([troubleshooting](troubleshooting.md)).

## First run

Do these once, in this order, after the [wiring](wiring.md) and before the first session. The bowl stays empty until step 4.

1. **Clutch slip.** Unplug the 12 V supply. Hook a luggage scale into a plate notch and pull along the rim until the plate turns on the clutch; the worm gear holds the motor side. Pull as flat and as close to the rim direction as the wall allows; a pull at an angle reads high. Read the highest force. Slip torque is that force times 0.115 m. It must be at most 2.1 Nm (estimate), a reading of at most 18 N (1.8 kg on the scale). Above that, take out two opposite springs (4 left) and test again. If it is still above, fit three springs in every other pocket. Never fewer than three: if three still read above the limit, do not run the feeder. Set `clutch.springs_fitted` to the number fitted. Test again after the feeder has stood for a week: printed faces can stick.
2. **Lowest speed.** Turn the knob to its lowest setting and move the POWER lever to one side. Turn the knob up until the plate turns. If it does not turn at any setting, turn the knob back down, move the lever to the other side and turn up again. Mark that lever position as ON on the lid. Turn the knob back down to the lowest setting that still runs. Switch POWER off.
3. **Tilt.** Set 45 deg as on the [tilt page](tilt.md), with the bowl empty.
4. **Stop test.** Fill up to 1 kg of brass and run the stop test above.
