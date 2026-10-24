"""Print orientation: how each part goes on the bed. The print exports, the bed check and the support check use it.

Parts are modelled in print orientation unless listed in UPSIDE_DOWN, TOP_DOWN_SLANTED or TURNED. Parts wider than the bed turn about z
until they fit (body halves and extender halves go across the bed diagonal).
"""

from build123d import Part, Pos, Rot

from feeder.config import CFG, Config
from feeder.parts import body

UPSIDE_DOWN = {"slip_clutch_cap", "body_track_gate", "body_exit_insert"}
TOP_DOWN_SLANTED = {"body_extender_0", "body_extender_1"}  # flat top falls at the wall slant
TURNED = {"electronics_box": Rot(X=-90), "electronics_lid": Rot(X=90)}  # box on its back wall, lid on its outer face


def fits(part: Part, cfg: Config = CFG) -> bool:
    p = cfg.printer
    size = part.bounding_box().size
    return size.X <= p.bed_x - 2 * p.margin + 1e-3 and size.Y <= p.bed_y - 2 * p.margin + 1e-3 and size.Z <= p.bed_z


def on_bed(name: str, part: Part, cfg: Config = CFG) -> Part:
    """`part` as it goes on the bed: flipped if it prints upside down, turned about z in 5 deg steps until it
    fits (unturned if it fits as is), centred on the origin with its bottom at z = 0."""
    if name in UPSIDE_DOWN:
        part = Rot(X=180) * part
    if name in TURNED:
        part = TURNED[name] * part
    if name in TOP_DOWN_SLANTED:
        part = Rot(X=180 + body.wall_slant(cfg)) * part
    turned = (Rot(Z=a) * part for a in range(0, 180, 5))
    part = next((t for t in turned if fits(t, cfg)), part)
    box = part.bounding_box()
    return Pos(-box.center().X, -box.center().Y, -box.min.Z) * part
