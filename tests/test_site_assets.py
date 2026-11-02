"""Logo, favicon and link preview of the guide: slate and blue tokens, both schemes, one card source."""

import html
import re
from pathlib import Path

from tools import social_card

ROOT = Path(__file__).parent.parent
ASSETS = ROOT / "site/static/assets"
OLD_GREENS = ("21634c", "72d6aa", "1b2622", "1f7a6d", "4fc2ae")


def _colors(path):
    return {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", path.read_text(encoding="utf-8"))}


def test_logo_and_favicon_use_only_the_site_tokens():
    tokens = _colors(ROOT / "site/src/css/brand.css")
    for name in ("logo.svg", "logo-dark.svg", "favicon.svg"):
        text = (ASSETS / name).read_text(encoding="utf-8").lower()
        assert not any(green in text for green in OLD_GREENS), name
        assert _colors(ASSETS / name) <= tokens, name


def test_black_and_white_variants_are_one_colour():
    for name, color in (("logo-black.svg", "#000"), ("logo-white.svg", "#fff"), ("mark-black.svg", "#000"), ("mark-white.svg", "#fff")):
        text = (ASSETS / name).read_text(encoding="utf-8")
        assert f'color="{color}"' in text, name
        assert not re.findall(r'(?:fill|stroke)="#', text), name


def test_header_shows_the_wordmark_of_each_scheme():
    config = (ROOT / "site/docusaurus.config.ts").read_text(encoding="utf-8")
    assert "src: 'assets/logo.svg', srcDark: 'assets/logo-dark.svg'" in config
    assert (ASSETS / "logo-dark.svg").exists()


def test_social_card_is_built_from_the_logo_tokens_and_description():
    card = social_card.card_html()
    tokens = social_card.light_tokens()
    assert tokens["page"] in card
    assert tokens["accent"] in card
    assert html.escape(social_card.site()["description"]) in card
    assert "openreloading.github.io/Feeder" in card
    assert 'aria-label="OpenReloading Feeder"' in card


def test_site_address_is_the_pages_address():
    site = social_card.site()
    assert site["url"] + site["baseUrl"] == "https://openreloading.github.io/Feeder/"
