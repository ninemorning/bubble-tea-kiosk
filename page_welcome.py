import json
import tkinter as tk
from tkinter import ttk, messagebox

MEMBERS_FILE = "data/members.json"

C = {
    "bg":       "#FFF5F9",
    "header":   "#F9C8D9",
    "btn":      "#F4A7C0",
    "accent":   "#D4547A",
    "text":     "#3A2030",
    "subtext":  "#7A5068",
    "confirm":  "#E87FAA",
    "confirm_t":"#FFFFFF",
    "entry_bg": "#FFFFFF",
    "card":     "#FFFFFF",
}


def _load_members():
    try:
        with open(MEMBERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_members(members):
    with open(MEMBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False, indent=2)


class WelcomePage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=C["bg"], **kwargs)
        self.app = app
        self._build_ui()

    def on_enter(self):
        if hasattr(self, "login_id"):
            self.login_id.delete(0, "end")
            self.login_pw.delete(0, "end")

    def _build_ui(self):
        # 상단 배너
        banner = tk.Frame(self, bg=C["header"])
        banner.pack(fill="x", ipady=40)
        tk.Label(banner, text="🧋", font=("맑은 고딕", 56),
                 bg=C["header"]).pack()
        tk.Label(banner, text="버블티 키오스크",
                 font=("맑은 고딕", 28, "bold"),
                 bg=C["header"], fg=C["accent"]).pack()
        tk.Label(banner, text="나만의 버블티를 만들어보세요 ✨",
                 font=("맑은 고딕", 12),
                 bg=C["header"], fg=C["subtext"]).pack(pady=(4, 0))

        # 가운데 카드
        outer = tk.Frame(self, bg=C["bg"])
        outer.pack(expand=True)

        card = tk.Frame(outer, bg=C["card"], relief="solid", bd=1,
                        padx=52, pady=36)
        card.pack(padx=80, pady=28)

        # 탭
        self.tab_var = tk.StringVar(value="login")
        tab_row = tk.Frame(card, bg=C["card"])
        tab_row.pack(fill="x", pady=(0, 16))
        for label, val in [("로그인", "login"), ("회원가입", "register")]:
            tk.Radiobutton(tab_row, text=label,
                           variable=self.tab_var, value=val,
                           font=("맑은 고딕", 13),
                           bg=C["card"], fg=C["text"],
                           selectcolor=C["btn"],
                           activebackground=C["card"],
                           command=self._switch_tab).pack(side="left", padx=14)

        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=(0, 18))

        self.form_frame = tk.Frame(card, bg=C["card"])
        self.form_frame.pack(fill="x")
        self._build_login_form()

        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=20)
        tk.Label(card, text="또는", font=("맑은 고딕", 10),
                 bg=C["card"], fg=C["subtext"]).pack()
        tk.Button(card, text="비회원으로 입장하기",
                  font=("맑은 고딕", 11),
                  bg=C["btn"], fg=C["text"],
                  relief="flat", padx=22, pady=7,
                  command=self._guest_enter).pack(pady=(10, 0))

    def _clear_form(self):
        for w in self.form_frame.winfo_children():
            w.destroy()

    def _build_login_form(self):
        self._clear_form()
        f = self.form_frame
        tk.Label(f, text="아이디", font=("맑은 고딕", 11),
                 bg=C["card"], fg=C["text"]).pack(anchor="w")
        self.login_id = tk.Entry(f, font=("맑은 고딕", 11), width=28,
                                  bg=C["entry_bg"], relief="solid", bd=1)
        self.login_id.pack(fill="x", pady=(2, 10))
        tk.Label(f, text="비밀번호", font=("맑은 고딕", 11),
                 bg=C["card"], fg=C["text"]).pack(anchor="w")
        self.login_pw = tk.Entry(f, show="●", font=("맑은 고딕", 11), width=28,
                                  bg=C["entry_bg"], relief="solid", bd=1)
        self.login_pw.pack(fill="x", pady=(2, 18))
        self.login_pw.bind("<Return>", lambda e: self._do_login())
        tk.Button(f, text="로그인하기",
                  font=("맑은 고딕", 12, "bold"),
                  bg=C["confirm"], fg=C["confirm_t"],
                  relief="flat", pady=9,
                  command=self._do_login).pack(fill="x")

    def _build_register_form(self):
        self._clear_form()
        f = self.form_frame
        for label, attr, show in [("아이디", "reg_id", ""),
                                   ("비밀번호", "reg_pw", "●"),
                                   ("비밀번호 확인", "reg_pw2", "●")]:
            tk.Label(f, text=label, font=("맑은 고딕", 11),
                     bg=C["card"], fg=C["text"]).pack(anchor="w")
            entry = tk.Entry(f, show=show, font=("맑은 고딕", 11), width=28,
                             bg=C["entry_bg"], relief="solid", bd=1)
            entry.pack(fill="x", pady=(2, 10))
            setattr(self, attr, entry)
        tk.Button(f, text="가입하기",
                  font=("맑은 고딕", 12, "bold"),
                  bg=C["confirm"], fg=C["confirm_t"],
                  relief="flat", pady=9,
                  command=self._do_register).pack(fill="x", pady=(6, 0))

    def _switch_tab(self):
        if self.tab_var.get() == "login":
            self._build_login_form()
        else:
            self._build_register_form()

    def _do_login(self):
        uid = self.login_id.get().strip()
        pw  = self.login_pw.get().strip()
        if not uid or not pw:
            messagebox.showwarning("알림", "아이디와 비밀번호를 입력하세요.")
            return
        members = _load_members()
        if uid not in members or members[uid]["password"] != pw:
            messagebox.showerror("로그인 실패", "아이디 또는 비밀번호가 틀렸습니다.")
            return
        self.app.state["member_id"] = uid
        self.app.navigate("menu")

    def _do_register(self):
        uid = self.reg_id.get().strip()
        pw  = self.reg_pw.get().strip()
        pw2 = self.reg_pw2.get().strip()
        if not uid or not pw:
            messagebox.showwarning("알림", "아이디와 비밀번호를 입력하세요.")
            return
        if pw != pw2:
            messagebox.showerror("오류", "비밀번호가 일치하지 않습니다.")
            return
        members = _load_members()
        if uid in members:
            messagebox.showerror("오류", "이미 사용 중인 아이디입니다.")
            return
        members[uid] = {"password": pw, "points": 0}
        _save_members(members)
        messagebox.showinfo("가입 완료", f"{uid}님, 가입을 환영합니다! 🎉")
        self.tab_var.set("login")
        self._build_login_form()
        self.login_id.insert(0, uid)

    def _guest_enter(self):
        self.app.state["member_id"] = None
        self.app.navigate("menu")
