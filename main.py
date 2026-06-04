import tkinter as tk
from page_welcome  import WelcomePage
from menu_frame    import MenuFrame
from order_frame   import OrderFrame
from payment_frame import PaymentFrame


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("버블티 키오스크")
        self.geometry("1400x760")
        self.minsize(1200, 700)
        self.configure(bg="#FFF5F9")
        self.resizable(True, True)

        self.state = {"member_id": None}

        self._build_pages()
        self.navigate("welcome")

    # ── 페이지 빌드 ──────────────────────────────────────────

    def _build_pages(self):
        # ① 환영 페이지
        self.welcome_page = WelcomePage(self, self)
        self.welcome_page.place(x=0, y=0, relwidth=1, relheight=1)

        # ② 주문 페이지 (메뉴 + 장바구니)
        self.order_page = tk.Frame(self, bg="#FFF5F9")
        self.order_page.place(x=0, y=0, relwidth=1, relheight=1)
        self._build_order_page()

        # ③ 결제 페이지
        self.payment = PaymentFrame(self, app=self)
        self.payment.place(x=0, y=0, relwidth=1, relheight=1)

    def _build_order_page(self):
        p = self.order_page

        # 상단 회원 정보 바
        self._member_bar = tk.Frame(p, bg="#F9C8D9", pady=8)
        self._member_bar.pack(fill="x")

        self._member_lbl = tk.Label(
            self._member_bar, text="",
            font=("맑은 고딕", 11),
            bg="#F9C8D9", fg="#7A5068")
        self._member_lbl.pack(side="right", padx=20)

        # 결제하기 연결: order_frame 확인 → payment.receive_order → navigate
        def go_to_payment(order):
            self.payment.receive_order(order)
            self.navigate("payment")

        content = tk.Frame(p, bg="#FFF5F9")
        content.pack(fill="both", expand=True)

        self.order_frame = OrderFrame(content, on_confirm_order=go_to_payment)
        self.menu_frame  = MenuFrame(content, on_add_to_cart=self.order_frame.add_item)

        self.menu_frame.pack(side="left",  fill="both", expand=True)
        self.order_frame.pack(side="right", fill="y", padx=6, pady=8, ipadx=4)

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
            # 장바구니 초기화
            self.order_frame.cart.clear()
            self.order_frame._refresh_cart()

    def _on_enter_menu(self):
        mid = self.state.get("member_id")
        self.order_frame.set_member(mid)
        if mid:
            self._member_lbl.config(text=f"👤  {mid} 님  |  로그인 중")
        else:
            self._member_lbl.config(text="비회원 이용 중")


if __name__ == "__main__":
    App().mainloop()
