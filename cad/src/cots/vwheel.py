"""
PROJECT A.R.C. – COTS: Mini V-Wheels & 684ZZ Bearings
======================================================
Detailed B-Rep models for OpenBuilds Mini V-Wheel, spacers, and 684ZZ bearings.
"""

from __future__ import annotations
import math
import build123d as bd
from build123d import (
    BuildPart, BuildSketch,
    Cylinder, Box, Cone, extrude, revolve,
    Plane, Locations, Location, Vector, Mode, Align,
    Rectangle, Circle, Polygon,
)

from .dims import (
    VWHEEL_MINI_OD, VWHEEL_MINI_WIDTH, VWHEEL_MINI_BORE,
    VWHEEL_MINI_V_DEPTH, VWHEEL_MINI_BEARING_ID,
    VWHEEL_SPACER_OD, VWHEEL_SPACER_LEN,
    BRG_684ZZ_OD, BRG_684ZZ_ID, BRG_684ZZ_WIDTH,
)

_VWHEEL_CACHE = None
_BEARING_CACHE = None


def build_mini_v_wheel(include_bearings: bool = True) -> bd.Solid:
    """
    Build a realistic Delrin Mini V-Wheel (OpenBuilds spec).
    
    Coordinate frame:
      - Axis along local Z, centred at origin in X-Y and Z.
      - Total width along Z: 8.8 mm (Z in [-4.4, +4.4]).
      - Outer diameter: 15.23 mm.
      - 90-degree V-groove around circumference.
      - Dual MR105ZZ bearing pockets (5 mm bore through).
    """
    global _VWHEEL_CACHE
    if _VWHEEL_CACHE is not None:
        return _VWHEEL_CACHE.moved(Location())

    od_r = VWHEEL_MINI_OD / 2.0         # 7.615 mm
    w = VWHEEL_MINI_WIDTH               # 8.8 mm
    bore_r = VWHEEL_MINI_BEARING_ID / 2.0  # 2.5 mm
    pocket_r = VWHEEL_MINI_BORE / 2.0   # 5.0 mm
    v_depth = VWHEEL_MINI_V_DEPTH       # 1.6 mm

    with BuildPart() as bp:
        # Base outer cylinder
        Cylinder(radius=od_r, height=w, align=Align.CENTER)

        # 90-degree V-groove cutout around circumference
        # Built via revolving a triangular sketch on Plane.XZ
        with BuildSketch(Plane.XZ) as v_sketch:
            Polygon(
                [
                    (od_r + 0.1, 0.0),
                    (od_r - v_depth, 0.0),
                    (od_r + 0.1, v_depth),
                ],
                mode=Mode.ADD,
            )
            Polygon(
                [
                    (od_r + 0.1, 0.0),
                    (od_r - v_depth, 0.0),
                    (od_r + 0.1, -v_depth),
                ],
                mode=Mode.ADD,
            )
        revolve(axis=bd.Axis.Z, mode=Mode.SUBTRACT)

        # 5 mm central axle through-bore
        Cylinder(radius=bore_r, height=w + 2.0, mode=Mode.SUBTRACT)

        # Dual bearing pockets from each face (10 mm diameter, 2.5 mm depth)
        for sz in (-1.0, 1.0):
            with Locations((0.0, 0.0, sz * (w / 2.0 - 1.25))):
                Cylinder(radius=pocket_r, height=2.5 + 0.01, mode=Mode.SUBTRACT)

    solid = bp.part
    _VWHEEL_CACHE = solid
    return solid.moved(Location())


def build_684zz_bearing() -> bd.Solid:
    """
    Build a realistic 684ZZ miniature ball bearing (4x9x4 mm).
    
    Coordinate frame:
      - Axis along local Z, centred at origin in X-Y and Z.
      - Outer diameter: 9.0 mm.
      - Inner bore: 4.0 mm.
      - Width: 4.0 mm (Z in [-2.0, +2.0]).
      - Outer/inner ring stepped relief and shield channel.
    """
    global _BEARING_CACHE
    if _BEARING_CACHE is not None:
        return _BEARING_CACHE.moved(Location())

    od_r = BRG_684ZZ_OD / 2.0    # 4.5 mm
    id_r = BRG_684ZZ_ID / 2.0    # 2.0 mm
    w = BRG_684ZZ_WIDTH          # 4.0 mm

    with BuildPart() as bp:
        # Main bearing ring
        Cylinder(radius=od_r, height=w, align=Align.CENTER)
        # Inner through bore
        Cylinder(radius=id_r, height=w + 2.0, mode=Mode.SUBTRACT)

        # Stamped metal shield relief channels on both faces
        shield_mid_r = (od_r + id_r) / 2.0
        shield_w = 0.8
        for sz in (-1.0, 1.0):
            with Locations((0.0, 0.0, sz * (w / 2.0 - 0.25))):
                Cylinder(radius=shield_mid_r + shield_w, height=0.51, mode=Mode.SUBTRACT)
            with Locations((0.0, 0.0, sz * (w / 2.0 - 0.25))):
                Cylinder(radius=shield_mid_r - shield_w, height=0.52, mode=Mode.ADD)

    solid = bp.part
    _BEARING_CACHE = solid
    return solid.moved(Location())


def build_vwheel_spacer(length: float = VWHEEL_SPACER_LEN, is_eccentric: bool = False) -> bd.Solid:
    """
    Build an aluminium spacer or eccentric spacer for V-wheel mounting.
    
    Coordinate frame:
      - Axis along local Z, Z in [0, length].
      - Outer diameter 8.0 mm (or 10 mm hex for eccentric).
      - M5 bore (5.1 mm).
    """
    bore_r = 2.55
    outer_r = VWHEEL_SPACER_OD / 2.0
    offset_x = 0.6 if is_eccentric else 0.0

    with BuildPart() as bp:
        if is_eccentric:
            # Hex body
            with BuildSketch(Plane.XY):
                Circle(outer_r + 1.0)
            extrude(amount=length)
        else:
            Cylinder(radius=outer_r, height=length, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Bore
        with Locations((offset_x, 0.0, 0.0)):
            Cylinder(radius=bore_r, height=length + 2.0, mode=Mode.SUBTRACT)

    return bp.part
