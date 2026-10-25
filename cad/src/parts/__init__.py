"""
PROJECT A.R.C. – Custom Manufactured Parts Package (src/parts/)
================================================================
Exposes all custom 3D-printable and machined parts:
  - endplate: Left and right carriage endplates with integrated N20 motor brackets
  - clamp / motor_clamp: 25GA-370 split clamp and N20 saddle clamp
  - sled: ESP32 Adapter Sled mounting cradle
  - couplers: N20 to Mini V-wheel drive hub coupler
  - blower: Blower cowl aerodynamic plenum and mounting bracket
"""

from src.parts.endplate import build_carriage_endplate
from src.parts.clamp import build_25ga_motor_clamp, build_n20_motor_clamp, build_clamp
from src.parts.sled import build_esp32_adapter_sled, build_sled
from src.parts.couplers import build_coupler_n20_vwheel
from src.parts.blower import build_blower_cowl_mount, build_blower_cowl_half
from src.parts.testbed import (
    build_testbed_rail_riser_foot,
    build_testbed_rail_panel_bracket,
    build_testbed_panel_pedestal,
)

__all__ = [
    "build_carriage_endplate",
    "build_25ga_motor_clamp",
    "build_n20_motor_clamp",
    "build_clamp",
    "build_esp32_adapter_sled",
    "build_sled",
    "build_coupler_n20_vwheel",
    "build_blower_cowl_mount",
    "build_blower_cowl_half",
    "build_testbed_rail_riser_foot",
    "build_testbed_rail_panel_bracket",
    "build_testbed_panel_pedestal",
]
