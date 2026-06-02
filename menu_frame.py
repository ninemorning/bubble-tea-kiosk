import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


MENU_FILE   = "data/menu.json"
IMAGES_DIR  = "data/images"

PASTEL = {
    "bg":       "#FFF5F9",
    "header":   "#F9C8D9",
    "btn":      "#F4A7C0",
    "btn_sel":  "#E87FAA",
    "card":     "#FFFFFF",
    "card_sel": "#FFE4F0",
    "accent":   "#D4547A",
    "text":     "#3A2030",
    "subtext":  "#7A5068",
    "add_btn":  "#E87FAA",
    "add_txt":  "#FFFFFF",
}

# 카테고리별 이모지 (이미지 파일이 없을 때 폴백)
CATEGORY_EMOJI = {
    "밀크티": "🧋",
    "과일차": "🍓",
    "슬러시": "🧊",
}


def load_menu():
    with open(MENU_FILE, encoding="utf-8") as f:
        return json.load(f)


def _load_photo(item_id: int, max_width=160, max_height=160):
    """
    data/images/<id>.png (또는 .jpg/.jpeg/.webp) 를 로드해 PhotoImage 반환.
    원본 비율을 유지하면서 max_width × max_height 안에 맞게 축소.
    파일이 없거나 PIL이 없으면 None 반환.
    """
    if not PIL_AVAILABLE:
        return None
    for ext in ("png", "jpg", "jpeg", "webp"):
        path = os.path.join(IMAGES_DIR, f"{item_id}.{ext}")
        if os.path.exists(path):
            try:
                img = Image.open(path).convert("RGBA")
                # 원본 비율 유지: max_width/max_height 박스 안에 fit
                img.thumbnail((max_width, max_height), Image.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception:
                return None
    return None


class CustomizeDialog(tk.Toplevel):
    """
    팝업 창: 당도 / 얼음 / 토핑 선택 후 장바구니에 담기
    반환값은 self.result (dict) — order_frame.py가 읽어감
    """
    def __init__(self, parent, item, menu_data):
        super().__init__(parent)
        self.title("옵션 선택")
        self.resizable(False, False)
        self.configure(bg=PASTEL["bg"])
        self.grab_set()
        self.result = None

        options  = menu_data["options"]
        toppings = options["toppings"]

        pad = {"padx": 16, "pady": 6}

        # ── 상품 이미지 (팝업 상단) ─────────────────────────
        photo = _load_photo(item["id"], max_width=200, max_height=180)
        if photo:
            self._photo_ref = photo          # 가비지 컬렉션 방지
            tk.Label(self, image=photo, bg=PASTEL["bg"]).pack(pady=(12, 0))
        else:
            emoji = CATEGORY_EMOJI.get(item.get("category", ""), "🧋")
            tk.Label(self, text=emoji, font=("맑은 고딕", 36),
                     bg=PASTEL["bg"]).pack(pady=(12, 0))

        tk.Label(self, text=item["name"], font=("맑은 고딕", 14, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["accent"]).pack(**pad, anchor="w")
        tk.Label(self, text=f"기본가격: {item['price']:,}원",
                 font=("맑은 고딕", 11), bg=PASTEL["bg"],
                 fg=PASTEL["subtext"]).pack(padx=16, pady=(0, 8), anchor="w")

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16)

        # 당도
        tk.Label(self, text="당도 (%)", font=("맑은 고딕", 11, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["text"]).pack(**pad, anchor="w")
        self.sweetness_var = tk.IntVar(value=50)
        sw_frame = tk.Frame(self, bg=PASTEL["bg"])
        sw_frame.pack(padx=16, pady=(0, 8))
        for val in options["sweetness"]:
            tk.Radiobutton(
                sw_frame, text=f"{val}%", variable=self.sweetness_var, value=val,
                bg=PASTEL["bg"], fg=PASTEL["text"],
                selectcolor=PASTEL["btn_sel"],
                activebackground=PASTEL["bg"],
            ).pack(side="left", padx=6)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16)

        # 얼음
        tk.Label(self, text="얼음", font=("맑은 고딕", 11, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["text"]).pack(**pad, anchor="w")
        self.ice_var = tk.StringVar(value="정량")
        ice_frame = tk.Frame(self, bg=PASTEL["bg"])
        ice_frame.pack(padx=16, pady=(0, 8))
        for opt in options["ice"]:
            tk.Radiobutton(
                ice_frame, text=opt, variable=self.ice_var, value=opt,
                bg=PASTEL["bg"], fg=PASTEL["text"],
                selectcolor=PASTEL["btn_sel"],
                activebackground=PASTEL["bg"],
            ).pack(side="left", padx=6)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16)

        # 토핑
        tk.Label(self, text="토핑 추가 (복수 선택 가능)",
                 font=("맑은 고딕", 11, "bold"),
                 bg=PASTEL["bg"], fg=PASTEL["text"]).pack(**pad, anchor="w")
        self.topping_vars = []
        topping_frame = tk.Frame(self, bg=PASTEL["bg"])
        topping_frame.pack(padx=16, pady=(0, 8))
        for t in toppings:
            var = tk.BooleanVar(value=False)
            self.topping_vars.append((t, var))
            tk.Checkbutton(
                topping_frame,
                text=f"{t['name']} +{t['price']:,}원",
                variable=var,
                bg=PASTEL["bg"], fg=PASTEL["text"],
                selectcolor=PASTEL["btn_sel"],
                activebackground=PASTEL["bg"],
            ).pack(anchor="w")

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16, pady=4)

        # 합계
        self.total_label = tk.Label(self, text="", font=("맑은 고딕", 12, "bold"),
                                    bg=PASTEL["bg"], fg=PASTEL["accent"])
        self.total_label.pack(**pad, anchor="e")
        self._update_total(item)

        for t, var in self.topping_vars:
            var.trace_add("write", lambda *_: self._update_total(item))

        # 버튼
        btn_frame = tk.Frame(self, bg=PASTEL["bg"])
        btn_frame.pack(padx=16, pady=12, fill="x")
        tk.Button(btn_frame, text="취소", font=("맑은 고딕", 11),
                  bg=PASTEL["header"], fg=PASTEL["text"],
                  relief="flat", padx=20,
                  command=self.destroy).pack(side="left")
        tk.Button(btn_frame, text="장바구니 담기 🧋",
                  font=("맑은 고딕", 11, "bold"),
                  bg=PASTEL["add_btn"], fg=PASTEL["add_txt"],
                  relief="flat", padx=20,
                  command=lambda: self._add_to_cart(item)).pack(side="right")

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _update_total(self, item):
        topping_total = sum(t["price"] for t, v in self.topping_vars if v.get())
        self.total_label.config(text=f"합계: {item['price'] + topping_total:,}원")

    def _add_to_cart(self, item):
        selected_toppings = [t for t, v in self.topping_vars if v.get()]
        topping_price     = sum(t["price"] for t in selected_toppings)
        self.result = {
            "item_id":    item["id"],
            "name":       item["name"],
            "base_price": item["price"],
            "sweetness":  self.sweetness_var.get(),
            "ice":        self.ice_var.get(),
            "toppings":   selected_toppings,
            "unit_price": item["price"] + topping_price,
            "quantity":   1,
        }
        self.destroy()


class MenuFrame(tk.Frame):
    """
    메뉴 화면 프레임
    - 카테고리 탭으로 메뉴 필터
    - 각 메뉴 카드 클릭 → CustomizeDialog
    - on_add_to_cart(order_item) 콜백으로 장바구니 연결

    [대외 인터페이스]
    on_add_to_cart : callable(order_item: dict)
    """
    def __init__(self, parent, on_add_to_cart, **kwargs):
        super().__init__(parent, bg=PASTEL["bg"], **kwargs)
        self.on_add_to_cart = on_add_to_cart
        self.menu_data      = load_menu()
        self.current_cat    = tk.StringVar(value="전체")
        self._photo_refs    = []   # PhotoImage 참조 보관 (GC 방지)

        self._build_header()
        self._build_category_tabs()
        self._build_menu_grid()

    # ── UI 빌드 ──────────────────────────────────────────────

    def _build_header(self):
        header = tk.Frame(self, bg=PASTEL["header"], pady=12)
        header.pack(fill="x")
        tk.Label(header, text="🧋  버블티 키오스크",
                 font=("맑은 고딕", 18, "bold"),
                 bg=PASTEL["header"], fg=PASTEL["accent"]).pack()

    def _build_category_tabs(self):
        tab_frame = tk.Frame(self, bg=PASTEL["bg"], pady=8)
        tab_frame.pack(fill="x", padx=16)

        categories = ["전체"] + self.menu_data["categories"]
        for cat in categories:
            tk.Button(
                tab_frame, text=cat,
                font=("맑은 고딕", 11),
                bg=PASTEL["btn"], fg=PASTEL["text"],
                relief="flat", padx=14, pady=4,
                command=lambda c=cat: self._select_category(c),
            ).pack(side="left", padx=4)

        self.tab_frame = tab_frame

    def _build_menu_grid(self):
        container = tk.Frame(self, bg=PASTEL["bg"])
        container.pack(fill="both", expand=True, padx=16, pady=8)

        canvas = tk.Canvas(container, bg=PASTEL["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical",
                                  command=canvas.yview)
        self.grid_frame = tk.Frame(canvas, bg=PASTEL["bg"])

        self.grid_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._render_cards("전체")

    # ── 카드 렌더링 ───────────────────────────────────────────

    def _select_category(self, cat):
        self.current_cat.set(cat)
        self._render_cards(cat)

    def _render_cards(self, category):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        # 이전 이미지 참조 해제 후 새로 수집
        self._photo_refs.clear()

        items = self.menu_data["items"]
        if category != "전체":
            items = [i for i in items if i["category"] == category]

        COLS = 3
        for idx, item in enumerate(items):
            row, col = divmod(idx, COLS)
            card = tk.Frame(
                self.grid_frame, bg=PASTEL["card"],
                relief="solid", bd=1,
                padx=12, pady=12, cursor="hand2",
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            # ── 이미지 영역 ───────────────────────────────────
            photo = _load_photo(item["id"], max_width=160, max_height=160)
            if photo:
                self._photo_refs.append(photo)   # GC 방지 필수
                tk.Label(card, image=photo,
                         bg=PASTEL["card"]).pack(pady=(0, 6))
            else:
                # 이미지 없으면 카테고리 이모지로 대체
                emoji = CATEGORY_EMOJI.get(item.get("category", ""), "🥤")
                tk.Label(card, text=emoji,
                         font=("맑은 고딕", 32),
                         bg=PASTEL["card"]).pack(pady=(0, 6))
            # ─────────────────────────────────────────────────

            tk.Label(card, text=item["name"],
                     font=("맑은 고딕", 12, "bold"),
                     bg=PASTEL["card"], fg=PASTEL["text"],
                     wraplength=130).pack()
            tk.Label(card, text=item["category"],
                     font=("맑은 고딕", 9),
                     bg=PASTEL["card"], fg=PASTEL["subtext"]).pack()
            tk.Label(card, text=f"{item['price']:,}원",
                     font=("맑은 고딕", 13, "bold"),
                     bg=PASTEL["card"], fg=PASTEL["accent"]).pack(pady=(6, 8))
            tk.Button(card, text="담기 +",
                      font=("맑은 고딕", 10, "bold"),
                      bg=PASTEL["add_btn"], fg=PASTEL["add_txt"],
                      relief="flat", padx=12,
                      command=lambda i=item: self._open_customize(i)).pack()

            for widget in [card] + card.winfo_children():
                widget.bind("<Button-1>",
                            lambda e, i=item: self._open_customize(i))

        for c in range(COLS):
            self.grid_frame.columnconfigure(c, weight=1)

    def _open_customize(self, item):
        dlg = CustomizeDialog(self.winfo_toplevel(), item, self.menu_data)
        self.wait_window(dlg)
        if dlg.result:
            self.on_add_to_cart(dlg.result)
