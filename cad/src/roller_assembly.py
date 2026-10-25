"""
PROJECT A.R.C. – Part D: Roller Core & Drive Assembly
=====================================================
Source: phase1.scad  ->  build123d B-Rep implementation.

CRITICAL CONSTRAINT: The 320 mm conduit and 390 mm EN31 axle are CONTINUOUS
solids — never split, clipped, or boolean-subtracted by cowl or fan geometry.

Exported builders
-----------------
  build_roller_end_plug()   -> Solid
  build_roller_conduit()    -> Solid  (reference solid – continuous)
  build_roller_axle()       -> Solid  (reference solid – continuous)
"""

from __future__ import annotations
import math
import build123d as bd
from build123d import (
    BuildPart, BuildSketch,
    Cylinder, Box, Cone,
    extrude, loft, fillet, chamfer,
    Location, Locations,
    Plane, Axis, Mode, Align,
    Circle, Rectangle, Polygon,
    Solid, Part, Vector,
)
from .parameters import (
    EPS,
    ROLLER_CONDUIT_OD, ROLLER_CONDUIT_ID, ROLLER_CONDUIT_LENGTH,
    AXLE_DIAMETER, AXLE_BORE_D, AXLE_TOTAL_LENGTH,
    PLUG_BODY_D, PLUG_BODY_LENGTH, PLUG_LEAD_CHAMFER,
    PLUG_FLANGE_D, PLUG_FLANGE_THICKNESS,
    NUT_AF_ACTUAL, NUT_AC_ACTUAL, NUT_DEPTH_ACTUAL,
    NUT_Z_ALONG_PLUG, NUT_WALL_MIN,
    SET_SCREW_D,
)


# ---------------------------------------------------------------------------
# Roller End Plug  (axis = Z, insertion tip at z = 0)
# ---------------------------------------------------------------------------

def build_roller_end_plug(d_bore: bool = False) -> bd.Solid:
    """
    Press-fit end plug for the 1.25" UPVC conduit roller core (v2.0).

    z = 0                    – insertion tip (lead-in chamfer base)
    z = PLUG_BODY_LENGTH     – inner face of retaining flange (20.0 mm)
    z = body_len + 3.0       – conduit stop lip (Ø40.0 mm)
    z = total_h              – outer face of external collar (27.5 mm, Ø24.0 mm)

    Features:
      - 7.5 mm thick external retaining collar (Ø24.0 mm with Ø40.0 mm base lip)
      - Radial M3 set-screw and captive hex nut pocket relocated to z = 23.75 mm
        inside the external collar (100% accessible after pressing into UPVC conduit).
      - If d_bore is True, bore has a 4.2 mm D-profile (flat at 3.6 mm) for direct coupling
        to 25GA-370 motor D-shaft.
    """
    plug_r   = PLUG_BODY_D / 2.0         # 18.0 mm
    lead_h   = PLUG_LEAD_CHAMFER         # 1.0  mm
    body_len = PLUG_BODY_LENGTH          # 20.0 mm
    flange_r = PLUG_FLANGE_D / 2.0       # 20.0 mm
    collar_r = 12.0                      # 12.0 mm (Ø24.0 mm OD collar)
    flange_t = PLUG_FLANGE_THICKNESS     # 7.5  mm
    lip_t    = 3.0                       # 3.0  mm conduit stop lip
    bore_r   = AXLE_BORE_D / 2.0         # 2.1  mm
    nut_z    = body_len + flange_t / 2.0 # 23.75 mm from tip (inside external collar)
    nut_x0   = bore_r + NUT_WALL_MIN     # 3.3  mm from axis

    total_h = body_len + flange_t        # 27.5 mm

    # ---- Outer stepped body via loft (lead-in chamfer) ----
    with BuildPart() as loft_bp:
        with BuildSketch(Plane.XY):
            Circle(plug_r - lead_h)
        with BuildSketch(Plane.XY.offset(lead_h)):
            Circle(plug_r)
        loft(ruled=True)

    result = loft_bp.part

    # ---- Plug body cylinder (from lead_h to body_len) ----
    with BuildPart() as body_bp:
        with BuildSketch(Plane.XY.offset(lead_h - EPS)):
            Circle(plug_r)
        extrude(amount=body_len - lead_h + EPS)
    result = result.fuse(body_bp.part)

    # ---- Retaining flange lip (Ø40.0 mm × 3.0 mm) seating against conduit face ----
    with BuildPart() as flange_bp:
        with BuildSketch(Plane.XY.offset(body_len)):
            Circle(flange_r)
        extrude(amount=lip_t)
    result = result.fuse(flange_bp.part)

    # ---- External set-screw collar (Ø24.0 mm extending to total_h = 27.5 mm) ----
    with BuildPart() as collar_bp:
        with BuildSketch(Plane.XY.offset(body_len)):
            Circle(collar_r)
        extrude(amount=flange_t)
    result = result.fuse(collar_bp.part)

    # ---- Central through bore (4.2 mm, optional D-profile) ----
    with BuildPart() as bore_bp:
        with BuildSketch(Plane.XY.offset(-EPS)):
            Circle(bore_r)
            if d_bore:
                flat_depth = 4.2 - 3.6  # 0.6 mm
                with Locations((0.0, bore_r - flat_depth / 2.0)):
                    Rectangle(bore_r * 2.5, flat_depth, mode=Mode.SUBTRACT)
        extrude(amount=total_h + 2.0 * EPS)
    result = result.cut(bore_bp.part)

    # ---- Captive M3 hex nut pocket (hexagonal prism along X, at nut_z in external collar) ----
    nut_r    = NUT_AC_ACTUAL / 2.0
    nut_dep  = NUT_DEPTH_ACTUAL

    with BuildPart() as nut_bp:
        with BuildSketch(Plane.YZ.offset(nut_x0)):
            with Locations((0.0, nut_z)):
                Polygon(6, nut_r, rotation=30)
        extrude(amount=nut_dep)
    result = result.cut(nut_bp.part)

    # ---- Side-entry slot (nut slid in from +Y, accessible on collar) ----
    slot_h   = NUT_AF_ACTUAL
    slot_len = collar_r + 2.0  # extends to outer collar surface

    with BuildPart() as slot_bp:
        Box(nut_dep, slot_len, slot_h,
            align=(Align.MIN, Align.MAX, Align.CENTER))
        slot_bp.part = slot_bp.part.move(Location(Vector(nut_x0, 0.0, nut_z)))
    result = result.cut(slot_bp.part)

    # ---- M3 set-screw radial bore (from +X collar surface into bore) ----
    screw_len = collar_r + 2.0

    with BuildPart() as screw_bp:
        with BuildSketch(Plane.YZ.offset(-EPS)):
            with Locations((0.0, nut_z)):
                Circle(SET_SCREW_D / 2.0)
        extrude(amount=screw_len + EPS)
    result = result.cut(screw_bp.part)

    return result


def build_roller_end_plug_25ga() -> bd.Solid:
    """Convenience builder for 25GA D-profile coupled right roller plug."""
    return build_roller_end_plug(d_bore=True)


# ---------------------------------------------------------------------------
# Roller conduit core reference solid  (CONTINUOUS – never clip)
# ---------------------------------------------------------------------------

def build_roller_conduit() -> bd.Solid:
    """
    1.25" UPVC electrical conduit core.
    OD = 41.2 mm, ID = 36.0 mm, length = 320 mm.
    Axis along Z; centred at (0, 0) in X-Y.
    """
    with BuildPart() as bp:
        Cylinder(ROLLER_CONDUIT_OD / 2.0, ROLLER_CONDUIT_LENGTH,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
        with BuildSketch(Plane.XY):
            Circle(ROLLER_CONDUIT_ID / 2.0)
        extrude(amount=ROLLER_CONDUIT_LENGTH, mode=Mode.SUBTRACT)
    return bp.part


# ---------------------------------------------------------------------------
# Central steel axle reference solid  (CONTINUOUS – never clip)
# ---------------------------------------------------------------------------

def build_roller_axle() -> bd.Solid:
    """
    EN31 silver steel rod, Ø 4 mm × 390 mm total span.
    Axis along Z, centred at (0, 0) in X-Y, centred along Z.
    """
    with BuildPart() as bp:
        Cylinder(AXLE_DIAMETER / 2.0, AXLE_TOTAL_LENGTH,
                 align=(Align.CENTER, Align.CENTER, Align.CENTER))
    return bp.part
