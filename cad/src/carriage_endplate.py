"""
PROJECT A.R.C. – Carriage Endplate & Motor Clamps
==================================================
Re-exports from src.parts for backward compatibility.
"""

from __future__ import annotations
from src.parts.endplate import build_carriage_endplate
from src.parts.motor_clamp import build_n20_motor_clamp, build_25ga_motor_clamp

__all__ = [
    "build_carriage_endplate",
    "build_n20_motor_clamp",
    "build_25ga_motor_clamp",
]
