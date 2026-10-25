# Project A.R.C. – Manufacturing Manifest
*Solar Panel Cleaning Robot — CAD-to-Print Reference*
*Generated from build123d parametric model | Units: mm | Material: PETG unless noted*

---

## Bill of Printed Parts

| # | Part Name | File | Material | Print Pose | Infill | Walls | Supports |
|---|-----------|------|----------|------------|--------|-------|----------|
| C | Carriage Endplate (×2) | `carriage_endplate.stl` | PETG Black | Flat (XZ face on bed) | 40 % gyroid | 4 | None |
| C | N20 Motor Clamp Saddle (×2) | `n20_motor_clamp.stl` | PETG Black | Upright (tunnel vertical) | 50 % gyroid | 4 | None |
| D | Roller End Plug (×2) | `roller_end_plug.stl` | PETG White | Flange-down | 40 % gyroid | 4 | None |
| E | Blower Cowl – Left Half | `blower_cowl_left.stl` | PETG Blue | Vertical (+X face up) | 35 % gyroid | 3 | None* |
| E | Blower Cowl – Right Half | `blower_cowl_right.stl` | PETG Blue | Vertical (+X face up) | 35 % gyroid | 3 | None* |
| — | Electronics Chassis Tray | `chassis_tray.stl` | PETG Grey | Flat (underside on bed) | 30 % grid | 3 | None |
| — | Solar Tilt Wedge | `solar_tilt_wedge.stl` | PETG Grey | Flat (base on bed) | 25 % gyroid | 3 | None |
| — | PV Corner Clamp Clip (×4) | `pv_clamp_clip.stl` | PETG Grey | Flat | 30 % grid | 3 | None |
| — | Limit Switch Trip Dog | `limit_switch_dog.stl` | PETG/ASA | 18 mm side face on bed | 40 % gyroid | 4 | None |

> *Cowl halves: the tongue/groove and dowel-boss chamfers are self-supporting at 45 °.
>  No support material required if printed with the joint face (X = 0) vertically oriented.

---

## Layer Settings

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Layer height | 0.20 mm | Best resolution for 3.2 mm and 5.5 mm features |
| First layer | 0.25 mm | Bed adhesion |
| Perimeter overlap | 20 % | PETG minimum for watertight walls |
| Extrusion width | 0.45 mm | 0.4 mm nozzle, slight over-extrusion for strength |
| Seam position | Rear (aligned) | Hidden inside bore or behind cowl |
| Bridge flow | 90 % | PETG bridging typical |
| Fan speed | 50–80 % | PETG inter-layer adhesion balance |

---

## Slicing Profiles by Part

### Carriage Endplate
- Print orientation: **flat**, 120 mm edge along X, 50 mm edge along Y.
- All holes (bearing pocket, V-wheel bores, crossbeam counterbores, motor holes) are vertical → no support.
- Bearing boss prints as an overhanging ring; fan at 80 % for bridge.
- First layer: 0.3 mm. Infill: gyroid 40 %.

### N20 Motor Clamp Saddle
- Print **upright** with the tunnel axis vertical so the 12 × 10 mm motor tunnel has clean, supported side walls.
- The ear cylinders are self-supporting (< 45 ° overhang from flat ears).
- Tolerances: tunnel adds 0.1 mm per side clearance; re-slice with 0 % horizontal expansion if printer is over-extrusion-prone.

### Roller End Plug
- Print **flange-down** so the critical press-fit section (36 mm OD) is built bottom-up with consistent layer bonding.
- Axle bore (4.2 mm) prints as a teardrop profile in Prusa Slicer; standard Cura users: enable "Avoid crossing perimeters."
- Post-process: light sanding of the 36 mm press-fit section with 220-grit if plug does not seat with hand pressure.

### Blower Cowl Halves (Left + Right)
- Print each half **vertically** with the flat joint face (X = 0) oriented upward.
- This makes the air-knife slit and plenum walls (all parallel to the build plate normal) perfectly perpendicular to layers = maximum pressure-tightness.
- The chamfered joint collar eliminates any overhangs.
- Slit width 1.5 mm: use 0.4 mm nozzle; do NOT use 0.6 mm nozzle (will bridge rather than print the slit).
- Minimum 3 perimeters = 3 × 0.45 = 1.35 mm ≈ 56 % of the 2.4 mm minimum wall. Add a 4th perimeter for the duct/flange sections.

### Electronics Chassis Tray
- Print **flat** (underside on bed). All holes and slots are vertical.
- Self-tapping M3 pilot bores (2.8 mm dia): print at 99 % flow; tap with M3 thread tap before assembly.
- Do NOT use heat-set inserts unless you toggle `use_heat_set_inserts = True` in the parameters (requires 4.0 mm pilot bores).

### Solar Tilt Wedge
- Print flat. Pilot holes for corner clips are at 90 ° to the slope face → verify 25 ° tilt does not create bridging issues.
- Cable bore (8 mm dia, vertical): prints clean without support.
- After printing, test-fit the PV cell in the pocket; if tight, lightly sand the 70.8 mm inner walls.

### PV Corner Clamp Clips (×4)
- Print flat. M3 hole prints as a 3.4 mm bore → use drill or M3 clearance reamer before assembly.

### Limit Switch Trip Dog
- Print on the **18 mm rail-face side** so the ramp profile is vertical (parallel to layers).
- This gives the 30 ° ramp a smooth surface finish and makes the 5.8 mm alignment key dimensionally accurate.
- Counterbore and M5 clearance hole are teardrop-shaped in the recommended orientation → no support needed.
- Material: ASA preferred for outdoor UV/heat resistance. PETG acceptable for indoor/shaded deployment.

---

## Bill of Hardware (Non-Printed)

| Item | Spec | Qty | Notes |
|------|------|-----|-------|
| Roller axle | EN31 / silver steel rod, Ø 4 mm × 390 mm | 1 | Precision-ground, h6 tolerance |
| Conduit | 1.25" UPVC electrical conduit, OD 41.2 mm | 1× 320 mm | Cut to length |
| Microfiber wrap | Auto Hub 800 GSM plush, finished OD 50 mm | 1 | Glue with contact cement |
| Bearing | 684ZZ miniature ball bearing (9 × 4 × 4 mm) | 2 | One per endplate |
| Mini V-wheel | OpenBuilds solid V-wheel (Ø 15.23 mm PD) | 4 | 2 per carriage side |
| 2020 crossbeam | Aluminium V-slot extrusion, 350 mm | 1 | |
| N20 gear motor | N20 12 V, 100–300 RPM (travel drive) | 2 | One per endplate |
| 5015 blower fan | 24 V radial blower, 50 × 15 mm | 1 | Bolt to flange with 4× M3×8 |
| Dowel pins | Ø 4 mm ground steel rod offcuts, 12 mm | 2 | Cut from axle scrap |
| M5 × 8 button head (ISO 7380) | Stainless A2 | 8 | Crossbeam + tray + dog |
| M5 roll-in T-nut | 2020 slot (6 mm) T-nut | 4 | Beam mounting |
| M3 × 6 self-tapping | Stainless | 16 | PCB standoff pilots |
| M3 × 8 SHCS | Stainless | 8 | Cowl-to-endplate, endplate-to-dog |
| M3 × 12 SHCS | Stainless | 4 | Blower flange |
| M3 hex nut | Standard DIN 934 | 2 | Captive in roller plug |
| M3 grub screw | M3 × 4 cup-point | 2 | Roller plug set-screw |
| ESP32 38-pin shield | Robu SKU 1738328 | 1 | |
| L298N H-bridge driver | Dual channel | 1 | |
| 5V relay module | 1-channel | 1 | |
| INA219 sensor | Current/power breakout | 1 | |

---

## Assembly Sequence

1. **Roller sub-assembly**: Press end plugs into conduit ends (hand-press + rubber mallet if needed). Insert axle through both plugs. Tighten M3 set-screws to clamp axle. Verify axle spins freely in both 684ZZ bearings.
2. **Carriage**: Press bearings into endplate pockets. Thread N20 motors into clamp saddles. Bolt saddles to endplates with M3 × 8. Attach V-wheels with M5 × 10 shoulder bolts (not included).
3. **Cowl assembly**: Mate left + right halves at X = 0 joint. Press 4 mm dowels into blind bores. Bolt halves to endplates with M3 × 8 at the 48 mm / 72 mm tab holes. Mount 5015 blower fan to flange.
4. **Gantry**: Mount both carriage assemblies on 2020 Y-rails. Slide 350 mm crossbeam through the X-bearings. Bolt tray to crossbeam top slot with M5 × 8 + T-nuts.
5. **Electronics**: Seat PCBs on standoffs, secure with M3 × 6 self-tapping screws. Route harness through wire-exit notches, secure with 3.6 mm zip ties.
6. **Solar wedge**: Mount to gantry frame with 4× M3 corner holes. Insert PV cell. Clip 4 corner clamps.
7. **Homing dog**: Clamp trip dog into Y-rail 6 mm slot. Adjust position until microswitch actuates cleanly at roller contact line.

---

## Quality Control Checklist

- [ ] Roller spins freely when axle clamped to endplate bearings
- [ ] Bearing ledge depth = 1.8 mm minimum (verify with depth micrometer)
- [ ] Cowl slit width = 1.5 mm ± 0.1 mm (gauge pin or feeler gauge)
- [ ] V-wheels roll without wobble (centre-to-centre = 35.23 mm)
- [ ] PCB standoffs torqued to 0.3 N·m (M3 self-tap, do not overtighten)
- [ ] Cowl joint tongue/groove mates with < 0.5 mm gap
- [ ] Trip dog actuates microswitch lever within 4 mm travel
- [ ] PV cell seats flush; 4 corner clips compress the top face

---

## Export Command Reference

```bash
# Full export (all parts, STL + STEP)
cd cad/
python export_all.py

# Single part
python export_all.py --parts roller_end_plug

# STL only with higher tolerance
python export_all.py --no-step --stl-tol 0.005

# Run test suite
python -m pytest tests/ -v
```
