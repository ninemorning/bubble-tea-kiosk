import json
import tkinter as tk
from tkinter import ttk, messagebox

from order_frame import save_order_to_file   # 결제 완료 후 저장


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


class PaymentFrame:
    """
    결제 팝업 (Toplevel)

    [변경사항]
    - tk.Frame 상속 제거 → 호출 시마다 Toplevel 팝업으로 생성
    - order_frame 참조를 받아 결제 완료 후 장바구니 직접 초기화
    - save_order_to_file() 을 결제 완료 시점으로 이동
    - 포인트 차감 시 음수 방지 (used_pts = min(discount, total))
    - member_frame.refresh_member_info() 로 UI 갱신 (의미 명확화)

    [대외 인터페이스]
    receive_order(order: dict)
        order_frame.py 에서 주문 확인 시 호출 → 팝업 열림

    set_member_frame(member_frame)
        main.py 에서 호출 — 포인트 적립 후 회원 화면 갱신용

    set_order_frame(order_frame)
        main.py 에서 호출 — 결제 완료 후 장바구니 초기화용
    """

    def __init__(self):
        self.member_frame = None
        self.order_frame  = None

    # ── 외부 인터페이스 ──────────────────────────────────────

    def receive_order(self, order: dict):
        """order_frame.py 에서 주문 확인 시 호출 → 결제 팝업 오픈"""
        self._open_popup(order)

    def set_member_frame(self, member_frame):
        self.member_frame = member_frame

    def set_order_frame(self, order_frame):
        self.order_frame = order_frame

    # ── 팝업 오픈 ────────────────────────────────────────────

    def _open_popup(self, order: dict):
        popup = tk.Toplevel()
        popup.title("💳  결제")
        popup.resizable(False, False)
        popup.configure(bg=PASTEL["bg"])
        popup.grab_set()

        use_points     = tk.BooleanVar(value=False)
        payment_method = tk.StringVar(value="카드")

        # ── 헤더 ─────────────────────────────────────────────
        header = tk.Frame(popup, bg=PASTEL["header"], pady=12)
        header.pack(fill="x")
        tk.Label(header, text="💳  결제",
                 font=("맑은 고딕", 16, "bold"),
                 bg=PASTEL["header"], fg=PASTEL["accent"]).pack()

        # ── 주문 내역 요약 ────────────────────────────────────
        tk.Label(popup, text="주문 내역",
                 font=("맑은 고딕", 12, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["text"]).pack(
                     padx=20, pady=(14, 4), anchor="w")

        table_wrap = tk.Frame(popup, bg=PASTEL["bg"])
        table_wrap.pack(fill="x", padx=20)
        cols = ("메뉴", "수량", "금액")
        tree = ttk.Treeview(table_wrap, columns=cols,
                             show="headings", height=min(len(order["items"]), 6))
        col_widths = {"메뉴": 180, "수량": 50, "금액": 90}
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=col_widths[c], anchor="center")
        tree.pack(fill="x")

        for idx, item in enumerate(order["items"]):
            tag = "even" if idx % 2 == 0 else "odd"
            tree.insert("", "end",
                        values=(item["name"], item["quantity"],
                                f"{item['unit_price'] * item['quantity']:,}원"),
                        tags=(tag,))
        tree.tag_configure("even", background=PASTEL["row_even"])
        tree.tag_configure("odd",  background=PASTEL["row_odd"])

        ttk.Separator(popup, orient="horizontal").pack(fill="x", padx=20, pady=10)

        # ── 포인트 사용 ───────────────────────────────────────
        member_id = order.get("member_id")
        pts_frame = tk.Frame(popup, bg=PASTEL["bg"])
        pts_frame.pack(fill="x", padx=20, pady=(0, 8))

        pts_check = tk.Checkbutton(
            pts_frame, text="포인트 사용",
            variable=use_points,
            font=("맑은 고딕", 11),
            bg=PASTEL["bg"], fg=PASTEL["text"],
            selectcolor=PASTEL["btn"],
            activebackground=PASTEL["bg"],
        )
        pts_check.pack(side="left")
        pts_info = tk.Label(pts_frame, text="",
                            font=("맑은 고딕", 10),
                            bg=PASTEL["bg"], fg=PASTEL["subtext"])
        pts_info.pack(side="left", padx=8)

        if member_id:
            members = _load_members()
            balance = members.get(member_id, {}).get("points", 0)
            pts_info.config(text=f"보유 {balance:,}pt  (최대 {balance:,}원 할인)")
            pts_check.config(state="normal")
        else:
            pts_info.config(text="비회원 — 포인트 사용 불가")
            pts_check.config(state="disabled")

        # ── 결제 수단 ─────────────────────────────────────────
        tk.Label(popup, text="결제 수단",
                 font=("맑은 고딕", 12, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["text"]).pack(
                     padx=20, pady=(0, 6), anchor="w")
        method_frame = tk.Frame(popup, bg=PASTEL["bg"])
        method_frame.pack(fill="x", padx=20, pady=(0, 10))
        for method in ["카드", "현금", "QR코드"]:
            tk.Radiobutton(
                method_frame, text=method,
                variable=payment_method, value=method,
                font=("맑은 고딕", 11),
                bg=PASTEL["bg"], fg=PASTEL["text"],
                selectcolor=PASTEL["btn"],
                activebackground=PASTEL["bg"],
            ).pack(side="left", padx=10)

        ttk.Separator(popup, orient="horizontal").pack(fill="x", padx=20, pady=6)

        # ── 최종 금액 표시 ────────────────────────────────────
        total_label = tk.Label(popup, text="",
                               font=("맑은 고딕", 14, "bold"),
                               bg=PASTEL["bg"], fg=PASTEL["accent"])
        total_label.pack(padx=20, pady=(0, 2), anchor="e")
        earn_label = tk.Label(popup, text="",
                              font=("맑은 고딕", 10),
                              bg=PASTEL["bg"], fg=PASTEL["subtext"])
        earn_label.pack(padx=20, pady=(0, 10), anchor="e")

        def refresh_total(*_):
            total    = order["total_price"]
            discount = 0
            if use_points.get() and member_id:
                members = _load_members()
                balance = members.get(member_id, {}).get("points", 0)
                # ✅ 포인트 할인은 총액을 초과할 수 없음
                discount = min(balance, total)
            final  = max(total - discount, 0)
            earned = (final // 1000) * 10
            total_label.config(
                text=f"합계: {final:,}원" + (f"  (-{discount:,}원)" if discount else "")
            )
            earn_label.config(text=f"결제 후 적립 예정: {earned:,}pt")

        use_points.trace_add("write", refresh_total)
        refresh_total()

        # ── 결제 완료 버튼 ────────────────────────────────────
        def do_payment():
            total     = order["total_price"]
            discount  = 0

            if use_points.get() and member_id:
                members  = _load_members()
                balance  = members.get(member_id, {}).get("points", 0)
                # ✅ 음수 방지: 할인은 실제 잔액과 총액 중 작은 값
                discount  = min(balance, total)
                used_pts  = discount
                members[member_id]["points"] -= used_pts
                _save_members(members)

            final  = max(total - discount, 0)
            earned = (final // 1000) * 10

            # ✅ 포인트 적립
            if member_id:
                members = _load_members()
                members[member_id]["points"] += earned
                _save_members(members)
                # ✅ UI 갱신 — 의미 명확한 메서드명 사용
                if self.member_frame and hasattr(self.member_frame, "refresh_member_info"):
                    self.member_frame.refresh_member_info()

            # ✅ 실제 결제 완료 후에만 파일 저장
            save_order_to_file(order)

            # ✅ 결제 완료 후 장바구니 초기화
            if self.order_frame:
                self.order_frame.clear_cart()

            popup.destroy()
            self._show_receipt(payment_method.get(), final, discount, earned)

        tk.Button(popup, text="결제 완료  ✓",
                  font=("맑은 고딕", 13, "bold"),
                  bg=PASTEL["confirm"], fg=PASTEL["confirm_t"],
                  relief="flat", pady=8,
                  command=do_payment).pack(fill="x", padx=20, pady=(0, 16))

        # 팝업 중앙 정렬
        popup.update_idletasks()
        sw = popup.winfo_screenwidth()
        sh = popup.winfo_screenheight()
        pw = popup.winfo_width()
        ph = popup.winfo_height()
        popup.geometry(f"+{(sw - pw) // 2}+{(sh - ph) // 2}")

    # ── 영수증 팝업 ───────────────────────────────────────────

    def _show_receipt(self, method: str, final: int, discount: int, earned: int):
        win = tk.Toplevel()
        win.title("결제 완료")
        win.resizable(False, False)
        win.configure(bg=PASTEL["bg"])
        win.grab_set()

        tk.Label(win, text="✅  결제가 완료되었습니다!",
                 font=("맑은 고딕", 14, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["green"]).pack(padx=30, pady=(20, 8))

        info_frame = tk.Frame(win, bg=PASTEL["green_bg"], relief="solid", bd=1)
        info_frame.pack(padx=24, pady=8, fill="x")

        rows = [("결제 수단", method), ("결제 금액", f"{final:,}원")]
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
                  command=win.destroy).pack(pady=16)

        win.update_idletasks()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry(f"+{(sw - win.winfo_width()) // 2}+{(sh - win.winfo_height()) // 2}")
