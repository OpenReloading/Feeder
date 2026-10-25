"""pylock.toml (what the environment installs) holds exactly the pins of requirements.txt (what Dependabot updates)."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _name(raw):
    return raw.lower().replace("_", "-")


def test_lock_matches_requirements_pins():
    lock = tomllib.loads((ROOT / "pylock.toml").read_text())
    locked = {_name(p["name"]): p["version"] for p in lock["packages"]}
    pins = dict(
        line.strip().split("==")
        for line in (ROOT / "requirements.txt").read_text().splitlines()
        if "==" in line
    )
    pinned = {_name(n): v for n, v in pins.items()}
    assert locked == pinned, "regenerate: pip lock --only-binary :all: -r requirements.txt -o pylock.toml"
    assert all(p["wheels"] and all(w["hashes"] for w in p["wheels"]) for p in lock["packages"])
