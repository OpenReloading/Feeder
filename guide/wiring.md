---
title: Wiring
---

# Wiring

!!! warning "Untested design"

    Seller listings disagree on the sensor output type (NPN normally closed in one, PNP normally open in another). Check the sensor as below before you wire it, and the relay module's mounting holes against `electronics.relay_holes`.

The 12 V supply feeds the PWM controller, the timer relay and the sensor through the switch, a 3.15 A fuse and a series diode that blocks a reversed supply. A second diode across the motor plug clamps the kick when the relay contact opens. The motor runs through the relay contact (module mode P8, held while the sensor output is low), so it stops when brass stays in front of the sensor for longer than the relay delay, or when the sensor loses power or a wire breaks.

## Check the sensor on delivery

The listings do not agree on the output type, and this wiring needs NPN normally closed (brown +12 V, blue 0 V, black output). Power the sensor from the 12 V supply, set a multimeter to continuity, and test with no metal in front of the sensor face, then with a steel plate against it:

| Black to blue | Black to brown | Type |
|---|---|---|
| continuity, opens with the steel | no continuity | NPN normally closed: use it |
| no continuity, closes with the steel | no continuity | NPN normally open: not for this wiring |
| any | continuity | PNP: not for this wiring |

Then put a 10 kΩ resistor between brown and black and read black to blue with no metal in front: it must stay below 0.2 V, the low-level limit of the timer relay module (seller sheet). A higher reading means the module may not trigger: use another sensor.

The lid has the plug pin map and the polarity of the supply jack engraved in its outer face, from the same data as the board below: check a plug against it before you close the box.

<div data-buildguide="board" data-board="wiring"></div>
