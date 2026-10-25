"""
PROJECT A.R.C. – Part E: Aerodynamic Blower Cowl
=================================================
Source: phase3.scad  ->  build123d B-Rep implementation.

Coordinate system (global ARC frame)
--------------------------------------
  Origin = roller contact line on panel glass.
  X = lateral (cowl centred at X = 0, spans to ±170 mm).
  Y = gantry travel (+Y = forward).
  Z = up from glass face.

Air-knife geometry
------------------
  Slit exits at Z = 20 mm aimed at −45° elevation.
  Jet lands on glass (Z = 0) at Y = +14 mm ahead of roller.

CRITICAL CONSTRAINTS:
  - Roller (Ø 50 mm, axis at Y=0, Z=25) must NOT be clipped by cowl.
  - Cowl body sits entirely at +Y of the roller.
  - Minimum wall = 2.4 mm everywhere.

Exported builders
-----------------
  build_blower_cowl_half(side: "left"|"right") -> Solid
  build_blower_cowl_left()                      -> Solid
  build_blower_cowl_right()                     -> Solid
"""

from __future__ import annotations
import math
import build123d as bd
from build123d import (
    BuildPart, BuildSketch, BuildLine,
    Plane, Axis, Mode, Align,
    extrude, loft, fillet, chamfer, revolve, mirror,
    Locations, Location,
    Box, Cylinder, Cone, Sphere,
    Circle, Rectangle, Polygon, Polyline, make_face,
    Solid, Part, Compound,
    Vector,
)
from .parameters import (
    EPS,
    COWL_HALF_SPAN, COWL_WALL, COWL_END_WALL,
    SLIT_WIDTH, SLIT_EXIT_Z, SLIT_LAND_LEN, JET_AIM_Y, S45,
    PLENUM_WIDTH, PLENUM_TAPER_LEN, PLENUM_TOP_Z, PLENUM_BOX_LEN,
    COLLAR_EXTRA_WALL, COLLAR_LEN,
    TONGUE_H, TONGUE_D0, TONGUE_D1,
    GROOVE_D0, GROOVE_D1, GROOVE_DEPTH,
    DOWEL_BORE_D, DOWEL_DEPTH,
    DUCT_CENTRE_Y, DUCT_ID, DUCT_WALL, DUCT_HEIGHT,
    FLANGE_D, FLANGE_THICKNESS, FLANGE_BOLT_CIRCLE, FLANGE_HOLE_D, FLANGE_BOLT_ANGLES,
    TAB_THICKNESS, TAB_HOLE_D, TAB_HOLE_POSITIONS,
    ROLLER_FINISHED_R,
)


# ---------------------------------------------------------------------------
# Jet-frame mapping helpers  (mirror of OpenSCAD lp() / eV())
# ---------------------------------------------------------------------------

def _lp(u: float, v: float):
    """Map jet-local (u=upstream, v=across-slit) → global (Y, Z)."""
    y = JET_AIM_Y + SLIT_EXIT_Z + S45 * (u + v)
    z = SLIT_EXIT_Z + S45 * (u - v)
    return (y, z)


def _eV(u: float) -> float:
    """Half-width of the flow path at upstream distance u."""
    sw = SLIT_WIDTH / 2.0
    pw = PLENUM_WIDTH / 2.0
    land = SLIT_LAND_LEN
    taper = PLENUM_TAPER_LEN
    if u <= land:
        return sw
    elif u <= land + taper:
        return sw + (u - land) / taper * (pw - sw)
    return pw


def _dowel_positions():
    """Return [(Y, Z)] for the two dowel boss centres."""
    bossA = _lp(14.0, -(_eV(14.0) + 9.0))
    bossB = _lp(22.0,  (_eV(22.0) + 9.0))
    return [bossA, bossB]


# ---------------------------------------------------------------------------
# 2-D air-cavity cross-section profile (Y-Z plane)
# ---------------------------------------------------------------------------

def _cavity_profile_pts(wall_offset: float = 0.0, n: int = 24):
    """
    Return list of (Y, Z) points describing the air-cavity perimeter
    (slit + taper + plenum box) optionally grown outward by wall_offset mm.
    """
    land  = SLIT_LAND_LEN      # 10 mm
    taper = PLENUM_TAPER_LEN   # 18 mm
    box   = PLENUM_BOX_LEN     # 70 mm
    u_max = land + taper + box

    top_pts = []
    bot_pts = []
    for i in range(n + 1):
        u = u_max * i / n
        half_w = _eV(u) + wall_offset
        top_pts.append(_lp(u, -half_w))
        bot_pts.append(_lp(u,  half_w))

    return top_pts + list(reversed(bot_pts))


def _make_profile_solid(x0: float, span: float, wall_offset: float = 0.0) -> bd.Solid:
    """Extrude the 2-D air profile along X and clip Z at PLENUM_TOP_Z."""
    pts = _cavity_profile_pts(wall_offset)
    with BuildPart() as bp:
        with BuildSketch(Plane.YZ.offset(x0)):
            with BuildLine():
                Polyline(*[(y, z) for (y, z) in pts], close=True)
            make_face()
        extrude(amount=span)
        
    # Clip top at PLENUM_TOP_Z outside the context so it doesn't auto-add
    height = 500.0 + PLENUM_TOP_Z + wall_offset
    with BuildPart() as clip_bp:
        clip_box = Box(500, 500, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        clip_bp.part = clip_bp.part.move(Location(Vector(0.0, 0.0, -500.0)))
        
    res = bp.part.intersect(clip_bp.part)
    return res[0] if isinstance(res, list) and res else res


# ---------------------------------------------------------------------------
# Sub-component builders
# ---------------------------------------------------------------------------

def _make_duct_solid_half(x_sign: float) -> bd.Solid:
    """
    5015 blower intake neck + mounting flange on one side (x >= 0 or x <= 0).
    x_sign = +1 for right half, -1 for left half.
    """
    outer_r = (DUCT_ID + 2.0 * DUCT_WALL) / 2.0
    neck_h  = DUCT_HEIGHT
    top_z   = PLENUM_TOP_Z

    with BuildPart() as bp:
        # Neck
        with BuildSketch(Plane.XY.offset(top_z)):
            with Locations((0.0, DUCT_CENTRE_Y)):
                Circle(outer_r)
        extrude(amount=neck_h)
        # Flange disk
        with BuildSketch(Plane.XY.offset(top_z + neck_h - FLANGE_THICKNESS)):
            with Locations((0.0, DUCT_CENTRE_Y)):
                Circle(FLANGE_D / 2.0)
        extrude(amount=FLANGE_THICKNESS, mode=Mode.ADD)

    # Clip to the correct half (x >= 0 or x <= 0)
    clip_size = 500.0
    with BuildPart() as clip_bp:
        if x_sign > 0:
            Box(clip_size, clip_size * 2, clip_size * 2,
                align=(Align.MIN, Align.CENTER, Align.MIN))
        else:
            Box(clip_size, clip_size * 2, clip_size * 2,
                align=(Align.MAX, Align.CENTER, Align.MIN))
    res = bp.part.intersect(clip_bp.part)
    return res[0] if isinstance(res, list) and res else res


def _make_duct_bore() -> bd.Solid:
    """Vertical bore through cowl roof into plenum."""
    with BuildPart() as bp:
        with BuildSketch(Plane.XY.offset(PLENUM_TOP_Z - 2.0)):
            with Locations((0.0, DUCT_CENTRE_Y)):
                Circle(DUCT_ID / 2.0)
        extrude(amount=DUCT_HEIGHT + 14.0)
    return bp.part


def _make_tab_ears_solid(x0: float, x1: float) -> bd.Solid:
    """Endplate mounting tab strip at the outer end of each half."""
    ear_r = 5.0
    anchor = (60.0, 33.0)

    with BuildPart() as bp:
        with BuildSketch(Plane.YZ.offset(x0)):
            for (y, z) in TAB_HOLE_POSITIONS:
                with Locations((y, z)):
                    Circle(ear_r)
            with Locations(anchor):
                Circle(4.0)
            bd.make_hull()
        extrude(amount=x1 - x0)
    result = bp.part

    # Subtract M3 screw holes
    for (y, z) in TAB_HOLE_POSITIONS:
        with BuildPart() as hole_bp:
            with BuildSketch(Plane.YZ.offset(x0 - EPS)):
                with Locations((y, z)):
                    Circle(TAB_HOLE_D / 2.0)
            extrude(amount=(x1 - x0) + 2.0 * EPS)
        result = result.cut(hole_bp.part)
    return result


def _make_dowel_boss(cy: float, cz: float, x_len: float) -> bd.Solid:
    """Cylindrical boss + chamfer run-out for one dowel-pin blind bore."""
    boss_r   = 4.5
    boss_cham = 11.0

    with BuildPart() as bp:
        # Main cylinder
        with BuildSketch(Plane.YZ.offset(0.0)):
            with Locations((cy, cz)):
                Circle(boss_r)
        extrude(amount=x_len)
        # Chamfer cone run-out
        with BuildSketch(Plane.YZ.offset(x_len)):
            with Locations((cy, cz)):
                Circle(boss_r)
        with BuildSketch(Plane.YZ.offset(x_len + boss_cham)):
            with Locations((cy, cz)):
                Circle(0.5)
        loft(ruled=True)
    return bp.part


# ---------------------------------------------------------------------------
# Right-half core (x >= 0)
# ---------------------------------------------------------------------------

def _build_right_half_core() -> bd.Solid:
    half = COWL_HALF_SPAN       # 170 mm
    wall = COWL_WALL            # 2.4 mm
    end_wall = COWL_END_WALL    # 4.0 mm

    # ---- 1. Main shell (filled outer profile) ----
    shell = _make_profile_solid(0.0, half, wall)

    # ---- 2. Collar reinforcement steps at joint face ----
    n_steps = 8
    collar_solids = []
    for i in range(1, n_steps + 1):
        run = COLLAR_LEN - (i - 1) * COLLAR_LEN / n_steps
        extra = COLLAR_EXTRA_WALL * i / n_steps
        if run > 0:
            collar_solids.append(_make_profile_solid(0.0, run, wall + extra))

    for s in collar_solids:
        shell = shell.fuse(s)

    # ---- 3. Dowel bosses ----
    boss_len = DOWEL_DEPTH + 3.0
    for (cy, cz) in _dowel_positions():
        boss = _make_dowel_boss(cy, cz, boss_len)
        shell = shell.fuse(boss)

    # ---- 4. Endplate mounting tab ----
    tab = _make_tab_ears_solid(half - TAB_THICKNESS, half)
    shell = shell.fuse(tab)

    # ---- 5. Blower duct solid ----
    duct = _make_duct_solid_half(+1.0)
    shell = shell.fuse(duct)

    # ---- 6. Subtract air cavity (plenum + slit) – leave end_wall closed ----
    cav = _make_profile_solid(-EPS, half - end_wall, 0.0)
    shell = shell.cut(cav)

    # ---- 7. Subtract duct bore ----
    shell = shell.cut(_make_duct_bore())

    # ---- 8. Subtract dowel-pin blind bores ----
    for (cy, cz) in _dowel_positions():
        with BuildPart() as dbp:
            with BuildSketch(Plane.YZ.offset(-EPS)):
                with Locations((cy, cz)):
                    Circle(DOWEL_BORE_D / 2.0)
            extrude(amount=DOWEL_DEPTH + EPS)
        shell = shell.cut(dbp.part)

    # ---- 9. Subtract blower flange screw holes ----
    top_z = PLENUM_TOP_Z + DUCT_HEIGHT - FLANGE_THICKNESS
    for angle_deg in FLANGE_BOLT_ANGLES:
        rad = math.radians(angle_deg)
        hx  = FLANGE_BOLT_CIRCLE / 2.0 * math.cos(rad)
        hy  = DUCT_CENTRE_Y + FLANGE_BOLT_CIRCLE / 2.0 * math.sin(rad)
        if hx >= -EPS:    # right half only
            with BuildPart() as fbp:
                with BuildSketch(Plane.XY.offset(top_z - EPS)):
                    with Locations((hx, hy)):
                        Circle(FLANGE_HOLE_D / 2.0)
                extrude(amount=FLANGE_THICKNESS + 2.0 * EPS)
            shell = shell.cut(fbp.part)

    # ---- 10. Subtract groove (right half carries the groove) ----
    groove_outer = _make_profile_solid(-EPS, GROOVE_DEPTH + EPS, GROOVE_D1)
    groove_inner = _make_profile_solid(-EPS, GROOVE_DEPTH + 2.0 * EPS, GROOVE_D0)
    groove_band  = groove_outer.cut(groove_inner)
    shell = shell.cut(groove_band)

    return shell


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

def build_blower_cowl_half(side: str = "right") -> bd.Solid:
    """
    Build one printable half of the 340 mm blower cowl.

    side = "right"  →  x in [0, +170], carries the mating GROOVE.
    side = "left"   →  x in [-170, 0], mirrored from right, carries TONGUE.
    """
    if side not in ("left", "right"):
        raise ValueError("side must be 'left' or 'right'")

    right_core = _build_right_half_core()

    if side == "right":
        return right_core

    # ---- Left half: mirror the right core across X = 0 ----
    left_core = mirror(right_core, about=Plane.YZ)

    # Remove the groove band that was cut into the right half (it was subtracted);
    # instead add the tongue extrusion on the left half at x = 0 face (now x_local = 0 after mirror)
    # Build tongue as extrusion from x=0 toward +X (i.e. toward the right half)
    # In the mirrored frame, x = 0 is still the joint face.
    tongue_outer = _make_profile_solid(0.0, TONGUE_H, TONGUE_D1)
    tongue_inner = _make_profile_solid(0.0, TONGUE_H + EPS, TONGUE_D0)

    tongue_ring = tongue_outer.cut(tongue_inner)
    left_core = left_core.fuse(tongue_ring)

    # Re-subtract duct bore on left half (it was mirrored but bore is centred at x=0)
    left_core = left_core.cut(_make_duct_bore())

    return left_core


def build_blower_cowl_left() -> bd.Solid:
    """Convenience alias – returns the left cowl half."""
    return build_blower_cowl_half("left")


def build_blower_cowl_right() -> bd.Solid:
    """Convenience alias – returns the right cowl half."""
    return build_blower_cowl_half("right")
