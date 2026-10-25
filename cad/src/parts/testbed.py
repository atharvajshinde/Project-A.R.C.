"""
PROJECT A.R.C. – Testbed & Calibration Infrastructure (src/parts/testbed.py)
=============================================================================
3D-printable PETG/PLA mounting brackets, risers, and shims to physically
assemble, calibrate, and elevate the A.R.C. digital twin testbed:

1. testbed_rail_riser_foot:
   - 40.0 mm elevation riser block supporting 2020 V-slot guide rail ends.
   - Suspends the rails in mid-air ("floating") so the 3rd bottom clamping
     V-wheel (lowest rim at Z = -50.5 mm) and lower endplate lobe (down to Z = -52.0 mm)
     have >23 mm of clear air over the workbench/baseboard.
   - Integrated 2020 endstop bumper flange (stops carriage from over-running rail).
   - Side and bottom M5 counterbored bolt holes for roll-in T-nut clamping.
   - Wide base flange with 2x M5/M4 baseboard mounting holes.

2. testbed_rail_panel_bracket:
   - Direct monolithic bridge connecting the 2020 guide rail to the solar panel frame.
   - 6 mm alignment key locks into the 2020 rail inner T-slot (M5 bolt + T-nut).
   - Step-shelf precisely holds the 25.0 mm deep aluminum solar panel frame so the
     top glass surface sits exactly 15.23 mm above the top face of the 2020 rail
     (placing the glass at Z = 0.0 mm datum, ensuring plush 800 GSM microfiber contact).
   - Side clamping holes (M4) and top lip set-screw boss for non-slip mechanical lock.

3. testbed_panel_pedestal:
   - Freestanding 50.23 mm high central anti-sag pedestal supporting the center/corners
     of the solar panel frame off the baseboard when 40 mm rail risers are used.
"""

from __future__ import annotations
import math
import build123d as bd
from build123d import (
    BuildPart, BuildSketch,
    Cylinder, Box, extrude,
    Plane, Locations, Location, Vector, Mode, Align,
    Rectangle, Circle, Polygon, RectangleRounded,
)

from src.parameters import EPS


def build_testbed_rail_riser_foot(height: float = 40.0) -> bd.Solid:
    """
    Elevates the 2020 V-slot guide rail ends above a baseboard or desk.
    
    Coordinates (local frame):
      - X = across rail (width 60 mm base, 26 mm column).
      - Y = along rail (length 45 mm base, 30 mm saddle).
      - Z = vertical (Z=0 bottom face on baseboard, Z=height rail seating floor).
      
    Features:
      - Rail seating saddle: 20.2 mm wide x 30.0 mm long pocket at Z = height.
      - Side retention walls: 3.0 mm thick walls rising 12.0 mm above rail floor.
      - Integrated end-stop bumper: 6.0 mm thick solid wall at +Y capping rail end.
      - Horizontal M5 bolt holes through side retention walls into 2020 side slots.
      - Vertical M5 through-hole from counterbore underneath into 2020 bottom slot.
      - 2x counterbored M5 holes on base flange (pitch 48 mm across X).
      - 45-degree gussets for high lateral rigidity under carriage acceleration.
    """
    base_w = 64.0        # X
    base_len = 45.0      # Y
    base_t = 6.0         # Z
    col_w = 26.2         # X
    col_len = 35.0       # Y
    saddle_w = 20.2      # fits 20 mm extrusion with 0.1 mm per side tolerance
    wall_t = 3.0
    wall_h = 12.0
    bumper_t = 6.0

    with BuildPart() as bp:
        # 1. Base flange with rounded corners
        with BuildSketch(Plane.XY):
            RectangleRounded(base_w, base_len, 4.0)
        extrude(amount=base_t)

        # 2. Riser column from base up to rail floor (Z = height)
        with BuildSketch(Plane.XY.offset(base_t - EPS)):
            with Locations((0.0, -bumper_t / 2.0)):
                RectangleRounded(col_w, col_len, 3.0)
        extrude(amount=height - base_t + EPS)

        # 3. Side retention walls (Z from height to height + wall_h)
        wall_total_w = saddle_w + 2.0 * wall_t
        with BuildSketch(Plane.XY.offset(height - EPS)):
            with Locations((0.0, -bumper_t / 2.0)):
                Rectangle(wall_total_w, col_len)
        extrude(amount=wall_h + EPS)

        # 4. Endstop bumper wall at rear (+Y) rising to height + 16 mm
        with BuildSketch(Plane.XY.offset(height - EPS)):
            with Locations((0.0, col_len / 2.0 - bumper_t / 2.0)):
                Rectangle(wall_total_w, bumper_t)
        extrude(amount=wall_h + 4.0 + EPS)

        # 5. Hollow out 20.2 mm rail seating saddle (down to Z = height)
        with BuildSketch(Plane.XY.offset(height)):
            with Locations((0.0, -bumper_t / 2.0 - 5.0)):
                Rectangle(saddle_w, col_len + 10.0)
        extrude(amount=wall_h + 2.0, mode=Mode.SUBTRACT)

        # 6. Gusset ribs connecting riser column to base flange
        for sign_x in (-1.0, 1.0):
            with BuildSketch(Plane.XZ.offset(-bumper_t / 2.0)):
                Polygon([
                    (sign_x * col_w / 2.0, base_t - EPS),
                    (sign_x * (base_w / 2.0 - 5.0), base_t - EPS),
                    (sign_x * col_w / 2.0, height - 5.0),
                ])
            extrude(amount=18.0, both=True)

        # 7. 2x M5 counterbored baseboard mounting holes on base flange (X = ±24 mm)
        for sign_x in (-1.0, 1.0):
            with Locations((sign_x * 24.0, 0.0, -EPS)):
                with BuildSketch(Plane.XY):
                    Circle(5.3 / 2.0)
                extrude(amount=base_t + 2.0 * EPS, mode=Mode.SUBTRACT)
                with BuildSketch(Plane.XY.offset(base_t - 2.5)):
                    Circle(9.5 / 2.0)
                extrude(amount=3.0, mode=Mode.SUBTRACT)

        # 8. Vertical M5 counterbored center hole (Z = 0 to height) into bottom T-slot
        with Locations((0.0, -bumper_t / 2.0, -EPS)):
            with BuildSketch(Plane.XY):
                Circle(5.3 / 2.0)
            extrude(amount=height + 2.0 * EPS, mode=Mode.SUBTRACT)
            with BuildSketch(Plane.XY):
                Circle(10.0 / 2.0)
            extrude(amount=height - 10.0, mode=Mode.SUBTRACT)

        # 9. Horizontal M5 clamping holes through side retention walls into side T-slot (Z = height + 10)
        screw_z = height + 10.0
        for sign_x in (-1.0, 1.0):
            with Locations((sign_x * (wall_total_w / 2.0 + EPS), -bumper_t / 2.0 - 3.0, screw_z)):
                with BuildSketch(Plane.YZ):
                    Circle(5.3 / 2.0)
                extrude(amount=-wall_t - 2.0 * EPS, mode=Mode.SUBTRACT)

    return bp.part


def build_testbed_rail_panel_bracket() -> bd.Solid:
    """
    Direct alignment bracket connecting 2020 V-slot guide rail to a plain display glass sheet.
    
    Locks the top surface of the plain glass sheet at exactly Z = 0.00 mm datum
    (15.23 mm above the top of the 2020 rail), ensuring precise microfiber roller wiping contact.
    
    Coordinates:
      - Origin (0,0,0) at rail inner face (X = 0), rail top face (Z = 0).
      - Bridging span (+X) extends 20.5 mm from rail inner face (X = -163.0) to glass edge (X = -142.5).
      - Glass support shelf (+X from 20.5 to 35.5 mm) holds the underside of the 3.2 mm glass sheet
        at local Z = +12.03 mm (global Z = -3.20 mm).
      - Glass edge stop shoulder at local Z = +15.23 mm (global Z = 0.00 mm, flush with glass top).
    
    Features:
      - 2020 rail interface:
        - 1.5 mm deep alignment tongue riding in 2020 extrusion inner slot.
        - 2x M5 counterbored through-holes (20 mm pitch along Y) for M5x8 screws + T-nuts.
      - Plain glass sheet interface:
        - 15.0 mm wide support shelf seated at Z = +12.03 mm (holding glass underside).
        - Edge stop registration shoulder flush with top of glass (Z = +15.23 mm, global Z = 0.00 mm).
        - Under-shelf stiffening gusset rib for high rigidity under gantry load.
    """
    blen = 40.0         # Y span
    gap = 20.5          # distance from 2020 rail inner face (X = -163) to glass edge (X = -142.5)
    shelf_inward = 15.0 # shelf extension under plain glass sheet (to X = -127.5 mm)
    shelf_z = 12.03     # shelf top floor (global Z = -15.23 + 12.03 = -3.20 mm, glass underside)
    shelf_t = 5.0
    shoulder_z = 15.23  # edge stop shoulder (global Z = -15.23 + 15.23 = 0.00 mm, flush with glass top)
    rail_bottom_z = -16.0
    rail_slot_z = -10.0 # center of 2020 rail inner slot

    with BuildPart() as bp:
        # 1. Main bridging body filling the gap between rail and glass edge
        with Locations((gap / 2.0, 0.0, (rail_bottom_z + shelf_z) / 2.0)):
            Box(gap, blen, shelf_z - rail_bottom_z)

        # 2. Alignment key entering 2020 inner slot (-X)
        with Locations((-1.5 / 2.0, 0.0, rail_slot_z)):
            Box(1.5, blen - 4.0, 5.8)

        # 3. Glass support shelf extending under the glass (+X, from gap to gap + shelf_inward)
        with Locations((gap + shelf_inward / 2.0, 0.0, shelf_z - shelf_t / 2.0)):
            Box(shelf_inward, blen, shelf_t)

        # 4. Glass edge registration shoulder (flush with glass top Z = shoulder_z = 15.23 mm)
        with Locations((gap - 2.5 / 2.0, 0.0, (shelf_z + shoulder_z) / 2.0)):
            Box(2.5, blen, shoulder_z - shelf_z)

        # 5. Gusset rib underneath
        with BuildSketch(Plane.XZ):
            Polygon([
                (2.0, rail_bottom_z),
                (gap + shelf_inward - 2.0, shelf_z - shelf_t),
                (2.0, shelf_z - shelf_t),
            ])
        extrude(amount=(blen - 8.0) / 2.0, both=True)

        # 6. 2x M5 counterbored holes through rail mounting face
        for sy in (-10.0, 10.0):
            with Locations((8.0, sy, rail_slot_z)):
                with BuildSketch(Plane.YZ):
                    Circle(5.3 / 2.0)
                extrude(amount=-12.0, mode=Mode.SUBTRACT)
                with BuildSketch(Plane.YZ.offset(2.5)):
                    Circle(9.5 / 2.0)
                extrude(amount=10.0, mode=Mode.SUBTRACT)

    return bp.part


def build_testbed_panel_pedestal(height: float = 72.03) -> bd.Solid:
    """
    Freestanding 72.03 mm pedestal supporting the plain display glass sheet from the baseboard.
    
    Height calculation:
      - 40.0 mm rail riser height off baseboard.
      - 2020 rail bottom at Z = -35.23 mm -> baseboard at Z = -75.23 mm.
      - Plain glass underside is at Z = -3.20 mm.
      - Required pedestal height = -3.20 - (-75.23) = 72.03 mm.
      
    Features:
      - 52 mm x 52 mm x 5.0 mm wide base with 4x M4 screw holes.
      - 28 mm x 28 mm central hollow column (3.0 mm walls) for fast, rigid printing.
      - Top flat glass platform (40.0 mm x 40.0 mm x 4.0 mm) with rounded edges directly cradling glass underside.
      - Hollow weight-reduction / material-saving core.
    """
    base_size = 52.0
    base_t = 5.0
    col_size = 28.0
    col_wall = 3.0
    top_pad_size = 40.0
    top_pad_t = 4.0

    with BuildPart() as bp:
        # 1. Base flange
        with BuildSketch(Plane.XY):
            RectangleRounded(base_size, base_size, 4.0)
        extrude(amount=base_t)

        # 2. Main pedestal column
        with BuildSketch(Plane.XY.offset(base_t - EPS)):
            RectangleRounded(col_size, col_size, 2.5)
        extrude(amount=height - top_pad_t - base_t + EPS)

        # 3. Top glass seating platform
        with BuildSketch(Plane.XY.offset(height - top_pad_t)):
            RectangleRounded(top_pad_size, top_pad_size, 3.0)
        extrude(amount=top_pad_t)

        # 4. Hollow weight-reduction / material-saving core (bottom opening)
        core_size = col_size - 2.0 * col_wall
        with BuildSketch(Plane.XY.offset(-EPS)):
            RectangleRounded(core_size, core_size, 2.0)
        extrude(amount=height - top_pad_t, mode=Mode.SUBTRACT)

        # 5. 4x M4 base mounting holes (pitch 40 mm)
        for sx in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                with Locations((sx * 20.0, sy * 20.0, -EPS)):
                    with BuildSketch(Plane.XY):
                        Circle(4.3 / 2.0)
                    extrude(amount=base_t + 2.0 * EPS, mode=Mode.SUBTRACT)
                    with BuildSketch(Plane.XY.offset(base_t - 2.0)):
                        Circle(8.0 / 2.0)
                    extrude(amount=3.0, mode=Mode.SUBTRACT)

    return bp.part


__all__ = [
    "build_testbed_rail_riser_foot",
    "build_testbed_rail_panel_bracket",
    "build_testbed_panel_pedestal",
]
