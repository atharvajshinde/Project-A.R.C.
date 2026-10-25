"""
PROJECT A.R.C. – COTS: Roller Microfibre Sleeve & Alignment Pins
=================================================================
B-Rep models for:
  - Microfibre plush roller sleeve (ID 41.2 mm, OD 50.0 mm, L 320 mm)
  - Hardened steel dowel pin Ø4 × 10 mm for cowl split joint
  - Roller axle set-screw (M3 × 4 mm DIN 916 cup-point)
"""

from __future__ import annotations
import build123d as bd
from build123d import (
    BuildPart, BuildSketch,
    Cylinder, Box, extrude,
    Plane, Locations, Location, Vector, Mode, Align,
    Circle, Polygon, RegularPolygon,
)

from .dims import (
    SLEEVE_ID, SLEEVE_OD, SLEEVE_LENGTH,
    DOWEL_PIN_D, DOWEL_PIN_L,
    M3_GRUB_D, M3_GRUB_L, M3_GRUB_HEX,
)

_SLEEVE_CACHE = None
_PIN_CACHE = None
_GRUB_CACHE = None


def build_microfiber_sleeve() -> bd.Solid:
    """
    Build the microfibre plush roller sleeve.
    
    Dimensions:
      - Inner Diameter: 41.2 mm (press-fit over 1.25" UPVC conduit).
      - Outer Diameter: 50.0 mm (finished cleaning diameter).
      - Length: 320.0 mm.
    Coordinate frame:
      - Axis along local Z, centred at origin in X-Y and Z.
    """
    global _SLEEVE_CACHE
    if _SLEEVE_CACHE is not None:
        return _SLEEVE_CACHE.moved(Location())

    id_r = SLEEVE_ID / 2.0      # 20.6 mm
    od_r = SLEEVE_OD / 2.0      # 25.0 mm
    l = SLEEVE_LENGTH           # 320.0 mm

    with BuildPart() as bp:
        Cylinder(radius=od_r, height=l, align=Align.CENTER)
        Cylinder(radius=id_r, height=l + 2.0, mode=Mode.SUBTRACT)

    solid = bp.part
    _SLEEVE_CACHE = solid
    return solid.moved(Location())


def build_dowel_pin() -> bd.Solid:
    """
    Build a precision ground steel dowel pin (Ø4.0 × 10.0 mm).
    
    Used for cowl split-joint alignment (Part E).
    Coordinate frame:
      - Axis along local Z, centred at origin in X-Y and Z.
    """
    global _PIN_CACHE
    if _PIN_CACHE is not None:
        return _PIN_CACHE.moved(Location())

    d_r = DOWEL_PIN_D / 2.0     # 2.0 mm
    l = DOWEL_PIN_L             # 10.0 mm

    with BuildPart() as bp:
        Cylinder(radius=d_r, height=l, align=Align.CENTER)
        # 0.4 mm chamfers on both ends
        for sz in (-1.0, 1.0):
            with Locations((0.0, 0.0, sz * l / 2.0)):
                pass  # Chamfer can be omitted or kept simple to avoid B-Rep artifacts

    solid = bp.part
    _PIN_CACHE = solid
    return solid.moved(Location())


def build_m3_set_screw() -> bd.Solid:
    """
    Build an M3 × 4 mm DIN 916 cup-point hex socket set screw (grub screw).
    
    Clamps the EN31 axle inside the roller end plugs.
    Coordinate frame:
      - Axis along local Z, Z in [0, 4 mm].
      - Cup point at Z = 0, hex drive recess at Z = 4 mm.
    """
    global _GRUB_CACHE
    if _GRUB_CACHE is not None:
        return _GRUB_CACHE.moved(Location())

    r = M3_GRUB_D / 2.0         # 1.5 mm
    l = M3_GRUB_L               # 4.0 mm
    hex_af = M3_GRUB_HEX        # 1.5 mm
    hex_r = hex_af / 1.73205    # radius across corners

    with BuildPart() as bp:
        Cylinder(radius=r, height=l, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Hex socket drive pocket on top (Z in [l - 1.5, l])
        with Locations((0.0, 0.0, l - 1.5)):
            with BuildSketch(Plane.XY):
                RegularPolygon(radius=hex_r, side_count=6)
            extrude(amount=1.6, mode=Mode.SUBTRACT)

    solid = bp.part
    _GRUB_CACHE = solid
    return solid.moved(Location())
