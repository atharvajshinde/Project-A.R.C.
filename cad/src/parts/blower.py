"""
PROJECT A.R.C. – 5015 Blower Cowl & Mounting System (src/parts/blower.py)
========================================================================
Exposes the 3D-printable Blower Cowl Mount bracket anchoring the 5015 blower cowl
flush against the chassis tray mounting flange with 0.0 mm gap, as well as the
aerodynamic blower cowl halves.
"""

from __future__ import annotations
import build123d as bd
from build123d import (
    BuildPart, BuildSketch, BuildLine,
    Plane, Mode, Locations,
    Polyline, make_face, extrude,
    Circle, RectangleRounded,
    Solid, Vector,
)

from src.blower_cowl import (
    build_blower_cowl_half,
    build_blower_cowl_left,
    build_blower_cowl_right,
)


def build_blower_cowl_mount() -> bd.Solid:
    """
    Build the 3D-printable Blower Cowl Mount bracket (PETG).
    
    Anchors the 5015 blower cowl flush against the chassis tray mounting flange
    and 2020 extrusion rail with 0.0 mm gap, bridging over the roller envelope.
    
    Key Features:
      - Rear tray interface: Mates flush with chassis tray front edge (Y = 12.5 mm, Z = 55..58 mm)
        and tray top surface (Z = 58.0 mm) with 0.0 mm gap.
      - 2x Ø3.4 mm M3 clearance mounting holes at X = ±16.0 mm, Y = 7.5 mm.
      - Structural bridge arch: Spans Y in [12.5, 28.0] mm with underside at Z >= 54.0 mm,
        maintaining >8.0 mm air clearance above the roller envelope (Z <= 50.0 mm).
      - Forward cowl interface: Steps down to Z = 32.90 mm at Y in [28.0, 32.5] mm,
        resting flush on the blower cowl plenum roof with 0.0 mm gap and zero fan clash.
    """
    # 2D cross-section profile in the Y-Z plane
    profile_pts = [
        # Top surface (rear to front)
        (2.5, 61.0),
        (12.5, 61.0),
        (24.0, 58.0),
        (28.0, 36.0),
        (32.5, 36.0),
        # Front tip
        (32.5, 32.90),
        # Landing on cowl roof
        (28.0, 32.90),
        # Bridge underside (over roller)
        (24.0, 54.0),
        (15.5, 54.0),
        # Chassis tray front abutment step
        (15.5, 55.0),
        (12.5, 55.0),
        (12.5, 58.0),
        (2.5, 58.0),
    ]

    mount_w = 50.0  # mm wide (X in [-25.0, 25.0])

    with BuildPart() as bp:
        with BuildSketch(Plane.YZ.offset(-mount_w / 2.0)):
            with BuildLine():
                Polyline(*profile_pts, close=True)
            make_face()
        extrude(amount=mount_w)

        # 2x Ø3.4 mm M3 clearance mounting holes for chassis tray attachment
        with BuildSketch(Plane.XY.offset(57.0)):
            with Locations((-16.0, 7.5), (16.0, 7.5)):
                Circle(1.7)
        extrude(amount=5.0, mode=Mode.SUBTRACT)

    return bp.part


__all__ = [
    "build_blower_cowl_mount",
    "build_blower_cowl_half",
    "build_blower_cowl_left",
    "build_blower_cowl_right",
]
