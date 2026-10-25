"""
PROJECT A.R.C. – Centralised Engineering Parameters
=====================================================
Single source of truth for every dimensional constant used across the
build123d CAD suite.  Units: millimetres, degrees.

Origin convention (global CAD frame)
--------------------------------------
  (0, 0, 0) – roller contact line on solar-panel glass face.
  X-axis    – lateral (along 320 mm roller & 350 mm crossbeam). X=0 = centreline.
  Y-axis    – gantry travel direction.  +Y = forward (direction of cleaning advance).
  Z-axis    – normal to solar panel glass.  +Z = up into free space.
  Panel glass face – Z = 0.  Glass slab – Z in [-3.2, 0].
  Roller centreline – (X in [-160, 160], Y = 0, Z = 25.0).
"""

from __future__ import annotations
import math

# =============================================================================
# GLOBAL / SHARED
# =============================================================================

EPS: float = 0.01          # epsilon overlap – avoids coincident-face artefacts (mm)

# =============================================================================
# PART D – ROLLER CORE & DRIVE ASSEMBLY  (phase1.scad)
# =============================================================================

# Conduit core (1.25" UPVC electrical conduit)
ROLLER_CONDUIT_OD: float = 41.2
ROLLER_CONDUIT_ID: float = 36.0
ROLLER_CONDUIT_LENGTH: float = 320.0

# Microfiber sleeve
ROLLER_FINISHED_OD: float = 50.0
ROLLER_FINISHED_R: float = ROLLER_FINISHED_OD / 2.0    # 25.0 mm

# Central axle (continuous EN31 silver steel rod – NEVER split or clipped)
AXLE_DIAMETER: float = 4.0
AXLE_CLEARANCE: float = 0.2                             # sliding fit
AXLE_BORE_D: float = AXLE_DIAMETER + AXLE_CLEARANCE    # 4.2 mm bore in plugs
AXLE_TOTAL_LENGTH: float = 390.0

# Roller global position
ROLLER_CENTRE_Z: float = 25.3
ROLLER_CENTRE_Y: float = 0.0

# End plug (qty 2, press-fit into conduit ends)
PLUG_BODY_D: float = ROLLER_CONDUIT_ID                 # 36.0 mm
PLUG_BODY_LENGTH: float = 20.0
PLUG_LEAD_CHAMFER: float = 1.0                          # 45 deg lead-in chamfer
PLUG_FLANGE_D: float = 40.0
PLUG_FLANGE_THICKNESS: float = 7.5                      # 7.5 mm external collar (outside conduit)
PLUG_COLLAR_D: float = 24.0                             # 24.0 mm OD external collar

# M3 captive nut pocket inside external collar
NUT_AF: float = 5.5
NUT_DEPTH: float = 2.5
NUT_TOLERANCE: float = 0.2
NUT_AF_ACTUAL: float = NUT_AF + NUT_TOLERANCE
NUT_AC_ACTUAL: float = NUT_AF_ACTUAL / math.cos(math.radians(30))
NUT_DEPTH_ACTUAL: float = NUT_DEPTH + NUT_TOLERANCE
NUT_Z_ALONG_PLUG: float = PLUG_BODY_LENGTH + 7.5 / 2.0  # 23.75 mm from tip (inside external collar)
NUT_WALL_MIN: float = 1.2

SET_SCREW_D: float = 3.2                               # M3 set-screw clearance bore

# =============================================================================
# PART C – CARRIAGE ENDPLATE  (phase1.scad)
# =============================================================================

PLATE_LENGTH: float = 136.0                             # Expanded to 136.0 mm for 110 mm wide-stance wheelbase
PLATE_HEIGHT: float = 50.0
PLATE_THICKNESS: float = 4.0
PLATE_CORNER_R: float = 4.0

# 684ZZ bearing pocket
BRG_OD_NOMINAL: float = 9.0
BRG_WIDTH: float = 4.0
BRG_PRESS_FIT: float = 0.1
BRG_POCKET_D: float = BRG_OD_NOMINAL + BRG_PRESS_FIT   # 9.1 mm
BRG_POCKET_DEPTH: float = BRG_WIDTH + 0.2               # 4.2 mm
BRG_THROUGH_D: float = 6.0
BEARING_BOSS_D: float = 16.0
BEARING_BOSS_H: float = 2.0
BEARING_LEDGE_T: float = PLATE_THICKNESS + BEARING_BOSS_H - BRG_POCKET_DEPTH  # 1.8 mm
BEARING_CENTRE_Y: float = 0.0                           # Fixed: Roller axis is strictly at Y = 0.0 mm
BEARING_CENTRE_Z: float = 0.0

# V-wheel axle holes & 3-wheel wide-stance geometry
RAIL_WIDTH: float = 20.0
WHEEL_PITCH_D: float = 15.23
WHEEL_CC: float = RAIL_WIDTH + WHEEL_PITCH_D            # 35.23 mm
WHEEL_HOLE_D: float = 5.3
WHEELBASE_Y: float = 110.0                              # 110.0 mm wide stance
WHEEL_FRONT_Y: float = -55.0                            # Front driven V-wheel
WHEEL_REAR_Y: float = 55.0                              # Rear passive V-wheel
WHEEL_BOTTOM_Y: float = 0.0                             # 3rd bottom clamping V-wheel
WHEEL_TOP_Z: float = -7.615                             # Global Z of top wheels
WHEEL_BOTTOM_Z: float = -42.845                         # Global Z of bottom clamping wheel
WHEEL_ECCENTRIC_BORE_D: float = 7.15                    # 7.15 mm through-bore for eccentric spacer boss
WHEEL_PASSIVE_BORE_D: float = 5.3                       # 5.3 mm through-bore for passive M5 bolt
WHEEL_CENTRE_Y: float = -55.0

# X-axis crossbeam M5 counterbored holes
XB_CLEAR_D: float = 5.2
XB_CBORE_D: float = 9.6
XB_CBORE_DEPTH: float = 2.6
XB_PITCH: float = 36.0

# N20 motor M3 mounting holes
MOTOR_HOLE_D: float = 3.2
MOTOR_PITCH: float = 22.0

# N20 motor gearbox clamp
MOTOR_GBX_W: float = 12.0
MOTOR_GBX_H: float = 10.0
MOTOR_GBX_L: float = 15.0
CLAMP_WALL: float = 3.0
CLAMP_CEILING: float = 2.5
CLAMP_CLEARANCE: float = 0.1
CLAMP_LENGTH: float = 12.0
CLAMP_CRUSH_PAD: float = 0.15

# =============================================================================
# PART E – AERODYNAMIC BLOWER COWL  (phase3.scad)
# =============================================================================

COWL_TOTAL_SPAN: float = 340.0
COWL_HALF_SPAN: float = COWL_TOTAL_SPAN / 2.0          # 170.0 mm per half
COWL_WALL: float = 2.4

# Air-knife slit
SLIT_WIDTH: float = 1.5
SLIT_EXIT_Z: float = 20.0
SLIT_LAND_LEN: float = 10.0
JET_AIM_Y: float = 14.0
S45: float = math.sqrt(0.5)                             # sin/cos 45 deg

# Plenum
PLENUM_WIDTH: float = 22.0
PLENUM_TAPER_LEN: float = 18.0
PLENUM_TOP_Z: float = 42.0
PLENUM_BOX_LEN: float = 70.0
COWL_END_WALL: float = 4.0

# Split-joint interlocking
COLLAR_EXTRA_WALL: float = 1.6
COLLAR_LEN: float = 8.0
TONGUE_H: float = 3.0
TONGUE_D0: float = 1.4
TONGUE_D1: float = 2.6
GROOVE_D0: float = 1.3
GROOVE_D1: float = 2.7
GROOVE_DEPTH: float = TONGUE_H + 0.4

DOWEL_D: float = 4.0
DOWEL_TOLERANCE: float = 0.1
DOWEL_DEPTH: float = 10.0
DOWEL_BORE_D: float = DOWEL_D + DOWEL_TOLERANCE        # 4.1 mm

# 5015 blower duct/flange
DUCT_CENTRE_Y: float = 58.0
DUCT_ID: float = 17.0
DUCT_WALL: float = 3.0
DUCT_HEIGHT: float = 10.0
FLANGE_D: float = 40.0
FLANGE_THICKNESS: float = 4.0
FLANGE_BOLT_CIRCLE: float = 30.0
FLANGE_HOLE_D: float = 3.2
FLANGE_BOLT_ANGLES = [45.0, 135.0, 225.0, 315.0]

# Endplate mounting tabs
TAB_THICKNESS: float = 4.0
TAB_HOLE_D: float = 3.2
TAB_HOLE_POSITIONS = [(48.0, 15.0), (72.0, 15.0)]     # (Y, Z) on tab face

# =============================================================================
# ELECTRONICS CHASSIS TRAY  (phase2.scad)
# =============================================================================

TRAY_LENGTH: float = 320.0   # r10: widened from 150 so the electronics fit in strips either side of the wedge
TRAY_WIDTH: float = 95.0
TRAY_THICKNESS: float = 3.0
TRAY_CORNER_R: float = 3.0
TRAY_EDGE_MARGIN: float = 1.5

TRAY_BOLT_X: float = 48.0
TRAY_BOLT_TRAVEL: float = 4.0
TRAY_POCKET_W: float = 10.0
TRAY_POCKET_DEPTH: float = 1.8

STANDOFF_HEIGHT: float = 8.0
STANDOFF_OD: float = 6.4
STANDOFF_PILOT_D: float = 2.8
STANDOFF_PILOT_INTO: float = 2.0

# PCB_LAYOUT: (name, cx, cy, hole_px, hole_py, n_holes, outline_w, outline_h)
# r10 layout (tray-local, origin = tray centre, +X right, +Y front).  The solar wedge sits
# centred on X = 0 and flush with the rear edge (X +-55.8, Y -47.5 .. +46.5), so every
# board lives in one of the two strips beside it:
#   +X strip : ESP32 shield (rear)  with INA219 in front of it
#   -X strip : 2x18650 holder (outer end, not listed here: no standoffs), then a column of
#              L298N (rear) over the relay module (front)
PCB_LAYOUT = [
    ("ESP32_38PIN", 107.9, -13.0, 71.0, 57.0, 4, 81.0, 65.0),
    ("L298N",       -88.0, -22.75, 38.5, 38.5, 4, 43.5, 43.5),
    ("RELAY_1CH",   -88.0,  15.0, 44.0, 20.0, 4, 50.0, 26.0),
    ("INA219",      107.9,  32.75, 20.0, 17.0, 2, 25.5, 22.5),
]

NOTCH_W: float = 7.0
NOTCH_D: float = 6.0
ZIP_SLOT_W: float = 1.8
ZIP_SLOT_L: float = 4.2
ANCHOR_INSET: float = 4.0
ANCHOR_OFF: float = 8.0

# WIRE_EXITS: (edge, position_mm)  edge = "L"/"R"/"T"/"B"; position is along that edge, tray-local
# r10: the old L / B exits would now sit under the battery holder and the wedge, so they were moved
# to the only free edge zones (checked against every board, the battery, the wedge and the plate edge):
#   R  0     : right edge, beside the ESP32 shield (right motor / limit switch)
#   T  140   : front edge, +X strip, clear of the INA219
#   T  -88   : front edge, above the relay module (blower wiring)
#   T  -140  : front edge, beyond the battery holder (left motor)
# The rear (B) edge has no free zone: every board sits right against it, and the wedge covers the middle.
WIRE_EXITS = [
    ("R",   0.0),
    ("T", 140.0),
    ("T", -88.0),
    ("T", -140.0),
]

# =============================================================================
# ESP32 ADAPTER SLED (b123d_esp32_adapter_sled)
# =============================================================================
ESP32_SLED_BASE_L: float = 81.0         # Base plate length along X (mm)
ESP32_SLED_BASE_W: float = 65.0         # Base plate width along Y (mm)
ESP32_SLED_BASE_T: float = 2.5          # Base plate thickness (mm)
ESP32_SLED_HOLE_PX: float = 71.0        # Standoff hole pitch along X (mm)
ESP32_SLED_HOLE_PY: float = 57.0        # Standoff hole pitch along Y (mm)
ESP32_SLED_HOLE_D: float = 3.4          # M3 clearance hole diameter (mm)
ESP32_SLED_CORNER_R: float = 2.5        # Base plate corner fillet radius (mm)

ESP32_DEV_L: float = 55.0               # 38-pin ESP32 PCB length (mm)
ESP32_DEV_W: float = 28.0               # 38-pin ESP32 PCB width (mm)
ESP32_DEV_T: float = 1.6                # PCB thickness (mm)
ESP32_POCKET_TOL: float = 0.30          # Per-side clearance (mm)
ESP32_POCKET_L: float = 55.6            # Inner pocket length (mm)
ESP32_POCKET_W: float = 28.6            # Inner pocket width (mm)
ESP32_POCKET_RIM_H: float = 3.5         # Rim wall height above base plate (mm)
ESP32_POCKET_WALL_T: float = 2.0        # Rim wall thickness (mm)
ESP32_CHANNEL_H: float = 2.0            # Slide-in channel vertical clearance (mm)
ESP32_LIP_OVERHANG: float = 1.2         # Inward retention lip overhang (mm)

ESP32_SHELF_L: float = 3.8              # Supporting ledge under short ends (mm)
ESP32_CUTOUT_L: float = 48.0            # Underside pin access cutout length (mm)
ESP32_CUTOUT_W: float = 26.6            # Underside pin access cutout width (mm) (widened for 1.0" pin headers)
ESP32_SNAP_OVERHANG: float = 1.2        # Lip retention overhang (mm)

# =============================================================================
# SOLAR TILT WEDGE  (phase3.scad)
# =============================================================================

WEDGE_TILT: float = 25.0
PV_CELL_L: float = 70.0
PV_CELL_W: float = 70.0
PV_CELL_T: float = 3.0
PV_TOLERANCE: float = 0.4
PV_POCKET_L: float = PV_CELL_L + 2.0 * PV_TOLERANCE   # 70.8 mm
PV_POCKET_W: float = PV_CELL_W + 2.0 * PV_TOLERANCE   # 70.8 mm
PV_POCKET_DEPTH: float = 2.8
PV_LIP_T: float = 2.4
PV_LIP_H: float = PV_CELL_T - 0.2                      # 2.8 mm

WEDGE_CABLE_D: float = 8.0
WEDGE_BASE_T: float = 3.0
WEDGE_H_LOW: float = 6.0
WEDGE_BODY_MARGIN: float = 3.0
WEDGE_BASE_EXT: float = 10.0

BASE_HOLE_D: float = 3.4

_Ls = PV_POCKET_W + 2.0 * PV_LIP_T + 2.0 * WEDGE_BODY_MARGIN
WEDGE_SLOPE_RUN: float = _Ls * math.cos(math.radians(WEDGE_TILT))
WEDGE_SLOPE_RISE: float = _Ls * math.sin(math.radians(WEDGE_TILT))
WEDGE_BODY_L: float = PV_POCKET_L + 2.0 * (PV_LIP_T + 5.0 + WEDGE_BODY_MARGIN)
WEDGE_BASE_L: float = WEDGE_BODY_L + 2.0 * WEDGE_BASE_EXT
WEDGE_BASE_W: float = WEDGE_SLOPE_RUN + 2.0 * WEDGE_BASE_EXT

CLIP_T: float = 3.0
CLIP_OVERLAP: float = 5.0
CLIP_HOLE_D: float = 3.4

# Pad positions (along slope axis) for corner screw tabs
_pad_s: float = 10.0
_pad_w: float = 10.0
_pad_a: float = PV_POCKET_L / 2.0 + PV_LIP_T + _pad_s / 2.0
_pad_bs = [
    WEDGE_BODY_MARGIN + PV_LIP_T + _pad_w / 2.0,
    WEDGE_BODY_MARGIN + PV_LIP_T + PV_POCKET_W - _pad_w / 2.0,
]
WEDGE_PAD_S: float = _pad_s
WEDGE_PAD_W: float = _pad_w
WEDGE_PAD_A: float = _pad_a
WEDGE_PAD_BS = _pad_bs

# =============================================================================
# LIMIT SWITCH TRIP DOG  (phase2.scad)
# =============================================================================

SLOT_OPEN: float = 6.0
LIP_THICKNESS: float = 1.8
V_SLOT_RAIL_W: float = 20.0

M5_CLEAR_D: float = 5.5
M5_HEAD_D: float = 9.5
M5_HEAD_H: float = 2.7
M5_LEN: float = 8.0

DOG_BODY_W: float = 18.0
DOG_H_BASE: float = 5.0
DOG_RAMP_ANGLE: float = 30.0
DOG_RAMP_RISE: float = 4.0
DOG_PLATEAU_LEN: float = 8.0
DOG_TRAIL_ANGLE: float = 30.0
DOG_BOSS_LEN: float = 15.0
DOG_KEY_W: float = 5.8
DOG_KEY_D: float = 1.5
DOG_KEY_MARGIN: float = 2.0

DOG_RAMP_RUN: float = DOG_RAMP_RISE / math.tan(math.radians(DOG_RAMP_ANGLE))
DOG_TRAIL_RUN: float = DOG_RAMP_RISE / math.tan(math.radians(DOG_TRAIL_ANGLE))
DOG_H_CAM: float = DOG_H_BASE + DOG_RAMP_RISE
DOG_X_B: float = DOG_RAMP_RUN
DOG_X_C: float = DOG_X_B + DOG_PLATEAU_LEN
DOG_X_D: float = DOG_X_C + DOG_TRAIL_RUN
DOG_TOTAL_LEN: float = DOG_X_D + DOG_BOSS_LEN
DOG_HOLE_X: float = DOG_X_D + DOG_BOSS_LEN / 2.0

DOG_CBORE_D: float = M5_HEAD_D + 0.5
DOG_CBORE_DEPTH: float = M5_HEAD_H + 0.3
DOG_FLOOR_T: float = DOG_H_BASE - DOG_CBORE_DEPTH
DOG_ENGAGEMENT: float = M5_LEN - DOG_FLOOR_T - LIP_THICKNESS
DOG_RELIEF_LEN: float = M5_CLEAR_D + 1.0

# 2D cam profile (x-z plane: x along rail, z = rise)
DOG_PROFILE = [
    (0.0,           0.0),
    (DOG_TOTAL_LEN, 0.0),
    (DOG_TOTAL_LEN, DOG_H_BASE),
    (DOG_X_D,       DOG_H_BASE),
    (DOG_X_C,       DOG_H_CAM),
    (DOG_X_B,       DOG_H_CAM),
    (0.0,           DOG_H_BASE),
]

# =============================================================================
# ASSEMBLY / GLOBAL REFERENCE DATUMS
# =============================================================================

CROSSBEAM_LENGTH: float = 340.0
GLASS_THICKNESS: float = 3.2
GLASS_Z_BOTTOM: float = -GLASS_THICKNESS
GLASS_Z_TOP: float = 0.0

MIN_WALL_THICKNESS: float = 2.4
MIN_AIR_KNIFE_CLEARANCE: float = 1.0
