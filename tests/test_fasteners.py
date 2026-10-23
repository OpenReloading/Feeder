"""Bought fasteners: the assembly places every one the BOM lists, each in its holes."""

import re
from dataclasses import replace
from pathlib import Path

import pytest
from build123d import Pos

from feeder import assembly, export
from feeder.config import CFG

SPLITS = ("arcs", "halves", "one_piece")
GAP = 0.5  # mm, as in test_body: hole clearances and fits
BOM = Path(__file__).parent.parent / "bom" / "case_feeder_9mm.md"


def test_fastener_counts_match_the_bom():
    bom: dict = {}
    for item, qty in re.findall(r"^\| ((?:ISO|DIN|CNC Kitchen) [^|]+?) \| (\d+) \|", BOM.read_text(), re.M):
        bom[item] = bom.get(item, 0) + int(qty)
    placed: dict = {}
    for f in assembly.fasteners_in_body(CFG):
        placed[f.name] = placed.get(f.name, 0) + len(f.at)
    assert placed == bom


def _apart(ba, bb, gap=0.0) -> bool:
    return any(getattr(ba.max, a) + gap < getattr(bb.min, a) or getattr(bb.max, a) + gap < getattr(ba.min, a) for a in "XYZ")


@pytest.mark.parametrize("split", SPLITS)
def test_fasteners_sit_in_their_holes_without_cutting_printed_parts(split):
    # nominal shank, head, nut and insert outer diameters: a misplaced fastener cuts solid material or floats
    cfg = replace(CFG, body=replace(CFG.body, split=split))
    placed = assembly.placed(cfg)
    names = {p.name for p in placed}
    printed = [(p.name, p.shape, p.shape.bounding_box()) for p in placed if not p.bought and not p.tool]
    fs = assembly.fasteners_in_body(cfg)
    solids = [(f, loc * f.shape) for f in fs for loc in f.at]
    boxes = [s.bounding_box() for _, s in solids]
    for i, (f, solid) in enumerate(solids):
        assert f.host in names, f
        box = boxes[i]
        near = [(n, s) for n, s, b in printed if not _apart(box, b, GAP)]
        for n, s in near:
            if _apart(box, s.bounding_box()):
                continue
            common = solid & s
            volume = common.volume if common.solids() else 0.0
            assert volume < 1e-3, f"{f.name} on {f.host} cuts {n} by {volume:.4f} mm3"
        near += [(g.name, s) for j, (g, s) in enumerate(solids) if j != i and not _apart(box, boxes[j], GAP)]  # a nut on its washer
        assert min((solid.distance_to(s) for _, s in near), default=GAP + 1) <= GAP, f"{f.name} on {f.host} floats"


def test_viewer_matrices_place_fasteners_like_the_cad():
    for f in assembly.fasteners_in_body(CFG):
        for loc in f.at:
            m = export._matrix(loc)  # column-major
            for p in ((0, 0, 0), (1, 2, 3)):
                q = (loc * Pos(*p)).position
                got = [sum(m[c * 4 + r] * v for c, v in enumerate((*p, 1))) for r in range(3)]
                assert got == pytest.approx((q.X, q.Y, q.Z), abs=1e-4), f.name
