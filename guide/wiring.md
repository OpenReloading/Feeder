---
title: Wiring
---

# Wiring

!!! warning "Untested design"

    The sensor output type and the relay input are unverified: check both against the parts you bought before the first power-up.

The 12 V supply feeds the PWM controller, the timer relay and the sensor. The motor runs through the relay's normally open contact, so it stops when brass stays in front of the sensor for longer than the relay delay, or when the sensor loses power or a wire breaks.

<div data-buildguide="board" data-board="wiring"></div>
