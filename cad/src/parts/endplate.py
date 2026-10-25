"""
PROJECT A.R.C. – Carriage Endplate Module (src/parts/endplate.py)
=================================================================
3D-printable PETG Carriage Endplates (Left & Right) – v2.0 Architecture:
  - Wide-stance 110.0 mm wheelbase (Y = -55.0 mm front, Y = +55.0 mm rear) to prevent gantry racking.
  - Main plate expanded to 136.0 mm (Y) × 50.0 mm (Z) × 4.0 mm (X).
  - 3-wheel pinching system: Lower triangular extension lobe centered at Y = 0.0 mm extending
    down to Z = -52.0 mm (global) / Z = -77.3 mm (local) with Ø7.15 mm through-bore for OpenBuilds
    eccentric spacer boss at Z = -42.845 mm (global) / Z = -68.145 mm (local).
  - Top passive idler wheel: Rear top lobe at Y = +55.0 mm with Ø5.3 mm through-hole at Z = -7.615 mm (global).
  - Front driven locomotion drive: Fully enclosed 4-sided rectangular N20 motor box sleeve at front
    V-wheel (Y = -55.0 mm, Z = -7.615 mm global) with 12.3 × 10.3 mm internal cross-section,
    18.0 mm depth, Ø11.0 mm shaft/coupler clearance through-bore in endplate wall, horizontal
    3.5 × 2.0 mm zip-tie pass-through slot, and M3 top set-screw hole.
  - Drop-in roller bearing slot on endplate_left: Vertical U-shaped slot opening upward with an M3
    retaining washer hole above it so the assembled 326 mm roller can be dropped in from above AFTER
    both endplates are bolted to the 2020 crossbeam.
  - Standard circular 684ZZ bearing pocket on endplate_right for 25GA-370 gearmotor mounting.
  - Integrated limit switch mounting tab on leading bottom edge of endplate_right (2x M3 holes @ 9.5 mm pitch).
  - Crossbeam mounts: 2x M5 clearance holes with flat counterbores on the outer face at Y = 0, Z = ±18.0 mm.
"""

from __future__ import annotations
import math
import build123d as bd
from build123d import (
    BuildPart, BuildSketch,
    Cylinder, Box, extrude,
    Plane, Locations, Location, Vector, Mode, Align,
    Rectangle, Circle, Polygon, RectangleRounded,
)

from src.parameters import (
    EPS,
    PLATE_LENGTH, PLATE_HEIGHT, PLATE_THICKNESS, PLATE_CORNER_R,
    BRG_POCKET_D, BRG_POCKET_DEPTH, BRG_THROUGH_D,
    BEARING_BOSS_D, BEARING_BOSS_H,
    BEARING_CENTRE_Y, BEARING_CENTRE_Z,
    ROLLER_CENTRE_Z,
    WHEEL_CC, WHEEL_HOLE_D, WHEEL_CENTRE_Y,
    WHEELBASE_Y, WHEEL_FRONT_Y, WHEEL_REAR_Y, WHEEL_BOTTOM_Y,
    WHEEL_TOP_Z, WHEEL_BOTTOM_Z, WHEEL_ECCENTRIC_BORE_D, WHEEL_PASSIVE_BORE_D,
    XB_CLEAR_D, XB_CBORE_D, XB_CBORE_DEPTH, XB_PITCH,
    MOTOR_HOLE_D, MOTOR_PITCH,
)


def build_carriage_endplate(side: str = "left", integrated_mounts: bool = False) -> bd.Solid:
    """
    PETG carriage endplate (v2.0).
    Plate in the Y-Z plane, thickness along X.
    Inner face at X = 0 (bearing boss side).
    Outer face at X = PLATE_THICKNESS (V-wheel counterbore and N20 cradle side).

    Parameters:
      - side: "left" or "right" (clean true structural mirror across Y-Z plane).
      - integrated_mounts: If True, integrates wide-stance 3-wheel mounts, lower triangular
        lobe with Ø7.15 mm eccentric bore, N20 closed sleeve, drop-in slot (left), and limit switch tab (right).
        If False, generates baseline Phase 1 geometry for test compatibility.
    """
    pl = PLATE_LENGTH        # 136.0 mm (Y)
    ph = PLATE_HEIGHT        # 50.0 mm (Z)
    pt = PLATE_THICKNESS     # 4.0 mm (X)
    cr = PLATE_CORNER_R      # 4.0 mm
    zc = ROLLER_CENTRE_Z     # 25.3 mm

    z_top_wheel = WHEEL_TOP_Z - zc       # -7.615 - 25.3 = -32.915 mm local
    z_bot_wheel = WHEEL_BOTTOM_Z - zc    # -42.845 - 25.3 = -68.145 mm local
    z_bot_tip = -52.0 - zc               # -77.3 mm local
    y_front = WHEEL_FRONT_Y              # -55.0 mm
    y_rear = WHEEL_REAR_Y                # +55.0 mm

    with BuildPart() as bp:
        # 1. Main plate body (Z in [-25, 25], Y in [-68, 68], X in [0, pt])
        with BuildSketch(Plane.YZ):
            RectangleRounded(pl, ph, cr)
        extrude(amount=pt)

        # 2. X-axis crossbeam M5 counterbored bolt holes (Y=0, Z=±XB_PITCH/2)
        for sign in (+1.0, -1.0):
            with Locations((0.0, 0.0, sign * XB_PITCH / 2.0)):
                with BuildSketch(Plane.YZ.offset(-EPS)):
                    Circle(XB_CLEAR_D / 2.0)
                extrude(amount=pt + 2.0 * EPS, mode=Mode.SUBTRACT)
                with BuildSketch(Plane.YZ.offset(pt)):
                    Circle(XB_CBORE_D / 2.0)
                extrude(amount=-XB_CBORE_DEPTH, mode=Mode.SUBTRACT)

        # 3. Standard endplate V-wheel holes (only for baseline Phase 1 when integrated_mounts=False)
        if not integrated_mounts:
            with Locations((0.0, WHEEL_CENTRE_Y, -WHEEL_CC / 2.0)):
                with BuildSketch(Plane.YZ.offset(-EPS)):
                    Circle(5.3 / 2.0)
                extrude(amount=pt + 2.0 * EPS, mode=Mode.SUBTRACT)

        # 4. Roller axis bearing features
        if integrated_mounts and side == "left":
            # Left endplate has a vertical U-shaped drop-in slot opening upward
            with BuildSketch(Plane.YZ.offset(-BEARING_BOSS_H)):
                Circle(BEARING_BOSS_D / 2.0)
            extrude(amount=BEARING_BOSS_H + EPS)

            # Outer face 684ZZ bearing pocket U-slot (width 9.1 mm, depth 4.2 mm from outer face)
            with BuildSketch(Plane.YZ.offset(pt)):
                with Locations((0.0, 0.0)):
                    Circle(BRG_POCKET_D / 2.0)
                with Locations((0.0, ph / 4.0 + 5.0)):
                    Rectangle(BRG_POCKET_D, ph / 2.0 + 10.0)
            extrude(amount=-BRG_POCKET_DEPTH, mode=Mode.SUBTRACT)

            # Through shaft clearance slot (width 6.0 mm, all the way to top edge)
            with BuildSketch(Plane.YZ.offset(-BEARING_BOSS_H - EPS)):
                with Locations((0.0, 0.0)):
                    Circle(BRG_THROUGH_D / 2.0)
                with Locations((0.0, ph / 4.0 + 5.0)):
                    Rectangle(BRG_THROUGH_D, ph / 2.0 + 10.0)
            extrude(amount=pt + BEARING_BOSS_H + 2.0 * EPS, mode=Mode.SUBTRACT)

            # M3 retaining washer screw hole above the bearing pocket at Z = 8.0 mm
            with BuildSketch(Plane.YZ.offset(pt)):
                with Locations((0.0, 8.0)):
                    Circle(3.0 / 2.0)
            extrude(amount=-pt, mode=Mode.SUBTRACT)

            # 2x M3 clamp mounting holes for N20 saddle clamp (Y = ±11.0 mm)
            with BuildSketch(Plane.YZ.offset(-BEARING_BOSS_H - EPS)):
                with Locations((-MOTOR_PITCH / 2.0, 0.0), (MOTOR_PITCH / 2.0, 0.0)):
                    Circle(1.7)
            extrude(amount=pt + BEARING_BOSS_H + 2.0 * EPS, mode=Mode.SUBTRACT)

        else:
            # Standard circular 684ZZ bearing pocket on outer face and boss on inner face
            with BuildSketch(Plane.YZ.offset(-BEARING_BOSS_H)):
                Circle(BEARING_BOSS_D / 2.0)
            extrude(amount=BEARING_BOSS_H + EPS)
            with BuildSketch(Plane.YZ.offset(pt)):
                Circle(BRG_POCKET_D / 2.0)
            extrude(amount=-BRG_POCKET_DEPTH, mode=Mode.SUBTRACT)
            with BuildSketch(Plane.YZ.offset(-BEARING_BOSS_H - EPS)):
                Circle(BRG_THROUGH_D / 2.0)
                # 2x M3 clamp mounting holes for N20 saddle clamp (Y = ±11.0 mm, pitch 22 mm)
                with Locations((-MOTOR_PITCH / 2.0, 0.0), (MOTOR_PITCH / 2.0, 0.0)):
                    Circle(1.7)
                # 2x M3 clamp mounting holes for 25GA split clamp (Y = ±19.0 mm, pitch 38 mm)
                with Locations((-19.0, 0.0), (19.0, 0.0)):
                    Circle(1.7)
            extrude(amount=pt + BEARING_BOSS_H + 2.0 * EPS, mode=Mode.SUBTRACT)

        # 5. Integrated 3-wheel mounts & N20 sleeve
        if integrated_mounts:
            # 5a. Top mounting lobes at front (y_front = -55.0) and rear (y_rear = +55.0)
            with BuildSketch(Plane.YZ):
                with Locations((y_front, -29.915), (y_rear, -29.915)):
                    RectangleRounded(32.0, 22.0, 3.0)
            extrude(amount=pt)

            # 5b. Rear passive idler V-wheel M5 through-hole (Ø5.3 mm)
            with BuildSketch(Plane.YZ.offset(-EPS)):
                with Locations((y_rear, z_top_wheel)):
                    Circle(5.3 / 2.0)
            extrude(amount=pt + 2.0 * EPS, mode=Mode.SUBTRACT)

            # 5c. Lower triangular 3rd bottom clamping V-wheel extension lobe at Y = 0.0
            # Stepped outward via bridge arm above rail (Z in [-38.0, -25.0]) to clear 2020 rail outer face (X_local >= 13.2)
            with BuildSketch(Plane.YZ.offset(pt)):
                with Locations((0.0, -31.5)):
                    Rectangle(44.0, 13.0)
            extrude(amount=13.2 - pt + EPS)

            # Outer triangular lobe at X_local in [13.2, 17.2] (clears rail outer face X=183.0 by 0.2 mm)
            with BuildSketch(Plane.YZ.offset(13.2)):
                Polygon([
                    (-22.0, -25.0),
                    (-12.0, z_bot_wheel),
                    (-6.0, z_bot_tip),
                    (6.0, z_bot_tip),
                    (12.0, z_bot_wheel),
                    (22.0, -25.0),
                ])
            extrude(amount=4.0)

            # 5d. Bottom eccentric spacer through-bore (Ø7.15 mm) at (Y = 0.0, Z = z_bot_wheel) in outer lobe
            with BuildSketch(Plane.YZ.offset(13.2 - EPS)):
                with Locations((0.0, z_bot_wheel)):
                    Circle(7.15 / 2.0)
            extrude(amount=4.0 + 2.0 * EPS, mode=Mode.SUBTRACT)

            # 5e. Fully enclosed 4-sided N20 motor box sleeve outer solid (depth 18.0 mm from outer face)
            pocket_w = 12.3
            pocket_h = 10.3
            sleeve_wall = 3.0
            floor_t = 2.2
            sleeve_depth = 18.0
            sleeve_outer_w = pocket_w + 2.0 * sleeve_wall
            sleeve_outer_h = pocket_h + sleeve_wall + floor_t
            sleeve_z_center = z_top_wheel + (sleeve_wall - floor_t) / 2.0

            with BuildSketch(Plane.YZ.offset(pt)):
                with Locations((y_front, sleeve_z_center)):
                    RectangleRounded(sleeve_outer_w, sleeve_outer_h, 2.0)
            extrude(amount=sleeve_depth)

            # 5f. Concentric circular through-hole (Ø11.0 mm) through endplate wall for shaft & coupler hub
            with BuildSketch(Plane.YZ.offset(-EPS)):
                with Locations((y_front, z_top_wheel)):
                    Circle(11.0 / 2.0)
            extrude(amount=pt + 2.0 * EPS, mode=Mode.SUBTRACT)

            # 5g. Internal pocket cavity: 12.3 mm wide x 10.3 mm tall x 18.0 mm depth
            with BuildSketch(Plane.YZ.offset(pt)):
                with Locations((y_front, z_top_wheel)):
                    Rectangle(pocket_w, pocket_h)
            extrude(amount=sleeve_depth + 1.0, mode=Mode.SUBTRACT)

            # 5h. Circular relief for round motor can at outer entrance of sleeve
            with BuildSketch(Plane.YZ.offset(pt + 15.0)):
                with Locations((y_front, z_top_wheel)):
                    Circle(12.3 / 2.0)
            extrude(amount=3.0 + 1.0, mode=Mode.SUBTRACT)

            # 5i. Horizontal zip-tie slot (3.5 mm wide x 2.0 mm tall) through side walls
            ziptie_x = pt + 15.0
            ziptie_z = z_top_wheel + pocket_h / 2.0 - 0.5
            with Locations((ziptie_x, y_front, ziptie_z)):
                Box(3.5, sleeve_outer_w + 4.0, 2.0, align=Align.CENTER, mode=Mode.SUBTRACT)

            # 5j. M3 set-screw hole on top ceiling for positive motor clamping
            screw_x = pt + 7.5
            with Locations((screw_x, y_front, z_top_wheel + pocket_h / 2.0)):
                Cylinder(radius=3.0 / 2.0, height=sleeve_wall + 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

            # 5k. Integrated Limit Switch Mount Tab on leading bottom edge of endplate_right
            if side == "right":
                tab_len = 18.0
                tab_h = 16.0
                tab_y_center = -68.0 - tab_len / 2.0  # -77.0 mm
                tab_z_center = -17.0
                with BuildSketch(Plane.YZ):
                    with Locations((tab_y_center, tab_z_center)):
                        RectangleRounded(tab_len, tab_h, 2.5)
                extrude(amount=pt)

                # 2x M3 mounting through-holes spaced at 9.5 mm pitch (pitch centered)
                with BuildSketch(Plane.YZ.offset(-EPS)):
                    with Locations((tab_y_center - 9.5 / 2.0, tab_z_center), (tab_y_center + 9.5 / 2.0, tab_z_center)):
                        Circle(3.4 / 2.0)
                extrude(amount=pt + 2.0 * EPS, mode=Mode.SUBTRACT)

        else:
            # Baseline Phase 1 motor holes when integrated_mounts=False
            for sign in (+1.0, -1.0):
                with BuildPart() as mh:
                    with BuildSketch(Plane.YZ.offset(-EPS)):
                        with Locations((sign * MOTOR_PITCH / 2.0, 0.0)):
                            Circle(MOTOR_HOLE_D / 2.0)
                    extrude(amount=pt + 2.0 * EPS)
                bp.part = bp.part.cut(mh.part)

    solid = bp.part
    if side == "left":
        # Left endplate has features pointing outward (-X) and bearing boss inward (+X)
        return solid.mirror(Plane.YZ)
    return solid


__all__ = ["build_carriage_endplate"]
