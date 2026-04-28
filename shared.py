import tkinter as tk
from tkinter import ttk
from database import db, _ts, _new_id

# ── palette ────────────────────────────────────────────────────────────────
BG      = "#0F1923"
CARD    = "#1A2636"
CARD2   = "#243447"
ACCENT  = "#F97316"
GREEN   = "#22C55E"
MUTED   = "#64748B"
TEXT    = "#F1F5F9"
SUBTEXT = "#94A3B8"
DANGER  = "#EF4444"
YELLOW  = "#EAB308"
BORDER  = "#2D3E50"

FONT_H1   = ("Georgia",    22, "bold")
FONT_H2   = ("Georgia",    16, "bold")
FONT_H3   = ("Georgia",    13, "bold")
FONT_BODY = ("Helvetica",  11)
FONT_SM   = ("Helvetica",   9)
FONT_BTN  = ("Helvetica",  11, "bold")
FONT_MONO = ("Courier",    10)


# ── styled helpers ─────────────────────────────────────────────────────────

def card_frame(parent, **kw):
    kw.setdefault("bg",     CARD)
    kw.setdefault("relief", "flat")
    kw.setdefault("bd",     0)
    f = tk.Frame(parent, **kw)
    return f

def lbl(parent, text, font=FONT_BODY, fg=TEXT, bg=None, **kw):
    bg = bg or parent.cget("bg")
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)

def btn(parent, text, command, color=ACCENT, fg="white", **kw):
    b = tk.Button(parent, text=text, command=command,
                  bg=color, fg=fg, font=FONT_BTN,
                  relief="flat", cursor="hand2",
                  padx=12, pady=6, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=_darken(color)))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b

def _darken(hex_col):
    r,g,b = int(hex_col[1:3],16), int(hex_col[3:5],16), int(hex_col[5:7],16)
    return f"#{max(r-30,0):02x}{max(g-30,0):02x}{max(b-30,0):02x}"

def scrolled_frame(parent, bg=BG):
    """Returns (outer_frame, inner_frame) — pack/grid the outer, add widgets to inner."""
    outer = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0)
    sb     = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    inner  = tk.Frame(canvas, bg=bg)

    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=sb.set)

    canvas.pack(side="left",  fill="both", expand=True)
    sb.pack(    side="right", fill="y")

    # mouse-wheel
    def _scroll(e):
        canvas.yview_scroll(int(-1*(e.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _scroll)

    return outer, inner

def separator(parent, bg=BORDER):
    tk.Frame(parent, bg=bg, height=1).pack(fill="x", pady=6)


# ── notification helpers ────────────────────────────────────────────────────

def push_notification(user_id, message, notif_type="info"):
    db.insert("notifications", {
        "_id":       _new_id(),
        "user_id":   user_id,
        "message":   message,
        "type":      notif_type,    # info / urgent / success
        "read":      False,
        "created_at": _ts(),
    })

def get_unread(user_id):
    all_n = db.find("notifications", {"user_id": user_id})
    return [n for n in all_n if not n.get("read")]

def mark_read(user_id):
    db.update("notifications", {"user_id": user_id, "read": False}, {"read": True})


# ── notification bell widget ───────────────────────────────────────────────

class NotifBell(tk.Frame):
    def __init__(self, parent, user, **kw):
        kw.setdefault("bg", BG)
        super().__init__(parent, **kw)
        self.user  = user
        self._bell = tk.Label(self, text="🔔", font=("Helvetica", 16),
                              bg=BG, fg=TEXT, cursor="hand2")
        self._bell.pack(side="left")
        self._badge = tk.Label(self, text="", font=FONT_SM,
                               bg=DANGER, fg="white", width=2)
        self._cnt = 0
        self._bell.bind("<Button-1>", self._open)
        self.refresh()

    def refresh(self):
        unread = get_unread(self.user["_id"])
        self._cnt = len(unread)
        if self._cnt:
            self._badge.config(text=str(self._cnt))
            self._badge.pack(side="left")
        else:
            self._badge.pack_forget()
        self.after(8000, self.refresh)   # poll every 8 s

    def _open(self, _=None):
        win = tk.Toplevel(self)
        win.title("Notifications")
        win.configure(bg=BG)
        win.geometry("420x380")

        lbl(win, "🔔  Notifications", font=FONT_H2, bg=BG).pack(pady=12, padx=16, anchor="w")
        separator(win)

        outer, inner = scrolled_frame(win)
        outer.pack(fill="both", expand=True, padx=12, pady=4)

        notifs = db.find("notifications", {"user_id": self.user["_id"]})
        notifs.sort(key=lambda n: n.get("created_at", ""), reverse=True)

        if not notifs:
            lbl(inner, "No notifications yet.", fg=SUBTEXT, bg=BG).pack(pady=20)
        else:
            for n in notifs:
                color = {"urgent": DANGER, "success": GREEN}.get(n.get("type"), ACCENT)
                row = card_frame(inner, bg=CARD)
                row.pack(fill="x", padx=4, pady=3, ipady=6)
                dot = "●" if not n.get("read") else "○"
                lbl(row, f"{dot}  {n['message']}", fg=TEXT, bg=CARD,
                    wraplength=360, justify="left").pack(anchor="w", padx=10)
                lbl(row, n.get("created_at",""), font=FONT_SM, fg=SUBTEXT, bg=CARD
                    ).pack(anchor="e", padx=10)

        mark_read(self.user["_id"])
        self.refresh()
        btn(win, "Close", win.destroy, color=MUTED).pack(pady=10)
