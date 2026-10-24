from collections import Counter
from dataclasses import replace

import pytest
import trimesh
from build123d import Mesher, export_stl

import build
from feeder import printing
from feeder.config import CFG
from feeder.parts import body


def test_part_names_are_unique_across_modules():
    # build.py writes build/<name>.stl, so a repeated name would overwrite another part.
    names = Counter(name for name, _ in build.iter_parts())
    assert [name for name, count in names.items() if count > 1] == []


@pytest.mark.parametrize("name, builder", list(build.iter_parts()), ids=lambda v: v if isinstance(v, str) else "")  # noqa: PT006
def test_part_fits_the_printer(name, builder):
    assert printing.fits(printing.on_bed(name, builder()), CFG), name


@pytest.mark.parametrize("name, builder", list(build.iter_parts()), ids=lambda v: v if isinstance(v, str) else "")  # noqa: PT006
def test_part_mesh_is_watertight(name, builder, tmp_path):
    # a slicer repairs or rejects a mesh with open or non-manifold edges, so the STL must close on its own
    export_stl(builder(), str(tmp_path / "part.stl"))
    assert trimesh.load(tmp_path / "part.stl").is_watertight, name


SPLIT_BODIES = [(split, name) for split in ("halves", "one_piece") for name in ("body_half_0", "body_half_1", "body") if name.startswith("body_half") == (split == "halves")]


@pytest.mark.parametrize("split, name", SPLIT_BODIES)  # noqa: PT006
def test_split_body_meshes_watertight_and_for_the_3mf(split, name, tmp_path):
    cfg = replace(CFG, body=replace(CFG.body, split=split))
    part = body.parts(cfg)[name]()
    export_stl(part, str(tmp_path / "part.stl"))
    assert trimesh.load(tmp_path / "part.stl").is_watertight
    Mesher().add_shape(part, linear_deflection=0.05, angular_deflection=0.3)  # as export_assembly, raises on an invalid mesh
