# Project A.R.C. (Autonomous Robotic Cleaner)
> **Autonomous Linear Traversing Robot for Dry-Dust Mitigation on Solar PV Modules & Precision Glass Testbeds**  
> *Developed for the Techfest Innovation Challenge*

---

## 🌟 Overview

**Project A.R.C.** is an autonomous robotic cleaner engineered to mitigate localized soiling and dry dust accumulation on photovoltaic (PV) solar panels and flat architectural glass surfaces. 

Traversing along dual **2020 V-slot aluminum guide rails** via a custom **3-wheel pinching gantry carriage**, the robot combines mechanical agitation with a plush microfiber roller drum and dry air mitigation to restore optical transmission and power harvesting efficiency without water waste.

```
       [ Dual N20 Drives ]       [ 25GA Roller Motor ]
               │                          │
               ▼                          ▼
 ═════════[ Motion Gantry ]════════════[ Roller ]═════════
       │                           ▲
       ▼                           │
 [ INA219 Telemetry ] ───► [ ESP32 FSM ] ───► [ Optical Dust Tracking ]
```

---

## 🚀 Key Engineering Highlights

* **Code-Driven Parametric CAD (`build123d`)**: Every physical component is modeled purely in Python using the `build123d` B-Rep kernel (`cad/src/`). The mechanical architecture is validated by **57 automated unit tests** enforcing geometric tolerances, non-collision bounds, and kinematic clearances.
* **Non-Blocking Embedded Firmware (`PlatformIO / C++17`)**: 5-state deterministic Finite State Machine (FSM: `IDLE` $\rightarrow$ `ACQUIRE` $\rightarrow$ `FORWARD` $\rightarrow$ `CLEAN` $\rightarrow$ `DOCK`) running on an ESP32 with hardware interrupt endstops, optical tachometer tracking, and INA219 I2C energy harvesting telemetry.
* **Interactive 3D Digital Twin (`Web / Three.js / Model-Viewer`)**: A self-contained, offline-first WebGL web portal (`web/index.html`) featuring real-time 3D orbital inspection, a 33-part scrubbable exploded view, physics sweep simulation, and direct CAD STEP/STL downloads.
* **Zero-Play 3-Wheel Gantry Kinematics**: 110 mm wide-stance carriage endplates riding twin 2020 V-slot tracks. Features an adjustable eccentric cam ($0.6\text{ mm}$ throw) on the bottom wheel to eliminate racking without binding.
* **Self-Sustaining Energy Budget**: Micro-power consumption profile verified by numerical energy harvest simulations ($E_{\text{in}} \gg E_{\text{out}}$ under daily 15-second sweep intervals).

---

## 📁 Repository Structure

```
Project A.R.C/
├── cad/                        # Parametric CAD source & exports
│   ├── src/                    # build123d Python modules (parts, COTS, assembly)
│   ├── tests/                  # Automated pytest geometric validation suite (57 tests)
│   ├── exports/                # Generated STEP, STL, GLB, and BOM CSV assets
│   ├── export_all.py           # Headless batch CAD export pipeline
│   └── manufacturing_manifest.md # Slicing & print parameters for PETG parts
├── docs/                       # Engineering specifications & papers
│   ├── ARC-MASTERDOC.pdf       # Compiled 15-page master engineering whitepaper
│   ├── ARC-MASTERDOC.tex       # LaTeX source code
│   └── OLL-INSTRUCTIONS.pdf    # Official competition guidelines
├── scripts/                    # Mission control & utilities
│   ├── arc_gui.py              # OpenCV Mission Control & real-time telemetry HUD
│   ├── vision_pipeline.py      # HSV dust tracking & centroid detection
│   ├── test_hardware.py        # Automated hardware-in-the-loop serial tester
│   ├── exploded.py             # CAD exploded assembly exporter
│   └── model-viewer.min.js     # Offline 3D WebGL viewer library
├── src/                        # Embedded firmware
│   └── main.cpp                # ESP32 C++17 non-blocking state machine & sensor loop
├── web/                        # Digital twin web experience
│   ├── index.html              # Apple-grade interactive 3D web presentation
│   └── assets/branding/        # Vector SVG logos, badges & sticker sheets
├── assembly_guide.md           # Step-by-step 4-module mechanical assembly guide
├── start_website.sh            # Local HTTP server launcher for the web experience
└── .gitignore                  # Clean repository ignore rules
```

---

## ⚡ Quickstart

### 1. View the Interactive 3D Digital Twin
Launch the local web server:
```bash
./start_website.sh
```
Or open `web/index.html` in any modern web browser supporting WebGL.

### 2. Run the CAD Geometry Tests
```bash
pytest cad/tests/
```
*Expected: 57 passed tests validating all component clearances and assembly datums.*

### 3. Rebuild CAD Artifacts (STEP / STL / GLB)
```bash
python cad/export_all.py
```

### 4. Flash ESP32 Firmware
```bash
pio run -t upload
```

---

## 📐 Mechanical Specifications

| Parameter | Specification | Notes |
| :--- | :--- | :--- |
| **Track Dimensions** | $20 \times 20 \times 600\text{ mm}$ (Y-axis) | 6063-T5 Silver Anodized V-Slot |
| **Carriage Wheelbase** | $110.0\text{ mm}$ Stance | $0.32$ span ratio (anti-racking) |
| **Roller Core** | $\varnothing 41.2\text{ mm}$ UPVC ($320\text{ mm}$ length) | Sleeved in 800 GSM plush microfiber |
| **Drive Motors** | Dual N20 Micro Gearmotors | 6V / 300 RPM direct-drive |
| **Roller Motor** | 25GA-370 DC Geared Motor | High torque, 12V nominal |
| **Main Controller** | ESP32-WROOM-32D (38-pin DevKit) | 240 MHz dual-core |
| **Power Storage** | 2S 18650 Li-ion ($7.4\text{V}$ nominal) | Integrated current/voltage sensing |

---

## 📄 Documentation

* The complete mathematical validations, dynamic torque margins, FSM transitions, and wiring schematics are documented in [`docs/ARC-MASTERDOC.pdf`](docs/ARC-MASTERDOC.pdf).
* Full mechanical build instructions broken into modular sessions are in [`assembly_guide.md`](assembly_guide.md).

---

## ⚖️ License & Attribution

Designed and engineered for the **Techfest Innovation Challenge**.  
All parametric CAD scripts, firmware, and presentation assets are released under open engineering practices.
