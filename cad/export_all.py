"""
PROJECT A.R.C. – Batch Export Pipeline
=======================================
Builds every part and exports:
  - exports/stl/<name>.stl   (watertight FDM mesh, 0.01 mm linear deflection)
  - exports/step/<name>.step (lossless OpenCASCADE STEP solid)

Run headlessly (no Qt/VTK required):
    python export_all.py

Optional arguments:
    --parts    Comma-separated part names to export (default: all)
    --stl-tol  STL linear deflection tolerance in mm (default: 0.01)
    --no-stl   Skip STL export
    --no-step  Skip STEP export
"""

from __future__ import annotations
import sys
import time
import argparse
import traceback
from pathlib import Path

# ---- resolve project root so imports work regardless of cwd ----
_THIS = Path(__file__).resolve()
_ROOT = _THIS.parent
sys.path.insert(0, str(_ROOT))

from build123d import export_step, export_stl
import build123d as bd

from src.parameters import EPS
from src.carriage_endplate import build_carriage_endplate, build_n20_motor_clamp
from src.parts.clamp import build_25ga_motor_clamp
from src.parts.sled import build_esp32_adapter_sled
from src.roller_assembly import build_roller_end_plug, build_roller_conduit, build_roller_axle
from src.blower_cowl import build_blower_cowl_half
from src.parts.blower import build_blower_cowl_mount
from src.chassis_tray import build_chassis_tray
from src.solar_tilt_wedge import build_solar_tilt_wedge, build_pv_clamp_clip
from src.limit_switch_dog import build_limit_switch_dog
from src.parts.couplers import build_coupler_n20_vwheel
from src.parts.testbed import (
    build_testbed_rail_riser_foot,
    build_testbed_rail_panel_bracket,
    build_testbed_panel_pedestal,
)


# ---------------------------------------------------------------------------
# Part registry
# ---------------------------------------------------------------------------

PARTS: dict = {
    # name -> builder callable
    "carriage_endplate":         build_carriage_endplate,
    "endplate_right":            lambda: build_carriage_endplate(side="right", integrated_mounts=True),
    "endplate_left":             lambda: build_carriage_endplate(side="left", integrated_mounts=True),
    "n20_motor_clamp":           build_n20_motor_clamp,
    "motor_clamp_25ga":          build_25ga_motor_clamp,
    "esp32_adapter_sled":        build_esp32_adapter_sled,
    "coupler_n20_vwheel":        build_coupler_n20_vwheel,
    "roller_end_plug":           build_roller_end_plug,
    "roller_conduit":            build_roller_conduit,
    "roller_axle":               build_roller_axle,
    "blower_cowl_left":          lambda: build_blower_cowl_half("left"),
    "blower_cowl_right":         lambda: build_blower_cowl_half("right"),
    "blower_cowl_mount":         build_blower_cowl_mount,
    "chassis_tray":              build_chassis_tray,
    "solar_tilt_wedge":          build_solar_tilt_wedge,
    "pv_clamp_clip":             build_pv_clamp_clip,
    "limit_switch_dog":          build_limit_switch_dog,
    "testbed_rail_riser_foot":   build_testbed_rail_riser_foot,
    "testbed_rail_panel_bracket": build_testbed_rail_panel_bracket,
    "testbed_panel_pedestal":    build_testbed_panel_pedestal,
}


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def _ensure_dirs():
    stl_dir = _ROOT / "exports" / "stl"
    step_dir = _ROOT / "exports" / "step"
    stl_dir.mkdir(parents=True, exist_ok=True)
    step_dir.mkdir(parents=True, exist_ok=True)
    return stl_dir, step_dir


def _export_part(
    name: str,
    solid: bd.Solid,
    stl_dir: Path,
    step_dir: Path,
    stl_tol: float,
    do_stl: bool,
    do_step: bool,
) -> bool:
    """Export a single solid to STL and/or STEP. Returns True if all succeeded."""
    ok = True
    if do_stl:
        stl_path = stl_dir / f"{name}.stl"
        try:
            export_stl(solid, str(stl_path), tolerance=stl_tol)
            print(f"  [STL] {stl_path.relative_to(_ROOT)}")
        except Exception:
            print(f"  [STL ERROR] {name}: {traceback.format_exc(limit=1)}")
            ok = False

    if do_step:
        step_path = step_dir / f"{name}.step"
        try:
            export_step(solid, str(step_path))
            print(f"  [STEP] {step_path.relative_to(_ROOT)}")
        except Exception:
            print(f"  [STEP ERROR] {name}: {traceback.format_exc(limit=1)}")
            ok = False

    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Project A.R.C. – Batch CAD Export Pipeline"
    )
    parser.add_argument(
        "--parts", default=None,
        help="Comma-separated list of part names (default: all)"
    )
    parser.add_argument(
        "--stl-tol", type=float, default=0.01,
        help="STL linear deflection tolerance in mm (default: 0.01)"
    )
    parser.add_argument("--no-stl",  action="store_true", help="Skip STL export")
    parser.add_argument("--no-step", action="store_true", help="Skip STEP export")
    args = parser.parse_args()

    # Resolve which parts to build
    if args.parts:
        requested = [p.strip() for p in args.parts.split(",")]
        unknown = [p for p in requested if p not in PARTS]
        if unknown:
            print(f"ERROR: Unknown part names: {unknown}")
            print(f"Valid names: {list(PARTS.keys())}")
            sys.exit(1)
        build_queue = {k: PARTS[k] for k in requested}
    else:
        build_queue = PARTS

    do_stl = not args.no_stl
    do_step = not args.no_step
    stl_tol = args.stl_tol

    stl_dir, step_dir = _ensure_dirs()

    print(f"\n{'=' * 60}")
    print(f"  PROJECT A.R.C. – Build & Export Pipeline")
    print(f"  Parts to process : {len(build_queue)}")
    print(f"  STL tolerance    : {stl_tol} mm  (export: {do_stl})")
    print(f"  STEP export      : {do_step}")
    print(f"{'=' * 60}\n")

    failures = []
    total_t0 = time.perf_counter()

    for name, builder in build_queue.items():
        print(f"\n[BUILD] {name} ...")
        t0 = time.perf_counter()
        try:
            solid = builder()
            dt = time.perf_counter() - t0
            bb = solid.bounding_box()
            vol = solid.volume
            print(f"  -> built in {dt:.1f}s | volume = {vol:.1f} mm3 | "
                  f"bbox = {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm")
        except Exception:
            dt = time.perf_counter() - t0
            print(f"  [BUILD ERROR] {name} (after {dt:.1f}s):\n{traceback.format_exc()}")
            failures.append(name)
            continue

        ok = _export_part(name, solid, stl_dir, step_dir, stl_tol, do_stl, do_step)
        if not ok:
            failures.append(name)

    total_dt = time.perf_counter() - total_t0
    print(f"\n{'=' * 60}")
    print(f"  Total time: {total_dt:.1f}s")
    if failures:
        print(f"  FAILED parts ({len(failures)}): {failures}")
        sys.exit(1)
    else:
        print(f"  All {len(build_queue)} parts exported successfully.")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
