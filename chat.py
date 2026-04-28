import tkinter as tk
from tkinter import scrolledtext
from database import db, _ts, _new_id
from shared import (BG, CARD, CARD2, ACCENT, GREEN, TEXT, SUBTEXT, MUTED,
                    FONT_H2, FONT_BODY, FONT_SM, FONT_BTN, lbl, btn,
                    card_frame, separator)


class ChatWindow(tk.Toplevel):
    """
    Opens a chat between two users linked to a donation.
    Pass:
        current_user  — the logged-in user dict
        other_user    — the other party (donor ↔ volunteer)
        donation      — the donation dict this chat belongs to
    """

    def __init__(self, parent, current_user, other_user, donation):
        super().__init__(parent)
        self.title(f"Chat — {donation['food_item']}")
        self.configure(bg=BG)
        self.geometry("480x560")
        self.resizable(False, True)

        self.me    = current_user
        self.other = other_user
        self.don   = donation
        self._build()
        self._load_messages()
        self._poll()

    # ── UI ─────────────────────────────────────────────────────────────────

    def _build(self):
        # header
        hdr = tk.Frame(self, bg=CARD, pady=10)
        hdr.pack(fill="x")
        lbl(hdr, f"💬  Chatting with {self.other['name']}", font=FONT_H2, bg=CARD
            ).pack(side="left", padx=16)
        lbl(hdr, f"Re: {self.don['food_item']}", font=FONT_SM, fg=SUBTEXT, bg=CARD
            ).pack(side="right", padx=16)

        separator(self)

        # message area
        self._msg_area = scrolledtext.ScrolledText(
            self, bg=BG, fg=TEXT, font=FONT_BODY,
            relief="flat", state="disabled",
            wrap="word", height=22, insertbackground=TEXT,
        )
        self._msg_area.pack(fill="both", expand=True, padx=10, pady=4)

        # bubble tags
        self._msg_area.tag_config("me",
            foreground="#FFF7ED", background=ACCENT,
            lmargin1=80, lmargin2=80, rmargin=10, spacing3=6)
        self._msg_area.tag_config("them",
            foreground=TEXT, background=CARD2,
            lmargin1=10, lmargin2=10, rmargin=80, spacing3=6)
        self._msg_area.tag_config("ts",
            foreground=SUBTEXT, font=("Helvetica", 8),
            justify="center", spacing1=2, spacing3=8)

        separator(self)

        # input bar
        bar = tk.Frame(self, bg=CARD, pady=8)
        bar.pack(fill="x", side="bottom")

        self._input = tk.Entry(bar, font=FONT_BODY, bg=CARD2, fg=TEXT,
                               relief="flat", insertbackground=TEXT)
        self._input.pack(side="left", fill="x", expand=True, padx=10, ipady=8)
        self._input.bind("<Return>", self._send)

        btn(bar, "Send ➤", self._send).pack(side="right", padx=10)

    # ── data ───────────────────────────────────────────────────────────────

    def _load_messages(self):
        msgs = db.find("messages", {"donation_id": self.don["_id"]})
        msgs.sort(key=lambda m: m.get("sent_at", ""))

        self._msg_area.configure(state="normal")
        self._msg_area.delete("1.0", "end")

        for m in msgs:
            self._render(m)

        self._msg_area.configure(state="disabled")
        self._msg_area.see("end")
        self._last_count = len(msgs)

    def _render(self, m):
        tag  = "me" if m["sender_id"] == self.me["_id"] else "them"
        who  = "You" if tag == "me" else m["sender_name"]
        time = m.get("sent_at", "")[-8:]   # HH:MM:SS

        self._msg_area.insert("end", f"  {m['text']}  \n", tag)
        self._msg_area.insert("end", f"{who}  {time}\n", "ts")

    def _send(self, _=None):
        text = self._input.get().strip()
        if not text:
            return
        msg = {
            "_id":         _new_id(),
            "donation_id": self.don["_id"],
            "sender_id":   self.me["_id"],
            "sender_name": self.me["name"],
            "receiver_id": self.other["_id"],
            "text":        text,
            "sent_at":     _ts(),
        }
        db.insert("messages", msg)
        self._input.delete(0, "end")
        self._load_messages()

    def _poll(self):
        """Refresh messages every 3 seconds (simulate real-time)."""
        msgs = db.find("messages", {"donation_id": self.don["_id"]})
        if len(msgs) != self._last_count:
            self._load_messages()
        self.after(3000, self._poll)
