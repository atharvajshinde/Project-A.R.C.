"""
PROJECT A.R.C. – Electronics Chassis Tray
==========================================
Source: phase2.scad  ->  build123d B-Rep implementation.

Geometry
--------
  Plate centred at origin in X-Y plane.
  X = along 2020 crossbeam (TRAY_LENGTH span).
  Y = across beam (95 mm span).
  Z = normal to plate; +Z = up (standoffs point up).
  Plate underside = Z = 0, top face = Z = TRAY_THICKNESS.

Exported builders
-----------------
  build_chassis_tray()  -> Solid
"""

from __future__ import annotations
import math
import build123d as bd
from build123d import (
    BuildPart, BuildSketch,
    Plane, Axis, Mode, Align,
    extrude, fillet,
    Locations, Location,
    Box, Cylinder,
    Circle, Rectangle, RectangleRounded,
    SlotOverall,
    Solid, Part, Vector,
)
from .parameters import (
    EPS,
    TRAY_LENGTH, TRAY_WIDTH, TRAY_THICKNESS, TRAY_CORNER_R, TRAY_EDGE_MARGIN,
    TRAY_BOLT_X, TRAY_BOLT_TRAVEL, TRAY_POCKET_W, TRAY_POCKET_DEPTH,
    STANDOFF_HEIGHT, STANDOFF_OD, STANDOFF_PILOT_D, STANDOFF_PILOT_INTO,
    PCB_LAYOUT,
    NOTCH_W, NOTCH_D, ZIP_SLOT_W, ZIP_SLOT_L, ANCHOR_INSET, ANCHOR_OFF,
    WIRE_EXITS,
    M5_CLEAR_D,
    WEDGE_BASE_W, WEDGE_CABLE_D,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pcb_hole_positions(entry: tuple) -> list:
    """
    Compute standoff hole (x, y) positions for a PCB entry.
    entry = (name, cx, cy, hx, hy, n_holes, ow, oh)
    n_holes = 2 -> diagonal pair; 4 -> rectangle corners.
    """
    _, cx, cy, hx, hy, n_holes, _, _ = entry
    hx2, hy2 = hx / 2.0, hy / 2.0
    if n_holes == 2:
        return [(cx - hx2, cy - hy2), (cx + hx2, cy + hy2)]
    return [
        (cx - hx2, cy - hy2), (cx + hx2, cy - hy2),
        (cx + hx2, cy + hy2), (cx - hx2, cy + hy2),
    ]


def _validate_layout():
    """Raise if any standoff position exceeds the plate boundary."""
    hx = TRAY_LENGTH / 2.0
    hy = TRAY_WIDTH / 2.0
    for entry in PCB_LAYOUT:
        for (px, py) in _pcb_hole_positions(entry):
            assert abs(px) + STANDOFF_OD / 2.0 <= hx - TRAY_EDGE_MARGIN, \
                f"Standoff off plate (X): {entry[0]} at ({px:.1f}, {py:.1f})"
            assert abs(py) + STANDOFF_OD / 2.0 <= hy - TRAY_EDGE_MARGIN, \
                f"Standoff off plate (Y): {entry[0]} at ({px:.1f}, {py:.1f})"


def _wire_exit_cuts() -> list:
    """
    Return a list of bd.Solid objects representing all wire-exit notches
    and zip-tie slot cuts, ready to be subtracted from the tray.
    """
    cuts = []
    hy = TRAY_WIDTH / 2.0
    hx = TRAY_LENGTH / 2.0
    nd = NOTCH_D
    hw = NOTCH_W / 2.0
    ai = ANCHOR_INSET
    ao = ANCHOR_OFF
    sw = ZIP_SLOT_W
    sl = ZIP_SLOT_L
    depth = TRAY_THICKNESS + 2.0 * EPS
    z0 = -EPS

    for (edge, pos) in WIRE_EXITS:
        if edge == "B":
            # Notch from -Y edge inward (+Y)
            notch = Box(NOTCH_W, nd, depth,
                        align=(Align.CENTER, Align.MIN, Align.MIN))
            notch = notch.move(Location(Vector(pos, -hy, z0)))
            cuts.append(notch)
            for s in (+1.0, -1.0):
                slot = Box(sw, sl, depth,
                           align=(Align.CENTER, Align.CENTER, Align.MIN))
                slot = slot.move(Location(Vector(pos + s * ao, -hy + ai, z0)))
                cuts.append(slot)

        elif edge == "T":
            # Notch from +Y edge inward (-Y)
            notch = Box(NOTCH_W, nd, depth,
                        align=(Align.CENTER, Align.MAX, Align.MIN))
            notch = notch.move(Location(Vector(pos, hy, z0)))
            cuts.append(notch)
            for s in (+1.0, -1.0):
                slot = Box(sw, sl, depth,
                           align=(Align.CENTER, Align.CENTER, Align.MIN))
                slot = slot.move(Location(Vector(pos + s * ao, hy - ai, z0)))
                cuts.append(slot)

        elif edge == "L":
            # Notch from -X edge inward (+X)
            notch = Box(nd, NOTCH_W, depth,
                        align=(Align.MIN, Align.CENTER, Align.MIN))
            notch = notch.move(Location(Vector(-hx, pos, z0)))
            cuts.append(notch)
            for s in (+1.0, -1.0):
                slot = Box(sl, sw, depth,
                           align=(Align.CENTER, Align.CENTER, Align.MIN))
                slot = slot.move(Location(Vector(-hx + ai, pos + s * ao, z0)))
                cuts.append(slot)

        elif edge == "R":
            # Notch from +X edge inward (-X)
            notch = Box(nd, NOTCH_W, depth,
                        align=(Align.MAX, Align.CENTER, Align.MIN))
            notch = notch.move(Location(Vector(hx, pos, z0)))
            cuts.append(notch)
            for s in (+1.0, -1.0):
                slot = Box(sl, sw, depth,
                           align=(Align.CENTER, Align.CENTER, Align.MIN))
                slot = slot.move(Location(Vector(hx - ai, pos + s * ao, z0)))
                cuts.append(slot)

    return cuts


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_chassis_tray() -> bd.Solid:
    """
    Build the electronics chassis tray.

    Features
    --------
    - TRAY_LENGTH × TRAY_WIDTH × 3 mm PETG plate (320 × 95 mm in r10) with 3 mm corner fillets
    - Two M5 SlotOverall beam-attachment slots at ±48 mm
    - PCB standoff matrix: ESP32, L298N, Relay, INA219
    - Wire-exit notches + zip-tie anchor slots (WIRE_EXITS)
    - Ø cable hole under the solar wedge's wiring tunnel (PV cell wires drop through to the beam)
    """
    _validate_layout()

    lx = TRAY_LENGTH
    ly = TRAY_WIDTH
    lz = TRAY_THICKNESS

    # ---- Base plate with rounded corners ----
    with BuildPart() as base_bp:
        with BuildSketch(Plane.XY):
            RectangleRounded(lx, ly, TRAY_CORNER_R)
        extrude(amount=lz)
    result = base_bp.part

    # ---- PCB standoff columns ----
    for entry in PCB_LAYOUT:
        for (px, py) in _pcb_hole_positions(entry):
            with BuildPart() as st:
                with BuildSketch(Plane.XY.offset(lz - EPS)):
                    with Locations((px, py)):
                        Circle(STANDOFF_OD / 2.0)
                extrude(amount=STANDOFF_HEIGHT + EPS)
            result = result.fuse(st.part)

    # ---- Subtract pilot holes through standoffs and into plate ----
    for entry in PCB_LAYOUT:
        for (px, py) in _pcb_hole_positions(entry):
            with BuildPart() as ph:
                with BuildSketch(Plane.XY.offset(lz - STANDOFF_PILOT_INTO)):
                    with Locations((px, py)):
                        Circle(STANDOFF_PILOT_D / 2.0)
                extrude(amount=STANDOFF_PILOT_INTO + STANDOFF_HEIGHT + EPS)
            result = result.cut(ph.part)

    # ---- M5 beam attachment slots (SlotOverall = total length including caps) ----
    slot_total = M5_CLEAR_D + TRAY_BOLT_TRAVEL   # clearance dia + travel
    pocket_total = TRAY_POCKET_W + TRAY_BOLT_TRAVEL

    for sx in (+1.0, -1.0):
        cx = sx * TRAY_BOLT_X
        # Through-slot
        with BuildPart() as slot_cut:
            with BuildSketch(Plane.XY.offset(-EPS)):
                with Locations((cx, 0.0)):
                    SlotOverall(slot_total, M5_CLEAR_D)
            extrude(amount=lz + 2.0 * EPS)
        result = result.cut(slot_cut.part)

        # Recessed head pocket
        with BuildPart() as pocket_cut:
            with BuildSketch(Plane.XY.offset(lz - TRAY_POCKET_DEPTH)):
                with Locations((cx, 0.0)):
                    SlotOverall(pocket_total, TRAY_POCKET_W)
            extrude(amount=TRAY_POCKET_DEPTH + EPS)
        result = result.cut(pocket_cut.part)

    # ---- Cable hole under the wedge's wiring tunnel ----
    # The wedge sits centred on X = 0 and flush with the rear (-Y) edge of the plate, so the
    # bottom of its vertical bore lands at the middle of the wedge base.  Without a hole
    # here the PV cell wires would dead-end on the plate.
    cable_y = -TRAY_WIDTH / 2.0 + WEDGE_BASE_W / 2.0
    with BuildPart() as cable_cut:
        with BuildSketch(Plane.XY.offset(-EPS)):
            with Locations((0.0, cable_y)):
                Circle(WEDGE_CABLE_D / 2.0)
        extrude(amount=lz + 2.0 * EPS)
    result = result.cut(cable_cut.part)

    # ---- Wire exit notches + zip-tie slots ----
    for cut in _wire_exit_cuts():
        result = result.cut(cut)

    # ---- 2x18650 Battery Holder Perimeter Retention Lip (v2.0) ----
    # Footprint centered at X = -137.5, Y = -7.0, height 3.0 mm above plate top
    batt_cx = -137.5
    batt_cy = -7.0
    lip_inner_w = 42.0
    lip_inner_l = 78.0
    lip_wall = 2.0
    lip_h = 3.0
    with BuildPart() as batt_lip:
        with Locations((batt_cx, batt_cy, lz)):
            with BuildSketch(Plane.XY):
                RectangleRounded(lip_inner_w + 2.0 * lip_wall, lip_inner_l + 2.0 * lip_wall, 2.5)
                Rectangle(lip_inner_w, lip_inner_l, mode=Mode.SUBTRACT)
            extrude(amount=lip_h)
    result = result.fuse(batt_lip.part)

    # ---- 2 pairs of 4.0 mm x 2.0 mm battery zip-tie slots through tray base ----
    with BuildPart() as batt_slots:
        for sx in (-1.0, 1.0):
            slot_x = batt_cx + sx * (lip_inner_w / 2.0 + 1.5)
            for sy in (-20.0, 20.0):
                slot_y = batt_cy + sy
                with Locations((slot_x, slot_y, -EPS)):
                    with BuildSketch(Plane.XY):
                        Rectangle(2.0, 4.0)
                    extrude(amount=lz + 2.0 * EPS)
    result = result.cut(batt_slots.part)

    # ---- Integrated C-shaped wire routing clips along front and side edges (v2.0) ----
    clip_locs = [
        (-50.0, ly / 2.0 - 4.5),
        ( 50.0, ly / 2.0 - 4.5),
        (-lx / 2.0 + 6.0, 36.0),
        ( lx / 2.0 - 6.0,  0.0),
    ]
    with BuildPart() as wire_clips:
        for (cx, cy) in clip_locs:
            with Locations((cx, cy, lz)):
                with BuildSketch(Plane.XY):
                    RectangleRounded(8.0, 6.0, 1.0)
                    Rectangle(5.0, 3.5, mode=Mode.SUBTRACT)
                extrude(amount=5.0)
    result = result.fuse(wire_clips.part)

    return result
