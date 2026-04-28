import tkinter as tk
from tkinter import ttk, messagebox
from database import db, _ts, _new_id
from donor_window import DonorWindow
from volunteer_window import VolunteerWindow
import hashlib

# ── colour palette ─────────────────────────────────────────────────────────
BG       = "#0F1923"
CARD     = "#1A2636"
ACCENT   = "#F97316"    # warm orange
GREEN    = "#22C55E"
MUTED    = "#64748B"
TEXT     = "#F1F5F9"
SUBTEXT  = "#94A3B8"
DANGER   = "#EF4444"
BORDER   = "#2D3E50"

FONT_H1  = ("Georgia", 26, "bold")
FONT_H2  = ("Georgia", 18, "bold")
FONT_H3  = ("Georgia", 14, "bold")
FONT_BODY= ("Helvetica", 11)
FONT_SM  = ("Helvetica", 9)
FONT_BTN = ("Helvetica", 11, "bold")

def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()


class LoginScreen(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FoodShare — Food Redistribution Network")
        self.geometry("860x620")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._mode = tk.StringVar(value="login")   # login / register
        self._role = tk.StringVar(value="donor")
        self._build()
        self.mainloop()

    # ── layout ─────────────────────────────────────────────────────────────

    def _build(self):
        # left panel — branding
        left = tk.Frame(self, bg=ACCENT, width=300)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="🍛", font=("Helvetica", 60), bg=ACCENT).pack(pady=(80,10))
        tk.Label(left, text="FoodShare", font=("Georgia", 28, "bold"),
                 bg=ACCENT, fg="white").pack()
        tk.Label(left, text="Connecting surplus\nto need", font=("Helvetica", 13),
                 bg=ACCENT, fg="#FED7AA", justify="center").pack(pady=10)

        tk.Label(left, text="━━━━━━━━━", bg=ACCENT, fg="#FED7AA").pack(pady=20)

        stats_frame = tk.Frame(left, bg=ACCENT)
        stats_frame.pack()
        for icon, label in [("🏠", "Hostels"), ("🍽️", "Restaurants"), ("🤝", "NGOs")]:
            row = tk.Frame(stats_frame, bg=ACCENT)
            row.pack(pady=4)
            tk.Label(row, text=f"{icon}  {label}", font=("Helvetica", 12),
                     bg=ACCENT, fg="#FFF7ED").pack()

        # right panel — form
        self._right = tk.Frame(self, bg=BG)
        self._right.pack(side="right", fill="both", expand=True)
        self._draw_form()

    def _draw_form(self):
        for w in self._right.winfo_children():
            w.destroy()

        f = tk.Frame(self._right, bg=BG)
        f.place(relx=0.5, rely=0.5, anchor="center")

        mode = self._mode.get()
        title = "Welcome Back" if mode == "login" else "Create Account"
        tk.Label(f, text=title, font=FONT_H1, bg=BG, fg=TEXT).pack(pady=(0, 4))
        tk.Label(f, text="Food redistribution network",
                 font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(pady=(0, 24))

        # name field (register only)
        self._name_var = tk.StringVar()
        if mode == "register":
            self._field(f, "Full Name", self._name_var)

        self._email_var = tk.StringVar()
        self._pw_var    = tk.StringVar()
        self._phone_var = tk.StringVar()
        self._loc_var   = tk.StringVar()

        self._field(f, "Email",    self._email_var)
        self._field(f, "Password", self._pw_var, show="•")

        if mode == "register":
            self._field(f, "Phone",    self._phone_var)
            self._field(f, "City / Location", self._loc_var)

            # role toggle
            role_f = tk.Frame(f, bg=BG)
            role_f.pack(fill="x", pady=6)
            tk.Label(role_f, text="I am a:", font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(side="left")
            for val, lbl in [("donor", "🍱 Donor"), ("volunteer", "🚴 Volunteer")]:
                rb = tk.Radiobutton(role_f, text=lbl, variable=self._role, value=val,
                                    bg=BG, fg=TEXT, selectcolor=CARD,
                                    activebackground=BG, font=FONT_BODY)
                rb.pack(side="left", padx=10)

        # submit
        btn_text = "Sign In" if mode == "login" else "Register"
        btn = tk.Button(f, text=btn_text, font=FONT_BTN, bg=ACCENT, fg="white",
                        relief="flat", cursor="hand2", padx=20, pady=10,
                        command=self._submit)
        btn.pack(fill="x", pady=(14, 6))

        # toggle link
        if mode == "login":
            link_text = "New here? Create account"
            link_cmd  = lambda: [self._mode.set("register"), self._draw_form()]
        else:
            link_text = "Already have an account? Sign in"
            link_cmd  = lambda: [self._mode.set("login"),    self._draw_form()]

        tk.Button(f, text=link_text, font=FONT_SM, bg=BG, fg=ACCENT,
                  relief="flat", cursor="hand2", command=link_cmd).pack()

    def _field(self, parent, label, var, show=None):
        tk.Label(parent, text=label, font=FONT_SM, bg=BG, fg=SUBTEXT, anchor="w"
                 ).pack(fill="x")
        kw = dict(textvariable=var, font=FONT_BODY, bg=CARD, fg=TEXT,
                  insertbackground=TEXT, relief="flat", bd=0)
        if show:
            kw["show"] = show
        e = tk.Entry(parent, **kw)
        e.pack(fill="x", ipady=8, pady=(2, 10))
        return e

    # ── actions ────────────────────────────────────────────────────────────

    def _submit(self):
        email = self._email_var.get().strip()
        pw    = self._pw_var.get().strip()

        if not email or not pw:
            messagebox.showerror("Missing", "Email and password are required.")
            return

        if self._mode.get() == "login":
            user = db.find_one("users", {"email": email})
            if not user:
                messagebox.showerror("Not found", "No account with that email.")
                return
            if user.get("pw_hash") and user["pw_hash"] != _hash(pw):
                messagebox.showerror("Wrong password", "Incorrect password.")
                return
            self._open_dashboard(user)

        else:   # register
            name  = self._name_var.get().strip()
            phone = self._phone_var.get().strip()
            loc   = self._loc_var.get().strip()
            role  = self._role.get()

            if not name or not phone:
                messagebox.showerror("Missing", "All fields are required.")
                return
            if db.find_one("users", {"email": email}):
                messagebox.showerror("Exists", "That email is already registered.")
                return

            user = {
                "_id":      _new_id(),
                "name":     name,
                "email":    email,
                "phone":    phone,
                "location": loc,
                "role":     role,
                "pw_hash":  _hash(pw),
                "joined":   _ts(),
            }
            db.insert("users", user)
            messagebox.showinfo("Welcome!", f"Account created! Welcome, {name} 🎉")
            self._open_dashboard(user)

    def _open_dashboard(self, user):
        self.destroy()
        if user["role"] == "donor":
            DonorWindow(user)
        else:
            VolunteerWindow(user)


if __name__ == "__main__":
    LoginScreen()