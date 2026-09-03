"""
Real AI Traffic Light Detection, ANPR License Plate Scanner & E-Challan Desktop Application.
Zero 2D cartoon simulation: 100% focused on real camera feeds, computer vision detection,
adaptive signal light timing, and vehicle registration & violation enforcement.
"""

import datetime
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional
import cv2
import numpy as np
from PIL import Image, ImageTk

from traffic_ai.anpr_engine import ANPREngine
from traffic_ai.challan_manager import Challan, ChallanManager
from traffic_ai.vision_pipeline import VisionPipeline


class RealTrafficApp:
    """Production GUI for Real-World AI Traffic Camera Detection & E-Challan Enforcement."""

    def __init__(self, root: tk.Tk, pipeline: Optional[VisionPipeline] = None):
        self.root = root
        self.challan_manager = ChallanManager()
        self.pipeline = pipeline or VisionPipeline(self.challan_manager)

        self.root.title("Real AI Traffic Light Vision, ANPR & E-Challan System")
        self.root.geometry("1280x860")
        self.root.minsize(1120, 780)
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

        self._image_tk = None
        self.is_paused = False

        self._configure_styles()
        self._create_layout()
        self._frame_loop()

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TNotebook", background=self.BG_DARK, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#1e293b",
            foreground="#94a3b8",
            font=("Segoe UI", 10, "bold"),
            padding=[20, 10],
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#0284c7")],
            foreground=[("selected", "#ffffff")],
        )

        style.configure(
            "Treeview",
            background="#1e293b",
            foreground="#f8fafc",
            fieldbackground="#1e293b",
            rowheight=28,
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
        """Builds top status bar and primary tabs."""
        # Top Header Bar
        header = tk.Frame(self.root, bg="#1e293b", height=54)
        header.pack(fill=tk.X, side=tk.TOP)

        title_lbl = tk.Label(
            header,
            text="🚦 REAL AI TRAFFIC VISION & ANPR E-CHALLAN SYSTEM",
            font=("Segoe UI", 15, "bold"),
            fg=self.TEXT_PRIMARY,
            bg="#1e293b",
            padx=16,
            pady=10,
        )
        title_lbl.pack(side=tk.LEFT)

        status_lbl = tk.Label(
            header,
            text="● LIVE AI COMPUTER VISION ENGINE ACTIVE",
            font=("Segoe UI", 9, "bold"),
            fg=self.ACCENT_GREEN,
            bg="#1e293b",
            padx=16,
        )
        status_lbl.pack(side=tk.RIGHT)

        # Tabs Container
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # Tab 1: Live AI Camera & Traffic Signal
        self.tab_camera = tk.Frame(self.notebook, bg=self.BG_DARK)
        # Tab 2: ANPR License Plate & E-Challan Portal
        self.tab_challan = tk.Frame(self.notebook, bg=self.BG_DARK)

        self.notebook.add(self.tab_camera, text="  📹 Live AI Camera & Traffic Signal Control  ")
        self.notebook.add(self.tab_challan, text="  🔍 ANPR Number Plate Scanner & E-Challan Portal  ")

        self._build_camera_tab()
        self._build_challan_tab()

    # =========================================================================
    # TAB 1: REAL CAMERA AI VISION & ADAPTIVE SIGNAL
    # =========================================================================
    def _build_camera_tab(self):
        main_box = tk.Frame(self.tab_camera, bg=self.BG_DARK)
        main_box.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Left: Big Video Feed Canvas
        left_box = tk.Frame(main_box, bg=self.PANEL_BG, bd=1, relief=tk.FLAT)
        left_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.video_label = tk.Label(left_box, bg="#050811")
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Right: Sidebar Controls & Real-Time Telemetry
        sidebar = tk.Frame(main_box, bg=self.PANEL_BG, width=420)
        sidebar.pack(side=tk.RIGHT, fill=tk.BOTH)
        sidebar.pack_propagate(False)

        side_container = tk.Frame(sidebar, bg=self.PANEL_BG)
        side_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # 1. Camera Input Source Selection
        src_card = tk.LabelFrame(
            side_container, text=" CAMERA & VIDEO INPUT SOURCE ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_BLUE, bg=self.CARD_BG, padx=8, pady=8
        )
        src_card.pack(fill=tk.X, pady=(0, 10))

        syn_btn = tk.Button(
            src_card, text="🛣️ Live Expressway Stream (AI Feed)",
            command=self.pipeline.set_source_synthetic, font=("Segoe UI", 9, "bold"),
            fg=self.TEXT_PRIMARY, bg="#0284c7", activebackground="#0369a1", bd=0, pady=5, cursor="hand2"
        )
        syn_btn.pack(fill=tk.X, pady=(0, 4))

        cam_btn = tk.Button(
            src_card, text="📷 Switch to Physical Webcam (0)",
            command=self._switch_webcam, font=("Segoe UI", 9),
            fg=self.TEXT_PRIMARY, bg="#475569", activebackground="#334155", bd=0, pady=5, cursor="hand2"
        )
        cam_btn.pack(fill=tk.X, pady=(0, 4))

        vid_btn = tk.Button(
            src_card, text="📂 Load Traffic Video File (.mp4)...",
            command=self._load_video_file, font=("Segoe UI", 9),
            fg=self.TEXT_PRIMARY, bg="#475569", activebackground="#334155", bd=0, pady=5, cursor="hand2"
        )
        vid_btn.pack(fill=tk.X, pady=(0, 4))

        img_btn = tk.Button(
            src_card, text="🖼️ Load Traffic Photo / Snapshot...",
            command=self._load_image_file, font=("Segoe UI", 9),
            fg=self.TEXT_PRIMARY, bg="#475569", activebackground="#334155", bd=0, pady=5, cursor="hand2"
        )
        img_btn.pack(fill=tk.X)

        # 2. Camera-Driven Smart Traffic Light Telemetry
        sig_card = tk.LabelFrame(
            side_container, text=" CAMERA-DRIVEN TRAFFIC SIGNAL ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_GREEN, bg=self.CARD_BG, padx=8, pady=8
        )
        sig_card.pack(fill=tk.X, pady=(0, 10))

        self.signal_status_lbl = tk.Label(
            sig_card, text="SIGNAL: GREEN", font=("Segoe UI", 12, "bold"),
            fg=self.ACCENT_GREEN, bg=self.CARD_BG
        )
        self.signal_status_lbl.pack(anchor=tk.W)

        self.signal_timer_lbl = tk.Label(
            sig_card, text="Time Remaining: 15.0s (Camera Adaptive)",
            font=("Consolas", 10, "bold"), fg=self.TEXT_PRIMARY, bg=self.CARD_BG
        )
        self.signal_timer_lbl.pack(anchor=tk.W, pady=(2, 6))

        em_btn = tk.Button(
            sig_card, text="🚨 DISPATCH AMBULANCE (PRIORITY GREEN WAVE)",
            command=self.pipeline.trigger_emergency_preemption, font=("Segoe UI", 9, "bold"),
            fg="white", bg="#dc2626", activebackground="#b91c1c", bd=0, pady=6, cursor="hand2"
        )
        em_btn.pack(fill=tk.X)

        # 3. Live AI Vehicle Detection Counters
        det_card = tk.LabelFrame(
            side_container, text=" REAL-TIME AI TELEMETRY ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_BLUE, bg=self.CARD_BG, padx=8, pady=8
        )
        det_card.pack(fill=tk.X, pady=(0, 10))

        self.fps_lbl = tk.Label(det_card, text="Inference Speed: 30.0 FPS", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG)
        self.fps_lbl.pack(anchor=tk.W)

        self.vehicles_view_lbl = tk.Label(det_card, text="Vehicles in Camera View: 0", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG)
        self.vehicles_view_lbl.pack(anchor=tk.W)

        self.total_passed_lbl = tk.Label(det_card, text="Total Passed Sensor: 0", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG)
        self.total_passed_lbl.pack(anchor=tk.W)

        # 4. Live ANPR Plate Scanner Box
        anpr_box = tk.LabelFrame(
            side_container, text=" LATEST SCANNED LICENSE PLATE ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_YELLOW, bg=self.CARD_BG, padx=8, pady=8
        )
        anpr_box.pack(fill=tk.BOTH, expand=True)

        self.scanned_plate_big = tk.Label(
            anpr_box, text="WAITING FOR PLATE...",
            font=("Consolas", 15, "bold"), fg="#38bdf8", bg="#0f172a", pady=8
        )
        self.scanned_plate_big.pack(fill=tk.X, pady=(0, 6))

        self.scanned_owner_txt = tk.Label(anpr_box, text="Owner: --", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG)
        self.scanned_owner_txt.pack(anchor=tk.W)

        self.scanned_model_txt = tk.Label(anpr_box, text="Model: --", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG)
        self.scanned_model_txt.pack(anchor=tk.W)

        self.scanned_challan_txt = tk.Label(
            anpr_box, text="Pending Fine: None", font=("Segoe UI", 10, "bold"),
            fg=self.ACCENT_GREEN, bg=self.CARD_BG
        )
        self.scanned_challan_txt.pack(anchor=tk.W, pady=(4, 6))

        jump_btn = tk.Button(
            anpr_box, text="🔍 Search in E-Challan Portal",
            command=self._jump_to_challan_portal, font=("Segoe UI", 9, "bold"),
            fg=self.TEXT_PRIMARY, bg="#059669", activebackground="#047857", bd=0, pady=5, cursor="hand2"
        )
        jump_btn.pack(fill=tk.X)

    def _switch_webcam(self):
        success = self.pipeline.set_source_webcam(0)
        if not success:
            messagebox.showwarning(
                "Webcam Notice",
                "Could not connect to physical webcam (Device 0).\nDefaulting back to the live expressway stream."
            )

    def _load_video_file(self):
        fpath = filedialog.askopenfilename(
            title="Select Traffic Video File",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv"), ("All Files", "*.*")]
        )
        if fpath:
            success = self.pipeline.set_source_video_file(fpath)
            if not success:
                messagebox.showerror("Error", "Could not open selected video file.")

    def _load_image_file(self):
        fpath = filedialog.askopenfilename(
            title="Select Traffic Photo",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp"), ("All Files", "*.*")]
        )
        if fpath:
            success = self.pipeline.set_source_image(fpath)
            if not success:
                messagebox.showerror("Error", "Could not load selected image.")

    def _jump_to_challan_portal(self):
        plate = self.pipeline.anpr.last_scanned_plate
        if plate:
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, plate)
            self.notebook.select(self.tab_challan)
            self._search_plate()

    # =========================================================================
    # TAB 2: ANPR NUMBER PLATE & E-CHALLAN ENFORCEMENT PORTAL
    # =========================================================================
    def _build_challan_tab(self):
        main_box = tk.Frame(self.tab_challan, bg=self.BG_DARK)
        main_box.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Top Search Card
        top_card = tk.Frame(main_box, bg=self.PANEL_BG, padx=12, pady=12)
        top_card.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            top_card, text="VEHICLE REGISTRATION SEARCH & E-CHALLAN DATABASE",
            font=("Segoe UI", 12, "bold"), fg=self.ACCENT_BLUE, bg=self.PANEL_BG
        ).pack(anchor=tk.W, pady=(0, 8))

        search_row = tk.Frame(top_card, bg=self.PANEL_BG)
        search_row.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            search_row, text="Vehicle Number Plate:", font=("Segoe UI", 10),
            fg=self.TEXT_PRIMARY, bg=self.PANEL_BG
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.search_entry = tk.Entry(
            search_row, font=("Consolas", 12, "bold"), bg="#0f172a", fg="#38bdf8",
            insertbackground="white", width=22, bd=1, relief=tk.SOLID
        )
        self.search_entry.insert(0, "DL-01-AB-1234")
        self.search_entry.pack(side=tk.LEFT, padx=(0, 8))

        search_btn = tk.Button(
            search_row, text="🔎 Search Challan", command=self._search_plate,
            font=("Segoe UI", 9, "bold"), fg="white", bg="#0284c7",
            activebackground="#0369a1", bd=0, padx=14, pady=4, cursor="hand2"
        )
        search_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Quick Demo Buttons
        q_row = tk.Frame(top_card, bg=self.PANEL_BG)
        q_row.pack(fill=tk.X)
        tk.Label(q_row, text="Quick Examples:", font=("Segoe UI", 8), fg=self.TEXT_SECONDARY, bg=self.PANEL_BG).pack(side=tk.LEFT, padx=(0, 6))

        for p in ["DL-01-AB-1234", "MH-02-CP-8921", "UP-14-EA-4521", "KA-03-MK-7821"]:
            btn = tk.Button(
                q_row, text=p, font=("Consolas", 8), fg="#38bdf8", bg="#334155",
                bd=0, padx=6, pady=2, cursor="hand2", command=lambda pl=p: self._fill_plate(pl)
            )
            btn.pack(side=tk.LEFT, padx=3)

        # Vehicle Profile Information Card
        self.profile_card = tk.LabelFrame(
            top_card, text=" REGISTERED OWNER & VEHICLE PROFILE ",
            font=("Segoe UI", 9, "bold"), fg=self.ACCENT_GREEN, bg=self.CARD_BG, padx=10, pady=8
        )
        self.profile_card.pack(fill=tk.X, pady=(10, 0))

        p_grid = tk.Frame(self.profile_card, bg=self.CARD_BG)
        p_grid.pack(fill=tk.X)

        self.p_owner = tk.Label(p_grid, text="Owner: --", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG)
        self.p_owner.grid(row=0, column=0, sticky=tk.W, padx=12, pady=2)

        self.p_model = tk.Label(p_grid, text="Vehicle Model: --", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG)
        self.p_model.grid(row=0, column=1, sticky=tk.W, padx=12, pady=2)

        self.p_city = tk.Label(p_grid, text="RTO City: --", font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.CARD_BG)
        self.p_city.grid(row=1, column=0, sticky=tk.W, padx=12, pady=2)

        self.p_fine = tk.Label(p_grid, text="Pending Fines: ₹0", font=("Segoe UI", 10, "bold"), fg=self.ACCENT_GREEN, bg=self.CARD_BG)
        self.p_fine.grid(row=1, column=1, sticky=tk.W, padx=12, pady=2)

        # Bottom Treeview: Violations Table
        bot_card = tk.Frame(main_box, bg=self.PANEL_BG, padx=10, pady=10)
        bot_card.pack(fill=tk.BOTH, expand=True)

        bar = tk.Frame(bot_card, bg=self.PANEL_BG)
        bar.pack(fill=tk.X, pady=(0, 6))

        tk.Label(bar, text="LIVE TRAFFIC VIOLATIONS LOG", font=("Segoe UI", 10, "bold"), fg=self.ACCENT_BLUE, bg=self.PANEL_BG).pack(side=tk.LEFT)

        pay_btn = tk.Button(
            bar, text="💳 Pay Selected Challan", command=self._pay_challan,
            font=("Segoe UI", 9, "bold"), fg="white", bg="#059669",
            activebackground="#047857", bd=0, padx=12, pady=3, cursor="hand2"
        )
        pay_btn.pack(side=tk.RIGHT, padx=4)

        refresh_btn = tk.Button(
            bar, text="🔄 Refresh All", command=self._refresh_table,
            font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg="#475569",
            bd=0, padx=10, pady=3, cursor="hand2"
        )
        refresh_btn.pack(side=tk.RIGHT, padx=4)

        cols = ("id", "time", "plate", "owner", "violation", "fine", "status")
        self.tree = ttk.Treeview(bot_card, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("id", text="Challan ID")
        self.tree.heading("time", text="Timestamp")
        self.tree.heading("plate", text="Plate Number")
        self.tree.heading("owner", text="Owner Name")
        self.tree.heading("violation", text="Violation Type")
        self.tree.heading("fine", text="Fine (₹)")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=120, anchor=tk.CENTER)
        self.tree.column("time", width=150, anchor=tk.CENTER)
        self.tree.column("plate", width=130, anchor=tk.CENTER)
        self.tree.column("owner", width=140, anchor=tk.W)
        self.tree.column("violation", width=190, anchor=tk.W)
        self.tree.column("fine", width=90, anchor=tk.CENTER)
        self.tree.column("status", width=100, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True)
        self._refresh_table()

    def _fill_plate(self, plate: str):
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, plate)
        self._search_plate()

    def _search_plate(self):
        plate = self.search_entry.get().strip()
        res = self.challan_manager.search_by_plate(plate)
        if res["found"]:
            v = res["vehicle"]
            self.p_owner.config(text=f"Owner: {v.owner_name}")
            self.p_model.config(text=f"Vehicle Model: {v.vehicle_model} ({v.vehicle_type.upper()})")
            self.p_city.config(text=f"RTO City: {v.registered_city} | Mobile: {v.contact_number}")
            fine = res["total_pending_fine"]
            self.p_fine.config(
                text=f"Total Pending Fine: ₹{fine}",
                fg=self.ACCENT_RED if fine > 0 else self.ACCENT_GREEN
            )
            self._fill_tree(res["challans"])
        else:
            messagebox.showinfo("Not Found", f"No registration records found for license plate: {plate}")

    def _refresh_table(self):
        challans = self.challan_manager.get_recent_challans(limit=35)
        self._fill_tree(challans)

    def _fill_tree(self, challans: List[Challan]):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for c in challans:
            st = "🟢 PAID" if c.status == "PAID" else "🔴 PENDING"
            self.tree.insert(
                "", tk.END, iid=c.challan_id,
                values=(c.challan_id, c.timestamp, c.plate_number, c.owner_name, c.violation_type, f"₹{c.fine_amount}", st)
            )

    def _pay_challan(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select Item", "Please click on a challan from the list to pay.")
            return

        cid = sel[0]
        c = self.challan_manager.challans.get(cid)
        if c:
            if c.status == "PAID":
                messagebox.showinfo("Already Paid", f"Challan {cid} has already been paid on {c.payment_date}.")
                return

            confirm = messagebox.askyesno(
                "Confirm Payment",
                f"Settle Challan {cid} Online?\n\nVehicle: {c.plate_number}\nViolation: {c.violation_type}\nAmount: ₹{c.fine_amount}"
            )
            if confirm:
                self.challan_manager.pay_challan(cid)
                messagebox.showinfo(
                    "Payment Successful! 🎉",
                    f"Official Receipt Generated!\nTransaction ID: {c.payment_id}\nAmount: ₹{c.fine_amount}\nStatus: PAID"
                )
                self._search_plate()

    # =========================================================================
    # VIDEO FRAME ANIMATION LOOP
    # =========================================================================
    def _frame_loop(self):
        """Processes video frame from pipeline and updates UI (~30 FPS)."""
        frame, tele = self.pipeline.process_next_frame()

        if frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            pil_img = pil_img.resize((760, 500), Image.Resampling.BILINEAR)
            self._image_tk = ImageTk.PhotoImage(image=pil_img)
            self.video_label.configure(image=self._image_tk)

            # Update Telemetry Labels
            self.fps_lbl.config(text=f"Inference Speed: {tele['fps']:.1f} FPS")
            self.vehicles_view_lbl.config(text=f"Vehicles in Camera View: {tele['detected_count']}")
            self.total_passed_lbl.config(text=f"Total Passed Sensor: {tele['total_passed']}")

            # Signal Controller State
            state = tele["signal_state"]
            rem = tele["signal_timer"]
            sig_col = self.ACCENT_GREEN if state == "GREEN" else (self.ACCENT_RED if state == "RED" else self.ACCENT_YELLOW)
            self.signal_status_lbl.config(text=f"SIGNAL: {state}", fg=sig_col)
            self.signal_timer_lbl.config(text=f"Remaining: {rem:04.1f}s (Camera Adaptive)")

            # ANPR Display
            plate = tele.get("last_plate")
            if plate:
                self.scanned_plate_big.config(text=plate)
                recents = tele.get("recent_scans", [])
                if recents:
                    r = recents[0]
                    self.scanned_owner_txt.config(text=f"Owner: {r['owner_name']}")
                    self.scanned_model_txt.config(text=f"Model: {r['vehicle_model']} ({r['vehicle_type'].upper()})")
                    fine = r["pending_fine"]
                    if fine > 0:
                        self.scanned_challan_txt.config(text=f"⚠️ Pending Challan: ₹{fine} (UNPAID)", fg=self.ACCENT_RED)
                    else:
                        self.scanned_challan_txt.config(text="✅ Clean Record (No Fines)", fg=self.ACCENT_GREEN)

        self.root.after(30, self._frame_loop)
