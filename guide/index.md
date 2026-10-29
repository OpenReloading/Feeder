---
title: Introduction
hide:
  - toc
---

<div class="feeder-hero">
<div class="feeder-hero__text">
<p class="feeder-hero__eyebrow">Parametric brass collator for reloading</p>
<h1>Build a 9mm case feeder</h1>
<p class="feeder-hero__lead">A tilted plate turns under loose brass and drops the cases base down into a hose to the press. Every part is generated from <code>feeder/config.py</code> and exported as STL and STEP.</p>
<p class="feeder-hero__actions"><a class="md-button md-button--primary" href="configurator/">Open the configurator</a> <a class="md-button" href="#start-here">Read the build guide</a></p>
</div>
<figure class="feeder-hero__figure">
<svg class="feeder-hero__drawing" viewBox="0 0 480 444" role="img" aria-label="Side view of the feeder: the plate with cases inside the wall, the body core, the motor, the tilt link, the stand tube, the drop tube and the optional extender">
<g aria-hidden="true">
<g transform="translate(230 210) rotate(-45)">
<path d="M -100 -100 V 14 H 100 V -100"/>
<path class="feeder-hero__optional" d="M -100 -100 V -135 M 100 -100 V -135"/>
<rect x="-92" y="-8" width="184" height="8"/>
<path class="feeder-hero__cases" d="M -82 -8 v -14 h 9 v 14 M -60 -8 v -14 h 9 v 14 M -38 -8 v -14 h 9 v 14 M -16 -8 v -14 h 9 v 14 M 6 -8 v -14 h 9 v 14 M 28 -8 v -14 h 9 v 14 M 50 -8 v -14 h 9 v 14 M 72 -8 v -14 h 9 v 14 M -92 -22 h 14 v -9 h -14 z M -76 -22 h 14 v -9 h -14 z M -90 -31 h 14 v -9 h -14 z"/>
<path d="M -100 14 L -60 50 H 60 L 100 14"/>
<rect x="-24" y="50" width="48" height="70"/>
</g>
<path d="M 146 267 V 390 M 162 283 V 390"/>
<path d="M 309 176 L 400 220 M 394 220 V 390 M 406 220 V 390 M 375 390 H 425"/>
<circle cx="309" cy="176" r="4"/>
<circle cx="400" cy="220" r="4"/>
<g class="feeder-hero__labels">
<path d="M 292 142 L 326 114 M 196 290 L 200 422 M 315 295 L 300 404 M 354 198 L 378 170 M 406 370 L 420 420 M 154 392 L 118 406 M 217 56 L 232 36"/>
<text x="330" y="114">01 Plate</text>
<text x="132" y="438">02 Body core</text>
<text x="262" y="420">03 Motor</text>
<text x="360" y="165">04 Tilt link</text>
<text x="350" y="438">05 Stand tube</text>
<text x="8" y="420">06 Drop tube</text>
<text x="230" y="32">07 Extender, optional</text>
</g>
</g>
</svg>
<ul class="feeder-hero__parts">
<li>01 Plate</li>
<li>02 Body core</li>
<li>03 Motor</li>
<li>04 Tilt link</li>
<li>05 Stand tube</li>
<li>06 Drop tube</li>
<li>07 Extender, optional</li>
</ul>
<figcaption>Start at 45 deg. Schematic, not to scale.</figcaption>
</figure>
</div>

![Render of the assembled feeder on its tilt mount](assets/feeder-light.png#only-light)
![Render of the assembled feeder on its tilt mount](assets/feeder-dark.png#only-dark)

!!! warning "Untested design"

    No feeder has been built from these files yet. Sizes marked unverified come from seller listings: measure on delivery.

## Start here

Pick your options in the [configurator](configurator.md), tick the parts off on the [BOM](bom.md), then follow the [assembly steps](assembly.md). Set the [tilt](tilt.md) last, and look at [troubleshooting](troubleshooting.md) when it does not work.

## What it does

- Brass goes into the bowl in any orientation, up to 250 9mm cases.
- The plate pockets take base-down cases. Mouth-down cases sit high and fall back at the tilt.
- Cases leave base down (mouth up) through the drop tube. An inductive sensor stops the motor when the tube is full.
- Plate sets for 18 pistol and revolver calibers fit the same body.

## Assembly steps

--8<-- "guide/generated/steps.md"

## Tilt

Start at 45 deg. [Tilt and capacity](tilt.md) lists when to go steeper and the capacity per angle.

## When it does not work

[Troubleshooting](troubleshooting.md) lists symptoms, causes and the config value or part to change.

## Printing

Every printed part prints without supports, except a few small support islands on the body core, the drop tube and the clamp. Print orientation STLs come from build.py (`build/print/`).
