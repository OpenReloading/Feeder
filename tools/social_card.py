"""Writes guide/assets/social-card.png (1200 x 630), the link preview of the guide, from guide/assets/logo.svg, the light
tokens of guide/stylesheets/extra.css and site_description and site_url in mkdocs.yml. Run after changing any of them
(Playwright is not part of the locked environment, so install it for this run only):

    .venv/bin/pip install playwright==1.64.0 && .venv/bin/python -m playwright install chromium
    .venv/bin/python tools/social_card.py
"""

import html
import json
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
    """A top-level scalar of mkdocs.yml (plain, single or double quoted, with or without a trailing comment);
    for `!ENV [NAME, default]` the default."""
    text = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    match = re.search(rf"^{re.escape(key)}:(.*)$", text, re.MULTILINE)
    if match is None:
        raise LookupError(key)
    raw = match.group(1).strip()
    if raw.startswith("!ENV"):
        inner = raw.removeprefix("!ENV").lstrip()
        if not inner.startswith("[") or "," not in inner:
            raise ValueError(raw)
        value, rest = _scalar(inner[inner.index(",") + 1 :].lstrip(), flow=True)
        rest = rest.lstrip()
        if not rest.startswith("]"):
            raise ValueError(raw)
        _expect_comment(rest[1:])
        return value
    value, rest = _scalar(raw, flow=False)
    _expect_comment(rest)
    return value


def _scalar(raw: str, *, flow: bool) -> tuple[str, str]:
    """The scalar at the start of raw and the text after it."""
    if raw.startswith("'"):
        parts, i = [], 1
        while True:
            end = raw.index("'", i)
            parts.append(raw[i:end])
            if raw[end + 1 : end + 2] != "'":
                return "".join(parts), raw[end + 1 :]
            parts.append("'")
            i = end + 2
    if raw.startswith('"'):
        i = 1
        while raw[i] != '"':
            i += 2 if raw[i] == "\\" else 1
        return json.loads(raw[: i + 1]), raw[i + 1 :]  # YAML double-quoted escapes are a superset of JSON's
    ends = [i for i in (raw.find(" #"), raw.find("\t#")) if i >= 0]
    if flow:
        ends += [i for i in (raw.find(","), raw.find("]")) if i >= 0]
    end = min(ends, default=len(raw))
    return raw[:end].strip(), raw[end:]


def _expect_comment(rest: str) -> None:
    rest = rest.strip()
    if rest and not rest.startswith("#"):
        raise ValueError(rest)


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
