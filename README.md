# 🚦 Smart AI Traffic Light Controller & Reality ANPR System (IBM Internship Project)

> **IBM Internship Project**: Real-time traffic light AI detection, accident-free adaptive signal control, and Automatic Number Plate Recognition (ANPR) with E-Challan enforcement developed by **Saif Ali Khan**.

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5.0+-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![AI-Powered](https://img.shields.io/badge/AI-Adaptive_Density-00B4D8?style=for-the-badge)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

An intelligent, real-time traffic management and enforcement system built in Python. Features dual-mode operation: **Accident-Free 4-Way Intersection Simulation** with dynamic AI signal scheduling, and **Reality Mode** leveraging OpenCV for real-world camera video processing, vehicle detection, and **ANPR License Plate Scanning with E-Challan generation and online payment**.

---

## 🌟 Key Features

### 1. 🛡️ Accident-Free Collision Prevention System
- **All-Red Clearance Interval (MUTCD Standard)**: Signals cycle `Green -> Yellow (3s) -> All-Red (2s) -> Next Green` so vehicles clearing the intersection never get T-boned by cross-traffic.
- **Junction Conflict Zone Lock**: Approaching vehicles yield at the stop line if perpendicular traffic is still occupying the center junction box.
- **Dynamic Safety Headway**: Adaptive car-following buffer ($18\text{px} + \text{speed} \times 3.5$) with strict position clamping to guarantee **0 collisions or overlapping**.

### 2. 📹 Dual Mode: Simulation & Reality Camera AI
- **Tab 1: 🚦 4-Way Intersection Simulator**:
  - Live top-down canvas with high-contrast asphalt, turn arrows, stop lines, zebra pedestrian crossings, and glowing traffic lights with digital countdowns.
  - Interactive controls: toggle between **AI Adaptive Mode** and **Fixed Timer Mode**, dispatch emergency vehicles, and adjust flow rates.
- **Tab 2: 📹 Reality Mode (OpenCV Camera & Video AI)**:
  - Real-time video processing supporting **Physical Webcam (0)**, **Video Files (`.mp4`, `.avi`)**, or the built-in **Live Expressway Stream**.
  - Object detection bounding boxes classifying **CARS**, **BUSES/TRUCKS**, and **BIKES**.
  - Virtual ANPR Camera scan line with live vehicle counter and speed calculation.

### 3. 🔍 ANPR License Plate Scanner & E-Challan Portal
- Every vehicle features realistic Indian registration plates (e.g. `DL-01-AB-1234`, `MH-02-CP-8921`, `UP-14-EA-4521`).
- **Automated Violation Detection**:
  - 🚨 **Red Light Jumping**: Auto-detects stop line breach during red signals and issues an instant e-challan.
  - ⚡ **Overspeeding**: Flags vehicles exceeding corridor speed limits.
- **Tab 3: E-Challan Portal**:
  - **Search Bar**: Look up any vehicle plate number to inspect vehicle model, registered owner, and active violations.
  - **Live Violations Feed**: Chronological log of issued citations with timestamps and fine amounts.
  - **💳 Online Fine Payment Simulator**: Select any pending challan and settle it instantly with a digital receipt ID!

---

## 🏗️ System Architecture

```
d:\class\project\
├── traffic_ai/
│   ├── __init__.py
│   ├── controller.py       # AI Traffic Controller (Adaptive timing, All-Red buffer, Emergency wave)
│   ├── intersection.py     # 4-way intersection geometry & conflict zone lock
│   ├── vehicle.py          # Vehicle kinematics, ANPR registration plates & violation flags
│   ├── simulation.py       # Accident-free physics engine & automated violation logger
│   ├── vision_detector.py  # Simulated vision telemetry & queue density estimation
│   ├── reality_detector.py # OpenCV video/camera AI, motion contours & live ANPR scanner
│   └── challan_manager.py  # E-Challan database, owner registry & online payment engine
├── gui/
│   ├── __init__.py
│   └── visualizer.py       # 3-Tab Tkinter application (Sim, Reality AI, E-Challan Portal)
├── tests/
│   └── test_traffic_ai.py  # Automated test suite (6/6 tests passing)
├── main.py                 # Application entry point
├── requirements.txt        # Dependencies (OpenCV, Pillow, NumPy)
├── upload_to_github.bat    # Windows 1-click GitHub push helper
├── upload_to_github.py     # GitHub sync script
├── .gitignore              # Git ignore rules
└── README.md               # Documentation
```

---

## 🚀 Getting Started

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
python main.py
```

### 3. Run the Headless AI Benchmark
```bash
python main.py --benchmark
```

### 4. Run Automated Unit Tests
```bash
python -m unittest discover -s tests
```

---

## 🎮 User Guide & Navigation

- **Tab 1: Simulation & AI Control**:
  - Click **"🚨 DISPATCH EMERGENCY AMBULANCE"** to watch the signals automatically preempt and grant a green wave.
  - Switch between **AI Adaptive** and **Fixed Timer** to observe congestion reduction.
- **Tab 2: Reality Mode**:
  - Switch between **Live Expressway Stream**, **Physical Webcam**, or **Load Video File**.
  - Watch the ANPR scanning line capture plates and display real-time fine alerts.
- **Tab 3: E-Challan Portal**:
  - Type or click any plate (e.g. `DL-01-AB-1234`, `MH-02-CP-8921`) and click **"🔎 Search Challan"**.
  - Select any pending violation row and click **"💳 Pay Selected Challan"** to simulate real-time settlement!

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
