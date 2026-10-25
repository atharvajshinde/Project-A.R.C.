"""
PROJECT A.R.C. – Couplers Module (src/parts/couplers.py)
=========================================================
3D-printable drive hub / shaft couplers for gantry locomotion:
  - coupler_n20_vwheel: Bearingless direct-drive stepped hub connecting
    N20 gearmotor 3.0 mm D-shaft directly to Delrin Mini V-Wheel tire
    with MR105ZZ bearings removed for positive torque transmission.
"""

from __future__ import annotations
import math
import build123d as bd
from build123d import (
    BuildPart, BuildSketch,
    Cylinder, extrude,
    Plane, Locations, Location, Vector, Mode, Align,
    Circle, Rectangle,
)

_COUPLER_CACHE = None


def build_coupler_n20_vwheel() -> bd.Solid:
    """
    Build the 3D-printable N20 to Mini V-Wheel direct-drive stepped hub coupler (v2.0).
    
    Geometry:
      - Retention backing flange: Ø14.5 mm, 3.0 mm thick (X = 0 to 3.0 mm),
        seats flat against the Delrin wheel face.
      - Wheel engagement boss: Stepped cylinder:
          * Root step: Ø10.05 mm OD × 3.5 mm long (X = 3.0 to 6.5 mm),
            press-fits into the 10.0 mm bearing cavity of the Delrin wheel.
          * Tip step: Ø7.80 mm OD × 2.0 mm long (X = 6.5 to 8.5 mm),
            clears the internal Delrin center rib.
          * Axial relief hole in tip: Ø5.2 mm bore in tip.
      - N20 D-shaft bore: Ø3.25 mm (depth 9.0 mm), with D-flat at 2.70 mm
        from bottom of circle (FDM compensated for 3.0 mm shaft).
    """
    global _COUPLER_CACHE
    if _COUPLER_CACHE is not None:
        return _COUPLER_CACHE.moved(Location())

    flange_d = 14.5
    flange_t = 3.0
    root_d = 10.05
    root_len = 3.5
    tip_d = 7.80
    tip_len = 2.0
    relief_d = 5.2

    shaft_bore_d = 3.25
    shaft_bore_r = shaft_bore_d / 2.0  # 1.625 mm
    flat_h = 2.70                      # mm height from bottom of circle
    flat_coord = -shaft_bore_r + flat_h  # +1.075 mm
    bore_depth = 9.0

    with BuildPart() as bp:
        # 1. Backing flange (Ø14.5 × 3.0 mm)
        with BuildSketch(Plane.YZ):
            Circle(flange_d / 2.0)
        extrude(amount=flange_t)

        # 2. Root step (Ø10.05 × 3.5 mm) press-fitting into 10 mm Delrin cavity
        with BuildSketch(Plane.YZ.offset(flange_t)):
            Circle(root_d / 2.0)
        extrude(amount=root_len)

        # 3. Tip step (Ø7.80 × 2.0 mm) clearing internal Delrin rib
        with BuildSketch(Plane.YZ.offset(flange_t + root_len)):
            Circle(tip_d / 2.0)
        extrude(amount=tip_len)

        # 4. Axial relief hole in tip (Ø5.2 mm)
        with BuildSketch(Plane.YZ.offset(flange_t + root_len - 0.5)):
            Circle(relief_d / 2.0)
        extrude(amount=tip_len + 1.0, mode=Mode.SUBTRACT)

        # 5. N20 D-shaft bore (Ø3.25 mm, D-flat at 2.70 mm from bottom, depth 9.0 mm)
        with BuildSketch(Plane.YZ.offset(-0.5)):
            Circle(shaft_bore_r)
            # Truncate circle above flat_coord to form D-flat chord
            with Locations((0.0, flat_coord + 5.0)):
                Rectangle(10.0, 10.0, mode=Mode.SUBTRACT)
        extrude(amount=bore_depth + 1.0, mode=Mode.SUBTRACT)

    solid = bp.part
    _COUPLER_CACHE = solid
    return solid.moved(Location())

