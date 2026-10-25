"""
PROJECT A.R.C. – COTS Library
==============================
Parametric, realistic B-Rep models of all bought components and hardware.
"""

from .dims import *
from .extrusion_2020 import build_2020_extrusion, build_m5_tnut
from .vwheel import build_mini_v_wheel, build_684zz_bearing, build_vwheel_spacer
from .electronics import (
    build_esp32_shield, build_l298n_driver,
    build_relay_module, build_ina219_sensor,
    build_battery_holder_2s,
)
from .blower_5015 import build_5015_blower
from .motors import build_n20_gearmotor, build_25ga370_motor, build_onpow_limit_switch
from .solar_panels import build_mini_pv_cell, build_loom_solar_10w, build_framed_solar_panel, build_flat_panel_slab
from .roller_hardware import build_microfiber_sleeve, build_dowel_pin, build_m3_set_screw
