"""
Random Password Generator — Oasis Infobyte Internship (Python Programming, Task 3, Advanced tier)

Author: Faizan Ali

Features
- tkinter GUI: length slider, character-type checkboxes, Generate button
- Secure generation with the `secrets` module
- At least one character from every selected type is guaranteed
- Option to exclude look-alike characters (0 O o 1 l I |)
- Strength indicator (Weak / Medium / Strong) with a colour bar
- Copy to clipboard (tkinter's built-in clipboard, no extra install)
- Last 5 passwords shown for this session only (never saved to disk)
- Input validation with clear messages inside the window
"""

import tkinter as tk
from tkinter import ttk

from generator import (
    CHARACTER_SETS,
    LABELS,
    MAX_LENGTH,
    MIN_LENGTH,
    PasswordError,
    generate_password,
    parse_length,
    password_strength,
)

BG = "#f1f5f9"
CARD = "#ffffff"
HEADER = "#0f172a"
TEXT = "#0f172a"
MUTED = "#64748b"
ACCENT = "#2563eb"
FONT = "Segoe UI"
MONO = "Consolas"
HISTORY_SIZE = 5


class PasswordApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Password Generator — Faizan Ali | OIBSIP")
        self.geometry("980x600")
        self.minsize(900, 580)
        self.configure(bg=BG)

        self.history = []          # in-memory only, cleared when the app closes
        self.current = ""
        self._build_header()
        self._build_body()
        self.bind("<Return>", lambda e: self.on_generate())

    # ================= UI =================
    def _build_header(self):
        header = tk.Frame(self, bg=HEADER)
        header.pack(fill="x")
        tk.Label(header, text="Password Generator", bg=HEADER, fg="white",
                 font=(FONT, 18, "bold")).pack(side="left", padx=24, pady=14)
        tk.Label(header, text="Strong, random passwords in one click", bg=HEADER,
                 fg="#94a3b8", font=(FONT, 10)).pack(side="left", pady=(20, 14))

    def _card(self, parent, **pack):
        frame = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground="#e2e8f0")
        frame.pack(**pack)
        inner = tk.Frame(frame, bg=CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=18)
        return inner

    def _build_body(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=20)

        left = tk.Frame(body, bg=BG, width=360)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(20, 0))

        self._build_settings(left)
        self._build_result(right)
        self._build_history(right)

    def _build_settings(self, parent):
        c = self._card(parent, fill="both", expand=True)
        tk.Label(c, text="Settings", bg=CARD, fg=TEXT,
                 font=(FONT, 13, "bold")).pack(anchor="w", pady=(0, 10))

        # length: slider + entry kept in sync
        row = tk.Frame(c, bg=CARD)
        row.pack(fill="x")
        tk.Label(row, text="Password length", bg=CARD, fg=MUTED, font=(FONT, 9)).pack(side="left")
        self.length_var = tk.StringVar(value="16")
        self.length_entry = tk.Entry(row, textvariable=self.length_var, width=5,
                                     font=(FONT, 11), justify="center", relief="solid", bd=1)
        self.length_entry.pack(side="right", ipady=2)

        self.slider = tk.Scale(c, from_=MIN_LENGTH, to=MAX_LENGTH, orient="horizontal",
                               showvalue=False, bg=CARD, highlightthickness=0,
                               troughcolor="#e2e8f0", activebackground=ACCENT,
                               command=lambda v: self.length_var.set(str(int(float(v)))))
        self.slider.set(16)
        self.slider.pack(fill="x", pady=(6, 14))
        self.length_var.trace_add("write", self._sync_slider)

        tk.Label(c, text="Include", bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w")
        self.type_vars = {}
        for name in CHARACTER_SETS:
            var = tk.BooleanVar(value=True)
            self.type_vars[name] = var
            tk.Checkbutton(c, text=LABELS[name], variable=var, bg=CARD, fg=TEXT,
                           activebackground=CARD, font=(FONT, 10), anchor="w",
                           highlightthickness=0, bd=0
                           ).pack(fill="x")

        self.ambiguous_var = tk.BooleanVar(value=False)
        tk.Checkbutton(c, text="Exclude look-alike characters (0 O o 1 l I)",
                       variable=self.ambiguous_var, bg=CARD, fg=TEXT,
                       activebackground=CARD, font=(FONT, 9), anchor="w",
                       highlightthickness=0, bd=0
                       ).pack(fill="x", pady=(10, 12))

        self.gen_btn = tk.Button(c, text="Generate Password", command=self.on_generate,
                                 bg=ACCENT, fg="white", activebackground="#1d4ed8",
                                 activeforeground="white", font=(FONT, 11, "bold"),
                                 relief="flat", cursor="hand2", pady=8)
        self.gen_btn.pack(fill="x")

        self.error_label = tk.Label(c, text="", bg=CARD, fg="#dc2626", font=(FONT, 9),
                                    wraplength=300, justify="left")
        self.error_label.pack(anchor="w", pady=(8, 0))

    def _build_result(self, parent):
        c = self._card(parent, fill="x")
        tk.Label(c, text="Your password", bg=CARD, fg=TEXT,
                 font=(FONT, 13, "bold")).pack(anchor="w")

        row = tk.Frame(c, bg=CARD)
        row.pack(fill="x", pady=(8, 10))
        self.pwd_var = tk.StringVar(value="")
        self.pwd_entry = tk.Entry(row, textvariable=self.pwd_var, font=(MONO, 15),
                                  state="readonly", relief="solid", bd=1,
                                  readonlybackground="#f8fafc", fg=TEXT)
        self.pwd_entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.copy_btn = tk.Button(row, text="Copy", command=self.on_copy, bg="#e2e8f0",
                                  fg=TEXT, relief="flat", font=(FONT, 10, "bold"),
                                  cursor="hand2", padx=16)
        self.copy_btn.pack(side="left", padx=(8, 0), fill="y")

        srow = tk.Frame(c, bg=CARD)
        srow.pack(fill="x")
        tk.Label(srow, text="Strength:", bg=CARD, fg=MUTED, font=(FONT, 10)).pack(side="left")
        self.strength_label = tk.Label(srow, text="—", bg=CARD, fg=MUTED, font=(FONT, 11, "bold"))
        self.strength_label.pack(side="left", padx=6)
        self.copied_label = tk.Label(srow, text="", bg=CARD, fg="#16a34a", font=(FONT, 9))
        self.copied_label.pack(side="right")

        self.meter = tk.Canvas(c, height=10, bg=CARD, highlightthickness=0)
        self.meter.pack(fill="x", pady=(8, 0))
        self.meter.bind("<Configure>", lambda e: self._draw_meter())
        self.score = 0
        self.score_colour = "#e2e8f0"

    def _build_history(self, parent):
        c = self._card(parent, fill="both", expand=True, pady=(16, 0))
        top = tk.Frame(c, bg=CARD)
        top.pack(fill="x")
        tk.Label(top, text="Recent passwords (this session only)", bg=CARD, fg=TEXT,
                 font=(FONT, 12, "bold")).pack(side="left")
        tk.Button(top, text="Clear", command=self.on_clear_history, bg="#f1f5f9", fg=TEXT,
                  relief="flat", font=(FONT, 9), cursor="hand2", padx=10).pack(side="right")
        self.history_box = tk.Listbox(c, font=(MONO, 12), height=HISTORY_SIZE, relief="flat",
                                      bg="#f8fafc", fg=TEXT, selectbackground="#dbeafe",
                                      selectforeground=TEXT, activestyle="none",
                                      highlightthickness=0)
        self.history_box.pack(fill="both", expand=True, pady=(8, 0))
        self.history_box.bind("<Double-Button-1>", self.on_history_copy)
        tk.Label(c, text="Double-click a password to copy it. Nothing is saved to disk.",
                 bg=CARD, fg=MUTED, font=(FONT, 8)).pack(anchor="w", pady=(6, 0))

    # ================= actions =================
    def _sync_slider(self, *_):
        try:
            value = int(self.length_var.get())
        except ValueError:
            return
        if MIN_LENGTH <= value <= MAX_LENGTH and value != self.slider.get():
            self.slider.set(value)

    def on_generate(self):
        self.error_label.config(text="")
        self.copied_label.config(text="")
        selected = [name for name, var in self.type_vars.items() if var.get()]
        try:
            length = parse_length(self.length_var.get())
            password = generate_password(length, selected, self.ambiguous_var.get())
        except PasswordError as err:
            self.error_label.config(text=str(err))
            return

        self.current = password
        self.pwd_var.set(password)
        label, self.score, self.score_colour = password_strength(password)
        self.strength_label.config(text=label, fg=self.score_colour)
        self._draw_meter()

        self.history.insert(0, password)
        del self.history[HISTORY_SIZE:]
        self.history_box.delete(0, "end")
        for pwd in self.history:
            self.history_box.insert("end", pwd)

    def _copy(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()  # keep clipboard content after the app loses focus
        self.copied_label.config(text="✓ Copied to clipboard")

    def on_copy(self):
        if not self.current:
            self.error_label.config(text="Generate a password first, then copy it.")
            return
        self._copy(self.current)

    def on_history_copy(self, _event=None):
        sel = self.history_box.curselection()
        if sel:
            self._copy(self.history_box.get(sel[0]))

    def on_clear_history(self):
        self.history.clear()
        self.history_box.delete(0, "end")

    def _draw_meter(self):
        m = self.meter
        m.delete("all")
        width = max(m.winfo_width(), 100)
        segments, gap = 6, 4
        seg_w = (width - gap * (segments - 1)) / segments
        for i in range(segments):
            x0 = i * (seg_w + gap)
            colour = self.score_colour if i < self.score else "#e2e8f0"
            m.create_rectangle(x0, 0, x0 + seg_w, 10, fill=colour, outline="")


if __name__ == "__main__":
    PasswordApp().mainloop()
