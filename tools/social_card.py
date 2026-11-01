"""Writes guide/assets/social-card.png (1200 x 630), the link preview of the guide, from guide/assets/logo.svg, the light
tokens of guide/stylesheets/extra.css and site_description and site_url in mkdocs.yml. Run after changing any of them
(Playwright is not part of the locked environment, so install it for this run only):

    .venv/bin/pip install playwright==1.64.0 && .venv/bin/python -m playwright install chromium
    .venv/bin/python tools/social_card.py
"""

import html
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "guide/assets/social-card.png"
SIZE = {"width": 1200, "height": 630}


def light_tokens() -> dict[str, str]:
    """The custom properties of the first rule of extra.css, the light scheme."""
    css = (ROOT / "guide/stylesheets/extra.css").read_text(encoding="utf-8")
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{3,8})\s*;", css.split("}", 1)[0]))


def site_value(key: str) -> str:
    """A plain value of mkdocs.yml; for `!ENV [NAME, default]` the default."""
    text = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    value = re.search(rf"^{key}:\s*(.+)$", text, re.MULTILINE)
    if value is None:
        raise LookupError(key)
    env = re.fullmatch(r"!ENV \[\w+,\s*'([^']*)'\]", value.group(1).strip())
    return env.group(1) if env else value.group(1).strip()


def card_html() -> str:
    token = light_tokens()
    logo = (ROOT / "guide/assets/logo.svg").read_text(encoding="utf-8")
    description = html.escape(site_value("site_description"))
    url = html.escape(site_value("site_url").removeprefix("https://").rstrip("/"))
    return f"""<body style="margin:0;width:1200px;height:630px;position:relative;background:{token["page"]};
font:36px/1.4 system-ui,sans-serif;color:{token["ink"]}">
<div style="position:absolute;left:80px;top:80px;height:210px">{logo.replace("<svg ", '<svg height="210" ', 1)}</div>
<p style="position:absolute;left:80px;top:330px;width:1040px;margin:0">{description}</p>
<p style="position:absolute;left:80px;top:500px;margin:0;font:26px ui-monospace,monospace;color:{token["muted"]}">{url}</p>
<div style="position:absolute;left:0;bottom:0;width:1200px;height:24px;background:{token["accent"]}"></div></body>"""


def main() -> None:
    from playwright.sync_api import sync_playwright  # noqa: PLC0415 - only this script needs it, not the environment

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=SIZE)
        page.set_content(card_html())
        page.screenshot(path=OUT)
        browser.close()


if __name__ == "__main__":
    main()
