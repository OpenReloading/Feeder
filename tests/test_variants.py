"""Configurator variants: the manifest covers every option combination, its files exist and are stored once per
content, and a part's geometry follows only the options it is keyed by."""

import hashlib
import json

import pytest

import variants
from variants import combinations, config, depends, key, printed_parts

SMALL = {**variants.OPTIONS, "plate": ("9mm_luger",), "link": ("adjustable", "50")}  # real builds: a plate set is the slow part
FIRST = {name: values[0] for name, values in SMALL.items()}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("configurator")
    return out, variants.build_configurator(out, SMALL)


def test_manifest_covers_every_combination(built):
    out, manifest = built
    assert json.loads((out / "manifest.json").read_text()) == manifest
    assert manifest["options"] == {k: list(v) for k, v in SMALL.items()}
    for choice in combinations(SMALL):
        parts, bom = variants.resolve(manifest, choice)
        assert set(parts) == set(printed_parts(config(choice))), choice
        assert bom, choice


def test_every_referenced_file_exists_and_is_named_by_its_content(built):
    out, manifest = built
    hashes = {h for p in manifest["parts"].values() for h in p["files"].values()}
    assert {f.stem for f in out.glob("*.stl")} == hashes  # nothing missing, no orphan
    for h in hashes:
        assert hashlib.sha256((out / f"{h}.stl").read_bytes()).hexdigest().startswith(h)


def test_identical_parts_share_one_file(built):
    out, manifest = built
    files = manifest["parts"]["body_track_gate"]["files"]
    assert len(files) == 6 and len(set(files.values())) == 4  # split x hub: the arcs and halves gates are the same part
    assert files["arcs/pololu_2693"] == files["halves/pololu_2693"] != files["arcs/generic_8mm_flange"]
    assert len(set(manifest["parts"]["slip_clutch_cap"]["files"].values())) == 1  # no option changes the cap
    contents = [f.read_bytes() for f in out.glob("*.stl")]
    assert len(set(contents)) == len(contents)  # no two files hold the same part


def test_a_fixed_link_choice_has_its_link_and_no_rod_end_or_rod(built):
    _, manifest = built
    adjustable, bom = variants.resolve(manifest, {**FIRST, "link": "adjustable"})
    fixed, bom_fixed = variants.resolve(manifest, {**FIRST, "link": "50"})
    assert {n for n in adjustable if n.startswith("mount_")} >= {"mount_rod_end_adjust", "mount_rod_end_fixed"}
    assert {n for n in fixed if n.startswith("mount_link")} == {"mount_link_50"} and not [n for n in fixed if "rod_end" in n]
    assert any(r["part"].startswith("DIN 976-1") for r in bom) and not any(r["part"].startswith("DIN 976-1") for r in bom_fixed)


def test_bom_follows_the_extender_and_the_hub(built):
    _, manifest = built

    def qty(**option) -> dict:
        return {r["part"]: r["qty"] for r in variants.resolve(manifest, {**FIRST, **option})[1]}

    default, bare, generic = qty(), qty(extender="without"), qty(hub="generic_8mm_flange")
    assert default["ISO 10642 M3 x 12"] == 4 and "ISO 10642 M3 x 12" not in bare  # the extender's screws
    assert default["ISO 4032 M3 nut"] == 4 and "ISO 4032 M3 nut" not in bare
    assert any(p.startswith("Pololu 2693") for p in default) and not any(p.startswith("Pololu 2693") for p in generic)
    assert any(p.startswith("Generic 8 mm") for p in generic)
    assert generic["ISO 4032 M3 nut"] == default["ISO 4032 M3 nut"] + 2  # nuts under the flange
    assert generic["ISO 4762 M3 x 12"] == default["ISO 4762 M3 x 12"] + 2


def test_every_combination_of_all_options_resolves():
    plan = variants.plan()
    for choice in combinations():
        for name in printed_parts(config(choice)):
            assert key(depends(name), choice) in plan[name], (name, choice)
        assert key(variants.BOM_DEPENDS, choice)


ALTERNATIVE = {"split": "halves", "plate": "pocket_pistol", "extender": "without", "link": "50", "tube": "square", "hub": "generic_8mm_flange"}


def _shape(part):
    box = part.bounding_box()
    return tuple(round(v, 3) for v in (part.volume, *box.min, *box.max))


@pytest.mark.parametrize("base", ("arcs", "one_piece"))
@pytest.mark.parametrize("option", ALTERNATIVE)
def test_a_part_does_not_change_with_an_option_it_is_not_keyed_by(base, option):
    a = {**FIRST, "split": base}
    b = {**a, option: ALTERNATIVE[option]}
    if a == b:
        pytest.skip("same choice")
    (cfg_a, cfg_b), (pa, pb) = (config(a), config(b)), (printed_parts(config(a)), printed_parts(config(b)))
    for name in pa.keys() & pb.keys():
        if option not in depends(name):
            assert _shape(pa[name](cfg_a)) == _shape(pb[name](cfg_b)), f"{name} changes with {option}"
