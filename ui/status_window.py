from __future__ import annotations

import tkinter as tk

from core.config import UI_WINDOW_TITLE


class StatusWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(UI_WINDOW_TITLE)
        self.root.geometry("260x120")
        self.root.resizable(False, False)

        self.status_var = tk.StringVar(value="Готов")
        self.detail_var = tk.StringVar(value="Ожидание команды")

        tk.Label(
            self.root,
            text="Jarvis",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(12, 4))

        tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Segoe UI", 14),
        ).pack()

        tk.Label(
            self.root,
            textvariable=self.detail_var,
            font=("Segoe UI", 10),
            wraplength=220,
        ).pack(pady=(6, 0))

    def set_status(self, status: str, detail: str = "") -> None:
        def apply_update() -> None:
            self.status_var.set(status)
            self.detail_var.set(detail)

        if self.root.winfo_exists():
            self.root.after(0, apply_update)

    def run(self) -> None:
        self.root.mainloop()
