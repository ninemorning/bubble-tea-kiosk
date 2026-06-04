import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

MEMBERS_FILE = "data/members.json"
ORDERS_FILE  = "data/orders.json"
POINT_RATE   = 10

# 적립품 교환 카탈로그
REWARDS = [
    {"name": "음료 50% 할인쿠폰", "points": 300, "desc": "다음 주문 시 사용 가능"},
    {"name": "버블티 키링 굿즈",   "points": 500, "desc": "매장 내 수령"},
    {"name": "무료 음료 쿠폰",     "points": 800, "desc": "당일 사용 가능"},
]

PASTEL = {
    "bg":        "#FFF5F9",
    "header":    "#F9C8D9",
    "btn":       "#F4A7C0",
    "accent":    "#D4547A",
    "text":      "#3A2030",
    "subtext":   "#7A5068",
    "confirm":   "#E87FAA",
    "confirm_t": "#FFFFFF",
    "card":      "#FFFFFF",
    "green":     "#1D9E75",
    "green_bg":  "#E1F5EE",
    "row_even":  "#FFFFFF",
    "row_odd":   "#FFF0F5",
    "reward_bg": "#FFF0F5",
}


def _load_members():
    try:
        with open(MEMBERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_members(m):
    with open(MEMBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def _load_orders():
    try:
        with open(ORDERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_orders(o):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(o, f, ensure_ascii=False, indent=2)


class PaymentFrame(tk.Frame):
    """
    결제 화면 프레임

    [대외 인터페이스]
    receive_order(order: dict)  ← order_frame.py 에서 호출
    set_member_frame(mf)        ← main.py 에서 연결 (선택)
    """

    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, bg=PASTEL["bg"], **kwargs)
        self.app            = app         # 페이지 전환용 (main.py App 인스턴스)
        self.order          = None
        self.member_frame   = None
        self.use_points     = tk.BooleanVar(value=False)
        self.payment_method = tk.StringVar(value="카드")
        self._build_ui()

    # ── 외부 인터페이스 ──────────────────────────────────────

    def receive_order(self, order: dict):
        self.order = order
        self.use_points.set(False)
        self._refresh_order_summary()
        self._refresh_points_section()
        self._refresh_total()

    def set_member_frame(self, member_frame):
        self.member_frame = member_frame

    def on_enter(self):
        """페이지 진입 시 호출 (main.py navigate)"""
        if self.order:
            self._refresh_points_section()
            self._refresh_total()

    # ── UI 빌드 ─────────────────────────────────────────────

    def _build_ui(self):
        # 헤더
        hdr = tk.Frame(self, bg=PASTEL["header"], pady=12)
        hdr.pack(fill="x")
        tk.Button(hdr, text="←  메뉴로",
                  font=("맑은 고딕", 11),
                  bg=PASTEL["header"], fg=PASTEL["subtext"],
                  relief="flat",
                  command=self._go_back).pack(side="left", padx=16)
        tk.Label(hdr, text="💳  결제",
                 font=("맑은 고딕", 16, "bold"),
                 bg=PASTEL["header"], fg=PASTEL["accent"]).pack(side="left")

        # 스크롤 가능한 본문
        canvas = tk.Canvas(self, bg=PASTEL["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self._body = tk.Frame(canvas, bg=PASTEL["bg"])
        self._body.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._body, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._build_body()

    def _build_body(self):
        b = self._body

        # ── 주문 내역 ─────────────────────────────────────────
        tk.Label(b, text="주문 내역",
                 font=("맑은 고딕", 13, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["accent"]).pack(
                     padx=24, pady=(18, 6), anchor="w")

        wrap = tk.Frame(b, bg=PASTEL["bg"])
        wrap.pack(fill="x", padx=24)
        cols = ("메뉴", "수량", "금액")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", height=5)
        for c, w in zip(cols, [200, 60, 90]):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="x")

        ttk.Separator(b, orient="horizontal").pack(fill="x", padx=24, pady=14)

        # ── 포인트 사용 ───────────────────────────────────────
        tk.Label(b, text="포인트 사용",
                 font=("맑은 고딕", 13, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["accent"]).pack(
                     padx=24, pady=(0, 6), anchor="w")

        pts_row = tk.Frame(b, bg=PASTEL["bg"])
        pts_row.pack(fill="x", padx=24, pady=(0, 6))
        self.points_check = tk.Checkbutton(
            pts_row, text="보유 포인트 전액 사용  (1pt = 1원 할인)",
            variable=self.use_points,
            font=("맑은 고딕", 11),
            bg=PASTEL["bg"], fg=PASTEL["text"],
            selectcolor=PASTEL["btn"],
            activebackground=PASTEL["bg"],
            command=self._refresh_total,
        )
        self.points_check.pack(side="left")
        self.points_info = tk.Label(pts_row, text="",
                                     font=("맑은 고딕", 10),
                                     bg=PASTEL["bg"], fg=PASTEL["subtext"])
        self.points_info.pack(side="left", padx=10)

        ttk.Separator(b, orient="horizontal").pack(fill="x", padx=24, pady=14)

        # ── 적립품 교환 ───────────────────────────────────────
        tk.Label(b, text="🎁  적립품 교환",
                 font=("맑은 고딕", 13, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["accent"]).pack(
                     padx=24, pady=(0, 8), anchor="w")
        self.rewards_frame = tk.Frame(b, bg=PASTEL["bg"])
        self.rewards_frame.pack(fill="x", padx=24, pady=(0, 4))

        ttk.Separator(b, orient="horizontal").pack(fill="x", padx=24, pady=14)

        # ── 결제 수단 ─────────────────────────────────────────
        tk.Label(b, text="결제 수단",
                 font=("맑은 고딕", 13, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["accent"]).pack(
                     padx=24, pady=(0, 8), anchor="w")
        method_row = tk.Frame(b, bg=PASTEL["bg"])
        method_row.pack(padx=24, pady=(0, 6), anchor="w")
        for method in ["카드", "현금", "QR코드"]:
            tk.Radiobutton(method_row, text=method,
                           variable=self.payment_method, value=method,
                           font=("맑은 고딕", 12),
                           bg=PASTEL["bg"], fg=PASTEL["text"],
                           selectcolor=PASTEL["btn"],
                           activebackground=PASTEL["bg"]).pack(
                               side="left", padx=12)

        ttk.Separator(b, orient="horizontal").pack(fill="x", padx=24, pady=14)

        # ── 합계 & 결제 버튼 ──────────────────────────────────
        self.total_label = tk.Label(b, text="합계: 0원",
                                     font=("맑은 고딕", 15, "bold"),
                                     bg=PASTEL["bg"], fg=PASTEL["accent"])
        self.total_label.pack(padx=24, pady=(0, 4), anchor="e")
        self.earn_label = tk.Label(b, text="",
                                    font=("맑은 고딕", 10),
                                    bg=PASTEL["bg"], fg=PASTEL["subtext"])
        self.earn_label.pack(padx=24, pady=(0, 12), anchor="e")

        tk.Button(b, text="결제 완료  ✓",
                  font=("맑은 고딕", 14, "bold"),
                  bg=PASTEL["confirm"], fg=PASTEL["confirm_t"],
                  relief="flat", pady=10,
                  command=self._do_payment).pack(
                      fill="x", padx=24, pady=(0, 24))

    # ── 갱신 ────────────────────────────────────────────────

    def _refresh_order_summary(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        if not self.order:
            return
        for idx, item in enumerate(self.order["items"]):
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", "end", tags=(tag,),
                values=(item["name"], item["quantity"],
                        f"{item['unit_price'] * item['quantity']:,}원"))
        self.tree.tag_configure("even", background=PASTEL["row_even"])
        self.tree.tag_configure("odd",  background=PASTEL["row_odd"])

    def _refresh_points_section(self):
        mid = self.order.get("member_id") if self.order else None
        if mid:
            members = _load_members()
            balance = members.get(mid, {}).get("points", 0)
            self.points_info.config(text=f"보유: {balance:,}pt")
            self.points_check.config(state="normal" if balance > 0 else "disabled")
        else:
            self.points_info.config(text="비회원 — 포인트 사용 불가")
            self.points_check.config(state="disabled")
        self._refresh_rewards()

    def _refresh_rewards(self):
        for w in self.rewards_frame.winfo_children():
            w.destroy()

        mid = self.order.get("member_id") if self.order else None
        if not mid:
            tk.Label(self.rewards_frame,
                     text="로그인 후 이용 가능합니다.",
                     font=("맑은 고딕", 10),
                     bg=PASTEL["bg"], fg=PASTEL["subtext"]).pack(anchor="w")
            return

        members = _load_members()
        balance = members.get(mid, {}).get("points", 0)

        for reward in REWARDS:
            row = tk.Frame(self.rewards_frame, bg=PASTEL["reward_bg"],
                            relief="solid", bd=1, padx=12, pady=8)
            row.pack(fill="x", pady=3)

            info = tk.Frame(row, bg=PASTEL["reward_bg"])
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=f"🎀  {reward['name']}",
                     font=("맑은 고딕", 11, "bold"),
                     bg=PASTEL["reward_bg"], fg=PASTEL["text"]).pack(anchor="w")
            tk.Label(info, text=f"{reward['points']:,}pt  |  {reward['desc']}",
                     font=("맑은 고딕", 10),
                     bg=PASTEL["reward_bg"], fg=PASTEL["subtext"]).pack(anchor="w")

            can = balance >= reward["points"]
            tk.Button(row, text="교환",
                      font=("맑은 고딕", 10, "bold"),
                      bg=PASTEL["confirm"] if can else PASTEL["btn"],
                      fg=PASTEL["confirm_t"] if can else PASTEL["subtext"],
                      relief="flat", padx=12, pady=4,
                      state="normal" if can else "disabled",
                      command=lambda r=reward: self._redeem(r)).pack(side="right")

    def _refresh_total(self):
        if not self.order:
            return
        total    = self.order["total_price"]
        discount = 0
        mid      = self.order.get("member_id")

        if self.use_points.get() and mid:
            members  = _load_members()
            balance  = members.get(mid, {}).get("points", 0)
            # ✅ 버그 수정: 포인트가 총 금액보다 많아도 최대 total까지만 할인
            discount = min(balance, total)

        final  = max(total - discount, 0)
        earned = (final // 1000) * POINT_RATE

        disc_str = f"  (-{discount:,}원)" if discount else ""
        self.total_label.config(text=f"합계: {final:,}원{disc_str}")
        self.earn_label.config(text=f"결제 후 적립: +{earned:,}pt")

    # ── 적립품 교환 ──────────────────────────────────────────

    def _redeem(self, reward):
        mid     = self.order.get("member_id") if self.order else None
        if not mid:
            return
        members = _load_members()
        balance = members.get(mid, {}).get("points", 0)

        if balance < reward["points"]:
            messagebox.showwarning("포인트 부족", "포인트가 부족합니다.")
            return
        if not messagebox.askyesno("교환 확인",
                f"'{reward['name']}' 으로 교환하시겠습니까?\n"
                f"차감 포인트: {reward['points']:,}pt"):
            return

        members[mid]["points"] -= reward["points"]
        _save_members(members)
        new_bal = members[mid]["points"]
        messagebox.showinfo("교환 완료",
                f"✅  교환 완료!\n남은 포인트: {new_bal:,}pt")
        self._refresh_points_section()
        self._refresh_total()

    # ── 결제 처리 ────────────────────────────────────────────

    def _do_payment(self):
        if not self.order:
            messagebox.showwarning("알림", "주문 내역이 없습니다.")
            return

        total    = self.order["total_price"]
        discount = 0
        mid      = self.order.get("member_id")

        if self.use_points.get() and mid:
            members  = _load_members()
            balance  = members.get(mid, {}).get("points", 0)
            discount = min(balance, total)  # ✅ 버그 수정
            members[mid]["points"] -= discount
            _save_members(members)

        final  = max(total - discount, 0)
        earned = (final // 1000) * POINT_RATE

        if mid:
            members = _load_members()
            members[mid]["points"] += earned
            _save_members(members)
            if self.member_frame:
                self.member_frame.add_points(mid, 0)

        # ✅ 결제 완료 후 orders.json 저장
        orders = _load_orders()
        orders.append({
            "items":         self.order["items"],
            "total_price":   total,
            "discount":      discount,
            "final_price":   final,
            "earned_points": earned,
            "member_id":     mid,
            "payment":       self.payment_method.get(),
            "timestamp":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        _save_orders(orders)

        self._show_receipt(final, discount, earned)

    def _show_receipt(self, final, discount, earned):
        mid = self.order.get("member_id") if self.order else None
        win = tk.Toplevel(self)
        win.title("결제 완료")
        win.resizable(False, False)
        win.configure(bg=PASTEL["bg"])
        win.grab_set()

        tk.Label(win, text="✅  결제가 완료되었습니다!",
                 font=("맑은 고딕", 15, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["green"]).pack(padx=40, pady=(24, 10))

        info = tk.Frame(win, bg=PASTEL["green_bg"], relief="solid", bd=1)
        info.pack(padx=30, pady=6, fill="x")

        rows = [("결제 수단", self.payment_method.get()),
                ("결제 금액", f"{final:,}원")]
        if discount:
            rows.append(("포인트 할인", f"-{discount:,}원"))
        if mid:
            members = _load_members()
            new_bal = members.get(mid, {}).get("points", 0)
            rows.append(("적립 포인트", f"+{earned:,}pt"))
            rows.append(("보유 포인트", f"{new_bal:,}pt  🎉"))

        for label, value in rows:
            r = tk.Frame(info, bg=PASTEL["green_bg"])
            r.pack(fill="x", padx=16, pady=5)
            tk.Label(r, text=label, font=("맑은 고딕", 11),
                     bg=PASTEL["green_bg"], fg=PASTEL["subtext"],
                     width=12, anchor="w").pack(side="left")
            tk.Label(r, text=value, font=("맑은 고딕", 11, "bold"),
                     bg=PASTEL["green_bg"], fg=PASTEL["text"]).pack(side="left")

        tk.Button(win, text="처음으로  🏠",
                  font=("맑은 고딕", 12, "bold"),
                  bg=PASTEL["confirm"], fg=PASTEL["confirm_t"],
                  relief="flat", padx=30, pady=8,
                  command=lambda: self._finish(win)).pack(pady=20)

        win.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width()  - win.winfo_width())  // 2
        y = self.winfo_rooty() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

    def _finish(self, win):
        win.destroy()
        self.order = None
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.total_label.config(text="합계: 0원")
        self.earn_label.config(text="")
        self.points_info.config(text="")
        self.use_points.set(False)
        if self.app:
            # 공유 카트 초기화
            if hasattr(self.app, "shared_cart"):
                self.app.shared_cart.clear()
            self.app.state["member_id"] = None
            self.app.navigate("welcome")

    def _go_back(self):
        if self.app:
            self.app.navigate("menu")
