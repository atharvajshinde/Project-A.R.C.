"""
PROJECT A.R.C. – Bill of Materials (BOM) Generator
===================================================
Dynamically generates the engineering Bill of Materials from the assembly parts
structure and exports to exports/bom.csv.
"""

from __future__ import annotations
import csv
import os
from typing import Dict, List
import build123d as bd

# Master catalog of part specifications, materials, and sourcing
_CATALOG = {
    "endplate": {
        "item": "Carriage Endplate (v2.0 3-Wheel)",
        "category": "Printed",
        "material": "PETG Black",
        "dimensions": "136 × 102 × 24.0 mm (110 mm wheelbase, 3rd bottom wheel lobe, N20 sleeve)",
        "supplier": "Internal 3D Print",
        "link": "manufacturing_manifest.md # Part C",
    },
    "motor_clamp": {
        "item": "N20 Motor Clamp Saddle",
        "category": "Printed",
        "material": "PETG Black",
        "dimensions": "34 × 12 × 12.7 mm",
        "supplier": "Internal 3D Print",
        "link": "manufacturing_manifest.md # Part C",
    },
    "coupler_n20_vwheel": {
        "item": "N20 to Mini V-Wheel Stepped Hub Coupler",
        "category": "Printed",
        "material": "PETG Black",
        "dimensions": "Ø14.5 × 8.5 mm (Ø10.05/Ø7.80 mm stepped hub, 3.25 mm D-bore)",
        "supplier": "Internal 3D Print",
        "link": "manufacturing_manifest.md # Coupler",
    },
    "roller_plug": {
        "item": "Roller End Plug (v2.0 External Collar)",
        "category": "Printed",
        "material": "PETG White",
        "dimensions": "Ø40 × 27.5 mm (7.5 mm external collar, M3 set-screw/nut, Ø36 mm stem)",
        "supplier": "Internal 3D Print",
        "link": "manufacturing_manifest.md # Part D",
    },
    "cowl_left": {
        "item": "Blower Cowl (Left Half)",
        "category": "Printed",
        "material": "PETG Blue",
        "dimensions": "90 × 78.6 × 35.4 mm (span 170 mm half)",
        "supplier": "Internal 3D Print",
        "link": "manufacturing_manifest.md # Part E",
    },
    "cowl_right": {
        "item": "Blower Cowl (Right Half)",
        "category": "Printed",
        "material": "PETG Blue",
        "dimensions": "90 × 78.6 × 35.4 mm (span 170 mm half)",
        "supplier": "Internal 3D Print",
        "link": "manufacturing_manifest.md # Part E",
    },
    "chassis_tray": {
        "item": "Electronics Chassis Tray",
        "category": "Printed",
        "material": "PETG Grey",
        "dimensions": "320 × 95 × 3.0 mm",
        "supplier": "Internal 3D Print",
        "link": "manufacturing_manifest.md",
    },
    "solar_wedge": {
        "item": "Solar Telemetry Tilt Wedge",
        "category": "Printed",
        "material": "PETG Grey",
        "dimensions": "111.6 × 94.0 × 41.8 mm (25° tilt)",
        "supplier": "Internal 3D Print",
        "link": "manufacturing_manifest.md",
    },
    "pv_clip": {
        "item": "PV Corner Clamp Clip",
        "category": "Printed",
        "material": "PETG Grey",
        "dimensions": "20.4 × 10.0 × 3.0 mm",
        "supplier": "Internal 3D Print",
        "link": "manufacturing_manifest.md",
    },
    "limit_dog": {
        "item": "Limit Switch Trip Dog",
        "category": "Printed",
        "material": "PETG/ASA",
        "dimensions": "36.9 × 18.0 × 10.5 mm",
        "supplier": "Internal 3D Print",
        "link": "manufacturing_manifest.md",
    },
    "esp32_adapter_sled": {
        "item": "ESP32 38-Pin Adapter Sled / Mounting Cradle",
        "category": "Printed",
        "material": "PETG Grey",
        "dimensions": "81.0 × 65.0 × 6.0 mm (71×57 mm M3 holes)",
        "supplier": "Internal 3D Print",
        "link": "manufacturing_manifest.md # Part SLED",
    },
    "cots_guide_rail": {
        "item": "2020 V-Slot Guide Rail",
        "category": "Bought",
        "material": "Aluminium 6063-T5",
        "dimensions": "20 × 20 × 600.0 mm",
        "supplier": "OpenBuilds / Local Sourcing",
        "link": "https://openbuildspartstore.com/v-slot-20x20-linear-rail/",
    },
    "cots_crossbeam": {
        "item": "2020 V-Slot Gantry Crossbeam",
        "category": "Bought",
        "material": "Aluminium 6063-T5",
        "dimensions": "20 × 20 × 340.0 mm",
        "supplier": "OpenBuilds / Local Sourcing",
        "link": "https://openbuildspartstore.com/v-slot-20x20-linear-rail/",
    },
    "roller_conduit": {
        "item": "UPVC Roller Conduit Core",
        "category": "Bought",
        "material": "1.25\" UPVC Conduit",
        "dimensions": "OD 41.2 × ID 36.0 × 320.0 mm",
        "supplier": "Local Electrical Supplier",
        "link": "Local Hardware (Thane/Mumbai)",
    },
    "roller_sleeve": {
        "item": "Plush Microfibre Roller Sleeve",
        "category": "Bought",
        "material": "800 GSM Microfiber",
        "dimensions": "OD 50.0 × ID 41.2 × 320.0 mm",
        "supplier": "Auto Hub / Amazon",
        "link": "https://www.amazon.in/dp/B08XYZ1234",
    },
    "roller_axle": {
        "item": "Continuous Roller Drive Axle",
        "category": "Bought",
        "material": "EN31 / Silver Steel",
        "dimensions": "Ø 4.0 × 390.0 mm Ground Rod (h6)",
        "supplier": "Precision Steel Supplier",
        "link": "Local Precision Metal Stock",
    },
    "cots_vwheel": {
        "item": "OpenBuilds Mini V-Wheel Kit",
        "category": "Bought",
        "material": "Delrin / POM",
        "dimensions": "OD 15.23 × W 8.8 mm (MR105ZZ)",
        "supplier": "OpenBuilds / Robu.in",
        "link": "https://openbuildspartstore.com/mini-v-wheel-kit/",
    },
    "hw_bearing_684zz": {
        "item": "684ZZ Miniature Ball Bearing",
        "category": "Bought",
        "material": "Chrome Steel GCr15",
        "dimensions": "ID 4.0 × OD 9.0 × W 4.0 mm",
        "supplier": "Robu.in / NMB",
        "link": "https://www.nmbtc.com/bearings/part-numbers/684ZZ",
    },
    "cots_blower_5015": {
        "item": "24V 5015 Radial Centrifugal Blower",
        "category": "Bought",
        "material": "PBT Thermoplastic",
        "dimensions": "50 × 50 × 15.0 mm (Flange BC 30mm)",
        "supplier": "Robu.in / Amazon",
        "link": "https://robu.in/product/5015-radial-blower-fan/",
    },
    "cots_motor_n20": {
        "item": "N20 Micro Metal Gear Motor (6V/12V)",
        "category": "Bought",
        "material": "Brass & Alloy Steel",
        "dimensions": "12 × 10 × 15 mm Gearbox, Ø3mm D-Shaft",
        "supplier": "Robu.in SKU 75800",
        "link": "https://robu.in/product/n20-6v-300-rpm-micro-metal-gear-motor/",
    },
    "cots_motor_25ga370": {
        "item": "25GA-370 DC Geared Motor",
        "category": "Bought",
        "material": "Alloy Steel",
        "dimensions": "Ø 25.0 × 45.0 mm, Ø4mm Shaft",
        "supplier": "Robu.in",
        "link": "https://robu.in/product/25ga-370-dc-gear-motor/",
    },
    "cots_motor_driver_l298n": {
        "item": "L298N 2A Dual H-Bridge Motor Driver",
        "category": "Bought",
        "material": "FR4 / Aluminium",
        "dimensions": "43.5 × 43.5 × 26.0 mm (38.5×38.5 mm holes)",
        "supplier": "Robu.in SKU 43821",
        "link": "https://robu.in/product/l298n-2a-dual-motor-driver-module/",
    },
    "cots_relay_module": {
        "item": "1-Channel 5V Relay Module (SRD)",
        "category": "Bought",
        "material": "FR4 / Plastic",
        "dimensions": "50.0 × 26.0 × 17.0 mm (44×20 mm holes)",
        "supplier": "Robu.in SKU R260153",
        "link": "https://robu.in/product/1-channel-isolated-5v-relay-module/",
    },
    "cots_ina219": {
        "item": "INA219 I2C Current/Power Sensor Breakout",
        "category": "Bought",
        "material": "FR4",
        "dimensions": "25.5 × 22.5 × 12.0 mm (20×17 mm holes)",
        "supplier": "Robu.in SKU 421237",
        "link": "https://robu.in/product/ina219-i2c-bi-directional-current-power-sensor-module/",
    },
    "cots_battery_2x18650": {
        "item": "2S 18650 Holder + 2× BAK 18650 Cells",
        "category": "Bought",
        "material": "Moulded ABS / Li-ion",
        "dimensions": "41.0 × 77.0 × 20.0 mm (2× 2600mAh)",
        "supplier": "Robu.in SKU 223415 / 1225174",
        "link": "https://robu.in/product/2-slot-18650-battery-holder-case-with-leads/",
    },
    "cots_solar_panel": {
        "item": "Plain Display Glass Sheet (Solar Panel Testbed)",
        "category": "Bought",
        "material": "Clear Float Glass (3.2 mm / 4.0 mm)",
        "dimensions": "285 × 560 × 3.2 mm (Plain Glass Display Slab)",
        "supplier": "Local Glass Vendor / Hardware Shop",
        "link": "Standard float glass sheet (cut to size)",
    },
    "cots_pv_mini_panel": {
        "item": "Mini Telemetry PV Cell (70×70 mm)",
        "category": "Bought",
        "material": "Polycrystalline / Resin",
        "dimensions": "70.0 × 70.0 × 3.0 mm",
        "supplier": "Robu.in / Amazon",
        "link": "https://robu.in/product/mini-solar-panel-cell/",
    },
    "cots_limit_switch": {
        "item": "ONPOW Roller Short Lever Limit Switch",
        "category": "Bought",
        "material": "Phenolic / Stainless",
        "dimensions": "20.0 × 10.0 × 6.0 mm (Holes 9.5 mm)",
        "supplier": "Robu.in SKU R255405",
        "link": "https://robu.in/product/onpow-roller-short-lever-limit-switch/",
    },
    "hw_screw_m5_crossbeam": {
        "item": "M5 × 8 Button Head Socket Screw (ISO 7380)",
        "category": "Fastener",
        "material": "Stainless Steel A2",
        "dimensions": "M5 × 8.0 mm (Head Ø9.5 mm)",
        "supplier": "Fastener Hardware Stock",
        "link": "DIN / ISO Fastener Standard",
    },
    "hw_screw_m5_tray": {
        "item": "M5 × 8 Button Head Socket Screw (ISO 7380)",
        "category": "Fastener",
        "material": "Stainless Steel A2",
        "dimensions": "M5 × 8.0 mm (Head Ø9.5 mm)",
        "supplier": "Fastener Hardware Stock",
        "link": "DIN / ISO Fastener Standard",
    },
    "hw_screw_m5_dog": {
        "item": "M5 × 8 Button Head Socket Screw (ISO 7380)",
        "category": "Fastener",
        "material": "Stainless Steel A2",
        "dimensions": "M5 × 8.0 mm (Head Ø9.5 mm)",
        "supplier": "Fastener Hardware Stock",
        "link": "DIN / ISO Fastener Standard",
    },
    "hw_screw_m5_vwheel": {
        "item": "M5 × 25 Button Head Screw / Bolt",
        "category": "Fastener",
        "material": "Stainless Steel A2",
        "dimensions": "M5 × 25.0 mm",
        "supplier": "Fastener Hardware Stock",
        "link": "DIN / ISO Fastener Standard",
    },
    "hw_tnut_m5": {
        "item": "M5 Drop-in Roll-in T-Nut (Slot 6)",
        "category": "Fastener",
        "material": "Zinc Plated Steel",
        "dimensions": "10.0 × 6.0 × 4.5 mm (M5 Thread)",
        "supplier": "OpenBuilds / Robu.in",
        "link": "https://openbuildspartstore.com/drop-in-tee-nuts/",
    },
    "hw_screw_m3_motor_clamp": {
        "item": "M3 × 8 Socket Head Cap Screw (DIN 912)",
        "category": "Fastener",
        "material": "Stainless Steel A2",
        "dimensions": "M3 × 8.0 mm (Head Ø5.5 mm)",
        "supplier": "Fastener Hardware Stock",
        "link": "ISO 4762 / DIN 912",
    },
    "hw_screw_m3_cowl_tab": {
        "item": "M3 × 8 Socket Head Cap Screw (DIN 912)",
        "category": "Fastener",
        "material": "Stainless Steel A2",
        "dimensions": "M3 × 8.0 mm (Head Ø5.5 mm)",
        "supplier": "Fastener Hardware Stock",
        "link": "ISO 4762 / DIN 912",
    },
    "hw_screw_m3_blower": {
        "item": "M3 × 12 Socket Head Cap Screw (DIN 912)",
        "category": "Fastener",
        "material": "Stainless Steel A2",
        "dimensions": "M3 × 12.0 mm (Head Ø5.5 mm)",
        "supplier": "Fastener Hardware Stock",
        "link": "ISO 4762 / DIN 912",
    },
    "hw_screw_m3_wedge_base": {
        "item": "M3 × 8 Socket Head Cap Screw (DIN 912)",
        "category": "Fastener",
        "material": "Stainless Steel A2",
        "dimensions": "M3 × 8.0 mm",
        "supplier": "Fastener Hardware Stock",
        "link": "ISO 4762 / DIN 912",
    },
    "hw_screw_m3_pv_clip": {
        "item": "M3 × 10 Socket Head Cap Screw (DIN 912)",
        "category": "Fastener",
        "material": "Stainless Steel A2",
        "dimensions": "M3 × 10.0 mm",
        "supplier": "Fastener Hardware Stock",
        "link": "ISO 4762 / DIN 912",
    },
    "hw_screw_m3_pcb": {
        "item": "M3 × 6 Pan Head Self-Tapping Screw",
        "category": "Fastener",
        "material": "Stainless Steel A2",
        "dimensions": "M3 × 6.0 mm (Standoff Pilots)",
        "supplier": "Fastener Hardware Stock",
        "link": "Standard Standoff Hardware",
    },
    "hw_nut_m3": {
        "item": "M3 Standard Hex Nut (DIN 934)",
        "category": "Fastener",
        "material": "Stainless Steel A2",
        "dimensions": "M3 (AF 5.5 × H 2.4 mm)",
        "supplier": "Fastener Hardware Stock",
        "link": "DIN 934",
    },
    "hw_grub_m3": {
        "item": "M3 × 4 Cup-Point Grub Screw (DIN 916)",
        "category": "Fastener",
        "material": "Hardened Carbon Steel",
        "dimensions": "M3 × 4.0 mm (Hex Key 1.5 mm)",
        "supplier": "Fastener Hardware Stock",
        "link": "DIN 916",
    },
    "hw_dowel_pin_cowl": {
        "item": "Hardened Ground Steel Dowel Pin",
        "category": "Hardware",
        "material": "Ground Steel",
        "dimensions": "Ø 4.0 × 10.0 mm (m6)",
        "supplier": "Precision Hardware Stock",
        "link": "DIN 7 / ISO 2338",
    },
    "wire_": {
        "item": "Hookup Wire Harness Lead (22 AWG)",
        "category": "Electrical",
        "material": "Tinned Copper / PVC",
        "dimensions": "Ø 1.2 mm Insulated Lead",
        "supplier": "Robu.in / Electronics Stock",
        "link": "manufacturing_manifest.md # Wiring",
    },
    "testbed_rail_riser": {
        "item": "Testbed 2020 Rail Elevation Riser Foot",
        "category": "Printed",
        "material": "PETG/PLA Black",
        "dimensions": "64.0 × 45.0 × 56.0 mm (40.0 mm rail elevation, M5 clamping, endstop bumper)",
        "supplier": "Internal 3D Print",
        "link": "cad/exports/stl/testbed_rail_riser_foot.stl",
    },
    "testbed_panel_bracket": {
        "item": "Testbed Rail-to-Panel Alignment Bracket",
        "category": "Printed",
        "material": "PETG/PLA Black",
        "dimensions": "37.0 × 40.0 × 31.23 mm (Locks plain display glass at Z=0.0 datum, 15.23 mm above rail)",
        "supplier": "Internal 3D Print",
        "link": "cad/exports/stl/testbed_rail_panel_bracket.stl",
    },
    "testbed_pedestal": {
        "item": "Testbed Panel Under-Frame Pedestal",
        "category": "Printed",
        "material": "PETG/PLA Black",
        "dimensions": "52.0 × 52.0 × 72.03 mm (72.03 mm elevation anti-sag pedestal for plain glass)",
        "supplier": "Internal 3D Print",
        "link": "cad/exports/stl/testbed_panel_pedestal.stl",
    },
}


def _catalog_key(part_name: str) -> str:
    """Find the catalog key that best matches a part label."""
    if part_name.startswith("wire_"):
        return "wire_"
    if part_name.startswith("hw_"):
        if "screw_m3_esp32" in part_name or "screw_m3_l298n" in part_name or \
           "screw_m3_relay" in part_name or "screw_m3_ina219" in part_name:
            return "hw_screw_m3_pcb"
        hw_keys = [k for k in _CATALOG.keys() if k.startswith("hw_")]
        for k in sorted(hw_keys, key=len, reverse=True):
            if k in part_name:
                return k
        return "hw_generic"
    if part_name.startswith("cots_"):
        cots_keys = [k for k in _CATALOG.keys() if k.startswith("cots_")]
        for k in sorted(cots_keys, key=len, reverse=True):
            if k in part_name:
                return k
        return "cots_generic"
    for k in sorted(_CATALOG.keys(), key=len, reverse=True):
        if k in part_name:
            return k
    return "other"


def generate_bom(parts_dict: Dict[str, bd.Shape]) -> List[Dict[str, str]]:
    """
    Generate Bill of Materials table by inspecting parts present in the assembly.
    Counts part quantities by catalog entry.
    """
    counts: Dict[str, int] = {}
    for name in parts_dict.keys():
        key = _catalog_key(name)
        counts[key] = counts.get(key, 0) + 1

    bom = []
    for key, qty in sorted(counts.items()):
        info = _CATALOG.get(key, {
            "item": key,
            "category": "Hardware",
            "material": "Mixed",
            "dimensions": "As modeled",
            "supplier": "Standard",
            "link": "-",
        })
        bom.append({
            "part": info["item"],
            "qty": str(qty),
            "category": info["category"],
            "material": info["material"],
            "key_dimensions": info["dimensions"],
            "supplier": info["supplier"],
            "supplier_link": info["link"],
        })
    return bom


def export_bom_csv(parts_dict: Dict[str, bd.Shape], out_path: str = "exports/bom.csv") -> None:
    """Write dynamically generated BOM to CSV file."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bom = generate_bom(parts_dict)
    fieldnames = ["part", "qty", "category", "material", "key_dimensions", "supplier", "supplier_link"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(bom)
    print(f"Generated dynamic BOM: {out_path} ({len(bom)} line items, {sum(int(r['qty']) for r in bom)} total parts).")
