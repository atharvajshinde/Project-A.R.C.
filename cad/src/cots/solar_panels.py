"""
PROJECT A.R.C. – COTS: Solar Panels & PV Telemetry Cells
=========================================================
B-Rep models for:
  - Mini 70×70×3 mm telemetry PV cell with contact tabs
  - Loom Solar 10W Polycrystalline Framed Solar Module (285×350×22 mm)
  - Baseline cleanable panel slab (324×580×3.2 mm)
"""

from __future__ import annotations
import build123d as bd
from build123d import (
    BuildPart, BuildSketch,
    Box, extrude,
    Plane, Locations, Location, Vector, Mode, Align,
    Rectangle, Circle,
)

from .dims import (
    MINI_PV_L, MINI_PV_W, MINI_PV_T, MINI_PV_TAB_W, MINI_PV_TAB_L,
    LOOM_SOLAR_10W_L, LOOM_SOLAR_10W_W, LOOM_SOLAR_10W_T,
    LOOM_SOLAR_10W_FRAME_LIP, LOOM_SOLAR_10W_GLASS_T,
    LOOM_SOLAR_10W_JBOX_L, LOOM_SOLAR_10W_JBOX_W, LOOM_SOLAR_10W_JBOX_H,
)

_MINI_PV_CACHE = None
_LOOM_10W_CACHE = None


def build_mini_pv_cell() -> bd.Solid:
    """
    Build the 70 × 70 × 3 mm mini telemetry PV cell with ribbon tabs.
    
    Coordinate frame:
      - Centred on (0, 0) in X-Y.
      - Underside at Z = 0, top face at Z = 3 mm.
      - Ribbon tabs extend from +Y edge for electrical connection.
    """
    global _MINI_PV_CACHE
    if _MINI_PV_CACHE is not None:
        return _MINI_PV_CACHE.moved(Location())

    w, l, t = MINI_PV_W, MINI_PV_L, MINI_PV_T
    tab_w, tab_l = MINI_PV_TAB_W, MINI_PV_TAB_L

    with BuildPart() as bp:
        # Main tempered glass/resin encapsulated cell body
        Box(w, l, t, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Two solder ribbon tabs on +Y edge
        for sx in (-15.0, 15.0):
            with Locations((sx, l / 2.0 + tab_l / 2.0, t - 0.2)):
                Box(tab_w, tab_l, 0.4, align=Align.CENTER)

        # Busbar silver contact relief traces on top face (+Z)
        for sx in (-15.0, 15.0):
            with Locations((sx, 0.0, t)):
                Box(1.2, l - 4.0, 0.2, align=(Align.CENTER, Align.CENTER, Align.MIN))

    solid = bp.part
    _MINI_PV_CACHE = solid
    return solid.moved(Location())


def build_loom_solar_10w(frame_depth: float = 25.0) -> bd.Solid:
    """
    Build the Loom Solar 10W Polycrystalline Solar Panel.
    
    Dimensions: 285 mm (width) × 350 mm (length) × 25 mm (frame depth).
    Coordinate frame:
      - Centred on (0, 0) in X-Y.
      - Active glass face at Z = 0 (top face).
      - Aluminium frame and junction box extend into -Z (downward).
    """
    w, l, h = LOOM_SOLAR_10W_W, LOOM_SOLAR_10W_L, frame_depth
    lip = LOOM_SOLAR_10W_FRAME_LIP
    glass_t = LOOM_SOLAR_10W_GLASS_T

    with BuildPart() as bp:
        # Outer aluminium frame perimeter
        with Locations((0.0, 0.0, -h)):
            Box(w, l, h, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Inner frame pocket (open from underside)
        with Locations((0.0, 0.0, -h - 0.1)):
            Box(w - 2.0 * lip, l - 2.0 * lip, h - glass_t + 0.1,
                align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

        # Front glass face active surface
        with Locations((0.0, 0.0, -glass_t)):
            Box(w - 4.0, l - 4.0, glass_t, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Rear IP65 junction box
        with Locations((0.0, l / 3.0, -h - LOOM_SOLAR_10W_JBOX_H)):
            Box(LOOM_SOLAR_10W_JBOX_W, LOOM_SOLAR_10W_JBOX_L, LOOM_SOLAR_10W_JBOX_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN))

    return bp.part


def build_framed_solar_panel(width: float = 285.0, length: float = 560.0, frame_depth: float = 25.0) -> bd.Solid:
    """
    Build a realistic framed solar panel testbed module.
    
    Dimensions: 285 mm (width) × 560 mm (length) × 25 mm (frame depth).
    Coordinate frame:
      - Centred at (0, 0) in X-Y.
      - Active glass face at Z = 0.
      - 25 mm anodised aluminium C-channel frame extending down to Z = -25 mm,
        resting flush on testbed mounting bracket shelves and anti-sag pedestals.
    """
    lip = 15.0
    glass_t = 3.2

    with BuildPart() as bp:
        # Outer aluminium frame perimeter
        with Locations((0.0, 0.0, -frame_depth)):
            Box(width, length, frame_depth, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Inner frame pocket (open from underside)
        with Locations((0.0, 0.0, -frame_depth - 0.1)):
            Box(width - 2.0 * lip, length - 2.0 * lip, frame_depth - glass_t + 0.1,
                align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

        # Front glass face active surface
        with Locations((0.0, 0.0, -glass_t)):
            Box(width - 4.0, length - 4.0, glass_t, align=(Align.CENTER, Align.CENTER, Align.MIN))

    return bp.part


def build_flat_panel_slab(width: float, length: float, thickness: float = 3.2) -> bd.Solid:
    """
    Build a flat solar panel substrate glass slab (baseline geometry).
    
    Coordinate frame:
      - Centred at (0, 0) in X-Y.
      - Glass face at Z = 0, slab extends to Z = -thickness.
    """
    with BuildPart() as bp:
        Box(width, length, thickness, align=(Align.CENTER, Align.CENTER, Align.MAX))
    return bp.part

