"""Copies the configurator's print files and manifest.json (build.py --configurator, build/configurator/) into the
site, next to the configurator page. Without them the page says that the files are built on release."""

import logging
import shutil
from pathlib import Path

log = logging.getLogger("mkdocs.hooks.configurator_files")


def on_post_build(config):
    src = Path(config.config_file_path).parent / "build" / "configurator"
    if not (src / "manifest.json").exists():
        log.info("no variant files in %s: the configurator page shows none", src)
        return
    dest = Path(config.site_dir) / "configurator" / "data"
    dest.mkdir(parents=True, exist_ok=True)
    files = [*src.glob("*.stl"), src / "manifest.json"]
    for f in files:
        shutil.copy2(f, dest / f.name)
    log.info("copied %d variant files to %s", len(files), dest)
