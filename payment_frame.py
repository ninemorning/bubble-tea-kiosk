import json
import tkinter as tk
from tkinter import ttk, messagebox


MEMBERS_FILE = "data/members.json"

PASTEL = {
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
    "green":    "#1D9E75",
    "green_bg": "#E1F5EE",
    "row_even": "#FFFFFF",
    "row_odd":  "#FFF0F5",
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


class PaymentFrame(tk.Frame):
    """
    결제 화면 프레임

    [대외 인터페이스]
    receive_order(order: dict)
        order_frame.py 에서 주문 확인 시 호출
        order 구조:
            { items, total_price, earned_points, member_id, timestamp }

    set_member_frame(member_frame)
        main.py 에서 호출 — 포인트 적립 후 회원 화면 갱신용
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=PASTEL["bg"], **kwargs)
        self.order         = None
        self.member_frame  = None   # main.py 에서 set_member_frame()으로 연결
        self.use_points    = tk.BooleanVar(value=False)
        self.payment_method = tk.StringVar(value="카드")

        self._build_ui()

    # ── 외부 인터페이스 ──────────────────────────────────────

    def receive_order(self, order: dict):
        """order_frame.py 에서 주문 확인 시 호출"""
        self.order = order
        self.use_points.set(False)
        self._refresh_order_summary()
        self._refresh_total()

    def set_member_frame(self, member_frame):
        """main.py 에서 포인트 적립 콜백 연결용"""
        self.member_frame = member_frame

    # ── UI 빌드 ─────────────────────────────────────────────

    def _build_ui(self):
        # 헤더
        header = tk.Frame(self, bg=PASTEL["header"], pady=12)
        header.pack(fill="x")
        tk.Label(header, text="💳  결제",
                 font=("맑은 고딕", 16, "bold"),
                 bg=PASTEL["header"], fg=PASTEL["accent"]).pack()

        # 주문 내역 요약
        tk.Label(self, text="주문 내역",
                 font=("맑은 고딕", 12, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["text"]).pack(
                     padx=20, pady=(14, 4), anchor="w")

        table_wrap = tk.Frame(self, bg=PASTEL["bg"])
        table_wrap.pack(fill="x", padx=20)
        cols = ("메뉴", "수량", "금액")
        self.tree = ttk.Treeview(table_wrap, columns=cols,
                                  show="headings", height=5)
        col_widths = {"메뉴": 160, "수량": 50, "금액": 80}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=col_widths[c], anchor="center")
        self.tree.pack(fill="x")

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=10)

        # 포인트 사용
        self.points_frame = tk.Frame(self, bg=PASTEL["bg"])
        self.points_frame.pack(fill="x", padx=20, pady=(0, 8))
        self.points_check = tk.Checkbutton(
            self.points_frame,
            text="포인트 사용",
            variable=self.use_points,
            font=("맑은 고딕", 11),
            bg=PASTEL["bg"], fg=PASTEL["text"],
            selectcolor=PASTEL["btn"],
            activebackground=PASTEL["bg"],
            command=self._refresh_total,
        )
        self.points_check.pack(side="left")
        self.points_info = tk.Label(self.points_frame, text="",
                                     font=("맑은 고딕", 10),
                                     bg=PASTEL["bg"], fg=PASTEL["subtext"])
        self.points_info.pack(side="left", padx=8)

        # 결제 수단
        tk.Label(self, text="결제 수단",
                 font=("맑은 고딕", 12, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["text"]).pack(
                     padx=20, pady=(0, 6), anchor="w")
        method_frame = tk.Frame(self, bg=PASTEL["bg"])
        method_frame.pack(fill="x", padx=20, pady=(0, 10))
        for method in ["카드", "현금", "QR코드"]:
            tk.Radiobutton(
                method_frame, text=method,
                variable=self.payment_method, value=method,
                font=("맑은 고딕", 11),
                bg=PASTEL["bg"], fg=PASTEL["text"],
                selectcolor=PASTEL["btn"],
                activebackground=PASTEL["bg"],
            ).pack(side="left", padx=10)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=6)

        # 최종 금액
        self.total_label = tk.Label(self, text="합계: 0원",
                                     font=("맑은 고딕", 14, "bold"),
                                     bg=PASTEL["bg"], fg=PASTEL["accent"])
        self.total_label.pack(padx=20, pady=(0, 4), anchor="e")
        self.earn_label = tk.Label(self, text="",
                                    font=("맑은 고딕", 10),
                                    bg=PASTEL["bg"], fg=PASTEL["subtext"])
        self.earn_label.pack(padx=20, pady=(0, 10), anchor="e")

        # 결제 버튼
        tk.Button(self, text="결제 완료  ✓",
                  font=("맑은 고딕", 13, "bold"),
                  bg=PASTEL["confirm"], fg=PASTEL["confirm_t"],
                  relief="flat", pady=8,
                  command=self._do_payment).pack(
                      fill="x", padx=20, pady=(0, 10))

    # ── 화면 갱신 ────────────────────────────────────────────

    def _refresh_order_summary(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        if not self.order:
            return
        for idx, item in enumerate(self.order["items"]):
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", "end",
                             values=(item["name"],
                                     item["quantity"],
                                     f"{item['unit_price'] * item['quantity']:,}원"),
                             tags=(tag,))
        self.tree.tag_configure("even", background=PASTEL["row_even"])
        self.tree.tag_configure("odd",  background=PASTEL["row_odd"])

        # 포인트 잔액 표시
        member_id = self.order.get("member_id")
        if member_id:
            members = _load_members()
            balance = members.get(member_id, {}).get("points", 0)
            discount = self._point_discount(balance)
            self.points_info.config(
                text=f"보유 {balance:,}pt  (최대 {discount:,}원 할인 가능)"
            )
            self.points_check.config(state="normal")
        else:
            self.points_info.config(text="비회원 — 포인트 사용 불가")
            self.points_check.config(state="disabled")

    def _refresh_total(self):
        if not self.order:
            return
        total    = self.order["total_price"]
        discount = 0

        member_id = self.order.get("member_id")
        if self.use_points.get() and member_id:
            members = _load_members()
            balance = members.get(member_id, {}).get("points", 0)
            discount = self._point_discount(balance)

        final        = max(total - discount, 0)
        earned       = (final // 1000) * 10

        self.total_label.config(
            text=f"합계: {final:,}원" +
                 (f"  (-{discount:,}원)" if discount else "")
        )
        self.earn_label.config(
            text=f"결제 후 적립 예정: {earned:,}pt"
        )

    # ── 결제 처리 ────────────────────────────────────────────

    def _do_payment(self):
        if not self.order:
            messagebox.showwarning("알림", "주문 내역이 없습니다.")
            return

        total     = self.order["total_price"]
        discount  = 0
        member_id = self.order.get("member_id")

        if self.use_points.get() and member_id:
            members  = _load_members()
            balance  = members.get(member_id, {}).get("points", 0)
            discount = self._point_discount(balance)
            used_pts = discount        # 1pt = 1원
            members[member_id]["points"] -= used_pts
            _save_members(members)

        final  = max(total - discount, 0)
        earned = (final // 1000) * 10

        # 포인트 적립
        if member_id:
            members = _load_members()
            members[member_id]["points"] += earned
            _save_members(members)
            if self.member_frame:
                self.member_frame.add_points(member_id, 0)  # 화면 갱신

        self._show_receipt(final, discount, earned)

    def _show_receipt(self, final: int, discount: int, earned: int):
        """결제 완료 영수증 팝업"""
        win = tk.Toplevel(self)
        win.title("결제 완료")
        win.resizable(False, False)
        win.configure(bg=PASTEL["bg"])
        win.grab_set()

        tk.Label(win, text="✅  결제가 완료되었습니다!",
                 font=("맑은 고딕", 14, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["green"]).pack(padx=30, pady=(20, 8))

        info_frame = tk.Frame(win, bg=PASTEL["green_bg"],
                               relief="solid", bd=1)
        info_frame.pack(padx=24, pady=8, fill="x")

        rows = [
            ("결제 수단",  self.payment_method.get()),
            ("결제 금액",  f"{final:,}원"),
        ]
        if discount:
            rows.append(("포인트 할인", f"-{discount:,}원"))
        rows.append(("적립 포인트", f"+{earned:,}pt"))

        for label, value in rows:
            row = tk.Frame(info_frame, bg=PASTEL["green_bg"])
            row.pack(fill="x", padx=14, pady=3)
            tk.Label(row, text=label,
                     font=("맑은 고딕", 11),
                     bg=PASTEL["green_bg"], fg=PASTEL["subtext"],
                     width=12, anchor="w").pack(side="left")
            tk.Label(row, text=value,
                     font=("맑은 고딕", 11, "bold"),
                     bg=PASTEL["green_bg"], fg=PASTEL["text"]).pack(side="left")

        tk.Button(win, text="확인",
                  font=("맑은 고딕", 12, "bold"),
                  bg=PASTEL["confirm"], fg=PASTEL["confirm_t"],
                  relief="flat", padx=30, pady=6,
                  command=lambda: self._close_receipt(win)).pack(pady=16)

        win.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width()  - win.winfo_width())  // 2
        y = self.winfo_rooty() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

    def _close_receipt(self, win):
        win.destroy()
        self.order = None
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.total_label.config(text="합계: 0원")
        self.earn_label.config(text="")
        self.points_info.config(text="")
        self.use_points.set(False)

    # ── 헬퍼 ────────────────────────────────────────────────

    @staticmethod
    def _point_discount(balance: int) -> int:
        """포인트 전액을 원화로 환산 (1pt = 1원)"""
        return balance
