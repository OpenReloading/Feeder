"""Logo, favicon and link preview of the guide: brass and slate tokens, both schemes, one card source."""

import re
from pathlib import Path

from tools import social_card

ROOT = Path(__file__).parent.parent
ASSETS = ROOT / "guide/assets"
OLD_GREENS = ("21634c", "72d6aa", "1b2622", "1f7a6d", "4fc2ae")


def _colors(path):
    return {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", path.read_text(encoding="utf-8"))}


def test_logo_and_favicon_use_only_the_site_tokens():
    tokens = _colors(ROOT / "guide/stylesheets/extra.css")
    for name in ("logo.svg", "logo-dark.svg", "favicon.svg"):
        text = (ASSETS / name).read_text(encoding="utf-8").lower()
        assert not any(green in text for green in OLD_GREENS), name
        assert _colors(ASSETS / name) <= tokens, name


def test_header_shows_the_wordmark_of_each_scheme():
    logo = (ROOT / "overrides/partials/logo.html").read_text(encoding="utf-8")
    assert "assets/logo.svg" in logo
    assert "assets/logo-dark.svg" in logo
    assert (ASSETS / "logo-dark.svg").exists()


def test_social_card_is_built_from_the_logo_tokens_and_description():
    card = social_card.card_html()
    tokens = social_card.light_tokens()
    assert tokens["page"] in card
    assert tokens["accent"] in card
    assert social_card.site_value("site_description").split(".")[0] in card
    assert "openreloading.github.io/Feeder" in card
    assert 'aria-label="OpenReloading Feeder"' in card
