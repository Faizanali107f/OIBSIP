"""
BMI Calculator — Oasis Infobyte Internship (Python Programming, Task 2, Advanced tier)

Author: Faizan Ali

Features
- tkinter GUI with labelled inputs and a Calculate button
- BMI rounded to 2 decimals with colour-coded category and a visual gauge
- Multi-user support: each record is saved under a user name
- History stored in SQLite (bmi_records.db)
- BMI trend line chart per user (matplotlib, embedded in the window)
- Input validation and database error handling shown inside the GUI
"""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from bmi import (
    CATEGORIES,
    HEIGHT_RANGE,
    WEIGHT_RANGE,
    InputError,
    calculate_bmi,
    classify_bmi,
    parse_positive_number,
)
from database import BMIDatabase, DatabaseError

# ---------- theme ----------
BG = "#f1f5f9"
CARD = "#ffffff"
HEADER = "#0f172a"
TEXT = "#0f172a"
MUTED = "#64748b"
ACCENT = "#2563eb"
FONT = "Segoe UI"

GAUGE_MIN, GAUGE_MAX = 10.0, 40.0


class BMIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BMI Calculator — Faizan Ali | OIBSIP")
        self.geometry("1100x720")
        self.minsize(980, 700)
        self.configure(bg=BG)

        try:
            self.db = BMIDatabase()
        except DatabaseError as err:
            messagebox.showerror("Database error", str(err))
            self.destroy()
            raise SystemExit(1)

        self.last_result = None  # (weight, height, bmi, category)
        self._setup_styles()
        self._build_header()
        self._build_body()
        self._refresh_users()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ================= UI construction =================
    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", font=(FONT, 10, "bold"), padding=(16, 6))
        style.configure("Treeview", font=(FONT, 10), rowheight=26)
        style.configure("Treeview.Heading", font=(FONT, 10, "bold"))
        style.configure("TCombobox", padding=6)

    def _build_header(self):
        header = tk.Frame(self, bg=HEADER, height=64)
        header.pack(fill="x")
        tk.Label(
            header, text="BMI Calculator", bg=HEADER, fg="white",
            font=(FONT, 18, "bold"),
        ).pack(side="left", padx=24, pady=14)
        tk.Label(
            header, text="Track your Body Mass Index over time", bg=HEADER,
            fg="#94a3b8", font=(FONT, 10),
        ).pack(side="left", pady=(20, 14))

    def _card(self, parent, **pack):
        frame = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground="#e2e8f0")
        frame.pack(**pack)
        return frame

    def _build_body(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=20)

        left = tk.Frame(body, bg=BG, width=340)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(20, 0))

        self._build_input_card(left)
        self._build_result_card(left)
        self._build_history_area(right)

    def _build_input_card(self, parent):
        card = self._card(parent, fill="x")
        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=20, pady=18)

        tk.Label(inner, text="Your details", bg=CARD, fg=TEXT,
                 font=(FONT, 13, "bold")).pack(anchor="w", pady=(0, 10))

        tk.Label(inner, text="User name", bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w")
        self.user_var = tk.StringVar()
        self.user_box = ttk.Combobox(inner, textvariable=self.user_var, font=(FONT, 11))
        self.user_box.pack(fill="x", pady=(2, 10))
        self.user_box.bind("<<ComboboxSelected>>", lambda e: self._refresh_history())
        self.user_box.bind("<FocusOut>", lambda e: self._refresh_history())

        self.weight_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self._labelled_entry(inner, "Weight (kg)", self.weight_var)
        self._labelled_entry(inner, "Height (m)  e.g. 1.75", self.height_var)

        self.save_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            inner, text="Save result to history", variable=self.save_var,
            bg=CARD, fg=TEXT, activebackground=CARD, font=(FONT, 9),
        ).pack(anchor="w", pady=(2, 8))

        tk.Button(
            inner, text="Calculate BMI", command=self.on_calculate,
            bg=ACCENT, fg="white", activebackground="#1d4ed8", activeforeground="white",
            font=(FONT, 11, "bold"), relief="flat", cursor="hand2", pady=8,
        ).pack(fill="x")

        self.error_label = tk.Label(inner, text="", bg=CARD, fg="#dc2626",
                                    font=(FONT, 9), wraplength=280, justify="left")
        self.error_label.pack(anchor="w", pady=(8, 0))

        self.bind("<Return>", lambda e: self.on_calculate())

    def _labelled_entry(self, parent, label, var):
        tk.Label(parent, text=label, bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w")
        entry = tk.Entry(parent, textvariable=var, font=(FONT, 11), relief="solid",
                         bd=1, highlightthickness=0)
        entry.pack(fill="x", ipady=5, pady=(2, 10))
        return entry

    def _build_result_card(self, parent):
        card = self._card(parent, fill="x", pady=(16, 0))
        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=20, pady=16)

        tk.Label(inner, text="Result", bg=CARD, fg=TEXT,
                 font=(FONT, 13, "bold")).pack(anchor="w")
        self.bmi_label = tk.Label(inner, text="--", bg=CARD, fg=TEXT, font=(FONT, 34, "bold"))
        self.bmi_label.pack(anchor="w")
        self.category_label = tk.Label(inner, text="Enter your details", bg=CARD,
                                       fg=MUTED, font=(FONT, 12, "bold"))
        self.category_label.pack(anchor="w", pady=(0, 8))

        self.gauge = tk.Canvas(inner, height=56, bg=CARD, highlightthickness=0)
        self.gauge.pack(fill="x")
        self.gauge.bind("<Configure>", lambda e: self._draw_gauge())

    def _build_history_area(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True)

        # --- Trend chart tab ---
        chart_tab = tk.Frame(notebook, bg=CARD)
        notebook.add(chart_tab, text="BMI Trend")
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.chart = FigureCanvasTkAgg(self.figure, master=chart_tab)
        self.chart.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        # --- History table tab ---
        table_tab = tk.Frame(notebook, bg=CARD)
        notebook.add(table_tab, text="History")
        columns = ("date", "weight", "height", "bmi", "category")
        self.tree = ttk.Treeview(table_tab, columns=columns, show="headings")
        headings = {"date": "Date & time", "weight": "Weight (kg)", "height": "Height (m)",
                    "bmi": "BMI", "category": "Category"}
        widths = {"date": 170, "weight": 100, "height": 100, "bmi": 80, "category": 120}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")
        for _, name, colour in CATEGORIES:
            self.tree.tag_configure(name, foreground=colour)

        scroll = ttk.Scrollbar(table_tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        btn_row = tk.Frame(table_tab, bg=CARD)
        btn_row.pack(side="bottom", fill="x", padx=10, pady=10)
        tk.Button(btn_row, text="Delete selected record", command=self.on_delete_record,
                  bg="#fee2e2", fg="#b91c1c", relief="flat", font=(FONT, 9, "bold"),
                  cursor="hand2", padx=10, pady=4).pack(side="left")
        tk.Button(btn_row, text="Delete user", command=self.on_delete_user,
                  bg="#f1f5f9", fg=TEXT, relief="flat", font=(FONT, 9, "bold"),
                  cursor="hand2", padx=10, pady=4).pack(side="left", padx=8)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(10, 0))
        scroll.pack(side="left", fill="y", pady=(10, 0))

        self._draw_chart([])

    # ================= actions =================
    def on_calculate(self):
        self.error_label.config(text="")
        try:
            weight = parse_positive_number(self.weight_var.get(), "weight", WEIGHT_RANGE)
            height = parse_positive_number(self.height_var.get(), "height", HEIGHT_RANGE)
        except InputError as err:
            self.error_label.config(text=str(err))
            return

        bmi = calculate_bmi(weight, height)
        category, colour = classify_bmi(bmi)
        self.last_result = (weight, height, bmi, category)

        self.bmi_label.config(text=f"{bmi:.2f}", fg=colour)
        self.category_label.config(text=category, fg=colour)
        self._draw_gauge()

        if self.save_var.get():
            name = self.user_var.get().strip()
            if not name:
                self.error_label.config(
                    text="BMI calculated. Enter a user name to save it to history.")
                return
            try:
                self.db.add_record(name, weight, height, bmi, category)
            except DatabaseError as err:
                messagebox.showerror("Database error", str(err))
                return
            self._refresh_users()
            self._refresh_history()

    def on_delete_record(self):
        selected = self.tree.selection()
        if not selected:
            self.error_label.config(text="Select a record in the History tab to delete it.")
            return
        if not messagebox.askyesno("Delete record", "Delete the selected record?"):
            return
        try:
            for item in selected:
                self.db.delete_record(int(item))
        except DatabaseError as err:
            messagebox.showerror("Database error", str(err))
        self._refresh_history()

    def on_delete_user(self):
        name = self.user_var.get().strip()
        if not name or name not in self.db.get_users():
            self.error_label.config(text="Choose an existing user to delete.")
            return
        if not messagebox.askyesno("Delete user", f"Delete '{name}' and all their records?"):
            return
        try:
            self.db.delete_user(name)
        except DatabaseError as err:
            messagebox.showerror("Database error", str(err))
            return
        self.user_var.set("")
        self._refresh_users()
        self._refresh_history()

    # ================= refresh / drawing =================
    def _refresh_users(self):
        try:
            self.user_box["values"] = self.db.get_users()
        except DatabaseError as err:
            messagebox.showerror("Database error", str(err))

    def _refresh_history(self):
        name = self.user_var.get().strip()
        self.tree.delete(*self.tree.get_children())
        if not name:
            self._draw_chart([])
            return
        try:
            records = self.db.get_records(name)
        except DatabaseError as err:
            messagebox.showerror("Database error", str(err))
            return
        for r in reversed(records):  # newest first in the table
            self.tree.insert(
                "", "end", iid=str(r["id"]), tags=(r["category"],),
                values=(r["created_at"], f"{r['weight_kg']:.1f}", f"{r['height_m']:.2f}",
                        f"{r['bmi']:.2f}", r["category"]),
            )
        self._draw_chart(records, name)

    def _draw_gauge(self):
        c = self.gauge
        c.delete("all")
        width = max(c.winfo_width(), 200)
        bar_top, bar_bottom = 18, 32
        span = GAUGE_MAX - GAUGE_MIN

        def x_for(value):
            value = min(max(value, GAUGE_MIN), GAUGE_MAX)
            return (value - GAUGE_MIN) / span * width

        start = GAUGE_MIN
        for upper, _, colour in CATEGORIES:
            end = min(upper, GAUGE_MAX)
            c.create_rectangle(x_for(start), bar_top, x_for(end), bar_bottom,
                               fill=colour, outline="")
            start = end
        for mark in (18.5, 25, 30):
            c.create_text(x_for(mark), bar_bottom + 8, text=f"{mark:g}",
                          fill=MUTED, font=(FONT, 8))

        if self.last_result:
            x = x_for(self.last_result[2])
            c.create_polygon(x - 7, 4, x + 7, 4, x, bar_top - 1, fill=TEXT, outline="")

    def _draw_chart(self, records, name=None):
        ax = self.ax
        ax.clear()
        bands = [(GAUGE_MIN, 18.5), (18.5, 25), (25, 30), (30, GAUGE_MAX)]
        for (low, high), (_, label, colour) in zip(bands, CATEGORIES):
            ax.axhspan(low, high, color=colour, alpha=0.08)
            ax.text(1.01, (low + high) / 2, label, transform=ax.get_yaxis_transform(),
                    va="center", fontsize=8, color=colour)

        if records:
            dates = [datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M:%S") for r in records]
            values = [r["bmi"] for r in records]
            ax.plot(dates, values, color=ACCENT, linewidth=2, marker="o", markersize=6)
            for d, v in zip(dates, values):
                ax.annotate(f"{v:.1f}", (d, v), textcoords="offset points",
                            xytext=(0, 8), ha="center", fontsize=8, color=TEXT)
            ax.set_title(f"BMI trend — {name}", fontsize=12, fontweight="bold", loc="left")
            self.figure.autofmt_xdate()
        else:
            ax.set_title("BMI trend", fontsize=12, fontweight="bold", loc="left")
            ax.text(0.5, 0.5, "Select or create a user to see their BMI trend",
                    transform=ax.transAxes, ha="center", va="center", color=MUTED)

        low = min([r["bmi"] for r in records] + [16]) - 2 if records else 14
        high = max([r["bmi"] for r in records] + [32]) + 2 if records else 34
        ax.set_ylim(low, high)
        ax.set_ylabel("BMI")
        ax.grid(alpha=0.25)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        self.figure.subplots_adjust(left=0.09, right=0.86, top=0.9, bottom=0.18)
        self.chart.draw()

    def _on_close(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    BMIApp().mainloop()
