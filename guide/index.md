---
title: Introduction
---

# 9mm case feeder

!!! warning "Untested design"

    No feeder has been built from these files yet. Sizes marked unverified come from seller listings: measure on delivery.

A tilted plate turns under loose brass and drops the cases base down, one at a time, into a hose to the press.

## What it does

- Brass goes into the bowl in any orientation, up to 250 9mm cases.
- The plate pockets take base-down cases. Mouth-down cases sit high and fall back at the tilt.
- Cases leave base down (mouth up) through the drop tube. An inductive sensor stops the motor when the tube is full.
- Plate sets for 18 pistol and revolver calibers fit the same body.

## Build

Tick the parts off on the [BOM](bom.md) page, then follow the [assembly steps](assembly.md):

--8<-- "guide/generated/steps.md"

## Tilt

Start at 45 deg. [Tilt and capacity](tilt.md) lists when to go steeper, the sources and the capacity per angle.

## When it does not work

[Troubleshooting](troubleshooting.md) lists symptoms, causes and the config value or part to change.

## Printing

Every printed part prints without supports, except a few small support islands on the body core, the drop tube and the clamp. Print orientation STLs come from build.py (`build/print/`).
