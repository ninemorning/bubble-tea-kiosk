"""
menu_frame.py  ─  버블티 키오스크 메뉴 화면

레이아웃 (참고 이미지 기반):
  ┌──────────┬───────────────────┬──────────────────────────┐
  │ 카테고리  │   메뉴 목록        │   상세 / 옵션 패널        │
  │ 사이드바  │  (스크롤 리스트)   │  이미지 + 이름 + 옵션     │
  └──────────┴───────────────────┴──────────────────────────┘
"""

import json
import os
import tkinter as tk
from tkinter import ttk

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


MENU_FILE  = "data/menu.json"
IMAGES_DIR = "data/images"

C = {
    "bg":          "#FFF5F9",
    "sidebar_bg":  "#FFFFFF",
    "sidebar_sel": "#FFF0F5",
    "sidebar_acc": "#D4547A",
    "list_bg":     "#F7F7F7",
    "card":        "#FFFFFF",
    "card_sel":    "#FFE4F0",
    "detail_bg":   "#FFFFFF",
    "header":      "#F9C8D9",
    "accent":      "#D4547A",
    "text":        "#3A2030",
    "subtext":     "#7A5068",
    "tag_bg":      "#FFFFFF",
    "tag_sel_bg":  "#D4547A",
    "tag_sel_fg":  "#FFFFFF",
    "tag_fg":      "#3A2030",
    "tag_border":  "#CCCCCC",
    "add_btn":     "#D4547A",
    "add_txt":     "#FFFFFF",
    "topping_bg":  "#FAFAFA",
    "topping_sel": "#FFE4F0",
}

CATEGORY_EMOJI = {
    "밀크티": "🧋",
    "과일차": "🍓",
    "슬러시": "🧊",
}


def load_menu() -> dict:
    with open(MENU_FILE, encoding="utf-8") as f:
        return json.load(f)


def _load_photo(item_id, max_w: int, max_h: int):
    if not PIL_AVAILABLE:
        return None
    for ext in ("png", "jpg", "jpeg", "webp"):
        path = os.path.join(IMAGES_DIR, f"{item_id}.{ext}")
        if os.path.exists(path):
            try:
                img = Image.open(path).convert("RGBA")
                img.thumbnail((max_w, max_h), Image.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception:
                return None
    return None


class TagButton(tk.Label):
    def __init__(self, parent, text, on_select, selected=False, **kw):
        super().__init__(parent, text=text,
                         font=("맑은 고딕", 10),
                         padx=14, pady=5,
                         relief="solid", bd=1,
                         cursor="hand2", **kw)
        self.on_select = on_select
        self.set_selected(selected)
        self.bind("<Button-1>", lambda e: self.on_select())

    def set_selected(self, val: bool):
        if val:
            self.config(bg=C["tag_sel_bg"], fg=C["tag_sel_fg"])
        else:
            self.config(bg=C["tag_bg"], fg=C["tag_fg"])


class MenuFrame(tk.Frame):
    """
    [대외 인터페이스]
    on_add_to_cart : callable(order_item: dict)
    on_open_cart   : callable()  — 장바구니 팝업 열기
    get_cart       : callable() -> list  — 현재 카트 리스트 반환
    """

    def __init__(self, parent, on_add_to_cart,
                 on_open_cart=None, get_cart=None, order_frame=None, **kwargs):
        super().__init__(parent, bg=C["bg"], **kwargs)
        self.on_add_to_cart = on_add_to_cart
        self.on_open_cart   = on_open_cart
        self.get_cart       = get_cart        # () -> list[dict]
        self.menu_data      = load_menu()
        self._photo_refs    = []

        self._cur_cat        = "전체"
        self._cur_item       = None
        self._sweetness_val  = None
        self._ice_val        = None
        self._sweetness_btns = []
        self._ice_btns       = []
        self._topping_states = {}
        self._topping_cards  = {}
        self._list_cards     = []

        self._build_layout()
        items = self.menu_data["items"]
        if items:
            self._select_item(items[0])

    # ────────────────────────────────────────────────────────
    # 레이아웃
    # ────────────────────────────────────────────────────────

    def _build_layout(self):
        header = tk.Frame(self, bg=C["header"], pady=8)
        header.pack(fill="x")
        tk.Label(header, text="🧋  버블티 키오스크",
                 font=("맑은 고딕", 14, "bold"),
                 bg=C["header"], fg=C["accent"]).pack()

        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_list_panel(body)
        self._build_detail_panel(body)

    # ── 사이드바 ─────────────────────────────────────────────
    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=C["sidebar_bg"], width=72)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        self._sidebar_btns = {}
        cats = ["전체"] + self.menu_data["categories"]
        for cat in cats:
            emoji = "🍵" if cat == "전체" else CATEGORY_EMOJI.get(cat, "☕")

            btn_frame = tk.Frame(sb, bg=C["sidebar_bg"], cursor="hand2")
            btn_frame.pack(fill="x")

            bar = tk.Frame(btn_frame, width=4, bg=C["sidebar_bg"])
            bar.pack(side="left", fill="y")

            inner = tk.Frame(btn_frame, bg=C["sidebar_bg"])
            inner.pack(side="left", fill="both", expand=True)

            icon = tk.Label(inner, text=emoji,
                            font=("맑은 고딕", 15),
                            bg=C["sidebar_bg"], fg=C["text"],
                            pady=4)
            icon.pack()
            lbl = tk.Label(inner, text=cat,
                           font=("맑은 고딕", 8),
                           bg=C["sidebar_bg"], fg=C["subtext"],
                           pady=0)
            lbl.pack(pady=(0, 6))

            self._sidebar_btns[cat] = (btn_frame, inner, icon, lbl, bar)

            for w in (btn_frame, inner, icon, lbl):
                w.bind("<Button-1>", lambda e, c=cat: self._select_category(c))

        self._update_sidebar_sel()

    # ── 메뉴 리스트 ─────────────────────────────────────────
    def _build_list_panel(self, parent):
        panel = tk.Frame(parent, bg=C["list_bg"], width=150)
        panel.pack(side="left", fill="y")
        panel.pack_propagate(False)

        canvas = tk.Canvas(panel, bg=C["list_bg"],
                           highlightthickness=0, width=145)
        sb = ttk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        self._list_inner = tk.Frame(canvas, bg=C["list_bg"])

        self._list_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._list_inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)

        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._render_list()

    # ── 상세 패널 ────────────────────────────────────────────
    def _build_detail_panel(self, parent):
        panel = tk.Frame(parent, bg=C["detail_bg"])
        panel.pack(side="left", fill="both", expand=True)

        # 하단 고정 바 — 왼쪽: 카트(클릭→팝업), 오른쪽: 담기 버튼
        bottom = tk.Frame(panel, bg="#FFFFFF", pady=0, padx=0)
        bottom.pack(fill="x", side="bottom")
        ttk.Separator(panel, orient="horizontal").pack(fill="x", side="bottom")

        # 왼쪽: 카트 아이콘 클릭 → 팝업
        left_area = tk.Frame(bottom, bg="#FFFFFF", cursor="hand2")
        left_area.pack(side="left", padx=14, pady=10)

        # 카트 아이콘 원형 배경
        cart_circle = tk.Frame(left_area, bg="#555555", width=50, height=50)
        cart_circle.pack(side="left")
        cart_circle.pack_propagate(False)
        self._cart_icon_lbl = tk.Label(cart_circle, text="🛒",
                                        font=("맑은 고딕", 17),
                                        bg="#555555", fg="white",
                                        cursor="hand2")
        self._cart_icon_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # 카트 개수 뱃지
        self._cart_badge = tk.Label(cart_circle, text="0",
                                     font=("맑은 고딕", 8, "bold"),
                                     bg="#E87FAA", fg="white",
                                     width=2)
        self._cart_badge.place(relx=0.72, rely=0.08)

        # 금액 & 상태 텍스트
        price_box = tk.Frame(left_area, bg="#FFFFFF", cursor="hand2")
        price_box.pack(side="left", padx=(10, 0))
        self._cart_total_label = tk.Label(price_box, text="₩ 0",
                                           font=("맑은 고딕", 13, "bold"),
                                           bg="#FFFFFF", fg=C["text"],
                                           cursor="hand2")
        self._cart_total_label.pack(anchor="w")
        self._cart_status = tk.Label(price_box, text="미선택 상품",
                                      font=("맑은 고딕", 9),
                                      bg="#FFFFFF", fg="#AAAAAA",
                                      cursor="hand2")
        self._cart_status.pack(anchor="w")

        # 클릭 바인딩 — 카트 팝업 열기
        def _open():
            if callable(self.on_open_cart):
                self.on_open_cart()
        for w in [left_area, cart_circle, self._cart_icon_lbl,
                  price_box, self._cart_total_label, self._cart_status,
                  self._cart_badge]:
            w.bind("<Button-1>", lambda e: _open())

        # 오른쪽: 담기 버튼
        self._total_label = tk.Label(bottom, text="")  # 더미 (내부 호환용)
        tk.Button(bottom, text="장바구니 담기",
                  font=("맑은 고딕", 12, "bold"),
                  bg=C["add_btn"], fg=C["add_txt"],
                  relief="flat", padx=28, pady=14,
                  command=self._add_to_cart).pack(side="right", fill="y")

        # 스크롤 영역
        canvas = tk.Canvas(panel, bg=C["detail_bg"], highlightthickness=0)
        sb = ttk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        self._detail_inner = tk.Frame(canvas, bg=C["detail_bg"])
        self._detail_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._detail_inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

    # ────────────────────────────────────────────────────────
    # 카테고리 선택
    # ────────────────────────────────────────────────────────

    def _select_category(self, cat):
        self._cur_cat = cat
        self._update_sidebar_sel()
        self._render_list()
        items = self._filtered_items()
        if items:
            self._select_item(items[0])

    def _update_sidebar_sel(self):
        for cat, (frm, inner, icon, lbl, bar) in self._sidebar_btns.items():
            sel = (cat == self._cur_cat)
            bg  = C["sidebar_sel"] if sel else C["sidebar_bg"]
            fg_main = C["accent"] if sel else C["text"]
            fg_sub  = C["accent"] if sel else C["subtext"]
            bar_c   = C["accent"] if sel else C["sidebar_bg"]
            for w in (frm, inner):
                w.config(bg=bg)
            icon.config(bg=bg, fg=fg_main)
            lbl.config(bg=bg, fg=fg_sub)
            bar.config(bg=bar_c)

    def _filtered_items(self):
        items = self.menu_data["items"]
        if self._cur_cat != "전체":
            items = [i for i in items if i["category"] == self._cur_cat]
        return items

    # ────────────────────────────────────────────────────────
    # 메뉴 리스트 렌더링
    # ────────────────────────────────────────────────────────

    def _render_list(self):
        for w in self._list_inner.winfo_children():
            w.destroy()
        self._list_photo_refs = []
        self._list_cards = []

        for item in self._filtered_items():
            self._make_list_card(item)

    def _make_list_card(self, item):
        card = tk.Frame(self._list_inner, bg=C["card"],
                        cursor="hand2", pady=8, padx=8)
        card.pack(fill="x", padx=6, pady=3)

        photo = _load_photo(item["id"], max_w=64, max_h=64)
        if photo:
            self._list_photo_refs.append(photo)
            tk.Label(card, image=photo, bg=C["card"]).pack(
                side="left", padx=(0, 8))
        else:
            emoji = CATEGORY_EMOJI.get(item.get("category", ""), "🥤")
            tk.Label(card, text=emoji, font=("맑은 고딕", 22),
                     bg=C["card"]).pack(side="left", padx=(0, 8))

        info = tk.Frame(card, bg=C["card"])
        info.pack(side="left", fill="both", expand=True)
        tk.Label(info, text=item["name"],
                 font=("맑은 고딕", 11, "bold"),
                 bg=C["card"], fg=C["text"],
                 anchor="w", wraplength=100).pack(anchor="w")
        tk.Label(info, text=f"{item['price']:,}원",
                 font=("맑은 고딕", 11),
                 bg=C["card"], fg=C["accent"],
                 anchor="w").pack(anchor="w", pady=(2, 0))

        all_ws = [card] + list(card.winfo_children()) + list(info.winfo_children())
        for w in all_ws:
            w.bind("<Button-1>", lambda e, i=item: self._select_item(i))

        card._item = item
        card._all_ws = all_ws
        self._list_cards.append(card)

    def _highlight_list_card(self, selected_item):
        for card in self._list_cards:
            sel = card._item["id"] == selected_item["id"]
            bg  = C["card_sel"] if sel else C["card"]
            for w in card._all_ws:
                try:
                    w.config(bg=bg)
                except Exception:
                    pass

    # ────────────────────────────────────────────────────────
    # 상세 패널 렌더링
    # ────────────────────────────────────────────────────────

    def _select_item(self, item):
        self._cur_item      = item
        self._sweetness_val = self.menu_data["options"]["sweetness"][2]
        self._ice_val       = self.menu_data["options"]["ice"][0]
        self._topping_states = {
            t["name"]: tk.BooleanVar(value=False)
            for t in self.menu_data["options"]["toppings"]
        }
        self._highlight_list_card(item)
        self._render_detail(item)
        self._refresh_total()

    def _render_detail(self, item):
        for w in self._detail_inner.winfo_children():
            w.destroy()
        self._photo_refs.clear()
        self._topping_cards.clear()

        options  = self.menu_data["options"]
        toppings = options["toppings"]

        # 큰 이미지
        photo = _load_photo(item["id"], max_w=220, max_h=180)
        if photo:
            self._photo_refs.append(photo)
            tk.Label(self._detail_inner, image=photo,
                     bg=C["detail_bg"]).pack(pady=(12, 0))
        else:
            emoji = CATEGORY_EMOJI.get(item.get("category", ""), "🥤")
            tk.Label(self._detail_inner, text=emoji,
                     font=("맑은 고딕", 48),
                     bg=C["detail_bg"]).pack(pady=(16, 0))

        # 이름 / 가격
        tk.Label(self._detail_inner, text=item["name"],
                 font=("맑은 고딕", 15, "bold"),
                 bg=C["detail_bg"], fg=C["text"]).pack(
                     anchor="w", padx=16, pady=(10, 0))
        tk.Label(self._detail_inner,
                 text=f"₩ {item['price']:,}",
                 font=("맑은 고딕", 13, "bold"),
                 bg=C["detail_bg"], fg=C["accent"]).pack(
                     anchor="w", padx=16, pady=(2, 8))

        ttk.Separator(self._detail_inner).pack(fill="x", padx=16, pady=3)

        # 당도
        self._build_option_section(
            "당도",
            choices=[f"{v}%" for v in options["sweetness"]],
            values=options["sweetness"],
            get_val=lambda: self._sweetness_val,
            set_val=lambda v: setattr(self, "_sweetness_val", v),
            attr="_sweetness_btns",
        )
        ttk.Separator(self._detail_inner).pack(fill="x", padx=16, pady=3)

        # 얼음
        self._build_option_section(
            "얼음",
            choices=options["ice"],
            values=options["ice"],
            get_val=lambda: self._ice_val,
            set_val=lambda v: setattr(self, "_ice_val", v),
            attr="_ice_btns",
        )
        ttk.Separator(self._detail_inner).pack(fill="x", padx=16, pady=3)

        # 토핑
        tk.Label(self._detail_inner, text="토핑  (복수 선택 가능)",
                 font=("맑은 고딕", 11, "bold"),
                 bg=C["detail_bg"], fg=C["text"]).pack(
                     anchor="w", padx=16, pady=(8, 4))

        grid = tk.Frame(self._detail_inner, bg=C["detail_bg"])
        grid.pack(fill="x", padx=16, pady=(0, 10))
        for idx, t in enumerate(toppings):
            tc = self._make_topping_card(grid, t)
            tc.grid(row=idx // 4, column=idx % 4, padx=3, pady=3, sticky="nsew")
            self._topping_cards[t["name"]] = tc
        for c in range(4):
            grid.columnconfigure(c, weight=1)

        tk.Label(self._detail_inner, bg=C["detail_bg"]).pack(pady=4)

    def _build_option_section(self, label, choices, values,
                               get_val, set_val, attr):
        tk.Label(self._detail_inner, text=label,
                 font=("맑은 고딕", 11, "bold"),
                 bg=C["detail_bg"], fg=C["text"]).pack(
                     anchor="w", padx=16, pady=(8, 4))

        row = tk.Frame(self._detail_inner, bg=C["detail_bg"])
        row.pack(anchor="w", padx=16, pady=(0, 8))

        btn_list = []
        setattr(self, attr, btn_list)

        def make_cb(val, blist, sv, gv):
            def cb():
                sv(val)
                for b, v in blist:
                    b.set_selected(v == gv())
                self._refresh_total()
            return cb

        for ch, val in zip(choices, values):
            is_sel = (val == get_val())
            btn = TagButton(row, text=ch, on_select=lambda: None,
                            selected=is_sel)
            btn_list.append((btn, val))
            btn.pack(side="left", padx=4)

        for btn, val in btn_list:
            btn.on_select = make_cb(val, btn_list, set_val, get_val)
            btn.bind("<Button-1>", lambda e, f=btn.on_select: f())

    def _make_topping_card(self, parent, topping):
        var  = self._topping_states[topping["name"]]
        card = tk.Frame(parent, bg=C["topping_bg"],
                        relief="solid", bd=1,
                        padx=6, pady=6, cursor="hand2")

        # 토핑 이미지 파일명 매핑: t1=타피오카 펄, t2=코코넛 젤리, t3=푸딩, t4=알로에
        TOPPING_FILE = {
            "타피오카 펄": "t1",
            "코코넛 젤리": "t2",
            "푸딩":        "t3",
            "알로에":      "t4",
        }
        TOPPING_EMOJI = {
            "타피오카 펄": "🫧",
            "코코넛 젤리": "🥥",
            "푸딩":        "🍮",
            "알로에":      "🌿",
        }
        fname   = TOPPING_FILE.get(topping["name"], f"t_{topping['name']}")
        t_photo = _load_photo(fname, max_w=60, max_h=60)
        if t_photo:
            self._photo_refs.append(t_photo)
            tk.Label(card, image=t_photo, bg=C["topping_bg"]).pack(pady=(2, 2))
        else:
            emoji = TOPPING_EMOJI.get(topping["name"], "🧁")
            tk.Label(card, text=emoji,
                     font=("맑은 고딕", 20),
                     bg=C["topping_bg"]).pack(pady=(2, 2))
        tk.Label(card, text=topping["name"],
                 font=("맑은 고딕", 9),
                 bg=C["topping_bg"], fg=C["text"]).pack()
        tk.Label(card, text=f"+{topping['price']:,}원",
                 font=("맑은 고딕", 9),
                 bg=C["topping_bg"], fg=C["subtext"]).pack()

        def toggle(c=card, v=var):
            v.set(not v.get())
            self._set_topping_style(c, v.get())
            self._refresh_total()

        for w in [card] + list(card.winfo_children()):
            w.bind("<Button-1>", lambda e, fn=toggle: fn())

        self._set_topping_style(card, var.get())
        return card

    def _set_topping_style(self, card, selected: bool):
        bg = C["topping_sel"] if selected else C["topping_bg"]
        for w in [card] + list(card.winfo_children()):
            try:
                w.config(bg=bg)
            except Exception:
                pass

    # ────────────────────────────────────────────────────────
    # 합계 & 담기
    # ────────────────────────────────────────────────────────

    def _calc_total(self) -> int:
        if not self._cur_item:
            return 0
        topping_price = sum(
            t["price"]
            for t in self.menu_data["options"]["toppings"]
            if self._topping_states.get(t["name"], tk.BooleanVar()).get()
        )
        return self._cur_item["price"] + topping_price

    def _refresh_total(self):
        # 하단 바: 선택 메뉴 금액 표시
        total = self._calc_total()
        if self._cur_item:
            self._cart_status.config(text=self._cur_item["name"])
        else:
            self._cart_status.config(text="미선택 상품")
        # 카트 전체 금액 & 개수 동기화
        self._sync_cart_bar()

    def _sync_cart_bar(self):
        """장바구니 실제 총액·개수를 하단 바에 반영"""
        cart = self.get_cart() if callable(self.get_cart) else []
        if cart:
            cart_total = sum(i["unit_price"] * i["quantity"] for i in cart)
            cart_count = sum(i["quantity"] for i in cart)
            self._cart_total_label.config(text=f"₩ {cart_total:,}")
            self._cart_badge.config(text=str(cart_count))
        else:
            self._cart_total_label.config(text="₩ 0")
            self._cart_badge.config(text="0")

    def _add_to_cart(self):
        if not self._cur_item:
            return
        item = self._cur_item
        selected_toppings = [
            t for t in self.menu_data["options"]["toppings"]
            if self._topping_states.get(t["name"], tk.BooleanVar()).get()
        ]
        topping_price = sum(t["price"] for t in selected_toppings)
        self.on_add_to_cart({
            "item_id":    item["id"],
            "name":       item["name"],
            "base_price": item["price"],
            "sweetness":  self._sweetness_val,
            "ice":        self._ice_val,
            "toppings":   selected_toppings,
            "unit_price": item["price"] + topping_price,
            "quantity":   1,
        })
        self._sync_cart_bar()
        # 토핑 초기화
        for var in self._topping_states.values():
            var.set(False)
        for card in self._topping_cards.values():
            self._set_topping_style(card, False)
        self._refresh_total()
