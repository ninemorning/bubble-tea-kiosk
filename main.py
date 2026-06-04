import tkinter as tk
from page_welcome  import WelcomePage
from menu_frame    import MenuFrame
from order_frame   import OrderFrame
from payment_frame import PaymentFrame


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("버블티 키오스크")
        self.geometry("480x820")
        self.minsize(420, 680)
        self.configure(bg="#FFF5F9")
        self.resizable(True, True)

        self.state = {"member_id": None}
        self._cart_popup = None
        # 공유 장바구니 데이터 (list of dict) — MenuFrame·팝업 OrderFrame이 함께 씀
        self.shared_cart: list = []

        self._build_pages()
        self.navigate("welcome")

    # ── 페이지 빌드 ──────────────────────────────────────────

    def _build_pages(self):
        self.welcome_page = WelcomePage(self, self)
        self.welcome_page.place(x=0, y=0, relwidth=1, relheight=1)

        self.order_page = tk.Frame(self, bg="#FFF5F9")
        self.order_page.place(x=0, y=0, relwidth=1, relheight=1)
        self._build_order_page()

        self.payment = PaymentFrame(self, app=self)
        self.payment.place(x=0, y=0, relwidth=1, relheight=1)

    def _build_order_page(self):
        p = self.order_page

        self._member_bar = tk.Frame(p, bg="#F9C8D9", pady=6)
        self._member_bar.pack(fill="x")
        self._member_lbl = tk.Label(
            self._member_bar, text="",
            font=("맑은 고딕", 10),
            bg="#F9C8D9", fg="#7A5068")
        self._member_lbl.pack(side="right", padx=14)

        content = tk.Frame(p, bg="#FFF5F9")
        content.pack(fill="both", expand=True)

        # MenuFrame — 장바구니 팝업 열기 콜백 연결
        self.menu_frame = MenuFrame(
            content,
            on_add_to_cart=self._on_add_to_cart,
            on_open_cart=self._open_cart_popup,
            get_cart=lambda: self.shared_cart,
        )
        self.menu_frame.pack(fill="both", expand=True)

    # ── 장바구니 아이템 추가 ─────────────────────────────────

    def _on_add_to_cart(self, item: dict):
        """MenuFrame에서 '장바구니 담기' 시 호출 — shared_cart에 직접 추가"""
        # 동일 옵션이면 수량 증가
        for ci in self.shared_cart:
            if (ci["item_id"]   == item["item_id"]  and
                ci["sweetness"] == item["sweetness"] and
                ci["ice"]       == item["ice"]       and
                [t["name"] for t in ci["toppings"]] ==
                [t["name"] for t in item["toppings"]]):
                ci["quantity"] += 1
                self.menu_frame._sync_cart_bar()
                # 팝업 열려 있으면 갱신
                if self._cart_popup and self._cart_popup.winfo_exists():
                    self._cart_popup_order_frame._refresh_cart()
                return
        self.shared_cart.append(dict(item))
        self.menu_frame._sync_cart_bar()
        if self._cart_popup and self._cart_popup.winfo_exists():
            self._cart_popup_order_frame._refresh_cart()

    # ── 장바구니 팝업 ────────────────────────────────────────

    def _open_cart_popup(self):
        if self._cart_popup and self._cart_popup.winfo_exists():
            self._cart_popup.lift()
            return

        popup = tk.Toplevel(self)
        self._cart_popup = popup
        popup.title("장바구니")
        popup.configure(bg="#FFF5F9")
        popup.resizable(False, False)
        popup.grab_set()

        pw, ph = 500, 580
        self.update_idletasks()
        rx = self.winfo_rootx() + (self.winfo_width()  - pw) // 2
        ry = self.winfo_rooty() + (self.winfo_height() - ph) // 2
        popup.geometry(f"{pw}x{ph}+{rx}+{ry}")

        mid = self.state.get("member_id")

        def go_to_payment(order):
            popup.destroy()
            self._cart_popup = None
            self.payment.receive_order(order)
            self.navigate("payment")

        # 팝업 전용 OrderFrame 생성 — shared_cart를 직접 주입
        of = OrderFrame(popup, on_confirm_order=go_to_payment)
        of.cart = self.shared_cart          # 공유 데이터 참조 연결
        of.member_id = mid
        of._refresh_cart()                  # 현재 카트 표시
        of.pack(fill="both", expand=True)
        self._cart_popup_order_frame = of

        # 팝업 OrderFrame의 카트 변경 → 하단 바 뱃지 동기화
        of.on_cart_change = self.menu_frame._sync_cart_bar

        def on_close():
            popup.destroy()
            self._cart_popup = None
            self._cart_popup_order_frame = None
            self.menu_frame._sync_cart_bar()

        popup.protocol("WM_DELETE_WINDOW", on_close)

    # ── 페이지 전환 ──────────────────────────────────────────

    def navigate(self, name: str):
        pages = {
            "welcome": self.welcome_page,
            "menu":    self.order_page,
            "payment": self.payment,
        }
        for page in pages.values():
            page.lower()
        pages[name].lift()

        if name == "menu":
            self._on_enter_menu()
        elif name == "payment":
            self.payment.on_enter()
        elif name == "welcome":
            self.welcome_page.on_enter()
            self.shared_cart.clear()
            if hasattr(self, "menu_frame"):
                self.menu_frame._sync_cart_bar()

    def _on_enter_menu(self):
        mid = self.state.get("member_id")
        if mid:
            self._member_lbl.config(text=f"👤  {mid} 님  |  로그인 중")
        else:
            self._member_lbl.config(text="비회원 이용 중")


if __name__ == "__main__":
    App().mainloop()
