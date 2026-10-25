"""
PROJECT A.R.C. – Solar Telemetry Tilt Wedge & Corner Clamp Clips
=================================================================
Source: phase3.scad  ->  build123d B-Rep implementation.

Geometry
--------
  Base flat on XY plane (Z = 0 = base underside).
  Tilt = 25 deg elevation facing +Y.
  PV cell pocket recessed 2.8 mm into the tilted slope face.
  Continuous 8 mm wiring tunnel through the wedge body.

Exported builders
-----------------
  build_solar_tilt_wedge()   -> Solid
  build_pv_clamp_clip()      -> Solid  (one clip; use 4 in assembly)
"""

from __future__ import annotations
import math
import build123d as bd
from build123d import (
    BuildPart, BuildSketch, BuildLine,
    Plane, Axis, Mode, Align,
    extrude, loft, fillet,
    Locations, Location,
    Box, Cylinder, Cone,
    Circle, Rectangle, Polygon, Polyline, make_face,
    Solid, Part, Vector,
)
from .parameters import (
    EPS,
    WEDGE_TILT, WEDGE_H_LOW, WEDGE_BODY_MARGIN,
    WEDGE_SLOPE_RUN, WEDGE_SLOPE_RISE,
    WEDGE_BODY_L, WEDGE_BASE_L, WEDGE_BASE_W, WEDGE_BASE_T, WEDGE_BASE_EXT,
    PV_POCKET_L, PV_POCKET_W, PV_POCKET_DEPTH, PV_LIP_T, PV_LIP_H,
    WEDGE_CABLE_D, BASE_HOLE_D,
    WEDGE_PAD_S, WEDGE_PAD_W, WEDGE_PAD_A, WEDGE_PAD_BS,
    CLIP_T, CLIP_OVERLAP, CLIP_HOLE_D,
)

_TILT_RAD = math.radians(WEDGE_TILT)


# ---------------------------------------------------------------------------
# Helper: slope-frame plane
# ---------------------------------------------------------------------------

def _slope_plane() -> Plane:
    """
    Plane on the PV-facing slope surface.
    Origin at the low front edge of the slope.
    Z-normal tilts at WEDGE_TILT degrees from horizontal.
    """
    origin = Vector(0.0, -WEDGE_SLOPE_RUN / 2.0, WEDGE_H_LOW)
    x_dir  = Vector(1.0, 0.0, 0.0)
    z_dir  = Vector(0.0, -math.sin(_TILT_RAD), math.cos(_TILT_RAD))
    return Plane(origin=origin, x_dir=x_dir, z_dir=z_dir)


# ---------------------------------------------------------------------------
# Wedge body (trapezoidal prism)
# ---------------------------------------------------------------------------

def _build_wedge_body() -> bd.Solid:
    """
    Trapezoidal cross-section in the Y-Z plane, extruded along X.
    Y-Z profile: [(0,0), (run,0), (run, h_low+rise), (0, h_low)]
    """
    run   = WEDGE_SLOPE_RUN
    h_low = WEDGE_H_LOW
    rise  = WEDGE_SLOPE_RISE
    wl    = WEDGE_BODY_L

    profile = [
        (0.0,        0.0),
        (run,        0.0),
        (run,        h_low + rise),
        (0.0,        h_low),
    ]

    with BuildPart() as bp:
        with BuildSketch(Plane.YZ.offset(-wl / 2.0)):
            with BuildLine():
                Polyline(*[(y, z) for (y, z) in profile], close=True)
            make_face()
        extrude(amount=wl)
    return bp.part


# ---------------------------------------------------------------------------
# PV lip ring and corner pad bosses (built in slope frame)
# ---------------------------------------------------------------------------

def _build_pv_lip_and_pads(slope_plane: Plane) -> bd.Solid:
    """Retaining lip ring + four screw-tab pads in slope-local coordinates."""
    bm    = WEDGE_BODY_MARGIN
    lip_t = PV_LIP_T
    lip_h = PV_LIP_H
    pk_l  = PV_POCKET_L
    pk_w  = PV_POCKET_W
    pad_s = WEDGE_PAD_S
    pad_w = WEDGE_PAD_W
    pad_a = WEDGE_PAD_A

    outer_l = pk_l + 2.0 * lip_t
    outer_w = pk_w + 2.0 * lip_t
    cy      = bm + lip_t + pk_w / 2.0   # pocket centre Y in slope frame

    # Lip ring = outer box minus inner box
    with BuildPart() as outer_bp:
        with BuildSketch(slope_plane):
            with Locations((0.0, cy)):
                Rectangle(outer_l, outer_w)
        extrude(amount=lip_h + EPS)
    with BuildPart() as inner_bp:
        with BuildSketch(slope_plane):
            with Locations((0.0, cy)):
                Rectangle(pk_l, pk_w)
        extrude(amount=lip_h + 2.0 * EPS)

    lip_ring = outer_bp.part.cut(inner_bp.part)

    # Corner pads
    pad_solids = []
    for sx in (+1.0, -1.0):
        for pb in WEDGE_PAD_BS:
            with BuildPart() as pad_bp:
                with BuildSketch(slope_plane):
                    with Locations((sx * pad_a, pb)):
                        Rectangle(pad_s + EPS, pad_w)
                extrude(amount=(lip_h + EPS) / 2.0)
            pad_solids.append(pad_bp.part)

    result = lip_ring
    for p in pad_solids:
        result = result.fuse(p)
    return result


# ---------------------------------------------------------------------------
# Main builder: Solar Tilt Wedge
# ---------------------------------------------------------------------------

def build_solar_tilt_wedge() -> bd.Solid:
    """
    25-degree tilted PV mounting wedge with:
    - Flat base mounting plate (WEDGE_BASE_L × WEDGE_BASE_W × 3 mm)
    - Trapezoidal wedge body
    - PV cell retaining lip pocket (70.8 × 70.8 × 2.8 mm)
    - 8 mm wiring cable tunnel (vertical)
    - Corner screw pad M3 self-tap pilots
    - 4 × M3 base corner clearance holes
    """
    run   = WEDGE_SLOPE_RUN
    rise  = WEDGE_SLOPE_RISE
    h_low = WEDGE_H_LOW

    # ---- 1. Base mounting plate ----
    with BuildPart() as base_bp:
        Box(WEDGE_BASE_L, WEDGE_BASE_W, WEDGE_BASE_T,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
    result = base_bp.part

    # ---- 2. Wedge body (centred on X, Y runs from -run/2 to +run/2) ----
    wedge = _build_wedge_body()
    # Profile was built at Y=0..run, centre at Y=run/2; shift to -run/2..+run/2
    wedge = wedge.move(Location(Vector(0.0, -run / 2.0, 0.0)))
    result = result.fuse(wedge)

    # ---- 3. PV lip and corner pads ----
    slope_plane = _slope_plane()
    pv_lip = _build_pv_lip_and_pads(slope_plane)
    result = result.fuse(pv_lip)

    # ---- 4. Cable bore (Ø 8 mm, vertical, through wedge body) ----
    max_h = h_low + rise + PV_LIP_H + 6.0
    with BuildPart() as cable_bp:
        with BuildSketch(Plane.XY.offset(-EPS)):
            Circle(WEDGE_CABLE_D / 2.0)
        extrude(amount=max_h + EPS)
    result = result.cut(cable_bp.part)

    # ---- 5. Base corner M3 clearance holes ----
    for sx in (+1.0, -1.0):
        for sy in (+1.0, -1.0):
            hx = sx * (WEDGE_BASE_L / 2.0 - 5.0)
            hy = sy * (WEDGE_BASE_W / 2.0 - 5.0)
            with BuildPart() as corner_bp:
                with BuildSketch(Plane.XY.offset(-EPS)):
                    with Locations((hx, hy)):
                        Circle(BASE_HOLE_D / 2.0)
                extrude(amount=WEDGE_BASE_T + 2.0 * EPS)
            result = result.cut(corner_bp.part)

    # ---- 6. Corner-pad M3 pilot bores (in slope frame, depth = 12 mm) ----
    pilot_d     = 2.5
    pilot_depth = 12.0
    for sx in (+1.0, -1.0):
        for pb in WEDGE_PAD_BS:
            with BuildPart() as pilot_bp:
                with BuildSketch(slope_plane):
                    with Locations((sx * WEDGE_PAD_A, pb)):
                        Circle(pilot_d / 2.0)
                extrude(amount=-pilot_depth)   # into the wedge body
            result = result.cut(pilot_bp.part)

    return result


# ---------------------------------------------------------------------------
# PV corner clamp clip
# ---------------------------------------------------------------------------

def build_pv_clamp_clip() -> bd.Solid:
    """
    Flat corner clamp clip (qty 4).
    Clip_len = pad_s/2 + lip_t + overlap + pad_w/2.
    Features a Ø 3.4 mm M3 clearance through-hole.
    """
    pad_w    = WEDGE_PAD_W         # 10.0 mm
    overlap  = CLIP_OVERLAP        # 5.0 mm
    lip_t    = PV_LIP_T            # 2.4 mm
    pad_s    = WEDGE_PAD_S         # 10.0 mm
    clip_len = pad_s / 2.0 + lip_t + overlap + pad_w / 2.0

    with BuildPart() as bp:
        # Round end near screw hole
        with BuildSketch(Plane.XY):
            with Locations((pad_w / 2.0, 0.0)):
                Circle(pad_w / 2.0)
        extrude(amount=CLIP_T)

        # Flat rectangular extension
        with BuildSketch(Plane.XY):
            Rectangle(clip_len, pad_w, align=(Align.MIN, Align.CENTER))
        extrude(amount=CLIP_T, mode=Mode.ADD)

        # M3 through-hole
        with BuildSketch(Plane.XY.offset(-EPS)):
            with Locations((pad_w / 2.0, 0.0)):
                Circle(CLIP_HOLE_D / 2.0)
        extrude(amount=CLIP_T + 2.0 * EPS, mode=Mode.SUBTRACT)

    return bp.part
