import tkinter as tk
from tkinter import ttk, messagebox
from database import db, _ts, _new_id
from shared import (BG, CARD, CARD2, ACCENT, GREEN, TEXT, SUBTEXT, MUTED, DANGER, YELLOW,
                    FONT_H1, FONT_H2, FONT_H3, FONT_BODY, FONT_SM, FONT_BTN,
                    lbl, btn, card_frame, scrolled_frame, separator,
                    NotifBell, push_notification)
from chat import ChatWindow
from analytics import AnalyticsWindow


class DonorWindow(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title(f"FoodShare — Donor: {user['name']}")
        self.geometry("1100x700")
        self.configure(bg=BG)
        self._active_tab = tk.StringVar(value="home")
        self._build()
        self.mainloop()

    # ── shell ──────────────────────────────────────────────────────────────

    def _build(self):
        self._sidebar()
        self._content_area = tk.Frame(self, bg=BG)
        self._content_area.pack(side="right", fill="both", expand=True)
        self._show("home")

    def _sidebar(self):
        sb = tk.Frame(self, bg=CARD, width=210)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        # avatar
        av = tk.Frame(sb, bg=CARD)
        av.pack(fill="x", pady=(24, 8))
        tk.Label(av, text="🧑", font=("Helvetica", 36), bg=CARD).pack()
        lbl(av, self.user["name"],    font=FONT_H3, bg=CARD).pack()
        lbl(av, "🍱 Donor",           font=FONT_SM, fg=ACCENT, bg=CARD).pack()
        lbl(av, self.user.get("location",""), font=FONT_SM, fg=SUBTEXT, bg=CARD).pack()

        separator(sb)

        nav = [
            ("🏠",  "Home",         "home"),
            ("➕",  "Post Food",    "post"),
            ("📋",  "My Donations", "my_donations"),
            ("🏛️",  "NGO List",     "ngos"),
            ("👥",  "All Donors",   "donors"),
            ("📊",  "Analytics",    "analytics"),
        ]
        for icon, label, key in nav:
            b = tk.Button(sb, text=f" {icon}  {label}", font=FONT_BODY,
                          bg=CARD, fg=TEXT, relief="flat", anchor="w",
                          cursor="hand2", pady=10, padx=16,
                          command=lambda k=key: self._show(k))
            b.pack(fill="x")
            b.bind("<Enter>", lambda e, w=b: w.config(bg=CARD2))
            b.bind("<Leave>", lambda e, w=b: w.config(bg=CARD))

        separator(sb)

        # notification bell at the bottom
        bell_row = tk.Frame(sb, bg=CARD)
        bell_row.pack(fill="x", padx=16, pady=8)
        lbl(bell_row, "Notifications", font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(side="left")
        NotifBell(bell_row, self.user).pack(side="right")

        btn(sb, "⬅ Logout", self._logout, color=MUTED).pack(pady=16, padx=16, fill="x")

    def _show(self, key):
        for w in self._content_area.winfo_children():
            w.destroy()
        if key == "home":           self._tab_home()
        elif key == "post":         self._tab_post()
        elif key == "my_donations": self._tab_my_donations()
        elif key == "ngos":         self._tab_ngos()
        elif key == "donors":       self._tab_donors()
        elif key == "analytics":    AnalyticsWindow(self)

    # ── TAB: Home ──────────────────────────────────────────────────────────

    def _tab_home(self):
        p = self._content_area
        lbl(p, f"Welcome back, {self.user['name']} 👋", font=FONT_H1, bg=BG
            ).pack(pady=(24, 4), padx=24, anchor="w")
        lbl(p, "Here's today's snapshot", font=FONT_BODY, fg=SUBTEXT, bg=BG
            ).pack(padx=24, anchor="w")
        separator(p)

        stats_row = tk.Frame(p, bg=BG)
        stats_row.pack(fill="x", padx=20, pady=10)

        my_d   = db.find("donations", {"donor_id": self.user["_id"]})
        avail  = [d for d in my_d if d["status"] == "available"]
        picked = [d for d in my_d if d["status"] == "picked_up"]
        done   = [d for d in my_d if d["status"] == "delivered"]
        urgent = [d for d in my_d if d.get("urgent")]

        for icon, label, count, color in [
            ("🍱", "Total Posted",  len(my_d),   ACCENT),
            ("✅", "Delivered",     len(done),   GREEN),
            ("🚚", "Being Picked",  len(picked), "#60A5FA"),
            ("🚨", "Urgent",        len(urgent), DANGER),
        ]:
            c = card_frame(stats_row, bg=CARD)
            c.pack(side="left", padx=8, pady=4, ipadx=16, ipady=12, fill="y")
            lbl(c, icon,        font=("Helvetica",28), bg=CARD, fg=color).pack(pady=(8,2))
            lbl(c, str(count),  font=("Georgia",22,"bold"), bg=CARD, fg=TEXT).pack()
            lbl(c, label,       font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(pady=(0,8))

        separator(p)
        lbl(p, "📋  Recent Activity", font=FONT_H2, bg=BG).pack(padx=20, anchor="w", pady=(4,8))

        outer, inner = scrolled_frame(p)
        outer.pack(fill="both", expand=True, padx=16)

        all_notifs = db.find("notifications", {"user_id": self.user["_id"]})
        all_notifs.sort(key=lambda n: n.get("created_at",""), reverse=True)
        if not all_notifs:
            lbl(inner, "No activity yet. Post your first donation!", fg=SUBTEXT, bg=BG
                ).pack(pady=20)
        else:
            for n in all_notifs[:12]:
                row = card_frame(inner, bg=CARD)
                row.pack(fill="x", padx=4, pady=3, ipady=6)
                lbl(row, f"{'🔴' if n.get('type')=='urgent' else '🔵'}  {n['message']}",
                    fg=TEXT, bg=CARD, wraplength=600, justify="left").pack(anchor="w", padx=12)
                lbl(row, n.get("created_at",""), font=FONT_SM, fg=SUBTEXT, bg=CARD
                    ).pack(anchor="e", padx=12)

    # ── TAB: Post Food ──────────────────────────────────────────────────────

    def _tab_post(self):
        p = self._content_area
        lbl(p, "➕  Post a Donation", font=FONT_H1, bg=BG
            ).pack(pady=(24,4), padx=24, anchor="w")
        separator(p)

        form = card_frame(p, bg=CARD)
        form.place(relx=0.5, rely=0.5, anchor="center", width=500)

        def field(label, var, show=None):
            lbl(form, label, font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(fill="x", padx=20, pady=(8,1))
            kw = dict(textvariable=var, font=FONT_BODY, bg=CARD2, fg=TEXT,
                      insertbackground=TEXT, relief="flat", bd=0)
            if show: kw["show"] = show
            tk.Entry(form, **kw).pack(fill="x", padx=20, ipady=8, pady=(0,4))

        lbl(form, "🍽️  New Food Donation", font=FONT_H2, bg=CARD
            ).pack(pady=(20,8), padx=20, anchor="w")

        food_var  = tk.StringVar()
        qty_var   = tk.StringVar()
        loc_var   = tk.StringVar(value=self.user.get("location",""))
        desc_var  = tk.StringVar()

        field("Food Item / Name", food_var)
        field("Quantity (e.g. '30 portions')", qty_var)
        field("Pickup Location", loc_var)
        field("Short Description (optional)", desc_var)

        # urgent toggle
        urgent_var = tk.BooleanVar()
        urg_row = tk.Frame(form, bg=CARD)
        urg_row.pack(fill="x", padx=20, pady=6)
        tk.Checkbutton(urg_row, text="🚨  URGENT — food will spoil soon! (priority pickup)",
                       variable=urgent_var, bg=CARD, fg=DANGER,
                       selectcolor=CARD2, activebackground=CARD,
                       font=FONT_BODY).pack(anchor="w")

        # beneficiary
        lbl(form, "Food is for:", font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(anchor="w", padx=20)
        benef_var = tk.StringVar(value="humans")
        brow = tk.Frame(form, bg=CARD)
        brow.pack(fill="x", padx=20, pady=4)
        for val, label in [("humans","👤 Humans"), ("animals","🐾 Animals"), ("both","👤🐾 Both")]:
            tk.Radiobutton(brow, text=label, variable=benef_var, value=val,
                           bg=CARD, fg=TEXT, selectcolor=CARD2,
                           activebackground=CARD, font=FONT_BODY).pack(side="left", padx=8)

        def _submit():
            food = food_var.get().strip()
            qty  = qty_var.get().strip()
            loc  = loc_var.get().strip()
            if not food or not qty:
                messagebox.showerror("Missing", "Food item and quantity are required.")
                return
            doc = {
                "_id":        _new_id(),
                "donor_id":   self.user["_id"],
                "donor_name": self.user["name"],
                "food_item":  food,
                "quantity":   qty,
                "location":   loc,
                "description": desc_var.get().strip(),
                "status":     "available",
                "urgent":     urgent_var.get(),
                "beneficiary": benef_var.get(),
                "posted_at":  _ts(),
                "volunteer_id": None,
            }
            db.insert("donations", doc)

            # notify all volunteers
            volunteers = db.find("users", {"role": "volunteer"})
            tag = "urgent" if urgent_var.get() else "info"
            msg = f"{'🚨 URGENT: ' if urgent_var.get() else ''}New donation available: {food} ({qty}) at {loc} by {self.user['name']}"
            for v in volunteers:
                push_notification(v["_id"], msg, tag)

            # self-notification
            push_notification(self.user["_id"],
                              f"✅ Your donation '{food}' has been posted successfully!", "success")

            messagebox.showinfo("Posted!", f"'{food}' has been listed successfully!\nVolunteers have been notified.")
            food_var.set(""); qty_var.set(""); desc_var.set("")
            urgent_var.set(False)
            self._show("my_donations")

        btn(form, "📤  Post Donation", _submit).pack(padx=20, pady=16, fill="x")

    # ── TAB: My Donations ──────────────────────────────────────────────────

    def _tab_my_donations(self):
        p = self._content_area
        lbl(p, "📋  My Donations", font=FONT_H1, bg=BG
            ).pack(pady=(24,4), padx=24, anchor="w")
        separator(p)

        outer, inner = scrolled_frame(p)
        outer.pack(fill="both", expand=True, padx=16, pady=8)

        donations = db.find("donations", {"donor_id": self.user["_id"]})
        donations.sort(key=lambda d: (not d.get("urgent"), d.get("posted_at","")), reverse=False)
        # urgent first
        donations.sort(key=lambda d: d.get("urgent", False), reverse=True)

        if not donations:
            lbl(inner, "You haven't posted any donations yet.", fg=SUBTEXT, bg=BG
                ).pack(pady=30)
            return

        for d in donations:
            self._donation_card(inner, d, is_donor=True)

    def _donation_card(self, parent, d, is_donor=False):
        status_color = {
            "available":  ACCENT,
            "picked_up":  "#60A5FA",
            "delivered":  GREEN,
            "cancelled":  MUTED,
        }.get(d.get("status",""), MUTED)

        urg_border = DANGER if d.get("urgent") else CARD

        card = tk.Frame(parent, bg=CARD, highlightbackground=urg_border,
                        highlightthickness=2)
        card.pack(fill="x", padx=4, pady=5, ipady=8)

        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x", padx=12, pady=(8,4))

        # urgent badge
        if d.get("urgent"):
            tk.Label(top, text=" 🚨 URGENT ", bg=DANGER, fg="white",
                     font=FONT_SM).pack(side="left", padx=(0,8))

        lbl(top, d["food_item"], font=FONT_H3, bg=CARD).pack(side="left")
        tk.Label(top, text=f" {d['status'].upper()} ",
                 bg=status_color, fg="white", font=FONT_SM).pack(side="right")

        mid = tk.Frame(card, bg=CARD)
        mid.pack(fill="x", padx=12, pady=2)
        meta = f"📦 {d.get('quantity','?')}   📍 {d.get('location','?')}   " \
               f"{'👤' if d.get('beneficiary')=='humans' else '🐾' if d.get('beneficiary')=='animals' else '👤🐾'}  {d.get('beneficiary','?')}   " \
               f"🕐 {d.get('posted_at','')[:16]}"
        lbl(mid, meta, font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(anchor="w")

        if d.get("description"):
            lbl(card, d["description"], font=FONT_SM, fg=SUBTEXT, bg=CARD
                ).pack(anchor="w", padx=12, pady=(0,4))

        # action buttons
        acts = tk.Frame(card, bg=CARD)
        acts.pack(fill="x", padx=12, pady=(4,6))

        if is_donor:
            if d["status"] == "available":
                btn(acts, "🗑 Cancel", lambda did=d["_id"]: self._cancel(did),
                    color=DANGER).pack(side="left", padx=4)

            # chat button — only if a volunteer is assigned
            if d.get("volunteer_id"):
                vol = db.find_one("users", {"_id": d["volunteer_id"]})
                if vol:
                    btn(acts, f"💬 Chat with {vol['name']}",
                        lambda v=vol, dd=d: ChatWindow(self, self.user, v, dd),
                        color="#60A5FA").pack(side="left", padx=4)

    def _cancel(self, donation_id):
        db.update("donations", {"_id": donation_id}, {"status": "cancelled"})
        push_notification(self.user["_id"], "Donation cancelled.", "info")
        messagebox.showinfo("Cancelled", "Donation has been cancelled.")
        self._show("my_donations")

    # ── TAB: NGO List ──────────────────────────────────────────────────────

    def _tab_ngos(self):
        p = self._content_area
        lbl(p, "🏛️  Registered NGOs", font=FONT_H1, bg=BG
            ).pack(pady=(24,4), padx=24, anchor="w")
        separator(p)

        outer, inner = scrolled_frame(p)
        outer.pack(fill="both", expand=True, padx=16, pady=8)

        ngos = db.find("ngos")
        if not ngos:
            lbl(inner, "No NGOs registered yet.", fg=SUBTEXT, bg=BG).pack(pady=20)
            return

        for n in ngos:
            card = card_frame(inner, bg=CARD)
            card.pack(fill="x", padx=4, pady=5, ipady=8)
            top = tk.Frame(card, bg=CARD)
            top.pack(fill="x", padx=12, pady=(8,4))
            lbl(top, f"🏛️  {n['name']}", font=FONT_H3, bg=CARD).pack(side="left")
            lbl(top, n.get("city",""), font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(side="right")
            lbl(card, f"📞 {n.get('contact','N/A')}   🗓 Registered: {n.get('registered','')[:10]}",
                font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(anchor="w", padx=12, pady=(0,6))

    # ── TAB: All Donors ─────────────────────────────────────────────────────

    def _tab_donors(self):
        p = self._content_area
        lbl(p, "👥  Community Donors", font=FONT_H1, bg=BG
            ).pack(pady=(24,4), padx=24, anchor="w")
        separator(p)

        outer, inner = scrolled_frame(p)
        outer.pack(fill="both", expand=True, padx=16, pady=8)

        users = db.find("users")
        donors = [u for u in users if u.get("role") == "donor"]

        if not donors:
            lbl(inner, "No donors registered yet.", fg=SUBTEXT, bg=BG).pack(pady=20)
            return

        for u in donors:
            card = card_frame(inner, bg=CARD)
            card.pack(fill="x", padx=4, pady=5, ipady=6)
            top = tk.Frame(card, bg=CARD)
            top.pack(fill="x", padx=12, pady=(8,2))
            lbl(top, f"🧑  {u['name']}", font=FONT_H3, bg=CARD).pack(side="left")
            lbl(top, u.get("location",""), font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(side="right")
            cnt = db.count("donations", {"donor_id": u["_id"]})
            lbl(card, f"📞 {u.get('phone','?')}   🍱 {cnt} donations   🕐 Joined: {u.get('joined','')[:10]}",
                font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(anchor="w", padx=12, pady=(0,6))

    # ── logout ─────────────────────────────────────────────────────────────

    def _logout(self):
        self.destroy()
        from main import LoginScreen
        LoginScreen()
