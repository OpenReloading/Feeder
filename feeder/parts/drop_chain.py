"""Drop tube chain: parts on the drop tube's male end (the exit spigot's form), each with the drop tube's female socket
and bayonet at one end and the male form at the other. Spacer, angled piece and hose adapter are the parts; the hose
adapter ends the chain, `drop_chain.parts` names the optional ones in front of it.

Frame of every part: print orientation, socket mouth on the bed at z = 0, +z along the case path, the wide lug of the
male end on +x. A part hangs on the previous part's male end the way the drop tube hangs on the exit spigot, so +x
carries through the chain and the sensor window of the first tube stays where it is. The bore is the drop tube bore
everywhere, the walls are the drop tube's.
"""

from build123d import Cylinder, Location, Part, Pos, Rot, Sphere

from feeder.config import CFG, Config
from feeder.lib.cache import per_config
from feeder.parts import drop_tube as dt

BOTTOM = dt.BOTTOM


def _socket_end(k: dt.Dims) -> Part:
    return Part(Cylinder(k.r_socket_out, k.socket_top, align=BOTTOM))


@per_config
def spacer(cfg: Config = CFG) -> Part:
    k = dt.dims(cfg)
    z = k.socket_top + cfg.drop_chain.spacer_len
    part = Part(_socket_end(k) + Cylinder(k.r_tube, z, align=BOTTOM) + dt.male(k, cfg, z))
    part -= dt.socket_cut(k, cfg)
    part -= Pos(0, 0, k.depth - 1) * Cylinder(k.r_bore, z + cfg.exit.spigot_len - k.depth + 2, align=BOTTOM)
    return Part(part)


def _bend(cfg: Config) -> tuple[float, Location]:
    """Height of the bend centre on the axis, and the frame of the second leg (+z along it, bent sideways to the lugs, away from the body)."""
    z = dt.dims(cfg).socket_top + cfg.drop_chain.leg_len
    return z, Pos(0, 0, z) * Rot(X=cfg.drop_chain.angle)


@per_config
def angled(cfg: Config = CFG) -> Part:
    k, c = dt.dims(cfg), cfg.drop_chain
    z, leg2 = _bend(cfg)
    part = Part(_socket_end(k) + Cylinder(k.r_tube, z, align=BOTTOM) + Pos(0, 0, z) * Sphere(k.r_tube))
    part += leg2 * (Cylinder(k.r_tube, c.leg_len, align=BOTTOM) + dt.male(k, cfg, c.leg_len))
    part -= dt.socket_cut(k, cfg)
    part -= Pos(0, 0, k.depth - 1) * Cylinder(k.r_bore, z - k.depth + 1, align=BOTTOM)
    part -= Pos(0, 0, z) * Sphere(k.r_bore)
    part -= leg2 * Cylinder(k.r_bore, c.leg_len + cfg.exit.spigot_len + 1, align=BOTTOM)
    return Part(part)


@per_config
def hose_adapter(cfg: Config = CFG) -> Part:
    k = dt.dims(cfg)
    tip = k.socket_top + cfg.drop_tube.barb_len
    part = Part(_socket_end(k) + dt.barb(k, cfg, tip))
    part -= dt.socket_cut(k, cfg)
    part -= Pos(0, 0, k.depth - 1) * Cylinder(k.r_bore, tip - k.depth + 2, align=BOTTOM)
    return Part(part)


def male_frames(cfg: Config = CFG) -> dict[str, Location]:
    """Start of the male end of each part that has one, in the part's frame."""
    k, c = dt.dims(cfg), cfg.drop_chain
    return {"spacer": Pos(0, 0, k.socket_top + c.spacer_len), "angled": _bend(cfg)[1] * Pos(0, 0, c.leg_len)}


def frames(cfg: Config = CFG) -> list[tuple[str, Location]]:
    """Name and frame in the body frame of every part after the drop tube, in order, ending with the hose adapter."""
    male = male_frames(cfg)
    unknown = [n for n in cfg.drop_chain.parts if n not in male]
    if unknown:
        raise ValueError(f"drop_chain.parts {unknown} are not chain parts, supported: {', '.join(male)}")
    loc = dt.placement(cfg).location * Pos(0, 0, dt.dims(cfg).male_z)
    out = []
    for n in (*cfg.drop_chain.parts, "hose_adapter"):
        out.append((f"drop_{n}", loc))
        loc = loc * male[n] if n in male else loc
    return out


PARTS = {"drop_spacer": spacer, "drop_angled": angled, "drop_hose_adapter": hose_adapter}
