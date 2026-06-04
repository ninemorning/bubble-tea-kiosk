import json
import tkinter as tk
from tkinter import ttk, messagebox


MEMBERS_FILE = "data/members.json"

PASTEL = {
    "bg":       "#FFF5F9",
    "header":   "#F9C8D9",
    "btn":      "#F4A7C0",
    "btn_sel":  "#E87FAA",
    "accent":   "#D4547A",
    "text":     "#3A2030",
    "subtext":  "#7A5068",
    "confirm":  "#E87FAA",
    "confirm_t":"#FFFFFF",
    "entry_bg": "#FFFFFF",
    "card":     "#FFFFFF",
}


def _load_members() -> dict:
    try:
        with open(MEMBERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_members(members: dict):
    with open(MEMBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False, indent=2)


class MemberFrame(tk.Frame):
    """
    회원 화면 프레임 — 가입 / 로그인 / 로그아웃 / 포인트 조회

    [대외 인터페이스]
    on_login : callable(member_id: str | None)
        로그인 성공 시 member_id 전달, 로그아웃 시 None 전달
        → order_frame.set_member() 로 연결

    add_points(member_id: str, points: int)
        payment_frame.py 에서 결제 완료 후 호출 — 포인트 적립
    """

    def __init__(self, parent, on_login=None, **kwargs):
        super().__init__(parent, bg=PASTEL["bg"], **kwargs)
        self.on_login    = on_login
        self.current_id  = None   # 현재 로그인된 회원 ID

        self._build_ui()

    # ── 외부 인터페이스 ──────────────────────────────────────

    def add_points(self, member_id: str, points: int):
        """하위 호환용 — refresh_member_info() 사용 권장"""
        members = _load_members()
        if member_id in members:
            members[member_id]["points"] += points
            _save_members(members)
            if self.current_id == member_id:
                self._refresh_info()

    def refresh_member_info(self):
        """✅ payment_frame 에서 적립/차감 후 UI만 갱신 (DB 쓰기 없음)"""
        if self.current_id:
            self._refresh_info()

    # ── UI 빌드 ─────────────────────────────────────────────

    def _build_ui(self):
        # 헤더
        header = tk.Frame(self, bg=PASTEL["header"], pady=12)
        header.pack(fill="x")
        tk.Label(header, text="👤  회원 서비스",
                 font=("맑은 고딕", 16, "bold"),
                 bg=PASTEL["header"], fg=PASTEL["accent"]).pack()

        # 탭: 로그인 / 회원가입
        self.tab_var = tk.StringVar(value="login")
        tab_frame = tk.Frame(self, bg=PASTEL["bg"], pady=10)
        tab_frame.pack(fill="x", padx=24)
        for label, val in [("로그인", "login"), ("회원가입", "register")]:
            tk.Radiobutton(
                tab_frame, text=label, variable=self.tab_var, value=val,
                font=("맑은 고딕", 11),
                bg=PASTEL["bg"], fg=PASTEL["text"],
                selectcolor=PASTEL["btn_sel"],
                activebackground=PASTEL["bg"],
                command=self._switch_tab,
            ).pack(side="left", padx=8)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24)

        # 폼 영역 (로그인 / 회원가입 전환)
        self.form_frame = tk.Frame(self, bg=PASTEL["bg"])
        self.form_frame.pack(fill="both", expand=True, padx=24, pady=12)
        self._build_login_form()

        # 로그인 상태 표시 카드
        self.info_card = tk.Frame(self, bg=PASTEL["card"],
                                   relief="solid", bd=1)
        self.info_card.pack(fill="x", padx=24, pady=(0, 16))
        self.info_label = tk.Label(self.info_card, text="로그인 전입니다.",
                                    font=("맑은 고딕", 11),
                                    bg=PASTEL["card"], fg=PASTEL["subtext"],
                                    pady=10)
        self.info_label.pack()

    # ── 폼 빌드 ─────────────────────────────────────────────

    def _clear_form(self):
        for w in self.form_frame.winfo_children():
            w.destroy()

    def _build_login_form(self):
        self._clear_form()
        pad = {"pady": 6, "anchor": "w"}

        tk.Label(self.form_frame, text="아이디",
                 font=("맑은 고딕", 11),
                 bg=PASTEL["bg"], fg=PASTEL["text"]).pack(**pad)
        self.login_id = tk.Entry(self.form_frame,
                                  font=("맑은 고딕", 11),
                                  bg=PASTEL["entry_bg"], relief="solid", bd=1)
        self.login_id.pack(fill="x", pady=(0, 8))

        tk.Label(self.form_frame, text="비밀번호",
                 font=("맑은 고딕", 11),
                 bg=PASTEL["bg"], fg=PASTEL["text"]).pack(**pad)
        self.login_pw = tk.Entry(self.form_frame, show="●",
                                  font=("맑은 고딕", 11),
                                  bg=PASTEL["entry_bg"], relief="solid", bd=1)
        self.login_pw.pack(fill="x", pady=(0, 14))

        tk.Button(self.form_frame, text="로그인",
                  font=("맑은 고딕", 12, "bold"),
                  bg=PASTEL["confirm"], fg=PASTEL["confirm_t"],
                  relief="flat", pady=6,
                  command=self._do_login).pack(fill="x")

    def _build_register_form(self):
        self._clear_form()
        pad = {"pady": 4, "anchor": "w"}

        tk.Label(self.form_frame, text="아이디",
                 font=("맑은 고딕", 11),
                 bg=PASTEL["bg"], fg=PASTEL["text"]).pack(**pad)
        self.reg_id = tk.Entry(self.form_frame,
                                font=("맑은 고딕", 11),
                                bg=PASTEL["entry_bg"], relief="solid", bd=1)
        self.reg_id.pack(fill="x", pady=(0, 6))

        tk.Label(self.form_frame, text="비밀번호",
                 font=("맑은 고딕", 11),
                 bg=PASTEL["bg"], fg=PASTEL["text"]).pack(**pad)
        self.reg_pw = tk.Entry(self.form_frame, show="●",
                                font=("맑은 고딕", 11),
                                bg=PASTEL["entry_bg"], relief="solid", bd=1)
        self.reg_pw.pack(fill="x", pady=(0, 6))

        tk.Label(self.form_frame, text="비밀번호 확인",
                 font=("맑은 고딕", 11),
                 bg=PASTEL["bg"], fg=PASTEL["text"]).pack(**pad)
        self.reg_pw2 = tk.Entry(self.form_frame, show="●",
                                 font=("맑은 고딕", 11),
                                 bg=PASTEL["entry_bg"], relief="solid", bd=1)
        self.reg_pw2.pack(fill="x", pady=(0, 14))

        tk.Button(self.form_frame, text="가입하기",
                  font=("맑은 고딕", 12, "bold"),
                  bg=PASTEL["confirm"], fg=PASTEL["confirm_t"],
                  relief="flat", pady=6,
                  command=self._do_register).pack(fill="x")

    def _switch_tab(self):
        if self.tab_var.get() == "login":
            self._build_login_form()
        else:
            self._build_register_form()

    # ── 로그인 / 로그아웃 / 가입 로직 ───────────────────────

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

        self.current_id = uid
        self._refresh_info()
        if callable(self.on_login):
            self.on_login(uid)
        messagebox.showinfo("환영합니다", f"{uid}님, 어서오세요! 🧋")

    def _do_logout(self):
        self.current_id = None
        self.info_label.config(text="로그인 전입니다.")

        # 로그아웃 버튼 제거
        for w in self.info_card.winfo_children():
            if isinstance(w, tk.Button):
                w.destroy()

        if callable(self.on_login):
            self.on_login(None)

    def _do_register(self):
        uid  = self.reg_id.get().strip()
        pw   = self.reg_pw.get().strip()
        pw2  = self.reg_pw2.get().strip()

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

        # 가입 후 로그인 탭으로 전환
        self.tab_var.set("login")
        self._build_login_form()
        self.login_id.insert(0, uid)

    # ── 상태 표시 갱신 ───────────────────────────────────────

    def _refresh_info(self):
        if not self.current_id:
            return
        members = _load_members()
        points  = members.get(self.current_id, {}).get("points", 0)
        self.info_label.config(
            text=f"✅  {self.current_id}  |  보유 포인트: {points:,}pt",
            fg=PASTEL["accent"],
        )

        # 로그아웃 버튼 (없으면 추가)
        has_btn = any(isinstance(w, tk.Button)
                      for w in self.info_card.winfo_children())
        if not has_btn:
            tk.Button(self.info_card, text="로그아웃",
                      font=("맑은 고딕", 10),
                      bg=PASTEL["btn"], fg=PASTEL["text"],
                      relief="flat", padx=12, pady=4,
                      command=self._do_logout).pack(pady=(0, 8))
