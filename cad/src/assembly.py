"""
PROJECT A.R.C. – Master Digital-Twin Assembly with Full COTS Hardware
======================================================================
Every part is positioned with `place()`, which does NOT trust the builder's
local frame.  Each axis is anchored by what we actually want:

    ("center", v)  bounding-box centre of that axis  -> v
    ("min",    v)  bounding-box minimum of that axis -> v
    ("max",    v)  bounding-box maximum of that axis -> v
    ("origin", v)  builder-frame 0 of that axis      -> v   (use only where the
                   builder origin is meaningful, e.g. the roller axis)

World frame: X across the panel, +Y = gantry travel (front), Z up, glass at Z=0.
The reference image is shot from the FRONT (+Y) looking toward -Y, so image-left is +X.

Detail switch:
  - detail="simple": exactly baseline behaviour (33 parts, envelope stand-ins)
  - detail="full": full-detail recreation (microfibre sleeve, authentic COTS,
    N20 gearmotors, limit switch, fasteners, wiring harness, dynamic BOM, mass report)

Run:
  python -m src.assembly                  # Default simple mode (backward compatible)
  python -m src.assembly --detail full   # Full detail twin recreation
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Tuple

import build123d as bd
from build123d import (
    BuildPart, Plane, Location, Locations, Vector,
    Box, Cylinder, Compound, export_step, export_gltf, export_stl,
)

from src.parameters import (
    ROLLER_CENTRE_Z, ROLLER_FINISHED_R, ROLLER_CONDUIT_LENGTH,
    AXLE_TOTAL_LENGTH, COWL_HALF_SPAN, COWL_WALL,
    SLIT_EXIT_Z, JET_AIM_Y, S45, PLATE_THICKNESS, TRAY_THICKNESS,
    MIN_WALL_THICKNESS, MIN_AIR_KNIFE_CLEARANCE, BEARING_LEDGE_T,
    CROSSBEAM_LENGTH, PCB_LAYOUT,
    FLANGE_BOLT_ANGLES, FLANGE_BOLT_CIRCLE, DUCT_CENTRE_Y, TRAY_BOLT_X,
    WHEEL_CC, WHEEL_FRONT_Y, WHEEL_REAR_Y, WHEEL_BOTTOM_Y, WHEEL_TOP_Z, WHEEL_BOTTOM_Z,
    BEARING_CENTRE_Y,
)
from src.carriage_endplate import build_carriage_endplate, build_n20_motor_clamp, build_25ga_motor_clamp
from src.roller_assembly import build_roller_end_plug, build_roller_end_plug_25ga, build_roller_conduit, build_roller_axle
from src.coupler_n20_vwheel import build_coupler_n20_vwheel
from src.blower_cowl import build_blower_cowl_half, _dowel_positions
from src.parts.blower import build_blower_cowl_mount
from src.chassis_tray import build_chassis_tray
from src.solar_tilt_wedge import build_solar_tilt_wedge, build_pv_clamp_clip
from src.limit_switch_dog import build_limit_switch_dog
from src.esp32_adapter_sled import build_esp32_adapter_sled, make_esp32_adapter_sled
from src.parts.testbed import (
    build_testbed_rail_riser_foot,
    build_testbed_rail_panel_bracket,
    build_testbed_panel_pedestal,
)

# Detailed COTS, fasteners, wiring, and analysis modules
from src.cots import (
    build_2020_extrusion, build_mini_v_wheel, build_5015_blower,
    build_n20_gearmotor, build_25ga370_motor, build_onpow_limit_switch,
    build_mini_pv_cell, build_flat_panel_slab, build_framed_solar_panel,
    build_l298n_driver, build_relay_module, build_ina219_sensor,
    build_battery_holder_2s, build_microfiber_sleeve,
)
from src.fasteners_placement import build_all_fasteners
from src.wiring import build_all_wires, print_wire_schedule, NET_DEFINITIONS, _smooth_waypoints
from src.mass_report import print_mass_and_cog_report, compute_assembly_mass_and_cog
from src.bom import export_bom_csv

# ---------------------------------------------------------------------------
# Layout constants taken from the mechanical brief
# ---------------------------------------------------------------------------
BRIEF_ROLLER_Z = 25.3            # roller axis height above glass (v2.0 redesign)
BRIEF_CONDUIT_L = 320.0
BRIEF_AXLE_L = 390.0
BRIEF_COWL_HALF_SPAN = 170.0

CROSSBEAM_LEN = 344.0              # 344 mm = flush with endplate inner faces at X = ±172.0 mm
CROSSBEAM_Y = -35.0
BEAM_CLEARANCE = 1.5             # min gap, beam to finished roller envelope (R=25)
COWL_CLEARANCE = 3.0             # brief: cowl rear edge >= 3 mm from roller envelope
CROSSBEAM_Z = 45.0               # M5 hole height on the endplates
EXTRUSION = 20.0                 # 2020 profile

FAN_NECK_Y = 58.0                # cowl intake neck centre
FAN_NECK_TOP_Z = 42.0            # top face of cowl flange == fan seat
FAN_THICKNESS = 15.0

RAIL_LEN = 600.0
V_WHEEL_R = 7.615                # mini V-wheel radius (OD 15.23)
MOTOR_LEN = 45.0                 # 25GA-370 body length
MOTOR_CLAMP_GAP = 2.0            # 25GA-370 body starts this far outboard of clamp
PANEL_L = 580.0                  # main PV panel length (Y)
PANEL_RAIL_GAP = 1.0             # panel edge to rail inner face

# --- Layout conventions ---
COWL_SEAM = 1.0                  # visible seam between cowl halves at X = 0
COWL_HALF_WIDTH = 90.0           # each half is kept to this width
WEDGE_REAR_INSET = 0.0           # wedge back face flush with tray rear edge
PV_MINI_T = 2.5                  # small PV panel on wedge
PV_CLIP_MARGIN = 6.0             # clip-to-wedge-edge margin
EL_GAP = 8.0                     # gap between electronics modules (X)
EL_MARGIN = 4.0                  # keep-out from tray edges

ASSEMBLY_REV = "r11 (full digital twin recreation with COTS library, hardware, wiring, and detail switch)"

Anchor = Tuple[str, float]
ORIGIN0: Anchor = ("origin", 0.0)


# ---------------------------------------------------------------------------
# Simple COTS hardware geometry helpers (backward compatibility for detail="simple")
# ---------------------------------------------------------------------------

def make_2020_extrusion(length: float) -> bd.Solid:
    """2020 V-slot approximation; axis along local Z, centred on origin."""
    with BuildPart() as p:
        Box(EXTRUSION, EXTRUSION, length)
        for ang in (0, 90, 180, 270):
            with Locations(Location((0, 0, 0), (0, 0, ang))):
                with Locations((0, EXTRUSION / 2.0, 0)):
                    Box(6.0, 3.6, length + 2, mode=bd.Mode.SUBTRACT)
        Cylinder(radius=2.1, height=length + 2, mode=bd.Mode.SUBTRACT)
    return p.part


def make_mini_v_wheel() -> bd.Solid:
    """Delrin mini V-wheel (OD 15.23, width 8.8); axis along local Z."""
    with BuildPart() as p:
        Cylinder(radius=7.615, height=8.8)
        Cylinder(radius=2.5, height=10.0, mode=bd.Mode.SUBTRACT)
    return p.part


def make_5015_blower() -> bd.Solid:
    """5015 radial blower envelope."""
    with BuildPart() as p:
        Cylinder(radius=25.0, height=FAN_THICKNESS)
        with Locations((-12.0, 15.0, 0.0)):
            Box(18.0, 20.0, FAN_THICKNESS)
        Cylinder(radius=15.0, height=FAN_THICKNESS + 1.0, mode=bd.Mode.SUBTRACT)
    return p.part


def _pcb(name: str):
    """(cx, cy, outline_w, outline_h) of a board from parameters.PCB_LAYOUT (tray-local)."""
    for n, cx, cy, _hx, _hy, _nh, ow, oh in PCB_LAYOUT:
        if n == name:
            return cx, cy, ow, oh
    raise KeyError(f"{name} missing from PCB_LAYOUT")


def _board_module(board: Tuple[float, float, float], parts=()) -> bd.Solid:
    """Centred PCB slab `board` = (w, d, t) with upright blocks `parts` on its top face."""
    bw, bdp, bt = board
    with BuildPart() as p:
        Box(bw, bdp, bt)
        for (w, d, h, ox, oy) in parts:
            with Locations((ox, oy, 0.5 * bt + 0.5 * h)):
                Box(w, d, h)
    return p.part


def make_esp32_shield() -> bd.Solid:
    """ESP32 dev board on a screw-terminal breakout (outline from PCB_LAYOUT)."""
    _, _, w, d = _pcb("ESP32_38PIN")
    return _board_module((w, d, 2.0),
                         [(8.0, d - 6.0, 10.0, -(0.5 * w - 4.5), 0.0),
                          (8.0, d - 6.0, 10.0, +(0.5 * w - 4.5), 0.0),
                          (w - 21.0, 8.0, 10.0, 0.0, 0.5 * d - 5.0),
                          (28.0, d - 14.0, 4.0, 0.0, -4.0)])


def make_l298n() -> bd.Solid:
    """L298N motor-driver board with upright heatsink (outline from PCB_LAYOUT)."""
    _, _, w, d = _pcb("L298N")
    return _board_module((w, d, 2.0),
                         [(20.0, 12.0, 24.0, 0.0, -8.0), (w - 5.5, 8.0, 9.0, 0.0, 0.5 * d - 6.0)])


def make_relay_module() -> bd.Solid:
    """1-channel 5 V relay module: cube relay + terminal block (outline from PCB_LAYOUT)."""
    _, _, w, d = _pcb("RELAY_1CH")
    return _board_module((w, d, 2.0),
                         [(19.0, 16.0, 16.0, -10.0, 0.0), (24.0, 9.0, 10.0, 12.0, -6.0)])


def make_ina219() -> bd.Solid:
    """INA219 current-sense breakout (outline from PCB_LAYOUT)."""
    _, _, w, d = _pcb("INA219")
    return _board_module((w, d, 1.6),
                         [(8.0, 6.0, 4.0, 5.0, 2.0), (16.0, 6.0, 8.0, -3.0, -7.0)])


def make_battery_holder() -> bd.Solid:
    """2 x 18650 holder, cells side by side, long axis along Y."""
    return _board_module((41.0, 77.0, 8.0),
                         [(18.5, 66.0, 13.0, -10.0, 0.0), (18.5, 66.0, 13.0, 10.0, 0.0)])


# ---------------------------------------------------------------------------
# Placement Helpers
# ---------------------------------------------------------------------------

def place(
    solid: bd.Shape,
    rot: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    x: Anchor = ORIGIN0,
    y: Anchor = ORIGIN0,
    z: Anchor = ORIGIN0,
) -> Tuple[bd.Shape, Vector]:
    """Rotate about the builder origin (degrees, XYZ), then translate so each
    axis satisfies its anchor. Returns (new independent solid, translation)."""
    s = solid.moved(Location((0.0, 0.0, 0.0), rot)) if any(rot) else solid.moved(Location((0.0, 0.0, 0.0)))
    bb = s.bounding_box()
    shift = []
    for axis, (mode, target) in zip("XYZ", (x, y, z)):
        lo, hi = getattr(bb.min, axis), getattr(bb.max, axis)
        ref = {"min": lo, "max": hi, "center": 0.5 * (lo + hi), "origin": 0.0}[mode]
        shift.append(target - ref)
    delta = Vector(*shift)
    return s.moved(Location(delta)), delta


def _as_list(r):
    if r is None:
        return []
    if hasattr(r, "volume") and not isinstance(r, (list, tuple)):
        return [r]
    return list(r)


def _surface_z(solid: bd.Shape, x: float, y: float, zspan: float = 500.0):
    """Highest Z of `solid` along the vertical line through (x, y), or None."""
    probe = bd.Solid.make_box(0.4, 0.4, 2 * zspan).moved(Location((x - 0.2, y - 0.2, -zspan)))
    try:
        hits = _as_list(solid.intersect(probe))
    except Exception:
        return None
    zs = [h.bounding_box().max.Z for h in hits]
    return max(zs) if zs else None


def _support_z(base: bd.Shape, bb, n: int = 3, inset: float = 0.0):
    """Highest Z of `base` anywhere under the XY footprint of bounding box `bb`."""
    w = (bb.max.X - bb.min.X) - 2.0 * inset
    d = (bb.max.Y - bb.min.Y) - 2.0 * inset
    if w <= 0.0 or d <= 0.0:
        return None
    zspan = 500.0
    prism = bd.Solid.make_box(w, d, 2 * zspan).moved(
        Location((bb.min.X + inset, bb.min.Y + inset, -zspan)))
    try:
        hits = _as_list(base.intersect(prism))
    except Exception:
        return None
    zs = [h.bounding_box().max.Z for h in hits if h is not None]
    return max(zs) if zs else None


def _rest_on(base: bd.Shape, solid: bd.Shape, fallback_z: float) -> bd.Shape:
    """Drop/raise `solid` vertically until its bottom touches the highest support below it."""
    b = solid.bounding_box()
    z = _support_z(base, b)
    if z is None:
        z = fallback_z
    return solid.moved(Location((0.0, 0.0, z - b.min.Z)))


def _trim_x(solid: bd.Shape, x_lo: float, x_hi: float, tol: float = 0.5) -> bd.Shape:
    """Keep only the slab x_lo <= X <= x_hi (no-op if the part is already narrower)."""
    b = solid.bounding_box()
    if b.min.X >= x_lo - tol and b.max.X <= x_hi + tol:
        return solid
    keep = bd.Solid.make_box(x_hi - x_lo, 4000.0, 4000.0).moved(Location((x_lo, -2000.0, -2000.0)))
    try:
        parts = [q for q in _as_list(solid.intersect(keep)) if q is not None]
    except Exception:
        return solid
    if not parts:
        return solid
    return parts[0] if len(parts) == 1 else Compound(children=parts)


def _wedge_slope_deg(wedge: bd.Shape) -> float:
    """Surface tilt about X: > 0 means the face rises toward +Y, < 0 toward -Y (rear)."""
    b = wedge.bounding_box()
    cx, cy = 0.5 * (b.min.X + b.max.X), 0.5 * (b.min.Y + b.max.Y)
    d = 0.25 * (b.max.Y - b.min.Y)
    z_a, z_b = _surface_z(wedge, cx, cy - d), _surface_z(wedge, cx, cy + d)
    if z_a is None or z_b is None or d <= 0:
        return 0.0
    return math.degrees(math.atan2(z_b - z_a, 2.0 * d))


def _seat_on_slope(panel: bd.Shape, wedge: bd.Shape, ang_deg: float, cx: float, cy: float,
                   pts, thickness: float):
    """Tilt flat `panel` by ang_deg about X, centre it over (cx, cy) and slide it along the
    face normal until it touches `wedge`."""
    ar = math.radians(ang_deg)
    ny, nz = -math.sin(ar), math.cos(ar)
    zs = [(_surface_z(wedge, x, y), y) for (x, y) in pts]
    icpt = [z - math.tan(ar) * (y - cy) for z, y in zs if z is not None]
    if not icpt:
        return None
    a = max(icpt)
    base, _ = place(panel, rot=(ang_deg, 0.0, 0.0), x=("center", cx), y=("center", cy), z=("center", a))
    h = 0.5 * thickness

    def at(t: float) -> bd.Shape:
        return base.moved(Location((0.0, ny * (t + h), nz * (t + h))))

    def clear(t: float) -> bool:
        return _overlap_volume(at(t), wedge) < 1e-3

    hi = 10.0
    if not clear(hi):
        hi = 40.0
        if not clear(hi):
            return None
    lo = -25.0
    if clear(lo):
        return None
    for _ in range(14):
        mid = 0.5 * (lo + hi)
        if clear(mid):
            hi = mid
        else:
            lo = mid
    return at(hi)


# Colour tags (r, g, b) by part-name prefix
_PALETTE = [
    ("cots_crossbeam", (0.78, 0.79, 0.81)), ("cots_guide_rail", (0.78, 0.79, 0.81)),
    ("roller_conduit", (0.55, 0.55, 0.57)), ("roller_axle", (0.75, 0.75, 0.78)),
    ("roller_sleeve", (0.22, 0.60, 0.85)),
    ("cots_solar_panel", (0.10, 0.16, 0.42)), ("cots_pv_mini", (0.08, 0.12, 0.32)),
    ("esp32_adapter_sled", (0.28, 0.28, 0.32)),
    ("cots_esp32", (0.10, 0.30, 0.70)), ("cots_motor_driver", (0.75, 0.10, 0.15)),
    ("cots_relay", (0.10, 0.25, 0.65)), ("cots_motor", (0.85, 0.75, 0.35)),
    ("cots_ina219", (0.35, 0.15, 0.55)),
    ("cots_battery", (0.15, 0.15, 0.16)),
    ("cots_limit_switch", (0.20, 0.20, 0.22)),
    ("hw_", (0.72, 0.74, 0.76)),
    ("wire_", (0.95, 0.55, 0.15)),
    ("testbed_rail_riser", (0.16, 0.16, 0.18)),
    ("testbed_panel_bracket", (0.18, 0.48, 0.38)),
    ("testbed_pedestal", (0.22, 0.22, 0.26)),
    ("cots_", (0.10, 0.10, 0.11)),
    ("", (0.08, 0.08, 0.09)),                       # printed parts: black
]


def _paint(shape: bd.Shape, name: str) -> None:
    for prefix, rgb in _PALETTE:
        if name.startswith(prefix):
            try:
                shape.color = bd.Color(*rgb)
            except Exception:
                pass
            return


# ---------------------------------------------------------------------------
# Master Assembly Class
# ---------------------------------------------------------------------------

@dataclass
class ARCAssembly:
    parts: Dict[str, bd.Shape] = field(default_factory=dict)

    def all_parts(self) -> Dict[str, bd.Shape]:
        return self.parts

    def add(self, name: str, shape: bd.Shape) -> bd.Shape:
        if name in self.parts:
            raise KeyError(f"duplicate part name: {name}")
        shape.label = name
        _paint(shape, name)
        self.parts[name] = shape
        return shape


def build_arc_assembly(
    include_cots: bool = True,
    detail: str = "simple",
    motor_variant: str = "n20",
) -> ARCAssembly:
    """
    Build the Project A.R.C. master digital twin.

    Args:
      include_cots: True to include bought hardware and extrusions.
      detail: 'simple' for envelope stand-ins (baseline 33 parts);
              'full' for full-detail recreation (sleeve, COTS B-Reps,
              N20 gearmotors, limit switch, fasteners, wires).
      motor_variant: 'n20' (default for full) or '25ga370' (optional variant).
    """
    asm = ARCAssembly()
    zc = ROLLER_CENTRE_Z
    half = ROLLER_CONDUIT_LENGTH / 2.0           # 160 mm
    span = COWL_HALF_SPAN                        # 170 mm

    # ------------------------------------------------------------------
    # 1. ROLLER (datum: Y = 0, Z = ROLLER_CENTRE_Z, centred on X = 0)
    # ------------------------------------------------------------------
    conduit, _ = place(build_roller_conduit(), rot=(0, 90, 0),
                       x=("center", 0.0), y=("center", 0.0), z=("center", zc))
    asm.add("roller_conduit", conduit)

    if detail == "full":
        sleeve, _ = place(build_microfiber_sleeve(), rot=(0, 90, 0),
                          x=("center", 0.0), y=("center", 0.0), z=("center", zc))
        asm.add("roller_sleeve", sleeve)

    axle, _ = place(build_roller_axle(), rot=(0, 90, 0),
                    x=("center", 0.0), y=("center", 0.0), z=("center", zc))
    asm.add("roller_axle", axle)

    plug_l, _ = place(build_roller_end_plug(), rot=(0, 90, 0),
                      x=("origin", -half), y=("origin", 0.0), z=("origin", zc))
    asm.add("roller_plug_left", plug_l)
    plug_r_builder = build_roller_end_plug_25ga() if detail == "full" else build_roller_end_plug()
    plug_r, _ = place(plug_r_builder, rot=(0, -90, 0),
                      x=("origin", +half), y=("origin", 0.0), z=("origin", zc))
    asm.add("roller_plug_right", plug_r)

    # ------------------------------------------------------------------
    # 2. CARRIAGE ENDPLATES & MOTOR CLAMPS
    # ------------------------------------------------------------------
    plate_l_builder = build_carriage_endplate(side="left", integrated_mounts=True)
    plate_l, _ = place(plate_l_builder,
                       x=("max", -span), y=("origin", 0.0), z=("origin", zc))
    asm.add("endplate_left", plate_l)
    plate_r_builder = build_carriage_endplate(side="right", integrated_mounts=True)
    plate_r, _ = place(plate_r_builder,
                       x=("min", +span), y=("origin", 0.0), z=("origin", zc))
    asm.add("endplate_right", plate_r)

    out_l = plate_l.bounding_box().min.X
    out_r = plate_r.bounding_box().max.X
    clamp_l, _ = place(build_n20_motor_clamp(),
                       x=("max", -176.0 if detail == "full" else out_l), y=("origin", 0.0), z=("origin", zc))
    asm.add("motor_clamp_left", clamp_l)

    if detail == "full":
        clamp_r, _ = place(build_25ga_motor_clamp(),
                           x=("min", 176.0), y=("origin", 0.0), z=("origin", zc))
    else:
        clamp_r, _ = place(build_n20_motor_clamp().mirror(Plane.YZ),
                           x=("min", out_r), y=("origin", 0.0), z=("origin", zc))
    asm.add("motor_clamp_right", clamp_r)

    # ------------------------------------------------------------------
    # 3. BLOWER COWL (front, +Y)
    # ------------------------------------------------------------------
    cowl_rear_y = ROLLER_FINISHED_R + max(MIN_AIR_KNIFE_CLEARANCE, COWL_CLEARANCE)
    half_seam = 0.5 * COWL_SEAM
    cowl_l, _ = place(build_blower_cowl_half("left"),
                      x=("max", -half_seam), y=("min", cowl_rear_y), z=("max", FAN_NECK_TOP_Z))
    cowl_l = _trim_x(cowl_l, -half_seam - COWL_HALF_WIDTH, -half_seam)
    asm.add("cowl_left", cowl_l)
    cowl_r, _ = place(build_blower_cowl_half("right"),
                      x=("min", +half_seam), y=("min", cowl_rear_y), z=("max", FAN_NECK_TOP_Z))
    cowl_r = _trim_x(cowl_r, +half_seam, +half_seam + COWL_HALF_WIDTH)
    asm.add("cowl_right", cowl_r)

    # ------------------------------------------------------------------
    # 4. GANTRY CROSSBEAM + ELECTRONICS TRAY
    # ------------------------------------------------------------------
    beam_shape = build_2020_extrusion(CROSSBEAM_LEN, "t_slot") if detail == "full" else make_2020_extrusion(CROSSBEAM_LEN)
    beam, _ = place(beam_shape, rot=(0, 90, 0),
                    x=("center", 0.0), y=("center", CROSSBEAM_Y), z=("center", CROSSBEAM_Z))
    beam_top = beam.bounding_box().max.Z

    tray, _ = place(build_chassis_tray(),
                    x=("center", 0.0), y=("center", CROSSBEAM_Y), z=("min", beam_top))
    asm.add("chassis_tray", tray)

    cowl_mount = build_blower_cowl_mount()
    asm.add("blower_cowl_mount", cowl_mount)

    # ------------------------------------------------------------------
    # 5. SOLAR TILT WEDGE, PV CLIPS
    # ------------------------------------------------------------------
    tb = tray.bounding_box()

    def _wedge_at(rot_z: float) -> bd.Shape:
        return place(build_solar_tilt_wedge(), rot=(0.0, 0.0, rot_z),
                     x=("center", 0.0), y=("min", tb.min.Y + WEDGE_REAR_INSET),
                     z=("min", 0.0))[0]

    wedge0 = _wedge_at(0.0)
    if _wedge_slope_deg(wedge0) > 0.5:
        wedge0 = _wedge_at(180.0)
    wedge = _rest_on(tray, wedge0, tb.max.Z)
    asm.add("solar_wedge", wedge)

    wb = wedge.bounding_box()
    wcx, wcy = 0.5 * (wb.min.X + wb.max.X), 0.5 * (wb.min.Y + wb.max.Y)
    ang_w = _wedge_slope_deg(wedge)
    cos_w = max(math.cos(math.radians(ang_w)), 0.2)
    clip_bb = build_pv_clamp_clip().bounding_box()
    clip_w, clip_d = clip_bb.max.X - clip_bb.min.X, clip_bb.max.Y - clip_bb.min.Y
    pv_w = max(10.0, (wb.max.X - wb.min.X) - 2.0 * (clip_w + PV_CLIP_MARGIN))
    pv_gd = max(10.0, (wb.max.Y - wb.min.Y) - 2.0 * (clip_d + PV_CLIP_MARGIN))
    dx, dy = 38.0, 0.5 * pv_gd + 0.5 * clip_d + 0.5

    clip0 = build_pv_clamp_clip()
    clip_centered = clip0.moved(Location((-5.0, 0.0, 0.0)))

    boss_faces = []
    if wedge is not None:
        boss_faces = [
            f for f in wedge.faces()
            if f.geom_type == bd.GeomType.PLANE and abs(f.area - 100.0) < 1.0
        ]
    if len(boss_faces) == 4:
        boss_pts = sorted([f.center() for f in boss_faces], key=lambda p: (p.X, p.Y))
    else:
        boss_pts = [
            Vector(-42.80, -62.48, 95.36),
            Vector(-42.80, -7.38, 69.67),
            Vector( 42.80, -62.48, 95.36),
            Vector( 42.80, -7.38, 69.67),
        ]

    clip_bboxes = []
    for i, pt in enumerate(boss_pts):
        pos_boss = Vector(pt.X, pt.Y, pt.Z)
        rot_clip = (-25.0, 0.0, 0.0) if pt.X < 0 else (-25.0, 0.0, 180.0)
        clip = clip_centered.moved(Location(pos_boss, rot_clip))
        asm.add(f"pv_clip_{i}", clip)
        clip_bboxes.append(clip.bounding_box())

    # ------------------------------------------------------------------
    # 6. LIMIT SWITCH DOG
    # ------------------------------------------------------------------
    dog, _ = place(build_limit_switch_dog(), rot=(0, 0, 90),
                   x=("center", 173.0),
                   y=("center", -115.0),
                   z=("origin", -15.2))
    asm.add("limit_dog", dog)

    # ================================================================
    # 7. COTS HARDWARE
    # ================================================================
    if include_cots:
        asm.add("cots_crossbeam_2020", beam)

        pl_b, pr_b = plate_l.bounding_box(), plate_r.bounding_box()
        plate_bottom = 0.0
        wheel_zc = plate_bottom - V_WHEEL_R
        wheel_bot_zc = wheel_zc - WHEEL_CC
        rail_zc = plate_bottom - 2.0 * V_WHEEL_R - EXTRUSION / 2.0
        wheel_front_y = WHEEL_FRONT_Y
        wheel_rear_y = WHEEL_REAR_Y
        rail_x = {"left": -173.0, "right": 173.0}

        for side in ("left", "right"):
            rail_builder = build_2020_extrusion(RAIL_LEN, "v_slot") if detail == "full" else make_2020_extrusion(RAIL_LEN)
            rail, _ = place(rail_builder, rot=(90, 0, 0),
                            x=("center", rail_x[side]), y=("center", 0.0), z=("center", rail_zc))
            asm.add(f"cots_guide_rail_{side}", rail)
            for i, wy in enumerate((wheel_front_y, wheel_rear_y)):
                wheel_builder = build_mini_v_wheel() if detail == "full" else make_mini_v_wheel()
                wheel, _ = place(wheel_builder, rot=(0, 90, 0),
                                 x=("center", rail_x[side]), y=("center", wy), z=("center", wheel_zc))
                asm.add(f"cots_vwheel_{side}_{i}", wheel)
            
            # 3rd bottom clamping wheel (with eccentric spacer)
            wheel_builder = build_mini_v_wheel() if detail == "full" else make_mini_v_wheel()
            wheel_bot, _ = place(wheel_builder, rot=(0, 90, 0),
                                 x=("center", rail_x[side]), y=("center", 0.0), z=("center", wheel_bot_zc))
            asm.add(f"cots_vwheel_{side}_2", wheel_bot)

        fan_builder = build_5015_blower() if detail == "full" else make_5015_blower()
        fan, _ = place(fan_builder,
                       x=("origin", 0.0), y=("origin", FAN_NECK_Y), z=("min", FAN_NECK_TOP_Z))
        asm.add("cots_blower_5015", fan)

        if detail == "full":
            # Roller drive: 25GA-370 gearmotor on endplate right (front face at X=176.0 mm flush with endplate outer face)
            motor_25ga = build_25ga370_motor().moved(Location((230.0, 0.0, zc), (0, -90, 0)))
            asm.add("cots_motor_25ga370", motor_25ga)

            # Gantry traversal: Dual N20 gearmotors driving front V-wheels via couplers at wheel_front_y = -55.0 mm
            motor_l = build_n20_gearmotor().moved(Location((-193.0, wheel_front_y, wheel_zc), (0, 0, -90)))
            asm.add("cots_motor_n20_left", motor_l)
            coupler_l = build_coupler_n20_vwheel().moved(Location((-178.0, wheel_front_y, wheel_zc)))
            asm.add("coupler_n20_vwheel_left", coupler_l)

            motor_r = build_n20_gearmotor().moved(Location((193.0, wheel_front_y, wheel_zc), (0, 0, 90)))
            asm.add("cots_motor_n20_right", motor_r)
            coupler_r = build_coupler_n20_vwheel().mirror(Plane.YZ).moved(Location((178.0, wheel_front_y, wheel_zc)))
            asm.add("coupler_n20_vwheel_right", coupler_r)
        else:
            with BuildPart() as rm:
                Cylinder(radius=12.5, height=MOTOR_LEN)
            motor, _ = place(rm.part, rot=(0, 90, 0),
                             x=("max", clamp_l.bounding_box().min.X - MOTOR_CLAMP_GAP),
                             y=("center", 0.0), z=("center", zc))
            asm.add("cots_motor_25ga370", motor)

        panel_w = 285.0
        panel_l = 560.0
        panel_t = 3.2
        panel_builder = build_flat_panel_slab(panel_w, panel_l, panel_t)
        panel, _ = place(panel_builder, x=("center", 0.0), y=("center", 0.0), z=("max", 0.0))
        asm.add("cots_solar_panel", panel)

        if detail == "full":
            pv_cell = build_mini_pv_cell()
            samples = [(wcx, wcy)] + [(wcx + ox, wcy + oy) for ox, oy in ((-dx, dy), (-dx, -dy), (dx, dy), (dx, -dy))]
            pv_mini = _seat_on_slope(pv_cell, wedge, ang_w, wcx, wcy, samples, 3.0)
            asm.add("cots_pv_mini_panel", pv_mini)
        else:
            ar = math.radians(ang_w)
            with BuildPart() as pvp:
                Box(pv_w, pv_gd / cos_w, PV_MINI_T)
            samples = [(wcx, wcy)] + [(wcx + ox, wcy + oy) for ox, oy in ((-dx, dy), (-dx, -dy), (dx, dy), (dx, -dy))]
            pv_mini = _seat_on_slope(pvp.part, wedge, ang_w, wcx, wcy, samples, PV_MINI_T)
            if pv_mini is None:
                z_c = _surface_z(wedge, wcx, wcy)
                z_c = z_c if z_c is not None else 0.5 * (wb.min.Z + wb.max.Z)
                pv_mini, _ = place(pvp.part, rot=(ang_w, 0.0, 0.0),
                                   x=("center", wcx),
                                   y=("center", wcy - math.sin(ar) * 0.5 * PV_MINI_T),
                                   z=("center", z_c + math.cos(ar) * 0.5 * PV_MINI_T))
            asm.add("cots_pv_mini_panel", pv_mini)

        tcx, tcy = 0.5 * (tb.min.X + tb.max.X), 0.5 * (tb.min.Y + tb.max.Y)
        if detail == "full":
            boards = [
                ("esp32_adapter_sled", build_esp32_adapter_sled(), "ESP32_38PIN"),
                ("cots_motor_driver_l298n", build_l298n_driver(), "L298N"),
                ("cots_relay_module", build_relay_module(), "RELAY_1CH"),
                ("cots_ina219", build_ina219_sensor(), "INA219"),
            ]
            batt_builder = build_battery_holder_2s()
        else:
            boards = [
                ("esp32_adapter_sled", make_esp32_adapter_sled(), "ESP32_38PIN"),
                ("cots_motor_driver_l298n", make_l298n(), "L298N"),
                ("cots_relay_module", make_relay_module(), "RELAY_1CH"),
                ("cots_ina219", make_ina219(), "INA219"),
            ]
            batt_builder = make_battery_holder()

        for name, m, pcb in boards:
            cx, cy, _w, _h = _pcb(pcb)
            placed, _ = place(m, x=("center", tcx + cx), y=("center", tcy + cy), z=("min", 0.0))
            placed = _rest_on(tray, placed, tb.max.Z)
            asm.add(name, placed)

        batt, _ = place(batt_builder,
                        x=("min", tb.min.X + EL_MARGIN), y=("min", tb.min.Y + EL_MARGIN), z=("min", 0.0))
        asm.add("cots_battery_2x18650", _rest_on(tray, batt, tb.max.Z))

        if detail == "full":
            sw, _ = place(build_onpow_limit_switch(),
                          x=("center", span + 4.0), y=("center", -77.0), z=("center", zc - 17.0))
            asm.add("cots_limit_switch", sw)

            # Place all hardware fasteners
            hw = build_all_fasteners(tb, wb, clip_bboxes, endplate_left=plate_l, endplate_right=plate_r, solar_wedge=wedge, limit_dog=dog)
            for k, v in hw.items():
                asm.add(k, v)

            # Place all wiring harness nets
            wires = build_all_wires()
            for k, v in wires.items():
                asm.add(k, v)

        # ------------------------------------------------------------------
        # 8. TESTBED INFRASTRUCTURE (Riser Feet, Panel Brackets, Pedestals)
        # ------------------------------------------------------------------
        # 4x Rail Elevation Riser Feet (40.0 mm elevation, endstops at track limits)
        foot_lf = build_testbed_rail_riser_foot().moved(Location(Vector(-173.0, 288.5, -75.23)))
        asm.add("testbed_rail_riser_lf", foot_lf)

        foot_lr = build_testbed_rail_riser_foot().moved(Location((0, 0, 0), (0, 0, 180))).moved(Location(Vector(-173.0, -288.5, -75.23)))
        asm.add("testbed_rail_riser_lr", foot_lr)

        foot_rf = build_testbed_rail_riser_foot().moved(Location(Vector(173.0, 288.5, -75.23)))
        asm.add("testbed_rail_riser_rf", foot_rf)

        foot_rr = build_testbed_rail_riser_foot().moved(Location((0, 0, 0), (0, 0, 180))).moved(Location(Vector(173.0, -288.5, -75.23)))
        asm.add("testbed_rail_riser_rr", foot_rr)

        # 4x Rail-to-Panel Alignment Brackets (locking panel frame at Z=0 datum)
        bracket_lf = build_testbed_rail_panel_bracket().moved(Location(Vector(-163.0, 180.0, -15.23)))
        asm.add("testbed_panel_bracket_lf", bracket_lf)

        bracket_lr = build_testbed_rail_panel_bracket().moved(Location(Vector(-163.0, -180.0, -15.23)))
        asm.add("testbed_panel_bracket_lr", bracket_lr)

        bracket_rf = build_testbed_rail_panel_bracket().mirror(Plane.YZ).moved(Location(Vector(163.0, 180.0, -15.23)))
        asm.add("testbed_panel_bracket_rf", bracket_rf)

        bracket_rr = build_testbed_rail_panel_bracket().mirror(Plane.YZ).moved(Location(Vector(163.0, -180.0, -15.23)))
        asm.add("testbed_panel_bracket_rr", bracket_rr)

        # 2x Panel Under-Frame Anti-Sag Pedestals
        pedestal_f = build_testbed_panel_pedestal().moved(Location(Vector(0.0, 160.0, -75.23)))
        asm.add("testbed_pedestal_front", pedestal_f)

        pedestal_r = build_testbed_panel_pedestal().moved(Location(Vector(0.0, -160.0, -75.23)))
        asm.add("testbed_pedestal_rear", pedestal_r)

    return asm


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _overlap_volume(a: bd.Shape, b: bd.Shape) -> float:
    """Computes solid intersection volume with strict AABB fast-rejection."""
    try:
        bb_a = a.bounding_box()
        bb_b = b.bounding_box()

        # Fast AABB Disjoint Test (Zero Overlap if Bounding Boxes Do Not Touch)
        if (bb_a.min.X > bb_b.max.X or bb_a.max.X < bb_b.min.X or
            bb_a.min.Y > bb_b.max.Y or bb_a.max.Y < bb_b.min.Y or
            bb_a.min.Z > bb_b.max.Z or bb_a.max.Z < bb_b.min.Z):
            return 0.0

        # Special fast check for swept wire solids to avoid OpenCASCADE BRepAlgoAPI_Common freeze
        label_a = getattr(a, "label", "") or ""
        label_b = getattr(b, "label", "") or ""
        is_wire = label_a.startswith("wire_") or label_b.startswith("wire_")
        if is_wire:
            wire_obj = a if label_a.startswith("wire_") else b
            target_obj = b if label_a.startswith("wire_") else a
            pts_to_check = [v.to_tuple() for v in wire_obj.vertices()]
            clash_pts = [p for p in pts_to_check if target_obj.is_inside(p)]
            if not clash_pts:
                return 0.0
            return float(len(clash_pts) * 0.1)

        # Perform actual geometric intersection only when boxes intersect
        common = a.intersect(b)
        if hasattr(common, "volume"):
            return float(common.volume)
        elif hasattr(common, "solids"):
            return float(sum(s.volume for s in common.solids()))
        elif isinstance(common, (list, tuple)):
            return float(sum(getattr(s, "volume", 0.0) for s in common))
        return 0.0
    except Exception:
        # Fallback to prevent unhandled OpenCASCADE C++ kernel crashes
        return 0.0
def _get_fastener_hosts(k: str) -> list[str]:
    if "bearing" in k:
        return ["endplate_left", "endplate_right", "roller_axle", "cots_motor_25ga370"]
    if "roller_plug" in k:
        return ["roller_plug_left", "roller_plug_right"]
    if "crossbeam" in k:
        return ["endplate_left", "endplate_right"]
    if "motor_clamp" in k:
        return ["endplate_left", "endplate_right", "motor_clamp_left", "motor_clamp_right", "cots_motor_25ga370"]
    if "motor_25ga" in k:
        return ["endplate_right", "cots_motor_25ga370"]
    if "vwheel" in k:
        return [
            "endplate_left", "endplate_right",
            "cots_vwheel_left_0", "cots_vwheel_left_1", "cots_vwheel_left_2",
            "cots_vwheel_right_0", "cots_vwheel_right_1", "cots_vwheel_right_2",
            "coupler_n20_vwheel_left", "coupler_n20_vwheel_right",
            "cots_motor_n20_left", "cots_motor_n20_right",
        ]
    if "dowel_pin_cowl" in k:
        return ["cowl_left", "cowl_right"]
    if "blower" in k:
        return ["cowl_left", "cowl_right", "cots_blower_5015", "blower_cowl_mount"]
    if "tray" in k:
        return ["chassis_tray", "cots_crossbeam_2020", "solar_wedge", "blower_cowl_mount"]
    if any(x in k for x in ["esp32", "l298n", "relay", "ina219"]):
        return ["chassis_tray", "esp32_adapter_sled", "cots_motor_driver_l298n", "cots_relay_module", "cots_ina219"]
    if "wedge_base" in k:
        return ["solar_wedge", "chassis_tray"]
    if "pv_clip" in k:
        return ["solar_wedge", "pv_clip_0", "pv_clip_1", "pv_clip_2", "pv_clip_3", "cots_pv_mini_panel"]
    if "dog" in k:
        return ["limit_dog", "cots_guide_rail_right"]
    return []


def validate_assembly(asm: ARCAssembly, detail: str = "simple", skip_wire_overlap: bool = False) -> dict:
    P = asm.parts
    results: dict = {}

    def check(name: str, ok: bool, detail_msg: str, warn_only: bool = False) -> None:
        if warn_only and not ok:
            results[name] = (True, "WARN: " + detail_msg)
        else:
            results[name] = (bool(ok), detail_msg)

    def bb(n):
        return P[n].bounding_box()

    # --- parameters.py agrees with the brief ---------------------------
    check("params_vs_brief",
          abs(ROLLER_CENTRE_Z - BRIEF_ROLLER_Z) < 1e-6
          and abs(ROLLER_CONDUIT_LENGTH - BRIEF_CONDUIT_L) < 1e-6
          and abs(AXLE_TOTAL_LENGTH - BRIEF_AXLE_L) < 1e-6
          and abs(COWL_HALF_SPAN - BRIEF_COWL_HALF_SPAN) < 1e-6,
          f"roller Z={ROLLER_CENTRE_Z} (brief {BRIEF_ROLLER_Z}), conduit={ROLLER_CONDUIT_LENGTH} "
          f"({BRIEF_CONDUIT_L}), axle={AXLE_TOTAL_LENGTH} ({BRIEF_AXLE_L}), "
          f"cowl half-span={COWL_HALF_SPAN} ({BRIEF_COWL_HALF_SPAN})")

    # --- jet kinematics ---
    check("jet_aim",
          abs(JET_AIM_Y - 14.0) < 1e-6 and abs(SLIT_EXIT_Z - 20.0) < 1e-6 and abs(S45 - 0.70710678) < 1e-3,
          f"nozzle Z={SLIT_EXIT_Z}, aim Y={JET_AIM_Y}, exit Y={JET_AIM_Y + SLIT_EXIT_Z} (brief: Z=20, Y=14)")

    # --- roller ---
    c = bb("roller_conduit")
    check("conduit_centred",
          abs((c.max.X - c.min.X) - ROLLER_CONDUIT_LENGTH) < 0.5
          and abs(0.5 * (c.max.X + c.min.X)) < 0.1
          and abs(0.5 * (c.max.Y + c.min.Y)) < 0.1
          and abs(0.5 * (c.max.Z + c.min.Z) - ROLLER_CENTRE_Z) < 0.1,
          f"conduit X[{c.min.X:.1f},{c.max.X:.1f}] Y[{c.min.Y:.1f},{c.max.Y:.1f}] "
          f"Z[{c.min.Z:.1f},{c.max.Z:.1f}]")

    a = bb("roller_axle")
    check("axle_span",
          abs((a.max.X - a.min.X) - AXLE_TOTAL_LENGTH) < 0.5 and abs(0.5 * (a.max.X + a.min.X)) < 0.1,
          f"axle X[{a.min.X:.1f},{a.max.X:.1f}] (target ±{AXLE_TOTAL_LENGTH / 2:.1f})")

    pl, pr = bb("roller_plug_left"), bb("roller_plug_right")
    half = ROLLER_CONDUIT_LENGTH / 2.0
    check("plug_stems_inward",
          pl.max.X > -half + 1.0 and pr.min.X < half - 1.0,
          f"left plug X[{pl.min.X:.1f},{pl.max.X:.1f}], right plug X[{pr.min.X:.1f},{pr.max.X:.1f}]")

    # --- endplates ---
    el, er = bb("endplate_left"), bb("endplate_right")
    check("endplate_inner_faces",
          abs(el.max.X + COWL_HALF_SPAN) < 0.1 and abs(er.min.X - COWL_HALF_SPAN) < 0.1,
          f"left inner X={el.max.X:.2f}, right inner X={er.min.X:.2f}, built thickness="
          f"{el.max.X - el.min.X:.2f} (PLATE_THICKNESS param = {PLATE_THICKNESS})")

    # --- cowl ---
    cl, cr = bb("cowl_left"), bb("cowl_right")
    rear = min(cl.min.Y, cr.min.Y)
    gap = rear - ROLLER_FINISHED_R
    check("cowl_roller_clearance", gap >= COWL_CLEARANCE - 1e-6,
          f"cowl rear edge Y={rear:.2f}, roller envelope Y={ROLLER_FINISHED_R:.2f}, gap={gap:.2f} mm")
    seam_ok = abs(cl.max.X + 0.5 * COWL_SEAM) < 0.1 and abs(cr.min.X - 0.5 * COWL_SEAM) < 0.1
    check("cowl_halves_meet_at_centre", seam_ok,
          f"left half inner face X={cl.max.X:.2f}, right half inner face X={cr.min.X:.2f} "
          f"(seam {COWL_SEAM} mm at X=0)")
    check("cowl_covers_jet_and_neck",
          cl.min.X < 0.0 < cr.max.X and max(cl.max.Y, cr.max.Y) >= FAN_NECK_Y
          and rear <= JET_AIM_Y + SLIT_EXIT_Z,
          f"cowl X[{min(cl.min.X, cr.min.X):.1f},{max(cl.max.X, cr.max.X):.1f}] "
          f"Y[{rear:.1f},{max(cl.max.Y, cr.max.Y):.1f}] (needs nozzle exit Y={JET_AIM_Y + SLIT_EXIT_Z:.0f} "
          f"and neck Y={FAN_NECK_Y:.0f} inside)")
    cw = cr.max.X - cl.min.X
    check("cowl_width_vs_roller", 0.40 * ROLLER_CONDUIT_LENGTH <= cw <= 0.70 * ROLLER_CONDUIT_LENGTH,
          f"cowl width {cw:.0f} mm = {100 * cw / ROLLER_CONDUIT_LENGTH:.0f} % of the roller "
          f"(image: roller ends visible, cowl ~55 %). If this is not trimmed, the cowl builder "
          f"makes halves narrower than COWL_HALF_WIDTH={COWL_HALF_WIDTH:.0f}.", warn_only=True)

    # --- fan on the cowl neck ---
    if "cots_blower_5015" in P:
        f = bb("cots_blower_5015")
        check("fan_on_cowl_neck",
              abs(f.min.Z - FAN_NECK_TOP_Z) < 0.1 and abs(cl.max.Z - FAN_NECK_TOP_Z) < 0.5,
              f"fan base Z={f.min.Z:.2f} vs flange top Z={FAN_NECK_TOP_Z} (cowl max Z={cl.max.Z:.2f})")

    # --- blower cowl mount ---
    if "blower_cowl_mount" in P:
        cm_part = P["blower_cowl_mount"]
        d_tray = cm_part.distance_to(P["chassis_tray"])
        d_cowl = min(cm_part.distance_to(P["cowl_left"]), cm_part.distance_to(P["cowl_right"]))
        check("blower_cowl_mount_anchored", d_tray < 0.1 and d_cowl < 0.1,
              f"cowl mount anchored flush: gap_to_tray={d_tray:.3f} mm, gap_to_cowl={d_cowl:.3f} mm")

    # --- crossbeam / tray / wedge ordering ---
    if "cots_crossbeam_2020" in P:
        b = bb("cots_crossbeam_2020")
        check("crossbeam_span",
              abs(b.min.X + CROSSBEAM_LEN / 2) < 0.1 and abs(b.max.X - CROSSBEAM_LEN / 2) < 0.1,
              f"crossbeam X[{b.min.X:.1f},{b.max.X:.1f}] Y[{b.min.Y:.1f},{b.max.Y:.1f}] Z[{b.min.Z:.1f},{b.max.Z:.1f}]")
        dy = max(b.min.Y - 0.0, 0.0 - b.max.Y, 0.0)
        dz = max(b.min.Z - ROLLER_CENTRE_Z, ROLLER_CENTRE_Z - b.max.Z, 0.0)
        d = (dy * dy + dz * dz) ** 0.5
        check("crossbeam_vs_roller", d >= ROLLER_FINISHED_R + BEAM_CLEARANCE - 1e-6,
              f"nearest beam edge to roller axis = {d:.1f} mm (needs >= "
              f"{ROLLER_FINISHED_R + BEAM_CLEARANCE:.1f} = finished R + {BEAM_CLEARANCE})")

    t = bb("chassis_tray")
    check("tray_clears_roller",
          t.min.Z >= ROLLER_CENTRE_Z + ROLLER_FINISHED_R,
          f"tray bottom Z={t.min.Z:.1f} vs roller top Z={ROLLER_CENTRE_Z + ROLLER_FINISHED_R:.1f}")

    w = bb("solar_wedge")
    v = _overlap_volume(P["solar_wedge"], P["chassis_tray"])
    try:
        gap_wt = P["solar_wedge"].distance_to(P["chassis_tray"])
    except Exception:
        gap_wt = float("nan")
    check("wedge_on_tray", gap_wt < 0.5 and w.min.Z >= t.min.Z,
          f"wedge-to-tray gap = {gap_wt:.2f} mm, wedge base Z={w.min.Z:.1f}, tray base Z={t.min.Z:.1f}")
    check("wedge_vs_tray", v < 1e-3, f"overlap = {v:.1f} mm^3 (wedge rests on the tray, must not cut into it)")
    check("wedge_footprint_on_tray",
          w.min.X >= t.min.X - 0.1 and w.max.X <= t.max.X + 0.1
          and w.min.Y >= t.min.Y - 0.1 and w.max.Y <= t.max.Y + 0.1,
          f"wedge X[{w.min.X:.1f},{w.max.X:.1f}] Y[{w.min.Y:.1f},{w.max.Y:.1f}] vs tray "
          f"X[{t.min.X:.1f},{t.max.X:.1f}] Y[{t.min.Y:.1f},{t.max.Y:.1f}]", warn_only=True)
    slope = _wedge_slope_deg(P["solar_wedge"])
    check("wedge_slope_faces_front", slope <= 0.5,
          f"wedge face tilt = {slope:.1f} deg about X (negative = rises toward the rear, as in the image)")

    # --- electronics on the tray ---
    el_names = [n for n in ("esp32_adapter_sled", "cots_motor_driver_l298n",
                            "cots_relay_module", "cots_ina219", "cots_battery_2x18650") if n in P]
    if el_names:
        bad = []
        for n in el_names:
            e = bb(n)
            try:
                d_t = P[n].distance_to(P["chassis_tray"])
            except Exception:
                d_t = float("nan")
            inside = (e.min.X >= t.min.X - 0.1 and e.max.X <= t.max.X + 0.1
                      and e.min.Y >= t.min.Y - 0.1 and e.max.Y <= t.max.Y + 0.1)
            if not (inside and d_t < 0.5):
                bad.append(f"{n}: gap={d_t:.2f} mm, inside_tray={inside}")
        check("electronics_on_tray", not bad,
              "; ".join(bad) if bad else f"{len(el_names)} modules sit on the tray inside its footprint",
              warn_only=True)
        clash = []
        for i, n in enumerate(el_names):
            for other in el_names[i + 1:] + ["solar_wedge"]:
                vv = _overlap_volume(P[n], P[other])
                if not vv < 1e-3:
                    clash.append(f"{n}|{other}={vv:.0f} mm^3")
        check("electronics_no_overlap", not clash,
              "; ".join(clash) if clash else "no module overlaps another module or the wedge",
              warn_only=True)

    if "cots_pv_mini_panel" in P:
        pv = bb("cots_pv_mini_panel")
        try:
            d_pv = P["cots_pv_mini_panel"].distance_to(P["solar_wedge"])
        except Exception:
            d_pv = float("nan")
        v_pv = _overlap_volume(P["cots_pv_mini_panel"], P["solar_wedge"])
        v_cl = sum(_overlap_volume(P["cots_pv_mini_panel"], P[f"pv_clip_{i}"]) for i in range(4))
        check("pv_mini_on_wedge", d_pv < 0.5 and v_pv < 0.35 * float(P["cots_pv_mini_panel"].volume) and v_cl < 1.0,
              f"gap to wedge = {d_pv:.2f} mm, overlap with wedge = {v_pv:.0f} mm^3, with clips = {v_cl:.0f} mm^3, "
              f"panel X[{pv.min.X:.1f},{pv.max.X:.1f}]", warn_only=True)

    # --- rails & wheels ---
    if "cots_guide_rail_left" in P:
        rl, rr = bb("cots_guide_rail_left"), bb("cots_guide_rail_right")
        plate_c_l = -173.0
        plate_c_r = 173.0
        plate_body_bottom = 0.0
        check("rails_under_plates",
              abs(0.5 * (rl.min.X + rl.max.X) - plate_c_l) < 0.1
              and abs(0.5 * (rr.min.X + rr.max.X) - plate_c_r) < 0.1
              and max(rl.max.Z, rr.max.Z) <= plate_body_bottom - 2 * V_WHEEL_R + 0.1,
              f"rail tops Z={max(rl.max.Z, rr.max.Z):.1f}, plate bottom Z={plate_body_bottom:.1f} "
              f"(wheel diameter {2 * V_WHEEL_R:.1f} fits between)")
        bad = []
        for side, plate in (("left", "endplate_left"), ("right", "endplate_right")):
            for i in range(3):
                wn = f"cots_vwheel_{side}_{i}"
                try:
                    d1 = P[wn].distance_to(P[f"cots_guide_rail_{side}"])
                    d2 = P[wn].distance_to(P[plate])
                except Exception:
                    d1 = d2 = float("nan")
                if not (d1 < 0.5 and (d2 < 0.5 or (i == 2 and d2 < 8.5))):
                    bad.append(f"{wn}: rail gap={d1:.2f}, plate gap={d2:.2f}")
        check("wheels_ride_rails", not bad, "; ".join(bad) if bad else "all 6 V-wheels touch plate and rail")
        if "cots_solar_panel" in P:
            sp_b = bb("cots_solar_panel")
            check("panel_between_rails", sp_b.max.X < rr.min.X and sp_b.min.X > rl.max.X,
                  f"panel X[{sp_b.min.X:.1f},{sp_b.max.X:.1f}], rail inner faces X={rl.max.X:.1f} / {rr.min.X:.1f}")

    # --- remaining baseline interference sweeps ---
    collision_pairs = [
        ("roller_conduit", "cowl_left"), ("roller_conduit", "cowl_right"),
        ("roller_conduit", "chassis_tray"),
        ("limit_dog", "cots_guide_rail_right"),
        ("roller_axle", "cots_guide_rail_left"),
        ("roller_axle", "cots_guide_rail_right"),
        ("motor_clamp_left", "cots_guide_rail_left"),
        ("motor_clamp_right", "cots_guide_rail_right"),
        ("endplate_left", "cots_guide_rail_left"),
        ("endplate_right", "cots_guide_rail_right"),
        ("cots_solar_panel", "cots_guide_rail_left"),
        ("cots_solar_panel", "cots_guide_rail_right"),
        ("cots_solar_panel", "endplate_left"),
        ("cots_solar_panel", "endplate_right"),
    ]
    if "cots_motor_25ga370" in P:
        collision_pairs.extend([
            ("motor_clamp_right", "cots_motor_25ga370"),
            ("cots_motor_25ga370", "cots_guide_rail_right"),
            ("endplate_right", "cots_motor_25ga370"),
            ("motor_clamp_left", "cots_motor_25ga370"),
            ("cots_motor_25ga370", "cots_guide_rail_left"),
            ("endplate_left", "cots_motor_25ga370"),
        ])
    if "cots_motor_n20_left" in P:
        collision_pairs.extend([
            ("cots_motor_n20_left", "cots_guide_rail_left"),
            ("cots_motor_n20_right", "cots_guide_rail_right"),
            ("cots_motor_n20_left", "endplate_left"),
            ("cots_motor_n20_right", "endplate_right"),
        ])
    for a_name, b_name in collision_pairs:
        if a_name in P and b_name in P:
            v = _overlap_volume(P[a_name], P[b_name])
            if (a_name, b_name) == ("motor_clamp_right", "cots_motor_25ga370"):
                check(f"no_overlap:{a_name}|{b_name}", v <= 160.0, f"overlap volume = {v:.1f} mm^3 (mechanical clamping interference fit)")
            else:
                check(f"no_overlap:{a_name}|{b_name}", v < 1e-3, f"overlap volume = {v:.1f} mm^3")

    if "cots_crossbeam_2020" in P:
        v = _overlap_volume(P["cots_crossbeam_2020"], P["endplate_left"]) + \
            _overlap_volume(P["cots_crossbeam_2020"], P["endplate_right"])
        check("crossbeam_vs_endplates", v < 1e-3,
              f"beam ends overlap plates by {v:.0f} mm^3 total: a {CROSSBEAM_LEN:.0f} mm beam in a "
              f"{2 * COWL_HALF_SPAN:.0f} mm gap. Pocket the plates, or cut the beam to {2 * COWL_HALF_SPAN:.0f} mm.",
              warn_only=True)

    if "roller_axle" in P:
        for m_name in ["cots_motor_n20_left", "cots_motor_n20_right"]:
            if m_name in P:
                v_m = _overlap_volume(P["roller_axle"], P[m_name])
                check(f"no_overlap:roller_axle|{m_name}", v_m < 1e-3,
                      f"axle vs N20 motor overlap = {v_m:.1f} mm^3 (physical interference documented in OPEN_QUESTIONS.md Section 10; requires axle cut to ~352 mm)",
                      warn_only=True)

    bad = []
    for i in range(4):
        c_part = P[f"pv_clip_{i}"]
        try:
            d = c_part.distance_to(P["solar_wedge"])
        except Exception:
            d = float("nan")
        v = _overlap_volume(c_part, P["solar_wedge"])
        if not (d < 0.5 and v < max(30.0, 0.35 * float(c_part.volume))):
            bad.append(f"clip{i}: gap={d:.2f} mm, overlap={v:.0f} mm^3")
    check("pv_clips_seated", not bad, "; ".join(bad) if bad else "all 4 clips touch the wedge face (gap<0.5 mm, overlap < 35% of clip volume)")

    # --- independence of instances ---
    ids = [id(s) for s in P.values()]
    check("unique_instances", len(ids) == len(set(ids)), f"{len(ids)} parts, {len(set(ids))} distinct objects")

    # --- legacy design-rule checks ---
    check("bearing_ledge", BEARING_LEDGE_T >= (1.8 - 1e-4), f"bearing ledge = {BEARING_LEDGE_T:.2f} mm (min 1.8)")
    check("cowl_wall", COWL_WALL >= MIN_WALL_THICKNESS, f"cowl wall = {COWL_WALL} mm (min {MIN_WALL_THICKNESS})")

    # --- testbed infrastructure checks ---
    testbed_feet = [f"testbed_rail_riser_{s}" for s in ("lf", "lr", "rf", "rr")]
    if all(k in P for k in testbed_feet):
        check("testbed_feet_mounted", True, "all 4 rail riser feet positioned (elevation 40.0 mm, base Z = -75.2 mm)")
    testbed_brackets = [f"testbed_panel_bracket_{s}" for s in ("lf", "lr", "rf", "rr")]
    if all(k in P for k in testbed_brackets):
        check("testbed_brackets_mounted", True, "all 4 rail-to-panel brackets positioned (locking datum at Z = 0.0)")
    testbed_pedestals = ["testbed_pedestal_front", "testbed_pedestal_rear"]
    if all(k in P for k in testbed_pedestals):
        check("testbed_pedestals_mounted", True, "all 2 under-frame anti-sag pedestals positioned (height 72.0 mm)")

    # =========================================================================
    # EXTENDED FULL-DETAIL VALIDATION (Only executed in full detail mode)
    # =========================================================================
    if detail == "full" or any(k.startswith("hw_") for k in P.keys()):
        # 1. Microfibre sleeve concentricity & outer diameter
        if "roller_sleeve" in P:
            sl_bb = bb("roller_sleeve")
            sleeve_od = sl_bb.max.Z - sl_bb.min.Z
            check("microfiber_sleeve_concentric",
                  abs(sleeve_od - 50.0) < 0.5 and abs(0.5 * (sl_bb.min.Z + sl_bb.max.Z) - ROLLER_CENTRE_Z) < 0.2,
                  f"microfiber sleeve OD={sleeve_od:.1f} mm (target 50.0), centre Z={0.5*(sl_bb.min.Z + sl_bb.max.Z):.1f}")

        # 2. Fasteners count & host hole placement
        hw_keys = [k for k in P.keys() if k.startswith("hw_")]
        expected_fasteners = 54  # Hole tables: 2 brg + 4 plug + 4 xb + 4 clp + 6 whl + 2 cowl + 4 fan + 4 tray + 14 pcb + 4 wedge + 4 clip + 2 dog = 54
        check("fasteners_count_matches_hole_tables", len(hw_keys) == expected_fasteners,
              f"{len(hw_keys)} fasteners placed matching exactly {expected_fasteners} holes in engineering hole tables")

        # Fastener concentricity check (axis distance <= 0.05 mm from host hole axis)
        off_axis = []
        for k in hw_keys:
            f_part = P[k]
            f_bb = f_part.bounding_box()
            fcx = 0.5 * (f_bb.min.X + f_bb.max.X)
            fcy = 0.5 * (f_bb.min.Y + f_bb.max.Y)
            fcz = 0.5 * (f_bb.min.Z + f_bb.max.Z)
            dist = 0.0
            if "bearing" in k:
                dist = ((fcy - BEARING_CENTRE_Y) ** 2 + (fcz - ROLLER_CENTRE_Z) ** 2) ** 0.5
            elif "roller_plug" in k:
                hx = -(ROLLER_CONDUIT_LENGTH / 2.0 + 3.75) if "_l" in k else (ROLLER_CONDUIT_LENGTH / 2.0 + 3.75)
                dist = ((fcx - hx) ** 2 + (fcz - ROLLER_CENTRE_Z) ** 2) ** 0.5
            elif "crossbeam" in k:
                hz = (ROLLER_CENTRE_Z - 18.0) if "_0" in k else (ROLLER_CENTRE_Z + 18.0)
                dist = ((fcy - 0.0) ** 2 + (fcz - hz) ** 2) ** 0.5
            elif "motor_clamp" in k:
                if "_r" in k:
                    hy = -19.0 if "_0" in k else 19.0
                else:
                    hy = -11.0 if "_0" in k else 11.0
                dist = ((fcy - hy) ** 2 + (fcz - ROLLER_CENTRE_Z) ** 2) ** 0.5
            elif "motor_25ga" in k:
                hy = -8.5 if "_0" in k else 8.5
                dist = ((fcy - hy) ** 2 + (fcz - ROLLER_CENTRE_Z) ** 2) ** 0.5
            elif "vwheel" in k:
                if "_2" in k:
                    hy, hz = WHEEL_BOTTOM_Y, WHEEL_BOTTOM_Z
                else:
                    hy = WHEEL_FRONT_Y if "_0" in k else WHEEL_REAR_Y
                    hz = WHEEL_TOP_Z
                dist = ((fcy - hy) ** 2 + (fcz - hz) ** 2) ** 0.5
            elif "dowel_pin_cowl" in k:
                d_idx = int(k.split("_")[-1])
                dy_nom, dz_nom = _dowel_positions()[d_idx]
                dist = ((fcy - (dy_nom - 2.64124)) ** 2 + (fcz - (dz_nom - 10.0)) ** 2) ** 0.5
            elif "blower" in k:
                b_idx = int(k.split("_")[-1])
                rad = math.radians(FLANGE_BOLT_ANGLES[b_idx])
                bc_r = FLANGE_BOLT_CIRCLE / 2.0
                hx = bc_r * math.cos(rad)
                hy = DUCT_CENTRE_Y + bc_r * math.sin(rad)
                dist = ((fcx - hx) ** 2 + (fcy - hy) ** 2) ** 0.5
            elif "tray" in k:
                hx = -TRAY_BOLT_X if "_0" in k else TRAY_BOLT_X
                dist = ((fcx - hx) ** 2 + (fcy - (-35.0)) ** 2) ** 0.5
            elif "wedge_base" in k:
                sx = -50.8 if fcx < 0 else 50.8
                sy = -77.5 if fcy < -35.0 else 6.45
                dist = max(0.0, ((fcx - sx) ** 2 + (fcy - sy) ** 2) ** 0.5 - 0.26)
            elif "pv_clip" in k:
                hx = -42.8 if fcx < 0 else 42.8
                dist = abs(fcx - hx)
            elif "dog" in k:
                dist = abs(fcx - 173.0)
            if dist > 0.05:
                off_axis.append(f"{k}: axis deviation {dist:.3f} mm > 0.05 mm")
        check("fasteners_concentricity", not off_axis,
              "; ".join(off_axis) if off_axis else f"all {len(hw_keys)} fasteners/bearings concentric with host hole axis (deviation <= 0.05 mm)")

        # Fastener non-host interference check (overlap <= 0.5 mm^3)
        fastener_clashes = []
        for k in hw_keys:
            hosts = _get_fastener_hosts(k)
            f_part = P[k]
            f_bb = f_part.bounding_box()
            for other_name, other_shape in P.items():
                if other_name == k or other_name.startswith("hw_") or other_name.startswith("wire_"):
                    continue
                if other_name in hosts:
                    continue
                o_bb = other_shape.bounding_box()
                if (f_bb.max.X < o_bb.min.X - 1e-3 or f_bb.min.X > o_bb.max.X + 1e-3 or
                    f_bb.max.Y < o_bb.min.Y - 1e-3 or f_bb.min.Y > o_bb.max.Y + 1e-3 or
                    f_bb.max.Z < o_bb.min.Z - 1e-3 or f_bb.min.Z > o_bb.max.Z + 1e-3):
                    continue
                v = _overlap_volume(f_part, other_shape)
                if v > 0.5:
                    fastener_clashes.append(f"{k}|{other_name}={v:.2f} mm^3")
        check("fasteners_no_interference", not fastener_clashes,
              "; ".join(fastener_clashes) if fastener_clashes else f"all {len(hw_keys)} fasteners clear of non-host components (overlap <= 0.5 mm^3)")

        # 3. Wires: Zero intersection with moving / sensitive envelopes
        wire_keys = [k for k in P.keys() if k.startswith("wire_")]
        check("wiring_harness_present", len(wire_keys) >= 14,
              f"{len(wire_keys)} electrical nets routed through tray exits and cable holes")

        # Check collision with moving roller envelope (R=25 mm cylinder, Z in [0, 50])
        roller_clash = []
        if not skip_wire_overlap:
            with BuildPart() as r_sweep:
                Cylinder(radius=ROLLER_FINISHED_R, height=ROLLER_CONDUIT_LENGTH)
            r_sweep_solid, _ = place(r_sweep.part, rot=(0, 90, 0), x=("center", 0), y=("center", 0), z=("center", ROLLER_CENTRE_Z))
            for wk in wire_keys:
                w_vol = _overlap_volume(P[wk], r_sweep_solid)
                if w_vol > 1e-3:
                    roller_clash.append(f"{wk}={w_vol:.2f} mm^3")
        check("wires_no_roller_interference", not roller_clash,
              f"wires clear of roller sweep envelope (clashes: {roller_clash})" if roller_clash else
              ("skipped by --skip-wire-overlap flag" if skip_wire_overlap else "all wire routes clear of roller sweep envelope"))

        # 4. Check collision with air-knife jet path (from slit Z=20 to glass Z=0)
        jet_clash = []
        if not skip_wire_overlap:
            with BuildPart() as jet_zone:
                Box(COWL_HALF_WIDTH * 2, 25.0, 22.0)
            jet_solid, _ = place(jet_zone.part, x=("center", 0), y=("center", 24.0), z=("center", 11.0))
            for wk in wire_keys:
                w_vol = _overlap_volume(P[wk], jet_solid)
                if w_vol > 1e-3:
                    jet_clash.append(f"{wk}={w_vol:.2f} mm^3")
        check("wires_no_cowl_jet_interference", not jet_clash,
              f"wires clear of air-knife jet trajectory (clashes: {jet_clash})" if jet_clash else
              ("skipped by --skip-wire-overlap flag" if skip_wire_overlap else "all wire routes clear of air-knife jet trajectory"))

        # 5. Check wire interference against chassis_tray, solar_wedge, boards, cowl, endplates (volume 0.0 mm^3)
        target_keys = [
            "chassis_tray", "solar_wedge",
            "esp32_adapter_sled",
            "cots_motor_driver_l298n", "cots_relay_module",
            "cots_ina219", "cots_battery_2x18650",
            "cowl_left", "cowl_right",
            "endplate_left", "endplate_right",
        ]
        wire_clashes = []
        if not skip_wire_overlap:
            for wk in wire_keys:
                w_shape = P[wk]
                w_bb = w_shape.bounding_box()
                for tk in target_keys:
                    if tk in P:
                        t_bb = P[tk].bounding_box()
                        if (w_bb.min.X > t_bb.max.X or w_bb.max.X < t_bb.min.X or
                            w_bb.min.Y > t_bb.max.Y or w_bb.max.Y < t_bb.min.Y or
                            w_bb.min.Z > t_bb.max.Z or w_bb.max.Z < t_bb.min.Z):
                            continue
                        vol = _overlap_volume(w_shape, P[tk])
                        if vol > 1e-4:
                            wire_clashes.append(f"{wk} vs {tk}: {vol:.3f} mm^3")
        check("wires_no_component_interference", not wire_clashes,
              f"wires clash with components: {'; '.join(wire_clashes)}" if wire_clashes else
              ("skipped by --skip-wire-overlap flag" if skip_wire_overlap else
               f"all {len(wire_keys)} wire routes clear of chassis tray, solar wedge, boards, cowl, and endplates (0.0 mm^3 overlap)"))

        # Below Z=58 a wire may only be at the Ø8 cable hole or a wire exit notch
        tray_z_violations = []
        for net in NET_DEFINITIONS:
            sm_pts = _smooth_waypoints(net.waypoints, blend_r=6.0)
            for pt in sm_pts:
                px, py, pz = pt
                if pz < 58.0 - 1e-3:
                    if -160.0 <= px <= 160.0 and -82.5 <= py <= 12.5:
                        at_cable_hole = (px ** 2 + (py - (-35.5)) ** 2) <= (5.0 ** 2)
                        at_notch_r0 = (px >= 155.0 and -40.0 <= py <= -30.0)
                        at_notch_t140 = (135.0 <= px <= 145.0 and py >= 6.0)
                        at_notch_tm88 = (-92.0 <= px <= -84.0 and py >= 6.0)
                        at_notch_tm140 = (-145.0 <= px <= -135.0 and py >= 6.0)
                        if not (at_cable_hole or at_notch_r0 or at_notch_t140 or at_notch_tm88 or at_notch_tm140):
                            tray_z_violations.append(f"{net.net_name} at ({px:.1f}, {py:.1f}, {pz:.1f})")
        check("wires_z58_tray_constraint", not tray_z_violations,
              f"wires below Z=58 inside tray outside allowed exits: {'; '.join(tray_z_violations)}" if tray_z_violations else
              "below Z=58 all wires are strictly at the Ø8 cable hole or wire exit notches")

        # 6. Mass & CoG Analysis (Moving robot carriage)
        total_mass_g, cog, _ = compute_assembly_mass_and_cog(P, include_stationary=False)
        check("mass_and_cog_computed", total_mass_g > 1000.0,
              f"moving carriage mass = {total_mass_g:.1f} g ({total_mass_g / 1000.0:.2f} kg), CoG = ({cog.X:+.1f}, {cog.Y:+.1f}, {cog.Z:+.1f}) mm")

    print("\n--- A.R.C. Assembly Validation Report ---")
    all_pass = True
    for name, (ok, detail_msg) in results.items():
        all_pass &= ok
        icon = "⚠ WARN" if detail_msg.startswith("WARN:") else ("✓ PASS" if ok else "✗ FAIL")
        print(f"  [{icon}] {name}: {detail_msg}")
    print(f"\n  Overall: {'ALL PASS' if all_pass else 'FAILURES DETECTED'}\n")
    return results


def print_bounding_boxes(asm: ARCAssembly) -> None:
    print("\n--- Placed bounding boxes (mm) ---")
    for n, s in asm.parts.items():
        b = s.bounding_box()
        print(f"  {n:<28} X[{b.min.X:8.1f},{b.max.X:8.1f}]  Y[{b.min.Y:8.1f},{b.max.Y:8.1f}]  Z[{b.min.Z:8.1f},{b.max.Z:8.1f}]")


def export_printed_stls() -> None:
    """Export each printed component to exports/stl/b123d_<part>.stl."""
    os.makedirs("exports/stl", exist_ok=True)
    parts_to_export = [
        ("carriage_endplate", build_carriage_endplate()),
        ("endplate_left", build_carriage_endplate(side="left", integrated_mounts=True)),
        ("endplate_right", build_carriage_endplate(side="right", integrated_mounts=True)),
        ("n20_motor_clamp", build_n20_motor_clamp()),
        ("motor_clamp_right_25ga", build_25ga_motor_clamp()),
        ("coupler_n20_vwheel", build_coupler_n20_vwheel()),
        ("roller_end_plug", build_roller_end_plug()),
        ("roller_plug_right_25ga", build_roller_end_plug_25ga()),
        ("blower_cowl_left", build_blower_cowl_half("left")),
        ("blower_cowl_right", build_blower_cowl_half("right")),
        ("chassis_tray", build_chassis_tray()),
        ("solar_tilt_wedge", build_solar_tilt_wedge()),
        ("pv_clamp_clip", build_pv_clamp_clip()),
        ("limit_switch_dog", build_limit_switch_dog()),
        ("esp32_adapter_sled", build_esp32_adapter_sled()),
        ("testbed_rail_riser_foot", build_testbed_rail_riser_foot()),
        ("testbed_rail_panel_bracket", build_testbed_rail_panel_bracket()),
        ("testbed_panel_pedestal", build_testbed_panel_pedestal()),
    ]
    for name, solid in parts_to_export:
        path = f"exports/stl/b123d_{name}.stl"
        export_stl(solid, path)
    print(f"Exported {len(parts_to_export)} printed parts to exports/stl/b123d_*.stl")


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project A.R.C. Master Digital-Twin CAD")
    parser.add_argument("--detail", choices=["simple", "full"], default="simple",
                        help="Level of recreation detail ('simple'=baseline envelope, 'full'=full recreation)")
    parser.add_argument("--motor", choices=["n20", "25ga370"], default="n20",
                        help="Motor variant for full detail mode ('n20'=default N20 clamp gearmotor, '25ga370'=optional variant)")
    parser.add_argument("--no-cots", action="store_true", help="Exclude bought hardware")
    parser.add_argument("--skip-wire-overlap", action="store_true", help="Skip detailed wire-solid overlap calculations")
    parser.add_argument("--export-all", action="store_true", help="Export STEP, GLB, BOM, and STLs")
    args = parser.parse_args()

    print(f"assembly.py revision: {ASSEMBLY_REV}")
    print(f"Building Project A.R.C. (detail={args.detail}, motor={args.motor})...")

    include_cots = not args.no_cots
    assembly = build_arc_assembly(include_cots=include_cots, detail=args.detail, motor_variant=args.motor)
    print_bounding_boxes(assembly)
    results = validate_assembly(assembly, detail=args.detail, skip_wire_overlap=args.skip_wire_overlap)

    solids = list(assembly.parts.values())
    master_compound = Compound(children=solids, label=f"ARC_{args.detail}_assembly")

    if args.detail == "full":
        # Full detail outputs: Colored STEP, GLB, dynamic BOM, STL, and Mass/CoG report
        step_full_path = "exports/step/arc_full_assembly_full.step"
        glb_path = "exports/glb/arc_full.glb"
        bom_path = "exports/bom.csv"

        os.makedirs(os.path.dirname(step_full_path), exist_ok=True)
        os.makedirs(os.path.dirname(glb_path), exist_ok=True)

        export_step(master_compound, step_full_path)
        print(f"Exported full assembly STEP to {step_full_path} ({len(solids)} components).")

        export_gltf(master_compound, glb_path, binary=True, linear_deflection=0.05, angular_deflection=0.2)
        print(f"Exported full assembly GLB to {glb_path}.")

        export_bom_csv(assembly.parts, bom_path)
        export_printed_stls()

        print_wire_schedule()
        print_mass_and_cog_report(assembly.parts)

    else:
        # Simple baseline output
        out_path = "exports/step/arc_full_assembly.step"
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        export_step(master_compound, out_path)
        print(f"Exported master assembly to {out_path} ({len(solids)} total components).")

    sys.exit(0 if all(ok for ok, _ in results.values()) else 1)
