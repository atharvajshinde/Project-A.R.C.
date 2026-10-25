"""
PROJECT A.R.C. – Exploded View Assembly Exporter
=================================================
Generates an exploded 3D model of Project A.R.C. by translating functional
subsystems outward along principal axes (X, Y, Z).
Exports to:
  - exports/step/arc_exploded.step
  - exports/glb/arc_exploded.glb
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "cad"))

import build123d as bd
from build123d import Location, Vector, Compound, export_step, export_gltf
from src.assembly import build_arc_assembly


def build_exploded_assembly(detail: str = "full") -> Compound:
    """
    Build the exploded digital twin with hierarchical subsystem offsets.
    """
    print(f"Building Project A.R.C. Exploded View (detail={detail})...")
    asm = build_arc_assembly(include_cots=True, detail=detail)
    parts = asm.parts

    exploded_parts = []

    # Exploded distance offsets (mm)
    DZ_RAILS = -60.0
    DY_ROLLER = -80.0
    DX_CARRIAGE = 90.0
    DY_COWL = 100.0
    DZ_FAN = 70.0
    DZ_TRAY = 50.0
    DZ_ELEC = 95.0
    DZ_WEDGE = 150.0
    DZ_PV = 210.0

    for name, solid in parts.items():
        shift = Vector(0, 0, 0)

        # 1. Guide Rails & Wheels (downward in -Z)
        if "guide_rail" in name or "vwheel" in name:
            shift = Vector(0, 0, DZ_RAILS)

        # 2. Roller Subassembly (forward in -Y)
        elif "roller_" in name or "nut_m3_roller" in name or "grub_m3_roller" in name:
            dx = 0.0
            if "plug_left" in name:
                dx = -40.0
            elif "plug_right" in name:
                dx = 40.0
            elif "axle" in name:
                dx = 0.0
            shift = Vector(dx, DY_ROLLER, 0.0)

        # 3. Left Carriage Endplate, Motor Clamp & Motor (outward in -X)
        elif "_left" in name and ("endplate" in name or "motor_clamp" in name or "motor_n20" in name or "crossbeam_l" in name):
            shift = Vector(-DX_CARRIAGE, 0, 0)

        # 4. Right Carriage Endplate, Motor Clamp & Motor (outward in +X)
        elif "_right" in name and ("endplate" in name or "motor_clamp" in name or "motor_n20" in name or "crossbeam_r" in name):
            shift = Vector(DX_CARRIAGE, 0, 0)

        # 5. Blower Cowl (forward in +Y)
        elif "cowl" in name or "dowel_pin" in name:
            dx = -15.0 if "left" in name else (15.0 if "right" in name else 0.0)
            shift = Vector(dx, DY_COWL, 0)

        # 6. Blower Fan (upward from cowl in +Z)
        elif "blower" in name:
            shift = Vector(0, DY_COWL, DZ_FAN)

        # 7. Chassis Tray (upward in +Z)
        elif "chassis_tray" in name or "tray" in name or "crossbeam" in name:
            shift = Vector(0, 0, DZ_TRAY)

        # 8. Electronics on Tray (further upward in +Z)
        elif any(e in name for e in ("esp32", "l298n", "relay", "ina219", "battery", "wire_")):
            shift = Vector(0, 0, DZ_ELEC)

        # 9. Solar Telemetry Wedge (further upward in +Z)
        elif "wedge" in name:
            shift = Vector(0, 0, DZ_WEDGE)

        # 10. Mini PV Cell & Clips (highest exploded tier in +Z)
        elif "pv_mini" in name or "pv_clip" in name:
            shift = Vector(0, 0, DZ_PV)

        # 11. Limit Switch & Dog
        elif "dog" in name or "limit_switch" in name or "limit" in name:
            shift = Vector(DX_CARRIAGE / 2.0, 0, DZ_RAILS / 2.0)

        moved_part = solid.moved(Location(shift))
        moved_part.label = f"exploded_{name}"
        exploded_parts.append(moved_part)

    master = Compound(children=exploded_parts, label="ARC_exploded_view")
    return master


def export_exploded(detail: str = "full"):
    compound = build_exploded_assembly(detail=detail)
    out_dir = _PROJECT_ROOT / "cad" / "exports"
    step_path = out_dir / "step" / "arc_exploded.step"
    glb_path = out_dir / "glb" / "arc_exploded.glb"

    os.makedirs(step_path.parent, exist_ok=True)
    os.makedirs(glb_path.parent, exist_ok=True)

    export_step(compound, str(step_path))
    print(f"Exported Exploded STEP: {step_path}")

    export_gltf(compound, str(glb_path), binary=True, linear_deflection=0.05, angular_deflection=0.2)
    print(f"Exported Exploded GLB:  {glb_path}")


if __name__ == "__main__":
    detail_arg = sys.argv[1] if len(sys.argv) > 1 else "full"
    export_exploded(detail=detail_arg)
