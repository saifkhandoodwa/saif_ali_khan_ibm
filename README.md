# 🚦 Real AI Traffic Vision, ANPR Plate Scanner & E-Challan System (IBM Internship Project)

> **IBM Internship Project**: Real-time Computer Vision traffic detection, Camera-Driven Adaptive Traffic Light Control, and Automatic Number Plate Recognition (ANPR) with E-Challan Enforcement developed by **Saif Ali Khan**.

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5.0+-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![AI-Powered](https://img.shields.io/badge/AI-Computer_Vision-00B4D8?style=for-the-badge)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

A production-grade, 100% real-world traffic management application. Eliminates toy/cartoon simulations and focuses directly on **Live Camera Feeds, Computer Vision Vehicle Detection, Dynamic Signal Timing, ANPR License Plate Recognition, and E-Challan Enforcement**.

---

## 🌟 Key Features

### 1. 📹 Live AI Traffic Camera & Computer Vision
- Ingests video from:
  - 📷 **Physical Webcams & USB Traffic Cameras (Device 0, 1)**
  - 📂 **Traffic Video Files (`.mp4`, `.avi`, `.mov`)**
  - 🛣️ **High-Definition Live Expressway Stream**
  - 🖼️ **Traffic Photos & Snapshots**
- **AI Object Detection**: Real-time bounding boxes classifying **CARS**, **BUSES/TRUCKS**, **BIKES**, and **EMERGENCY VEHICLES** with live speed estimation ($km/h$).

### 2. 🚦 Camera-Driven Smart Traffic Light Signal
- Real-time Traffic Signal Head mounted on the camera HUD (RED, YELLOW, GREEN).
- **Camera-Driven Adaptation**:
  - Green light timer dynamically expands when the camera detects heavy queues.
  - Signal cycles early to yellow and red when the approach lane clears.
  - Emergency ambulance dispatch button activates an instant green corridor.

### 3. 🔍 ANPR Automatic Number Plate Recognition
- Virtual Sensor Line on the roadway automatically detects approaching vehicles.
- Crops license plate regions and extracts registration numbers (e.g. `DL-01-AB-1234`, `MH-02-CP-8921`, `UP-14-EA-4521`).
- Displays live scanned plates with owner information, vehicle model, and active fines.

### 4. 💳 E-Challan Enforcement & Online Payment Portal
- **Automated Violation Detection**:
  - 🚨 **Red Light Jumping**: Auto-captures stop line breaches during RED signals and issues citations.
  - ⚡ **Overspeeding**: Flags vehicles exceeding speed limits.
- **Searchable Vehicle Registry**: Search any vehicle plate number to inspect owner details, RTO city, contact info, and pending fines.
- **Online Payment Simulator**: Settle pending challans online with instant receipt generation and digital transaction IDs.

---

## 🏗️ System Architecture

```
d:\class\project\
├── traffic_ai/
│   ├── __init__.py
│   ├── vision_pipeline.py  # Video ingestion, AI vehicle tracking, and camera-driven signal timing
│   ├── anpr_engine.py      # License plate detection, morphological filtering & OCR recognition
│   └── challan_manager.py  # E-Challan database, owner registry & online payment engine
├── gui/
│   ├── __init__.py
│   └── real_app.py         # Modern Dark-Mode GUI (Live Camera AI & E-Challan Portal)
├── tests/
│   └── test_traffic_ai.py  # Automated unit & integration tests
├── main.py                 # Application launcher
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

### 2. Run the Application
```bash
python main.py
```

### 3. Optional Command-Line Arguments
```bash
# Start directly with physical webcam:
python main.py --webcam

# Process a traffic video file:
python main.py --video path/to/traffic_video.mp4

# Inspect a traffic photo:
python main.py --image path/to/cars.jpg
```

### 4. Run Automated Tests
```bash
python -m unittest discover -s tests
```

---

## 🎮 Navigation & User Guide

- **Tab 1: Live AI Camera & Traffic Signal Control**:
  - Watch real-time AI bounding boxes, speed metrics, and stop line detections.
  - Observe the smart traffic light timer adapt in real-time to the number of vehicles in view.
  - Click **"🚨 DISPATCH AMBULANCE"** to trigger priority signal preemption.
- **Tab 2: ANPR Number Plate Scanner & E-Challan Portal**:
  - Enter any plate number (e.g. `DL-01-AB-1234`, `MH-02-CP-8921`) and click **"🔎 Search Challan"**.
  - Select any pending violation row and click **"💳 Pay Selected Challan"** to settle fines online!

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
