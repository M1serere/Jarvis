from __future__ import annotations

import math
import time
import threading
import tkinter as tk
from collections import deque

from core.config import UI_WINDOW_TITLE
from services.system_monitor import SystemMonitor


class StatusWindow:
    BG = "#03131f"
    PANEL = "#071f33"
    PANEL_2 = "#0a2740"
    LINE = "#123a58"
    CYAN = "#69e6ff"
    CYAN_SOFT = "#3aa9d6"
    TEXT = "#d8f6ff"
    TEXT_DIM = "#7db6c8"
    ALERT = "#8ff7ff"
    GRID = "#0b2537"
    PULSE = "#a6f6ff"

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(UI_WINDOW_TITLE)
        self.root.configure(bg=self.BG)

        # overlay / fullscreen / borderless
        self.overlay_mode = True
        self.windowed_geometry = "980x620+80+60"
        self.root.geometry(self.windowed_geometry)
        self.root.minsize(980, 620)

        try:
            self.root.overrideredirect(True)
        except Exception:
            pass

        try:
            self.root.attributes("-topmost", True)
        except Exception:
            pass

        try:
            self.root.attributes("-alpha", 0.93)
        except Exception:
            pass

        self.root.bind("<Escape>", self._exit_app)
        self.root.bind("<F11>", self._toggle_overlay_mode)
        self.root.bind("<Control-F11>", self._toggle_window_mode)
        self.root.bind("<Map>", self._handle_window_restore)

        self.status_var = tk.StringVar(value="ГОТОВ")
        self.detail_var = tk.StringVar(value="Система в режиме ожидания")
        self.clock_var = tk.StringVar(value="00:00:00")

        self.monitor = SystemMonitor()
        self.stats_history: dict[str, list[float]] = {
            "cpu": [],
            "ram": [],
            "disk": [],
            "net_rx": [],
            "net_tx": [],
        }
        self.max_points = 90

        self.command_history = deque(maxlen=6)

        self._angle = 0.0
        self._pulse_phase = 0.0
        self._pulse_level = 0.25
        self._mic_phase = 0.0

        self._build_layout()
        self.root.bind("<Configure>", self._on_resize)

        self._set_fullscreen_overlay()

        self._push_log("BOOT SEQUENCE STARTED")
        self._push_log("VISUAL CORE ONLINE")
        self._push_log("VOICE CHANNEL READY")
        self._push_log("OVERLAY MODE ENABLED")

        self._update_clock()
        self._update_stats_loop()
        self._animate()

    def _build_layout(self) -> None:
        self.main = tk.Frame(self.root, bg=self.BG)
        self.main.pack(fill="both", expand=True, padx=14, pady=14)

        self.left_panel = tk.Frame(
            self.main,
            bg=self.PANEL,
            highlightbackground=self.LINE,
            highlightthickness=1,
        )
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.right_panel = tk.Frame(
            self.main,
            bg=self.PANEL,
            width=320,
            highlightbackground=self.LINE,
            highlightthickness=1,
        )
        self.right_panel.pack(side="right", fill="y")
        self.right_panel.pack_propagate(False)

        self.canvas = tk.Canvas(
            self.left_panel,
            bg=self.BG,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.top_bar = tk.Frame(self.canvas, bg=self.BG)
        self.canvas.create_window(
            24,
            18,
            anchor="nw",
            window=self.top_bar,
            tags="top_bar",
        )

        self.title_label = tk.Label(
            self.top_bar,
            text="JARVIS INTERFACE",
            bg=self.BG,
            fg=self.CYAN,
            font=("Segoe UI", 18, "bold"),
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = tk.Label(
            self.top_bar,
            text="TACTICAL OVERLAY / LIVE SYSTEM VISUALIZATION",
            bg=self.BG,
            fg=self.TEXT_DIM,
            font=("Consolas", 10),
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        self.window_controls = tk.Frame(self.canvas, bg=self.BG)
        self.canvas.create_window(
            0,
            18,
            anchor="ne",
            window=self.window_controls,
            tags="window_controls",
        )

        self.minimize_button = tk.Button(
            self.window_controls,
            text="_",
            command=self._minimize_window,
            bg=self.PANEL_2,
            fg=self.CYAN,
            activebackground=self.LINE,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.LINE,
            font=("Consolas", 12, "bold"),
            width=3,
            cursor="hand2",
        )
        self.minimize_button.pack(anchor="e")

        self.right_title = tk.Label(
            self.right_panel,
            text="JARVIS STATUS",
            bg=self.PANEL,
            fg=self.CYAN,
            font=("Segoe UI", 16, "bold"),
        )
        self.right_title.pack(anchor="w", padx=16, pady=(16, 10))

        self.clock_label = tk.Label(
            self.right_panel,
            textvariable=self.clock_var,
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Consolas", 18, "bold"),
        )
        self.clock_label.pack(anchor="w", padx=16, pady=(0, 14))

        self.block_status = self._make_info_block("STATUS", "READY")
        self.block_detail = self._make_info_block("DETAIL", "WAITING")
        self.block_mode = self._make_info_block("VOICE MODE", "WAKE WORD")
        self.block_core = self._make_info_block("CORE", "ONLINE")
        self.block_audio = self._make_info_block("AUDIO LINK", "STANDBY")

        # микрофон справа под статусами
        self.mic_frame = tk.Frame(
            self.right_panel,
            bg=self.PANEL_2,
            highlightbackground=self.LINE,
            highlightthickness=1,
        )
        self.mic_frame.pack(fill="x", padx=16, pady=(10, 10))

        tk.Label(
            self.mic_frame,
            text="VOICE SENSOR",
            bg=self.PANEL_2,
            fg=self.CYAN,
            font=("Consolas", 10, "bold"),
        ).pack(anchor="w", padx=10, pady=(8, 4))

        self.mic_canvas = tk.Canvas(
            self.mic_frame,
            width=260,
            height=110,
            bg=self.PANEL_2,
            highlightthickness=0,
            bd=0,
        )
        self.mic_canvas.pack(fill="x", padx=8, pady=(0, 8))

        self.log_title = tk.Label(
            self.right_panel,
            text="LIVE TELEMETRY",
            bg=self.PANEL,
            fg=self.CYAN_SOFT,
            font=("Segoe UI", 12, "bold"),
        )
        self.log_title.pack(anchor="w", padx=16, pady=(8, 8))

        self.log_box = tk.Text(
            self.right_panel,
            height=12,
            bg=self.PANEL_2,
            fg=self.TEXT_DIM,
            insertbackground=self.CYAN,
            relief="flat",
            bd=0,
            font=("Consolas", 9),
            padx=10,
            pady=10,
        )
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.log_box.configure(state="disabled")

    def _make_info_block(self, title: str, value: str) -> tk.Label:
        outer = tk.Frame(
            self.right_panel,
            bg=self.PANEL_2,
            highlightbackground=self.LINE,
            highlightthickness=1,
        )
        outer.pack(fill="x", padx=16, pady=5)

        tk.Label(
            outer,
            text=title,
            bg=self.PANEL_2,
            fg=self.TEXT_DIM,
            font=("Consolas", 9),
        ).pack(anchor="w", padx=10, pady=(8, 0))

        value_label = tk.Label(
            outer,
            text=value,
            bg=self.PANEL_2,
            fg=self.TEXT,
            font=("Segoe UI", 12, "bold"),
            justify="left",
            wraplength=250,
        )
        value_label.pack(anchor="w", padx=10, pady=(2, 8))
        return value_label

    def _on_resize(self, _event=None) -> None:
        self.canvas.coords("top_bar", 24, 18)
        canvas_width = max(self.canvas.winfo_width(), 200)
        self.canvas.coords("window_controls", canvas_width - 24, 18)

    def _set_fullscreen_overlay(self) -> None:
        try:
            self.root.overrideredirect(True)
        except Exception:
            pass

        try:
            self.root.state("zoomed")
        except Exception:
            self.root.attributes("-fullscreen", True)

    def _set_windowed_mode(self) -> None:
        try:
            self.root.attributes("-fullscreen", False)
        except Exception:
            pass

        try:
            self.root.overrideredirect(False)
        except Exception:
            pass

        self.root.geometry(self.windowed_geometry)

    def _toggle_overlay_mode(self, _event=None) -> None:
        if self.overlay_mode:
            self.overlay_mode = False
            self._set_windowed_mode()
            self._push_log("OVERLAY MODE DISABLED")
        else:
            self.overlay_mode = True
            self._set_fullscreen_overlay()
            self._push_log("OVERLAY MODE ENABLED")

    def _toggle_window_mode(self, _event=None) -> None:
        self._toggle_overlay_mode()

    def _exit_app(self, _event=None) -> None:
        self.root.destroy()

    def _minimize_window(self) -> None:
        try:
            self.root.overrideredirect(False)
        except Exception:
            pass
        self.root.iconify()

    def _handle_window_restore(self, _event=None) -> None:
        if self.root.state() == "iconic":
            return
        if self.overlay_mode:
            self.root.after(10, self._set_fullscreen_overlay)

    def set_status(self, status: str, detail: str = "") -> None:
        self.root.after(0, self._apply_status, status, detail)

    def _apply_status(self, status: str, detail: str) -> None:
        status_upper = status.upper()
        detail = detail or "..."

        self.status_var.set(status_upper)
        self.detail_var.set(detail)

        self.block_status.configure(text=status_upper)
        self.block_detail.configure(text=detail)

        normalized = status.strip().lower()

        if "слуш" in normalized:
            self._pulse_level = 0.60
            self.block_audio.configure(text="INPUT CAPTURE")
            self.block_core.configure(text="ANALYZING")
            self._push_log("VOICE INPUT DETECTED")
        elif "дум" in normalized:
            self._pulse_level = 0.90
            self.block_audio.configure(text="SIGNAL LOCK")
            self.block_core.configure(text="PROCESSING")
            self._push_log("INTENT ANALYSIS RUNNING")
        elif "выполня" in normalized:
            self._pulse_level = 1.00
            self.block_audio.configure(text="COMMAND RELAY")
            self.block_core.configure(text="EXECUTING")
            self._push_log(f"EXECUTION: {detail}")
        elif "говор" in normalized:
            self._pulse_level = 0.95
            self.block_audio.configure(text="VOICE OUTPUT")
            self.block_core.configure(text="RESPONDING")
            self._push_log("SPEECH SYNTHESIS ACTIVE")
        elif "актив" in normalized:
            self._pulse_level = 0.80
            self.block_audio.configure(text="WAKE CONFIRMED")
            self.block_core.configure(text="ONLINE")
            self._push_log("WAKE WORD ACCEPTED")
        else:
            self._pulse_level = 0.25
            self.block_audio.configure(text="STANDBY")
            self.block_core.configure(text="ONLINE")
            self._push_log("SYSTEM IDLE")

    def add_user_command(self, text: str) -> None:
        if not text:
            return
        self.root.after(0, self._add_user_command_ui, text)

    def _add_user_command_ui(self, text: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        line = f"[{stamp}] {text}"
        self.command_history.appendleft(line)
        self._push_log(f"USER: {text}")

    def _push_log(self, text: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        line = f"[{stamp}] {text}\n"

        self.log_box.configure(state="normal")
        self.log_box.insert("end", line)
        lines = self.log_box.get("1.0", "end").splitlines()
        if len(lines) > 120:
            self.log_box.delete("1.0", f"{len(lines) - 120}.0")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _update_clock(self) -> None:
        self.clock_var.set(time.strftime("%H:%M:%S"))
        self.root.after(1000, self._update_clock)

    def _append_history(self, key: str, value: float) -> None:
        history = self.stats_history[key]
        history.append(value)
        if len(history) > self.max_points:
            del history[0]

    def _update_stats_loop(self) -> None:
        try:
            stats = self.monitor.get_stats()
            self._append_history("cpu", stats.cpu_percent)
            self._append_history("ram", stats.memory_percent)
            self._append_history("disk", stats.disk_percent)
            self._append_history("net_rx", min(stats.net_recv_kbps / 20.0, 100.0))
            self._append_history("net_tx", min(stats.net_sent_kbps / 20.0, 100.0))
        except Exception as exc:
            self._push_log(f"STATS ERROR: {exc}")

        self.root.after(1000, self._update_stats_loop)

    def _animate(self) -> None:
        self.canvas.delete("hud")
        self.mic_canvas.delete("all")

        width = max(self.canvas.winfo_width(), 600)
        height = max(self.canvas.winfo_height(), 400)

        self._draw_grid(width, height)
        self._draw_chart_panel(width, height)
        self._draw_command_history(width, height)
        self._draw_mic_icon()

        self._angle += 2.0
        self._pulse_phase += 0.18
        self._mic_phase += 0.24

        self.root.after(80, self._animate)

    def _draw_grid(self, width: int, height: int) -> None:
        step = 37

        for x in range(0, width, step):
            self.canvas.create_line(
                x, 0, x, height,
                fill=self.GRID,
                width=1,
                tags="hud",
            )

        for y in range(0, height, step):
            self.canvas.create_line(
                0, y, width, y,
                fill=self.GRID,
                width=1,
                tags="hud",
            )

        for y in range(0, height, 148):
            self.canvas.create_line(
                0, y, width, y,
                fill="#10344d",
                width=1,
                tags="hud",
            )

    def _draw_chart_panel(self, width: int, height: int) -> None:
        left = 28
        right = width - 28
        top = 90
        bottom = height - 170

        self.canvas.create_text(
            left,
            60,
            anchor="w",
            text="LIVE SYSTEM GRAPHS",
            fill=self.CYAN,
            font=("Segoe UI", 18, "bold"),
            tags="hud",
        )

        self.canvas.create_text(
            left,
            82,
            anchor="w",
            text="CPU / RAM / DISK / NETWORK",
            fill=self.TEXT_DIM,
            font=("Consolas", 10),
            tags="hud",
        )

        col_gap = 16
        row_gap = 16

        chart_w = (right - left - col_gap) / 2
        chart_h = (bottom - top - row_gap) / 3

        charts = [
            ("CPU", self.stats_history["cpu"], 0, 0, self._cpu_label()),
            ("RAM", self.stats_history["ram"], 1, 0, self._ram_label()),
            ("DISK", self.stats_history["disk"], 2, 0, self._disk_label()),
            ("NET RX", self.stats_history["net_rx"], 0, 1, self._net_rx_label()),
            ("NET TX", self.stats_history["net_tx"], 1, 1, self._net_tx_label()),
        ]

        for title, values, row, col, value_text in charts:
            x1 = left + col * (chart_w + col_gap)
            y1 = top + row * (chart_h + row_gap)
            x2 = x1 + chart_w
            y2 = y1 + chart_h
            self._draw_single_chart(x1, y1, x2, y2, title, values, value_text)

        x1 = left + 1 * (chart_w + col_gap)
        y1 = top + 2 * (chart_h + row_gap)
        x2 = x1 + chart_w
        y2 = y1 + chart_h

        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=self.LINE,
            width=1,
            tags="hud",
        )
        self.canvas.create_text(
            x1 + 14,
            y1 + 14,
            anchor="nw",
            text="JARVIS CORE",
            fill=self.CYAN,
            font=("Consolas", 10, "bold"),
            tags="hud",
        )
        self.canvas.create_text(
            x1 + 14,
            y1 + 42,
            anchor="nw",
            text=f"STATUS   {self.status_var.get()}",
            fill=self.TEXT,
            font=("Consolas", 10),
            tags="hud",
        )
        self.canvas.create_text(
            x1 + 14,
            y1 + 64,
            anchor="nw",
            text=f"DETAIL   {self.detail_var.get()[:30]}",
            fill=self.TEXT_DIM,
            font=("Consolas", 10),
            tags="hud",
        )
        self.canvas.create_text(
            x1 + 14,
            y1 + 92,
            anchor="nw",
            text="HUD NODE ACTIVE",
            fill=self.CYAN_SOFT,
            font=("Consolas", 10),
            tags="hud",
        )

    def _draw_single_chart(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        title: str,
        values: list[float],
        value_text: str,
    ) -> None:
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=self.LINE,
            width=1,
            tags="hud",
        )

        self.canvas.create_text(
            x1 + 12,
            y1 + 10,
            anchor="nw",
            text=title,
            fill=self.CYAN,
            font=("Consolas", 10, "bold"),
            tags="hud",
        )

        self.canvas.create_text(
            x2 - 12,
            y1 + 10,
            anchor="ne",
            text=value_text,
            fill=self.TEXT,
            font=("Consolas", 10),
            tags="hud",
        )

        plot_left = x1 + 10
        plot_top = y1 + 32
        plot_right = x2 - 10
        plot_bottom = y2 - 10

        for i in range(1, 4):
            yy = plot_top + (plot_bottom - plot_top) * i / 4
            self.canvas.create_line(
                plot_left, yy, plot_right, yy,
                fill="#10344d",
                width=1,
                tags="hud",
            )

        if len(values) < 2:
            return

        points = []
        fill_points = [plot_left, plot_bottom]
        count = len(values)
        width = plot_right - plot_left
        height = plot_bottom - plot_top

        for idx, value in enumerate(values):
            x = plot_left + (width * idx / max(count - 1, 1))
            y = plot_bottom - (max(0.0, min(value, 100.0)) / 100.0) * height
            points.extend([x, y])
            fill_points.extend([x, y])

        fill_points.extend([plot_right, plot_bottom])

        self.canvas.create_polygon(
            *fill_points,
            fill="#0a3852",
            outline="",
            stipple="gray25",
            tags="hud",
        )

        self.canvas.create_line(
            *points,
            fill=self.CYAN,
            width=2,
            smooth=True,
            tags="hud",
        )

    def _draw_command_history(self, width: int, height: int) -> None:
        x1 = 28
        x2 = width - 28
        y2 = height - 24
        y1 = y2 - 112

        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=self.LINE,
            width=1,
            tags="hud",
        )

        self.canvas.create_text(
            x1 + 14,
            y1 + 12,
            anchor="nw",
            text="LAST USER COMMANDS",
            fill=self.CYAN,
            font=("Consolas", 10, "bold"),
            tags="hud",
        )

        if not self.command_history:
            self.canvas.create_text(
                x1 + 14,
                y1 + 42,
                anchor="nw",
                text="История пока пуста",
                fill=self.TEXT_DIM,
                font=("Consolas", 10),
                tags="hud",
            )
            return

        for idx, item in enumerate(list(self.command_history)[:5]):
            self.canvas.create_text(
                x1 + 14,
                y1 + 38 + idx * 18,
                anchor="nw",
                text=item[:120],
                fill=self.TEXT if idx == 0 else self.TEXT_DIM,
                font=("Consolas", 9),
                tags="hud",
            )

    def _draw_center_pulse(self, width: int, height: int) -> None:
        cx = width * 0.50
        cy = height * 0.52
        pulse = (math.sin(self._pulse_phase) + 1.0) / 2.0
        pulse_strength = 8 + 22 * self._pulse_level * pulse

        r1 = 34 + pulse_strength * 0.35
        r2 = 58 + pulse_strength * 0.55
        r3 = 92 + pulse_strength * 0.85

        self.canvas.create_oval(
            cx - r3, cy - r3, cx + r3, cy + r3,
            outline="#0c5c87",
            width=2,
            tags="hud",
        )
        self.canvas.create_oval(
            cx - r2, cy - r2, cx + r2, cy + r2,
            outline=self.CYAN_SOFT,
            width=2,
            tags="hud",
        )
        self.canvas.create_oval(
            cx - r1, cy - r1, cx + r1, cy + r1,
            outline=self.PULSE,
            width=3,
            tags="hud",
        )

        arc_extent = 35 + 120 * self._pulse_level
        self.canvas.create_arc(
            cx - r3 - 10,
            cy - r3 - 10,
            cx + r3 + 10,
            cy + r3 + 10,
            start=self._angle * 2,
            extent=arc_extent,
            style="arc",
            outline=self.ALERT,
            width=4,
            tags="hud",
        )

        self.canvas.create_text(
            cx,
            cy,
            text="J",
            fill=self.TEXT,
            font=("Segoe UI", 30, "bold"),
            tags="hud",
        )

    def _draw_mic_icon(self) -> None:
        w = max(self.mic_canvas.winfo_width(), 200)
        h = max(self.mic_canvas.winfo_height(), 100)

        cx = w / 2
        cy = h / 2 + 6

        pulse = (math.sin(self._mic_phase) + 1.0) / 2.0
        amp = 6 + pulse * 10 * self._pulse_level

        ring_r = 34 + amp

        self.mic_canvas.create_oval(
            cx - ring_r,
            cy - ring_r,
            cx + ring_r,
            cy + ring_r,
            outline="#0f4a6d",
            width=2,
        )

        self.mic_canvas.create_oval(
            cx - 16,
            cy - 28,
            cx + 16,
            cy + 6,
            outline=self.CYAN,
            width=3,
        )

        self.mic_canvas.create_line(
            cx,
            cy + 6,
            cx,
            cy + 26,
            fill=self.CYAN,
            width=3,
        )

        self.mic_canvas.create_arc(
            cx - 24,
            cy - 8,
            cx + 24,
            cy + 28,
            start=200,
            extent=140,
            style="arc",
            outline=self.CYAN_SOFT,
            width=3,
        )

        self.mic_canvas.create_line(
            cx - 18,
            cy + 32,
            cx + 18,
            cy + 32,
            fill=self.CYAN,
            width=3,
        )

        for i in range(5):
            x = cx - 52 + i * 26
            bar_h = 8 + abs(math.sin(self._mic_phase + i * 0.7)) * (10 + 20 * self._pulse_level)
            self.mic_canvas.create_line(
                x,
                h - 18,
                x,
                h - 18 - bar_h,
                fill=self.ALERT if i == 2 else self.CYAN_SOFT,
                width=3,
            )

    def _cpu_label(self) -> str:
        if not self.stats_history["cpu"]:
            return "--"
        return f"{self.stats_history['cpu'][-1]:.0f}%"

    def _ram_label(self) -> str:
        if not self.stats_history["ram"]:
            return "--"
        return f"{self.stats_history['ram'][-1]:.0f}%"

    def _disk_label(self) -> str:
        if not self.stats_history["disk"]:
            return "--"
        return f"{self.stats_history['disk'][-1]:.0f}%"

    def _net_rx_label(self) -> str:
        if not self.stats_history["net_rx"]:
            return "--"
        return f"{self.stats_history['net_rx'][-1] * 20:.0f} KB/s"

    def _net_tx_label(self) -> str:
        if not self.stats_history["net_tx"]:
            return "--"
        return f"{self.stats_history['net_tx'][-1] * 20:.0f} KB/s"

    def start_in_thread(self) -> None:
        thread = threading.Thread(target=self.root.mainloop, daemon=True)
        thread.start()

    def run(self) -> None:
        self.root.mainloop()
