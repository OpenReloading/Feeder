"""Side view of the introduction page: the assembly at its tilt, seen from +x and cut through the middle plane
(x = 0: shaft, exit, stand tube), as inline SVG in the colors of guide/stylesheets/extra.css."""

import math
from dataclasses import dataclass

import numpy as np
import shapely
from build123d import Plane, section
from shapely import affinity
from shapely.geometry import Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points, unary_union

from feeder import assembly
from feeder.config import CFG, Config

# Kind in assembly.placed -> drawn group. Left out: the electronics box with its boards and panel parts and the level
# sensor, which sit in front of the cut.
GROUPS = {
    "body": "body", "wall": "body", "gate": "body", "exit": "body", "extender": "extender", "plate": "plate",
    "steel": "clutch", "alu": "clutch", "pla": "clutch", "ring": "clutch", "pla2": "clutch", "pla3": "clutch", "cap": "clutch",
    "motor": "motor", "drop": "drop", "yoke": "mount", "clamp": "mount", "link": "link", "tube": "tube",
}
# Back to front: group, "outline" (seen from the side) or "cut" (faces in the plane), class suffix in extra.css
LAYERS = (
    ("extender", "outline", "optional"), ("body", "outline", "behind"), ("drop", "outline", "behind"),
    ("tube", "outline", "whole"), ("mount", "outline", "whole"), ("link", "outline", "whole"), ("motor", "outline", "whole"),
    ("body", "cut", "cut"), ("drop", "cut", "cut"), ("mount", "cut", "cut"),
    ("clutch", "outline", "whole"), ("plate", "cut", "plate"),
)
STEP = 0.5  # mm between points along a cut edge
DETAIL = 0.25  # mm, smaller detail is dropped from the drawing
SMOOTH = 2.0  # mm, outlines lose notches narrower than twice this
MARGIN = 14.0  # mm around the drawing
TEXT_GAP = 9.0  # mm between a number's center and the end of its leader


@dataclass(frozen=True)
class Callout:
    name: str
    group: str
    at: tuple[float, float]  # where the leader ends, as fractions of the group's bounds from its left top
    label: tuple[float, float]  # the number's center from that point, mm right and down


CALLOUTS = (
    Callout("Plate", "plate", (0.75, 0.25), (-52, -34)),
    Callout("Clutch and cap", "clutch", (0.15, 0.6), (-55, -12)),
    Callout("Body", "body", (0.18, 0.78), (-30, 30)),
    Callout("Extender, optional", "extender", (0.4, 0.0), (-14, -24)),
    Callout("Motor", "motor", (0.85, 0.55), (48, 46)),
    Callout("Drop tube", "drop", (0.75, 0.55), (36, 0)),
    Callout("Tilt mount", "mount", (1.0, 0.31), (50, 28)),
    Callout("Tilt link", "link", (0.5, 0.5), (-48, 10)),
    Callout("Stand tube", "tube", (0.5, 0.45), (44, 0)),
)


@dataclass(frozen=True)
class View:
    """The drawing in mm, x to the right (the high side), y down."""

    tilt: float
    outlines: dict[str, BaseGeometry]
    cuts: dict[str, BaseGeometry]
    callouts: tuple[tuple[Callout, tuple[float, float], tuple[float, float]], ...]  # callout, leader end on the part, number's center
    box: tuple[float, float, float, float]  # left, top, width, height


def _polygons(geom: BaseGeometry) -> list[Polygon]:
    return [g for g in getattr(geom, "geoms", [geom]) if isinstance(g, Polygon) and not g.is_empty]


def _ring(wire) -> list[tuple[float, float]]:
    pts = []
    for edge in wire.order_edges():
        n = max(3, math.ceil(edge.length / STEP))  # 3: a ring of one edge is still a polygon
        pts += [(p.Y, p.Z) for p in (edge.position_at(i / n) for i in range(n))]
    return pts


def _cut(shape) -> BaseGeometry:
    """Faces of `shape` in the plane x = 0, in the body frame's (y, z)."""
    box = shape.bounding_box()
    if box.min.X >= 0 or box.max.X <= 0:
        return Polygon()
    return unary_union([Polygon(_ring(face.outer_wire()), [_ring(w) for w in face.inner_wires()]).buffer(0)
                        for face in section(shape, section_by=Plane.YZ).faces()])


def _outline(shape) -> BaseGeometry:
    """Outline of `shape` seen along x, in the body frame's (y, z)."""
    vertices, triangles = shape.tessellate(0.2, 0.3)
    faces = np.asarray(shapely.polygons(np.array([(v.Y, v.Z) for v in vertices])[np.array(triangles)]))
    return unary_union([Polygon(p.exterior) for p in _polygons(unary_union(faces[shapely.area(faces) > 1e-6]))])  # without faces seen edge-on


def _clean(geom: BaseGeometry, turn: list[float], close: float = DETAIL) -> BaseGeometry:
    """Into the drawing's frame, with notches narrower than 2 * `close` filled and detail under DETAIL dropped."""
    out = affinity.affine_transform(geom, turn).simplify(DETAIL / 5)  # mitred corners need distinct points
    out = out.buffer(close, join_style="mitre").buffer(-close - DETAIL, join_style="mitre").buffer(DETAIL, join_style="mitre").simplify(DETAIL)
    return unary_union([Polygon(p.exterior, [r for r in p.interiors if Polygon(r).area > 4 * DETAIL]) for p in _polygons(out)])


def _leader_end(geom: BaseGeometry, at: tuple[float, float]) -> tuple[float, float]:
    left, top, right, bottom = geom.bounds
    target = Point(left + at[0] * (right - left), top + at[1] * (bottom - top))
    p = nearest_points(geom, target)[0]
    return p.x, p.y


def view(cfg: Config = CFG, tilt: float | None = None) -> View:
    tilt = assembly.body_tilt(cfg) if tilt is None else tilt
    a = math.radians(tilt)
    turn = [math.cos(a), -math.sin(a), -math.sin(a), -math.cos(a), 0.0, 0.0]  # body frame (y, z) at the tilt, y down
    seen: dict[str, list] = {}
    cut: dict[str, list] = {}
    for p in assembly.placed(cfg, tilt):
        if p.kind in GROUPS:
            seen.setdefault(GROUPS[p.kind], []).append(_outline(p.shape))
            cut.setdefault(GROUPS[p.kind], []).append(_cut(p.shape))
    outlines = {g: _clean(unary_union(parts), turn, SMOOTH) for g, parts in seen.items()}
    outlines["extender"] = _clean(outlines["extender"].difference(outlines["body"]), [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])  # the body hides the rest
    cuts = {g: _clean(unary_union(parts), turn) for g, parts in cut.items()}
    front = {group: what for group, what, _ in LAYERS}  # what a leader points at
    callouts = []
    for c in CALLOUTS:
        x, y = _leader_end((outlines if front[c.group] == "outline" else cuts)[c.group], c.at)
        callouts.append((c, (x, y), (x + c.label[0], y + c.label[1])))
    # The stand tube runs out of the drawing at the bottom
    left, top, right, bottom = unary_union([g for name, g in outlines.items() if name != "tube"] + [Point(end) for _, _, end in callouts]).bounds
    box = (left - MARGIN, top - MARGIN, right - left + 2 * MARGIN, bottom - top + 2 * MARGIN)
    return View(tilt, outlines, cuts, tuple(callouts), box)


def _path(geom: BaseGeometry) -> str:
    return "".join("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in ring.coords[:-1]) + "Z"
                   for poly in _polygons(geom) for ring in (poly.exterior, *poly.interiors))


def side_view_html(cfg: Config = CFG) -> str:
    """Content of the introduction page's figure: the drawing, its numbered parts as a list, the caption."""
    v = view(cfg)
    names = [f"{i:02d} {c.name}" for i, (c, _, _) in enumerate(v.callouts, 1)]
    alt = f"Side view of the feeder at {v.tilt:.0f} deg, cut through the middle. Its parts: " + "; ".join(c.name.lower() for c, _, _ in v.callouts)
    lines = [f'<svg class="feeder-hero__drawing" viewBox="{" ".join(f"{n:.0f}" for n in v.box)}" role="img" aria-label="{alt}">',
             '<g aria-hidden="true">']
    for group, what, cls in LAYERS:
        lines.append(f'<path class="feeder-hero__{cls}" d="{_path((v.outlines if what == "outline" else v.cuts)[group])}"/>')
    lines.append('<g class="feeder-hero__labels">')
    for i, (_, (x, y), (tx, ty)) in enumerate(v.callouts, 1):
        k = 1 - TEXT_GAP / math.hypot(tx - x, ty - y)
        lines.append(f'<path d="M{x:.1f} {y:.1f}L{x + k * (tx - x):.1f} {y + k * (ty - y):.1f}"/><circle cx="{x:.1f}" cy="{y:.1f}" r="1.8"/>'
                     f'<text x="{tx:.1f}" y="{ty:.1f}" dy=".35em">{i:02d}</text>')
    lines += ["</g>", "</g>", "</svg>", '<ul class="feeder-hero__parts">', *(f"<li>{n}</li>" for n in names), "</ul>",
              f"<figcaption>Cut through the middle at {v.tilt:.0f} deg, drawn from the CAD model. "
              "Without the electronics box, the level sensor and the fasteners.</figcaption>"]
    return "\n".join(lines) + "\n"
