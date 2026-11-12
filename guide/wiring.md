---
title: Wiring
---

# Wiring

!!! warning "Untested design"

    Seller listings disagree on the sensor output type (NPN normally closed in one, PNP normally open in another). Check the sensor as below before you wire it, and the relay module's mounting holes against `electronics.relay_holes`.

The 12 V supply feeds the PWM controller, the timer relay and the sensor through the switch, a 1 A time-lag fuse and a series diode that blocks a reversed supply. A second diode across the motor line, after the relay contact, clamps the kick when the contact opens. The motor runs through the relay contact (module mode P8, held while the sensor output is low), so it stops when brass stays in front of the sensor for longer than the relay delay, or when the sensor loses power or a wire breaks.

## Check the sensor on delivery

The listings do not agree on the output type, and this wiring needs NPN normally closed (brown +12 V, blue 0 V, black output). Power the sensor from the 12 V supply, put the 10 kΩ resistor between brown and black, set a multimeter to DC volts and read black to blue with no metal in front of the sensor face, then with a steel plate against it:

| No metal | Steel | Type |
|---|---|---|
| near 0 V | near 12 V | NPN normally closed: use it |
| near 12 V | near 0 V | NPN normally open: not for this wiring |
| near 12 V | near 12 V | PNP, or the output does not switch: not for this wiring |
| near 0 V | near 0 V | output stuck on: not for this wiring |

## Check the diodes before the fuse goes in

With the wiring done, the fuse out and the motor plug out, set the meter to the diode range. Red probe on pin 2 of the motor socket, black on pin 1: a low reading (about 0.1 to 0.4 V, estimate) through D2. Swap the probes: open. Open both ways means D2 is missing or open; low both ways is a short; the reverse pattern means D2 is the wrong way round, and it would short the controller output when the relay closes. D1 is right when its band points away from the fuse.

## First power-up, before the plate and the cap go on

Turn the knob to the lowest setting, plug in the motor and the sensor, keep metal away from the sensor face, fit the fuse and switch on. Turn the knob up until the motor turns.

1. **Direction.** The hub must turn counter-clockwise seen from above (`case_plate.direction` 1; clockwise for -1). If it does not, switch off, unplug the supply and swap the two cores at the motor terminals. Never swap them at the controller, the relay or the plugs: D2 sits on the box side of the plug, so the plug pins, the lid map and D2 stay correct.
2. **Sensor at the relay input.** Read the black core against the blue at the sensor socket's solder cups 3 and 2: the relay input is the sensor's load. With no metal in front the reading must be at most 0.2 V, the module's low-level limit (seller sheet), and the motor turns. A higher reading with the motor still: the sensor's on-state voltage is too high for the module, use another sensor. Hold a steel plate to the sensor face: the motor must stop after the relay delay and stay stopped for a minute. Take the steel away: it starts again. If the motor does not stop while the sensor's own LED changes, the sensor leaks enough current to hold the input: switch off, solder a 2.2 kΩ resistor from black to brown at the sensor socket's solder cups (0.07 W at 12 V, estimate) and test again. If it still does not stop, use another sensor.

## Motor noise on the sensor line

Keep the sensor cable apart from the motor cable down the stand, or cross it at right angles, and use a round two-core motor cable (BOM). At the first run, at each knob position: let the motor run with the sensor clear, then hold steel to the sensor face (or let the tube fill). The motor must stop after the relay delay and stay stopped for a minute. If the relay chatters, or the motor fails to stop at some knob positions only, solder a 0.1 µF ceramic capacitor across the motor terminals ([Pololu on motor noise](https://www.pololu.com/docs/0J15/9)). Fit it only if the test shows the fault.

The lid has the plug pin map and the polarity of the supply jack engraved in its outer face, from the same data as the board below: check a plug against it before you close the box.

<div data-buildguide="board" data-board="wiring"></div>
