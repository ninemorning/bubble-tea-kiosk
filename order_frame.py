import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


ORDERS_FILE  = "data/orders.json"
POINT_RATE   = 10        # 포인트: 1,000원당 10포인트

PASTEL = {
    "bg":       "#FFF5F9",
    "header":   "#F9C8D9",
    "btn":      "#F4A7C0",
    "btn_sel":  "#E87FAA",
    "accent":   "#D4547A",
    "text":     "#3A2030",
    "subtext":  "#7A5068",
    "remove":   "#F2C4CE",
    "confirm":  "#E87FAA",
    "confirm_t":"#FFFFFF",
    "row_even": "#FFFFFF",
    "row_odd":  "#FFF0F5",
}


def _load_orders():
    try:
        with open(ORDERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_orders(orders):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)


def calc_points(total_price: int) -> int:
    """1,000원당 POINT_RATE 포인트 적립"""
    return (total_price // 1000) * POINT_RATE


class OrderFrame(tk.Frame):
    """
    장바구니 & 주문 확인 프레임

    [대외 인터페이스]
    add_item(order_item: dict)
        menu_frame.py 에서 호출 — 아이템을 장바구니에 추가

    on_confirm_order: callable(order: dict) | None
        payment_frame.py 가 설정 — 결제 화면으로 넘어갈 때 호출됨
        order 구조:
            {
              "items": [...],
              "total_price": int,
              "earned_points": int,
              "member_id": str | None,
              "timestamp": str
            }

    set_member(member_id: str | None)
        member_frame.py 가 로그인/로그아웃 시 호출
    """

    def __init__(self, parent, on_confirm_order=None, **kwargs):
        super().__init__(parent, bg=PASTEL["bg"], **kwargs)
        self.on_confirm_order = on_confirm_order
        self.cart: list[dict] = []
        self.member_id: str | None = None

        self._build_ui()

    # ── 외부 인터페이스 ──────────────────────────────────────

    def add_item(self, order_item: dict):
        """
        menu_frame.py → 여기로 아이템 전달
        동일 상품+옵션이면 수량 증가, 아니면 새 행 추가
        """
        for cart_item in self.cart:
            if self._same_option(cart_item, order_item):
                cart_item["quantity"] += 1
                self._refresh_cart()
                return
        self.cart.append(dict(order_item))
        self._refresh_cart()

    def set_member(self, member_id: str | None):
        """member_frame.py 에서 로그인/로그아웃 시 호출"""
        self.member_id = member_id
        self._refresh_summary()

    # ── UI 빌드 ─────────────────────────────────────────────

    def _build_ui(self):
        tk.Label(self, text="장바구니",
                 font=("맑은 고딕", 15, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["accent"]).pack(
                     pady=(12, 4), padx=16, anchor="w")

        # 장바구니 테이블
        table_frame = tk.Frame(self, bg=PASTEL["bg"])
        table_frame.pack(fill="both", expand=True, padx=16)

        cols = ("메뉴", "옵션", "수량", "금액", "")
        self.tree = ttk.Treeview(table_frame, columns=cols,
                                  show="headings", height=10)
        col_widths = {"메뉴": 110, "옵션": 130, "수량": 50, "금액": 70, "": 50}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=col_widths[c], anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)
        ttk.Scrollbar(table_frame, orient="vertical",
                      command=self.tree.yview).pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=lambda *a: None)

        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)

        # 수량 조절 버튼 줄
        qty_frame = tk.Frame(self, bg=PASTEL["bg"])
        qty_frame.pack(fill="x", padx=16, pady=4)
        tk.Button(qty_frame, text="− 수량 감소",
                  font=("맑은 고딕", 10),
                  bg=PASTEL["btn"], fg=PASTEL["text"],
                  relief="flat", padx=10,
                  command=self._decrease_qty).pack(side="left", padx=4)
        tk.Button(qty_frame, text="+ 수량 증가",
                  font=("맑은 고딕", 10),
                  bg=PASTEL["btn"], fg=PASTEL["text"],
                  relief="flat", padx=10,
                  command=self._increase_qty).pack(side="left", padx=4)
        tk.Button(qty_frame, text="선택 삭제",
                  font=("맑은 고딕", 10),
                  bg=PASTEL["remove"], fg=PASTEL["text"],
                  relief="flat", padx=10,
                  command=self._remove_selected).pack(side="left", padx=4)
        tk.Button(qty_frame, text="전체 비우기",
                  font=("맑은 고딕", 10),
                  bg=PASTEL["remove"], fg=PASTEL["text"],
                  relief="flat", padx=10,
                  command=self._clear_cart).pack(side="right", padx=4)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16, pady=6)

        # 합계 & 적립 예정 포인트
        self.summary_label = tk.Label(self, text="",
                                       font=("맑은 고딕", 12),
                                       bg=PASTEL["bg"], fg=PASTEL["text"],
                                       justify="right")
        self.summary_label.pack(padx=16, anchor="e")

        # 주문 확인 버튼
        tk.Button(self, text="주문 확인  →",
                  font=("맑은 고딕", 13, "bold"),
                  bg=PASTEL["confirm"], fg=PASTEL["confirm_t"],
                  relief="flat", pady=8,
                  command=self._confirm_order).pack(
                      fill="x", padx=16, pady=10)

        self._refresh_cart()

    # ── 장바구니 렌더링 ──────────────────────────────────────

    def _refresh_cart(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for idx, item in enumerate(self.cart):
            topping_names = ", ".join(t["name"] for t in item["toppings"]) or "없음"
            option_str    = f"당도 {item['sweetness']}% / 얼음 {item['ice']}\n토핑: {topping_names}"
            price_str     = f"{item['unit_price'] * item['quantity']:,}원"
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", "end",
                             iid=str(idx),
                             values=(item["name"], option_str,
                                     item["quantity"], price_str, "🗑"),
                             tags=(tag,))

        self.tree.tag_configure("even", background=PASTEL["row_even"])
        self.tree.tag_configure("odd",  background=PASTEL["row_odd"])
        self._refresh_summary()

    def _refresh_summary(self):
        total   = self._total_price()
        points  = calc_points(total)
        member  = f"(회원: {self.member_id})" if self.member_id else "(비회원)"
        text    = (f"합계: {total:,}원    "
                   f"적립 예정: {points:,}pt  {member}")
        self.summary_label.config(text=text)

    # ── 이벤트 핸들러 ────────────────────────────────────────

    def _on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        col    = self.tree.identify_column(event.x)
        if region == "cell" and col == "#5":   # 삭제 아이콘 열
            self._remove_selected()

    def _selected_index(self) -> int | None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("알림", "항목을 먼저 선택하세요.")
            return None
        return int(sel[0])

    def _increase_qty(self):
        idx = self._selected_index()
        if idx is not None:
            self.cart[idx]["quantity"] += 1
            self._refresh_cart()

    def _decrease_qty(self):
        idx = self._selected_index()
        if idx is not None:
            if self.cart[idx]["quantity"] > 1:
                self.cart[idx]["quantity"] -= 1
            else:
                self.cart.pop(idx)
            self._refresh_cart()

    def _remove_selected(self):
        idx = self._selected_index()
        if idx is not None:
            self.cart.pop(idx)
            self._refresh_cart()

    def _clear_cart(self):
        if self.cart and messagebox.askyesno("확인", "장바구니를 비울까요?"):
            self.cart.clear()
            self._refresh_cart()

    def _confirm_order(self):
        if not self.cart:
            messagebox.showwarning("알림", "장바구니가 비어 있습니다.")
            return

        total  = self._total_price()
        points = calc_points(total)
        order  = {
            "items":         list(self.cart),
            "total_price":   total,
            "earned_points": points,
            "member_id":     self.member_id,
            "timestamp":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        _save_order_to_file(order)

        if callable(self.on_confirm_order):
            self.on_confirm_order(order)   # → payment_frame.py
        else:
            messagebox.showinfo(
                "주문 완료",
                f"주문이 접수되었습니다!\n"
                f"합계: {total:,}원\n"
                f"적립 포인트: {points:,}pt"
            )
            self.cart.clear()
            self._refresh_cart()

    # ── 헬퍼 ────────────────────────────────────────────────

    def _total_price(self) -> int:
        return sum(i["unit_price"] * i["quantity"] for i in self.cart)

    @staticmethod
    def _same_option(a: dict, b: dict) -> bool:
        """동일 상품 + 동일 옵션 여부 판단"""
        return (a["item_id"]  == b["item_id"]  and
                a["sweetness"] == b["sweetness"] and
                a["ice"]       == b["ice"]       and
                [t["name"] for t in a["toppings"]] ==
                [t["name"] for t in b["toppings"]])


def _save_order_to_file(order: dict):
    """주문 내역을 orders.json 에 누적 저장"""
    orders = _load_orders()
    orders.append(order)
    _save_orders(orders)
