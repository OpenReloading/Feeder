"""The configurator page offers exactly the options of the variant manifest, each value once."""

from html.parser import HTMLParser
from pathlib import Path

import variants

PAGE = Path(__file__).parent.parent / "guide" / "configurator.md"


class Selects(HTMLParser):
    def __init__(self):
        super().__init__()
        self.options: dict = {}
        self._select = None

    def handle_starttag(self, tag, attrs):
        if tag == "select":
            self._select = dict(attrs)["name"]
            self.options[self._select] = []
        elif tag == "option":
            self.options[self._select].append(dict(attrs)["value"])


def test_page_options_match_the_manifest_options():
    page = Selects()
    page.feed(PAGE.read_text(encoding="utf-8"))
    assert page.options == {name: list(values) for name, values in variants.OPTIONS.items()}
    assert all(len(set(values)) == len(values) for values in page.options.values())
