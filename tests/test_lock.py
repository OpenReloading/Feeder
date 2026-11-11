"""pylock.toml (what the environment installs) holds exactly the pins of requirements.txt (what Dependabot updates), and
the top-level pins repeated in pyproject.toml and docs/environment.md are the same versions."""

import itertools
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _name(raw):
    return raw.lower().replace("_", "-")


def _pins():
    lines = (ROOT / "requirements.txt").read_text().splitlines()
    return {_name(name): version for name, version in (line.strip().split("==") for line in lines if "==" in line)}


def test_lock_matches_requirements_pins():
    lock = tomllib.loads((ROOT / "pylock.toml").read_text())
    locked = {_name(p["name"]): p["version"] for p in lock["packages"]}
    assert locked == _pins(), "regenerate: python3 tools/lock.py (a package only in the lock is a new dependency: pin it in requirements.txt)"
    # wheels only, hashed and from PyPI: an older uv also locks source distributions, an index set in the environment its own URLs
    other = [
        p["name"] for p in lock["packages"]
        if "sdist" in p or not p.get("wheels") or not all(w["hashes"] and w["url"].startswith("https://files.pythonhosted.org/") for w in p["wheels"])
    ]
    assert other == [], "regenerate with uv 0.10 or newer: python3 tools/lock.py"


def test_repeated_pins_match_requirements():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    repeated = [pin.split("==") for pin in project["dependencies"]]
    repeated += [pin.split("==") for extra in project["optional-dependencies"].values() for pin in extra]
    # every row of the package table `| name (note) | version |`, none once the table is gone
    lines = [line.strip() for line in (ROOT / "docs/environment.md").read_text().splitlines()]
    header = next((i for i, s in enumerate(lines) if s.replace(" ", "").startswith("|Package|Version|")), None)
    table = [] if header is None else lines[header + 2:]
    cells = [[c.strip().strip("`") for c in line.strip("|").split("|")] for line in itertools.takewhile(lambda s: s.startswith("|"), table)]
    assert all(len(c) == 2 for c in cells), "docs/environment.md: a package row needs exactly two cells"
    rows = [(re.sub(r" \(.*\)$", "", name), version) for name, version in cells]
    pins = _pins()
    assert [(name, version) for name, version in [*repeated, *rows] if pins.get(_name(name)) != version] == []
