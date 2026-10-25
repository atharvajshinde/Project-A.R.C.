"""
PROJECT A.R.C. – COTS: 5015 Centrifugal Radial Blower Fan
==========================================================
Detailed B-Rep model of the 24V 5015 DC centrifugal blower fan.
Features:
  - Scroll volute housing (50 × 50 × 15 mm envelope)
  - Circular air intake eye (concentric with duct ID 17)
  - Central impeller motor hub
  - Tangential exhaust nozzle
  - 4 × M3 mounting tab ears on 30 mm bolt circle at 45°, 135°, 225°, 315°
    matched to Part E Blower Cowl flange.

Origin convention:
  - Central intake eye centred at (0, 0) in X-Y.
  - Underside (mounting face to cowl flange) at Z = 0.
  - Fan body extends along Z in [0, 15 mm].
"""

from __future__ import annotations
import math
import build123d as bd
from build123d import (
    BuildPart, BuildSketch,
    Cylinder, Box, extrude,
    Plane, Locations, Location, Vector, Mode, Align,
    Rectangle, Circle, RectangleRounded,
)

from .dims import (
    BLOWER_5015_SIZE, BLOWER_5015_THICKNESS, BLOWER_5015_INLET_D,
    BLOWER_5015_HUB_D, BLOWER_5015_OUTLET_W, BLOWER_5015_OUTLET_H,
    BLOWER_5015_FLANGE_BC, BLOWER_5015_HOLE_D,
)

_BLOWER_CACHE = None


def build_5015_blower() -> bd.Solid:
    """
    Build a realistic 5015 radial blower fan.
    
    Coordinate frame:
      - Intake eye centred at (0, 0) in X-Y.
      - Mounting face at Z = 0, fan height 15 mm (Z in [0, 15]).
      - Outlet nozzle extends toward -X / +Y.
      - 4 mounting ears on 30 mm bolt circle at 45° angles.
    """
    global _BLOWER_CACHE
    if _BLOWER_CACHE is not None:
        return _BLOWER_CACHE.moved(Location())

    th = BLOWER_5015_THICKNESS      # 15 mm
    body_r = 25.0                   # 50 mm diameter scroll body
    bc_r = BLOWER_5015_FLANGE_BC / 2.0  # 15 mm bolt circle radius
    hole_r = BLOWER_5015_HOLE_D / 2.0   # 1.6 mm
    ear_w = 7.0                     # mounting ear tab width
    ear_t = 3.5                     # ear thickness from base

    with BuildPart() as bp:
        # Main round volute body
        with BuildSketch(Plane.XY):
            Circle(body_r)
        extrude(amount=th)

        # Tangential outlet spout extending toward -X / +Y
        with Locations((-14.0, 15.0, 0.0)):
            Box(18.0, 20.0, th, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # 4 mounting ear tabs on 30 mm bolt circle at 45°, 135°, 225°, 315°
        for ang in (45.0, 135.0, 225.0, 315.0):
            rad = math.radians(ang)
            ex = bc_r * math.cos(rad)
            ey = bc_r * math.sin(rad)
            with Locations((ex, ey, 0.0)):
                with BuildSketch(Plane.XY):
                    Circle(ear_w / 2.0)
                extrude(amount=ear_t)
                # M3 screw clearance hole through tab
                with Locations((0.0, 0.0, -0.5)):
                    Cylinder(radius=hole_r, height=th + 1.0, mode=Mode.SUBTRACT)

        # Intake eye depression on top face (+Z)
        with Locations((0.0, 0.0, th - 3.0)):
            Cylinder(radius=16.0, height=3.5, mode=Mode.SUBTRACT)

        # Central impeller motor hub
        with Locations((0.0, 0.0, th - 2.5)):
            Cylinder(radius=10.0, height=2.0)

        # Bottom intake bore matching cowl duct (ID 17 mm)
        with Locations((0.0, 0.0, -0.5)):
            Cylinder(radius=8.5, height=6.0, mode=Mode.SUBTRACT)

        # Exhaust rectangular air chamber hollowed inside outlet
        with Locations((-14.0, 16.0, 2.0)):
            Box(14.0, 16.0, th - 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

    solid = bp.part
    _BLOWER_CACHE = solid
    return solid.moved(Location())
