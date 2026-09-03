"""
Main Entry Point for AI Smart Traffic Light Controller & Simulator.
"""

import argparse
import sys
import tkinter as tk

from traffic_ai.controller import ControlMode, TrafficController
from traffic_ai.intersection import Intersection
from traffic_ai.simulation import TrafficSimulation
from traffic_ai.vision_detector import VisionDetector
from gui.visualizer import TrafficVisualizer


def run_benchmark(steps: int = 1000):
    """Runs headless benchmark comparing AI Adaptive vs Fixed Timer mode."""
    print("==================================================")
    print("[*] RUNNING HEADLESS AI TRAFFIC BENCHMARK")
    print("==================================================")

    # 1. Test Fixed Timer
    inter_fixed = Intersection()
    ctrl_fixed = TrafficController(inter_fixed, mode=ControlMode.FIXED_TIMER)
    vision_fixed = VisionDetector()
    sim_fixed = TrafficSimulation(inter_fixed, ctrl_fixed, vision_fixed, spawn_rate=0.6)

    print(f"Executing Fixed Timer simulation ({steps} ticks)...")
    for _ in range(steps):
        sim_fixed.update(dt=0.1)

    fixed_passed = sim_fixed.total_passed
    fixed_delay = sim_fixed.get_average_wait_time()
    fixed_throughput = sim_fixed.get_throughput_rate()

    # 2. Test AI Adaptive
    inter_ai = Intersection()
    ctrl_ai = TrafficController(inter_ai, mode=ControlMode.AI_ADAPTIVE)
    vision_ai = VisionDetector()
    sim_ai = TrafficSimulation(inter_ai, ctrl_ai, vision_ai, spawn_rate=0.6)

    print(f"Executing AI Adaptive simulation ({steps} ticks)...")
    for _ in range(steps):
        sim_ai.update(dt=0.1)

    ai_passed = sim_ai.total_passed
    ai_delay = sim_ai.get_average_wait_time()
    ai_throughput = sim_ai.get_throughput_rate()

    print("\n--- BENCHMARK RESULTS ---")
    print(f"{'Metric':<25} | {'Fixed Timer':<15} | {'AI Adaptive':<15}")
    print("-" * 60)
    print(f"{'Vehicles Passed':<25} | {fixed_passed:<15} | {ai_passed:<15}")
    print(f"{'Throughput (veh/min)':<25} | {fixed_throughput:<15.1f} | {ai_throughput:<15.1f}")
    print(f"{'Average Delay (s/veh)':<25} | {fixed_delay:<15.2f} | {ai_delay:<15.2f}")
    
    improvement = ((fixed_delay - ai_delay) / max(0.01, fixed_delay)) * 100 if fixed_delay > 0 else 0
    print(f"\n[+] AI Adaptive Delay Reduction: {improvement:+.1f}%")
    print("==================================================")


def main():
    parser = argparse.ArgumentParser(description="AI Smart Traffic Light Simulation")
    parser.add_argument("--benchmark", action="store_true", help="Run headless benchmark comparison")
    parser.add_argument("--mode", choices=["ai", "fixed"], default="ai", help="Initial controller mode")
    args = parser.parse_args()

    if args.benchmark:
        run_benchmark()
        return

    # Graphical User Interface Mode
    intersection = Intersection(width=800, height=800, road_width=160)
    mode = ControlMode.AI_ADAPTIVE if args.mode == "ai" else ControlMode.FIXED_TIMER
    controller = TrafficController(intersection, mode=mode)
    vision = VisionDetector()
    simulation = TrafficSimulation(intersection, controller, vision, spawn_rate=0.5)

    root = tk.Tk()
    app = TrafficVisualizer(root, simulation)
    root.mainloop()


if __name__ == "__main__":
    main()
