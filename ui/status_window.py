from __future__ import annotations

import math
import random
import threading
import time
import tkinter as tk

from core.config import UI_WINDOW_TITLE


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

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(UI_WINDOW_TITLE)
        self.root.geometry("980x620")
        self.root.minsize(860, 540)
        self.root.configure(bg=self.BG)
        self.root.resizable(True, True)

        try:
            self.root.attributes("-alpha", 0.98)
        except Exception:
            pass

        self.status_var = tk.StringVar(value="ГОТОВ")
        self.detail_var = tk.StringVar(value="Система в режиме ожидания")
        self.clock_var = tk.StringVar(value="00:00:00")

        self._status_level = 0.35
        self._angle = 0.0
        self._particles: list[dict] = []
        self._data_streams: list[dict] = []
        self._busy = False

        self._build_layout()
        self._create_background_elements()

        self.root.bind("<Configure>", self._on_resize)

        self._animate()
        self._update_clock()

    def _build_layout(self) -> None:
        self.main = tk.Frame(self.root, bg=self.BG)
        self.main.pack(fill="both", expand=True, padx=18, pady=18)

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
            width=290,
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
            text="TACTICAL VOICE ASSISTANT / NEURAL CONTROL SYSTEM",
            bg=self.BG,
            fg=self.TEXT_DIM,
            font=("Consolas", 10),
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        self.center_status = tk.Frame(self.canvas, bg=self.BG)
        self.canvas.create_window(
            0,
            0,
            anchor="center",
            window=self.center_status,
            tags="center_status",
        )

        self.status_label = tk.Label(
            self.center_status,
            textvariable=self.status_var,
            bg=self.BG,
            fg=self.ALERT,
            font=("Segoe UI", 26, "bold"),
        )
        self.status_label.pack()

        self.detail_label = tk.Label(
            self.center_status,
            textvariable=self.detail_var,
            bg=self.BG,
            fg=self.TEXT,
            font=("Segoe UI", 11),
            wraplength=320,
            justify="center",
        )
        self.detail_label.pack(pady=(6, 0))

        self.right_title = tk.Label(
            self.right_panel,
            text="SYSTEM DATA",
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
        self.clock_label.pack(anchor="w", padx=16, pady=(0, 18))

        self.block_status = self._make_info_block("STATUS", "READY")
        self.block_mode = self._make_info_block("VOICE MODE", "WAKE WORD")
        self.block_core = self._make_info_block("CORE", "ONLINE")
        self.block_audio = self._make_info_block("AUDIO LINK", "STANDBY")

        self.log_title = tk.Label(
            self.right_panel,
            text="LIVE TELEMETRY",
            bg=self.PANEL,
            fg=self.CYAN_SOFT,
            font=("Segoe UI", 12, "bold"),
        )
        self.log_title.pack(anchor="w", padx=16, pady=(18, 8))

        self.log_box = tk.Text(
            self.right_panel,
            height=16,
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

        self._push_log("BOOT SEQUENCE STARTED")
        self._push_log("VISUAL CORE ONLINE")
        self._push_log("VOICE CHANNEL READY")
        self._push_log("AWAITING ACTIVATION")

    def _make_info_block(self, title: str, value: str) -> tk.Label:
        outer = tk.Frame(
            self.right_panel,
            bg=self.PANEL_2,
            highlightbackground=self.LINE,
            highlightthickness=1,
        )
        outer.pack(fill="x", padx=16, pady=6)

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
        )
        value_label.pack(anchor="w", padx=10, pady=(2, 8))
        return value_label

    def _create_background_elements(self) -> None:
        for _ in range(40):
            self._particles.append(
                {
                    "x": random.uniform(40, 700),
                    "y": random.uniform(40, 500),
                    "r": random.uniform(1.0, 2.5),
                    "speed": random.uniform(0.2, 1.1),
                    "alpha": random.uniform(0.2, 1.0),
                }
            )

        for idx in range(14):
            self._data_streams.append(
                {
                    "x": 40 + idx * 48,
                    "offset": random.randint(0, 200),
                    "speed": random.uniform(1.4, 3.2),
                }
            )

    def _on_resize(self, _event=None) -> None:
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        self.canvas.coords("top_bar", 24, 18)
        self.canvas.coords("center_status", width / 2, height / 2 + 110)

    def set_status(self, status: str, detail: str = "") -> None:
        self.root.after(0, self._apply_status, status, detail)

    def _apply_status(self, status: str, detail: str) -> None:
        status_upper = status.upper()
        detail = detail or "..."

        self.status_var.set(status_upper)
        self.detail_var.set(detail)
        self.block_status.configure(text=status_upper)

        normalized = status.strip().lower()

        if "слуш" in normalized:
            self._status_level = 0.70
            self.block_audio.configure(text="INPUT CAPTURE")
            self.block_core.configure(text="ANALYZING")
            self._push_log("VOICE INPUT DETECTED")
        elif "дум" in normalized:
            self._status_level = 0.92
            self.block_audio.configure(text="SIGNAL LOCK")
            self.block_core.configure(text="PROCESSING")
            self._push_log("INTENT ANALYSIS RUNNING")
        elif "выполня" in normalized:
            self._status_level = 1.00
            self.block_audio.configure(text="COMMAND RELAY")
            self.block_core.configure(text="EXECUTING")
            self._push_log(f"EXECUTION: {detail}")
        elif "говор" in normalized:
            self._status_level = 0.82
            self.block_audio.configure(text="VOICE OUTPUT")
            self.block_core.configure(text="RESPONDING")
            self._push_log("SPEECH SYNTHESIS ACTIVE")
        elif "актив" in normalized:
            self._status_level = 0.86
            self.block_audio.configure(text="WAKE CONFIRMED")
            self.block_core.configure(text="ONLINE")
            self._push_log("WAKE WORD ACCEPTED")
        else:
            self._status_level = 0.35
            self.block_audio.configure(text="STANDBY")
            self.block_core.configure(text="ONLINE")
            self._push_log("SYSTEM IDLE")

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

    def _animate(self) -> None:
        self.canvas.delete("hud")

        width = max(self.canvas.winfo_width(), 600)
        height = max(self.canvas.winfo_height(), 400)
        cx = width * 0.50
        cy = height * 0.46

        self._draw_grid(width, height)
        self._draw_data_streams(width, height)
        self._draw_particles()
        self._draw_center_hud(cx, cy)
        self._draw_side_readouts(width, height)

        self._angle += 1.8
        self.root.after(33, self._animate)

    def _draw_grid(self, width: int, height: int) -> None:
        step = 34

        for x in range(0, width, step):
            self.canvas.create_line(
                x, 0, x, height,
                fill="#0b2537",
                width=1,
                tags="hud",
            )

        for y in range(0, height, step):
            self.canvas.create_line(
                0, y, width, y,
                fill="#0b2537",
                width=1,
                tags="hud",
            )

        for y in range(0, height, 120):
            self.canvas.create_line(
                0, y, width, y,
                fill="#10344d",
                width=1,
                tags="hud",
            )

    def _draw_particles(self) -> None:
        width = max(self.canvas.winfo_width(), 600)
        height = max(self.canvas.winfo_height(), 400)

        for p in self._particles:
            p["y"] += p["speed"]
            if p["y"] > height + 10:
                p["y"] = -10
                p["x"] = random.uniform(20, width - 20)

            r = p["r"]
            self.canvas.create_oval(
                p["x"] - r,
                p["y"] - r,
                p["x"] + r,
                p["y"] + r,
                fill=self.CYAN_SOFT,
                outline="",
                tags="hud",
            )

    def _draw_data_streams(self, width: int, height: int) -> None:
        glyphs = "01AF9C7E4D2B8"

        for stream in self._data_streams:
            x = stream["x"]
            stream["offset"] += stream["speed"]
            if stream["offset"] > 36:
                stream["offset"] = 0

            for i in range(-2, int(height / 18) + 3):
                y = i * 18 + stream["offset"]
                text = "".join(random.choice(glyphs) for _ in range(6))
                alpha_color = self.TEXT_DIM if i % 4 else self.CYAN_SOFT
                self.canvas.create_text(
                    x,
                    y,
                    text=text,
                    fill=alpha_color,
                    font=("Consolas", 8),
                    tags="hud",
                )

    def _draw_center_hud(self, cx: float, cy: float) -> None:
        pulse = 8 * math.sin(math.radians(self._angle * 2.4))
        main_r = 92 + pulse
        outer_r = 135 + pulse * 0.6
        ring_r = 176 + pulse * 0.4

        self.canvas.create_oval(
            cx - ring_r,
            cy - ring_r,
            cx + ring_r,
            cy + ring_r,
            outline="#0e4c74",
            width=2,
            tags="hud",
        )

        self.canvas.create_oval(
            cx - outer_r,
            cy - outer_r,
            cx + outer_r,
            cy + outer_r,
            outline=self.CYAN_SOFT,
            width=2,
            tags="hud",
        )

        self.canvas.create_oval(
            cx - main_r,
            cy - main_r,
            cx + main_r,
            cy + main_r,
            outline=self.CYAN,
            width=3,
            tags="hud",
        )

        inner_r = 42 + pulse * 0.25
        self.canvas.create_oval(
            cx - inner_r,
            cy - inner_r,
            cx + inner_r,
            cy + inner_r,
            fill="#06263b",
            outline=self.CYAN,
            width=2,
            tags="hud",
        )

        for i in range(0, 360, 30):
            angle = math.radians(i + self._angle)
            x1 = cx + math.cos(angle) * (outer_r + 6)
            y1 = cy + math.sin(angle) * (outer_r + 6)
            x2 = cx + math.cos(angle) * (outer_r + 22)
            y2 = cy + math.sin(angle) * (outer_r + 22)
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=self.CYAN_SOFT,
                width=2,
                tags="hud",
            )

        for i in range(0, 360, 45):
            angle = math.radians(-i + self._angle * 1.5)
            x1 = cx + math.cos(angle) * (main_r - 18)
            y1 = cy + math.sin(angle) * (main_r - 18)
            x2 = cx + math.cos(angle) * (main_r + 14)
            y2 = cy + math.sin(angle) * (main_r + 14)
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=self.ALERT,
                width=2,
                tags="hud",
            )

        sweep_extent = 32 + self._status_level * 90
        self.canvas.create_arc(
            cx - outer_r - 10,
            cy - outer_r - 10,
            cx + outer_r + 10,
            cy + outer_r + 10,
            start=self._angle * 2,
            extent=sweep_extent,
            style="arc",
            outline=self.ALERT,
            width=4,
            tags="hud",
        )

        self.canvas.create_line(cx - 210, cy, cx - 118, cy, fill=self.CYAN_SOFT, width=2, tags="hud")
        self.canvas.create_line(cx + 118, cy, cx + 210, cy, fill=self.CYAN_SOFT, width=2, tags="hud")
        self.canvas.create_line(cx, cy - 210, cx, cy - 118, fill=self.CYAN_SOFT, width=2, tags="hud")
        self.canvas.create_line(cx, cy + 118, cx, cy + 210, fill=self.CYAN_SOFT, width=2, tags="hud")

        self.canvas.create_text(
            cx,
            cy,
            text="AI",
            fill=self.TEXT,
            font=("Segoe UI", 24, "bold"),
            tags="hud",
        )

        percent = int(self._status_level * 100)
        self.canvas.create_text(
            cx,
            cy + 56,
            text=f"CORE LOAD {percent}%",
            fill=self.TEXT_DIM,
            font=("Consolas", 10, "bold"),
            tags="hud",
        )

    def _draw_side_readouts(self, width: int, height: int) -> None:
        left_x = 100
        right_x = width - 180

        readings_left = [
            f"FFT {random.randint(12, 99)}.{random.randint(0,9)}",
            f"MIC {random.randint(40, 87)}%",
            f"LANG RU",
            f"LAT {random.randint(100, 999)}ms",
        ]

        readings_right = [
            f"MEM {random.randint(18, 66)}%",
            f"CPU {random.randint(9, 52)}%",
            f"NODES {random.randint(3, 12)}",
            f"LINK OK",
        ]

        top_y = 120
        for idx, item in enumerate(readings_left):
            y = top_y + idx * 26
            self.canvas.create_text(
                left_x,
                y,
                text=item,
                fill=self.TEXT_DIM if idx % 2 else self.CYAN,
                font=("Consolas", 10),
                anchor="w",
                tags="hud",
            )

        for idx, item in enumerate(readings_right):
            y = top_y + idx * 26
            self.canvas.create_text(
                right_x,
                y,
                text=item,
                fill=self.TEXT_DIM if idx % 2 else self.CYAN,
                font=("Consolas", 10),
                anchor="w",
                tags="hud",
            )

        wave_y = height - 90
        points = []
        for x in range(40, width - 40, 12):
            value = math.sin((x / 22) + math.radians(self._angle * 3)) * 12
            value += math.sin((x / 57) + math.radians(self._angle * 2)) * 7
            points.extend([x, wave_y + value])

        self.canvas.create_line(
            *points,
            fill=self.CYAN,
            width=2,
            smooth=True,
            tags="hud",
        )

        self.canvas.create_text(
            44,
            wave_y - 22,
            text="SIGNAL TRACE",
            fill=self.TEXT_DIM,
            font=("Consolas", 9),
            anchor="w",
            tags="hud",
        )

    def start_in_thread(self) -> None:
        thread = threading.Thread(target=self.root.mainloop, daemon=True)
        thread.start()

    def run(self) -> None:
        self.root.mainloop()
