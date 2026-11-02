"""Writes site/static/assets/social-card.png (1200 x 630), the link preview of the guide, from site/static/assets/logo.svg,
the light tokens of site/src/css/brand.css and the description and address in site/site.json. Run after changing any of
them (Playwright is not part of the locked environment, so install it for this run only):

    .venv/bin/pip install playwright==1.64.0 && .venv/bin/python -m playwright install chromium
    .venv/bin/python tools/social_card.py
"""

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "site/static/assets/social-card.png"
SIZE = {"width": 1200, "height": 630}


def light_tokens() -> dict[str, str]:
    """The custom properties of the first rule of brand.css, the light scheme."""
    css = (ROOT / "site/src/css/brand.css").read_text(encoding="utf-8")
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{3,8})\s*;", css.split("}", 1)[0]))


def site() -> dict[str, str]:
    """Title, description, address and repository of the guide (site/site.json, also read by site/docusaurus.config.ts)."""
    return json.loads((ROOT / "site/site.json").read_text(encoding="utf-8"))


def card_html() -> str:
    token = light_tokens()
    config = site()
    logo = (ROOT / "site/static/assets/logo.svg").read_text(encoding="utf-8")
    description = html.escape(config["description"])
    url = html.escape((config["url"] + config["baseUrl"]).removeprefix("https://").rstrip("/"))
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
