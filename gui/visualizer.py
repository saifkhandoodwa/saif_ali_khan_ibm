"""
Interactive Traffic Light Simulation GUI using Tkinter.
Includes real-time intersection rendering, signal countdowns,
AI telemetry dashboard, and simulation controls.
"""

import math
import time
import tkinter as tk
from tkinter import ttk
from typing import Dict

from traffic_ai.controller import ControlMode, TrafficController
from traffic_ai.intersection import Intersection, LightState, TrafficPhase
from traffic_ai.simulation import TrafficSimulation
from traffic_ai.vehicle import Direction, Vehicle, VehicleType
from traffic_ai.vision_detector import LaneTelemetry


class TrafficVisualizer:
    """Main Application Window for AI Traffic Light Simulation."""

    def __init__(self, root: tk.Tk, simulation: TrafficSimulation):
        self.root = root
        self.sim = simulation
        self.intersection = simulation.intersection
        self.controller = simulation.controller

        self.root.title("AI Smart Traffic Light Controller & Simulation")
        self.root.geometry("1260x860")
        self.root.minsize(1100, 780)
        self.root.configure(bg="#0f172a")

        # Color Palette
        self.BG_DARK = "#0f172a"
        self.PANEL_BG = "#1e293b"
        self.CARD_BG = "#334155"
        self.ACCENT_BLUE = "#38bdf8"
        self.ACCENT_GREEN = "#22c55e"
        self.ACCENT_RED = "#ef4444"
        self.ACCENT_YELLOW = "#f59e0b"
        self.TEXT_PRIMARY = "#f8fafc"
        self.TEXT_SECONDARY = "#94a3b8"

        self.lane_centers = {
            Direction.NORTH: 440,
            Direction.SOUTH: 360,
            Direction.WEST: 440,
            Direction.EAST: 360,
        }

        self.sim_speed = 1.0
        self.last_frame_time = time.time()
        self.fps_counter = 0
        self.current_fps = 0
        self.fps_timer = time.time()

        self._create_layout()
        self._animate()

    def _create_layout(self):
        """Constructs split-pane layout: Left Canvas, Right Analytics & Controls."""
        # Top Header Bar
        header = tk.Frame(self.root, bg="#1e293b", height=50)
        header.pack(fill=tk.X, side=tk.TOP)

        title_lbl = tk.Label(
            header,
            text="🚦 AI SMART TRAFFIC LIGHT OPTIMIZER",
            font=("Segoe UI", 16, "bold"),
            fg=self.TEXT_PRIMARY,
            bg="#1e293b",
            padx=16,
            pady=8,
        )
        title_lbl.pack(side=tk.LEFT)

        status_lbl = tk.Label(
            header,
            text="● LIVE SIMULATION",
            font=("Segoe UI", 10, "bold"),
            fg=self.ACCENT_GREEN,
            bg="#1e293b",
            padx=16,
        )
        status_lbl.pack(side=tk.RIGHT)

        # Main Body Container
        main_body = tk.Frame(self.root, bg=self.BG_DARK)
        main_body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Left: Simulation Canvas Container
        canvas_frame = tk.Frame(main_body, bg=self.PANEL_BG, bd=2, relief=tk.FLAT)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.canvas = tk.Canvas(
            canvas_frame,
            width=800,
            height=800,
            bg="#111827",
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Right: Dashboard & Control Panel
        sidebar = tk.Frame(main_body, bg=self.PANEL_BG, width=420)
        sidebar.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(0, 0))
        sidebar.pack_propagate(False)

        self._build_sidebar(sidebar)

    def _build_sidebar(self, parent: tk.Frame):
        """Builds controls, live metrics, and AI decision terminal."""
        # Scrollable container for sidebar if screen is small
        container = tk.Frame(parent, bg=self.PANEL_BG)
        container.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        # 1. Mode Selector Card
        mode_card = tk.LabelFrame(
            container,
            text=" CONTROLLER MODE ",
            font=("Segoe UI", 10, "bold"),
            fg=self.ACCENT_BLUE,
            bg=self.CARD_BG,
            bd=1,
            padx=10,
            pady=8,
        )
        mode_card.pack(fill=tk.X, pady=(0, 10))

        self.mode_var = tk.StringVar(value=self.controller.mode.value)
        ai_rb = tk.Radiobutton(
            mode_card,
            text="🟢 AI Adaptive (Dynamic Density)",
            variable=self.mode_var,
            value=ControlMode.AI_ADAPTIVE.value,
            command=self._on_mode_change,
            font=("Segoe UI", 10, "bold"),
            fg=self.TEXT_PRIMARY,
            bg=self.CARD_BG,
            selectcolor="#1e293b",
            activebackground=self.CARD_BG,
        )
        ai_rb.pack(anchor=tk.W, pady=2)

        fixed_rb = tk.Radiobutton(
            mode_card,
            text="🔵 Fixed Timer (14s Round-Robin)",
            variable=self.mode_var,
            value=ControlMode.FIXED_TIMER.value,
            command=self._on_mode_change,
            font=("Segoe UI", 10),
            fg=self.TEXT_SECONDARY,
            bg=self.CARD_BG,
            selectcolor="#1e293b",
            activebackground=self.CARD_BG,
        )
        fixed_rb.pack(anchor=tk.W, pady=2)

        # 2. Emergency Quick Action
        em_btn = tk.Button(
            container,
            text="🚨 DISPATCH EMERGENCY VEHICLE",
            command=self._trigger_emergency,
            font=("Segoe UI", 11, "bold"),
            fg="white",
            bg="#dc2626",
            activebackground="#b91c1c",
            activeforeground="white",
            bd=0,
            padx=10,
            pady=8,
            cursor="hand2",
        )
        em_btn.pack(fill=tk.X, pady=(0, 10))

        # 3. Live Phase & Signal Telemetry Card
        phase_card = tk.LabelFrame(
            container,
            text=" ACTIVE SIGNAL PHASE ",
            font=("Segoe UI", 10, "bold"),
            fg=self.ACCENT_BLUE,
            bg=self.CARD_BG,
            bd=1,
            padx=10,
            pady=8,
        )
        phase_card.pack(fill=tk.X, pady=(0, 10))

        self.phase_lbl = tk.Label(
            phase_card,
            text="NORTH-SOUTH CORRIDOR",
            font=("Segoe UI", 12, "bold"),
            fg=self.ACCENT_GREEN,
            bg=self.CARD_BG,
        )
        self.phase_lbl.pack(anchor=tk.W)

        self.timer_lbl = tk.Label(
            phase_card,
            text="Time Remaining: 00.0s",
            font=("Consolas", 14, "bold"),
            fg=self.TEXT_PRIMARY,
            bg=self.CARD_BG,
        )
        self.timer_lbl.pack(anchor=tk.W, pady=(4, 0))

        # 4. Lane Density Telemetry
        density_card = tk.LabelFrame(
            container,
            text=" VISION SENSOR TELEMETRY ",
            font=("Segoe UI", 10, "bold"),
            fg=self.ACCENT_BLUE,
            bg=self.CARD_BG,
            bd=1,
            padx=10,
            pady=8,
        )
        density_card.pack(fill=tk.X, pady=(0, 10))

        self.lane_labels: Dict[Direction, tk.Label] = {}
        for d in Direction:
            row = tk.Frame(density_card, bg=self.CARD_BG)
            row.pack(fill=tk.X, pady=2)
            name_lbl = tk.Label(
                row,
                text=f"{d.value:5s}:",
                font=("Consolas", 9, "bold"),
                fg=self.TEXT_SECONDARY,
                bg=self.CARD_BG,
                width=6,
                anchor=tk.W,
            )
            name_lbl.pack(side=tk.LEFT)

            val_lbl = tk.Label(
                row,
                text="0 vehicles | 0% density",
                font=("Segoe UI", 9),
                fg=self.TEXT_PRIMARY,
                bg=self.CARD_BG,
                anchor=tk.W,
            )
            val_lbl.pack(side=tk.LEFT, padx=6)
            self.lane_labels[d] = val_lbl

        # 5. Global Metrics Card
        metrics_card = tk.LabelFrame(
            container,
            text=" SYSTEM METRICS ",
            font=("Segoe UI", 10, "bold"),
            fg=self.ACCENT_BLUE,
            bg=self.CARD_BG,
            bd=1,
            padx=10,
            pady=8,
        )
        metrics_card.pack(fill=tk.X, pady=(0, 10))

        self.throughput_lbl = tk.Label(
            metrics_card,
            text="Throughput: 0.0 veh/min",
            font=("Segoe UI", 10),
            fg=self.TEXT_PRIMARY,
            bg=self.CARD_BG,
        )
        self.throughput_lbl.pack(anchor=tk.W, pady=1)

        self.avg_wait_lbl = tk.Label(
            metrics_card,
            text="Avg Delay: 0.0s",
            font=("Segoe UI", 10),
            fg=self.TEXT_PRIMARY,
            bg=self.CARD_BG,
        )
        self.avg_wait_lbl.pack(anchor=tk.W, pady=1)

        self.total_passed_lbl = tk.Label(
            metrics_card,
            text="Total Passed: 0",
            font=("Segoe UI", 10),
            fg=self.TEXT_PRIMARY,
            bg=self.CARD_BG,
        )
        self.total_passed_lbl.pack(anchor=tk.W, pady=1)

        # 6. Controls (Speed & Spawn Rate)
        controls_card = tk.LabelFrame(
            container,
            text=" SIMULATION CONTROLS ",
            font=("Segoe UI", 10, "bold"),
            fg=self.ACCENT_BLUE,
            bg=self.CARD_BG,
            bd=1,
            padx=10,
            pady=6,
        )
        controls_card.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            controls_card,
            text="Traffic Flow Rate:",
            font=("Segoe UI", 9),
            fg=self.TEXT_SECONDARY,
            bg=self.CARD_BG,
        ).pack(anchor=tk.W)

        self.spawn_slider = ttk.Scale(
            controls_card,
            from_=0.1,
            to=1.2,
            value=self.sim.spawn_rate,
            orient=tk.HORIZONTAL,
            command=self._on_spawn_change,
        )
        self.spawn_slider.pack(fill=tk.X, pady=(2, 6))

        btn_row = tk.Frame(controls_card, bg=self.CARD_BG)
        btn_row.pack(fill=tk.X)

        self.pause_btn = tk.Button(
            btn_row,
            text="⏸ Pause",
            command=self._toggle_pause,
            font=("Segoe UI", 9, "bold"),
            fg=self.TEXT_PRIMARY,
            bg="#475569",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        self.pause_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        clear_btn = tk.Button(
            btn_row,
            text="🔄 Reset",
            command=self._reset_sim,
            font=("Segoe UI", 9, "bold"),
            fg=self.TEXT_PRIMARY,
            bg="#475569",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        clear_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(4, 0))

        # 7. AI Decision Log Terminal
        log_card = tk.LabelFrame(
            container,
            text=" AI DECISION LOG ",
            font=("Segoe UI", 10, "bold"),
            fg=self.ACCENT_BLUE,
            bg=self.CARD_BG,
            bd=1,
            padx=6,
            pady=4,
        )
        log_card.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_card,
            height=6,
            bg="#090d16",
            fg="#38bdf8",
            font=("Consolas", 8),
            bd=0,
            wrap=tk.WORD,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _on_mode_change(self):
        val = self.mode_var.get()
        if val == ControlMode.AI_ADAPTIVE.value:
            self.controller.mode = ControlMode.AI_ADAPTIVE
        else:
            self.controller.mode = ControlMode.FIXED_TIMER

    def _trigger_emergency(self):
        self.sim.trigger_emergency_vehicle()

    def _on_spawn_change(self, val):
        self.sim.spawn_rate = float(val)

    def _toggle_pause(self):
        self.sim.is_paused = not self.sim.is_paused
        self.pause_btn.config(text="▶ Resume" if self.sim.is_paused else "⏸ Pause")

    def _reset_sim(self):
        for d in Direction:
            self.sim.vehicles[d].clear()
        self.sim.total_passed = 0
        self.sim.total_spawned = 0
        self.sim.completed_wait_times.clear()
        self.sim.sim_elapsed = 0.0
        self.controller.phase_time_elapsed = 0.0

    def _animate(self):
        """Simulation and render frame loop (~40 FPS)."""
        now = time.time()
        dt = min(0.08, now - self.last_frame_time)
        self.last_frame_time = now

        # Update simulation physics & AI
        self.sim.update(dt)

        # Render frame
        self._draw_intersection()
        self._draw_traffic_lights()
        self._draw_vehicles()
        self._update_sidebar_telemetry()

        # Target ~40 ms per tick
        self.root.after(30, self._animate)

    def _draw_intersection(self):
        """Draws top-down roads, lanes, curbs, crosswalks, and markings."""
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100:
            w, h = 800, 800

        cx, cy = w / 2.0, h / 2.0
        rw = self.intersection.road_width

        # 1. Background Grass / Concrete
        self.canvas.create_rectangle(0, 0, w, h, fill="#0f172a", outline="")

        # 2. Roads (Asphalt Dark Grey)
        # Vertical Road
        self.canvas.create_rectangle(cx - rw / 2, 0, cx + rw / 2, h, fill="#1e293b", outline="")
        # Horizontal Road
        self.canvas.create_rectangle(0, cy - rw / 2, w, cy + rw / 2, fill="#1e293b", outline="")

        # 3. Road Borders / Curbs
        border_col = "#475569"
        self.canvas.create_line(cx - rw / 2, 0, cx - rw / 2, cy - rw / 2, fill=border_col, width=2)
        self.canvas.create_line(0, cy - rw / 2, cx - rw / 2, cy - rw / 2, fill=border_col, width=2)

        self.canvas.create_line(cx + rw / 2, 0, cx + rw / 2, cy - rw / 2, fill=border_col, width=2)
        self.canvas.create_line(cx + rw / 2, cy - rw / 2, w, cy - rw / 2, fill=border_col, width=2)

        self.canvas.create_line(cx - rw / 2, h, cx - rw / 2, cy + rw / 2, fill=border_col, width=2)
        self.canvas.create_line(0, cy + rw / 2, cx - rw / 2, cy + rw / 2, fill=border_col, width=2)

        self.canvas.create_line(cx + rw / 2, h, cx + rw / 2, cy + rw / 2, fill=border_col, width=2)
        self.canvas.create_line(cx + rw / 2, cy + rw / 2, w, cy + rw / 2, fill=border_col, width=2)

        # 4. Yellow Center Dividers (Dashed)
        dash = (10, 10)
        yellow_col = "#eab308"
        self.canvas.create_line(cx, 0, cx, cy - rw / 2, fill=yellow_col, width=2, dash=dash)
        self.canvas.create_line(cx, cy + rw / 2, cx, h, fill=yellow_col, width=2, dash=dash)
        self.canvas.create_line(0, cy, cx - rw / 2, cy, fill=yellow_col, width=2, dash=dash)
        self.canvas.create_line(cx + rw / 2, cy, w, cy, fill=yellow_col, width=2, dash=dash)

        # 5. Stop Lines (Solid White)
        white_col = "#f8fafc"
        stop_offset = rw / 2 + 10
        # North incoming stop line (right lane: cx to cx + rw/2)
        self.canvas.create_line(cx, cy - stop_offset, cx + rw / 2, cy - stop_offset, fill=white_col, width=4)
        # South incoming stop line (left lane: cx - rw/2 to cx)
        self.canvas.create_line(cx - rw / 2, cy + stop_offset, cx, cy + stop_offset, fill=white_col, width=4)
        # West incoming stop line (bottom lane: cy to cy + rw/2)
        self.canvas.create_line(cx - stop_offset, cy, cx - stop_offset, cy + rw / 2, fill=white_col, width=4)
        # East incoming stop line (top lane: cy - rw/2 to cy)
        self.canvas.create_line(cx + stop_offset, cy - rw / 2, cx + stop_offset, cy, fill=white_col, width=4)

        # 6. Zebra Crossings (Walkways)
        self._draw_crosswalk(cx - rw / 2, cy - rw / 2 - 24, rw, 14, horizontal=True)
        self._draw_crosswalk(cx - rw / 2, cy + rw / 2 + 10, rw, 14, horizontal=True)
        self._draw_crosswalk(cx - rw / 2 - 24, cy - rw / 2, 14, rw, horizontal=False)
        self._draw_crosswalk(cx + rw / 2 + 10, cy - rw / 2, 14, rw, horizontal=False)

        # 7. AI Vision Detection Zone Indicators (Light blue HUD border)
        self._draw_detection_zones(cx, cy, rw)

    def _draw_crosswalk(self, x: float, y: float, w: float, h: float, horizontal: bool):
        """Draws striped zebra crossing."""
        if horizontal:
            stripes = 8
            sw = w / stripes
            for i in range(stripes):
                if i % 2 == 0:
                    self.canvas.create_rectangle(x + i * sw, y, x + (i + 1) * sw, y + h, fill="#cbd5e1", outline="")
        else:
            stripes = 8
            sh = h / stripes
            for i in range(stripes):
                if i % 2 == 0:
                    self.canvas.create_rectangle(x, y + i * sh, x + w, y + (i + 1) * sh, fill="#cbd5e1", outline="")

    def _draw_detection_zones(self, cx: float, cy: float, rw: float):
        """Subtle HUD indicators denoting camera sensing field of view."""
        hud_col = "#0284c7"
        self.canvas.create_text(
            cx, cy, text="AI SMART INTERSECTION", font=("Consolas", 10, "bold"), fill="#334155"
        )

    def _draw_traffic_lights(self):
        """Renders 4 traffic signal heads with glowing lights and countdown timers."""
        cx = 400
        cy = 400
        rw = self.intersection.road_width
        rem_time = self.controller.get_remaining_time()

        # Signal Gantry coordinate anchors
        gantries = {
            Direction.NORTH: (cx + rw / 2 + 20, cy - rw / 2 - 25),
            Direction.SOUTH: (cx - rw / 2 - 50, cy + rw / 2 + 10),
            Direction.WEST: (cx - rw / 2 - 25, cy + rw / 2 + 35),
            Direction.EAST: (cx + rw / 2 + 10, cy - rw / 2 - 50),
        }

        for direction, (gx, gy) in gantries.items():
            state = self.intersection.get_light(direction)
            self._render_signal_box(gx, gy, state, rem_time)

    def _render_signal_box(self, x: float, y: float, state: LightState, rem_time: float):
        """Renders a single 3-aspect traffic light fixture."""
        bw, bh = 26, 68
        self.canvas.create_rectangle(x, y, x + bw, y + bh, fill="#0f172a", outline="#64748b", width=1.5)

        # Red, Yellow, Green bulbs
        r_col = "#ef4444" if state == LightState.RED else "#3b0c0c"
        y_col = "#f59e0b" if state == LightState.YELLOW else "#3b2e0c"
        g_col = "#22c55e" if state == LightState.GREEN else "#0c3b1e"

        # Bulb radiuses
        br = 7
        cx = x + bw / 2
        self.canvas.create_oval(cx - br, y + 12 - br, cx + br, y + 12 + br, fill=r_col, outline="")
        self.canvas.create_oval(cx - br, y + 34 - br, cx + br, y + 34 + br, fill=y_col, outline="")
        self.canvas.create_oval(cx - br, y + 56 - br, cx + br, y + 56 + br, fill=g_col, outline="")

        # Countdown display
        if state in (LightState.GREEN, LightState.YELLOW):
            self.canvas.create_text(
                cx, y - 8,
                text=f"{int(rem_time)}s",
                font=("Consolas", 8, "bold"),
                fill="#38bdf8",
            )

    def _draw_vehicles(self):
        """Renders vehicles with orientation, lights, and emergency animations."""
        for direction, lane in self.sim.vehicles.items():
            lane_coord = self.lane_centers[direction]
            
            for v in lane:
                length, width = v.length, v.width

                if direction == Direction.NORTH:
                    # travels vertically down (pos is y)
                    x1 = lane_coord - width / 2
                    x2 = lane_coord + width / 2
                    y1 = v.position - length / 2
                    y2 = v.position + length / 2
                    self._draw_single_vehicle(v, x1, y1, x2, y2, heading="DOWN")

                elif direction == Direction.SOUTH:
                    # travels vertically up (pos is y)
                    x1 = lane_coord - width / 2
                    x2 = lane_coord + width / 2
                    y1 = v.position - length / 2
                    y2 = v.position + length / 2
                    self._draw_single_vehicle(v, x1, y1, x2, y2, heading="UP")

                elif direction == Direction.WEST:
                    # travels horizontally right (pos is x)
                    x1 = v.position - length / 2
                    x2 = v.position + length / 2
                    y1 = lane_coord - width / 2
                    y2 = lane_coord + width / 2
                    self._draw_single_vehicle(v, x1, y1, x2, y2, heading="RIGHT")

                elif direction == Direction.EAST:
                    # travels horizontally left (pos is x)
                    x1 = v.position - length / 2
                    x2 = v.position + length / 2
                    y1 = lane_coord - width / 2
                    y2 = lane_coord + width / 2
                    self._draw_single_vehicle(v, x1, y1, x2, y2, heading="LEFT")

    def _draw_single_vehicle(self, v: Vehicle, x1: float, y1: float, x2: float, y2: float, heading: str):
        """Draws styled vehicle body, windows, headlights, and flashing beacons."""
        # Vehicle chassis
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=v.color, outline="#1e293b", width=1)

        # Windshield / Roof highlight
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        rw = (x2 - x1) * 0.6
        rh = (y2 - y1) * 0.6
        self.canvas.create_rectangle(mx - rw / 2, my - rh / 2, mx + rw / 2, my + rh / 2, fill="#0f172a", outline="")

        # Emergency Siren Beacon
        if v.is_emergency:
            siren_color = "#ef4444" if int(v.siren_phase * 10) % 2 == 0 else "#38bdf8"
            self.canvas.create_oval(mx - 4, my - 4, mx + 4, my + 4, fill=siren_color, outline="white", width=1)
            # Pulse glow ring
            self.canvas.create_oval(mx - 10, my - 10, mx + 10, my + 10, outline=siren_color, width=1)

    def _update_sidebar_telemetry(self):
        """Updates right-side metrics, lane queues, and AI decision console."""
        # 1. Active Phase
        is_ns = self.controller.active_phase == TrafficPhase.NORTH_SOUTH
        self.phase_lbl.config(
            text="NORTH-SOUTH CORRIDOR" if is_ns else "EAST-WEST CORRIDOR",
            fg=self.ACCENT_GREEN if self.controller.light_state == LightState.GREEN else self.ACCENT_YELLOW,
        )

        rem = self.controller.get_remaining_time()
        self.timer_lbl.config(text=f"Phase Remaining: {rem:04.1f}s ({self.controller.light_state.value})")

        # 2. Lane Vision Telemetry
        telemetry = self.sim.vision.get_intersection_snapshot(
            self.sim.vehicles, self.intersection.stop_positions
        )
        for d in Direction:
            t = telemetry[d]
            em_tag = " [🚨EM]" if t.emergency_present else ""
            self.lane_labels[d].config(
                text=f"{t.vehicle_count} veh (Wait: {t.avg_wait_time:.1f}s){em_tag}",
                fg=self.ACCENT_RED if t.emergency_present else self.TEXT_PRIMARY,
            )

        # 3. Global Stats
        self.throughput_lbl.config(text=f"Throughput: {self.sim.get_throughput_rate():.1f} vehicles/min")
        self.avg_wait_lbl.config(text=f"Avg Delay: {self.sim.get_average_wait_time():.1f} sec/veh")
        self.total_passed_lbl.config(
            text=f"Passed: {self.sim.total_passed} | Active: {sum(len(v) for v in self.sim.vehicles.values())}"
        )

        # 4. AI Log Feed
        if self.controller.ai_decisions_log:
            latest = "\n".join(self.controller.ai_decisions_log[-8:])
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert(tk.END, latest)
            self.log_text.see(tk.END)
