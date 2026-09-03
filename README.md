# 🚦 Smart AI Traffic Light Controller & Simulator (IBM Internship Project)

> **IBM Internship Project**: Real-time traffic light AI detection & adaptive signal control system developed by **Saif Ali Khan**.

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![AI-Powered](https://img.shields.io/badge/AI-Adaptive_Density-00B4D8?style=for-the-badge)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

An intelligent, real-time traffic signal optimization system built in Python. Unlike traditional static round-robin timers, this system leverages **Computer Vision sensing and Adaptive Heuristic AI** to dynamically allocate green light durations based on real-time vehicle queue density, waiting times, and emergency vehicle preemption.

---

## 🌟 Key Features

- 🧠 **Dynamic AI Green Phase Allocation**:
  - Dynamically calculates the optimal green duration ($T_{green}$) based on approach queue lengths and vehicle delay times to eliminate empty-intersection waiting.
- 🚨 **Emergency Vehicle Preemption (Priority Wave)**:
  - Immediately detects emergency vehicles (ambulances/fire trucks) and triggers a priority green wave corridor.
- 🖥️ **Interactive Live Simulation Dashboard**:
  - High-performance top-down 4-way intersection canvas with realistic traffic lights, digital countdowns, and car-following physics.
  - Live telemetry displays: queue lengths per lane, throughput (vehicles/min), and average waiting delay.
  - Interactive controls: toggle between **AI Adaptive Mode** and **Fixed Timer Mode** in real time, spawn emergency vehicles, adjust traffic flow rates, and pause/resume.
- ⚡ **Headless Benchmark Engine**:
  - Built-in simulation benchmark comparing AI Adaptive vs. Fixed Timer mode (`python main.py --benchmark`). Demonstrates **~20%+ reduction in vehicle delays**!

---

## 🏗️ System Architecture

```
d:\class\project\
├── traffic_ai/
│   ├── __init__.py
│   ├── controller.py       # AI Traffic Controller (Adaptive dynamic green timer & phase scheduler)
│   ├── intersection.py     # 4-way intersection state machine (North, South, East, West)
│   ├── vehicle.py          # Vehicle entities & kinematics (Cars, Buses, Trucks, Bikes, Ambulances)
│   ├── simulation.py       # Traffic simulation engine & car-following physics
│   └── vision_detector.py  # Computer vision telemetry & density estimation module
├── gui/
│   ├── __init__.py
│   └── visualizer.py       # Tkinter GUI Visualizer & telemetry dashboard
├── tests/
│   └── test_traffic_ai.py  # Automated unit tests
├── main.py                 # Application launcher
├── requirements.txt        # Python dependencies
├── upload_to_github.bat    # Windows 1-click GitHub push helper
├── upload_to_github.py     # Cross-platform GitHub repository setup tool
├── .gitignore              # Git ignore rules
└── README.md               # Documentation
```

---

## 📐 AI Algorithm Formulation

### 1. Phase Demand Score
For an intersection phase $P \in \{\text{North-South}, \text{East-West}\}$:

$$\text{Demand}(P) = \sum_{d \in P} \left( 1.5 \cdot W_{\text{load}}(d) + 1.8 \cdot T_{\text{avg\_wait}}(d) + 2.5 \cdot N_{\text{waiting}}(d) \right)$$

Where:
- $W_{\text{load}}$: Weighted vehicle mass (Buses & Trucks carry higher weight).
- $T_{\text{avg\_wait}}$: Average stationary wait time in seconds.
- $N_{\text{waiting}}$: Number of stopped vehicles behind the stop line.

### 2. Optimal Green Time Calculation

$$T_{\text{green}} = \text{clamp}\left( T_{\min} + (2.0 \cdot N_{\max}) + (0.8 \cdot T_{\max\_wait}),\ T_{\min},\ T_{\max} \right)$$

- $T_{\min} = 6.0\text{s}$ (minimum clearance window).
- $T_{\max} = 28.0\text{s}$ (prevent starvation on cross street).
- Early clearance trigger: If current green phase has 0 waiting vehicles while cross phase has high demand, signal transitions to yellow immediately to maximize intersection capacity.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8+ installed
- Git installed

### 2. Installation
Clone the repository (or extract files) and install dependencies:

```bash
pip install -r requirements.txt
```

*(Note: Core GUI and simulation use standard Python libraries, so it runs out-of-the-box!)*

### 3. Running the Live Simulation
Launch the visual interactive simulator:

```bash
python main.py
```

### 4. Running the Benchmark (AI vs Fixed Timer)
Compare the AI Adaptive controller against classic fixed-timer scheduling in headless mode:

```bash
python main.py --benchmark
```

### 5. Running Automated Tests
```bash
python -m unittest discover -s tests
```

---

## 🎮 Simulation Controls & Dashboard

| Control | Description |
|---|---|
| **AI Adaptive (Smart)** | Real-time density-driven scheduling and early-phase clearing. |
| **Fixed Timer (Classic)** | Traditional 14-second fixed round-robin cycle. |
| **Dispatch Emergency Vehicle** | Injects an ambulance with emergency siren to demonstrate priority preemption. |
| **Traffic Flow Rate Slider** | Dynamically scales vehicle arrival rate from light traffic to rush hour gridlock. |
| **Pause / Resume** | Freezes simulation ticks for close inspection. |
| **Reset** | Flushes active vehicles and resets simulation statistics. |

---

## 📤 Uploading to GitHub

You can upload this project to your GitHub account in two simple ways:

### Option A: Using the Interactive Upload Script (Easiest)
Run:
```bash
python upload_to_github.py
```
Or double-click `upload_to_github.bat` on Windows. It will prompt you for your GitHub repository URL (e.g. `https://github.com/<your-username>/ai-traffic-light.git`) and automatically commit and push all code!

### Option B: Using Git Command Line
1. Create a new empty repository on [GitHub](https://github.com/new) (e.g., `ai-traffic-light`).
2. Run the following commands in your terminal:

```bash
git init
git add .
git commit -m "feat: initial release of AI smart traffic light controller"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY>.git
git push -u origin main
```

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
>>>>>>> 1977a73 (feat: AI smart traffic light controller and visual simulation)
