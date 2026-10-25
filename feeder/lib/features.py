"""Shared geometry features."""

import math  # noqa: I001

from build123d import Circle, Part, Plane, Polygon, Pos, Rectangle, RegularPolygon, Sketch, extrude, loft


def d_profile(d: float, across_flat: float) -> Sketch:
    """D shape: circle of diameter d with one flat at +x, across_flat from the opposite side."""
    # a d x d square centred at x = across_flat spans from the flat (x = across_flat - r) outward
    return Circle(d / 2) - Pos(across_flat, 0) * Rectangle(d, d)


def d_bore(d: float, across_flat: float, depth: float) -> Part:
    return extrude(d_profile(d, across_flat), depth)


def hex_prism(across_flats: float, height: float) -> Part:
    return extrude(RegularPolygon(across_flats / 2, 6, major_radius=False), height)


def hex_corner_r(across_flats: float) -> float:
    return across_flats / math.sqrt(3)


def _teardrop_profile(d: float) -> Sketch:
    r = d / 2
    k = r / math.sqrt(2)  # tangent points of the 45 deg roof lines
    return Circle(r) + Polygon((-k, k), (k, k), (0, r * math.sqrt(2)), align=None)


def teardrop(d: float, depth: float) -> Part:
    """Hole along +x from x = 0 with a 45 deg roof (tip at +z), so a horizontal hole prints without supports."""
    return Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)) * extrude(_teardrop_profile(d), depth)


def teardrop_cone(d0: float, d1: float, depth: float) -> Part:
    """Cone along +x from diameter d0 at x = 0 to d1 at x = depth, with the roof of `teardrop`."""
    return loft([Plane(origin=(x, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)) * _teardrop_profile(d) for x, d in ((0, d0), (depth, d1))])
