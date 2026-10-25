"""
PROJECT A.R.C. – COTS: Electronics Modules & Battery System
============================================================
Detailed B-Rep models for all control, sensing, and power modules:
  - NodeMCU ESP32 on 38-pin screw-terminal expansion board (Robu SKU 1738328)
  - L298N 2A dual H-bridge motor driver (Robu SKU 43821)
  - 1-channel 5V relay module (Robu SKU R260153)
  - INA219 I2C current/power sensor (Robu SKU 421237)
  - 2S 18650 battery holder with BAK NMC 18650 cells (Robu SKU 223415 / 1225174)

Origin convention:
  - Centred at (0, 0) in X-Y on the PCB outline.
  - PCB underside at Z = 0 (components rise into +Z).
"""

from __future__ import annotations
import build123d as bd
from build123d import (
    BuildPart, BuildSketch,
    Box, Cylinder, extrude,
    Plane, Locations, Location, Vector, Mode, Align,
    Rectangle, Circle, RectangleRounded,
)

from .dims import (
    ESP32_SHIELD_PCB_W, ESP32_SHIELD_PCB_D, ESP32_SHIELD_PCB_T,
    ESP32_SHIELD_HOLE_PX, ESP32_SHIELD_HOLE_PY, ESP32_SHIELD_HOLE_D,
    ESP32_MODULE_W, ESP32_MODULE_L, ESP32_MODULE_H,
    ESP32_CAN_W, ESP32_CAN_L, ESP32_CAN_H,
    ESP32_TERMINAL_W, ESP32_TERMINAL_H,
    L298N_PCB_W, L298N_PCB_D, L298N_PCB_T,
    L298N_HOLE_PX, L298N_HOLE_PY, L298N_HOLE_D,
    L298N_HEATSINK_W, L298N_HEATSINK_D, L298N_HEATSINK_H,
    L298N_CAP_D, L298N_CAP_H,
    RELAY_PCB_W, RELAY_PCB_D, RELAY_PCB_T,
    RELAY_HOLE_PX, RELAY_HOLE_PY, RELAY_HOLE_D,
    RELAY_CUBE_W, RELAY_CUBE_D, RELAY_CUBE_H,
    RELAY_TERMINAL_W, RELAY_TERMINAL_D, RELAY_TERMINAL_H,
    INA219_PCB_W, INA219_PCB_D, INA219_PCB_T,
    INA219_HOLE_PX, INA219_HOLE_PY, INA219_HOLE_D,
    INA219_TERMINAL_W, INA219_TERMINAL_D, INA219_TERMINAL_H,
    INA219_SHUNT_W, INA219_SHUNT_D, INA219_SHUNT_H,
    BATTERY_HOLDER_W, BATTERY_HOLDER_L, BATTERY_HOLDER_H,
    BATTERY_HOLDER_WALL, CELL_18650_D, CELL_18650_L,
    CELL_18650_NUB_D, CELL_18650_NUB_H,
)

_CACHE = {}


def build_esp32_shield() -> bd.Solid:
    """
    Build the ESP32 38-Pin Expansion Board with NodeMCU dev module.
    
    Dimensions: 77 × 63 mm PCB, 4 × M3 mounting holes at 71 × 57 mm.
    Underside at Z = 0.
    """
    if "esp32" in _CACHE:
        return _CACHE["esp32"].moved(Location())

    w, d, t = ESP32_SHIELD_PCB_W, ESP32_SHIELD_PCB_D, ESP32_SHIELD_PCB_T
    hx, hy = ESP32_SHIELD_HOLE_PX, ESP32_SHIELD_HOLE_PY
    hd = ESP32_SHIELD_HOLE_D

    with BuildPart() as bp:
        # Base FR4 PCB
        Box(w, d, t, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # 4 mounting clearance holes
        for sx in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                with Locations((sx * hx / 2.0, sy * hy / 2.0, -0.5)):
                    Cylinder(radius=hd / 2.0, height=t + 1.0, mode=Mode.SUBTRACT)

        # Dual rows of terminal blocks along left (-X) and right (+X) edges
        term_x = w / 2.0 - ESP32_TERMINAL_W / 2.0
        term_len = d - 8.0
        for sx in (-1.0, 1.0):
            with Locations((sx * term_x, 0.0, t)):
                Box(ESP32_TERMINAL_W, term_len, ESP32_TERMINAL_H,
                    align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Female socket header strips (two 19-pin rows)
        sock_h = 8.5
        sock_sep = 25.4
        for sx in (-1.0, 1.0):
            with Locations((sx * sock_sep / 2.0, 0.0, t)):
                Box(2.5, 48.0, sock_h, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # ESP32 NodeMCU board plugged in
        node_z = t + sock_h
        with Locations((0.0, 0.0, node_z)):
            Box(ESP32_MODULE_W, ESP32_MODULE_L, 1.6,
                align=(Align.CENTER, Align.CENTER, Align.MIN))

        # ESP-WROOM-32 metal RF shield can
        with Locations((0.0, -4.0, node_z + 1.6)):
            Box(ESP32_CAN_W, ESP32_CAN_L, ESP32_CAN_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Micro-USB port on dev module
        with Locations((0.0, -ESP32_MODULE_L / 2.0 + 2.0, node_z + 1.6)):
            Box(7.5, 5.5, 2.8, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # DC barrel power jack on expansion board (+Y edge)
        with Locations((0.0, d / 2.0 - 5.0, t)):
            Cylinder(radius=4.5, height=11.0, align=(Align.CENTER, Align.CENTER, Align.MIN))

    solid = bp.part
    _CACHE["esp32"] = solid
    return solid.moved(Location())


def build_l298n_driver() -> bd.Solid:
    """
    Build the L298N 2A Dual H-Bridge Motor Driver Module.
    
    Dimensions: 43.5 × 43.5 mm PCB, 4 × M3 holes at 38.5 × 38.5 mm.
    Underside at Z = 0.
    """
    if "l298n" in _CACHE:
        return _CACHE["l298n"].moved(Location())

    w, d, t = L298N_PCB_W, L298N_PCB_D, L298N_PCB_T
    hx, hy = L298N_HOLE_PX, L298N_HOLE_PY
    hd = L298N_HOLE_D

    with BuildPart() as bp:
        # Base PCB
        Box(w, d, t, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # 4 corner mounting holes
        for sx in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                with Locations((sx * hx / 2.0, sy * hy / 2.0, -0.5)):
                    Cylinder(radius=hd / 2.0, height=t + 1.0, mode=Mode.SUBTRACT)

        # Central aluminium heatsink
        hw, hd_hs, hh = L298N_HEATSINK_W, L298N_HEATSINK_D, L298N_HEATSINK_H
        with Locations((0.0, -5.0, t)):
            Box(hw, hd_hs, hh, align=(Align.CENTER, Align.CENTER, Align.MIN))
            # Heatsink fin slots (cut 3 slots along Y)
            for ox in (-5.0, 0.0, 5.0):
                with Locations((ox, 0.0, hh / 2.0)):
                    Box(1.5, hd_hs + 1.0, hh * 0.7, mode=Mode.SUBTRACT)

        # 3-pin power screw terminal block (+Y edge)
        with Locations((0.0, d / 2.0 - 5.0, t)):
            Box(22.0, 8.5, 10.0, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Motor output screw terminals (-X and +X sides)
        for sx in (-1.0, 1.0):
            with Locations((sx * (w / 2.0 - 5.0), 4.0, t)):
                Box(8.5, 15.0, 10.0, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Electrolytic filter capacitors
        for ox in (-12.0, 12.0):
            with Locations((ox, -12.0, t)):
                Cylinder(radius=L298N_CAP_D / 2.0, height=L298N_CAP_H,
                         align=(Align.CENTER, Align.CENTER, Align.MIN))

    solid = bp.part
    _CACHE["l298n"] = solid
    return solid.moved(Location())


def build_relay_module() -> bd.Solid:
    """
    Build the 1-Channel 5V Relay Module (SRD-05VDC-SL-C).
    
    Dimensions: 50 × 26 mm PCB, 4 × M3 holes at 44 × 20 mm.
    Underside at Z = 0.
    """
    if "relay" in _CACHE:
        return _CACHE["relay"].moved(Location())

    w, d, t = RELAY_PCB_W, RELAY_PCB_D, RELAY_PCB_T
    hx, hy = RELAY_HOLE_PX, RELAY_HOLE_PY
    hd = RELAY_HOLE_D

    with BuildPart() as bp:
        # Base PCB
        Box(w, d, t, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # 4 mounting holes
        for sx in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                with Locations((sx * hx / 2.0, sy * hy / 2.0, -0.5)):
                    Cylinder(radius=hd / 2.0, height=t + 1.0, mode=Mode.SUBTRACT)

        # Songle SRD blue relay cube (-X side)
        with Locations((-w / 2.0 + RELAY_CUBE_W / 2.0 + 5.0, 0.0, t)):
            Box(RELAY_CUBE_W, RELAY_CUBE_D, RELAY_CUBE_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN))

        # 3-pin output screw terminal block (+X side)
        with Locations((w / 2.0 - RELAY_TERMINAL_D / 2.0 - 3.0, 0.0, t)):
            Box(RELAY_TERMINAL_D, RELAY_TERMINAL_W, RELAY_TERMINAL_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN))

        # 3-pin input header pins (-X edge)
        with Locations((-w / 2.0 + 3.0, 0.0, t)):
            Box(2.5, 7.6, 8.5, align=(Align.CENTER, Align.CENTER, Align.MIN))

    solid = bp.part
    _CACHE["relay"] = solid
    return solid.moved(Location())


def build_ina219_sensor() -> bd.Solid:
    """
    Build the INA219 I2C Current/Power Sensor Breakout.
    
    Dimensions: 25.5 × 22.5 mm PCB, 2 × M3 holes at 20 × 17 mm.
    Underside at Z = 0.
    """
    if "ina219" in _CACHE:
        return _CACHE["ina219"].moved(Location())

    w, d, t = INA219_PCB_W, INA219_PCB_D, INA219_PCB_T
    hx, hy = INA219_HOLE_PX, INA219_HOLE_PY
    hd = INA219_HOLE_D

    with BuildPart() as bp:
        # Base PCB
        Box(w, d, t, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # 2 diagonal mounting holes
        with Locations((-hx / 2.0, -hy / 2.0, -0.5)):
            Cylinder(radius=hd / 2.0, height=t + 1.0, mode=Mode.SUBTRACT)
        with Locations((hx / 2.0, hy / 2.0, -0.5)):
            Cylinder(radius=hd / 2.0, height=t + 1.0, mode=Mode.SUBTRACT)

        # 2-pin screw terminal for current sensing (+Y side)
        with Locations((0.0, d / 2.0 - INA219_TERMINAL_D / 2.0 - 2.0, t)):
            Box(INA219_TERMINAL_W, INA219_TERMINAL_D, INA219_TERMINAL_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN))

        # R100 high-precision shunt resistor
        with Locations((0.0, -1.0, t)):
            Box(INA219_SHUNT_W, INA219_SHUNT_D, INA219_SHUNT_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN))

        # 6-pin male header (-Y edge)
        with Locations((0.0, -d / 2.0 + 2.5, t)):
            Box(15.2, 2.5, 8.5, align=(Align.CENTER, Align.CENTER, Align.MIN))

    solid = bp.part
    _CACHE["ina219"] = solid
    return solid.moved(Location())


def build_battery_holder_2s() -> bd.Solid:
    """
    Build the 2S 18650 Battery Holder with two BAK NMC 18650 cells.
    
    Dimensions: 41 × 77 × 20 mm outer casing.
    Long axis along Y. Underside at Z = 0.
    """
    if "battery" in _CACHE:
        return _CACHE["battery"].moved(Location())

    w, l, h = BATTERY_HOLDER_W, BATTERY_HOLDER_L, BATTERY_HOLDER_H
    wall = BATTERY_HOLDER_WALL
    cell_d = CELL_18650_D
    cell_l = CELL_18650_L
    cell_r = cell_d / 2.0

    with BuildPart() as bp:
        # Outer holder tray (Box with rounded corners)
        with BuildSketch(Plane.XY):
            RectangleRounded(w, l, 2.5)
        extrude(amount=h)

        # Cavity cut for cells (Z > wall)
        cav_w = w - 2.0 * wall
        cav_l = l - 2.0 * wall
        with Locations((0.0, 0.0, wall)):
            Box(cav_w, cav_l, h, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)

        # Two 18650 cylindrical cells inside cavities
        # Cell centres at X = ±10 mm, Y = 0 mm, Z = wall + cell_r
        cell_zc = wall + cell_r
        for sx in (-1.0, 1.0):
            cx = sx * 10.0
            with Locations((cx, 0.0, cell_zc)):
                # Cylindrical cell body along Y
                with BuildSketch(Plane.XZ.offset(-cell_l / 2.0)):
                    Circle(cell_r)
                extrude(amount=cell_l)
                # Positive button nub at +Y end
                with BuildSketch(Plane.XZ.offset(cell_l / 2.0)):
                    Circle(CELL_18650_NUB_D / 2.0)
                extrude(amount=CELL_18650_NUB_H)

        # Slide power switch on one end (+Y face)
        with Locations((0.0, l / 2.0, h / 2.0)):
            Box(10.0, 3.0, 6.0, align=(Align.CENTER, Align.MIN, Align.CENTER))

    solid = bp.part
    _CACHE["battery"] = solid
    return solid.moved(Location())
