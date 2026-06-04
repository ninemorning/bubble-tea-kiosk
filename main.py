import tkinter as tk
from menu_frame    import MenuFrame
from order_frame   import OrderFrame
from member_frame  import MemberFrame
from payment_frame import PaymentFrame


def main():
    root = tk.Tk()
    root.title("버블티 키오스크")
    root.geometry("1700x720")
    root.minsize(1500, 720)
    root.configure(bg="#FFF5F9")
    root.resizable(True, True)

    # PaymentFrame 은 이제 팝업 관리 객체 (Frame 위젯 아님)
    payment = PaymentFrame()

    order_frame  = OrderFrame(root, on_confirm_order=payment.receive_order)
    member_frame = MemberFrame(root, on_login=order_frame.set_member)
    menu_frame   = MenuFrame(root,  on_add_to_cart=order_frame.add_item)

    # 연결
    payment.set_member_frame(member_frame)
    payment.set_order_frame(order_frame)   # ✅ 결제 후 장바구니 초기화용

    # 레이아웃: 왼쪽 메뉴 | 가운데 장바구니 | 오른쪽 회원
    menu_frame.pack(  side="left", fill="both", expand=True)
    order_frame.pack( side="left", fill="y",    padx=4, pady=8, ipadx=4)
    member_frame.pack(side="left", fill="y",    padx=4, pady=8, ipadx=4)
    # payment_frame 은 pack 하지 않음 — 팝업으로 동작

    root.mainloop()


if __name__ == "__main__":
    main()
