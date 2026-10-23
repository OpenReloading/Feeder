import pytest
from build123d import Pos
from test_mount import _unsupported

from feeder import printing
from feeder.parts import body, case_plate, electronics
from feeder.parts import slip_clutch as sc

# print orientation from feeder.printing. Not here: the core (its mesh does not
# slice cleanly, test_body checks its bridges by numbers), the drop tube (accepted flags: the 45 deg ridge under
# the thumb screw boss, the socket shoulder, the nut slot ceiling and the flat sensor hole roof, all short bridges)
# and the mount parts (test_mount). The check slices every 1 mm, so it cannot judge the 1 mm deep cap thread.
PARTS = {
    "slip_clutch_carrier_metal_hub": sc.carrier,
    "slip_clutch_drive_ring": sc.drive_ring,
    "slip_clutch_disc": sc.disc,
    "slip_clutch_knob": sc.knob,
    "slip_clutch_cap": sc.cap,
    "case_plate": case_plate.plate,
    "body_wall_0": lambda: body.wall(0),
    "body_track_gate": body.track_gate,
    "body_exit_insert": body.exit_insert,
    "electronics_box": electronics.box,
    "electronics_lid": electronics.lid,
}


@pytest.mark.parametrize("name", PARTS)
def test_part_prints_without_supports(name):
    part = Pos(0, 0, -0.013) * printing.on_bed(name, PARTS[name]())  # layers off the coplanar faces
    assert _unsupported(part) == []
