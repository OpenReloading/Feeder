---
title: Introduction
hide:
  - toc
---

<div class="feeder-hero" markdown>
<div class="feeder-hero__text" markdown>
<p class="feeder-hero__eyebrow">Parametric brass collator for reloading</p>

# Build a 9mm case feeder

<p class="feeder-hero__lead">A tilted plate turns under loose brass and drops the cases base down into a hose to the press. Every part is generated from <code>feeder/config.py</code> and exported as STL and STEP.</p>
<p class="feeder-hero__actions"><a class="md-button md-button--primary" href="configurator/">Open the configurator</a> <a class="md-button" href="#how-to-start">Read the build guide</a></p>
</div>
<figure class="feeder-hero__figure">
--8<-- "guide/generated/side-view.md"
</figure>
</div>

!!! warning "Untested design"

    No feeder has been built from these files yet. Sizes marked unverified come from seller listings: measure on delivery.

<div class="feeder-intro" markdown>

## What it is, and who it is for

<div class="feeder-cards" markdown>
<div class="feeder-card" markdown>
<p class="feeder-card__label">WHAT IT IS</p>

Brass goes into the bowl in any orientation, up to 1 kg (about 250 9mm cases). An inductive sensor stops the motor when the tube is full.
</div>
<div class="feeder-card" markdown>
<p class="feeder-card__label">WHO IT IS FOR</p>

For reloaders who 3D print their own tools and can buy a gear motor, an M18 inductive sensor and metric DIN/ISO hardware. The default feeder holds up to 1 kg of brass (about 250 9mm cases) and prints on a 256 mm bed.
</div>
<div class="feeder-card" markdown>
<p class="feeder-card__label">HOW IT WORKS</p>

The plate pockets take base-down cases. Mouth-down cases sit high and fall back at the tilt. Cases leave base down (mouth up) through the drop tube.
</div>
</div>

![Render of the assembled feeder on its tilt mount](assets/feeder-light.png#only-light)
![Render of the assembled feeder on its tilt mount](assets/feeder-dark.png#only-dark)

## What you get

<div class="feeder-rows" markdown>

1. [Configurator](configurator.md): it shows the options. It lists parts and packs print files only on a site you build yourself after `build.py --configurator` (docs/development.md in the repository). Print files are not published until a first feeder is built and tested.
1. [BOM](bom.md): tick the parts off.
--8<-- "guide/generated/assembly-row.md"
1. [Wiring](wiring.md) of the electronics box.
1. [Safety and first run](safety.md): how to stop it, what goes into the bowl, the stop test before each session and the first-run checks.
1. [Tilt and capacity](tilt.md) lists when to go steeper and the capacity per angle.
1. [Troubleshooting](troubleshooting.md) lists symptoms, causes and the config value or part to change.

</div>

## Plate sets for 18 calibers

Plates for 18 pistol and revolver calibers fit the same body. Pick one in the [configurator](configurator.md).

--8<-- "guide/generated/plate-groups.md"

## Start at 45 degrees

<div class="feeder-tilt" markdown>

--8<-- "docs/design.md:tilt-table"

</div>

Fill at most 1 kg of brass (about 250 9mm cases) on any plate set.

## How to start

<div class="feeder-cards feeder-steps" markdown>
<div class="feeder-card" markdown>
<p class="feeder-card__label">01</p>

Read the status: no feeder has been built from these files yet. Tick the parts off on the [BOM](bom.md).
</div>
<div class="feeder-card" markdown>
<p class="feeder-card__label">02</p>

Pick your options in the [configurator](configurator.md).
</div>
<div class="feeder-card" markdown>
<p class="feeder-card__label">03</p>

Print the parts, then follow the [assembly steps](assembly.md).
</div>
<div class="feeder-card" markdown>
<p class="feeder-card__label">04</p>

Read [safety and first run](safety.md) before the first power-up, set the [tilt](tilt.md) last, and look at [troubleshooting](troubleshooting.md) when it does not work.
</div>
</div>

<p class="feeder-intro__actions"><a class="md-button md-button--primary" href="configurator/">Open the configurator</a> <a class="md-button" href="assembly/">See the assembly steps</a> <a class="md-button" href="bom/">BOM checklist</a> <a class="md-button" href="troubleshooting/">Troubleshooting</a></p>

</div>

## Assembly steps

--8<-- "guide/generated/steps.md"

## When it does not work

[Troubleshooting](troubleshooting.md) lists symptoms, causes and the config value or part to change.

## Printing

Every printed part prints without supports, except a few small support islands on the body core, the drop tube and the clamp. Print orientation STLs come from build.py (`build/print/`).
