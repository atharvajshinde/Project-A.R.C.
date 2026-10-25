"""
PROJECT A.R.C. – Limit Switch Trip Dog
=======================================
Source: phase2.scad  ->  build123d B-Rep implementation.

Function
--------
  Cam dog that locks into the Y-axis 2020 V-slot rail to actuate a
  roller-lever microswitch for gantry homing.

Coordinate system (module local)
---------------------------------
  Rail axis = X.
  Rail face = Z = 0 plane (dog body rises into +Z).
  Alignment key projects into -Z (into the 6 mm slot).
  Cam profile is in the X-Z plane, extruded along Y (dog body width = 18 mm).

Exported builders
-----------------
  build_limit_switch_dog()  -> Solid
"""

from __future__ import annotations
import math
from build123d import (
    BuildPart, BuildSketch, BuildLine,
    Plane, Axis, Mode, Align,
    extrude, fillet,
    Locations, Location,
    Box, Cylinder,
    Circle, Rectangle, Polygon, Polyline, make_face,
    Solid, Part,
    Vector,
)
import build123d as bd
from .parameters import (
    EPS,
    DOG_PROFILE, DOG_BODY_W, DOG_H_BASE, DOG_H_CAM, DOG_TOTAL_LEN,
    DOG_X_B, DOG_X_C, DOG_X_D, DOG_HOLE_X,
    DOG_KEY_W, DOG_KEY_D, DOG_KEY_MARGIN, DOG_RELIEF_LEN,
    DOG_CBORE_D, DOG_CBORE_DEPTH, DOG_FLOOR_T,
    DOG_ENGAGEMENT, DOG_RELIEF_LEN,
    M5_CLEAR_D, M5_HEAD_D, M5_HEAD_H,
    LIP_THICKNESS, SLOT_OPEN,
)

# ---------------------------------------------------------------------------
# Validation assertions (mirror of OpenSCAD asserts)
# ---------------------------------------------------------------------------

def _validate():
    assert DOG_KEY_D < LIP_THICKNESS, \
        f"Key depth {DOG_KEY_D} must be < lip thickness {LIP_THICKNESS}"
    assert DOG_KEY_W < SLOT_OPEN, \
        f"Key width {DOG_KEY_W} must be < slot opening {SLOT_OPEN}"
    assert DOG_ENGAGEMENT >= 3.5, \
        f"M5 thread engagement too short: {DOG_ENGAGEMENT:.2f} mm"
    assert DOG_FLOOR_T >= 1.2, \
        f"Floor under screw head too thin: {DOG_FLOOR_T:.2f} mm"
    boss_len = DOG_TOTAL_LEN - DOG_X_D
    assert boss_len >= DOG_CBORE_D + 4.0, \
        f"Boss zone too short for counterbore: {boss_len:.2f} mm"


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_limit_switch_dog() -> bd.Solid:
    """
    Cam trip dog for Y-axis 2020 V-slot rail homing.

    Geometry (local frame)
    ----------------------
      X = along rail axis.
      Y = across rail face (body width = 18 mm, centred at Y=0).
      Z = normal to rail face (+Z = up, -Z = into slot).
      Z = 0 = rail top face.

    Features
    --------
      - Cam body: XZ profile (lead ramp, plateau, exit ramp, boss zone)
        extruded symmetrically from Y = -9 to Y = +9.
      - Alignment key: 5.8 mm wide x 1.5 mm deep, rides in 6 mm slot, cut
        around screw position for clearance.
      - M5 counterbored through-bolt + ISO 7380 button-head pocket.
    """
    _validate()

    bw = DOG_BODY_W      # 18.0 mm  (Y span)

    # ---- 1. Cam body: extrude the XZ profile along Y ----
    # DOG_PROFILE is (x, z) vertices; extrude along Y (Y = -bw/2 to +bw/2)
    with BuildPart() as cam_bp:
        with BuildSketch(Plane.XZ.offset(-bw / 2.0)):
            with BuildLine():
                Polyline(*[(x, z) for (x, z) in DOG_PROFILE], close=True)
            make_face()
        extrude(amount=bw)

    result = cam_bp.part

    # ---- 2. Alignment key (rides in 6 mm V-slot opening) ----
    key_x0 = DOG_KEY_MARGIN
    key_x1 = DOG_TOTAL_LEN - DOG_KEY_MARGIN
    key_len = key_x1 - key_x0

    with BuildPart() as key_bp:
        Box(key_len, DOG_KEY_W, DOG_KEY_D + EPS,
            align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.MAX))
        key_bp.part = key_bp.part.move(Location(Vector(key_x0, 0.0, 0.0)))

    # Add key, then remove relief gap around screw hole
    result = result.fuse(key_bp.part)

    # Key relief cut around the screw position
    relief_x0 = DOG_HOLE_X - DOG_RELIEF_LEN / 2.0
    with BuildPart() as relief_bp:
        Box(DOG_RELIEF_LEN, DOG_KEY_W + 2.0, DOG_KEY_D + EPS + 1.0,
            align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.MAX))
        relief_bp.part = relief_bp.part.move(Location(Vector(relief_x0, 0.0, 0.0)))

    result = result.cut(relief_bp.part)

    # ---- 3. M5 clearance through-hole + button-head counterbore ----
    # Clearance hole through full Z range (-key_d-1 to h_base+1)
    z_bottom = -DOG_KEY_D - 1.0
    z_top = DOG_H_BASE + 1.0

    with BuildPart() as bolt_bp:
        with BuildSketch(Plane.XY.offset(z_bottom)):
            with Locations((DOG_HOLE_X, 0.0)):
                Circle(M5_CLEAR_D / 2.0)
        extrude(amount=z_top - z_bottom)
    result = result.cut(bolt_bp.part)

    # Counterbore (button-head pocket) from dog_floor_t to z_top
    with BuildPart() as cbore_bp:
        with BuildSketch(Plane.XY.offset(DOG_FLOOR_T)):
            with Locations((DOG_HOLE_X, 0.0)):
                Circle(DOG_CBORE_D / 2.0)
        extrude(amount=z_top - DOG_FLOOR_T)
    result = result.cut(cbore_bp.part)

    return result
