"""Configurator variants: every combination of the options that change parts, each printed part exported once per key
(the options it depends on) and stored once per content hash, plus a manifest for the build guide page.

Run in the dev container from the project root:
    .venv/bin/python build.py --configurator --no-test    # build/configurator/<hash>.stl and manifest.json

manifest.json: "options" (each option and its values), "parts" (per part name: "depends" on options and "files", the
STL hash per key), "bom" (bought parts: "depends" and "rows" per key). `resolve` reads it for one choice of options.
A key is the values of the options, in the order of "depends", joined by "/" (`*` for none). Part files are in the
orientation they go on the print bed.
"""

import hashlib
import itertools
import json
from dataclasses import replace
from pathlib import Path

from build123d import export_stl

import build
from feeder import guide, printing
from feeder.config import CFG, GENERIC_8MM_FLANGE, Config
from feeder.parts import body, mount

OPTIONS = {
    "split": build.SPLITS,
    "plate": (*CFG.calibers.groups, *CFG.calibers.table),  # plate set: a caliber group or one caliber
    "extender": ("with", "without"),
    "link": ("adjustable", *(f"{t:.0f}" for t in CFG.mount.fixed_tilts)),
    "tube": ("round", "square"),
    "hub": ("pololu_2693", "generic_8mm_flange"),
}

# part name prefix -> the options its geometry or presence depends on, checked by `plan` for presence and by
# tests/test_variants.py for geometry. The first matching prefix counts, so a part not listed fails the build.
DEPENDS = [
    ("body_core", ("split", "hub")),
    ("body_wall", ("split", "extender", "hub")),
    ("body_half", ("split", "plate", "extender", "hub")),
    ("body_extender", ("split", "extender", "hub")),
    ("body_track_gate", ("split", "hub")),
    ("body_exit_insert_blank", ("split", "hub")),
    ("body_exit_insert", ("split", "plate", "hub")),
    ("body", ("split", "plate", "extender", "hub")),
    ("case_plate", ("split", "plate")),
    ("drop_", ("plate",)),
    ("electronics_box", ("tube",)),
    ("electronics", ()),
    ("mount_yoke", ()),
    ("mount_clamp", ("tube",)),
    ("mount_rod_end", ("link",)),
    ("mount_link", ("link",)),
    ("slip_clutch_carrier", ("hub",)),
    ("slip_clutch_hub_gauge", ("hub",)),
    ("slip_clutch", ()),
]
BOM_DEPENDS = ("split", "extender", "link", "hub")


def combinations(options: dict = OPTIONS) -> list[dict]:
    return [dict(zip(options, values)) for values in itertools.product(*options.values())]  # noqa: B905


def config(choice: dict) -> Config:
    link = choice["link"]
    cfg = replace(
        CFG,
        body=replace(CFG.body, split=choice["split"], extender_h=CFG.body.extender_h if choice["extender"] == "with" else 0.0),
        case_plate=replace(CFG.case_plate, caliber=choice["plate"]),
        mount=replace(CFG.mount, tube_shape=choice["tube"], link=link if link == "adjustable" else float(link)),
    )
    return body.with_hub(cfg, {"pololu_2693": CFG.metal_hub, "generic_8mm_flange": GENERIC_8MM_FLANGE}[choice["hub"]])


def depends(name: str) -> tuple[str, ...]:
    return next(deps for prefix, deps in DEPENDS if name.startswith(prefix))


def key(deps: tuple[str, ...], choice: dict) -> str:
    return "/".join(choice[d] for d in deps) or "*"


def printed_parts(cfg: Config) -> dict:
    """Name and builder of every part printed for `cfg`: the plate set's parts under their plate's name, one kind of link."""
    angle = mount.link_angle(cfg)
    out = {n: b for n, b in build.iter_parts(cfg) if not n.startswith("case_plate_")} | dict(build.plate_set_parts(cfg))
    return {n: b for n, b in out.items()
            if (n.startswith("mount_rod_end") if angle is None else n == f"mount_link_{angle:.0f}") or not n.startswith(("mount_rod_end", "mount_link"))}


def plan(options: dict = OPTIONS) -> dict:
    """{part name: {key: first choice with that key}}. The names a choice has must follow from its key."""
    seen: dict = {}
    absent: dict = {}
    names_of = [(c, set(printed_parts(config(c)))) for c in combinations(options)]
    every = set().union(*(n for _, n in names_of))
    for choice, names in names_of:
        for name in every:
            k = key(depends(name), choice)
            (seen.setdefault(name, {}).setdefault(k, choice) if name in names else absent.setdefault(name, set()).add(k))
    for name, keys in absent.items():
        assert not keys & set(seen.get(name, ())), f"{name} is present for some choices and absent for others with the same key {keys & set(seen[name])}"
    return seen


def bom_rows(cfg: Config) -> list[dict]:
    """The bought parts for `cfg`: its fasteners from the assembly, the other parts from the BOM file. Rows of the file that
    belong to an option (the extender's fasteners, the rod of the adjustable link, the Pololu hub) follow the option."""
    rows = [r for r in guide.bom_items([], cfg)
            if r["group"] == "Fasteners" or not guide.FASTENER.match(r["part"]) or r["part"].startswith("DIN 976-1")]
    if mount.link_angle(cfg) is not None:  # printed link: no rod
        rows = [r for r in rows if not r["part"].startswith("DIN 976-1")]
    if cfg.metal_hub == GENERIC_8MM_FLANGE:
        rows = [dict(r, part="Generic 8 mm aluminium flange coupling, 4 clearance holes", spec="nuts under the flange. Unverified, measure on delivery")
                if r["part"].startswith("Pololu 2693") else r for r in rows]
    return rows


def _export(name: str, builder, cfg: Config, out: Path) -> str:
    """Write the print-bed STL of one part to out/<hash>.stl, once per content, and return the hash."""
    tmp = out / "part.tmp.stl"
    export_stl(printing.on_bed(name, builder(cfg), cfg), str(tmp))
    digest = hashlib.sha256(tmp.read_bytes()).hexdigest()[:16]
    final = out / f"{digest}.stl"
    tmp.replace(final) if not final.exists() else tmp.unlink()
    return digest


def build_configurator(out: Path = build.BUILD / "configurator", options: dict = OPTIONS) -> dict:
    """Export every part key of `options` to `out` and write out/manifest.json. Returns the manifest."""
    out.mkdir(parents=True, exist_ok=True)
    parts = {}
    for name, keys in sorted(plan(options).items()):
        deps = depends(name)
        files = {k: _export(name, printed_parts(config(c))[name], config(c), out) for k, c in keys.items()}
        parts[name] = {"depends": list(deps), "files": files}
        print(f"built {name}: {len(files)} keys, {len(set(files.values()))} files")
    bom = {key(BOM_DEPENDS, c): bom_rows(config(c)) for c in {key(BOM_DEPENDS, c): c for c in combinations(options)}.values()}
    manifest = {"options": {k: list(v) for k, v in options.items()}, "parts": parts, "bom": {"depends": list(BOM_DEPENDS), "rows": bom}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


def resolve(manifest: dict, choice: dict) -> tuple[dict, list[dict]]:
    """({part name: file hash}, BOM rows) of one choice of options."""
    parts = {}
    for name, p in manifest["parts"].items():
        k = key(tuple(p["depends"]), choice)
        if k in p["files"]:
            parts[name] = p["files"][k]
    return parts, manifest["bom"]["rows"][key(tuple(manifest["bom"]["depends"]), choice)]
