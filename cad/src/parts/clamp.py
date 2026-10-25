"""
PROJECT A.R.C. – Motor Clamp Module (src/parts/clamp.py)
========================================================
3D-printable 25GA-370 gearmotor split clamp:
- Internal bore diameter: tightened to Ø24.8 mm for positive mechanical clamping under bolt torque.
- Wall thickness: 3.5 mm.
- Split gap: 2.5 mm along XZ at Y = 0.
- Base mounting flange: 2x Ø3.4 mm M3 clearance holes at Y = ±19.0 mm (38.0 mm pitch).
- Pinch ears: 2x M3 clamping bores (Ø3.4 mm) at X = 8.0 and 16.0 mm (Z = 17.5 mm),
  featuring flat counterbored seating faces for standard DIN 912 M3 SHCS and hex nuts.
"""

from __future__ import annotations
import build123d as bd
from build123d import (
    BuildPart, BuildSketch,
    Cylinder, Box, extrude,
    Plane, Locations, Location, Vector, Mode, Align,
    Rectangle, Circle, Polygon, RectangleRounded,
    Solid,
)

from src.parameters import (
    PLATE_THICKNESS,
    MOTOR_PITCH,
)


def build_25ga_motor_clamp() -> bd.Solid:
    """
    Build the 3D-printable split clamp for 25GA-370 gearmotor (PETG).
    
    Coordinate frame:
      - Motor axis along X (motor centerline at Y = 0, Z = 0).
      - Inner mating face at X = 0.
      - Clamp extends from X = 0 to X = 20.0 mm along +X.
      - Base flange: X in [0, 4.0], ears at Y = ±19.0 mm with 2x Ø3.4 mm holes.
      - Cylindrical body: ID Ø24.8 mm, 3.5 mm wall (OD Ø31.8 mm).
      - Pinch ears on top (+Z, Z in [10, 23]): 2x M3 pinch screws at X = 8.0 and 16.0 mm,
        with 2.5 mm split gap, Ø3.4 mm clearance bores, and flat counterbored seating faces.
    """
    bore_d = 24.8          # Ø24.8 mm clamped bore
    bore_r = bore_d / 2.0  # 12.4 mm
    wall = 3.5            # 3.5 mm wall thickness
    outer_r = bore_r + wall  # 15.9 mm (OD 31.8 mm)
    clamp_len = 20.0       # mm along X
    flange_t = 4.0        # mm base flange thickness along X
    ear_pitch = 38.0       # 2x M3 mounting holes at Y = ±19.0 mm
    ear_r = 5.5            # flange ear radius
    split_gap = 2.5        # mm pinch gap

    with BuildPart() as bp:
        # 1. Main cylindrical collar (along X from 0 to clamp_len)
        with BuildSketch(Plane.YZ):
            Circle(outer_r)
        extrude(amount=clamp_len)

        # 2. Base mounting flange (X in [0, flange_t], ears at Y = ±19.0 mm)
        with BuildSketch(Plane.YZ):
            with Locations((0.0, 0.0)):
                RectangleRounded(ear_pitch + 2 * ear_r, 14.0, ear_r)
            for sy in (-1.0, 1.0):
                with Locations((sy * ear_pitch / 2.0, 0.0)):
                    Circle(ear_r)
        extrude(amount=flange_t)

        # 3. Pinch ear blocks on top (+Z, Z from 10 to 22.5 mm, along X)
        with BuildSketch(Plane.YZ):
            with Locations((0.0, 16.5)):
                RectangleRounded(18.0, 12.0, 2.0)
        extrude(amount=clamp_len)

        # 4. Central bore for 25GA motor can (Ø24.8 mm through-bore)
        with BuildSketch(Plane.YZ.offset(-1.0)):
            Circle(bore_r)
        extrude(amount=clamp_len + 2.0, mode=Mode.SUBTRACT)

        # 5. Base flange 2x M3 mounting through-holes (at Y = ±19.0 mm, Z = 0)
        for sy in (-1.0, 1.0):
            with BuildSketch(Plane.YZ.offset(-1.0)):
                with Locations((sy * ear_pitch / 2.0, 0.0)):
                    Circle(1.7)  # Ø3.4 mm M3 clearance
            extrude(amount=flange_t + 2.0, mode=Mode.SUBTRACT)

        # 6. Split relief slot (2.5 mm wide along XZ plane at Y = 0, cutting top from Z=10 to 25 mm)
        with Locations((clamp_len / 2.0, 0.0, 17.0)):
            Box(clamp_len + 2.0, split_gap, 18.0, mode=Mode.SUBTRACT)

        # 7. Pinch ears 2x M3 clamping screw holes & flat counterbores (along Y, at X = 8.0 and 16.0 mm, Z = 17.5 mm)
        for sx in (8.0, 16.0):
            # Through-bore Ø3.4 mm across both ears
            with Locations((sx, -10.0, 17.5)):
                with BuildSketch(Plane.XZ):
                    Circle(1.7)
                extrude(amount=20.0, mode=Mode.SUBTRACT)

            # Flat counterbored seating face for DIN 912 M3 socket head (at Y = -9.0 down to -7.0 mm)
            with Locations((sx, -9.01, 17.5)):
                with BuildSketch(Plane.XZ):
                    Circle(3.1)  # Ø6.2 mm counterbore
                extrude(amount=2.01, mode=Mode.SUBTRACT)

            # Flat counterbored seating face for M3 hex nut (at Y = +9.0 down to +7.0 mm)
            with Locations((sx, 9.01, 17.5)):
                with BuildSketch(Plane.XZ):
                    Circle(3.25)  # Ø6.5 mm counterbore
                extrude(amount=-2.01, mode=Mode.SUBTRACT)

    return bp.part


def build_n20_motor_clamp() -> bd.Solid:
    """One-piece saddle clamp for the N20 12×10×15 mm gearbox."""
    body_w = 16.0
    body_h = 12.0
    clamp_l = 12.0
    pocket_w = 12.2
    pocket_h = 10.2
    ear_span = 30.0
    ear_t = 3.0
    hole_pitch = 22.0
    hole_d = 3.4

    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            RectangleRounded(body_w, clamp_l, 2.0)
            RectangleRounded(ear_span, clamp_l, 2.0)
        extrude(amount=body_h)

        with Locations((0.0, 0.0, -0.5)):
            with BuildSketch(Plane.XY):
                Rectangle(pocket_w, clamp_l + 2.0)
            extrude(amount=pocket_h + 0.5, mode=Mode.SUBTRACT)

        with Locations((0.0, 0.0, ear_t)):
            for sx in (-1.0, 1.0):
                with Locations((sx * (ear_span + body_w) / 4.0, 0.0)):
                    with BuildSketch(Plane.XY):
                        Rectangle((ear_span - body_w) / 2.0 + 1.0, clamp_l + 2.0)
                    extrude(amount=body_h, mode=Mode.SUBTRACT)

        for sx in (-1.0, 1.0):
            with Locations((sx * hole_pitch / 2.0, 0.0, -0.5)):
                with BuildSketch(Plane.XY):
                    Circle(hole_d / 2.0)
                extrude(amount=ear_t + 1.0, mode=Mode.SUBTRACT)

    return bp.part


build_clamp = build_25ga_motor_clamp

__all__ = [
    "build_25ga_motor_clamp",
    "build_n20_motor_clamp",
    "build_clamp",
]
