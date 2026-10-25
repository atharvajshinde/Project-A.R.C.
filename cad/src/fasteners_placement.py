"""
PROJECT A.R.C. – Fastener Placement & Hardware Integration
===========================================================
Places every fastener (screws, nuts, washers, dowel pins, set screws) at its
actual host hole position derived directly from parameters and part geometry.
"""

from __future__ import annotations
import math
from typing import Dict, Tuple
import build123d as bd
from build123d import Location, Vector, Plane

from .parameters import (
    ROLLER_CENTRE_Z, ROLLER_CONDUIT_LENGTH, COWL_HALF_SPAN,
    PLATE_THICKNESS, BEARING_BOSS_H, BEARING_CENTRE_Y, BEARING_CENTRE_Z,
    XB_PITCH, MOTOR_PITCH, WHEEL_CENTRE_Y, WHEEL_CC,
    TAB_HOLE_POSITIONS, FLANGE_BOLT_ANGLES, FLANGE_BOLT_CIRCLE,
    DUCT_CENTRE_Y, PLENUM_TOP_Z,
    TRAY_BOLT_X, PCB_LAYOUT,
    WEDGE_BASE_L, WEDGE_BASE_W, WEDGE_TILT,
    DOG_HOLE_X,
)
FAN_NECK_TOP_Z = PLENUM_TOP_Z
from .blower_cowl import _dowel_positions
from .cots.fasteners import (
    build_screw_shcs, build_screw_button, build_screw_selftap,
    build_nut_hex, build_washer,
    build_vwheel_axle_fastener, build_clamp_bolt_fastener,
)
from build123d import GeomType
from .cots.extrusion_2020 import build_m5_tnut
from .cots.vwheel import build_684zz_bearing
from .cots.roller_hardware import build_dowel_pin, build_m3_set_screw


def _find_cyl_face(solid: bd.Shape | None, r_target: float, y_target: float, z_target: float, tol: float = 1.5) -> Tuple[float, float, Tuple[float, float]]:
    """Query a solid for a cylindrical face matching the target radius and approximate Y, Z position."""
    if solid is not None:
        for f in solid.faces():
            if f.geom_type == GeomType.CYLINDER and getattr(f, "radius", None) is not None and abs(f.radius - r_target) < 0.25:
                bb = f.bounding_box()
                cy = 0.5 * (bb.min.Y + bb.max.Y)
                cz = 0.5 * (bb.min.Z + bb.max.Z)
                if abs(cy - y_target) < tol and abs(cz - z_target) < tol:
                    return cy, cz, (bb.min.X, bb.max.X)
    return y_target, z_target, (0.0, 0.0)


def build_all_fasteners(
    tray_bbox, wedge_bbox, clip_bboxes,
    endplate_left: bd.Shape | None = None,
    endplate_right: bd.Shape | None = None,
    solar_wedge: bd.Shape | None = None,
    limit_dog: bd.Shape | None = None,
) -> Dict[str, bd.Solid]:
    """
    Build and place all fasteners in the robot assembly.
    
    Fasteners are placed directly at the host hole axes queried from cylindrical
    faces of the placed parts.
    
    Returns a dictionary of parts with the prefix 'hw_'.
    """
    hw: Dict[str, bd.Solid] = {}
    zc = ROLLER_CENTRE_Z                     # 25.0 mm
    span = COWL_HALF_SPAN                    # 170.0 mm
    half_conduit = ROLLER_CONDUIT_LENGTH / 2.0  # 160.0 mm

    # =========================================================================
    # 1. ROLLER AXLE HARDWARE
    # =========================================================================
    # 684ZZ miniature bearings pressed into endplate bearing pockets (r=4.55 mm at Y=0, Z=zc)
    b = build_684zz_bearing()
    by_l, bz_l, _ = _find_cyl_face(endplate_left, 4.55, 0.0, zc)
    by_r, bz_r, _ = _find_cyl_face(endplate_right, 4.55, 0.0, zc)
    hw["hw_bearing_684zz_l"] = b.moved(Location((-172.0, by_l, bz_l), (0, 90, 0)))
    hw["hw_bearing_684zz_r"] = b.moved(Location((172.0, by_r, bz_r), (0, 90, 0)))

    # M3 captive hex nuts and grub screws inside external retaining collar of roller end plugs
    nut_m3 = build_nut_hex(3.0)
    grub_m3 = build_m3_set_screw()
    nut_l_x = -half_conduit - 3.75   # -163.75 mm in external collar
    nut_r_x = half_conduit + 3.75    # +163.75 mm in external collar
    hw["hw_nut_m3_roller_plug_l"] = nut_m3.moved(Location((nut_l_x, 5.0, zc), (90, 0, 0)))
    hw["hw_nut_m3_roller_plug_r"] = nut_m3.moved(Location((nut_r_x, 5.0, zc), (90, 0, 0)))
    hw["hw_grub_m3_roller_plug_l"] = grub_m3.moved(Location((nut_l_x, 10.0, zc), (90, 0, 0)))
    hw["hw_grub_m3_roller_plug_r"] = grub_m3.moved(Location((nut_r_x, 10.0, zc), (90, 0, 0)))

    # =========================================================================
    # 2. CARRIAGE ENDPLATE FASTENERS (Exact hole axes in placed endplates)
    # =========================================================================
    # 4 × M5 × 8 Button Head screws in endplate crossbeam holes (Y=0, Z=zc±18.0)
    m5_8 = build_screw_button(5.0, 8.0)
    for i, sign in enumerate((-1.0, 1.0)):
        z_nom = zc + sign * XB_PITCH / 2.0
        y_l, z_l, _ = _find_cyl_face(endplate_left, 2.6, 0.0, z_nom)
        y_r, z_r, _ = _find_cyl_face(endplate_right, 2.6, 0.0, z_nom)
        # Left plate (counterbore on X in [-172.6, -170.0], head sits at -170.0)
        hw[f"hw_screw_m5_crossbeam_l_{i}"] = m5_8.moved(
            Location((-170.0, y_l, z_l), (0, -90, 0))
        )
        # Right plate (counterbore on X in [170.0, 172.6], head sits at 170.0)
        hw[f"hw_screw_m5_crossbeam_r_{i}"] = m5_8.moved(
            Location((170.0, y_r, z_r), (0, 90, 0))
        )

    # 4 × M3 × 8 SHCS bolting N20 motor clamp saddles to endplates (Y=±11, Z=25)
    m3_8 = build_screw_shcs(3.0, 8.0)
    for sign in (-1.0, 1.0):
        y_nom = sign * MOTOR_PITCH / 2.0
        y_l, z_l, _ = _find_cyl_face(endplate_left, 1.6, y_nom, zc)
        hw[f"hw_screw_m3_motor_clamp_l_{int(sign > 0)}"] = m3_8.moved(
            Location((-176.0, y_l, z_l), (0, -90, 0))
        )
        # Right side: 25GA-370 split-clamp base flange bolts to endplate_right at Y = ±19.0 mm
        m3_clamp = build_clamp_bolt_fastener(3.0, 12.0)
        y_r, z_r, _ = _find_cyl_face(endplate_right, 1.6, sign * 19.0, zc)
        hw[f"hw_screw_m3_motor_clamp_r_{int(sign > 0)}"] = m3_clamp.moved(
            Location((180.0, y_r, z_r), (0, 90, 0))
        )

    # 6 × M5 × 25 Button Head screws in endplate V-wheel holes terminating with washers & nylon locknuts
    # Hole 0 (front): X = ±174.0, Y = -55.0, Z = -7.615
    # Hole 1 (rear):  X = ±174.0, Y = +55.0, Z = -7.615
    # Hole 2 (bottom clamp): X = ±174.0, Y = 0.0, Z = -42.845
    m5_vwheel = build_vwheel_axle_fastener(5.0, 11.0)
    for i, wy in enumerate((-55.0, 55.0)):
        hw[f"hw_screw_m5_vwheel_left_{i}"] = m5_vwheel.moved(
            Location((-174.0, wy, -7.615), (0, -90, 0))
        )
        hw[f"hw_screw_m5_vwheel_right_{i}"] = m5_vwheel.moved(
            Location((174.0, wy, -7.615), (0, 90, 0))
        )
    # 3rd bottom clamping wheel (with eccentric spacer)
    hw["hw_screw_m5_vwheel_left_2"] = m5_vwheel.moved(
        Location((-174.0, 0.0, -42.845), (0, -90, 0))
    )
    hw["hw_screw_m5_vwheel_right_2"] = m5_vwheel.moved(
        Location((174.0, 0.0, -42.845), (0, 90, 0))
    )

    # =========================================================================
    # 3. BLOWER COWL FASTENERS & DOWEL PINS
    # =========================================================================
    # 2 × Ø4 × 10 mm ground steel dowel pins at the cowl centre split seam
    dowel = build_dowel_pin()
    dowel_pts = _dowel_positions()
    for i, (dy, dz) in enumerate(dowel_pts):
        hw[f"hw_dowel_pin_cowl_{i}"] = dowel.moved(
            Location((0.0, dy - 2.64124, dz - 10.0), (0, 90, 0))
        )

    # 4 × M3 × 12 SHCS bolting 5015 blower ears to cowl flange
    m3_12 = build_screw_shcs(3.0, 12.0)
    bc_r = FLANGE_BOLT_CIRCLE / 2.0
    for i, ang in enumerate(FLANGE_BOLT_ANGLES):
        rad = math.radians(ang)
        bx = bc_r * math.cos(rad)
        by = DUCT_CENTRE_Y + bc_r * math.sin(rad)
        hw[f"hw_screw_m3_blower_{i}"] = m3_12.moved(
            Location((bx, by, FAN_NECK_TOP_Z))
        )

    # =========================================================================
    # 4. CHASSIS TRAY ATTACHMENT & PCB STANDOFF FASTENERS
    # =========================================================================
    # 2 × M5 × 8 Button Head screws + M5 T-Nuts clamping tray to crossbeam slot
    # Head sits on pocket floor (Z 56.2), T-nut top at Z 53.2 (center at Z 50.95)
    tnut = build_m5_tnut()
    for i, sx in enumerate((-TRAY_BOLT_X, TRAY_BOLT_X)):
        hw[f"hw_screw_m5_tray_{i}"] = m5_8.moved(Location((sx, -35.0, 56.2)))
        hw[f"hw_tnut_m5_tray_{i}"] = tnut.moved(Location((sx, -35.0, 50.95)))

    # 14 × M3 × 6 Self-Tapping Screws securing PCBs into standoffs
    m3_selftap = build_screw_selftap(3.0, 6.0)
    tcx = 0.5 * (tray_bbox.min.X + tray_bbox.max.X)
    tcy = 0.5 * (tray_bbox.min.Y + tray_bbox.max.Y)
    so_top_z = 62.0   # top of standoffs

    for entry in PCB_LAYOUT:
        name, cx, cy, hx, hy, n_holes, _, _ = entry
        hx2, hy2 = hx / 2.0, hy / 2.0
        coords = [(cx - hx2, cy - hy2), (cx + hx2, cy + hy2)] if n_holes == 2 else [
            (cx - hx2, cy - hy2), (cx + hx2, cy - hy2),
            (cx + hx2, cy + hy2), (cx - hx2, cy + hy2),
        ]
        for i, (px, py) in enumerate(coords):
            z_pos = (so_top_z + 2.5) if name == "ESP32_38PIN" else so_top_z
            hw[f"hw_screw_m3_{name.lower()}_{i}"] = m3_selftap.moved(
                Location((tcx + px, tcy + py, z_pos))
            )

    # =========================================================================
    # 5. SOLAR TILT WEDGE & PV CLIP FASTENERS
    # =========================================================================
    # 4 × M3 × 8 screws through wedge base corners into tray
    wb = wedge_bbox
    wcx = 0.5 * (wb.min.X + wb.max.X)
    wcy = 0.5 * (wb.min.Y + wb.max.Y)
    wedge_holes = []
    if solar_wedge is not None:
        for f in solar_wedge.faces():
            if f.geom_type == GeomType.CYLINDER and abs(f.radius - 1.7) < 0.2:
                f_bb = f.bounding_box()
                hx = 0.5 * (f_bb.min.X + f_bb.max.X)
                hy = 0.5 * (f_bb.min.Y + f_bb.max.Y)
                wedge_holes.append((hx, hy))
    if len(wedge_holes) == 4:
        for i, (bx, by) in enumerate(sorted(wedge_holes)):
            hw[f"hw_screw_m3_wedge_base_{i}"] = m3_8.moved(Location((bx, by, 61.0)))
    else:
        for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)]):
            bx = wcx + sx * (WEDGE_BASE_L / 2.0 - 5.0)
            by = wcy + sy * (WEDGE_BASE_W / 2.0 - 5.0)
            hw[f"hw_screw_m3_wedge_base_{i}"] = m3_8.moved(Location((bx, by, 61.0)))

    # 4 × M3 × 10 screws securing PV clamp clips on slope
    m3_10 = build_screw_shcs(3.0, 10.0)
    rad25 = math.radians(WEDGE_TILT)
    n_slope = Vector(0.0, math.sin(rad25), math.cos(rad25))

    boss_faces = []
    if solar_wedge is not None:
        boss_faces = [
            f for f in solar_wedge.faces()
            if f.geom_type == GeomType.PLANE and abs(f.area - 100.0) < 1.0
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
    for i, pt in enumerate(boss_pts):
        pos_clip_top = Vector(pt.X, pt.Y, pt.Z) + 3.0 * n_slope
        hw[f"hw_screw_m3_pv_clip_{i}"] = m3_10.moved(
            Location(pos_clip_top, (-WEDGE_TILT, 0.0, 0.0))
        )

    # =========================================================================
    # 6. LIMIT SWITCH TRIP DOG FASTENER
    # =========================================================================
    # 1 × M5 × 8 Button Head screw + M5 T-Nut clamping dog to rail
    # Dog counterbore floor at Z -13.2; T-nut inside rail slot (top at Z -17.0, center at Z -19.25)
    dog_hole_x = 173.0
    dog_hole_y = -34.072
    if limit_dog is not None:
        for f in limit_dog.faces():
            if f.geom_type == GeomType.CYLINDER and abs(f.radius - 2.75) < 0.2:
                f_bb = f.bounding_box()
                dog_hole_x = 0.5 * (f_bb.min.X + f_bb.max.X)
                dog_hole_y = 0.5 * (f_bb.min.Y + f_bb.max.Y)
                break
    hw["hw_screw_m5_dog"] = m5_8.moved(Location((dog_hole_x, dog_hole_y, -13.2)))
    hw["hw_tnut_m5_dog"] = tnut.moved(Location((dog_hole_x, dog_hole_y, -19.25)))

    return hw
