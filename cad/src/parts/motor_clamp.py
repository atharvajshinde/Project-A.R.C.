"""
PROJECT A.R.C. – Motor Clamps Module (src/parts/motor_clamp.py)
==============================================================
Re-exports the 25GA split clamp and N20 saddle clamp from src.parts.clamp.
"""

from __future__ import annotations
from src.parts.clamp import (
    build_25ga_motor_clamp,
    build_n20_motor_clamp,
    build_clamp,
)

__all__ = [
    "build_25ga_motor_clamp",
    "build_n20_motor_clamp",
    "build_clamp",
]
