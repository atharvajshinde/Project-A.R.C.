"""
PROJECT A.R.C. – COTS: 2020 Aluminium Extrusion & M5 T-Nuts
============================================================
Parametric true-profile B-Rep models for 2020 structural extrusion and hardware.
"""

from __future__ import annotations
import build123d as bd
from build123d import (
    BuildPart, BuildSketch, BuildLine,
    Box, Cylinder, extrude,
    Plane, Locations, Location, Vector, Mode, Align,
    Rectangle, Circle, Polygon, make_face,
)

from .dims import (
    EXTRUSION_WIDTH, EXTRUSION_HEIGHT, EXTRUSION_CENTER_BORE_D,
    EXTRUSION_SLOT_OPEN, EXTRUSION_SLOT_DEPTH, EXTRUSION_LIP_THICKNESS,
    EXTRUSION_SLOT_BASE_W, TNUT_M5_LENGTH, TNUT_M5_WIDTH, TNUT_M5_HEIGHT,
    TNUT_M5_THREAD_D,
)

# Cache generated extrusions by (length, slot_type) to avoid redundant B-Rep computations
_EXTRUSION_CACHE = {}


def _make_2020_profile_sketch(is_v_slot: bool = True):
    """Create a 2D cross-section face for 2020 extrusion on Plane.XY."""
    w = EXTRUSION_WIDTH
    h = EXTRUSION_HEIGHT
    cb_r = EXTRUSION_CENTER_BORE_D / 2.0
    slot_open = EXTRUSION_SLOT_OPEN
    slot_dep = EXTRUSION_SLOT_DEPTH
    lip_t = EXTRUSION_LIP_THICKNESS
    base_w = EXTRUSION_SLOT_BASE_W

    with BuildSketch(Plane.XY) as s:
        # Base outer 20x20 square with rounded outer corners
        Rectangle(w, h)
        # Center core hole
        Circle(cb_r, mode=Mode.SUBTRACT)

        # 4 slot cuts
        for angle in (0.0, 90.0, 180.0, 270.0):
            with Locations(Location((0, 0, 0), (0, 0, angle))):
                # Outer slot entry
                with Locations((0.0, w / 2.0 - lip_t / 2.0)):
                    Rectangle(slot_open, lip_t, mode=Mode.SUBTRACT)
                # Inner cavity
                cav_h = slot_dep - lip_t
                cav_cy = w / 2.0 - lip_t - cav_h / 2.0
                with Locations((0.0, cav_cy)):
                    Rectangle(base_w, cav_h, mode=Mode.SUBTRACT)

                # V-slot 45 deg chamfer along slot outer lips
                if is_v_slot:
                    chamfer_size = 1.2
                    for sx in (-1.0, 1.0):
                        px = sx * (slot_open / 2.0)
                        py = w / 2.0
                        with Locations((px, py)):
                            # Triangular cutout
                            Polygon(
                                [
                                    (0.0, 0.0),
                                    (-sx * chamfer_size, 0.0),
                                    (0.0, -chamfer_size),
                                ],
                                mode=Mode.SUBTRACT,
                            )
    return s.sketch


def build_2020_extrusion(length: float, slot_type: str = "v_slot") -> bd.Solid:
    """
    Build a realistic 2020 aluminium extrusion rod.
    
    Coordinate frame:
      - Axis along local Z, centred at (0, 0) in X-Y.
      - Z extends from -length/2 to +length/2.
    
    Args:
      length: Extrusion length in mm.
      slot_type: 'v_slot' (with 45° wheel tracking lips) or 't_slot' (standard).
    """
    cache_key = (round(length, 3), slot_type)
    if cache_key in _EXTRUSION_CACHE:
        return _EXTRUSION_CACHE[cache_key].moved(Location())

    is_v = (slot_type == "v_slot")
    sketch = _make_2020_profile_sketch(is_v_slot=is_v)
    with BuildPart() as bp:
        with BuildSketch(Plane.XY.offset(-length / 2.0)):
            bd.add(sketch)
        extrude(amount=length)

    solid = bp.part
    _EXTRUSION_CACHE[cache_key] = solid
    return solid.moved(Location())


def build_m5_tnut() -> bd.Solid:
    """
    Build an M5 drop-in roll-in T-nut for 2020 extrusion (6 mm slot).
    
    Coordinate frame:
      - Centred on local origin.
      - Length along X (10 mm), width along Y (6 mm), height along Z (4.5 mm).
      - M5 threaded bore through Z axis.
    """
    with BuildPart() as bp:
        Box(TNUT_M5_LENGTH, TNUT_M5_WIDTH, TNUT_M5_HEIGHT, align=Align.CENTER)
        # Side guide wings
        with Locations((0.0, 0.0, TNUT_M5_HEIGHT / 2.0 - 1.0)):
            Box(TNUT_M5_LENGTH, TNUT_M5_WIDTH + 3.0, 2.0, align=Align.CENTER)
        # Threaded bore
        Cylinder(radius=TNUT_M5_THREAD_D / 2.0, height=TNUT_M5_HEIGHT + 2.0, mode=Mode.SUBTRACT)
    return bp.part
