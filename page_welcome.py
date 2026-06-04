"""
page_welcome.py

두 단계 구조:
  SplashPage  — 브랜드 이미지 전체 화면, 어디든 클릭하면 로그인 화면으로 전환
  WelcomePage — 로그인 / 회원가입 / 비회원 입장 (기존 로직 유지)
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


MEMBERS_FILE  = "data/members.json"
SPLASH_IMAGE  = "data/images/splash.png"   # ← 이미지 파일을 이 경로에 두세요

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
    "splash_bg":"#FDE8EF",   # 이미지 로드 실패 시 폴백 배경
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


# ══════════════════════════════════════════════════════════════
#  스플래시 페이지 — 브랜드 이미지, 클릭하면 로그인 페이지로
# ══════════════════════════════════════════════════════════════

class SplashPage(tk.Frame):
    """
    전체 화면 브랜드 이미지.
    어디든 클릭하면 on_click() 콜백 호출 (→ 로그인 화면으로 전환).
    """

    def __init__(self, parent, on_click, **kwargs):
        super().__init__(parent, bg=C["splash_bg"], **kwargs)
        self.on_click   = on_click
        self._photo_ref = None

        self._build_ui()
        # 창 크기가 바뀔 때 이미지 리사이즈
        self.bind("<Configure>", self._on_resize)
        # 어디든 클릭 → 로그인
        self.bind("<Button-1>", lambda e: self.on_click())

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self):
        self.canvas = tk.Canvas(self, highlightthickness=0,
                                bg=C["splash_bg"])
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", lambda e: self.on_click())

        # 이미지가 없을 때 폴백 텍스트
        self._fallback_frame = tk.Frame(self, bg=C["splash_bg"])
        tk.Label(self._fallback_frame, text="🧋",
                 font=("맑은 고딕", 72),
                 bg=C["splash_bg"]).pack(pady=(60, 0))
        tk.Label(self._fallback_frame, text="한 잔의 좋은 차, 좋은 마음",
                 font=("맑은 고딕", 26, "bold"),
                 bg=C["splash_bg"], fg=C["accent"]).pack(pady=(12, 4))
        tk.Label(self._fallback_frame, text="신선한 재료로 만든 건강한 맛",
                 font=("맑은 고딕", 13),
                 bg=C["splash_bg"], fg=C["subtext"]).pack()



    def _load_image(self, w, h):
        """창 크기에 맞춰 이미지를 로드/리사이즈"""
        if not PIL_AVAILABLE or w < 10 or h < 10:
            return False

        # 여러 경로 시도
        candidates = [
            SPLASH_IMAGE,
            "data/images/splash.jpg",
            "data/images/splash.jpeg",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    img = Image.open(path).convert("RGB")
                    # 창 비율에 맞게 cover 방식으로 리사이즈
                    img_w, img_h = img.size
                    scale = max(w / img_w, h / img_h)
                    new_w = int(img_w * scale)
                    new_h = int(img_h * scale)
                    img = img.resize((new_w, new_h), Image.LANCZOS)
                    # 중앙 crop
                    left = (new_w - w) // 2
                    top  = (new_h - h) // 2
                    img  = img.crop((left, top, left + w, top + h))
                    self._photo_ref = ImageTk.PhotoImage(img)
                    return True
                except Exception:
                    pass
        return False

    def _on_resize(self, event):
        w, h = event.width, event.height
        self.canvas.delete("all")

        if self._load_image(w, h):
            self._fallback_frame.place_forget()
            self.canvas.create_image(0, 0, anchor="nw",
                                     image=self._photo_ref)
            # 터치 안내 오버레이 (이미지 위)

        else:
            # 이미지 없으면 폴백 텍스트 레이아웃
            self.canvas.place_forget()
            self._fallback_frame.place(x=0, y=0, relwidth=1, relheight=1)
            self._fallback_frame.bind("<Button-1>", lambda e: self.on_click())


# ══════════════════════════════════════════════════════════════
#  로그인 / 회원가입 / 비회원 페이지 (기존 WelcomePage 구조 유지)
# ══════════════════════════════════════════════════════════════

class WelcomePage(tk.Frame):
    """
    app.navigate("welcome") 시 표시.
    내부적으로 SplashPage ↔ LoginPage 두 레이어를 겹쳐서 전환.
    """

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=C["bg"], **kwargs)
        self.app = app

        # 스플래시
        self.splash = SplashPage(self, on_click=self._show_login)
        self.splash.place(x=0, y=0, relwidth=1, relheight=1)

        # 로그인 레이어 (처음엔 숨김)
        self.login_layer = tk.Frame(self, bg=C["bg"])
        self.login_layer.place(x=0, y=0, relwidth=1, relheight=1)
        self._build_login_layer()
        self.login_layer.lower()   # 처음엔 스플래시가 위

    def on_enter(self):
        """결제 완료 후 welcome 으로 돌아올 때 스플래시부터 다시 시작"""
        self._show_splash()
        if hasattr(self, "login_id"):
            self.login_id.delete(0, "end")
        if hasattr(self, "login_pw"):
            self.login_pw.delete(0, "end")

    def _show_splash(self):
        self.splash.lift()

    def _show_login(self):
        self.login_layer.lift()
        if hasattr(self, "login_id"):
            self.login_id.focus_set()

    # ── 로그인 레이어 빌드 ────────────────────────────────────

    def _build_login_layer(self):
        lay = self.login_layer

        # 상단 미니 배너
        banner = tk.Frame(lay, bg=C["header"])
        banner.pack(fill="x", ipady=20)
        tk.Label(banner, text="🧋  버블티 키오스크",
                 font=("맑은 고딕", 20, "bold"),
                 bg=C["header"], fg=C["accent"]).pack()
        tk.Label(banner, text="나만의 버블티를 만들어보세요 ✨",
                 font=("맑은 고딕", 10),
                 bg=C["header"], fg=C["subtext"]).pack(pady=(2, 0))

        # 카드
        outer = tk.Frame(lay, bg=C["bg"])
        outer.pack(expand=True)

        card = tk.Frame(outer, bg=C["card"], relief="solid", bd=1,
                        padx=48, pady=30)
        card.pack(padx=60, pady=20)

        # 탭
        self.tab_var = tk.StringVar(value="login")
        tab_row = tk.Frame(card, bg=C["card"])
        tab_row.pack(fill="x", pady=(0, 14))
        for label, val in [("로그인", "login"), ("회원가입", "register")]:
            tk.Radiobutton(tab_row, text=label,
                           variable=self.tab_var, value=val,
                           font=("맑은 고딕", 13),
                           bg=C["card"], fg=C["text"],
                           selectcolor=C["btn"],
                           activebackground=C["card"],
                           command=self._switch_tab).pack(side="left", padx=12)

        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=(0, 16))

        self.form_frame = tk.Frame(card, bg=C["card"])
        self.form_frame.pack(fill="x")
        self._build_login_form()

        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=18)
        tk.Label(card, text="또는", font=("맑은 고딕", 10),
                 bg=C["card"], fg=C["subtext"]).pack()
        tk.Button(card, text="비회원으로 입장하기",
                  font=("맑은 고딕", 11),
                  bg=C["btn"], fg=C["text"],
                  relief="flat", padx=22, pady=7,
                  command=self._guest_enter).pack(pady=(10, 0))

        # 뒤로가기 (스플래시로)
        tk.Button(lay, text="← 처음으로",
                  font=("맑은 고딕", 9),
                  bg=C["bg"], fg=C["subtext"],
                  relief="flat",
                  command=self._show_splash).pack(pady=(0, 8))

    # ── 폼 ───────────────────────────────────────────────────

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
        self.login_id.pack(fill="x", ipady=3, pady=(2, 10))
        tk.Label(f, text="비밀번호", font=("맑은 고딕", 11),
                 bg=C["card"], fg=C["text"]).pack(anchor="w")
        self.login_pw = tk.Entry(f, show="●", font=("맑은 고딕", 11), width=28,
                                  bg=C["entry_bg"], relief="solid", bd=1)
        self.login_pw.pack(fill="x", ipady=3, pady=(2, 18))
        self.login_pw.bind("<Return>", lambda e: self._do_login())
        tk.Button(f, text="로그인하기",
                  font=("맑은 고딕", 12, "bold"),
                  bg=C["confirm"], fg=C["confirm_t"],
                  relief="flat", pady=9,
                  command=self._do_login).pack(fill="x")

    def _build_register_form(self):
        self._clear_form()
        f = self.form_frame
        for label, attr, show in [("아이디",     "reg_id",  ""),
                                   ("비밀번호",   "reg_pw",  "●"),
                                   ("비밀번호 확인", "reg_pw2", "●")]:
            tk.Label(f, text=label, font=("맑은 고딕", 11),
                     bg=C["card"], fg=C["text"]).pack(anchor="w")
            e = tk.Entry(f, show=show, font=("맑은 고딕", 11), width=28,
                         bg=C["entry_bg"], relief="solid", bd=1)
            e.pack(fill="x", ipady=3, pady=(2, 10))
            setattr(self, attr, e)
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

    # ── 로직 ─────────────────────────────────────────────────

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
