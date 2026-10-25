"""One-command build: export every part to build/ as STL and STEP, then run the tests.

Run in the dev container from the project root:
    .venv/bin/python build.py              # build all parts, then pytest
    .venv/bin/python build.py --no-test    # build only
    .venv/bin/python build.py --assembly   # also build/assembly/: feeder.step, feeder.3mf, viewer.html
    .venv/bin/python build.py --variants   # also build/variants/<split>/: body and plate for each body split, with assembly
    .venv/bin/python build.py --plates     # also build/plates/<set>/: plate, exit insert, drop tube and its chain parts per plate
    .venv/bin/python build.py --configurator  # also build/configurator/: print files by content hash and manifest.json for the configurator (variants.py)
    .venv/bin/python build.py --guide      # also the build guide data and assembly for mkdocs build (mkdocs.yml)

build/<name>.stl and .step are in the modelled orientation, build/print/<name>.stl as the part goes on the bed.
"""

import argparse  # noqa: I001
import importlib
import pkgutil
import subprocess
import sys
from pathlib import Path

from dataclasses import replace

from build123d import export_step, export_stl

from feeder import printing
from feeder.config import CFG, Config

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"

SPLITS = ("arcs", "halves", "one_piece")


def iter_parts(cfg: Config = CFG, modules: tuple[str, ...] | None = None):
    """Yield (name, builder) from every feeder.parts module's PARTS mapping, or its parts(cfg) where the part
    set depends on the config. Each builder takes the config."""
    import feeder.parts  # noqa: PLC0415

    for info in pkgutil.iter_modules(feeder.parts.__path__):
        if modules is not None and info.name not in modules:
            continue
        module = importlib.import_module(f"feeder.parts.{info.name}")
        yield from (module.parts(cfg) if hasattr(module, "parts") else getattr(module, "PARTS", {})).items()


def build_all(cfg: Config = CFG, out: Path = BUILD, modules: tuple[str, ...] | None = None, parts=None) -> int:
    """Export the parts of `modules` (all by default), or the (name, builder) pairs in `parts`."""
    (out / "print").mkdir(parents=True, exist_ok=True)
    count = 0
    for name, builder in parts or iter_parts(cfg, modules):
        part = builder(cfg)
        export_stl(part, str(out / f"{name}.stl"))
        export_step(part, str(out / f"{name}.step"))
        export_stl(printing.on_bed(name, part, cfg), str(out / "print" / f"{name}.stl"))
        print(f"built {name}")
        count += 1
    return count


def plate_set_parts(cfg: Config) -> list:
    """The parts that belong to one plate: the rest of the feeder takes every plate."""
    from feeder.parts import body, case_plate, drop_chain, drop_tube  # noqa: PLC0415

    return [(f"case_plate_{cfg.case_plate.caliber}", case_plate.plate), ("body_exit_insert", body.exit_insert),
            ("drop_tube", drop_tube.drop_tube), *drop_chain.PARTS.items()]


def build_assembly(cfg: Config, out: Path, title: str) -> None:
    from feeder.export import export_assembly  # noqa: PLC0415

    for f in export_assembly(cfg, out, title):
        print(f"built {f.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-test", action="store_true", help="skip pytest")
    parser.add_argument("--assembly", action="store_true", help="also export the assembled feeder to build/assembly/")
    parser.add_argument("--variants", action="store_true", help="also build body and plate for each body split to build/variants/")
    parser.add_argument("--plates", action="store_true", help="also build each plate set to build/plates/")
    parser.add_argument("--configurator", action="store_true", help="also write every option combination's print files and manifest.json to build/configurator/")
    parser.add_argument("--guide", action="store_true", help="also write build/guide/buildguide.json and guide/generated/ for mkdocs build")
    args = parser.parse_args()
    print(f"{build_all()} parts in {BUILD}")
    if args.assembly:
        build_assembly(CFG, BUILD / "assembly", f"Body {CFG.body.split.replace('_', ' ')}, default configuration")
    if args.variants:
        for split in SPLITS:
            cfg = replace(CFG, body=replace(CFG.body, split=split))
            out = BUILD / "variants" / split
            print(f"{build_all(cfg, out, ('body', 'case_plate'))} parts in {out}")
            build_assembly(cfg, out / "assembly", f"Body {split.replace('_', ' ')}")
    if args.plates:
        from feeder.parts import layout  # noqa: PLC0415

        for cfg in layout.plate_sets(CFG):
            out = BUILD / "plates" / cfg.case_plate.caliber
            print(f"{build_all(cfg, out, parts=plate_set_parts(cfg))} parts in {out}")
    if args.configurator:
        import variants  # noqa: PLC0415

        variants.build_configurator()
    if args.guide:
        import json  # noqa: PLC0415

        from feeder import guide  # noqa: PLC0415

        build_assembly(CFG, ROOT / "guide" / "generated" / "assembly", f"Body {CFG.body.split.replace('_', ' ')}, default configuration")
        data = BUILD / "guide" / "buildguide.json"
        data.parent.mkdir(parents=True, exist_ok=True)
        data.write_text(json.dumps(guide.guide_data([name for name, _ in iter_parts(CFG)]), indent=1), encoding="utf-8")
        print(f"built {data.relative_to(ROOT)}")
        (ROOT / "guide" / "generated" / "steps.md").write_text(guide.steps_markdown(CFG), encoding="utf-8")
        (ROOT / "guide" / "generated" / "steps-detail.md").write_text(guide.steps_detail_markdown(CFG), encoding="utf-8")
    if args.no_test:
        return 0
    return subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT).returncode  # noqa: PLW1510


if __name__ == "__main__":
    raise SystemExit(main())
