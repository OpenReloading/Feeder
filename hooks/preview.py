"""Development preview of the guide (mkdocs-preview.yml sets `extra.preview`; mkdocs.yml alone builds the released site).

The preview lives under `<site_url>develop/`: the hook moves `site_url` there and keeps the released address in
`extra.release_url` for the banner (overrides/main.html). After the build every HTML file gets a noindex tag, including
the standalone assembly viewer, and the sitemap is removed.
"""

import re
from pathlib import Path

SEGMENT = "develop/"
NOINDEX = '<meta name="robots" content="noindex">'
HEAD = re.compile(r"<head[^>]*>", re.I)
DOCTYPE = re.compile(r"<!doctype html>", re.I)  # the viewer page has no <head> tag


def on_config(config):
    if config.extra.get("preview"):
        config.extra["release_url"] = config.site_url
        config.site_url += SEGMENT
    return config


def on_post_build(config):
    if not config.extra.get("preview"):
        return
    site = Path(config.site_dir)
    for sitemap in site.glob("sitemap.xml*"):
        sitemap.unlink()
    for page in site.rglob("*.html"):
        html = page.read_text(encoding="utf-8")
        start = HEAD.search(html) or DOCTYPE.search(html)
        page.write_text(html[: start.end()] + NOINDEX + html[start.end() :] if start else NOINDEX + html, encoding="utf-8")
