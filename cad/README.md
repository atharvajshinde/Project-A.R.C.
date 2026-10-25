# Project A.R.C. – build123d Digital Twin & CAD Package

This directory contains the complete parametric CAD digital twin of **Project A.R.C.**
(Autonomous Solar-Panel Cleaning Robot), developed with `build123d` (OpenCASCADE Python B-Rep kernel).

---

## 1. Directory Structure

```text
cad/
├── src/
│   ├── parameters.py            # Single source of truth for printed chassis parameters (mm, deg)
│   ├── assembly.py              # Master assembly builder, detail switch, validation suite, exports
│   ├── chassis_tray.py          # Electronics tray with PCB standoffs, wire channels & cable hole
│   ├── carriage_endplate.py     # Left/right carriage endplates & N20 motor clamp saddle
│   ├── roller_assembly.py       # UPVC core conduit, end plugs, EN31 axle & microfibre sleeve
│   ├── blower_cowl.py           # Split dual-chamber air-knife cowl halves (left/right)
│   ├── solar_tilt_wedge.py      # 25-degree tilted solar telemetry wedge & PV clamp clips
│   ├── limit_switch_dog.py      # Cam trip dog for rail limit switch
│   ├── fasteners_placement.py   # Stack-up fastener placement engine (56 fasteners)
│   ├── wiring.py                # Swept 3D wire harness router (16 nets, min bend >= 6 mm)
│   ├── mass_report.py           # Material density table, mass breakdown & CoG solver
│   ├── bom.py                   # Automatic bill of materials extractor (CSV exporter)
│   └── cots/                    # COTS bought-parts library
│       ├── dims.py              # Sourcing dimensions, suppliers, SKUs & datasheet links
│       ├── extrusion_2020.py    # 2020 T-slot crossbeam & V-slot guide rails + M5 T-nuts
│       ├── vwheel.py            # Mini V-wheels with 684ZZ bearings & spacers
│       ├── electronics.py       # ESP32 38-pin shield, L298N driver, relay, INA219, 18650 holder
│       ├── motors.py            # N20 micro metal gearmotor & ONPOW roller limit switch
│       ├── blower_5015.py       # 5015 centrifugal blower with volute scroll & mounting ears
│       ├── solar_panels.py      # Loom Solar 10W framed module & 70x70 mini PV telemetry cell
│       ├── roller_hardware.py   # Microfibre sleeve, dowel pins, set screws
│       └── fasteners.py         # Parametric DIN 912, ISO 7380, DIN 934, washers
├── tests/                       # Complete pytest unit and integration test suite
├── exports/                     # Generated CAD artifacts (STEP, GLB, STL, BOM)
│   ├── step/
│   │   ├── arc_full_assembly.step        # Baseline envelope STEP (33 components)
│   │   ├── arc_full_assembly_full.step   # Full-detail digital twin STEP (108 components)
│   │   └── arc_exploded.step             # Exploded view STEP
│   ├── glb/
│   │   ├── arc_full.glb                  # Full-detail 3D GLB for Web / IDE viewing
│   │   └── arc_exploded.glb              # Exploded view 3D GLB
│   ├── stl/
│   │   └── b123d_<part>.stl              # STL meshes for all 9 3D-printed parts
│   └── bom.csv                           # Dynamic Bill of Materials (count from model)
└── scripts/
    └── exploded.py                       # Exploded-view generator with directional group offsets
```

---

## 2. Environment Setup

The package requires Python 3.14 with `build123d` installed in the project root venv:
```bash
# From the cad/ directory:
source ../.venv/bin/activate.fish   # (or source ../.venv/bin/activate in bash/zsh)
```

> **IMPORTANT**: Always execute commands from inside the `cad/` directory so that `src`
> resolves to `cad/src/` rather than the firmware directory.

---

## 3. Running the Digital Twin

### A. Default Baseline Build (Simple Envelope Mode)
Runs the lightweight envelope model in ~10 seconds. Verifies all baseline geometric checks
and exports `exports/step/arc_full_assembly.step`:
```bash
python -m src.assembly
```

### B. Full-Detail Recreation Build
Builds every COTS bought part realistically, places all 56 fasteners at exact host hole coordinates,
routes the 16-net swept 3D wire harness through tray exits, runs extended kinematic and clearance
validations, computes total mass and CoG, and exports full STEP, GLB, STLs, and BOM:
```bash
python -m src.assembly --detail full
```

#### Optional CLI Flags:
- `--motor {n20, 25ga370}`: Selects the drive motor variant (defaults to `n20` matching the clamp).
- `--no-cots`: Excludes bought hardware components from the build.

### C. Exploded Assembly View
Generates exploded assemblies with hierarchical subsystem offsets:
```bash
python scripts/exploded.py full
```

### D. Running Test Suite
Execute the pytest regression suite:
```bash
python -m pytest tests/ -v
```

---

## 4. Documentation References

- `docs/BASELINE.md`: Initial digital twin component volumes, timings, and metrics.
- `docs/FULL_RECREATION_PLAN.md`: Phase-by-phase architectural blueprint.
- `docs/ASSUMPTIONS.md`: Catalog of all unverified dimensions marked `# ASSUMED` with rationale.
- `docs/OPEN_QUESTIONS.md`: Known physical/procurement discrepancies tracked with CAD vs notes.
- `docs/MEASURE_ME.md`: Printable caliper measurement sheet for validating physical parts upon arrival.
