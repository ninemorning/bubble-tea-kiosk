import tkinter as tk
from menu_frame    import MenuFrame
from order_frame   import OrderFrame
from member_frame  import MemberFrame
from payment_frame import PaymentFrame


def main():
    root = tk.Tk()
    root.title("🧋 버블티 키오스크")
    root.geometry("1200x720")
    root.configure(bg="#FFF5F9")
    root.resizable(False, False)

    # 모듈 초기화 (의존 순서대로)
    payment_frame = PaymentFrame(root)
    order_frame   = OrderFrame(root,  on_confirm_order=payment_frame.receive_order)
    member_frame  = MemberFrame(root, on_login=order_frame.set_member)
    menu_frame    = MenuFrame(root,   on_add_to_cart=order_frame.add_item)

    # payment ↔ member 포인트 적립 연결
    payment_frame.set_member_frame(member_frame)

    # 레이아웃: 왼쪽 메뉴 | 가운데 장바구니 | 오른쪽 회원+결제
    menu_frame.pack(   side="left",  fill="both", expand=True)
    order_frame.pack(  side="left",  fill="y",    padx=4, pady=8, ipadx=4)
    member_frame.pack( side="left",  fill="y",    padx=4, pady=8, ipadx=4)
    payment_frame.pack(side="left",  fill="y",    padx=4, pady=8, ipadx=4)

    root.mainloop()


if __name__ == "__main__":
    main()
