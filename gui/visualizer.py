"""
Interactive Traffic Light Simulation & Reality Camera AI GUI using Tkinter.
Includes:
- Tab 1: 🚦 Accident-Free 4-Way Simulation & Adaptive AI Controller
- Tab 2: 📹 Reality Mode (OpenCV Video / Webcam AI & ANPR License Plate Scanner)
- Tab 3: 🔍 E-Challan Portal & Vehicle Registry Search
"""

import math
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional
import cv2
import numpy as np
from PIL import Image, ImageTk

from traffic_ai.challan_manager import Challan, ChallanManager
from traffic_ai.controller import ControlMode, TrafficController
from traffic_ai.intersection import Intersection, LightState, TrafficPhase
from traffic_ai.reality_detector import RealityDetector
from traffic_ai.simulation import TrafficSimulation
from traffic_ai.vehicle import Direction, Vehicle, VehicleType


class TrafficVisualizer:
    """Multi-Tab Desktop Application for AI Traffic Simulation and Reality Camera AI."""

    def __init__(
        self,
        root: tk.Tk,
        simulation: TrafficSimulation,
        challan_manager: Optional[ChallanManager] = None,
    ):
        self.root = root
        self.sim = simulation
        self.intersection = simulation.intersection
        self.controller = simulation.controller
        self.challan_manager = challan_manager or simulation.challan_manager
        self.reality = RealityDetector(self.challan_manager)

        self.root.title("AI Smart Traffic Light Controller & Reality ANPR System")
        self.root.geometry("1280x880")
        self.root.minsize(1120, 780)
        self.root.configure(bg="#0f172a")

        # Palette
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

        self.last_frame_time = time.time()
        self.selected_vehicle: Optional[Vehicle] = None
        self._cam_image_tk = None

        self._configure_styles()
        self._create_layout()
        self._animate()

    def _configure_styles(self):
        """Configures ttk Notebook and Treeview dark themes."""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Notebook Tabs
        style.configure(
            "TNotebook",
            background=self.BG_DARK,
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            background="#1e293b",
            foreground="#94a3b8",
            font=("Segoe UI", 10, "bold"),
            padding=[16, 8],
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#0284c7")],
            foreground=[("selected", "#ffffff")],
        )

        # Treeview
        style.configure(
            "Treeview",
            background="#1e293b",
            foreground="#f8fafc",
            fieldbackground="#1e293b",
            rowheight=26,
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#334155",
            foreground="#38bdf8",
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
        )
        style.map("Treeview", background=[("selected", "#0369a1")])

    def _create_layout(self):
        """Builds the main header and tabbed interface."""
        # Top Header Bar
        header = tk.Frame(self.root, bg="#1e293b", height=50)
        header.pack(fill=tk.X, side=tk.TOP)

        title_lbl = tk.Label(
            header,
            text="🚦 AI TRAFFIC CONTROLLER & E-CHALLAN SYSTEM",
            font=("Segoe UI", 15, "bold"),
            fg=self.TEXT_PRIMARY,
            bg="#1e293b",
            padx=16,
            pady=8,
        )
        title_lbl.pack(side=tk.LEFT)

        status_lbl = tk.Label(
            header,
            text="🛡️ ACCIDENT-FREE ACTIVE | DUAL MODE (SIM + REALITY)",
            font=("Segoe UI", 9, "bold"),
            fg=self.ACCENT_GREEN,
            bg="#1e293b",
            padx=16,
        )
        status_lbl.pack(side=tk.RIGHT)

        # Notebook Container
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # 3 Tabs
        self.tab_sim = tk.Frame(self.notebook, bg=self.BG_DARK)
        self.tab_reality = tk.Frame(self.notebook, bg=self.BG_DARK)
        self.tab_challan = tk.Frame(self.notebook, bg=self.BG_DARK)

        self.notebook.add(self.tab_sim, text="  🚦 Simulation & AI Control  ")
        self.notebook.add(self.tab_reality, text="  📹 Reality Mode (Camera AI & ANPR)  ")
        self.notebook.add(self.tab_challan, text="  🔍 E-Challan & Plate Search  ")

        # Build each tab
        self._build_sim_tab()
        self._build_reality_tab()
        self._build_challan_tab()

    # =========================================================================
    # TAB 1: SIMULATION & AI CONTROL
    # =========================================================================
    def _build_sim_tab(self):
        """Constructs Tab 1: 4-Way Intersection Simulator + AI Controls."""
        main_body = tk.Frame(self.tab_sim, bg=self.BG_DARK)
        main_body.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Left Canvas
        canvas_frame = tk.Frame(main_body, bg=self.PANEL_BG, bd=1, relief=tk.FLAT)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.canvas = tk.Canvas(
            canvas_frame,
            width=800,
            height=800,
            bg="#0b0f19",
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Right Sidebar
        sidebar = tk.Frame(main_body, bg=self.PANEL_BG, width=420)
        sidebar.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(0, 0))
        sidebar.pack_propagate(False)

        container = tk.Frame(sidebar, bg=self.PANEL_BG)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Mode Selection
        mode_card = tk.LabelFrame(
            container, text=" CONTROLLER MODE ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_BLUE, bg=self.CARD_BG, padx=8, pady=6
        )
        mode_card.pack(fill=tk.X, pady=(0, 8))

        self.mode_var = tk.StringVar(value=self.controller.mode.value)
        ai_rb = tk.Radiobutton(
            mode_card, text="🟢 AI Adaptive (Zero-Delay Dynamic)",
            variable=self.mode_var, value=ControlMode.AI_ADAPTIVE.value,
            command=self._on_mode_change, font=("Segoe UI", 9, "bold"),
            fg=self.TEXT_PRIMARY, bg=self.CARD_BG, selectcolor="#1e293b", activebackground=self.CARD_BG
        )
        ai_rb.pack(anchor=tk.W)

        fixed_rb = tk.Radiobutton(
            mode_card, text="🔵 Fixed Timer (Classic 14s)",
            variable=self.mode_var, value=ControlMode.FIXED_TIMER.value,
            command=self._on_mode_change, font=("Segoe UI", 9),
            fg=self.TEXT_SECONDARY, bg=self.CARD_BG, selectcolor="#1e293b", activebackground=self.CARD_BG
        )
        fixed_rb.pack(anchor=tk.W)

        # Emergency Button
        em_btn = tk.Button(
            container, text="🚨 DISPATCH EMERGENCY AMBULANCE",
            command=self.sim.trigger_emergency_vehicle, font=("Segoe UI", 10, "bold"),
            fg="white", bg="#dc2626", activebackground="#b91c1c", activeforeground="white",
            bd=0, padx=8, pady=6, cursor="hand2"
        )
        em_btn.pack(fill=tk.X, pady=(0, 8))

        # Signal Status
        phase_card = tk.LabelFrame(
            container, text=" ACTIVE SIGNAL PHASE ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_BLUE, bg=self.CARD_BG, padx=8, pady=6
        )
        phase_card.pack(fill=tk.X, pady=(0, 8))

        self.phase_lbl = tk.Label(
            phase_card, text="NORTH-SOUTH CORRIDOR",
            font=("Segoe UI", 11, "bold"), fg=self.ACCENT_GREEN, bg=self.CARD_BG
        )
        self.phase_lbl.pack(anchor=tk.W)

        self.timer_lbl = tk.Label(
            phase_card, text="Remaining: 00.0s",
            font=("Consolas", 13, "bold"), fg=self.TEXT_PRIMARY, bg=self.CARD_BG
        )
        self.timer_lbl.pack(anchor=tk.W)

        # Lane Density Telemetry
        density_card = tk.LabelFrame(
            container, text=" APPROACH QUEUE DENSITY ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_BLUE, bg=self.CARD_BG, padx=8, pady=6
        )
        density_card.pack(fill=tk.X, pady=(0, 8))

        self.lane_labels: Dict[Direction, tk.Label] = {}
        for d in Direction:
            row = tk.Frame(density_card, bg=self.CARD_BG)
            row.pack(fill=tk.X, pady=1)
            tk.Label(
                row, text=f"{d.value:5s}:", font=("Consolas", 8, "bold"),
                fg=self.TEXT_SECONDARY, bg=self.CARD_BG, width=6, anchor=tk.W
            ).pack(side=tk.LEFT)

            val_lbl = tk.Label(
                row, text="0 veh (Wait: 0.0s)", font=("Segoe UI", 8),
                fg=self.TEXT_PRIMARY, bg=self.CARD_BG, anchor=tk.W
            )
            val_lbl.pack(side=tk.LEFT, padx=4)
            self.lane_labels[d] = val_lbl

        # Metrics
        metrics_card = tk.LabelFrame(
            container, text=" PERFORMANCE & SAFETY ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_BLUE, bg=self.CARD_BG, padx=8, pady=6
        )
        metrics_card.pack(fill=tk.X, pady=(0, 8))

        self.throughput_lbl = tk.Label(
            metrics_card, text="Throughput: 0.0 veh/min",
            font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG
        )
        self.throughput_lbl.pack(anchor=tk.W)

        self.avg_wait_lbl = tk.Label(
            metrics_card, text="Avg Delay: 0.0s",
            font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG
        )
        self.avg_wait_lbl.pack(anchor=tk.W)

        self.collision_lbl = tk.Label(
            metrics_card, text="Accidents: 0 (All-Red Lock Active)",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_GREEN, bg=self.CARD_BG
        )
        self.collision_lbl.pack(anchor=tk.W)

        # Controls
        controls_card = tk.LabelFrame(
            container, text=" SIMULATION CONTROLS ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_BLUE, bg=self.CARD_BG, padx=8, pady=6
        )
        controls_card.pack(fill=tk.X, pady=(0, 8))

        self.spawn_slider = ttk.Scale(
            controls_card, from_=0.1, to=1.2, value=self.sim.spawn_rate,
            orient=tk.HORIZONTAL, command=self._on_spawn_change
        )
        self.spawn_slider.pack(fill=tk.X, pady=(0, 4))

        btn_row = tk.Frame(controls_card, bg=self.CARD_BG)
        btn_row.pack(fill=tk.X)

        self.pause_btn = tk.Button(
            btn_row, text="⏸ Pause", command=self._toggle_pause,
            font=("Segoe UI", 9, "bold"), fg=self.TEXT_PRIMARY, bg="#475569",
            bd=0, padx=8, pady=3, cursor="hand2"
        )
        self.pause_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 3))

        reset_btn = tk.Button(
            btn_row, text="🔄 Reset", command=self._reset_sim,
            font=("Segoe UI", 9, "bold"), fg=self.TEXT_PRIMARY, bg="#475569",
            bd=0, padx=8, pady=3, cursor="hand2"
        )
        reset_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(3, 0))

        # Log
        log_card = tk.LabelFrame(
            container, text=" AI DECISION CONSOLE ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_BLUE, bg=self.CARD_BG, padx=6, pady=4
        )
        log_card.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_card, height=5, bg="#090d16", fg="#38bdf8",
            font=("Consolas", 8), bd=0, wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # =========================================================================
    # TAB 2: REALITY MODE (OPENCV CAMERA AI & ANPR SCANNER)
    # =========================================================================
    def _build_reality_tab(self):
        """Constructs Tab 2: Live Camera / Video Stream with AI Object & ANPR Plate Detection."""
        main_frame = tk.Frame(self.tab_reality, bg=self.BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Left: Video Display
        vid_frame = tk.Frame(main_frame, bg=self.PANEL_BG, bd=1, relief=tk.FLAT)
        vid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.vid_label = tk.Label(vid_frame, bg="#0b0f19")
        self.vid_label.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Right: Video Source & ANPR Telemetry
        r_sidebar = tk.Frame(main_frame, bg=self.PANEL_BG, width=380)
        r_sidebar.pack(side=tk.RIGHT, fill=tk.BOTH)
        r_sidebar.pack_propagate(False)

        r_container = tk.Frame(r_sidebar, bg=self.PANEL_BG)
        r_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Source Selection
        src_card = tk.LabelFrame(
            r_container, text=" REALITY VIDEO FEED SOURCE ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_BLUE, bg=self.CARD_BG, padx=8, pady=8
        )
        src_card.pack(fill=tk.X, pady=(0, 10))

        syn_btn = tk.Button(
            src_card, text="🛣️ Live Expressway Stream (AI Feed)",
            command=self.reality.set_source_synthetic, font=("Segoe UI", 9, "bold"),
            fg=self.TEXT_PRIMARY, bg="#0284c7", activebackground="#0369a1", bd=0, pady=6, cursor="hand2"
        )
        syn_btn.pack(fill=tk.X, pady=(0, 6))

        cam_btn = tk.Button(
            src_card, text="📷 Switch to Physical Webcam (0)",
            command=self._switch_webcam, font=("Segoe UI", 9),
            fg=self.TEXT_PRIMARY, bg="#475569", activebackground="#334155", bd=0, pady=6, cursor="hand2"
        )
        cam_btn.pack(fill=tk.X, pady=(0, 6))

        file_btn = tk.Button(
            src_card, text="📂 Load Traffic Video File...",
            command=self._load_video_file, font=("Segoe UI", 9),
            fg=self.TEXT_PRIMARY, bg="#475569", activebackground="#334155", bd=0, pady=6, cursor="hand2"
        )
        file_btn.pack(fill=tk.X)

        # ANPR Plate Scanner Box
        anpr_card = tk.LabelFrame(
            r_container, text=" LIVE ANPR NUMBER PLATE SCANNER ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_YELLOW, bg=self.CARD_BG, padx=8, pady=8
        )
        anpr_card.pack(fill=tk.X, pady=(0, 10))

        self.scanned_plate_lbl = tk.Label(
            anpr_card, text="WAITING FOR VEHICLE...",
            font=("Consolas", 14, "bold"), fg="#38bdf8", bg="#0f172a", pady=10
        )
        self.scanned_plate_lbl.pack(fill=tk.X, pady=(0, 6))

        self.scanned_owner_lbl = tk.Label(
            anpr_card, text="Owner: --", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG
        )
        self.scanned_owner_lbl.pack(anchor=tk.W)

        self.scanned_model_lbl = tk.Label(
            anpr_card, text="Model: --", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG
        )
        self.scanned_model_lbl.pack(anchor=tk.W)

        self.scanned_fine_lbl = tk.Label(
            anpr_card, text="Pending Challan: None", font=("Segoe UI", 10, "bold"),
            fg=self.ACCENT_GREEN, bg=self.CARD_BG
        )
        self.scanned_fine_lbl.pack(anchor=tk.W, pady=(4, 6))

        inspect_btn = tk.Button(
            anpr_card, text="🔍 Search Plate in Challan Portal",
            command=self._jump_to_scanned_plate, font=("Segoe UI", 9, "bold"),
            fg=self.TEXT_PRIMARY, bg="#059669", activebackground="#047857", bd=0, pady=5, cursor="hand2"
        )
        inspect_btn.pack(fill=tk.X)

        # Reality Telemetry
        tele_card = tk.LabelFrame(
            r_container, text=" REAL-WORLD AI TELEMETRY ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_BLUE, bg=self.CARD_BG, padx=8, pady=8
        )
        tele_card.pack(fill=tk.BOTH, expand=True)

        self.r_fps_lbl = tk.Label(
            tele_card, text="Inference FPS: 30.0", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG
        )
        self.r_fps_lbl.pack(anchor=tk.W)

        self.r_count_lbl = tk.Label(
            tele_card, text="Vehicles Detected: 0", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG
        )
        self.r_count_lbl.pack(anchor=tk.W)

        self.r_total_lbl = tk.Label(
            tele_card, text="Total Passed ANPR: 0", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG
        )
        self.r_total_lbl.pack(anchor=tk.W)

    def _switch_webcam(self):
        success = self.reality.set_source_webcam(0)
        if not success:
            messagebox.showwarning(
                "Webcam Not Found",
                "Could not connect to physical webcam (0).\nDefaulting to the simulated live expressway feed."
            )

    def _load_video_file(self):
        fpath = filedialog.askopenfilename(
            title="Select Traffic Video File",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv"), ("All Files", "*.*")]
        )
        if fpath:
            success = self.reality.set_source_video_file(fpath)
            if not success:
                messagebox.showerror("Error", "Failed to open selected video file.")

    def _jump_to_scanned_plate(self):
        plate = self.reality.last_scanned_plate
        if plate:
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, plate)
            self.notebook.select(self.tab_challan)
            self._search_plate()

    # =========================================================================
    # TAB 3: E-CHALLAN PORTAL & NUMBER PLATE SEARCH
    # =========================================================================
    def _build_challan_tab(self):
        """Constructs Tab 3: Searchable Vehicle Registry, Challan Records, and Payment."""
        main_frame = tk.Frame(self.tab_challan, bg=self.BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Top: Search & Profile Section
        top_frame = tk.Frame(main_frame, bg=self.PANEL_BG, padx=12, pady=12)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            top_frame, text="VEHICLE NUMBER PLATE SEARCH & E-CHALLAN INQUIRY",
            font=("Segoe UI", 12, "bold"), fg=self.ACCENT_BLUE, bg=self.PANEL_BG
        ).pack(anchor=tk.W, pady=(0, 8))

        search_row = tk.Frame(top_frame, bg=self.PANEL_BG)
        search_row.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            search_row, text="Enter Plate Number:", font=("Segoe UI", 10),
            fg=self.TEXT_PRIMARY, bg=self.PANEL_BG
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.search_entry = tk.Entry(
            search_row, font=("Consolas", 12, "bold"), bg="#0f172a", fg="#38bdf8",
            insertbackground="white", width=20, bd=1, relief=tk.SOLID
        )
        self.search_entry.insert(0, "DL-01-AB-1234")
        self.search_entry.pack(side=tk.LEFT, padx=(0, 8))

        search_btn = tk.Button(
            search_row, text="🔎 Search Challan", command=self._search_plate,
            font=("Segoe UI", 9, "bold"), fg="white", bg="#0284c7",
            activebackground="#0369a1", bd=0, padx=14, pady=4, cursor="hand2"
        )
        search_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Quick Select Buttons for Demo
        quick_frame = tk.Frame(top_frame, bg=self.PANEL_BG)
        quick_frame.pack(fill=tk.X)
        tk.Label(
            quick_frame, text="Quick Examples:", font=("Segoe UI", 8),
            fg=self.TEXT_SECONDARY, bg=self.PANEL_BG
        ).pack(side=tk.LEFT, padx=(0, 6))

        for p in ["DL-01-AB-1234", "MH-02-CP-8921", "UP-14-EA-4521", "KA-03-MK-7821"]:
            btn = tk.Button(
                quick_frame, text=p, font=("Consolas", 8), fg="#38bdf8", bg="#334155",
                bd=0, padx=6, pady=2, cursor="hand2",
                command=lambda pl=p: self._quick_fill_plate(pl)
            )
            btn.pack(side=tk.LEFT, padx=3)

        # Profile Card
        self.profile_frame = tk.LabelFrame(
            top_frame, text=" REGISTERED VEHICLE DETAILS ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_GREEN, bg=self.CARD_BG, padx=10, pady=8
        )
        self.profile_frame.pack(fill=tk.X, pady=(10, 0))

        p_grid = tk.Frame(self.profile_frame, bg=self.CARD_BG)
        p_grid.pack(fill=tk.X)

        self.p_owner_lbl = tk.Label(p_grid, text="Owner: --", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG)
        self.p_owner_lbl.grid(row=0, column=0, sticky=tk.W, padx=10, pady=2)

        self.p_model_lbl = tk.Label(p_grid, text="Model: --", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG)
        self.p_model_lbl.grid(row=0, column=1, sticky=tk.W, padx=10, pady=2)

        self.p_city_lbl = tk.Label(p_grid, text="RTO City: --", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG)
        self.p_city_lbl.grid(row=1, column=0, sticky=tk.W, padx=10, pady=2)

        self.p_fine_lbl = tk.Label(p_grid, text="Total Pending Fine: ₹0", font=("Segoe UI", 10, "bold"), fg=self.ACCENT_GREEN, bg=self.CARD_BG)
        self.p_fine_lbl.grid(row=1, column=1, sticky=tk.W, padx=10, pady=2)

        # Bottom: Challan Records Treeview
        bot_frame = tk.Frame(main_frame, bg=self.PANEL_BG, padx=10, pady=10)
        bot_frame.pack(fill=tk.BOTH, expand=True)

        t_header = tk.Frame(bot_frame, bg=self.PANEL_BG)
        t_header.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            t_header, text="TRAFFIC VIOLATION RECORDS (LIVE FEED)",
            font=("Segoe UI", 10, "bold"), fg=self.ACCENT_BLUE, bg=self.PANEL_BG
        ).pack(side=tk.LEFT)

        pay_btn = tk.Button(
            t_header, text="💳 Pay Selected Challan", command=self._pay_selected_challan,
            font=("Segoe UI", 9, "bold"), fg="white", bg="#059669",
            activebackground="#047857", bd=0, padx=12, pady=3, cursor="hand2"
        )
        pay_btn.pack(side=tk.RIGHT, padx=4)

        refresh_btn = tk.Button(
            t_header, text="🔄 Refresh", command=self._refresh_challan_table,
            font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg="#475569",
            bd=0, padx=10, pady=3, cursor="hand2"
        )
        refresh_btn.pack(side=tk.RIGHT, padx=4)

        # Columns
        cols = ("id", "time", "plate", "owner", "violation", "fine", "status")
        self.challan_tree = ttk.Treeview(bot_frame, columns=cols, show="headings", selectmode="browse")
        self.challan_tree.heading("id", text="Challan ID")
        self.challan_tree.heading("time", text="Timestamp")
        self.challan_tree.heading("plate", text="Plate No.")
        self.challan_tree.heading("owner", text="Owner")
        self.challan_tree.heading("violation", text="Violation Reason")
        self.challan_tree.heading("fine", text="Fine (₹)")
        self.challan_tree.heading("status", text="Status")

        self.challan_tree.column("id", width=120, anchor=tk.CENTER)
        self.challan_tree.column("time", width=150, anchor=tk.CENTER)
        self.challan_tree.column("plate", width=130, anchor=tk.CENTER)
        self.challan_tree.column("owner", width=140, anchor=tk.W)
        self.challan_tree.column("violation", width=180, anchor=tk.W)
        self.challan_tree.column("fine", width=90, anchor=tk.CENTER)
        self.challan_tree.column("status", width=100, anchor=tk.CENTER)

        self.challan_tree.pack(fill=tk.BOTH, expand=True)
        self._refresh_challan_table()

    def _quick_fill_plate(self, plate: str):
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, plate)
        self._search_plate()

    def _search_plate(self):
        plate = self.search_entry.get().strip()
        res = self.challan_manager.search_by_plate(plate)
        if res["found"]:
            v = res["vehicle"]
            self.p_owner_lbl.config(text=f"Owner: {v.owner_name}")
            self.p_model_lbl.config(text=f"Model: {v.vehicle_model} ({v.vehicle_type.upper()})")
            self.p_city_lbl.config(text=f"RTO City: {v.registered_city} | Contact: {v.contact_number}")
            fine = res["total_pending_fine"]
            self.p_fine_lbl.config(
                text=f"Total Pending Fine: ₹{fine}",
                fg=self.ACCENT_RED if fine > 0 else self.ACCENT_GREEN
            )
            # Filter treeview to this vehicle's records
            self._populate_treeview(res["challans"])
        else:
            messagebox.showinfo("Search Result", f"No registration records found for plate: {plate}")

    def _refresh_challan_table(self):
        all_challans = self.challan_manager.get_recent_challans(limit=30)
        self._populate_treeview(all_challans)

    def _populate_treeview(self, challan_list: List[Challan]):
        for item in self.challan_tree.get_children():
            self.challan_tree.delete(item)

        for c in challan_list:
            status_display = "🟢 PAID" if c.status == "PAID" else "🔴 PENDING"
            self.challan_tree.insert(
                "", tk.END, iid=c.challan_id,
                values=(c.challan_id, c.timestamp, c.plate_number, c.owner_name, c.violation_type, f"₹{c.fine_amount}", status_display)
            )

    def _pay_selected_challan(self):
        selected = self.challan_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a challan from the list to pay.")
            return

        cid = selected[0]
        c = self.challan_manager.challans.get(cid)
        if c:
            if c.status == "PAID":
                messagebox.showinfo("Already Paid", f"Challan {cid} has already been paid on {c.payment_date}.")
                return

            confirm = messagebox.askyesno(
                "Confirm Payment",
                f"Pay E-Challan {cid}?\n\nVehicle: {c.plate_number}\nViolation: {c.violation_type}\nAmount: ₹{c.fine_amount}"
            )
            if confirm:
                self.challan_manager.pay_challan(cid)
                messagebox.showinfo(
                    "Payment Successful! 🎉",
                    f"Receipt Generated!\nPayment ID: {c.payment_id}\nStatus: PAID\nDate: {c.payment_date}"
                )
                self._search_plate()

    # =========================================================================
    # SIMULATION CANVAS RENDERING (ACCIDENT-FREE ROAD DESIGN)
    # =========================================================================
    def _on_mode_change(self):
        val = self.mode_var.get()
        if val == ControlMode.AI_ADAPTIVE.value:
            self.controller.mode = ControlMode.AI_ADAPTIVE
        else:
            self.controller.mode = ControlMode.FIXED_TIMER

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
        """Simulation tick and multi-tab rendering loop (~35 FPS)."""
        now = time.time()
        dt = min(0.08, now - self.last_frame_time)
        self.last_frame_time = now

        # 1. Update Simulation Physics & AI
        self.sim.update(dt)

        # 2. Render Simulation Tab
        self._draw_intersection()
        self._draw_traffic_lights()
        self._draw_vehicles()
        self._update_sidebar_telemetry()

        # 3. Update Reality Tab if active
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 1:  # Reality tab
            self._update_reality_feed()

        self.root.after(30, self._animate)

    def _update_reality_feed(self):
        """Reads frame from RealityDetector and updates image in Tab 2."""
        frame, tele = self.reality.read_frame()
        if frame is not None:
            # Convert OpenCV BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            # Resize nicely for canvas
            pil_img = pil_img.resize((720, 480), Image.Resampling.BILINEAR)
            self._cam_image_tk = ImageTk.PhotoImage(image=pil_img)
            self.vid_label.configure(image=self._cam_image_tk)

            # Update Telemetry in Sidebar
            self.r_fps_lbl.config(text=f"Inference FPS: {tele['fps']:.1f}")
            self.r_count_lbl.config(text=f"Vehicles Detected: {tele['detected_count']}")
            self.r_total_lbl.config(text=f"Total Passed ANPR: {tele['total_counted']}")

            # ANPR Banner
            plate = tele.get("last_plate")
            if plate:
                self.scanned_plate_lbl.config(text=plate)
                res = tele.get("last_scan_result")
                if res and res.get("found"):
                    v = res["vehicle"]
                    self.scanned_owner_lbl.config(text=f"Owner: {v.owner_name}")
                    self.scanned_model_lbl.config(text=f"Model: {v.vehicle_model}")
                    fine = res["total_pending_fine"]
                    if fine > 0:
                        self.scanned_fine_lbl.config(text=f"⚠️ Pending Challan: ₹{fine} (UNPAID)", fg=self.ACCENT_RED)
                    else:
                        self.scanned_fine_lbl.config(text="✅ No Pending Challans (Clean)", fg=self.ACCENT_GREEN)

    def _draw_intersection(self):
        """Draws realistic asphalt roadway with dual lanes, stop lines, and markings."""
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100:
            w, h = 800, 800

        cx, cy = w / 2.0, h / 2.0
        rw = self.intersection.road_width

        # Grass / Urban Ground
        self.canvas.create_rectangle(0, 0, w, h, fill="#0f172a", outline="")

        # Asphalt Roadways
        road_col = "#1e293b"
        self.canvas.create_rectangle(cx - rw / 2, 0, cx + rw / 2, h, fill=road_col, outline="")
        self.canvas.create_rectangle(0, cy - rw / 2, w, cy + rw / 2, fill=road_col, outline="")

        # Road Curbs / Borders
        curb_col = "#64748b"
        self.canvas.create_line(cx - rw / 2, 0, cx - rw / 2, cy - rw / 2, fill=curb_col, width=3)
        self.canvas.create_line(0, cy - rw / 2, cx - rw / 2, cy - rw / 2, fill=curb_col, width=3)

        self.canvas.create_line(cx + rw / 2, 0, cx + rw / 2, cy - rw / 2, fill=curb_col, width=3)
        self.canvas.create_line(cx + rw / 2, cy - rw / 2, w, cy - rw / 2, fill=curb_col, width=3)

        self.canvas.create_line(cx - rw / 2, h, cx - rw / 2, cy + rw / 2, fill=curb_col, width=3)
        self.canvas.create_line(0, cy + rw / 2, cx - rw / 2, cy + rw / 2, fill=curb_col, width=3)

        self.canvas.create_line(cx + rw / 2, h, cx + rw / 2, cy + rw / 2, fill=curb_col, width=3)
        self.canvas.create_line(cx + rw / 2, cy + rw / 2, w, cy + rw / 2, fill=curb_col, width=3)

        # Yellow Center Divider Lines (Double Dashed)
        yellow_col = "#eab308"
        dash = (12, 10)
        self.canvas.create_line(cx, 0, cx, cy - rw / 2, fill=yellow_col, width=2, dash=dash)
        self.canvas.create_line(cx, cy + rw / 2, cx, h, fill=yellow_col, width=2, dash=dash)
        self.canvas.create_line(0, cy, cx - rw / 2, cy, fill=yellow_col, width=2, dash=dash)
        self.canvas.create_line(cx + rw / 2, cy, w, cy, fill=yellow_col, width=2, dash=dash)

        # Solid White Stop Lines
        white_col = "#f8fafc"
        stop_offset = rw / 2 + 16
        self.canvas.create_line(cx, cy - stop_offset, cx + rw / 2, cy - stop_offset, fill=white_col, width=5)
        self.canvas.create_line(cx - rw / 2, cy + stop_offset, cx, cy + stop_offset, fill=white_col, width=5)
        self.canvas.create_line(cx - stop_offset, cy, cx - stop_offset, cy + rw / 2, fill=white_col, width=5)
        self.canvas.create_line(cx + stop_offset, cy - rw / 2, cx + stop_offset, cy, fill=white_col, width=5)

        # Zebra Crossings
        self._draw_crosswalk(cx - rw / 2, cy - rw / 2 - 28, rw, 12, horizontal=True)
        self._draw_crosswalk(cx - rw / 2, cy + rw / 2 + 16, rw, 12, horizontal=True)
        self._draw_crosswalk(cx - rw / 2 - 28, cy - rw / 2, 12, rw, horizontal=False)
        self._draw_crosswalk(cx + rw / 2 + 16, cy - rw / 2, 12, rw, horizontal=False)

        # Center Junction Box Marking (Yellow Box Junction to prevent blocking)
        box_pad = 6
        self.canvas.create_rectangle(
            cx - rw / 2 + box_pad, cy - rw / 2 + box_pad,
            cx + rw / 2 - box_pad, cy + rw / 2 - box_pad,
            outline="#ca8a04", width=1, dash=(4, 4)
        )

    def _draw_crosswalk(self, x: float, y: float, w: float, h: float, horizontal: bool):
        stripes = 8
        if horizontal:
            sw = w / stripes
            for i in range(stripes):
                if i % 2 == 0:
                    self.canvas.create_rectangle(x + i * sw, y, x + (i + 1) * sw, y + h, fill="#cbd5e1", outline="")
        else:
            sh = h / stripes
            for i in range(stripes):
                if i % 2 == 0:
                    self.canvas.create_rectangle(x, y + i * sh, x + w, y + (i + 1) * sh, fill="#cbd5e1", outline="")

    def _draw_traffic_lights(self):
        """Renders 4 traffic signals with live digital countdowns."""
        cx = 400
        cy = 400
        rw = self.intersection.road_width
        rem_time = self.controller.get_remaining_time()

        gantries = {
            Direction.NORTH: (cx + rw / 2 + 16, cy - rw / 2 - 32),
            Direction.SOUTH: (cx - rw / 2 - 46, cy + rw / 2 + 12),
            Direction.WEST: (cx - rw / 2 - 32, cy + rw / 2 + 34),
            Direction.EAST: (cx + rw / 2 + 12, cy - rw / 2 - 54),
        }

        for direction, (gx, gy) in gantries.items():
            state = self.intersection.get_light(direction)
            self._render_signal_box(gx, gy, state, rem_time)

    def _render_signal_box(self, x: float, y: float, state: LightState, rem_time: float):
        bw, bh = 26, 68
        self.canvas.create_rectangle(x, y, x + bw, y + bh, fill="#0f172a", outline="#64748b", width=1.5)

        r_col = "#ef4444" if state in (LightState.RED, LightState.ALL_RED) else "#3b0c0c"
        y_col = "#f59e0b" if state == LightState.YELLOW else "#3b2e0c"
        g_col = "#22c55e" if state == LightState.GREEN else "#0c3b1e"

        br = 7
        cx = x + bw / 2
        self.canvas.create_oval(cx - br, y + 12 - br, cx + br, y + 12 + br, fill=r_col, outline="")
        self.canvas.create_oval(cx - br, y + 34 - br, cx + br, y + 34 + br, fill=y_col, outline="")
        self.canvas.create_oval(cx - br, y + 56 - br, cx + br, y + 56 + br, fill=g_col, outline="")

        if state in (LightState.GREEN, LightState.YELLOW, LightState.ALL_RED):
            tag = "ALL RED" if state == LightState.ALL_RED else f"{int(rem_time)}s"
            self.canvas.create_text(
                cx, y - 9, text=tag, font=("Consolas", 8, "bold"),
                fill="#ef4444" if state == LightState.ALL_RED else "#38bdf8"
            )

    def _draw_vehicles(self):
        """Renders vehicles with license plate badges and emergency sirens."""
        for direction, lane in self.sim.vehicles.items():
            lane_coord = self.lane_centers[direction]
            
            for v in lane:
                length, width = v.length, v.width

                if direction == Direction.NORTH:
                    x1 = lane_coord - width / 2
                    x2 = lane_coord + width / 2
                    y1 = v.position - length / 2
                    y2 = v.position + length / 2
                elif direction == Direction.SOUTH:
                    x1 = lane_coord - width / 2
                    x2 = lane_coord + width / 2
                    y1 = v.position - length / 2
                    y2 = v.position + length / 2
                elif direction == Direction.WEST:
                    x1 = v.position - length / 2
                    x2 = v.position + length / 2
                    y1 = lane_coord - width / 2
                    y2 = lane_coord + width / 2
                elif direction == Direction.EAST:
                    x1 = v.position - length / 2
                    x2 = v.position + length / 2
                    y1 = lane_coord - width / 2
                    y2 = lane_coord + width / 2

                self._draw_single_vehicle(v, x1, y1, x2, y2, direction)

    def _draw_single_vehicle(self, v: Vehicle, x1: float, y1: float, x2: float, y2: float, direction: Direction):
        # Body
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=v.color, outline="#0f172a", width=1)

        # Windshield
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        rw = (x2 - x1) * 0.6
        rh = (y2 - y1) * 0.6
        self.canvas.create_rectangle(mx - rw / 2, my - rh / 2, mx + rw / 2, my + rh / 2, fill="#0f172a", outline="")

        # Emergency Siren
        if v.is_emergency:
            siren_color = "#ef4444" if int(v.siren_phase * 10) % 2 == 0 else "#38bdf8"
            self.canvas.create_oval(mx - 4, my - 4, mx + 4, my + 4, fill=siren_color, outline="white", width=1)
            self.canvas.create_oval(mx - 9, my - 9, mx + 9, my + 9, outline=siren_color, width=1)

        # ANPR License Plate Tag on Top
        plate_short = v.plate_number.split("-")
        tag_text = f"{plate_short[0]}-{plate_short[-1]}" if len(plate_short) >= 4 else v.plate_number[:6]
        
        offset_y = -10 if direction.is_vertical else 0
        offset_x = 0 if direction.is_vertical else (14 if direction == Direction.WEST else -14)

        self.canvas.create_text(
            mx + offset_x, my + offset_y,
            text=tag_text,
            font=("Consolas", 7, "bold"),
            fill="#f8fafc" if not v.has_jumped_red_light else "#ef4444"
        )

    def _update_sidebar_telemetry(self):
        """Updates right-side simulation metrics and AI console."""
        is_ns = self.controller.active_phase == TrafficPhase.NORTH_SOUTH
        state_val = self.controller.light_state.value
        self.phase_lbl.config(
            text="NORTH-SOUTH CORRIDOR" if is_ns else "EAST-WEST CORRIDOR",
            fg=self.ACCENT_GREEN if self.controller.light_state == LightState.GREEN else (
                self.ACCENT_RED if self.controller.light_state == LightState.ALL_RED else self.ACCENT_YELLOW
            )
        )

        rem = self.controller.get_remaining_time()
        self.timer_lbl.config(text=f"Phase Remaining: {rem:04.1f}s ({state_val})")

        telemetry = self.sim.vision.get_intersection_snapshot(
            self.sim.vehicles, self.intersection.stop_positions
        )
        for d in Direction:
            t = telemetry[d]
            em_tag = " [🚨EM]" if t.emergency_present else ""
            self.lane_labels[d].config(
                text=f"{t.vehicle_count} veh (Wait: {t.avg_wait_time:.1f}s){em_tag}",
                fg=self.ACCENT_RED if t.emergency_present else self.TEXT_PRIMARY
            )

        self.throughput_lbl.config(text=f"Throughput: {self.sim.get_throughput_rate():.1f} veh/min")
        self.avg_wait_lbl.config(text=f"Avg Delay: {self.sim.get_average_wait_time():.1f} sec/veh")

        # AI Console
        if self.controller.ai_decisions_log:
            latest = "\n".join(self.controller.ai_decisions_log[-7:])
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert(tk.END, latest)
            self.log_text.see(tk.END)
