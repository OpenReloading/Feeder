"""The development preview of the guide: hooks/preview.py and mkdocs-preview.yml. The released site must not change."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from hooks import preview

ROOT = Path(__file__).resolve().parents[1]

RELEASED = "https://openreloading.github.io/Feeder/"


def _config(site_dir, **extra):
    return SimpleNamespace(site_url=RELEASED, site_dir=str(site_dir), extra=extra)


def test_preview_config_inherits_the_released_one_and_only_sets_the_flag():
    lines = [line for line in (ROOT / "mkdocs-preview.yml").read_text().splitlines() if not line.startswith("#")]
    assert lines == ["INHERIT: mkdocs.yml", "extra:", "  preview: true"]


def test_released_build_loads_the_hook_and_keeps_its_site_url():
    text = (ROOT / "mkdocs.yml").read_text()
    assert "hooks/preview.py" in text
    assert f"site_url: {RELEASED}\n" in text


def test_preview_site_url_is_under_develop_and_the_banner_links_the_released_site():
    config = preview.on_config(_config(Path(), preview=True))
    assert config.site_url == RELEASED + "develop/"
    assert config.extra["release_url"] == RELEASED


def test_released_build_is_left_alone(tmp_path):
    (tmp_path / "index.html").write_text("<html><head></head></html>")
    (tmp_path / "sitemap.xml").write_text("<urlset/>")
    config = _config(tmp_path)
    assert preview.on_config(config).site_url == RELEASED
    preview.on_post_build(config)
    assert (tmp_path / "index.html").read_text() == "<html><head></head></html>"
    assert (tmp_path / "sitemap.xml").exists()


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        ("<!doctype html><html><head><title>t</title></head></html>", f"<!doctype html><html><head>{preview.NOINDEX}<title>t</title></head></html>"),
        ('<html><head lang="en"><title>t</title>', f'<html><head lang="en">{preview.NOINDEX}<title>t</title>'),
        ("<!DOCTYPE html>\n<title>viewer</title>", f"<!DOCTYPE html>{preview.NOINDEX}\n<title>viewer</title>"),  # no <head> tag
        ("<p>fragment</p>", f"{preview.NOINDEX}<p>fragment</p>"),
    ],
)
def test_preview_marks_every_html_file_noindex_and_drops_the_sitemap(tmp_path, html, expected):
    (tmp_path / "a" / "b").mkdir(parents=True)
    pages = [tmp_path / "index.html", tmp_path / "a" / "b" / "viewer.html"]
    for page in pages:
        page.write_text(html)
    (tmp_path / "sitemap.xml").write_text("<urlset/>")
    (tmp_path / "sitemap.xml.gz").write_bytes(b"x")
    (tmp_path / "data.json").write_text("{}")
    preview.on_post_build(_config(tmp_path, preview=True))
    assert [page.read_text() for page in pages] == [expected, expected]
    assert not list(tmp_path.glob("sitemap*"))
    assert (tmp_path / "data.json").read_text() == "{}"

