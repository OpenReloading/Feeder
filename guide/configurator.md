---
title: Configurator
hide:
  - toc
---

<div class="page-intro" markdown>
<p class="feeder-hero__eyebrow">Print files</p>

# Configurator

Pick the options of your feeder. The page lists the parts to print and the parts to buy for that choice, and packs the print files into one zip in your browser.
</div>

!!! warning "Untested design"

    No feeder has been built from these files yet. Sizes marked unverified come from seller listings: measure on delivery.

<div id="configurator-unavailable" class="admonition warning" hidden>
<p class="admonition-title">No print files on this page</p>
<p>The print files are built when a release is published, so this copy of the site has none. You can still read the options. Build the files yourself with <code>build.py --configurator</code> (see docs/development.md in the repository).</p>
</div>

<div class="configurator">
<form id="configurator-form" autocomplete="off">
<fieldset>
<p><label>Body split
<select name="split">
<option value="arcs">arcs: core and three wall arcs</option>
<option value="halves">halves: two halves</option>
<option value="one_piece">one piece</option>
</select></label>
Plate, exit insert and gate follow the body.</p>

<p><label>Plate set
<select name="plate">
<optgroup label="Plate groups">
<option value="pocket_pistol">pocket pistol: 25 ACP, 32 ACP, 380 ACP</option>
<option value="small_pistol">small pistol: 9mm Makarov, 9mm Luger, 45 GAP, 9x21</option>
<option value="large_pistol">large pistol: 40 S&amp;W, 357 SIG, 45 ACP, 38 Super, 7.62x25, 10mm Auto</option>
<option value="revolver">revolver: 38 Special, 357 Magnum, 44 Special, 44 Magnum, 45 Colt</option>
</optgroup>
<optgroup label="Single caliber plates">
<option value="25_acp">25 ACP</option>
<option value="32_acp">32 ACP</option>
<option value="380_acp">380 ACP</option>
<option value="9mm_makarov">9mm Makarov</option>
<option value="9mm_luger" selected>9mm Luger</option>
<option value="9x21">9x21</option>
<option value="45_gap">45 GAP</option>
<option value="40_sw">40 S&amp;W</option>
<option value="357_sig">357 SIG</option>
<option value="38_super">38 Super</option>
<option value="45_acp">45 ACP</option>
<option value="10mm_auto">10mm Auto</option>
<option value="7_62x25">7.62x25</option>
<option value="38_special">38 Special</option>
<option value="44_special">44 Special</option>
<option value="357_magnum">357 Magnum</option>
<option value="44_magnum">44 Magnum</option>
<option value="45_colt">45 Colt</option>
</optgroup>
</select></label>
Changes the plate, the exit insert and the drop tube.</p>

<p><label>Wall extender
<select name="extender">
<option value="with">with: more wall over the low side</option>
<option value="without">without</option>
</select></label>
Adds the extender part and its screws and nuts.</p>

<p><label>Tilt link
<select name="link">
<option value="adjustable">adjustable: rod ends and a rod</option>
<option value="45">fixed, 45 deg</option>
<option value="50">fixed, 50 deg</option>
<option value="55">fixed, 55 deg</option>
</select></label>
A fixed link is one printed part. It sets the tilt, see <a href="../tilt/">Tilt and capacity</a>.</p>

<p><label>Stand tube
<select name="tube">
<option value="round">round</option>
<option value="square">square, 25 mm</option>
</select></label>
Changes the clamp and the electronics box.</p>

<p><label>Hub
<select name="hub">
<option value="pololu_2693">aluminium hub with tapped holes</option>
<option value="generic_8mm_flange">generic flange coupling, 8 mm bore</option>
</select></label>
Changes the clutch carrier and the body core, and adds hub screws and nuts for the flange.</p>
</fieldset>
</form>

<div id="configurator-result" hidden>
<h2>Print files</h2>
<p>Every part prints once.</p>

<table>
<thead><tr><th>Part</th><th>Prints</th><th>File size</th></tr></thead>
<tbody id="configurator-parts"></tbody>
</table>

<p class="configurator__actions"><button type="button" id="configurator-download" class="md-button md-button--primary">Download zip</button>
<span id="configurator-summary"></span> <span id="configurator-status" role="status"></span></p>
<h2>Parts to buy</h2>
<table data-stack>
<thead><tr><th>Group</th><th>Part</th><th>Qty</th><th>Used in</th></tr></thead>
<tbody id="configurator-bom"></tbody>
</table>
</div>
</div>

<noscript>The configurator needs JavaScript to list the parts and build the zip. The <a href="../bom/">BOM</a> lists the parts of the default feeder.</noscript>
