"""
버블티 키오스크 — 실행 진입점
현재: 메뉴 + 장바구니 화면만 포함 (데모용)
추후: member_frame, payment_frame 연결 예정
"""
import tkinter as tk
from menu_frame  import MenuFrame
from order_frame import OrderFrame


def main():
    root = tk.Tk()
    root.title("🧋 버블티 키오스크")
    root.geometry("1100x680")
    root.configure(bg="#FFF5F9")
    root.resizable(False, False)

    # 왼쪽: 메뉴, 오른쪽: 장바구니
    order_frame = OrderFrame(root)
    menu_frame  = MenuFrame(root, on_add_to_cart=order_frame.add_item)

    menu_frame.pack(side="left",  fill="both", expand=True)
    order_frame.pack(side="right", fill="y", padx=8, pady=8, ipadx=4)

    root.mainloop()


if __name__ == "__main__":
    main()
