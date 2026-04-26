import ctypes
import json
import os
import sys
import threading
import time
import urllib.request
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
try:
    import winreg
except Exception:
    winreg = None

from PIL import Image, ImageTk
import pystray

import bm_single_instance


PROJECT_NAME = "塔科夫商人補貨計時"
APP_SHORT_NAME = "tarkov-trader-restock-timer"
APP_EXE_PREFIX = "bm-" + APP_SHORT_NAME
HTTP_USER_AGENT = APP_EXE_PREFIX + "/1.0"
TITLE_PREFIX = "[B.M] "
TITLE_SUFFIX = " V1.0 By. [B.M] 圓周率 3.14"
SINGLE_APP_ID = APP_EXE_PREFIX
CONFIG_NAME = APP_EXE_PREFIX + ".json"
ABOUT_URL = "http://exnormal.com:81/"
REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040
WINDOW_WIDTH = 950
                                                                         
WINDOW_HEIGHT = 200
WINDOW_X = 100
WINDOW_Y = 100
CARD_WIDTH = 100
                                                                   
CARD_HEIGHT = 152
                                  
RESTOCK_DETAIL_LINE_HEIGHT = 20
CARD_PAD_X = 2
                                                   
TRADER_STRIP_OUTER_PAD = 6
                              
CARD_INNER_PADDING = (2, 2, 2, 0)
                                                  
TRADER_IMAGE_SIZE = 90
IMAGE_TOP_PAD = 3
                                  
HIDDEN_IMAGE_STRIP_HEIGHT = IMAGE_TOP_PAD + TRADER_IMAGE_SIZE
                                         
BOTTOM_STACK_WHEN_AT_MOST = 3
BOTTOM_STACK_EXTRA_HEIGHT = 90
DEFAULT_GAME_MODE = "pve"
GAME_MODES = ("pve", "regular")
BUILTIN_I18N_ORDER = ("zh_TW", "zh_CN", "ja_JP", "en_US")
DEFAULT_TK_FONT_SIZE = 10

TRADERS = [
    ("prapor", {"zh_TW": "Prapor", "zh_CN": "Prapor", "ja_JP": "Prapor", "en_US": "Prapor"}),
    ("therapist", {"zh_TW": "Therapist", "zh_CN": "Therapist", "ja_JP": "Therapist", "en_US": "Therapist"}),
    ("fence", {"zh_TW": "Fence", "zh_CN": "Fence", "ja_JP": "Fence", "en_US": "Fence"}),
    ("skier", {"zh_TW": "Skier", "zh_CN": "Skier", "ja_JP": "Skier", "en_US": "Skier"}),
    ("peacekeeper", {"zh_TW": "Peacekeeper", "zh_CN": "Peacekeeper", "ja_JP": "Peacekeeper", "en_US": "Peacekeeper"}),
    ("mechanic", {"zh_TW": "Mechanic", "zh_CN": "Mechanic", "ja_JP": "Mechanic", "en_US": "Mechanic"}),
    ("ragman", {"zh_TW": "Ragman", "zh_CN": "Ragman", "ja_JP": "Ragman", "en_US": "Ragman"}),
    ("jaeger", {"zh_TW": "Jaeger", "zh_CN": "Jaeger", "ja_JP": "Jaeger", "en_US": "Jaeger"}),
    ("ref", {"zh_TW": "競技場裁判", "zh_CN": "竞技场裁判", "ja_JP": "アリーナ審判", "en_US": "Ref"}),
]

def default_trader_names_for_lang(lang_code):
    return {slug: names.get(lang_code, names.get("en_US", slug)) for slug, names in TRADERS}


def trader_row_content_width(visible_n):
    if visible_n < 1:
        visible_n = 1
    return TRADER_STRIP_OUTER_PAD * 2 + visible_n * (CARD_WIDTH + 2 * CARD_PAD_X)


def default_visible_traders():
    visible = {slug: True for slug, _names in TRADERS}
    visible["fence"] = False
    return visible


def resource_path(*parts):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base.joinpath(*parts)


def apply_default_font_size(root):
    for name in (
        "TkDefaultFont",
        "TkTextFont",
        "TkFixedFont",
        "TkMenuFont",
        "TkHeadingFont",
        "TkCaptionFont",
        "TkSmallCaptionFont",
        "TkIconFont",
        "TkTooltipFont",
    ):
        try:
            tkfont.nametofont(name).configure(size=DEFAULT_TK_FONT_SIZE)
        except tk.TclError:
            pass


def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def default_config():
    cfg = {
        "settings": {
            "languages": "zh_TW",
            "game_mode": DEFAULT_GAME_MODE,
            "auto_start": False,
            "auto_minimize": False,
            "always_on_top": False,
            "hide_trader_images": False,
            "show_next_arrival": False,
            "visible_traders": default_visible_traders(),
        },
        "languages": {
            "zh_TW": {
                "language_name": "繁體中文",
                "project_name": "塔科夫商人補貨計時",
                "settings": "設定",
                "settings_button": "設定",
                "settings_title": "設定",
                "autostart_checkbox": "跟著 Windows 啟動",
                "auto_minimize_checkbox": "啟動後自動縮小",
                "hide_trader_images_checkbox": "隱藏商人圖片",
                "always_on_top_checkbox": "最上層顯示",
                "show_next_arrival_checkbox": "顯示下次到貨時間",
                "traders_visibility_title": "顯示商人",
                "settings_close": "關閉",
                "next_arrival_prefix": "下次到貨",
                "countdown_updating": "更新中",
                "tray_restore": "還原",
                "about": "關於",
                "exit": "離開",
            },
            "zh_CN": {
                "language_name": "简体中文",
                "project_name": "塔科夫商人补货计时",
                "settings": "设置",
                "settings_button": "设置",
                "settings_title": "设置",
                "autostart_checkbox": "随 Windows 启动",
                "auto_minimize_checkbox": "启动后自动最小化",
                "hide_trader_images_checkbox": "隐藏商人图片",
                "always_on_top_checkbox": "置顶显示",
                "show_next_arrival_checkbox": "显示下次到货时间",
                "traders_visibility_title": "显示商人",
                "settings_close": "关闭",
                "next_arrival_prefix": "下次到货",
                "countdown_updating": "更新中",
                "tray_restore": "还原",
                "about": "关于",
                "exit": "离开",
            },
            "ja_JP": {
                "language_name": "日本語",
                "project_name": "タルコフトレーダー補充タイマー",
                "settings": "設定",
                "settings_button": "設定",
                "settings_title": "設定",
                "autostart_checkbox": "Windows 起動時に実行",
                "auto_minimize_checkbox": "起動後に最小化",
                "hide_trader_images_checkbox": "トレーダー画像を非表示",
                "always_on_top_checkbox": "最前面に表示",
                "show_next_arrival_checkbox": "次回入荷時刻を表示",
                "traders_visibility_title": "表示するトレーダー",
                "settings_close": "閉じる",
                "next_arrival_prefix": "次回入荷",
                "countdown_updating": "更新中",
                "tray_restore": "復元",
                "about": "バージョン情報",
                "exit": "終了",
            },
            "en_US": {
                "language_name": "English",
                "project_name": "Tarkov Trader Restock Timer",
                "settings": "Settings",
                "settings_button": "Settings",
                "settings_title": "Settings",
                "autostart_checkbox": "Start with Windows",
                "auto_minimize_checkbox": "Start minimized",
                "hide_trader_images_checkbox": "Hide trader images",
                "always_on_top_checkbox": "Always on top",
                "show_next_arrival_checkbox": "Show next arrival time",
                "traders_visibility_title": "Visible traders",
                "settings_close": "Close",
                "next_arrival_prefix": "Next",
                "countdown_updating": "Updating",
                "tray_restore": "Restore",
                "about": "About",
                "exit": "Exit",
            },
        },
    }
    for code in cfg["languages"]:
        cfg["languages"][code]["trader_names"] = default_trader_names_for_lang(code)
    return cfg


def _tarkov_reference_lang_block():
    return default_config()["languages"]["zh_TW"]


def _tarkov_lang_block_valid(m: object) -> bool:
    if not isinstance(m, dict):
        return False
    ref = _tarkov_reference_lang_block()
    if frozenset(m.keys()) != frozenset(ref.keys()):
        return False
    rtr = ref.get("trader_names") or {}
    for k, _sample in ref.items():
        if k == "trader_names":
            tr = m.get("trader_names")
            if not isinstance(tr, dict):
                return False
            if frozenset(tr.keys()) != frozenset(rtr.keys()):
                return False
            for sk in rtr:
                v = tr.get(sk)
                if not isinstance(v, str) or not v.strip():
                    return False
        else:
            v = m.get(k)
            if not isinstance(v, str):
                return False
            if k in ("language_name", "project_name", "settings") and not v.strip():
                return False
    return True


def merge_config(data):
    merged = default_config()
    if not isinstance(data, dict):
        return merged
    settings = data.get("settings")
    if isinstance(settings, dict):
        merged["settings"].update(settings)
    if merged["settings"].get("game_mode") not in GAME_MODES:
        merged["settings"]["game_mode"] = DEFAULT_GAME_MODE
    visible = merged["settings"].get("visible_traders")
    if not isinstance(visible, dict):
        visible = {}
    merged["settings"]["visible_traders"] = {
        slug: bool(visible.get(slug, True)) for slug, _names in TRADERS
    }
    languages = data.get("languages")
    if isinstance(languages, dict) and languages:
        for code, values in languages.items():
            if not isinstance(values, dict):
                continue
            base = dict(merged["languages"].get(code, merged["languages"]["en_US"]))
            base.update(values)
            merged["languages"][code] = base
    for code, block in list(merged["languages"].items()):
        tnames = block.get("trader_names")
        names_out = default_trader_names_for_lang(code)
        if isinstance(tnames, dict):
            for slug, _n in TRADERS:
                v = tnames.get(slug)
                if isinstance(v, str) and v.strip():
                    names_out[slug] = v.strip()
        block["trader_names"] = names_out
        w = block.get("settings")
        if not (isinstance(w, str) and w.strip()):
            st = block.get("settings_title")
            if isinstance(st, str) and st.strip():
                block["settings"] = st.strip()
            else:
                block["settings"] = (merged["languages"].get("en_US") or {}).get("settings", "Settings")
    sel = merged["settings"].get("languages")
    if not isinstance(sel, str) or sel.strip() not in merged["languages"]:
        picked = None
        for c in BUILTIN_I18N_ORDER:
            if c in merged["languages"]:
                picked = c
                break
        if picked is None:
            first = next(iter(merged["languages"].keys()), "zh_TW")
            picked = first
        merged["settings"]["languages"] = picked
    return merged


def is_valid_config(data):
    if not isinstance(data, dict):
        return False
    settings = data.get("settings")
    languages = data.get("languages")
    if not isinstance(settings, dict) or not isinstance(languages, dict) or not languages:
        return False
    selected = settings.get("languages")
    if not isinstance(selected, str) or not selected.strip():
        return False
    if selected not in languages:
        return False
    if settings.get("game_mode", DEFAULT_GAME_MODE) not in GAME_MODES:
        return False
    vis = settings.get("visible_traders")
    if not isinstance(vis, dict):
        return False
    for slug, _n in TRADERS:
        if slug not in vis or not isinstance(vis.get(slug), bool):
            return False
    for value in languages.values():
        if not _tarkov_lang_block_valid(value):
            return False
    return True


def load_config():
    path = app_dir() / CONFIG_NAME
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if is_valid_config(data):
                data = merge_config(data)
                save_config(data)
                return data
        except Exception:
            pass
        try:
            path.unlink()
        except Exception:
            pass
    data = default_config()
    save_config(data)
    return data


def save_config(data):
    try:
        with (app_dir() / CONFIG_NAME).open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_exe_path_for_autostart():
    if getattr(sys, "frozen", False) and sys.executable:
        return os.path.normpath(sys.executable)
    return os.path.normpath(os.path.abspath(sys.argv[0]))


def set_auto_start(enabled):
    if os.name != "nt" or winreg is None:
        return
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_SET_VALUE)
    except Exception:
        return
    try:
        if enabled:
            winreg.SetValueEx(key, APP_EXE_PREFIX, 0, winreg.REG_SZ, get_exe_path_for_autostart())
        else:
            try:
                winreg.DeleteValue(key, APP_EXE_PREFIX)
            except OSError:
                pass
    except Exception:
        pass
    try:
        winreg.CloseKey(key)
    except Exception:
        pass


class TraderTimerApp:
    def __init__(self, root, _mutex_handle):
        self.root = root
        self.config = load_config()
        self.tray_icon = None
        self.tray_thread = None
        self.exiting = False
        self.fetching_reset_times = False
        self.reset_times = {}
        self.countdown_labels = {}
        self.next_arrival_labels = {}
        self.image_labels = {}
        self.name_labels = {}
        self.trader_cards = {}
        self.images = []
        self.settings_window = None
        self.settings_vars = {}
        self.always_on_top_var = tk.BooleanVar(value=bool(self.config["settings"].get("always_on_top")))

        self.configure_window()
        self.configure_styles()
        self.build_ui()
        self._install_no_focus_dotted_ring()
        self.apply_visibility()
        self.apply_image_visibility()
        self.apply_always_on_top()
        bm_single_instance.start_pipe_server(
            SINGLE_APP_ID,
            lambda: self.root.after(0, self.exit_app),
        )
        self.start_tray()
        set_auto_start(bool(self.config["settings"].get("auto_start")))
        self.refresh_reset_times_async()
        self.tick()
        if bool(self.config["settings"].get("auto_minimize")):
            self.root.after(0, self.hide_to_tray)

    @property
    def language(self):
        selected = self.config["settings"].get("languages")
        if selected in self.config["languages"]:
            return selected
        return next(iter(self.config["languages"]))

    @property
    def game_mode(self):
        selected = self.config["settings"].get("game_mode", DEFAULT_GAME_MODE)
        if selected in GAME_MODES:
            return selected
        return DEFAULT_GAME_MODE

    def text_for(self, key):
        lang = self.config["languages"].get(self.language, {})
        if key in lang:
            return lang[key]
        return default_config()["languages"]["en_US"].get(key, key)

    def trader_display_name(self, slug):
        block = self.config["languages"].get(self.language) or {}
        tnames = block.get("trader_names") or {}
        if isinstance(tnames.get(slug), str) and tnames[slug].strip():
            return tnames[slug].strip()
        for s, names in TRADERS:
            if s == slug:
                return names.get(self.language, names.get("en_US", slug))
        return slug

    def full_title(self):
        return TITLE_PREFIX + self.text_for("project_name") + TITLE_SUFFIX

    def configure_window(self):
        self.root.title(self.full_title())
        self.position_window()
        self.root.resizable(False, False)
        self.root.configure(bg="#111310")
        try:
            self.root.iconbitmap(str(resource_path("icons", "icon.ico")))
        except Exception:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
        self.root.bind("<Unmap>", self.on_unmap)
        self.root.after(200, self.disable_maximize_button)

    def configure_styles(self):
        style = ttk.Style(self.root)
        style.configure("Dark.TFrame", background="#111310")
        style.configure("Card.TFrame", background="#20231f", borderwidth=1, relief="solid")
                                
        style.configure("CardInner.TFrame", background="#20231f", borderwidth=0, relief="flat")
        style.configure("Image.TLabel", background="#151714", anchor=tk.CENTER, relief="flat", borderwidth=0)
                 
        style.configure("Name.TLabel", background="#20231f", foreground="#cfc6a5", anchor=tk.CENTER, relief="flat", borderwidth=0)
        style.configure("Countdown.TLabel", background="#20231f", foreground="#bdbdbd", anchor=tk.CENTER, relief="flat", borderwidth=0)
        style.configure("Detail.TLabel", background="#20231f", foreground="#8f9588", anchor=tk.CENTER, relief="flat", borderwidth=0)
        style.configure("Dark.TLabel", background="#111310", foreground="#ddd7c3")
        style.configure("Dark.TCheckbutton", background="#111310", foreground="#ddd7c3", focuscolor="#111310")
        style.map(
            "Dark.TCheckbutton",
            background=[("active", "#111310"), ("!active", "#111310")],
            foreground=[("active", "#ffffff"), ("!active", "#ddd7c3")],
            focuscolor=[("focus", "#111310"), ("!focus", "#111310")],
        )
        try:
            style.configure("TButton", focuscolor=style.lookup("TButton", "background"))
        except tk.TclError:
            pass

    def _ttk_set_no_takefocus(self, widget):
        for ch in widget.winfo_children():
            self._ttk_set_no_takefocus(ch)
        try:
            cls = widget.winfo_class()
        except tk.TclError:
            return
        if cls in ("TButton", "TCheckbutton"):
            try:
                widget.configure(takefocus=False)
            except tk.TclError:
                pass

    def _defocus_toplevel_of(self, w):
        try:
            top = w.winfo_toplevel()
            if top and top.winfo_exists():
                top.focus_set()
        except Exception:
            pass

    def _on_ttk_buttonlike_release(self, event):
        self.root.after_idle(lambda w=event.widget: self._defocus_toplevel_of(w))

    def _install_no_focus_dotted_ring(self):
        self._ttk_set_no_takefocus(self.root)
        if getattr(self, "_focus_release_bind_done", False):
            return
        self._focus_release_bind_done = True
        self.root.bind_class("TButton", "<ButtonRelease-1>", self._on_ttk_buttonlike_release, add="+")
        self.root.bind_class("TCheckbutton", "<ButtonRelease-1>", self._on_ttk_buttonlike_release, add="+")

    def disable_maximize_button(self):
        if os.name != "nt":
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
            ctypes.windll.user32.SetWindowLongW(hwnd, -16, style & ~0x00010000)
        except Exception:
            pass

    def build_ui(self):
        self.trader_strip = ttk.Frame(self.root, style="Dark.TFrame")
        self.trader_strip.pack(side=tk.TOP, fill=tk.X, padx=TRADER_STRIP_OUTER_PAD, pady=(6, 2))
        self.trader_row = ttk.Frame(self.trader_strip, style="Dark.TFrame")
        self.trader_row.pack(anchor=tk.CENTER)
        for slug, _names in TRADERS:
            self.create_trader_card(self.trader_row, slug)

        bottom = ttk.Frame(self.root, style="Dark.TFrame")
        self.bottom = bottom
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=TRADER_STRIP_OUTER_PAD, pady=(0, 5))
        self.always_on_top_check = ttk.Checkbutton(
            bottom,
            text=self.text_for("always_on_top_checkbox"),
            variable=self.always_on_top_var,
            command=self.toggle_always_on_top,
            style="Dark.TCheckbutton",
            takefocus=False,
        )
        self.always_on_top_check.pack(side=tk.LEFT)
        self.language_button = ttk.Button(
            bottom,
            text=self.text_for("language_name"),
            command=self.cycle_language,
            takefocus=False,
        )
        self.game_mode_button = ttk.Button(
            bottom,
            text=self.game_mode_label(),
            command=self.toggle_game_mode,
            takefocus=False,
        )
        self.settings_button = ttk.Button(
            bottom,
            text=self.text_for("settings_button"),
            command=self.open_settings,
            takefocus=False,
        )
    def bottom_layout_is_stacked(self):
        return len(self.visible_traders()) <= BOTTOM_STACK_WHEN_AT_MOST

    def apply_bottom_layout(self):
        for w in (self.always_on_top_check, self.language_button, self.game_mode_button, self.settings_button):
            w.pack_forget()
        if self.bottom_layout_is_stacked():
            self.always_on_top_check.pack(in_=self.bottom, side=tk.TOP, fill=tk.X, pady=(0, 4))
            self.language_button.pack(in_=self.bottom, side=tk.TOP, fill=tk.X, pady=2)
            self.game_mode_button.pack(in_=self.bottom, side=tk.TOP, fill=tk.X, pady=2)
            self.settings_button.pack(in_=self.bottom, side=tk.TOP, fill=tk.X, pady=2)
        else:
            self.always_on_top_check.pack(in_=self.bottom, side=tk.LEFT)
            self.settings_button.pack(in_=self.bottom, side=tk.RIGHT)
            self.game_mode_button.pack(in_=self.bottom, side=tk.RIGHT, padx=(0, 5))
            self.language_button.pack(in_=self.bottom, side=tk.RIGHT, padx=(0, 5))

    def create_trader_card(self, parent, slug):
        card = ttk.Frame(parent, width=CARD_WIDTH, height=CARD_HEIGHT, style="Card.TFrame")
        card.pack(side=tk.LEFT, padx=2)
        card.pack_propagate(False)
        self.trader_cards[slug] = card

        inner = ttk.Frame(card, style="CardInner.TFrame", padding=CARD_INNER_PADDING)
        inner.pack(fill=tk.BOTH, expand=True)

        image_label = ttk.Label(inner, style="Image.TLabel")
        image_label.pack(
            side=tk.TOP,
            anchor=tk.CENTER,
            pady=(IMAGE_TOP_PAD, 0),
        )
        image_label.configure(image=self.load_trader_image(slug))
        self.image_labels[slug] = image_label

        name_label = ttk.Label(
            inner,
            text=self.trader_display_name(slug),
            style="Name.TLabel",
            anchor=tk.CENTER,
        )
        name_label.pack(side=tk.TOP, anchor=tk.CENTER, pady=(0, 0))
        self.name_labels[slug] = name_label

        countdown = ttk.Label(inner, text="--:--:--", style="Countdown.TLabel")
        countdown.pack(side=tk.TOP, anchor=tk.CENTER, pady=(0, 0))
        self.countdown_labels[slug] = countdown

        next_arrival = ttk.Label(inner, text="", style="Detail.TLabel")
        self.next_arrival_labels[slug] = next_arrival

    def load_trader_image(self, slug):
        size = TRADER_IMAGE_SIZE
        try:
            image = Image.open(resource_path("icons", "Origin", slug + ".webp")).convert("RGBA")
            image.thumbnail((size, size), Image.LANCZOS)
            canvas = Image.new("RGBA", (size, size), (18, 20, 17, 255))
            x = (size - image.width) // 2
            y = (size - image.height) // 2
            canvas.alpha_composite(image, (x, y))
        except Exception:
            canvas = Image.new("RGBA", (size, size), (35, 35, 35, 255))
        photo = ImageTk.PhotoImage(canvas)
        self.images.append(photo)
        return photo

    def cycle_language(self):
        lm = self.config["languages"]
        keys = [c for c in BUILTIN_I18N_ORDER if c in lm]
        for k in lm.keys():
            if k not in keys:
                keys.append(k)
        if not keys:
            return
        current = self.language
        index = keys.index(current) if current in keys else 0
        self.config["settings"]["languages"] = keys[(index + 1) % len(keys)]
        save_config(self.config)
        self.apply_language()

    def game_mode_label(self):
        return "PVE" if self.game_mode == "pve" else "PVP"

    def toggle_game_mode(self):
        self.config["settings"]["game_mode"] = "regular" if self.game_mode == "pve" else "pve"
        save_config(self.config)
        self.game_mode_button.configure(text=self.game_mode_label())
        self.reset_times = {}
        self.update_countdown_labels()
        self.refresh_reset_times_async()

    def toggle_always_on_top(self):
        self.config["settings"]["always_on_top"] = bool(self.always_on_top_var.get())
        save_config(self.config)
        self.apply_always_on_top()

    def apply_always_on_top(self):
        enabled = bool(self.always_on_top_var.get())
        try:
            self.root.attributes("-topmost", enabled)
        except Exception:
            pass
        self.apply_window_topmost(self.root, enabled)
        if self.settings_window is not None and self.settings_window.winfo_exists():
            try:
                self.settings_window.attributes("-topmost", enabled)
            except Exception:
                pass
            self.apply_window_topmost(self.settings_window, enabled)

    def apply_window_topmost(self, window, enabled):
        if os.name != "nt":
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            insert_after = HWND_TOPMOST if enabled else HWND_NOTOPMOST
            flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
            ctypes.windll.user32.SetWindowPos(hwnd, insert_after, 0, 0, 0, 0, flags)
        except Exception:
            pass

    def open_settings(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title(self.text_for("settings_title"))
        self.settings_window.resizable(False, False)
        self.settings_window.configure(bg="#111310")
        self.settings_window.transient(self.root)
        try:
            self.settings_window.iconbitmap(str(resource_path("icons", "icon.ico")))
        except Exception:
            pass
        self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings)
        self.settings_vars = {}

        options = ttk.Frame(self.settings_window, style="Dark.TFrame")
        options.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 6))
        self.add_settings_checkbutton(options, "auto_start", self.text_for("autostart_checkbox"))
        self.add_settings_checkbutton(options, "auto_minimize", self.text_for("auto_minimize_checkbox"))
        self.add_settings_checkbutton(options, "hide_trader_images", self.text_for("hide_trader_images_checkbox"))
        self.add_settings_checkbutton(options, "show_next_arrival", self.text_for("show_next_arrival_checkbox"))

        traders_title = ttk.Label(
            self.settings_window,
            text=self.text_for("traders_visibility_title"),
            anchor="w",
            style="Dark.TLabel",
        )
        traders_title.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(6, 2))

        traders_frame = ttk.Frame(self.settings_window, style="Dark.TFrame")
        traders_frame.pack(side=tk.TOP, fill=tk.X, padx=10)
        visible = self.config["settings"].get("visible_traders", default_visible_traders())
        for index, (slug, names) in enumerate(TRADERS):
            var = tk.BooleanVar(value=bool(visible.get(slug, True)))
            self.settings_vars["visible_" + slug] = var
            cb = ttk.Checkbutton(
                traders_frame,
                text=self.trader_display_name(slug),
                variable=var,
                command=self.on_settings_changed,
                style="Dark.TCheckbutton",
                takefocus=False,
            )
            cb.grid(row=index // 3, column=index % 3, sticky="w", padx=(0, 14), pady=2)

        close_button = ttk.Button(
            self.settings_window,
            text=self.text_for("settings_close"),
            command=self.close_settings,
            takefocus=False,
        )
        close_button.pack(side=tk.RIGHT, padx=10, pady=10)
        self._ttk_set_no_takefocus(self.settings_window)
        self.position_settings_window()
        self.apply_always_on_top()

    def add_settings_checkbutton(self, parent, key, text):
        var = tk.BooleanVar(value=bool(self.config["settings"].get(key)))
        self.settings_vars[key] = var
        cb = ttk.Checkbutton(
            parent,
            text=text,
            variable=var,
            command=self.on_settings_changed,
            style="Dark.TCheckbutton",
            takefocus=False,
        )
        cb.pack(side=tk.TOP, anchor="w", pady=2)

    def close_settings(self):
        if self.settings_window is not None:
            try:
                self.settings_window.destroy()
            except Exception:
                pass
        self.settings_window = None
        self.settings_vars = {}

    def position_settings_window(self):
        self.settings_window.update_idletasks()
        x, y = self.current_root_position()
        self.settings_window.geometry(f"+{x + 20}+{y + 20}")
        self.settings_window.after(50, self.position_settings_window_once)

    def position_settings_window_once(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            return
        x, y = self.current_root_position()
        self.settings_window.geometry(f"+{x + 20}+{y + 20}")

    def current_root_position(self):
        self.root.update_idletasks()
        try:
            geometry = self.root.wm_geometry()
            position = geometry.rsplit("+", 2)
            if len(position) == 3:
                return int(position[1]), int(position[2])
        except Exception:
            pass
        return self.root.winfo_x(), self.root.winfo_y()

    def on_settings_changed(self):
        settings = self.config["settings"]
        auto_start_var = self.settings_vars.get("auto_start")
        auto_minimize_var = self.settings_vars.get("auto_minimize")
        hide_images_var = self.settings_vars.get("hide_trader_images")
        show_next_var = self.settings_vars.get("show_next_arrival")
        settings["auto_start"] = bool(auto_start_var.get()) if auto_start_var is not None else False
        settings["auto_minimize"] = bool(auto_minimize_var.get()) if auto_minimize_var is not None else False
        settings["hide_trader_images"] = bool(hide_images_var.get()) if hide_images_var is not None else False
        settings["show_next_arrival"] = bool(show_next_var.get()) if show_next_var is not None else False
        visible = {}
        for slug, _names in TRADERS:
            var = self.settings_vars.get("visible_" + slug)
            visible[slug] = True if var is None else bool(var.get())
        if not any(visible.values()):
            first_slug = TRADERS[0][0]
            visible[first_slug] = True
            var = self.settings_vars.get("visible_" + first_slug)
            if var is not None:
                var.set(True)
        settings["visible_traders"] = visible
        set_auto_start(settings["auto_start"])
        save_config(self.config)
        self.apply_visibility()
        self.apply_image_visibility()
        self.update_countdown_labels()

    def apply_language(self):
        self.root.title(self.full_title())
        self.always_on_top_check.configure(text=self.text_for("always_on_top_checkbox"))
        self.language_button.configure(text=self.text_for("language_name"))
        self.game_mode_button.configure(text=self.game_mode_label())
        self.settings_button.configure(text=self.text_for("settings_button"))
        for slug, label in self.name_labels.items():
            label.configure(text=self.trader_display_name(slug))
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.close_settings()
        try:
            if self.tray_icon:
                self.tray_icon.menu = self._tray_build_menu()
                if hasattr(self.tray_icon, "update_menu"):
                    self.tray_icon.update_menu()
                self.tray_icon.title = self.full_title()
        except Exception:
            pass
        self.update_countdown_labels()

    def visible_traders(self):
        visible = self.config["settings"].get("visible_traders", default_visible_traders())
        return [slug for slug, _names in TRADERS if visible.get(slug, True)]

    def apply_visibility(self):
        self.apply_bottom_layout()
        visible = set(self.visible_traders())
        for slug, _names in TRADERS:
            card = self.trader_cards.get(slug)
            if card is None:
                continue
            card.pack_forget()
        for slug, _names in TRADERS:
            if slug in visible and slug in self.trader_cards:
                self.trader_cards[slug].pack(side=tk.LEFT, padx=CARD_PAD_X)
        self.apply_restock_detail_visibility()
        self.apply_image_visibility()
        self.position_window()

    def apply_image_visibility(self):
        hide_images = bool(self.config["settings"].get("hide_trader_images"))
        for label in self.image_labels.values():
            label.pack_forget()
        if not hide_images:
            for slug, _names in TRADERS:
                label = self.image_labels.get(slug)
                if label is not None:
                    label.pack(
                        side=tk.TOP,
                        anchor=tk.CENTER,
                        pady=(IMAGE_TOP_PAD, 0),
                        before=self.name_labels[slug],
                    )

    def apply_restock_detail_visibility(self):
        show_next = bool(self.config["settings"].get("show_next_arrival"))
        extra_lines = int(show_next)
        image_height_delta = HIDDEN_IMAGE_STRIP_HEIGHT if bool(self.config["settings"].get("hide_trader_images")) else 0
        card_height = CARD_HEIGHT - image_height_delta + (RESTOCK_DETAIL_LINE_HEIGHT * extra_lines)
        for card in self.trader_cards.values():
            card.configure(height=card_height)
        for label in self.next_arrival_labels.values():
            label.pack_forget()
        for slug, _names in TRADERS:
            next_label = self.next_arrival_labels.get(slug)
            if show_next and next_label is not None:
                next_label.pack(side=tk.TOP, anchor=tk.CENTER, pady=(0, 0))

    def refresh_reset_times_async(self):
        if self.exiting or self.fetching_reset_times:
            return
        self.fetching_reset_times = True
        threading.Thread(target=self.fetch_reset_times, args=(self.game_mode,), daemon=True).start()

    def fetch_reset_times(self, game_mode):
        next_refresh_ms = 10000
        query = {"query": f"{{ traders(gameMode: {game_mode}) {{ normalizedName resetTime }} }}"}
        try:
            req = urllib.request.Request(
                "https://api.tarkov.dev/graphql",
                data=json.dumps(query).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": HTTP_USER_AGENT},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
            reset_times = {}
            for trader in payload.get("data", {}).get("traders", []):
                if trader.get("normalizedName") in self.countdown_labels and trader.get("resetTime"):
                    reset_times[trader["normalizedName"]] = trader["resetTime"]
            if game_mode == self.game_mode:
                self.reset_times = reset_times
                next_refresh_ms = 5000 if self.has_expired_reset_time() else 60000
            else:
                next_refresh_ms = 0
        except Exception:
            pass
        finally:
            self.fetching_reset_times = False
            self.root.after(0, lambda: self.after_reset_times_updated(next_refresh_ms))

    def after_reset_times_updated(self, next_refresh_ms):
        self.update_countdown_labels()
        if not self.exiting:
            self.root.after(next_refresh_ms, self.refresh_reset_times_async)

    def tick(self):
        self.update_countdown_labels()
        if not self.exiting:
            self.root.after(1000, self.tick)

    def update_countdown_labels(self):
        now = datetime.now(timezone.utc)
        for slug, label in self.countdown_labels.items():
            iso_text = self.reset_times.get(slug)
            label.configure(text=self.format_remaining(iso_text, now))
            arrival_label = self.next_arrival_labels.get(slug)
            if arrival_label is not None:
                arrival_label.configure(text=self.format_next_arrival(iso_text))

    def has_expired_reset_time(self):
        now = datetime.now(timezone.utc)
        for iso_text in self.reset_times.values():
            target = self.parse_reset_time(iso_text)
            if target and target <= now:
                return True
        return False

    def parse_reset_time(self, iso_text):
        try:
            return datetime.fromisoformat(iso_text.replace("Z", "+00:00"))
        except Exception:
            return None

    def format_remaining(self, iso_text, now):
        if not iso_text:
            return "--:--:--"
        target = self.parse_reset_time(iso_text)
        if not target:
            return "--:--:--"
        seconds = int((target - now).total_seconds())
        if seconds <= 0:
            return self.text_for("countdown_updating")
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def format_next_arrival(self, iso_text):
        if not iso_text:
            return ""
        target = self.parse_reset_time(iso_text)
        if not target:
            return ""
        return f"{self.text_for('next_arrival_prefix')} {target.astimezone():%H:%M}"

    def on_unmap(self, _event):
        if not self.exiting and self.root.state() == "iconic":
            self.root.after(0, self.hide_to_tray)

    def hide_to_tray(self):
        try:
            self.root.withdraw()
        except Exception:
            pass

    def position_window(self):
        visible_count = max(1, len(self.visible_traders()) if hasattr(self, "trader_cards") else len(TRADERS))
        width = min(WINDOW_WIDTH, trader_row_content_width(visible_count))
        detail_lines = int(bool(self.config["settings"].get("show_next_arrival")))
        image_height_delta = HIDDEN_IMAGE_STRIP_HEIGHT if bool(self.config["settings"].get("hide_trader_images")) else 0
        stack_extra = BOTTOM_STACK_EXTRA_HEIGHT if self.bottom_layout_is_stacked() else 0
        height = (
            WINDOW_HEIGHT
            - image_height_delta
            + (RESTOCK_DETAIL_LINE_HEIGHT * detail_lines)
            + stack_extra
        )
        geometry = f"{width}x{height}+{WINDOW_X}+{WINDOW_Y}"
        self.root.geometry(geometry)
        self.root.update_idletasks()
        if os.name != "nt":
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            ctypes.windll.user32.SetWindowPos(hwnd, 0, WINDOW_X, WINDOW_Y, 0, 0, 0x0001 | 0x0040)
            ctypes.windll.user32.BringWindowToTop(hwnd)
        except Exception:
            pass

    def restore_window(self):
        try:
            self.root.deiconify()
            self.root.state("normal")
            self.position_window()
            self.root.lift()
            if self.always_on_top_var.get():
                self.apply_always_on_top()
            else:
                self.root.attributes("-topmost", True)
                self.root.after(250, lambda: self.root.attributes("-topmost", False))
            self.root.after(50, self.position_window)
            self.restore_settings_window()
            self.root.focus_force()
        except Exception:
            pass

    def restore_settings_window(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            return
        try:
            self.settings_window.deiconify()
            self.settings_window.state("normal")
            self.position_settings_window_once()
            self.settings_window.lift()
            self.apply_always_on_top()
        except Exception:
            pass

    def _tray_build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                " ",
                lambda _icon, _item: self.root.after(0, self.restore_window),
                default=True,
                visible=False,
            ),
            pystray.MenuItem(
                self.text_for("about"),
                lambda _icon, _item: self.root.after(0, self.open_about),
            ),
            pystray.MenuItem(
                self.text_for("exit"),
                lambda _icon, _item: self.root.after(0, self.exit_app),
            ),
        )

    def start_tray(self):
        try:
            image = Image.open(resource_path("icons", "icon.png"))
        except Exception:
            try:
                image = Image.open(resource_path("icons", "icon.ico"))
            except Exception:
                image = Image.new("RGBA", (64, 64), (30, 30, 30, 255))
        self.tray_icon = pystray.Icon(
            APP_SHORT_NAME,
            image,
            self.full_title(),
            self._tray_build_menu(),
        )
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()

    def open_about(self):
        try:
            webbrowser.open(ABOUT_URL)
        except Exception:
            pass

    def exit_app(self):
        if self.exiting:
            return
        self.exiting = True
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass


def main():
    mh = bm_single_instance.acquire_or_handshake(SINGLE_APP_ID)
    if not mh:
        return
    root = tk.Tk()
    apply_default_font_size(root)
    TraderTimerApp(root, mh)
    try:
        root.mainloop()
    finally:
        bm_single_instance.release_mutex(mh)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
