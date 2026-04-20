from __future__ import annotations

import ctypes
import math
import time
import tkinter as tk
from collections import deque
from collections.abc import Callable

from core.config import UI_WINDOW_TITLE
from services.system_monitor import SystemMonitor


class StatusWindow:
    BG = "#03131f"
    PANEL = "#071f33"
    PANEL_2 = "#0a2740"
    LINE = "#123a58"
    CYAN = "#69E6FF"
    CYAN_SOFT = "#3AA9D6"
    TEXT = "#D8F6FF"
    TEXT_DIM = "#7DB6C8"
    GRID = "#0B2537"

    def __init__(
        self,
        voice_volume: int = 80,
        on_voice_volume_change: Callable[[int], None] | None = None,
        autostart_enabled: bool = False,
        on_autostart_change: Callable[[bool], None] | None = None,
        overlay_mode: bool = True,
        on_overlay_mode_change: Callable[[bool], None] | None = None,
    ) -> None:
        self.root = tk.Tk()
        self.root.title(UI_WINDOW_TITLE)
        self.root.configure(bg=self.BG)
        self.root.protocol("WM_DELETE_WINDOW", self._exit_app)

        self.overlay_mode = overlay_mode
        self.windowed_geometry = "980x620+80+60"
        self.root.geometry(self.windowed_geometry)
        self.root.minsize(980, 620)

        try:
            self.root.overrideredirect(False)
        except Exception:
            pass

        try:
            self.root.attributes("-topmost", False)
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
        self.root.bind("<Button-1>", self._handle_global_click, add="+")

        self.status_var = tk.StringVar(value="ГОТОВ")
        self.detail_var = tk.StringVar(value="Система в режиме ожидания")
        self.clock_var = tk.StringVar(value="00:00:00")
        self.voice_volume_var = tk.IntVar(value=max(0, min(voice_volume, 100)))
        self.voice_volume_text_var = tk.StringVar()
        self.autostart_var = tk.BooleanVar(value=autostart_enabled)
        self._on_voice_volume_change = on_voice_volume_change
        self._on_autostart_change = on_autostart_change
        self._on_overlay_mode_change = on_overlay_mode_change
        self._settings_menu_visible = False
        self._restoring_from_minimize = False

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

        self._pulse_level = 0.25

        self._build_layout()
        self._update_volume_label(self.voice_volume_var.get())
        self.root.bind("<Configure>", self._on_resize)

        if self.overlay_mode:
            self._set_fullscreen_overlay()
        else:
            self._set_windowed_mode()

        self._push_log("BOOT SEQUENCE STARTED")
        self._push_log("VISUAL CORE ONLINE")
        self._push_log("VOICE CHANNEL READY")
        self._push_log("OVERLAY MODE ENABLED" if self.overlay_mode else "WINDOWED MODE ENABLED")

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
        self.canvas.create_window(24, 18, anchor="nw", window=self.top_bar, tags="top_bar")

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

        self.close_button = tk.Button(
            self.window_controls,
            text="X",
            command=self._exit_app,
            bg=self.PANEL_2,
            fg=self.CYAN,
            activebackground="#5B1B24",
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.LINE,
            font=("Consolas", 12, "bold"),
            width=3,
            cursor="hand2",
        )
        self.close_button.pack(side="right", anchor="e")

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
        self.minimize_button.pack(side="right", anchor="e", padx=(0, 6))

        self.header_frame = tk.Frame(self.right_panel, bg=self.PANEL)
        self.header_frame.pack(fill="x", padx=16, pady=(16, 10))

        self.right_title = tk.Label(
            self.header_frame,
            text="JARVIS STATUS",
            bg=self.PANEL,
            fg=self.CYAN,
            font=("Segoe UI", 16, "bold"),
        )
        self.right_title.pack(side="left", anchor="w")

        self.settings_button = tk.Button(
            self.header_frame,
            text="\u2699",
            command=self._toggle_settings_menu,
            bg=self.PANEL_2,
            fg=self.CYAN,
            activebackground=self.LINE,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.LINE,
            font=("Consolas", 9, "bold"),
            width=4,
            cursor="hand2",
        )
        self.settings_button.pack(side="right")

        self.settings_panel = self._create_settings_panel()

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

    def _create_settings_panel(self) -> tk.Frame:
        panel = tk.Frame(self.right_panel, bg=self.LINE, highlightthickness=0, bd=0)

        frame = tk.Frame(
            panel,
            bg=self.PANEL,
            highlightbackground=self.CYAN_SOFT,
            highlightthickness=1,
            padx=14,
            pady=14,
        )
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="SETTINGS",
            bg=self.PANEL,
            fg=self.CYAN,
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Jarvis voice volume",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(12, 4))

        self.volume_scale = tk.Scale(
            frame,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.voice_volume_var,
            command=self._on_volume_slider_change,
            bg=self.PANEL,
            fg=self.TEXT,
            troughcolor=self.LINE,
            highlightthickness=0,
            activebackground=self.CYAN,
            bd=0,
            length=220,
            showvalue=False,
        )
        self.volume_scale.pack(anchor="w")

        tk.Label(
            frame,
            textvariable=self.voice_volume_text_var,
            bg=self.PANEL,
            fg=self.CYAN_SOFT,
            font=("Consolas", 10, "bold"),
        ).pack(anchor="w", pady=(6, 0))

        tk.Label(
            frame,
            text="System startup",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(14, 4))

        self.autostart_check = tk.Checkbutton(
            frame,
            text="Launch Jarvis when Windows starts",
            variable=self.autostart_var,
            command=self._on_autostart_toggle,
            bg=self.PANEL,
            fg=self.TEXT,
            selectcolor=self.PANEL_2,
            activebackground=self.PANEL,
            activeforeground=self.TEXT,
            highlightthickness=0,
            bd=0,
            anchor="w",
            font=("Segoe UI", 10),
        )
        self.autostart_check.pack(fill="x", anchor="w")

        return panel

    def _toggle_settings_menu(self) -> None:
        if self._settings_menu_visible:
            self._hide_settings_menu()
            return
        self._show_settings_menu()

    def _show_settings_menu(self) -> None:
        self._settings_menu_visible = True
        self.settings_panel.place(
            relx=1.0,
            x=-16,
            y=58,
            anchor="ne",
            width=260,
        )
        self.settings_panel.lift()

    def _hide_settings_menu(self) -> None:
        self._settings_menu_visible = False
        self.settings_panel.place_forget()

    def _handle_global_click(self, event: tk.Event) -> None:
        if not self._settings_menu_visible:
            return

        widget = event.widget
        while widget is not None:
            if widget == self.settings_panel or widget == self.settings_button:
                return
            widget = getattr(widget, "master", None)

        self._hide_settings_menu()

    def _on_resize(self, _event=None) -> None:
        self.canvas.coords("top_bar", 24, 18)
        canvas_width = max(self.canvas.winfo_width(), 200)
        self.canvas.coords("window_controls", canvas_width - 24, 18)

        if self._settings_menu_visible:
            self._show_settings_menu()

    def _set_fullscreen_overlay(self) -> None:
        try:
            self.root.attributes("-fullscreen", False)
        except Exception:
            pass

        try:
            self.root.attributes("-topmost", False)
        except Exception:
            pass

        try:
            self.root.state("normal")
        except Exception:
            pass

        try:
            self.root.overrideredirect(True)
        except Exception:
            pass

        left, top, width, height = self._get_work_area_geometry()
        self.root.geometry(f"{width}x{height}+{left}+{top}")

    def _set_windowed_mode(self) -> None:
        try:
            self.root.attributes("-fullscreen", False)
        except Exception:
            pass

        try:
            self.root.attributes("-topmost", False)
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
        if self._on_overlay_mode_change is not None:
            self._on_overlay_mode_change(self.overlay_mode)

    def _toggle_window_mode(self, _event=None) -> None:
        self._toggle_overlay_mode()

    def _exit_app(self, _event=None) -> None:
        self.root.destroy()

    def _minimize_window(self) -> None:
        self._restoring_from_minimize = True
        try:
            self.root.overrideredirect(False)
        except Exception:
            pass
        self.root.iconify()

    def _handle_window_restore(self, _event=None) -> None:
        if self.root.state() == "iconic":
            return
        if self._restoring_from_minimize:
            self._restoring_from_minimize = False
            self.root.after(30, self._restore_focus)
        if self.overlay_mode:
            self.root.after(10, self._set_fullscreen_overlay)

    def _restore_focus(self) -> None:
        try:
            self.root.deiconify()
        except Exception:
            pass
        try:
            self.root.lift()
        except Exception:
            pass
        try:
            self.root.focus_force()
        except Exception:
            pass

    @staticmethod
    def _get_work_area_geometry() -> tuple[int, int, int, int]:
        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        rect = RECT()
        spi_getworkarea = 0x0030
        success = ctypes.windll.user32.SystemParametersInfoW(
            spi_getworkarea,
            0,
            ctypes.byref(rect),
            0,
        )
        if success:
            return (
                int(rect.left),
                int(rect.top),
                max(200, int(rect.right - rect.left)),
                max(200, int(rect.bottom - rect.top)),
            )

        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return (0, 0, max(200, int(width)), max(200, int(height)))

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
        self.command_history.appendleft(f"[{stamp}] {text}")
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

        self.root.after(80, self._animate)

    def _draw_grid(self, width: int, height: int) -> None:
        step = 37
        for x in range(0, width, step):
            self.canvas.create_line(x, 0, x, height, fill=self.GRID, width=1, tags="hud")
        for y in range(0, height, step):
            self.canvas.create_line(0, y, width, y, fill=self.GRID, width=1, tags="hud")
        for y in range(0, height, 148):
            self.canvas.create_line(0, y, width, y, fill="#10344D", width=1, tags="hud")

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

        x1 = left + chart_w + col_gap
        y1 = top + (chart_h + row_gap) * 2
        x2 = x1 + chart_w
        y2 = y1 + chart_h

        self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.LINE, width=1, tags="hud")
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
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.LINE, width=1, tags="hud")
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
            self.canvas.create_line(plot_left, yy, plot_right, yy, fill="#10344D", width=1, tags="hud")

        if len(values) < 2:
            return

        points = []
        fill_points = [plot_left, plot_bottom]
        count = len(values)
        plot_width = plot_right - plot_left
        plot_height = plot_bottom - plot_top

        for idx, value in enumerate(values):
            x = plot_left + (plot_width * idx / max(count - 1, 1))
            y = plot_bottom - (max(0.0, min(value, 100.0)) / 100.0) * plot_height
            points.extend([x, y])
            fill_points.extend([x, y])

        fill_points.extend([plot_right, plot_bottom])
        self.canvas.create_polygon(*fill_points, fill="#0A3852", outline="", stipple="gray25", tags="hud")
        self.canvas.create_line(*points, fill=self.CYAN, width=2, smooth=True, tags="hud")

    def _draw_command_history(self, width: int, height: int) -> None:
        x1 = 28
        x2 = width - 28
        y2 = height - 24
        y1 = y2 - 112

        self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.LINE, width=1, tags="hud")
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
                text="waiting for voice commands...",
                fill=self.TEXT_DIM,
                font=("Consolas", 10),
                tags="hud",
            )
            return

        for idx, line in enumerate(self.command_history):
            self.canvas.create_text(
                x1 + 14,
                y1 + 42 + idx * 14,
                anchor="nw",
                text=line[:120],
                fill=self.TEXT if idx == 0 else self.TEXT_DIM,
                font=("Consolas", 9),
                tags="hud",
            )

    def _draw_mic_icon(self) -> None:
        width = max(self.mic_canvas.winfo_width(), 260)
        height = max(self.mic_canvas.winfo_height(), 110)
        center_x = width / 2
        center_y = height / 2 - 13
        accent = "#241CFF"
        accent_soft = "#4D46FF"
        phase = time.monotonic() * 3.2

        self.mic_canvas.create_rectangle(0, 0, width, height, outline="", fill=self.PANEL)

        capsule_w = 26
        capsule_h = 41
        stem_h = 24
        base_w = 26
        outline_w = 3

        capsule_left = center_x - capsule_w / 2
        capsule_top = center_y - capsule_h / 2
        capsule_right = center_x + capsule_w / 2
        capsule_bottom = center_y + capsule_h / 2

        self.mic_canvas.create_oval(
            capsule_left,
            capsule_top,
            capsule_right,
            capsule_bottom,
            outline="",
            fill=accent,
        )
        self.mic_canvas.create_rectangle(
            capsule_left,
            center_y,
            capsule_right,
            capsule_bottom,
            outline="",
            fill=accent,
        )

        self.mic_canvas.create_arc(
            center_x - 22,
            center_y + 1,
            center_x + 22,
            center_y + 35,
            start=180,
            extent=180,
            style="arc",
            outline=accent,
            width=outline_w,
        )
        self.mic_canvas.create_line(
            center_x,
            capsule_bottom + 2,
            center_x,
            capsule_bottom + stem_h,
            fill=accent,
            width=outline_w,
        )
        self.mic_canvas.create_rectangle(
            center_x - 2,
            capsule_bottom + 2,
            center_x + 2,
            capsule_bottom + stem_h,
            outline="",
            fill=accent,
        )
        self.mic_canvas.create_line(
            center_x - base_w / 2,
            capsule_bottom + stem_h,
            center_x + base_w / 2,
            capsule_bottom + stem_h,
            fill=accent,
            width=outline_w,
        )
        self.mic_canvas.create_rectangle(
            center_x - base_w / 2,
            capsule_bottom + stem_h - 1,
            center_x + base_w / 2,
            capsule_bottom + stem_h + 2,
            outline="",
            fill=accent,
        )

        def draw_wave_cluster(x_center: float, mirrored: bool, phase_shift: float) -> None:
            bars = 11
            bar_spacing = 4.8
            max_bar_h = 39
            min_bar_h = 10
            base_y = center_y

            for idx in range(bars):
                dist = abs(idx - (bars - 1) / 2)
                envelope = max(0.0, 1.0 - dist / 5.5)
                anim = 0.55 + 0.45 * math.sin(phase + phase_shift + idx * 0.55)
                bar_h = min_bar_h + (max_bar_h - min_bar_h) * envelope * anim
                x = x_center + (idx - (bars - 1) / 2) * bar_spacing
                y1 = base_y - bar_h / 2
                y2 = base_y + bar_h / 2
                color = accent if envelope > 0.5 else accent_soft
                self.mic_canvas.create_line(x, y1, x, y2, fill=color, width=2)

            points = []
            lobe_w = 32
            steps = 18
            for step in range(steps + 1):
                t = step / steps
                local_x = t * lobe_w
                wave = math.sin(t * math.pi) * (12 + 6 * math.sin(phase + phase_shift + t * math.pi * 2))
                draw_x = x_center + local_x if mirrored else x_center - local_x
                points.extend([draw_x, base_y - wave / 2])
            for step in range(steps, -1, -1):
                t = step / steps
                local_x = t * lobe_w
                wave = math.sin(t * math.pi) * (12 + 6 * math.sin(phase + phase_shift + t * math.pi * 2))
                draw_x = x_center + local_x if mirrored else x_center - local_x
                points.extend([draw_x, base_y + wave / 2])
            self.mic_canvas.create_polygon(points, outline=accent, fill="", width=2, smooth=True)

        draw_wave_cluster(center_x - 68, mirrored=False, phase_shift=0.0)
        draw_wave_cluster(center_x + 68, mirrored=True, phase_shift=1.2)

    def _on_volume_slider_change(self, value: str) -> None:
        volume = max(0, min(int(float(value)), 100))
        self.voice_volume_var.set(volume)
        self._update_volume_label(volume)
        if self._on_voice_volume_change is not None:
            self._on_voice_volume_change(volume)

    def _update_volume_label(self, volume: int) -> None:
        self.voice_volume_text_var.set(f"OUTPUT LEVEL: {volume}%")

    def _on_autostart_toggle(self) -> None:
        if self._on_autostart_change is not None:
            self._on_autostart_change(self.autostart_var.get())

    def set_autostart_value(self, enabled: bool) -> None:
        self.autostart_var.set(bool(enabled))

    def _cpu_label(self) -> str:
        value = self.stats_history["cpu"][-1] if self.stats_history["cpu"] else 0.0
        return f"{value:5.1f}%"

    def _ram_label(self) -> str:
        value = self.stats_history["ram"][-1] if self.stats_history["ram"] else 0.0
        return f"{value:5.1f}%"

    def _disk_label(self) -> str:
        value = self.stats_history["disk"][-1] if self.stats_history["disk"] else 0.0
        return f"{value:5.1f}%"

    def _net_rx_label(self) -> str:
        value = self.stats_history["net_rx"][-1] if self.stats_history["net_rx"] else 0.0
        return f"{value:5.1f}%"

    def _net_tx_label(self) -> str:
        value = self.stats_history["net_tx"][-1] if self.stats_history["net_tx"] else 0.0
        return f"{value:5.1f}%"

    def run(self) -> None:
        self.root.mainloop()
