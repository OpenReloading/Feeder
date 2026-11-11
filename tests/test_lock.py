"""pylock.toml (what the environment installs) holds exactly the pins of requirements.txt (what Dependabot updates), and
the top-level pins repeated in pyproject.toml and docs/environment.md are the same versions."""

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
    assert locked == _pins(), "regenerate: python3 tools/lock.py"
    assert all(p["wheels"] and all(w["hashes"] for w in p["wheels"]) for p in lock["packages"])


def test_repeated_pins_match_requirements():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    repeated = [pin.split("==") for pin in project["dependencies"]]
    repeated += [pin.split("==") for extra in project["optional-dependencies"].values() for pin in extra]
    # rows `| name (note) | version |` of the package table; none once the table is gone
    rows = re.findall(r"^\| ([\w.-]+)(?: \(.*\))? \| (\d\S*) \|$", (ROOT / "docs/environment.md").read_text(), re.M)
    pins = _pins()
    assert [(name, version) for name, version in [*repeated, *rows] if pins.get(_name(name)) != version] == []
