"""
PROJECT A.R.C. – ESP32 Adapter Sled (src/parts/sled.py)
======================================================
Custom 3D-printable adapter sled mounting directly to the chassis tray standoffs.
- Base plate perimeter flange: 77.0 × 63.0 × 2.4 mm with R3.0 mm filleted corners.
- 4x M3 through-hole mounting pattern: Ø3.4 mm clearance with Ø6.0 mm counterbores (depth 1.2 mm)
  on a 71.0 mm × 57.0 mm grid matching chassis tray standoffs.
- Internal pocket clearance width: 28.6 mm (accommodates 28.0 mm wide 1.0-inch pitch 38-pin ESP32 PCB
  with 0.3 mm per-side clearance).
- Inner pocket length: 55.6 mm (accommodating 54.6 mm - 55.0 mm 38-pin PCB length).
- PCB slide-in channel height: 2.0 mm vertical clearance under top retention lips (for 1.6 mm PCB).
- Top retention lip inward overhang: 1.2 mm on left and right rails.
- Open front end for sliding PCB in and clearing the USB port.
- Rear short end (+Y) stop wall of height 3.5 mm above base plate.
- Expanded central floor cutout window: 24.0 mm × 48.0 mm for clean frame design and DuPont jumper wiring access.
"""

from __future__ import annotations
from typing import Dict
import build123d as bd
from build123d import (
    BuildPart, BuildSketch,
    Plane, Mode, Align,
    extrude,
    Locations, Location,
    Box, Cylinder,
    Rectangle, RectangleRounded, Polygon, Circle,
    Solid,
)

_CACHE: Dict[str, bd.Solid] = {}


def build_esp32_adapter_sled() -> bd.Solid:
    """
    Build the 3D-printable ESP32 Adapter Sled (PETG).
    Underside rests at Z = 0.
    """
    if "esp32_adapter_sled" in _CACHE:
        return _CACHE["esp32_adapter_sled"].moved(Location())

    base_l = 81.0         # mm along X (extended to provide full wall around M3 holes)
    base_w = 65.0         # mm along Y
    base_t = 2.5          # mm flange thickness
    corner_r = 2.5        # mm fillet radius
    hole_px = 71.0        # mm hole pitch along X (matches tray standoffs)
    hole_py = 57.0        # mm hole pitch along Y (matches tray standoffs)
    hole_d = 3.4          # mm M3 clearance bore
    cbore_d = 6.2         # mm M3 counterbore diameter
    cbore_depth = 1.2     # mm M3 counterbore depth into flange

    pocket_w = 28.6       # mm internal pocket clearance width (28.0 mm board + 0.3 mm per-side clearance)
    pocket_l = 55.6       # mm internal pocket length (accommodates 54.6 - 55.0 mm board)
    channel_h = 2.0       # mm vertical clearance under top retention lips (for 1.6 mm thick PCB)
    lip_overhang = 1.2    # mm inward retention lip overhang on left and right rails
    rim_h = 3.5           # mm rim wall height above base plate
    wall_t = 2.0          # mm rim wall thickness
    cutout_w = 26.6       # mm central through-cutout width through floor (widened for 1.0" pin header clearance)
    cutout_l = 48.0       # mm central through-cutout length

    outer_w = pocket_w + 2.0 * wall_t            # 32.6 mm
    lip_gap_w = pocket_w - 2.0 * lip_overhang    # 26.2 mm

    y_back_inner = pocket_l / 2.0                # +27.8 mm (inner face of back stop wall)
    y_back_outer = y_back_inner + wall_t         # +29.8 mm (outer face of back wall)
    y_front = -pocket_l / 2.0                    # -27.8 mm (open front entrance)

    cradle_l = y_back_outer - y_front            # 57.6 mm total cradle length
    cradle_y_center = (y_back_outer + y_front) / 2.0  # +1.0 mm

    with BuildPart() as bp:
        # 1. Base perimeter flange with filleted corners
        with BuildSketch(Plane.XY):
            RectangleRounded(base_l, base_w, corner_r)
        extrude(amount=base_t)

        # 2. Outer cradle block with rounded corners
        with Locations((0.0, cradle_y_center, base_t)):
            with BuildSketch(Plane.XY):
                RectangleRounded(outer_w, cradle_l, 1.5)
            extrude(amount=rim_h)

        # 3. Slide-in pocket cavity under top lips (28.6 mm wide x 2.0 mm high)
        # Front is open (-Y), extending past the front edge to clear USB and allow sliding in
        with Locations((0.0, y_back_inner, base_t)):
            Box(pocket_w, pocket_l + 10.0, channel_h, align=(Align.CENTER, Align.MAX, Align.MIN), mode=Mode.SUBTRACT)

        # 4. Top opening between retention lips (26.2 mm wide, full rim height)
        with Locations((0.0, y_back_inner, base_t)):
            Box(lip_gap_w, pocket_l + 10.0, rim_h + 1.0, align=(Align.CENTER, Align.MAX, Align.MIN), mode=Mode.SUBTRACT)

        # 5. Expanded central through-cutout through floor for DuPont header wiring (24.0 x 48.0 mm)
        with Locations((0.0, 0.0, -1.0)):
            with BuildSketch(Plane.XY):
                Rectangle(cutout_w, cutout_l)
            extrude(amount=base_t + 2.0, mode=Mode.SUBTRACT)

        # 6. 4x M3 through-hole mounting pattern with counterbores (71.0 × 57.0 mm grid)
        for sx in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                hx = sx * hole_px / 2.0
                hy = sy * hole_py / 2.0
                # Through-bore Ø3.4 mm cutting all the way through
                with Locations((hx, hy, -1.0)):
                    with BuildSketch(Plane.XY):
                        Circle(hole_d / 2.0)
                    extrude(amount=base_t + 2.0, mode=Mode.SUBTRACT)
                # Counterbore Ø6.2 mm from top face (base_t) down by cbore_depth
                with Locations((hx, hy, base_t - cbore_depth)):
                    with BuildSketch(Plane.XY):
                        Circle(cbore_d / 2.0)
                    extrude(amount=cbore_depth + 1.0, mode=Mode.SUBTRACT)

    solid = bp.part
    _CACHE["esp32_adapter_sled"] = solid
    return solid.moved(Location())


def make_esp32_adapter_sled() -> bd.Solid:
    """Simplified envelope representation of the ESP32 adapter sled for fast simple mode."""
    return build_esp32_adapter_sled()


build_sled = build_esp32_adapter_sled

__all__ = [
    "build_esp32_adapter_sled",
    "make_esp32_adapter_sled",
    "build_sled",
]
