import tkinter as tk
from tkinter import ttk
from database import db
from shared import (BG, CARD, ACCENT, GREEN, TEXT, SUBTEXT, MUTED, DANGER,
                    FONT_H1, FONT_H2, FONT_BODY, FONT_SM, lbl, btn,
                    card_frame, separator)

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# ── matplotlib dark style ──────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor":  "#1A2636",
    "axes.facecolor":    "#0F1923",
    "axes.edgecolor":    "#2D3E50",
    "axes.labelcolor":   "#94A3B8",
    "xtick.color":       "#94A3B8",
    "ytick.color":       "#94A3B8",
    "text.color":        "#F1F5F9",
    "grid.color":        "#2D3E50",
    "grid.linestyle":    "--",
    "grid.alpha":        0.4,
})
PALETTE = [ACCENT, GREEN, "#60A5FA", "#A78BFA", "#F472B6", DANGER]


class AnalyticsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("FoodShare — Analytics Dashboard")
        self.configure(bg=BG)
        self.geometry("980x680")
        self._build()

    def _build(self):
        lbl(self, "📊  Analytics Dashboard", font=FONT_H1, bg=BG
            ).pack(pady=(18, 4), padx=20, anchor="w")
        lbl(self, "Data-driven insights on food redistribution",
            font=FONT_BODY, fg=SUBTEXT, bg=BG).pack(padx=20, anchor="w")
        separator(self)

        # tab bar
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=8)

        style = ttk.Style()
        style.configure("TNotebook",            background=BG,   borderwidth=0)
        style.configure("TNotebook.Tab",        background=CARD, foreground=TEXT,
                        padding=[14, 6],         font=FONT_BODY)
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])

        tabs = [
            ("Donation Status",    self._tab_status),
            ("Food Categories",    self._tab_categories),
            ("Beneficiary Split",  self._tab_beneficiary),
            ("Daily Trend",        self._tab_trend),
            ("Stats Summary",      self._tab_summary),
        ]
        for name, builder in tabs:
            frame = tk.Frame(nb, bg=BG)
            nb.add(frame, text=f"  {name}  ")
            builder(frame)

    # ── helpers ────────────────────────────────────────────────────────────

    def _donations_df(self):
        rows = db.find("donations")
        if not rows:
            return pd.DataFrame(columns=["status","food_item","beneficiary",
                                          "urgent","posted_at","quantity"])
        df = pd.DataFrame(rows)
        return df

    def _embed(self, fig, parent):
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        return canvas

    def _no_data(self, parent):
        lbl(parent, "No donation data yet. Post some food to see charts!",
            fg=SUBTEXT, bg=BG).pack(pady=40)

    # ── Tab 1 : donation status bar chart ──────────────────────────────────

    def _tab_status(self, parent):
        df = self._donations_df()
        if df.empty:
            return self._no_data(parent)

        counts = df["status"].value_counts()
        labels = counts.index.tolist()
        values = counts.values

        fig = Figure(figsize=(8, 4.2))
        ax  = fig.add_subplot(111)
        bars = ax.bar(labels, values,
                      color=[ACCENT, GREEN, "#60A5FA", DANGER][:len(labels)],
                      width=0.45, edgecolor="none")
        ax.bar_label(bars, padding=4, color=TEXT, fontsize=10, fontweight="bold")
        ax.set_title("Donations by Status", color=TEXT, fontsize=14, pad=14)
        ax.set_ylabel("Count", labelpad=8)
        ax.set_xlabel("Status", labelpad=8)
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        self._embed(fig, parent)

    # ── Tab 2 : food category horizontal bar ───────────────────────────────

    def _tab_categories(self, parent):
        df = self._donations_df()
        if df.empty or "food_item" not in df.columns:
            return self._no_data(parent)

        counts = df["food_item"].value_counts().head(10)
        y_pos  = np.arange(len(counts))

        fig = Figure(figsize=(8, 4.2))
        ax  = fig.add_subplot(111)
        bars = ax.barh(y_pos, counts.values,
                       color=ACCENT, edgecolor="none", height=0.5)
        ax.bar_label(bars, padding=4, color=TEXT, fontsize=10)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(counts.index, color=TEXT)
        ax.set_title("Top Food Items Donated", color=TEXT, fontsize=14, pad=14)
        ax.set_xlabel("Frequency", labelpad=8)
        ax.grid(axis="x")
        ax.set_axisbelow(True)
        self._embed(fig, parent)

    # ── Tab 3 : beneficiary pie chart ──────────────────────────────────────

    def _tab_beneficiary(self, parent):
        df = self._donations_df()
        if df.empty or "beneficiary" not in df.columns:
            return self._no_data(parent)

        counts = df["beneficiary"].value_counts()
        labels = counts.index.tolist()

        fig = Figure(figsize=(6, 4.2))
        ax  = fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(
            counts.values,
            labels     = labels,
            colors     = PALETTE[:len(labels)],
            autopct    = "%1.0f%%",
            startangle = 140,
            pctdistance= 0.82,
            wedgeprops = {"linewidth": 2, "edgecolor": BG},
        )
        for t in texts + autotexts:
            t.set_color(TEXT)
        ax.set_title("Beneficiary Split", color=TEXT, fontsize=14, pad=14)
        self._embed(fig, parent)

    # ── Tab 4 : daily posting trend line chart ─────────────────────────────

    def _tab_trend(self, parent):
        df = self._donations_df()
        if df.empty or "posted_at" not in df.columns:
            return self._no_data(parent)

        df["date"] = pd.to_datetime(df["posted_at"]).dt.date
        trend = df.groupby("date").size().reset_index(name="count")

        if len(trend) < 2:
            lbl(parent, "Need more data points for a trend. Post more donations!",
                fg=SUBTEXT, bg=BG).pack(pady=40)
            return

        dates  = pd.to_datetime(trend["date"])
        counts = trend["count"].values

        fig = Figure(figsize=(8, 4.2))
        ax  = fig.add_subplot(111)
        ax.plot(dates, counts, color=ACCENT, linewidth=2.5, marker="o",
                markersize=6, markerfacecolor=GREEN)
        ax.fill_between(dates, counts, alpha=0.15, color=ACCENT)

        # NumPy rolling average
        if len(counts) >= 3:
            window = min(3, len(counts))
            kernel = np.ones(window) / window
            smooth = np.convolve(counts, kernel, mode="valid")
            ax.plot(dates[window-1:], smooth, color=GREEN, linewidth=1.5,
                    linestyle="--", label="3-day avg")
            ax.legend(labelcolor=TEXT, facecolor=CARD)

        ax.set_title("Daily Donation Trend", color=TEXT, fontsize=14, pad=14)
        ax.set_xlabel("Date", labelpad=8)
        ax.set_ylabel("Donations", labelpad=8)
        ax.grid()
        self._embed(fig, parent)

    # ── Tab 5 : stats summary cards ────────────────────────────────────────

    def _tab_summary(self, parent):
        df     = self._donations_df()
        users  = db.find("users")
        ngos   = db.find("ngos")

        donors     = [u for u in users if u.get("role") == "donor"]
        vols       = [u for u in users if u.get("role") == "volunteer"]

        total_d    = len(df)
        available  = len(df[df["status"] == "available"]) if not df.empty else 0
        delivered  = len(df[df["status"] == "delivered"]) if not df.empty else 0
        urgent_cnt = len(df[df["urgent"] == True])        if not df.empty else 0

        pct_done   = (delivered / total_d * 100) if total_d else 0

        stats = [
            ("🍱", "Total Donations",    total_d,           ACCENT),
            ("✅", "Delivered",          delivered,          GREEN),
            ("⏳", "Available",          available,          "#60A5FA"),
            ("🚨", "Urgent",             urgent_cnt,         DANGER),
            ("🧑‍🤝‍🧑", "Donors",           len(donors),        "#A78BFA"),
            ("🚴", "Volunteers",         len(vols),          "#F472B6"),
            ("🏛️", "NGOs",               len(ngos),          ACCENT),
            ("📈", "Completion %",       f"{pct_done:.0f}%", GREEN),
        ]

        grid = tk.Frame(parent, bg=BG)
        grid.pack(padx=20, pady=20, fill="both", expand=True)

        for i, (icon, label, value, color) in enumerate(stats):
            r, c = divmod(i, 4)
            cell = card_frame(grid, bg=CARD)
            cell.grid(row=r, column=c, padx=8, pady=8, sticky="nsew", ipadx=10, ipady=14)
            grid.columnconfigure(c, weight=1)

            tk.Label(cell, text=icon,   font=("Helvetica", 28), bg=CARD, fg=color).pack(pady=(8,2))
            tk.Label(cell, text=str(value), font=("Georgia", 20, "bold"), bg=CARD, fg=TEXT).pack()
            tk.Label(cell, text=label,  font=("Helvetica", 10), bg=CARD, fg=SUBTEXT).pack(pady=(0,6))
