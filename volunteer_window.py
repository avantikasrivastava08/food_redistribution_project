import tkinter as tk
from tkinter import ttk, messagebox
from database import db, _ts, _new_id
from shared import (BG, CARD, CARD2, ACCENT, GREEN, TEXT, SUBTEXT, MUTED, DANGER, YELLOW,
                    FONT_H1, FONT_H2, FONT_H3, FONT_BODY, FONT_SM, FONT_BTN,
                    lbl, btn, card_frame, scrolled_frame, separator,
                    NotifBell, push_notification)
from chat import ChatWindow
from analytics import AnalyticsWindow


class VolunteerWindow(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title(f"FoodShare — Volunteer: {user['name']}")
        self.geometry("1100x700")
        self.configure(bg=BG)
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

        av = tk.Frame(sb, bg=CARD)
        av.pack(fill="x", pady=(24, 8))
        tk.Label(av, text="🚴", font=("Helvetica", 36), bg=CARD).pack()
        lbl(av, self.user["name"],    font=FONT_H3, bg=CARD).pack()
        lbl(av, "🚴 Volunteer",        font=FONT_SM, fg=GREEN, bg=CARD).pack()
        lbl(av, self.user.get("location",""), font=FONT_SM, fg=SUBTEXT, bg=CARD).pack()

        separator(sb)

        nav = [
            ("🏠",  "Home",          "home"),
            ("📦",  "Available Food", "available"),
            ("🚚",  "My Pickups",     "my_pickups"),
            ("🏛️",  "NGO List",       "ngos"),
            ("👥",  "All Volunteers", "volunteers"),
            ("📊",  "Analytics",      "analytics"),
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

        bell_row = tk.Frame(sb, bg=CARD)
        bell_row.pack(fill="x", padx=16, pady=8)
        lbl(bell_row, "Notifications", font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(side="left")
        NotifBell(bell_row, self.user).pack(side="right")

        btn(sb, "⬅ Logout", self._logout, color=MUTED).pack(pady=16, padx=16, fill="x")

    def _show(self, key):
        for w in self._content_area.winfo_children():
            w.destroy()
        if key == "home":       self._tab_home()
        elif key == "available":self._tab_available()
        elif key == "my_pickups":self._tab_my_pickups()
        elif key == "ngos":     self._tab_ngos()
        elif key == "volunteers":self._tab_volunteers()
        elif key == "analytics":AnalyticsWindow(self)

    # ── TAB: Home ──────────────────────────────────────────────────────────

    def _tab_home(self):
        p = self._content_area
        lbl(p, f"Hey, {self.user['name']} 🚴", font=FONT_H1, bg=BG
            ).pack(pady=(24,4), padx=24, anchor="w")
        lbl(p, "Ready to make a difference today?", font=FONT_BODY, fg=SUBTEXT, bg=BG
            ).pack(padx=24, anchor="w")
        separator(p)

        stats_row = tk.Frame(p, bg=BG)
        stats_row.pack(fill="x", padx=20, pady=10)

        my_pickups  = db.find("donations", {"volunteer_id": self.user["_id"]})
        delivered   = [d for d in my_pickups if d["status"] == "delivered"]
        in_progress = [d for d in my_pickups if d["status"] == "picked_up"]
        avail_all   = db.find("donations", {"status": "available"})
        urgent_all  = [d for d in avail_all if d.get("urgent")]

        for icon, label, count, color in [
            ("✅", "Delivered",      len(delivered),   GREEN),
            ("🚚", "In Progress",    len(in_progress), "#60A5FA"),
            ("📦", "Available",      len(avail_all),   ACCENT),
            ("🚨", "Urgent",         len(urgent_all),  DANGER),
        ]:
            c = card_frame(stats_row, bg=CARD)
            c.pack(side="left", padx=8, pady=4, ipadx=16, ipady=12, fill="y")
            lbl(c, icon,       font=("Helvetica",28), bg=CARD, fg=color).pack(pady=(8,2))
            lbl(c, str(count), font=("Georgia",22,"bold"), bg=CARD, fg=TEXT).pack()
            lbl(c, label,      font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(pady=(0,8))

        separator(p)

        # urgent section
        if urgent_all:
            lbl(p, "🚨  URGENT Pickups Needed", font=FONT_H2, fg=DANGER, bg=BG
                ).pack(padx=20, anchor="w", pady=(4,8))
            for d in urgent_all[:3]:
                self._donation_card(p, d)

            separator(p)

        lbl(p, "📋  Recent Notifications", font=FONT_H2, bg=BG
            ).pack(padx=20, anchor="w", pady=(4,8))

        outer, inner = scrolled_frame(p)
        outer.pack(fill="both", expand=True, padx=16)

        notifs = db.find("notifications", {"user_id": self.user["_id"]})
        notifs.sort(key=lambda n: n.get("created_at",""), reverse=True)
        if not notifs:
            lbl(inner, "No notifications yet.", fg=SUBTEXT, bg=BG).pack(pady=20)
        else:
            for n in notifs[:10]:
                row = card_frame(inner, bg=CARD)
                row.pack(fill="x", padx=4, pady=3, ipady=6)
                icon = "🔴" if n.get("type") == "urgent" else "🟢" if n.get("type") == "success" else "🔵"
                lbl(row, f"{icon}  {n['message']}", fg=TEXT, bg=CARD,
                    wraplength=600, justify="left").pack(anchor="w", padx=12)
                lbl(row, n.get("created_at",""), font=FONT_SM, fg=SUBTEXT, bg=CARD
                    ).pack(anchor="e", padx=12)

    # ── TAB: Available Food ────────────────────────────────────────────────

    def _tab_available(self):
        p = self._content_area
        lbl(p, "📦  Available Food", font=FONT_H1, bg=BG
            ).pack(pady=(24,4), padx=24, anchor="w")
        separator(p)

        # filter bar
        filter_bar = tk.Frame(p, bg=BG)
        filter_bar.pack(fill="x", padx=20, pady=4)
        lbl(filter_bar, "Filter:", fg=SUBTEXT, bg=BG).pack(side="left")

        self._filter_benef = tk.StringVar(value="all")
        self._filter_urgent = tk.BooleanVar(value=False)

        for val, label in [("all","All"), ("humans","Humans"), ("animals","Animals"), ("both","Both")]:
            tk.Radiobutton(filter_bar, text=label, variable=self._filter_benef, value=val,
                           bg=BG, fg=TEXT, selectcolor=CARD2,
                           activebackground=BG, font=FONT_SM,
                           command=lambda: self._refresh_available(inner)
                           ).pack(side="left", padx=6)

        tk.Checkbutton(filter_bar, text="🚨 Urgent only", variable=self._filter_urgent,
                       bg=BG, fg=DANGER, selectcolor=CARD2, activebackground=BG,
                       font=FONT_SM,
                       command=lambda: self._refresh_available(inner)
                       ).pack(side="left", padx=16)

        outer, inner = scrolled_frame(p)
        outer.pack(fill="both", expand=True, padx=16, pady=4)
        self._avail_inner = inner
        self._refresh_available(inner)

    def _refresh_available(self, inner):
        for w in inner.winfo_children():
            w.destroy()

        donations = db.find("donations", {"status": "available"})
        # urgent first
        donations.sort(key=lambda d: d.get("urgent", False), reverse=True)

        benef = self._filter_benef.get()
        urg   = self._filter_urgent.get()

        if benef != "all":
            donations = [d for d in donations if d.get("beneficiary") == benef]
        if urg:
            donations = [d for d in donations if d.get("urgent")]

        if not donations:
            lbl(inner, "No available donations matching your filter.", fg=SUBTEXT, bg=BG
                ).pack(pady=30)
            return
        for d in donations:
            self._donation_card(inner, d)

    def _donation_card(self, parent, d):
        urg_border = DANGER if d.get("urgent") else CARD
        card = tk.Frame(parent, bg=CARD, highlightbackground=urg_border, highlightthickness=2)
        card.pack(fill="x", padx=4, pady=5, ipady=4)

        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x", padx=12, pady=(8,4))

        if d.get("urgent"):
            tk.Label(top, text=" 🚨 URGENT ", bg=DANGER, fg="white",
                     font=FONT_SM).pack(side="left", padx=(0,8))

        lbl(top, d["food_item"], font=FONT_H3, bg=CARD).pack(side="left")

        benef_icon = {"humans":"👤","animals":"🐾"}.get(d.get("beneficiary","both"), "👤🐾")
        tk.Label(top, text=f" {benef_icon} {d.get('beneficiary','?')} ",
                 bg=CARD2, fg=TEXT, font=FONT_SM).pack(side="right")

        mid = tk.Frame(card, bg=CARD)
        mid.pack(fill="x", padx=12, pady=2)
        lbl(mid, f"📦 {d.get('quantity','?')}   📍 {d.get('location','?')}   "
                 f"🧑 {d.get('donor_name','?')}   🕐 {d.get('posted_at','')[:16]}",
            font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(anchor="w")

        if d.get("description"):
            lbl(card, d["description"], font=FONT_SM, fg=SUBTEXT, bg=CARD
                ).pack(anchor="w", padx=12)

        acts = tk.Frame(card, bg=CARD)
        acts.pack(fill="x", padx=12, pady=(4,8))

        if d["status"] == "available":
            btn(acts, "✋  Accept Pickup", lambda did=d["_id"]: self._accept(did),
                color=GREEN).pack(side="left", padx=4)

        # chat button
        if d.get("volunteer_id") == self.user["_id"]:
            donor = db.find_one("users", {"_id": d["donor_id"]})
            if donor:
                btn(acts, f"💬 Chat with {donor['name']}",
                    lambda dn=donor, dd=d: ChatWindow(self, self.user, dn, dd),
                    color="#60A5FA").pack(side="left", padx=4)

    def _accept(self, donation_id):
        d = db.find_one("donations", {"_id": donation_id})
        if not d:
            return
        if d["status"] != "available":
            messagebox.showwarning("Taken", "This donation was already claimed.")
            self._show("available")
            return

        db.update("donations", {"_id": donation_id}, {
            "status":       "picked_up",
            "volunteer_id": self.user["_id"],
            "picked_at":    _ts(),
        })

        # notify donor
        push_notification(d["donor_id"],
            f"🚴 {self.user['name']} is on the way to pick up '{d['food_item']}'!", "success")

        # self notification
        push_notification(self.user["_id"],
            f"✅ You accepted pickup for '{d['food_item']}' from {d['donor_name']}.", "success")

        messagebox.showinfo("Accepted!", f"You've claimed the pickup for '{d['food_item']}'.\n"
                                         f"Contact the donor to coordinate.")
        self._show("my_pickups")

    # ── TAB: My Pickups ─────────────────────────────────────────────────────

    def _tab_my_pickups(self):
        p = self._content_area
        lbl(p, "🚚  My Pickups", font=FONT_H1, bg=BG
            ).pack(pady=(24,4), padx=24, anchor="w")
        separator(p)

        outer, inner = scrolled_frame(p)
        outer.pack(fill="both", expand=True, padx=16, pady=8)

        pickups = db.find("donations", {"volunteer_id": self.user["_id"]})
        pickups.sort(key=lambda d: d.get("picked_at",""), reverse=True)

        if not pickups:
            lbl(inner, "You haven't accepted any pickups yet.", fg=SUBTEXT, bg=BG
                ).pack(pady=30)
            return

        for d in pickups:
            self._pickup_card(inner, d)

    def _pickup_card(self, parent, d):
        status_color = {
            "picked_up": "#60A5FA",
            "delivered": GREEN,
        }.get(d.get("status",""), MUTED)

        card = card_frame(parent, bg=CARD)
        card.pack(fill="x", padx=4, pady=5, ipady=4)

        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x", padx=12, pady=(8,4))
        lbl(top, d["food_item"], font=FONT_H3, bg=CARD).pack(side="left")
        tk.Label(top, text=f" {d['status'].upper()} ",
                 bg=status_color, fg="white", font=FONT_SM).pack(side="right")

        lbl(card, f"📦 {d.get('quantity','?')}   📍 {d.get('location','?')}   "
                  f"🧑 Donor: {d.get('donor_name','?')}   "
                  f"{'🚚 Picked: ' + d.get('picked_at','')[:16] if d.get('picked_at') else ''}",
            font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(anchor="w", padx=12, pady=2)

        acts = tk.Frame(card, bg=CARD)
        acts.pack(fill="x", padx=12, pady=(4,8))

        if d["status"] == "picked_up":
            btn(acts, "✅ Mark Delivered", lambda did=d["_id"], dn=d["donor_id"],
                fi=d["food_item"]: self._deliver(did, dn, fi),
                color=GREEN).pack(side="left", padx=4)

        # chat
        donor = db.find_one("users", {"_id": d["donor_id"]})
        if donor:
            btn(acts, f"💬 Chat with {donor['name']}",
                lambda dn=donor, dd=d: ChatWindow(self, self.user, dn, dd),
                color="#60A5FA").pack(side="left", padx=4)

    def _deliver(self, donation_id, donor_id, food_item):
        db.update("donations", {"_id": donation_id}, {
            "status":       "delivered",
            "delivered_at": _ts(),
        })
        push_notification(donor_id,
            f"🎉 Your donation '{food_item}' has been delivered successfully!", "success")
        push_notification(self.user["_id"],
            f"🏆 Great job! You delivered '{food_item}'.", "success")
        messagebox.showinfo("Delivered!", f"'{food_item}' marked as delivered. Thank you! 🙏")
        self._show("my_pickups")

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
            card.pack(fill="x", padx=4, pady=5, ipady=6)
            top = tk.Frame(card, bg=CARD)
            top.pack(fill="x", padx=12, pady=(8,4))
            lbl(top, f"🏛️  {n['name']}", font=FONT_H3, bg=CARD).pack(side="left")
            lbl(top, n.get("city",""), font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(side="right")
            lbl(card, f"📞 {n.get('contact','N/A')}   🗓 Registered: {n.get('registered','')[:10]}",
                font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(anchor="w", padx=12, pady=(0,6))

    # ── TAB: All Volunteers ─────────────────────────────────────────────────

    def _tab_volunteers(self):
        p = self._content_area
        lbl(p, "👥  Community Volunteers", font=FONT_H1, bg=BG
            ).pack(pady=(24,4), padx=24, anchor="w")
        separator(p)
        outer, inner = scrolled_frame(p)
        outer.pack(fill="both", expand=True, padx=16, pady=8)
        users = db.find("users")
        vols = [u for u in users if u.get("role") == "volunteer"]
        if not vols:
            lbl(inner, "No volunteers yet.", fg=SUBTEXT, bg=BG).pack(pady=20)
            return
        for u in vols:
            card = card_frame(inner, bg=CARD)
            card.pack(fill="x", padx=4, pady=5, ipady=6)
            top = tk.Frame(card, bg=CARD)
            top.pack(fill="x", padx=12, pady=(8,4))
            lbl(top, f"🚴  {u['name']}", font=FONT_H3, bg=CARD).pack(side="left")
            lbl(top, u.get("location",""), font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(side="right")
            cnt = db.count("donations", {"volunteer_id": u["_id"]})
            lbl(card, f"📞 {u.get('phone','?')}   🚚 {cnt} pickups   🕐 Joined: {u.get('joined','')[:10]}",
                font=FONT_SM, fg=SUBTEXT, bg=CARD).pack(anchor="w", padx=12, pady=(0,6))

    # ── logout ─────────────────────────────────────────────────────────────

    def _logout(self):
        self.destroy()
        from main import LoginScreen
        LoginScreen()
