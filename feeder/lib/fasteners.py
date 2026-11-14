"""Fastener data from bd_warehouse and the cutting tools for their holes.

Tools are solids to subtract. Each starts at z = 0 and runs into -z, so place them on the face they enter.
The tools take the insert table and `head_fit` from the `cfg` passed in. Thread pitches and the screw, nut and washer
data are standard (ISO 261, bd_warehouse) and cached by size, so they come from the global `CFG` for every config.
"""

from functools import cache  # cached screws are shared: callers read them, never move or change them  # noqa: I001
from typing import Literal

from bd_warehouse.fastener import CounterSunkScrew, HexHeadScrew, HexNut, PlainWasher, SocketHeadCapScrew
from build123d import Align, Cone, Cylinder, Part, RegularPolygon, extrude, Pos

from feeder.config import CFG, Config

DOWN = (Align.CENTER, Align.CENTER, Align.MAX)


def nominal_d(size: str) -> float:
    return float(size.removeprefix("M"))


def _thread(size: str) -> str:
    return f"{size}-{CFG.fasteners.coarse_pitch[size]:g}"


@cache
def hex_screw(size: str, length: float, fastener_type: Literal["iso4014", "iso4017"] = "iso4017") -> HexHeadScrew:
    """ISO 4017 hex head screw with full thread, or ISO 4014 with a plain shank (`thread_length` from the head's far end)."""
    return HexHeadScrew(size=_thread(size), length=length, fastener_type=fastener_type, simple=True)


@cache
def socket_screw(size: str, length: float) -> SocketHeadCapScrew:
    """ISO 4762 socket head cap screw."""
    return SocketHeadCapScrew(size=_thread(size), length=length, fastener_type="iso4762", simple=True)


@cache
def socket_screw_lengths(size: str) -> tuple[float, ...]:
    probe_length = 20  # see hex_screw_lengths
    return tuple(socket_screw(size, probe_length).nominal_lengths)


@cache
def countersunk_screw(size: str, length: float) -> CounterSunkScrew:
    """ISO 10642 countersunk socket head screw."""
    return CounterSunkScrew(size=_thread(size), length=length, fastener_type="iso10642", simple=True)


@cache
def countersunk_screw_lengths(size: str) -> tuple[float, ...]:
    probe_length = 20  # see hex_screw_lengths
    return tuple(countersunk_screw(size, probe_length).nominal_lengths)


def clearance_d(size: str, fit: str = "Normal") -> float:
    """ISO 273 series: "Close" (fine), "Normal" (medium) or "Loose" (coarse)."""
    return hex_screw(size, hex_screw_lengths(size)[0]).clearance_hole_diameters[fit]


def nut_data(size: str) -> dict:
    """ISO 4032 hex nut: m height, s across flats."""
    return hex_nut(size).nut_data


@cache
def washer_data(size: str) -> dict:
    """ISO 7089 plain washer (same size as DIN 125 A): d1 bore, d2 outside, h thickness."""
    return PlainWasher(size=size, fastener_type="iso7089").washer_data


def pick_length(lengths: tuple[float, ...], minimum: float) -> float:
    """Shortest standard length that is at least `minimum`."""
    fits = [length for length in lengths if length >= minimum]
    if not fits:
        raise ValueError(f"no standard length >= {minimum:.1f} in {lengths}")
    return min(fits)


@cache
def hex_screw_lengths(size: str, fastener_type: Literal["iso4014", "iso4017"] = "iso4017") -> tuple[float, ...]:
    """Nominal lengths of a size for ISO 4017 or ISO 4014, from bd_warehouse."""
    probe_length = float(HexHeadScrew.fastener_data[_thread(size)][f"{fastener_type}:short"])  # only the length table is read
    return tuple(hex_screw(size, probe_length, fastener_type).nominal_lengths or ())


def insert_hole(size: str, cfg: Config = CFG) -> Part:
    """Blind hole for a heat-set insert, CNC Kitchen hole diameter and depth L + 1."""
    insert = cfg.fasteners.inserts[size]
    return Cylinder(insert.hole_d / 2, insert.hole_depth, align=DOWN)


def clearance_hole(size: str, depth: float) -> Part:
    return Cylinder(clearance_d(size) / 2, depth, align=DOWN)


def hex_head_pocket(size: str, length: float, cfg: Config = CFG) -> Part:
    """Pocket that captures an ISO 4017 head so the part can turn the screw."""
    head = hex_screw(size, length).screw_data
    across = head["s"] + 2 * cfg.fasteners.head_fit
    return Pos(0, 0, -head["k"]) * extrude(RegularPolygon(across / 2, 6, major_radius=False), head["k"])


def socket_head_counterbore(size: str, length: float, depth: float, cfg: Config = CFG) -> Part:
    """Counterbore of depth `depth` for an ISO 4762 head."""
    head_d = socket_screw(size, length).screw_data["dk"]
    return Cylinder(head_d / 2 + cfg.fasteners.head_fit, depth, align=DOWN)


def countersink(size: str, length: float, depth: float, cfg: Config = CFG) -> Part:
    """Clearance hole of depth `depth` with a 90 deg countersink for an ISO 10642 head."""
    head_r = countersunk_screw(size, length).screw_data["dk"] / 2 + cfg.fasteners.head_fit
    hole_r = clearance_d(size) / 2
    return clearance_hole(size, depth) + Cone(hole_r, head_r, head_r - hole_r, align=DOWN)


@cache
def hex_nut(size: str) -> HexNut:
    """ISO 4032 hex nut."""
    return HexNut(size=_thread(size), fastener_type="iso4032", simple=True)


def nut_pocket(size: str, cfg: Config = CFG) -> Part:
    """Pocket that holds an ISO 4032 nut against turning, depth = nut height."""
    nut = nut_data(size)
    across = nut["s"] + 2 * cfg.fasteners.head_fit
    return Pos(0, 0, -nut["m"]) * extrude(RegularPolygon(across / 2, 6, major_radius=False), nut["m"])
