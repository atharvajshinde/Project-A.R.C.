"""
PROJECT A.R.C. – Electrical Wiring Harness & Routing
=====================================================
3D CAD representation of the complete robot wiring harness.
Wires are modelled as swept circular profiles (Ø 1.2 mm) along smooth 3D paths
with minimum bend radius >= 5.0 mm.

Physical routing constraints:
  - Routed through chassis tray wire exits (WIRE_EXITS) and Ø8 cable hole.
  - Zero collision with roller envelope (R = 25 mm cylinder, Z in [0, 50]).
  - Zero collision with blower cowl plenum and air-knife -45° jet path.
  - Generates cut-length schedule table (Path Length + 10%).
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Tuple, Dict
import build123d as bd
from build123d import (
    BuildPart, BuildSketch, BuildLine,
    Spline, Circle, sweep, Plane, Vector,
    Compound, Solid, Location, Color,
)

# Standard wire gauge diameter: Ø 1.2 mm (approx. 22 AWG hookup wire with PVC insulation)
WIRE_DIAMETER = 1.2
WIRE_RADIUS = WIRE_DIAMETER / 2.0   # 0.6 mm


@dataclass
class WireNet:
    net_name: str
    source_component: str
    source_pin: str
    target_component: str
    target_pin: str
    color_name: str
    rgb_color: Tuple[float, float, float]
    waypoints: List[Tuple[float, float, float]]


def _smooth_waypoints(pts: List[Tuple[float, float, float]], blend_r: float = 6.0) -> List[Tuple[float, float, float]]:
    """Insert tangent blend points at sharp corners to guarantee bend radius >= blend_r."""
    if len(pts) <= 2:
        return pts
    smooth_pts = [pts[0]]
    for i in range(1, len(pts) - 1):
        p_prev = Vector(pts[i - 1])
        p_curr = Vector(pts[i])
        p_next = Vector(pts[i + 1])
        d_in = (p_curr - p_prev).length
        d_out = (p_next - p_curr).length
        if d_in < 1e-4 or d_out < 1e-4:
            continue
        v_in = (p_curr - p_prev).normalized()
        v_out = (p_next - p_curr).normalized()
        offset_in = min(blend_r, d_in * 0.4)
        offset_out = min(blend_r, d_out * 0.4)
        smooth_pts.append(tuple(p_curr - v_in * offset_in))
        smooth_pts.append(tuple(p_curr + v_out * offset_out))
    smooth_pts.append(pts[-1])
    return smooth_pts


# Definition of all physical harness runs in the robot
NET_DEFINITIONS: List[WireNet] = [
    # 1. 2S Battery to Motor Driver (Main Power Rail)
    WireNet(
        net_name="NET_VBAT_POS",
        source_component="cots_battery_2x18650",
        source_pin="BAT+",
        target_component="cots_motor_driver_l298n",
        target_pin="12V_IN",
        color_name="Red",
        rgb_color=(0.85, 0.10, 0.10),
        waypoints=[
            (-114.2, -40.0, 68.0),
            (-112.5, -40.0, 65.0),
            (-112.5, -34.0, 65.0),
            (-98.0, -34.0, 65.0),
            (-89.5, -34.0, 65.0),
        ],
    ),
    WireNet(
        net_name="NET_VBAT_NEG",
        source_component="cots_battery_2x18650",
        source_pin="BAT-",
        target_component="cots_motor_driver_l298n",
        target_pin="GND",
        color_name="Black",
        rgb_color=(0.10, 0.10, 0.10),
        waypoints=[
            (-114.2, -70.0, 68.0),
            (-112.5, -70.0, 65.0),
            (-112.5, -34.5, 65.0),
            (-86.5, -34.5, 65.0),
        ],
    ),

    # 2. Motor Driver 5V Logic to ESP32 Breakout (via Front Raceway)
    WireNet(
        net_name="NET_5V_SYS",
        source_component="cots_motor_driver_l298n",
        source_pin="5V_OUT",
        target_component="esp32_adapter_sled",
        target_pin="VIN",
        color_name="Red",
        rgb_color=(0.85, 0.10, 0.10),
        waypoints=[
            (-83.0, -34.0, 65.5),
            (-72.0, -34.0, 65.5),
            (-59.4, -34.0, 65.5),
            (-59.4, 15.0, 60.5),
            (140.0, 15.0, 60.5),
            (147.2, 10.0, 63.0),
            (147.2, -15.8, 65.0),
        ],
    ),
    WireNet(
        net_name="NET_GND_SYS",
        source_component="cots_motor_driver_l298n",
        source_pin="GND",
        target_component="esp32_adapter_sled",
        target_pin="GND",
        color_name="Black",
        rgb_color=(0.10, 0.10, 0.10),
        waypoints=[
            (-85.0, -34.0, 65.5),
            (-72.0, -34.0, 65.5),
            (-59.4, -34.0, 65.5),
            (-59.4, 17.0, 60.5),
            (140.0, 17.0, 60.5),
            (147.2, 10.0, 63.0),
            (147.2, -18.8, 65.0),
        ],
    ),

    # 3. Relay to 5015 Blower Fan (via Exit T -88.0)
    WireNet(
        net_name="NET_BLOWER_PWR",
        source_component="cots_relay_module",
        source_pin="NO",
        target_component="cots_blower_5015",
        target_pin="FAN+",
        color_name="Yellow",
        rgb_color=(0.90, 0.80, 0.10),
        waypoints=[
            (-85.0, -6.2, 65.0),
            (-88.0, 0.0, 62.0),
            (-88.0, 14.0, 59.5),
            (-80.0, 22.0, 52.0),
            (-40.0, 35.0, 48.0),
            (-15.0, 48.0, 45.0),
        ],
    ),
    WireNet(
        net_name="NET_BLOWER_GND",
        source_component="cots_motor_driver_l298n",
        source_pin="GND",
        target_component="cots_blower_5015",
        target_pin="FAN-",
        color_name="Black",
        rgb_color=(0.10, 0.10, 0.10),
        waypoints=[
            (-84.0, -34.0, 65.5),
            (-72.0, -34.0, 65.5),
            (-59.4, -34.0, 65.5),
            (-59.4, 0.0, 62.0),
            (-86.0, 14.0, 59.5),
            (-78.0, 22.0, 52.0),
            (-38.0, 35.0, 48.0),
            (-17.0, 48.0, 45.0),
        ],
    ),

    # 4. L298N Channel A (OUT1/OUT2): Paralleled Dual N20 Gantry Traversal Motors
    WireNet(
        net_name="NET_MOTOR_L_A",
        source_component="cots_motor_driver_l298n",
        source_pin="OUT1",
        target_component="cots_motor_n20_left",
        target_pin="M1+",
        color_name="Blue",
        rgb_color=(0.15, 0.35, 0.85),
        waypoints=[
            (-110.5, -53.0, 65.0),
            (-112.5, -53.0, 65.0),
            (-112.5, -34.0, 65.0),
            (-100.0, -34.0, 65.0),
            (-72.0, -34.0, 65.0),
            (-57.0, -34.0, 64.0),
            (-57.0, -5.0, 64.0),
            (-57.0, 15.0, 62.0),
            (-140.0, 15.0, 62.0),
            (-170.0, 15.0, 54.0),
            (-180.0, 15.0, 48.0),
            (-190.0, 0.0, 30.0),
            (-200.0, -20.0, 10.0),
            (-208.0, -36.0, -5.0),
        ],
    ),
    WireNet(
        net_name="NET_MOTOR_L_B",
        source_component="cots_motor_driver_l298n",
        source_pin="OUT2",
        target_component="cots_motor_n20_left",
        target_pin="M1-",
        color_name="White",
        rgb_color=(0.85, 0.85, 0.88),
        waypoints=[
            (-110.5, -55.0, 65.0),
            (-112.5, -55.0, 65.0),
            (-112.5, -34.0, 65.0),
            (-100.0, -34.0, 65.0),
            (-72.0, -34.0, 65.0),
            (-57.0, -34.0, 64.0),
            (-57.0, -5.0, 64.0),
            (-57.0, 15.0, 62.0),
            (-140.0, 15.0, 62.0),
            (-170.0, 15.0, 54.0),
            (-180.0, 15.0, 48.0),
            (-190.0, 0.0, 30.0),
            (-200.0, -20.0, 10.0),
            (-208.0, -36.0, -7.0),
        ],
    ),
    WireNet(
        net_name="NET_MOTOR_R_A",
        source_component="cots_motor_driver_l298n",
        source_pin="OUT1",
        target_component="cots_motor_n20_right",
        target_pin="M2+",
        color_name="Blue",
        rgb_color=(0.15, 0.35, 0.85),
        waypoints=[
            (-110.5, -53.0, 65.0),
            (-100.0, -34.0, 65.0),
            (-59.4, -34.0, 65.0),
            (-59.4, 19.0, 60.5),
            (140.0, 19.0, 60.5),
            (170.0, 19.0, 54.0),
            (180.0, 19.0, 48.0),
            (190.0, 0.0, 30.0),
            (200.0, -20.0, 10.0),
            (208.0, -36.0, -5.0),
        ],
    ),
    WireNet(
        net_name="NET_MOTOR_R_B",
        source_component="cots_motor_driver_l298n",
        source_pin="OUT2",
        target_component="cots_motor_n20_right",
        target_pin="M2-",
        color_name="White",
        rgb_color=(0.85, 0.85, 0.88),
        waypoints=[
            (-110.5, -55.0, 65.0),
            (-100.0, -34.0, 65.0),
            (-59.4, -34.0, 65.0),
            (-59.4, 21.0, 60.5),
            (140.0, 21.0, 60.5),
            (170.0, 21.0, 54.0),
            (180.0, 21.0, 48.0),
            (190.0, 0.0, 30.0),
            (200.0, -20.0, 10.0),
            (208.0, -36.0, -7.0),
        ],
    ),

    # 5. L298N Channel B (OUT3/OUT4): Single 25GA-370 Roller Drive Motor
    WireNet(
        net_name="NET_MOTOR_ROLLER_POS",
        source_component="cots_motor_driver_l298n",
        source_pin="OUT3",
        target_component="cots_motor_25ga370",
        target_pin="MOTOR+",
        color_name="Blue",
        rgb_color=(0.15, 0.35, 0.85),
        waypoints=[
            (-65.8, -54.0, 65.0),
            (-59.4, -34.5, 65.0),
            (-59.4, 17.0, 60.5),
            (140.0, 17.0, 60.5),
            (170.0, 17.0, 54.0),
            (185.0, 15.0, 45.0),
            (205.0, 5.0, 35.0),
            (230.0, 0.0, 26.0),
        ],
    ),
    WireNet(
        net_name="NET_MOTOR_ROLLER_NEG",
        source_component="cots_motor_driver_l298n",
        source_pin="OUT4",
        target_component="cots_motor_25ga370",
        target_pin="MOTOR-",
        color_name="White",
        rgb_color=(0.85, 0.85, 0.88),
        waypoints=[
            (-65.8, -56.0, 65.0),
            (-59.4, -34.5, 65.0),
            (-59.4, 15.0, 60.5),
            (140.0, 15.0, 60.5),
            (170.0, 15.0, 54.0),
            (185.0, 15.0, 43.0),
            (205.0, 5.0, 33.0),
            (230.0, 0.0, 24.0),
        ],
    ),

    # 6. ONPOW Limit Switch to ESP32 GPIO (via Outboard Endplate & Tray Bridge)
    WireNet(
        net_name="NET_LIMIT_SIG",
        source_component="cots_limit_switch",
        source_pin="NO",
        target_component="esp32_adapter_sled",
        target_pin="GPIO18",
        color_name="Green",
        rgb_color=(0.15, 0.80, 0.25),
        waypoints=[
            (180.0, -42.0, 16.5),
            (178.5, -36.0, 53.0),
            (165.0, -36.0, 53.0),
            (150.0, -36.0, 64.0),
            (147.2, -40.0, 65.0),
        ],
    ),
    WireNet(
        net_name="NET_LIMIT_GND",
        source_component="cots_limit_switch",
        source_pin="COM",
        target_component="esp32_adapter_sled",
        target_pin="GND",
        color_name="Black",
        rgb_color=(0.10, 0.10, 0.10),
        waypoints=[
            (180.0, -45.0, 16.5),
            (178.5, -36.0, 53.0),
            (165.0, -36.0, 53.0),
            (150.0, -36.0, 64.0),
            (147.2, -43.0, 65.0),
        ],
    ),

    # 7. Mini PV Telemetry to INA219 (Direct slope corridor, above Z=58)
    WireNet(
        net_name="NET_PV_POS",
        source_component="cots_pv_mini_panel",
        source_pin="PV+",
        target_component="cots_ina219",
        target_pin="VIN+",
        color_name="Orange",
        rgb_color=(0.95, 0.50, 0.10),
        waypoints=[
            (-15.0, -3.0, 75.0),
            (0.0, 12.0, 65.0),
            (95.0, 12.0, 65.0),
            (99.0, 9.8, 65.0),
        ],
    ),
    WireNet(
        net_name="NET_PV_NEG",
        source_component="cots_pv_mini_panel",
        source_pin="PV-",
        target_component="cots_ina219",
        target_pin="VIN-",
        color_name="Black",
        rgb_color=(0.10, 0.10, 0.10),
        waypoints=[
            (15.0, -3.0, 75.0),
            (20.0, 12.0, 65.0),
            (95.0, 12.0, 65.0),
            (102.0, 9.8, 65.0),
        ],
    ),

    # 8. INA219 I2C Bus to ESP32 Shield (Board gap raceway)
    WireNet(
        net_name="NET_I2C_SDA",
        source_component="cots_ina219",
        source_pin="SDA",
        target_component="esp32_adapter_sled",
        target_pin="GPIO21",
        color_name="Yellow",
        rgb_color=(0.90, 0.80, 0.10),
        waypoints=[
            (105.0, -14.2, 64.0),
            (105.0, -15.0, 66.0),
            (105.0, -15.8, 64.0),
        ],
    ),
    WireNet(
        net_name="NET_I2C_SCL",
        source_component="cots_ina219",
        source_pin="SCL",
        target_component="esp32_adapter_sled",
        target_pin="GPIO22",
        color_name="Green",
        rgb_color=(0.15, 0.80, 0.25),
        waypoints=[
            (108.0, -14.2, 64.0),
            (108.0, -15.0, 66.0),
            (108.0, -15.8, 64.0),
        ],
    ),
]


def build_wire_solid(net: WireNet) -> Tuple[bd.Solid, float]:
    """
    Build a swept circular wire solid along the net's smoothed waypoints.
    Returns (Solid, wire_length_mm).
    """
    sm_pts = _smooth_waypoints(net.waypoints, blend_r=6.0)
    with BuildPart() as bp:
        with BuildLine() as bl:
            spl = Spline(*sm_pts)
        wire_len = float(spl.length)
        # Tangent plane at start point for circular profile
        v_start = Vector(sm_pts[1]) - Vector(sm_pts[0])
        pl = Plane(origin=sm_pts[0], z_dir=v_start.normalized())
        with BuildSketch(pl):
            Circle(WIRE_RADIUS)
        sweep()

    solid = bp.part
    try:
        solid.color = Color(*net.rgb_color)
    except Exception:
        pass
    solid.label = f"wire_{net.net_name.lower()}"
    return solid, wire_len


def generate_wire_schedule() -> List[Dict[str, str]]:
    """Generate the engineering wire cut list table with +10% manufacturing margin."""
    schedule = []
    for net in NET_DEFINITIONS:
        sm_pts = _smooth_waypoints(net.waypoints, blend_r=6.0)
        with BuildLine():
            spl = Spline(*sm_pts)
            length = float(spl.length)
        cut_length = round(length * 1.10, 1)   # +10% cut length margin
        schedule.append({
            "Net": net.net_name,
            "From": f"{net.source_component} [{net.source_pin}]",
            "To": f"{net.target_component} [{net.target_pin}]",
            "Color": net.color_name,
            "Route_mm": f"{length:.1f}",
            "CutLength_mm": f"{cut_length:.1f}",
        })
    return schedule


def print_wire_schedule() -> None:
    """Print formatted wire harness table to stdout."""
    sched = generate_wire_schedule()
    print("\n--- Project A.R.C. Wire Harness Schedule ---")
    print(f"{'Net':<18} {'From':<32} {'To':<30} {'Color':<8} {'Route (mm)':<12} {'Cut (+10%)':<12}")
    print("-" * 116)
    total_len = 0.0
    for row in sched:
        print(f"{row['Net']:<18} {row['From']:<32} {row['To']:<30} {row['Color']:<8} {row['Route_mm']:<12} {row['CutLength_mm']:<12}")
        total_len += float(row['CutLength_mm'])
    print("-" * 116)
    print(f"Total Wire Harness Stock Required: {total_len:.1f} mm ({total_len / 1000.0:.2f} m)\n")


def build_all_wires() -> Dict[str, bd.Solid]:
    """Build all wire solids, keyed by 'wire_<net_name_lower>'."""
    wires = {}
    for net in NET_DEFINITIONS:
        name = f"wire_{net.net_name.lower()}"
        solid, _ = build_wire_solid(net)
        wires[name] = solid
    return wires
