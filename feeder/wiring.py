"""Wiring data of the electronics box: parts, terminals and connections. The guide board and the lid labels read it,
so the text on the lid cannot drift from the wiring page."""

import re


def _part(kind: str, name: str, sub: str, at: tuple, size: tuple, **ports) -> dict:
    return {"kind": kind, "name": name, "sub": sub, "at": list(at), "size": list(size), "ports": ports}


# Electronics box wiring, not to scale. Sockets (GX12, 3-pin for the sensor, 2-pin for the motor): P = plug
# pin outside, S = solder cup of the same pin inside.
WIRING_PARTS = {
    "B1": _part("sensor", "B1 sensor, NPN NC", "", (620, 20), (150, 60), bottom=["BN", "BU", "BK"]),
    "M1": _part("box", "M1 motor, 12 V", "", (810, 20), (120, 60), bottom=["+", "-"]),
    "X2": _part("socket", "X2 sensor socket", "", (620, 220), (150, 60), top=["P1", "P2", "P3"], bottom=["S1", "S2", "S3"]),
    "X1": _part("socket", "X1 motor socket", "", (810, 220), (120, 60), top=["P1", "P2"], bottom=["S1", "S2"]),
    "Q1": _part("box", "Q1 power switch", "front face", (70, 220), (100, 60), right=["COM", "ON"]),
    "J1": _part("box", "J1 12 V in", "DC jack, centre pin +, front face", (70, 440), (100, 70), right=["+", "-"]),
    "F1": _part("box", "F1 fuse", "3.15 A time-lag, inline holder", (200, 330), (90, 50), left=["1"], right=["2"]),
    "D1": _part("box", "D1 reverse polarity diode", "Schottky, series", (330, 330), (110, 50), left=["A"], right=["K"]),
    "D2": _part("box", "D2 flyback diode", "across the motor plug", (810, 420), (110, 50), top=["K", "A"]),
    "XP": _part("join", "XP +12 V", "", (230, 240), (150, 30), bottom=["1", "2", "3", "4"]),
    "XN": _part("join", "XN 0 V", "", (420, 240), (150, 30), bottom=["1", "2", "3", "4"]),
    "U1": _part("box", "U1 PWM controller", "knob in the front face", (260, 420), (130, 110), left=["V+", "V-"], right=["M+", "M-"]),
    "K1": _part("box", "K1 timer relay", "DROK 200391, mode P8, about 2 s", (580, 420), (150, 110), left=["VCC", "GND", "IN"], right=["OUT1", "OUT2"]),
}

# (step id, title, note, [(no, a, b, colour)])
WIRING_STEPS = [
    ("A", "Power in", "Unplug the 12 V supply before you touch a terminal. Fit the fuse last. The diode band (cathode) points away "
     "from the fuse; a reversed supply then reaches nothing behind it. Use 0.75 mm² wire for the 12 V and motor lines.",
     [("1", "J1:+", "Q1:COM", "RD"), ("2", "Q1:ON", "F1:1", "RD"), ("3", "F1:2", "D1:A", "RD"), ("4", "D1:K", "XP:1", "RD"),
      ("5", "J1:-", "XN:1", "BK")]),
    ("B", "PWM controller", "Turn the knob to the lowest setting before the first power-up.",
     [("6", "XP:2", "U1:V+", "RD"), ("7", "XN:2", "U1:V-", "BK")]),
    ("C", "Timer relay supply", "Set the module to mode P8 and OP to about 2 s. IN is its low-level trigger terminal.",
     [("8", "XP:3", "K1:VCC", "RD"), ("9", "XN:3", "K1:GND", "BK")]),
    ("D", "Sensor socket", "The sensor output pulls the relay input to 0 V while no brass is in front of it. "
     "Check the sensor type and its on-state voltage first (see above).",
     [("10", "XP:4", "X2:S1", "BN"), ("11", "XN:4", "X2:S2", "BU"), ("12", "X2:S3", "K1:IN", "BK")]),
    ("E", "Motor line", "The motor runs only while the relay holds. The flyback diode D2 sits across the motor plug, after "
     "the relay contact, cathode (band) on the + pin. The cap thread follows the plate direction, so the motor turns one way "
     "only: set `case_plate.direction` in the configuration and print the matching plate and cap.",
     [("13", "U1:M+", "K1:OUT1", "RD"), ("14", "K1:OUT2", "X1:S1", "RD"), ("15", "U1:M-", "X1:S2", "BK"),
      ("16", "D2:K", "X1:S1", "RD"), ("17", "D2:A", "X1:S2", "BK")]),
    ("F", "Plugs", "Solder the sensor cable and the motor cable to the plugs: brown, blue, black to pins 1, 2, 3; "
     "motor + to pin 1.",
     [("18", "B1:BN", "X2:P1", "BN"), ("19", "B1:BU", "X2:P2", "BU"), ("20", "B1:BK", "X2:P3", "BK"),
      ("21", "M1:+", "X1:P1", "RD"), ("22", "M1:-", "X1:P2", "BK")]),
]


def plug_pins() -> dict[str, list[tuple[str, str]]]:
    """(pin number, what the plug carries there) of each socket, from the plug step: {"X2": [("1", "BN"), ...]}."""
    pins: dict[str, list[tuple[str, str]]] = {}
    for step, _, _, wires in WIRING_STEPS:
        if step != "F":
            continue
        for _, a, b, _ in wires:
            for socket, other in ((a, b), (b, a)):
                ref, pin = socket.split(":")
                if WIRING_PARTS[ref]["kind"] == "socket" and pin.startswith("P"):
                    pins.setdefault(ref, []).append((pin[1:], other.split(":")[1]))
    return {ref: sorted(rows) for ref, rows in pins.items()}


def centre_polarity(ref: str) -> str:
    """Polarity of the centre pin of a jack, from the part description: "+" or "-"."""
    sign = re.search(r"centre pin ([+-])", WIRING_PARTS[ref]["sub"])
    if not sign:
        raise ValueError(f"{ref} has no centre pin polarity in its description")
    return sign.group(1)
