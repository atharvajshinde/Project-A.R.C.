"""
PROJECT A.R.C. – COTS: Fasteners Library
=========================================
Parametric B-Rep models for standard metric screws, nuts, washers, and set screws.
No cosmetic threads (per specification Rule 5).
"""

from __future__ import annotations
import math
import build123d as bd
from build123d import (
    BuildPart, BuildSketch,
    Cylinder, Box, Cone, extrude,
    Plane, Locations, Location, Vector, Mode, Align,
    Rectangle, Circle, RegularPolygon,
)

from .dims import (
    M3_SHCS_HEAD_D, M3_SHCS_HEAD_H, M3_SHCS_HEX,
    M3_BUTTON_HEAD_D, M3_BUTTON_HEAD_H,
    M5_BUTTON_HEAD_D, M5_BUTTON_HEAD_H,
    M3_HEX_NUT_AF, M3_HEX_NUT_H,
    M3_GRUB_D, M3_GRUB_L, M3_GRUB_HEX,
)

_FASTENER_CACHE = {}


def build_screw_shcs(thread_d: float, length: float) -> bd.Solid:
    """
    Build a DIN 912 / ISO 4762 Socket Head Cap Screw (SHCS).
    
    Coordinate frame:
      - Head sits above Z = 0 (Z in [0, head_h]).
      - Threaded shank extends into -Z (Z in [-length, 0]).
      - Centred on local origin in X-Y.
    """
    cache_key = ("shcs", thread_d, length)
    if cache_key in _FASTENER_CACHE:
        return _FASTENER_CACHE[cache_key].moved(Location())

    # Proportions based on standard DIN 912
    head_d = M3_SHCS_HEAD_D if abs(thread_d - 3.0) < 0.5 else thread_d * 1.8
    head_h = M3_SHCS_HEAD_H if abs(thread_d - 3.0) < 0.5 else thread_d
    hex_af = M3_SHCS_HEX if abs(thread_d - 3.0) < 0.5 else thread_d * 0.8
    hex_r = hex_af / 1.73205

    with BuildPart() as bp:
        # Head cylinder
        Cylinder(radius=head_d / 2.0, height=head_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Hex socket drive recess in top face
        with Locations((0.0, 0.0, head_h - thread_d * 0.5)):
            with BuildSketch(Plane.XY):
                RegularPolygon(radius=hex_r, side_count=6)
            extrude(amount=thread_d * 0.5 + 0.1, mode=Mode.SUBTRACT)
        # Threaded shank extending into -Z
        with Locations((0.0, 0.0, -length)):
            Cylinder(radius=thread_d / 2.0, height=length, align=(Align.CENTER, Align.CENTER, Align.MIN))

    solid = bp.part
    _FASTENER_CACHE[cache_key] = solid
    return solid.moved(Location())


def build_screw_button(thread_d: float, length: float) -> bd.Solid:
    """
    Build an ISO 7380 Button Head Hex Socket Screw.
    
    Coordinate frame:
      - Dome head sits above Z = 0 (Z in [0, head_h]).
      - Threaded shank extends into -Z (Z in [-length, 0]).
      - Centred on local origin in X-Y.
    """
    cache_key = ("button", thread_d, length)
    if cache_key in _FASTENER_CACHE:
        return _FASTENER_CACHE[cache_key].moved(Location())

    if abs(thread_d - 5.0) < 0.5:
        head_d = M5_BUTTON_HEAD_D
        head_h = M5_BUTTON_HEAD_H
        hex_af = 3.0
    elif abs(thread_d - 3.0) < 0.5:
        head_d = M3_BUTTON_HEAD_D
        head_h = M3_BUTTON_HEAD_H
        hex_af = 2.0
    else:
        head_d = thread_d * 1.9
        head_h = thread_d * 0.55
        hex_af = thread_d * 0.6
    hex_r = hex_af / 1.73205

    with BuildPart() as bp:
        # Dome head: chamfered/radiused cylinder approximation
        Cylinder(radius=head_d / 2.0, height=head_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Chamfer outer rim of head
        with Locations((0.0, 0.0, head_h / 2.0)):
            pass
        # Hex socket recess
        with Locations((0.0, 0.0, head_h - head_h * 0.6)):
            with BuildSketch(Plane.XY):
                RegularPolygon(radius=hex_r, side_count=6)
            extrude(amount=head_h * 0.6 + 0.1, mode=Mode.SUBTRACT)
        # Shank extending into -Z
        with Locations((0.0, 0.0, -length)):
            Cylinder(radius=thread_d / 2.0, height=length, align=(Align.CENTER, Align.CENTER, Align.MIN))

    solid = bp.part
    _FASTENER_CACHE[cache_key] = solid
    return solid.moved(Location())


def build_screw_selftap(thread_d: float, length: float) -> bd.Solid:
    """
    Build a pan-head self-tapping screw for plastic standoff pilots.
    
    Coordinate frame:
      - Head sits above Z = 0 (Z in [0, head_h]).
      - Shank extends into -Z (Z in [-length, 0]).
      - Centred on local origin in X-Y.
    """
    cache_key = ("selftap", thread_d, length)
    if cache_key in _FASTENER_CACHE:
        return _FASTENER_CACHE[cache_key].moved(Location())

    head_d = thread_d * 1.8
    head_h = thread_d * 0.6

    with BuildPart() as bp:
        # Rounded pan head
        Cylinder(radius=head_d / 2.0, height=head_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Cross-slot / phillips drive recess
        slot_w = 0.8
        slot_l = head_d * 0.7
        slot_dep = head_h * 0.6
        with Locations((0.0, 0.0, head_h - slot_dep)):
            Box(slot_l, slot_w, slot_dep + 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
            Box(slot_w, slot_l, slot_dep + 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # Shank
        with Locations((0.0, 0.0, -length)):
            Cylinder(radius=thread_d / 2.0, height=length, align=(Align.CENTER, Align.CENTER, Align.MIN))

    solid = bp.part
    _FASTENER_CACHE[cache_key] = solid
    return solid.moved(Location())


def build_nut_hex(thread_d: float) -> bd.Solid:
    """
    Build a DIN 934 Standard Hexagon Nut.
    
    Coordinate frame:
      - Centred at origin in X-Y.
      - Thickness along Z: Z in [0, nut_h].
      - Thread through-bore along Z.
    """
    cache_key = ("nut", thread_d)
    if cache_key in _FASTENER_CACHE:
        return _FASTENER_CACHE[cache_key].moved(Location())

    if abs(thread_d - 3.0) < 0.5:
        af = M3_HEX_NUT_AF
        nut_h = M3_HEX_NUT_H
    elif abs(thread_d - 5.0) < 0.5:
        af = 8.0
        nut_h = 4.0
    else:
        af = thread_d * 1.8
        nut_h = thread_d * 0.8
    hex_r = af / 1.73205

    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            RegularPolygon(radius=hex_r, side_count=6)
        extrude(amount=nut_h)
        # Thread bore
        with Locations((0.0, 0.0, -0.5)):
            Cylinder(radius=thread_d / 2.0, height=nut_h + 1.0, mode=Mode.SUBTRACT)

    solid = bp.part
    _FASTENER_CACHE[cache_key] = solid
    return solid.moved(Location())


def build_washer(inner_d: float, outer_d: float, thickness: float) -> bd.Solid:
    """
    Build a flat washer (DIN 125).
    
    Coordinate frame:
      - Centred at origin in X-Y.
      - Thickness along Z: Z in [0, thickness].
    """
    cache_key = ("washer", inner_d, outer_d, thickness)
    if cache_key in _FASTENER_CACHE:
        return _FASTENER_CACHE[cache_key].moved(Location())

    with BuildPart() as bp:
        Cylinder(radius=outer_d / 2.0, height=thickness, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((0.0, 0.0, -0.5)):
            Cylinder(radius=inner_d / 2.0, height=thickness + 1.0, mode=Mode.SUBTRACT)

    solid = bp.part
    _FASTENER_CACHE[cache_key] = solid
    return solid.moved(Location())


def build_vwheel_axle_fastener(thread_d: float = 5.0, length: float = 11.0) -> bd.Solid:
    """
    Build an M5 wheel axle fastener terminating with standard M5 flat washer
    and DIN 985 nylon locknut against the wheel bearings.
    """
    cache_key = ("vwheel_axle_fastener", thread_d, length)
    if cache_key in _FASTENER_CACHE:
        return _FASTENER_CACHE[cache_key].moved(Location())

    bolt = build_screw_button(thread_d, length)
    washer = build_washer(inner_d=5.3, outer_d=10.0, thickness=1.0).moved(Location((0.0, 0.0, -6.4)))
    nut = build_nut_hex(thread_d).moved(Location((0.0, 0.0, -10.4)))
    solid = bolt.fuse(washer).fuse(nut)
    _FASTENER_CACHE[cache_key] = solid
    return solid.moved(Location())


def build_clamp_bolt_fastener(thread_d: float = 3.0, length: float = 12.0) -> bd.Solid:
    """
    DIN 912 M3 socket head cap screw terminating with standard M3 hex nut.
    """
    cache_key = ("clamp_bolt_fastener", thread_d, length)
    if cache_key in _FASTENER_CACHE:
        return _FASTENER_CACHE[cache_key].moved(Location())

    bolt = build_screw_shcs(thread_d, length)
    nut = build_nut_hex(thread_d).moved(Location((0.0, 0.0, -10.0)))
    solid = bolt.fuse(nut)
    _FASTENER_CACHE[cache_key] = solid
    return solid.moved(Location())

