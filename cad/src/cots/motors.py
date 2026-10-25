"""
PROJECT A.R.C. – COTS: Drive Motors & Homing Limit Switch
==========================================================
Detailed B-Rep models for:
  - N20 Micro Metal Gear Motor (12×10×15 mm brass gearbox, Robu SKU 75800)
  - 25GA-370 Geared Motor (optional variant)
  - ONPOW Roller Short Lever Limit Switch (Robu SKU R255405)

Coordinate frames:
  - N20 Gearmotor: Gearbox centred in X-Z, back face at Y = 0, output shaft
    pointing toward +Y (or along length axis).
  - Limit Switch: Body flat on bottom face, lever arm extending along length.
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

from .dims import (
    N20_GEARBOX_W, N20_GEARBOX_H, N20_GEARBOX_L,
    N20_MOTOR_D, N20_MOTOR_FLAT_H, N20_MOTOR_L,
    N20_SHAFT_D, N20_SHAFT_L, N20_SHAFT_FLAT_D, N20_SHAFT_FLAT_L,
    LIMIT_SW_BODY_L, LIMIT_SW_BODY_H, LIMIT_SW_BODY_W,
    LIMIT_SW_HOLE_SPACING, LIMIT_SW_HOLE_D,
    LIMIT_SW_LEVER_L, LIMIT_SW_ROLLER_D, LIMIT_SW_ROLLER_W,
)

_N20_CACHE = None
_LIMIT_SW_CACHE = None
_MOTOR_25GA_CACHE = None


def build_n20_gearmotor() -> bd.Solid:
    """
    Build an authentic N20 micro metal gear motor.
    
    Coordinate frame:
      - Gearbox body: 12 mm wide (X) × 10 mm high (Z) × 15 mm long (Y).
      - Gearbox front face (shaft exit) at Y = N20_GEARBOX_L (15 mm).
      - Motor can body extends from Y = 0 to Y = -N20_MOTOR_L (-15 mm).
      - Output D-shaft extends from Y = 15 to Y = 25 mm along +Y.
      - Centred on (0, 0) in X and Z.
    """
    global _N20_CACHE
    if _N20_CACHE is not None:
        return _N20_CACHE.moved(Location())

    gw, gh, gl = N20_GEARBOX_W, N20_GEARBOX_H, N20_GEARBOX_L
    ml = N20_MOTOR_L
    mr = N20_MOTOR_D / 2.0
    shaft_r = N20_SHAFT_D / 2.0
    shaft_l = N20_SHAFT_L

    with BuildPart() as bp:
        # 1. Brass spur gearbox (12 × 15 × 10 mm)
        with Locations((0.0, gl / 2.0, 0.0)):
            Box(gw, gl, gh, align=Align.CENTER)

        # 2. Brushed DC motor can (Ø12 mm with 10 mm flats, length 15 mm in -Y)
        with BuildSketch(Plane.XZ):
            Circle(mr)
            # Cut flats on top and bottom
            Rectangle(gw + 2.0, mr - gh / 2.0 + 0.01,
                      align=(Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
            Rectangle(gw + 2.0, mr - gh / 2.0 + 0.01,
                      align=(Align.CENTER, Align.MAX), mode=Mode.SUBTRACT)
        extrude(amount=ml)

        # 3. Motor rear terminal endcap and solder lugs (-Y face)
        with Locations((0.0, -ml, 0.0)):
            # Rear insulating endcap plate
            with BuildSketch(Plane.XZ):
                RectangleRounded(gw - 2.0, gh - 2.0, 1.0)
            extrude(amount=0.8)
            # Solder terminal lugs solidly attached to endcap
            for sx in (-3.5, 3.5):
                with Locations((sx, -1.0, 0.0)):
                    Box(1.5, 2.0, 3.0, align=Align.CENTER)

        # 4. Output bearing collar & D-shaft (+Y face of gearbox)
        with Locations((0.0, gl, 0.0)):
            # Bearing collar extending into +Y
            with BuildSketch(Plane.XZ):
                Circle(2.2)
            extrude(amount=-1.5)
            # D-shaft extending further into +Y
            with BuildSketch(Plane.XZ.offset(-1.5)):
                Circle(shaft_r)
                # D-flat cutout
                flat_depth = N20_SHAFT_D - N20_SHAFT_FLAT_D
                with Locations((0.0, shaft_r - flat_depth / 2.0)):
                    Rectangle(shaft_r * 2.5, flat_depth, mode=Mode.SUBTRACT)
            extrude(amount=-(shaft_l - 1.5))

    solid = bp.part
    _N20_CACHE = solid
    return solid.moved(Location())


def build_25ga370_motor(shaft_len: float = 11.5) -> bd.Solid:
    """
    Build a 25GA-370 geared motor (verified dimensions).
    
    Coordinate frame:
      - Cylindrical body Ø25 mm × 54.0 mm total length along Z (Z in [0, 54]).
      - Front bearing boss Ø7.0 mm × 2.0 mm height (Z in [54, 56]).
      - Output D-shaft Ø4.0 mm × shaft_len along +Z (flat at 3.5 mm).
      - 2× M3 threaded holes on 17.0 mm PCD on front face.
      - Centred on (0, 0) in X-Y.
    """
    global _MOTOR_25GA_CACHE
    if _MOTOR_25GA_CACHE is not None and getattr(_MOTOR_25GA_CACHE, "_shaft_len", None) == shaft_len:
        return _MOTOR_25GA_CACHE.moved(Location())

    shaft_r = 2.0  # Ø4 mm
    flat_depth = 0.5  # 3.5 mm flat

    with BuildPart() as bp:
        # Gearbox + motor cylinder body (Ø25 × 54 mm)
        Cylinder(radius=12.5, height=54.0, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Output bearing boss (Ø7 × 2.0 mm)
        with Locations((0.0, 0.0, 54.0)):
            Cylinder(radius=3.5, height=2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Output 4.0 mm D-shaft
        with Locations((0.0, 0.0, 56.0)):
            with BuildSketch(Plane.XY):
                Circle(shaft_r)
                with Locations((0.0, shaft_r - flat_depth / 2.0)):
                    Rectangle(shaft_r * 2.5, flat_depth, mode=Mode.SUBTRACT)
            extrude(amount=shaft_len)

        # 2× M3 mounting holes on 17.0 mm PCD on front face (Z = 54.0)
        with Locations((0.0, 0.0, 54.0)):
            for sy in (-8.5, 8.5):
                with Locations((0.0, sy, 0.0)):
                    with BuildSketch(Plane.XY):
                        Circle(1.5)  # M3 tap pilot
                    extrude(amount=-4.0, mode=Mode.SUBTRACT)

    solid = bp.part
    solid._shaft_len = shaft_len
    _MOTOR_25GA_CACHE = solid
    return solid.moved(Location())


def build_onpow_limit_switch() -> bd.Solid:
    """
    Build an ONPOW miniature roller-lever limit switch (Robu SKU R255405).
    
    Coordinate frame:
      - Switch body: 20 mm length (Y), 10 mm height (Z), 6 mm width (X).
      - Underside at Z = 0.
      - Centred in X.
      - Roller lever extends above top face.
    """
    global _LIMIT_SW_CACHE
    if _LIMIT_SW_CACHE is not None:
        return _LIMIT_SW_CACHE.moved(Location())

    bl, bh, bw = LIMIT_SW_BODY_L, LIMIT_SW_BODY_H, LIMIT_SW_BODY_W
    hole_pitch = LIMIT_SW_HOLE_SPACING
    hole_r = LIMIT_SW_HOLE_D / 2.0

    with BuildPart() as bp:
        # Main rectangular snap-switch housing
        with BuildSketch(Plane.XY):
            RectangleRounded(bw, bl, 1.0)
        extrude(amount=bh)

        # 2 mounting through-holes (along X)
        for sy in (-1.0, 1.0):
            with Locations((0.0, sy * hole_pitch / 2.0, bh / 2.0)):
                with BuildSketch(Plane.YZ.offset(-bw / 2.0 - 0.5)):
                    Circle(hole_r)
                extrude(amount=bw + 1.0, mode=Mode.SUBTRACT)

        # 3 solder terminal lugs on bottom (-Z)
        for sy in (-bl / 3.0, 0.0, bl / 3.0):
            with Locations((0.0, sy, -2.5)):
                Box(0.8, 2.5, 3.0, align=Align.CENTER)

        # Actuator leaf spring lever with miniature roller
        lever_ang = 15.0
        with Locations((0.0, -bl / 2.0 + 3.0, bh)):
            # Lever arm
            with Locations((0.0, 5.0, 2.0)):
                Box(1.2, 12.0, 0.6, align=Align.CENTER)
            # Roller at tip
            with Locations((0.0, 12.0, 3.5)):
                with BuildSketch(Plane.YZ.offset(-LIMIT_SW_ROLLER_W / 2.0)):
                    Circle(LIMIT_SW_ROLLER_D / 2.0)
                extrude(amount=LIMIT_SW_ROLLER_W)

    solid = bp.part
    _LIMIT_SW_CACHE = solid
    return solid.moved(Location())
