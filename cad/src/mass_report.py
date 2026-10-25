"""
PROJECT A.R.C. – Mass & Centre of Gravity (CoG) Analysis
=========================================================
Computes physical mass and 3D Centre of Gravity for every component in the assembly.
Material density table:
  - PETG: 1.27 g/cm³
  - ASA: 1.07 g/cm³
  - Aluminium 6061/6063: 2.70 g/cm³
  - Steel (EN31 silver steel, A2 fasteners): 7.85 g/cm³
  - UPVC: 1.40 g/cm³
  - Delrin / POM: 1.41 g/cm³
  - Copper: 8.96 g/cm³
Verified/assumed board masses per procurement datasheets (docs/ASSUMPTIONS.md).
"""

from __future__ import annotations
from typing import Dict, Tuple, List
import build123d as bd
from build123d import Vector

from .cots.dims import (
    DENSITY_PETG, DENSITY_ASA, DENSITY_ALUMINIUM, DENSITY_STEEL,
    DENSITY_DELRIN, DENSITY_COPPER,
    ESP32_SHIELD_MASS_G, L298N_MASS_G, RELAY_MASS_G, INA219_MASS_G,
    CELL_18650_MASS_G, BATTERY_HOLDER_EMPTY_MASS_G,
    BLOWER_5015_MASS_G, N20_MASS_G, LIMIT_SW_MASS_G,
    SLEEVE_MASS_G, MINI_PV_MASS_G, LOOM_SOLAR_10W_MASS_G,
)

# UPVC density in g/cm³
DENSITY_UPVC = 1.40


def get_part_mass(name: str, shape: bd.Shape) -> float:
    """Compute physical mass in grams for a given part."""
    # Volume in cm³ (shape.volume is in mm³)
    vol_cm3 = float(shape.volume) / 1000.0

    if "esp32_adapter_sled" in name:
        return vol_cm3 * DENSITY_PETG
    if "cots_motor_driver_l298n" in name:
        return L298N_MASS_G
    if "cots_relay_module" in name:
        return RELAY_MASS_G
    if "cots_ina219" in name:
        return INA219_MASS_G
    if "cots_battery_2x18650" in name:
        return BATTERY_HOLDER_EMPTY_MASS_G + 2.0 * CELL_18650_MASS_G  # 102.0 g
    if "cots_blower_5015" in name:
        return BLOWER_5015_MASS_G
    if "cots_motor_n20" in name:
        return N20_MASS_G
    if "cots_motor_25ga370" in name:
        return 85.0   # # ASSUMED: 25GA370 gearmotor mass
    if "cots_limit_switch" in name:
        return LIMIT_SW_MASS_G
    if "cots_pv_mini_panel" in name:
        return MINI_PV_MASS_G
    if "cots_solar_panel" in name:
        return LOOM_SOLAR_10W_MASS_G
    if "roller_sleeve" in name:
        return SLEEVE_MASS_G

    # 2. Structural Stock & Extrusions
    if "cots_crossbeam" in name or "cots_guide_rail" in name:
        return vol_cm3 * DENSITY_ALUMINIUM
    if "roller_conduit" in name:
        return vol_cm3 * DENSITY_UPVC
    if "roller_axle" in name:
        return vol_cm3 * DENSITY_STEEL
    if "cots_vwheel" in name:
        return 4.5    # Mini V-wheel assembly with 2x MR105ZZ bearings

    # 3. Hardware & Fasteners
    if name.startswith("hw_"):
        if "bearing" in name:
            return 1.1   # 684ZZ bearing mass
        return vol_cm3 * DENSITY_STEEL

    # 4. Wiring Harness
    if name.startswith("wire_"):
        return vol_cm3 * DENSITY_COPPER * 0.45  # Copper core + lightweight PVC insulation

    # 5. 3D Printed Parts
    if "limit_dog" in name:
        return vol_cm3 * DENSITY_ASA
    # All other printed parts are PETG
    return vol_cm3 * DENSITY_PETG


STATIONARY_INFRASTRUCTURE = {
    "cots_solar_panel",
    "cots_guide_rail_left",
    "cots_guide_rail_right",
}


def compute_subassembly_mass_and_cog(parts: Dict[str, bd.Shape]) -> Tuple[float, Vector, List[Dict]]:
    """Compute mass, CoG, and breakdown for a dictionary of parts."""
    total_mass_g = 0.0
    weighted_pos = Vector(0.0, 0.0, 0.0)
    breakdown = []

    for name, shape in parts.items():
        mass_g = get_part_mass(name, shape)
        centroid = shape.center()
        total_mass_g += mass_g
        weighted_pos += centroid * mass_g
        breakdown.append({
            "name": name,
            "mass_g": mass_g,
            "cx": centroid.X,
            "cy": centroid.Y,
            "cz": centroid.Z,
        })

    cog = weighted_pos / total_mass_g if total_mass_g > 0 else Vector(0, 0, 0)
    return total_mass_g, cog, breakdown


def compute_assembly_mass_and_cog(parts: Dict[str, bd.Shape], include_stationary: bool = False) -> Tuple[float, Vector, List[Dict]]:
    """
    Compute mass and Center of Gravity vector (X, Y, Z).
    By default (include_stationary=False), computes the moving robot carriage mass and CoG
    (excluding stationary testbed infrastructure: cots_solar_panel and guide rails).
    """
    if include_stationary:
        return compute_subassembly_mass_and_cog(parts)
    carriage_parts = {k: v for k, v in parts.items() if k not in STATIONARY_INFRASTRUCTURE}
    return compute_subassembly_mass_and_cog(carriage_parts)


def print_mass_and_cog_report(parts: Dict[str, bd.Shape]) -> Tuple[float, Vector]:
    """Format and print the engineering mass & CoG analysis."""
    carriage_mass_g, carriage_cog, carriage_breakdown = compute_assembly_mass_and_cog(parts, include_stationary=False)
    testbed_parts = {k: v for k, v in parts.items() if k in STATIONARY_INFRASTRUCTURE}
    testbed_mass_g, testbed_cog, testbed_breakdown = compute_subassembly_mass_and_cog(testbed_parts)
    total_digital_twin_mass_g = carriage_mass_g + testbed_mass_g

    print("\n" + "=" * 80)
    print(" PROJECT A.R.C. – MASS & CENTRE OF GRAVITY (CoG) REPORT")
    print("=" * 80)
    print(" 1. MOVING ROBOT CARRIAGE (Chassis, Roller, Crossbeam, Electronics, Wiring)")
    print(f"    Carriage Mass: {carriage_mass_g:.1f} g ({carriage_mass_g / 1000.0:.3f} kg)")
    print(f"    Carriage CoG : X = {carriage_cog.X:+.2f} mm | Y = {carriage_cog.Y:+.2f} mm | Z = {carriage_cog.Z:+.2f} mm")
    print("-" * 80)

    # Carriage subsystems
    subsystems = {
        "3D Printed Chassis & Aerodynamics": lambda n: not (n.startswith("cots_") or n.startswith("hw_") or n.startswith("wire_") or n.startswith("roller_")),
        "Microfibre Roller Assembly": lambda n: n.startswith("roller_") or "roller_plug" in n,
        "Structural Aluminium Stock (2020 Crossbeam)": lambda n: "crossbeam" in n,
        "Electronics, Sensing & Actuators": lambda n: n.startswith("cots_") and n not in STATIONARY_INFRASTRUCTURE and "crossbeam" not in n,
        "Hardware, Bearings & Fasteners": lambda n: n.startswith("hw_"),
        "Electrical Wiring Harness": lambda n: n.startswith("wire_"),
    }

    for sub_name, filter_fn in subsystems.items():
        sub_parts = [p for p in carriage_breakdown if filter_fn(p["name"])]
        if not sub_parts:
            continue
        sub_mass = sum(p["mass_g"] for p in sub_parts)
        pct = (sub_mass / carriage_mass_g) * 100.0 if carriage_mass_g > 0 else 0
        print(f"\n  • {sub_name:<44} : {sub_mass:7.1f} g ({pct:4.1f} %)")
        for p in sub_parts[:6]:
            print(f"      - {p['name']:<28} : {p['mass_g']:6.1f} g  [CoG: {p['cx']:+6.1f}, {p['cy']:+6.1f}, {p['cz']:+6.1f}]")
        if len(sub_parts) > 6:
            print(f"      ... and {len(sub_parts) - 6} more components")

    if testbed_parts:
        print("\n" + "-" * 80)
        print(" 2. STATIONARY TESTBED INFRASTRUCTURE (Solar Panel Slab & Guide Rails)")
        print(f"    Infrastructure Mass: {testbed_mass_g:.1f} g ({testbed_mass_g / 1000.0:.3f} kg)")
        print(f"    Infrastructure CoG : X = {testbed_cog.X:+.2f} mm | Y = {testbed_cog.Y:+.2f} mm | Z = {testbed_cog.Z:+.2f} mm")
        for p in testbed_breakdown:
            print(f"      - {p['name']:<28} : {p['mass_g']:6.1f} g  [CoG: {p['cx']:+6.1f}, {p['cy']:+6.1f}, {p['cz']:+6.1f}]")

    print("\n" + "=" * 80)
    print(f" Total Digital Twin Combined Mass: {total_digital_twin_mass_g:.1f} g ({total_digital_twin_mass_g / 1000.0:.3f} kg)")
    print("=" * 80 + "\n")
    return carriage_mass_g, carriage_cog
