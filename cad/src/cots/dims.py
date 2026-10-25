"""
PROJECT A.R.C. – COTS Dimensions & Sourcing Specifications
===========================================================
Single source of truth for all Commercial Off-The-Shelf (COTS) bought parts.
Contains dimensional specifications, supplier metadata, datasheets, and URLs.
Units: millimetres, degrees, grams.

Every dimension is either verified by manufacturer datasheet/supplier page
or explicitly tagged '# ASSUMED' and catalogued in docs/ASSUMPTIONS.md.
"""

from __future__ import annotations

# =============================================================================
# 1. 2020 STRUCTURAL EXTRUSION & HARDWARE
# =============================================================================
# Source: OpenBuilds V-Slot 2020 Linear Rail Specification / Misumi HFS5-2020
# URL: https://openbuildspartstore.com/v-slot-20x20-linear-rail/
EXTRUSION_WIDTH = 20.0             # Outer profile width (mm)
EXTRUSION_HEIGHT = 20.0            # Outer profile height (mm)
EXTRUSION_CENTER_BORE_D = 4.2      # M5 tap core diameter (mm)
EXTRUSION_SLOT_OPEN = 6.2          # 6 mm nominal T/V-slot outer opening width (mm)
EXTRUSION_SLOT_DEPTH = 6.1         # Total depth from face to slot floor (mm)
EXTRUSION_LIP_THICKNESS = 1.8      # Slot retaining lip thickness (mm)
EXTRUSION_SLOT_BASE_W = 10.5       # Internal slot cavity width (mm)

# M5 Drop-in / Roll-in T-nut (2020 slot 6 mm)
# Source: OpenBuilds Drop-In Tee Nut M5 / Misumi HNTA5-5
TNUT_M5_LENGTH = 10.0              # Overall length along slot (mm)
TNUT_M5_WIDTH = 6.0                # Body width entering slot (mm)
TNUT_M5_HEIGHT = 4.5               # Overall height (mm)
TNUT_M5_THREAD_D = 5.0             # M5 internal thread (mm)
TNUT_M5_MASS_G = 2.0               # # ASSUMED: average zinc-plated steel M5 T-nut mass (g)

# =============================================================================
# 2. V-WHEELS & BEARINGS
# =============================================================================
# Mini V-Wheel kit (OpenBuilds Mini V Wheel)
# Source: OpenBuilds Mini V Wheel Kit Spec Sheet
# URL: https://openbuildspartstore.com/mini-v-wheel-kit/
VWHEEL_MINI_OD = 15.23             # Pitch outer diameter across V-peaks (mm)
VWHEEL_MINI_WIDTH = 8.8            # Delrin wheel width (mm)
VWHEEL_MINI_BORE = 10.0            # Bearing pocket outer bore diameter (mm)
VWHEEL_MINI_V_ANGLE = 90.0         # Included angle of V-groove (deg)
VWHEEL_MINI_V_DEPTH = 1.6          # # ASSUMED: depth of V-groove from OD (mm)
VWHEEL_MINI_BEARING_OD = 10.0      # MR105ZZ bearing outer diameter (mm)
VWHEEL_MINI_BEARING_ID = 5.0       # MR105ZZ bearing inner diameter / bolt size (mm)
VWHEEL_MINI_BEARING_W = 4.0        # MR105ZZ bearing width (mm)
VWHEEL_SPACER_OD = 8.0             # Precision aluminium spacer diameter (mm)
VWHEEL_SPACER_LEN = 6.0            # Spacer length between wheel and plate (mm)
VWHEEL_MASS_G = 4.5                # Complete mini V-wheel assembly mass with bearings (g)

# 684ZZ Miniature Precision Ball Bearing
# Source: NMB / NSK Miniature Deep Groove Ball Bearings Datasheet (684ZZ)
# URL: https://www.nmbtc.com/bearings/part-numbers/684ZZ
BRG_684ZZ_OD = 9.0                 # Outer diameter (mm)
BRG_684ZZ_ID = 4.0                 # Inner bore diameter (mm)
BRG_684ZZ_WIDTH = 4.0              # Total width (mm)
BRG_684ZZ_SHIELD_T = 0.5           # # ASSUMED: stamped metal shield inset depth (mm)
BRG_684ZZ_MASS_G = 1.1             # Mass per bearing (g)

# =============================================================================
# 3. ELECTRONICS MODULES & BATTERY SYSTEM
# =============================================================================
# NodeMCU ESP32-WROOM-32D on 38-Pin Screw-Terminal Expansion Board
# Source: Robu.in SKU 1738328 & SKU 1308031
# URL: https://robu.in/product/esp32-expansion-board-38-pins-screw-terminal/
ESP32_SHIELD_PCB_W = 77.0          # PCB length along X (mm)
ESP32_SHIELD_PCB_D = 63.0          # PCB width along Y (mm)
ESP32_SHIELD_PCB_T = 1.6           # FR4 board thickness (mm)
ESP32_SHIELD_HOLE_PX = 71.0        # Mounting hole pitch along X (mm)
ESP32_SHIELD_HOLE_PY = 57.0        # Mounting hole pitch along Y (mm)
ESP32_SHIELD_HOLE_D = 3.2          # Mounting hole clearance diameter (mm)
ESP32_MODULE_W = 28.5              # NodeMCU ESP32 board width (mm)
ESP32_MODULE_L = 54.5              # NodeMCU ESP32 board length (mm)
ESP32_MODULE_H = 12.0              # Height including headers above breakout (mm)
ESP32_CAN_W = 18.0                 # Metal RF shield can width (mm)
ESP32_CAN_L = 25.5                 # Metal RF shield can length (mm)
ESP32_CAN_H = 3.0                  # Metal RF shield can height (mm)
ESP32_TERMINAL_W = 8.5             # Terminal block width along outer sides (mm)
ESP32_TERMINAL_H = 10.0            # Terminal block height above PCB (mm)
ESP32_SHIELD_MASS_G = 45.0         # # ASSUMED: Expansion board + ESP32 dev board combined mass (g)

# L298N Dual H-Bridge Motor Driver Module
# Source: Robu.in SKU 43821 / ST L298N Datasheet
# URL: https://robu.in/product/l298n-2a-dual-motor-driver-module/
L298N_PCB_W = 43.5                 # Board width (mm)
L298N_PCB_D = 43.5                 # Board depth (mm)
L298N_PCB_T = 1.6                  # PCB thickness (mm)
L298N_HOLE_PX = 38.5               # Mounting hole pitch along X (mm)
L298N_HOLE_PY = 38.5               # Mounting hole pitch along Y (mm)
L298N_HOLE_D = 3.2                 # Mounting hole diameter (mm)
L298N_HEATSINK_W = 20.0            # Aluminium heatsink width (mm)
L298N_HEATSINK_D = 12.0            # Aluminium heatsink depth (mm)
L298N_HEATSINK_H = 24.0            # Heatsink height above PCB (mm)
L298N_CAP_D = 8.0                  # Electrolytic filter cap diameter (mm)
L298N_CAP_H = 12.0                 # Electrolytic filter cap height (mm)
L298N_MASS_G = 26.0                # Total module mass (g)

# 1-Channel 5V Relay Module (High Level Trigger)
# Source: Robu.in SKU R260153 / Songle SRD-05VDC-SL-C
# URL: https://robu.in/product/1-channel-isolated-5v-relay-module/
RELAY_PCB_W = 50.0                 # Board length (mm)
RELAY_PCB_D = 26.0                 # Board width (mm)
RELAY_PCB_T = 1.6                  # PCB thickness (mm)
RELAY_HOLE_PX = 44.0               # Mounting hole pitch along X (mm)
RELAY_HOLE_PY = 20.0               # Mounting hole pitch along Y (mm)
RELAY_HOLE_D = 3.2                 # Mounting hole diameter (mm)
RELAY_CUBE_W = 19.0                # Songle SRD blue relay cube length (mm)
RELAY_CUBE_D = 15.5                # Songle SRD blue relay cube width (mm)
RELAY_CUBE_H = 15.5                # Songle SRD blue relay cube height (mm)
RELAY_TERMINAL_W = 24.0            # 3-pin output terminal block length (mm)
RELAY_TERMINAL_D = 8.5             # Terminal block width (mm)
RELAY_TERMINAL_H = 10.0            # Terminal block height (mm)
RELAY_MASS_G = 16.0                # Total relay module mass (g)

# INA219 I2C Current/Power Sensor Breakout
# Source: Robu.in SKU 421237 / TI INA219 Datasheet
# URL: https://robu.in/product/ina219-i2c-bi-directional-current-power-sensor-module/
INA219_PCB_W = 25.5                # Board width (mm)
INA219_PCB_D = 22.5                # Board depth (mm)
INA219_PCB_T = 1.6                 # PCB thickness (mm)
INA219_HOLE_PX = 20.0              # Mounting hole pitch along X (mm)
INA219_HOLE_PY = 17.0              # Mounting hole pitch along Y (mm)
INA219_HOLE_D = 3.0                # Mounting hole diameter (mm)
INA219_TERMINAL_W = 10.0           # 2-pin screw terminal length (mm)
INA219_TERMINAL_D = 8.0            # Terminal width (mm)
INA219_TERMINAL_H = 10.0           # Terminal height (mm)
INA219_SHUNT_W = 6.4               # R100 alloy shunt resistor width (mm)
INA219_SHUNT_D = 3.2               # R100 alloy shunt resistor depth (mm)
INA219_SHUNT_H = 1.2               # Shunt resistor height (mm)
INA219_MASS_G = 3.5                # Total sensor module mass (g)

# 2S 18650 Battery Holder & BAK 18650 Cells
# Source: Robu.in SKU 223415 (holder) & SKU 1225174 (BAK 18650 2600mAh cell)
# URL: https://robu.in/product/2-slot-18650-battery-holder-case-with-leads/
BATTERY_HOLDER_W = 41.0            # Outer tray width (mm)
BATTERY_HOLDER_L = 77.0            # Outer tray length (mm)
BATTERY_HOLDER_H = 20.0            # Outer tray depth/height (mm)
BATTERY_HOLDER_WALL = 1.5          # Moulded ABS wall thickness (mm)
CELL_18650_D = 18.5                # 18650 cell cylindrical diameter (mm)
CELL_18650_L = 65.3                # 18650 cell length (mm)
CELL_18650_NUB_D = 6.0             # Positive terminal button diameter (mm)
CELL_18650_NUB_H = 1.5             # Positive terminal button height (mm)
CELL_18650_MASS_G = 45.0           # BAK NMC 18650CH cell mass (g per cell)
BATTERY_HOLDER_EMPTY_MASS_G = 12.0 # Empty plastic holder + contacts mass (g)

# =============================================================================
# 4. 5015 RADIAL BLOWER FAN
# =============================================================================
# Source: Standard 5015 DC Brushless Centrifugal Blower Datasheet (Delta BFB0512HH / Sunon GB1205PHV1)
# Dimensions matched to Part E Blower Cowl intake neck and mounting flange
BLOWER_5015_SIZE = 50.0            # Overall width & height envelope (mm)
BLOWER_5015_THICKNESS = 15.0       # Axial thickness (mm)
BLOWER_5015_INLET_D = 32.0         # Air intake eye diameter (mm)
BLOWER_5015_HUB_D = 20.0           # Impeller centre motor hub diameter (mm)
BLOWER_5015_OUTLET_W = 15.0        # Rectangular exhaust outlet width (mm)
BLOWER_5015_OUTLET_H = 20.0        # Rectangular exhaust outlet height (mm)
BLOWER_5015_FLANGE_BC = 30.0       # Flange mounting bolt circle (mm) - matches FLANGE_BOLT_CIRCLE
BLOWER_5015_HOLE_D = 3.2           # Mounting tab hole diameter (mm)
BLOWER_5015_MASS_G = 28.0          # Blower fan mass (g)

# =============================================================================
# 5. MOTORS & LIMIT SWITCH
# =============================================================================
# N20 Micro Metal Gear Motor (6V / 12V 300 RPM)
# Source: Robu.in SKU 75800 / Pololu Micro Metal Gearmotor Datasheet
# URL: https://robu.in/product/n20-6v-300-rpm-micro-metal-gear-motor/
N20_GEARBOX_W = 12.0               # Gearbox width (mm) - matches MOTOR_GBX_W
N20_GEARBOX_H = 10.0               # Gearbox height (mm) - matches MOTOR_GBX_H
N20_GEARBOX_L = 15.0               # Gearbox length (mm) - matches MOTOR_GBX_L
N20_MOTOR_D = 12.0                 # Motor can diameter (mm)
N20_MOTOR_FLAT_H = 10.0            # Motor can flat-to-flat thickness (mm)
N20_MOTOR_L = 15.0                 # Motor can body length (mm)
N20_TERMINAL_L = 2.0               # Solder terminal lug protrusion (mm)
N20_SHAFT_D = 3.0                  # Output shaft outer diameter (mm)
N20_SHAFT_L = 10.0                 # Shaft extension length (mm)
N20_SHAFT_FLAT_D = 2.5             # D-cut flat thickness (mm)
N20_SHAFT_FLAT_L = 7.0             # D-cut flat length (mm)
N20_MASS_G = 9.5                   # Mass per N20 gearmotor (g)

# ONPOW Roller Short Lever Limit Switch (Endstop)
# Source: Robu.in SKU R255405 / ONPOW Miniature Snap-Action Switch
# URL: https://robu.in/product/onpow-roller-short-lever-limit-switch/
LIMIT_SW_BODY_L = 20.0             # Switch body length (mm)
LIMIT_SW_BODY_H = 10.0             # Switch body height (mm)
LIMIT_SW_BODY_W = 6.0              # Switch body thickness (mm)
LIMIT_SW_HOLE_SPACING = 9.5        # Mounting hole pitch (mm)
LIMIT_SW_HOLE_D = 2.5              # Mounting hole diameter (mm)
LIMIT_SW_LEVER_L = 14.5            # Actuating lever arm length (mm)
LIMIT_SW_ROLLER_D = 4.8            # Lever tip roller diameter (mm)
LIMIT_SW_ROLLER_W = 3.0            # Lever tip roller width (mm)
LIMIT_SW_MASS_G = 4.0              # Switch mass (g)

# =============================================================================
# 6. SOLAR PANELS
# =============================================================================
# Loom Solar 10 W 12 V Polycrystalline Solar Panel
# Source: Loom Solar 10W Module Technical Datasheet / Retail Spec
# URL: https://www.loomsolar.com/products/loom-solar-panel-10-watt
LOOM_SOLAR_10W_L = 350.0           # Length along long axis (mm)
LOOM_SOLAR_10W_W = 285.0           # Width along short axis (mm)
LOOM_SOLAR_10W_T = 22.0            # Anodized aluminium frame depth (mm)
LOOM_SOLAR_10W_FRAME_LIP = 15.0    # Aluminium frame lip width (mm)
LOOM_SOLAR_10W_GLASS_T = 3.2       # Low-iron tempered glass thickness (mm)
LOOM_SOLAR_10W_JBOX_L = 50.0       # # ASSUMED: Rear junction box length (mm)
LOOM_SOLAR_10W_JBOX_W = 40.0       # # ASSUMED: Rear junction box width (mm)
LOOM_SOLAR_10W_JBOX_H = 15.0       # # ASSUMED: Rear junction box height (mm)
LOOM_SOLAR_10W_MASS_G = 1000.0     # Nominal panel mass (g)

# Mini Telemetry PV Cell (70 x 70 mm)
# Source: Standard epoxy-encapsulated polycrystalline mini solar cell
# URL: https://robu.in/product/mini-solar-panel-cell/
MINI_PV_L = 70.0                   # Cell length (mm) - matches PV_CELL_L
MINI_PV_W = 70.0                   # Cell width (mm) - matches PV_CELL_W
MINI_PV_T = 3.0                    # Cell thickness (mm) - matches PV_CELL_T
MINI_PV_TAB_W = 2.0                # Solder ribbon tab width (mm)
MINI_PV_TAB_L = 8.0                # Solder ribbon tab length (mm)
MINI_PV_MASS_G = 18.0              # # ASSUMED: Mini cell mass (g)

# =============================================================================
# 7. ROLLER HARDWARE & FASTENERS
# =============================================================================
# Microfibre Plush Roller Sleeve
# Source: Auto Hub 800 GSM plush microfiber sleeve (matches ROLLER_FINISHED_OD)
SLEEVE_ID = 41.2                   # Inner diameter matching UPVC conduit OD (mm)
SLEEVE_OD = 50.0                   # Outer finished diameter (mm)
SLEEVE_LENGTH = 320.0              # Sleeve length (mm)
SLEEVE_MASS_G = 42.0               # # ASSUMED: 800 GSM microfiber wrap mass (g)

# Dowel Pins for Cowl Joint
# Source: DIN 7 / ISO 2338 hardened ground steel dowel pin Ø4 × 10 mm
DOWEL_PIN_D = 4.0                  # Ground steel pin diameter (mm)
DOWEL_PIN_L = 10.0                 # Pin length (mm)
DOWEL_PIN_MASS_G = 1.0             # Mass per pin (g)

# DIN 912 / ISO 4762 Socket Head Cap Screws (SHCS)
# Source: ISO 4762 metric fastener standard
M3_SHCS_HEAD_D = 5.5               # M3 socket head diameter (mm)
M3_SHCS_HEAD_H = 3.0               # M3 socket head height (mm)
M3_SHCS_HEX = 2.5                  # M3 socket key size (mm)

# ISO 7380 Button Head Screws
# Source: ISO 7380 metric button head standard
M3_BUTTON_HEAD_D = 5.7             # M3 button head diameter (mm)
M3_BUTTON_HEAD_H = 1.65            # M3 button head height (mm)
M5_BUTTON_HEAD_D = 9.5             # M5 button head diameter (mm)
M5_BUTTON_HEAD_H = 2.75            # M5 button head height (mm)

# DIN 934 Hexagon Nuts
# Source: DIN 934 metric nut standard
M3_HEX_NUT_AF = 5.5                # M3 width across flats (mm)
M3_HEX_NUT_H = 2.4                 # M3 nominal nut thickness (mm)

# DIN 916 Cup-point Hex Socket Set Screws (Grub Screws)
# Source: DIN 916 metric grub screw standard
M3_GRUB_D = 3.0                    # Thread diameter (mm)
M3_GRUB_L = 4.0                    # Standard grub screw length for plug clamping (mm)
M3_GRUB_HEX = 1.5                  # Hex key drive size (mm)

# Densities for Mass Computations (g/cm^3)
DENSITY_PETG = 1.27
DENSITY_ASA = 1.07
DENSITY_ALUMINIUM = 2.70
DENSITY_STEEL = 7.85
DENSITY_BRASS = 8.40
DENSITY_DELRIN = 1.41
DENSITY_ABS = 1.04
DENSITY_COPPER = 8.96
