import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import datetime
import os
import sys
import time
import threading
import shutil
import random
import math
from PIL import Image, ImageTk, ImageDraw
import ctypes
from ctypes import wintypes
from pystray import Icon, MenuItem as Item, Menu
from screeninfo import get_monitors
import darkdetect

# ===================== Windows GDI 截图核心 =====================
user32 = ctypes.WinDLL('user32', use_last_error=True)
gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)

SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB = 0


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD)
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def capture_screen_gdi(x, y, width, height):
    try:
        hdc_screen = user32.GetDC(0)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        hbitmap = gdi32.CreateCompatibleBitmap(hdc_screen, width, height)
        gdi32.SelectObject(hdc_mem, hbitmap)
        gdi32.BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, x, y, SRCCOPY)

        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = BI_RGB
        bmi.bmiHeader.biSizeImage = width * height * 4

        buf_size = width * height * 4
        buf = ctypes.create_string_buffer(buf_size)
        gdi32.GetDIBits(hdc_mem, hbitmap, 0, height, buf, ctypes.byref(bmi), DIB_RGB_COLORS)

        gdi32.DeleteObject(hbitmap)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)

        img = Image.frombytes("RGBA", (width, height), buf, "raw", "BGRA")
        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
        rgb_img.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
        return rgb_img
    except:
        try:
            import pyautogui
            return pyautogui.screenshot(region=(x, y, width, height))
        except:
            return Image.new("RGB", (width, height), (128, 128, 128))


# ===================== 资源路径 =====================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ===================== 系统API =====================
user32_old = ctypes.WinDLL('user32', use_last_error=True)
SPI_GETWORKAREA = 0x0030


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


def get_work_area():
    rect = RECT()
    user32_old.SystemParametersInfoA(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
    return rect.left, rect.top, rect.right, rect.bottom


# ===================== 主题配置 =====================
class ThemeManager:
    LIGHT = {
        "bg": "#F5F7FA",
        "fg": "#1E1E1E",
        "frame_bg": "#FFFFFF",
        "frame_fg": "#2C3E50",
        "entry_bg": "#FFFFFF",
        "entry_fg": "#1E1E1E",
        "entry_border": "#D0D7DE",
        "primary": "#4A90E2",
        "primary_hover": "#5BA0F5",
        "danger": "#E74C3C",
        "warning": "#F39C12",
        "success": "#27AE60",
        "border": "#E1E4E8",
        "list_bg": "#FFFFFF",
        "list_fg": "#1E1E1E",
        "list_select": "#4A90E2",
        "list_select_fg": "#FFFFFF",
        "status_run": "#27AE60",
        "status_stop": "#E74C3C",
        "placeholder": "#8B949E",
        "edit_bg": "#FFFDE7",
        "edit_fg": "#1E1E1E",
        "scrollbar_bg": "#D0D7DE",
        "ball_color": (74, 144, 226),
        "empty_text": "#8B949E",
        "stop_btn_enabled_bg": "#E74C3C",
        "stop_btn_enabled_fg": "#FFFFFF",
        "stop_btn_disabled_bg": "#E1E4E8",
        "stop_btn_disabled_fg": "#8B949E",
        "status_label_bg": "#FFFFFF",
        "path_entry_fg": "#1E1E1E",
        "header_fg": "#2C3E50",
    }

    DARK = {
        "bg": "#1A1E24",
        "fg": "#E6E6E6",
        "frame_bg": "#21262D",
        "frame_fg": "#E6E6E6",
        "entry_bg": "#161B22",
        "entry_fg": "#E6E6E6",
        "entry_border": "#30363D",
        "primary": "#388BFD",
        "primary_hover": "#58A6FF",
        "danger": "#F85149",
        "warning": "#D29922",
        "success": "#3FB950",
        "border": "#30363D",
        "list_bg": "#161B22",
        "list_fg": "#E6E6E6",
        "list_select": "#388BFD",
        "list_select_fg": "#FFFFFF",
        "status_run": "#3FB950",
        "status_stop": "#F85149",
        "placeholder": "#6E7681",
        "edit_bg": "#1F2A3A",
        "edit_fg": "#E6E6E6",
        "scrollbar_bg": "#30363D",
        "ball_color": (56, 139, 253),
        "empty_text": "#8B949E",
        "stop_btn_enabled_bg": "#F85149",
        "stop_btn_enabled_fg": "#FFFFFF",
        "stop_btn_disabled_bg": "#30363D",
        "stop_btn_disabled_fg": "#8B949E",
        "status_label_bg": "#21262D",
        "path_entry_fg": "#E6E6E6",
        "header_fg": "#E6E6E6",
    }

    def __init__(self):
        try:
            is_dark = darkdetect.isDark()
        except:
            is_dark = False
        self.is_dark = is_dark
        self.manual_override = False
        self.current = self.DARK if self.is_dark else self.LIGHT

    def toggle(self):
        self.is_dark = not self.is_dark
        self.manual_override = True
        self.current = self.DARK if self.is_dark else self.LIGHT
        return self.current

    def set_theme(self, is_dark):
        self.is_dark = is_dark
        self.current = self.DARK if self.is_dark else self.LIGHT
        return self.current

    def sync_with_system(self):
        if not self.manual_override:
            try:
                system_is_dark = darkdetect.isDark()
                if system_is_dark != self.is_dark:
                    self.is_dark = system_is_dark
                    self.current = self.DARK if self.is_dark else self.LIGHT
                    return True
            except:
                pass
        return False


# ===================== 可编辑的规则列表 =====================
class EditableRuleListbox(tk.Frame):
    def __init__(self, master, theme, font_size, main_app, **kwargs):
        super().__init__(master, bg=theme["frame_bg"])
        self.theme = theme
        self.font_size = font_size
        self.main_app = main_app
        self.check_vars = {}
        self.rule_items = []
        self.editing_index = None
        self.edit_widgets = {}

        self.build_ui()

    def build_ui(self):
        self.select_all_var = tk.BooleanVar(value=False)
        self.select_all_cb = tk.Checkbutton(
            self, text="全选", variable=self.select_all_var,
            command=self.toggle_select_all,
            bg=self.theme["frame_bg"], fg=self.theme["fg"],
            selectcolor=self.theme["frame_bg"],
            activebackground=self.theme["frame_bg"],
            font=("", self.font_size - 1)
        )
        self.select_all_cb.pack(anchor="w", padx=5, pady=2)

        separator = tk.Frame(self, height=1, bg=self.theme["border"])
        separator.pack(fill="x", padx=5, pady=2)

        list_container = tk.Frame(self, bg=self.theme["frame_bg"])
        list_container.pack(fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(list_container, bg=self.theme["scrollbar_bg"],
                                      troughcolor=self.theme["frame_bg"])
        self.scrollbar.pack(side="right", fill="y")

        self.canvas = tk.Canvas(list_container, bg=self.theme["frame_bg"],
                                highlightthickness=0,
                                yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.canvas.yview)

        self.rules_frame = tk.Frame(self.canvas, bg=self.theme["frame_bg"])
        self.canvas_window = self.canvas.create_window((0, 0), window=self.rules_frame, anchor="nw")

        self.rules_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def toggle_select_all(self):
        select_all = self.select_all_var.get()
        for var in self.check_vars.values():
            var.set(select_all)

    def finish_editing(self):
        if self.editing_index is not None:
            self.save_edit()

    def save_edit(self):
        if self.editing_index is None:
            return

        idx = self.editing_index
        start_entry = self.edit_widgets.get('start')
        end_entry = self.edit_widgets.get('end')
        interval_entry = self.edit_widgets.get('interval')

        if not all([start_entry, end_entry, interval_entry]):
            self.cancel_edit()
            return

        new_start = start_entry.get().strip()
        new_end = end_entry.get().strip()
        new_interval = interval_entry.get().strip()

        try:
            datetime.datetime.strptime(new_start, "%H:%M")
            datetime.datetime.strptime(new_end, "%H:%M")
            new_interval_int = int(new_interval)
            if new_interval_int < 3:
                messagebox.showwarning("提示", "截图间隔不能小于3秒")
                return
        except ValueError:
            messagebox.showerror("格式错误", "时间格式应为 HH:MM，间隔为数字")
            return

        conflict_result = self.main_app.check_rule_overlap_except(new_start, new_end, idx)
        if conflict_result:
            is_valid, conflict_rule = conflict_result
            if not is_valid:
                messagebox.showwarning(
                    "时段冲突",
                    f"修改后的规则与现有规则时间重叠！\n\n"
                    f"冲突规则：{conflict_rule['start']} ~ {conflict_rule['end']}"
                )
                return

        old_rule = self.rule_items[idx]
        old_rule["start"] = new_start
        old_rule["end"] = new_end
        old_rule["interval"] = new_interval_int

        self.cancel_edit()
        self.refresh_rules(self.rule_items)
        messagebox.showinfo("成功", "规则已更新")

    def cancel_edit(self):
        self.editing_index = None
        self.edit_widgets.clear()

    def start_edit(self, idx):
        if self.editing_index is not None:
            self.save_edit()

        self.editing_index = idx
        self.refresh_rules(self.rule_items)

    def update_theme(self, theme):
        self.theme = theme
        self.configure(bg=theme["frame_bg"])
        self.select_all_cb.config(bg=theme["frame_bg"], fg=theme["fg"],
                                  selectcolor=theme["frame_bg"],
                                  activebackground=theme["frame_bg"])
        self.canvas.config(bg=theme["frame_bg"])
        self.rules_frame.config(bg=theme["frame_bg"])
        self.refresh_rules(self.rule_items)

    def refresh_rules(self, rules):
        for widget in self.rules_frame.winfo_children():
            widget.destroy()
        self.check_vars.clear()
        self.rule_items = rules.copy()

        if not rules:
            empty_label = tk.Label(self.rules_frame, text="暂无规则，请添加",
                                   bg=self.theme["frame_bg"], fg=self.theme["empty_text"],
                                   font=("", self.font_size))
            empty_label.pack(pady=20)
            self.select_all_cb.config(state="disabled")
            return

        self.select_all_cb.config(state="normal")
        self.select_all_var.set(False)

        header_frame = tk.Frame(self.rules_frame, bg=self.theme["frame_bg"])
        header_frame.pack(fill="x", pady=2)

        headers = [("选择", 4), ("开始时间", 10), ("结束时间", 10), ("间隔(秒)", 8), ("操作", 6)]
        for text, width in headers:
            tk.Label(header_frame, text=text, width=width,
                     bg=self.theme["frame_bg"], fg=self.theme["header_fg"],
                     font=("", self.font_size - 1, "bold")).pack(side="left", padx=2)

        sep = tk.Frame(self.rules_frame, height=1, bg=self.theme["border"])
        sep.pack(fill="x", pady=2)

        sorted_rules = sorted(rules, key=lambda x: x["start"])
        for display_idx, rule in enumerate(sorted_rules):
            original_idx = self.rule_items.index(rule)
            self.add_rule_row(rule, original_idx, display_idx == self.editing_index)

        self.rule_items = sorted_rules

    def add_rule_row(self, rule, idx, is_editing=False):
        row_frame = tk.Frame(self.rules_frame, bg=self.theme["frame_bg"])
        row_frame.pack(fill="x", pady=1)

        var = tk.BooleanVar(value=False)
        self.check_vars[idx] = var
        cb = tk.Checkbutton(row_frame, variable=var,
                            bg=self.theme["frame_bg"],
                            selectcolor=self.theme["frame_bg"],
                            activebackground=self.theme["frame_bg"])
        cb.pack(side="left", padx=2)

        if is_editing:
            start_entry = tk.Entry(row_frame, width=10, font=("", self.font_size - 1),
                                   bg=self.theme["edit_bg"], fg=self.theme["edit_fg"],
                                   insertbackground=self.theme["fg"],
                                   relief="solid", bd=1)
            start_entry.insert(0, rule["start"])
            start_entry.pack(side="left", padx=2)
            self.edit_widgets['start'] = start_entry

            end_entry = tk.Entry(row_frame, width=10, font=("", self.font_size - 1),
                                 bg=self.theme["edit_bg"], fg=self.theme["edit_fg"],
                                 insertbackground=self.theme["fg"],
                                 relief="solid", bd=1)
            end_entry.insert(0, rule["end"])
            end_entry.pack(side="left", padx=2)
            self.edit_widgets['end'] = end_entry

            interval_entry = tk.Entry(row_frame, width=8, font=("", self.font_size - 1),
                                      bg=self.theme["edit_bg"], fg=self.theme["edit_fg"],
                                      insertbackground=self.theme["fg"],
                                      relief="solid", bd=1)
            interval_entry.insert(0, str(rule["interval"]))
            interval_entry.pack(side="left", padx=2)
            self.edit_widgets['interval'] = interval_entry

            btn_frame = tk.Frame(row_frame, bg=self.theme["frame_bg"])
            btn_frame.pack(side="left", padx=2)

            tk.Button(btn_frame, text="✓", command=self.save_edit,
                      bg=self.theme["success"], fg="white", font=("", 8),
                      width=2, relief="flat", cursor="hand2").pack(side="left", padx=1)
            tk.Button(btn_frame, text="✗", command=self.cancel_edit,
                      bg=self.theme["danger"], fg="white", font=("", 8),
                      width=2, relief="flat", cursor="hand2").pack(side="left", padx=1)

            start_entry.bind("<Return>", lambda e: self.save_edit())
            end_entry.bind("<Return>", lambda e: self.save_edit())
            interval_entry.bind("<Return>", lambda e: self.save_edit())
            start_entry.bind("<Escape>", lambda e: self.cancel_edit())

            start_entry.focus()
        else:
            tk.Label(row_frame, text=rule["start"], width=10,
                     bg=self.theme["frame_bg"], fg=self.theme["list_fg"],
                     font=("", self.font_size - 1)).pack(side="left", padx=2)

            tk.Label(row_frame, text=rule["end"], width=10,
                     bg=self.theme["frame_bg"], fg=self.theme["list_fg"],
                     font=("", self.font_size - 1)).pack(side="left", padx=2)

            tk.Label(row_frame, text=str(rule["interval"]), width=8,
                     bg=self.theme["frame_bg"], fg=self.theme["list_fg"],
                     font=("", self.font_size - 1)).pack(side="left", padx=2)

            edit_btn = tk.Button(row_frame, text="✎", command=lambda i=idx: self.start_edit(i),
                                 bg=self.theme["primary"], fg="white", font=("", 8),
                                 width=2, relief="flat", cursor="hand2")
            edit_btn.pack(side="left", padx=2)

    def get_selected_rules(self):
        selected = []
        for idx, var in self.check_vars.items():
            if var.get():
                selected.append(idx)
        return selected


# ===================== 时间选择器 =====================
class TimePicker(tk.Toplevel):
    def __init__(self, parent, theme, initial_time=None):
        super().__init__(parent)
        self.theme = theme
        self.result = None
        self.title("选择时间")
        self.geometry("350x320")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=theme["frame_bg"])

        if initial_time is None:
            now = datetime.datetime.now()
            initial_time = f"{now.hour:02d}:{now.minute:02d}"

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 350) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 320) // 2
        self.geometry(f"+{x}+{y}")

        self.build_ui(initial_time)

    def build_ui(self, initial_time):
        bg = self.theme["frame_bg"]
        fg = self.theme["fg"]

        tk.Label(self, text="⏰ 选择时间", font=("", 14, "bold"), bg=bg, fg=fg).pack(pady=15)

        time_frame = tk.Frame(self, bg=bg)
        time_frame.pack(pady=10)
        self.hour_var = tk.StringVar(value=initial_time.split(":")[0])
        self.minute_var = tk.StringVar(value=initial_time.split(":")[1])

        hour_spin = tk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var,
                               width=5, font=("", 18), justify="center",
                               bg=self.theme["entry_bg"], fg=fg, relief="flat",
                               buttonbackground=self.theme["primary"])
        hour_spin.pack(side="left", padx=8)
        tk.Label(time_frame, text=":", font=("", 18, "bold"), bg=bg, fg=fg).pack(side="left")
        minute_spin = tk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var,
                                 width=5, font=("", 18), justify="center",
                                 bg=self.theme["entry_bg"], fg=fg, relief="flat",
                                 buttonbackground=self.theme["primary"])
        minute_spin.pack(side="left", padx=8)

        tk.Label(self, text="快捷选择", font=("", 10), bg=bg, fg=fg).pack(pady=(15, 5))
        btn_frame = tk.Frame(self, bg=bg)
        btn_frame.pack(pady=5)
        times = ["06:00", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00"]
        for i, t in enumerate(times):
            btn = tk.Button(btn_frame, text=t, width=7,
                            command=lambda x=t: self.set_time(x),
                            bg=self.theme["primary"], fg="white", relief="flat", cursor="hand2")
            btn.grid(row=i // 3, column=i % 3, padx=4, pady=4)

        action_frame = tk.Frame(self, bg=bg)
        action_frame.pack(pady=15)
        tk.Button(action_frame, text="取消", command=self.cancel, width=12,
                  bg=self.theme["border"], fg=self.theme["fg"], relief="flat", cursor="hand2").pack(side="left", padx=8)
        tk.Button(action_frame, text="确认", command=self.confirm, width=12,
                  bg=self.theme["primary"], fg="white", relief="flat", cursor="hand2").pack(side="left", padx=8)

    def set_time(self, time_str):
        h, m = time_str.split(":")
        self.hour_var.set(h)
        self.minute_var.set(m)

    def confirm(self):
        try:
            h = int(self.hour_var.get())
            m = int(self.minute_var.get())
            if 0 <= h <= 23 and 0 <= m <= 59:
                self.result = f"{h:02d}:{m:02d}"
                self.destroy()
            else:
                messagebox.showwarning("提示", "时间范围: 00:00 - 23:59")
        except:
            messagebox.showwarning("提示", "请输入有效的时间")

    def cancel(self):
        self.destroy()


# ===================== 时间输入框 =====================
class TimeInput(tk.Frame):
    def __init__(self, master, theme, placeholder="HH:MM"):
        super().__init__(master, bg=theme["frame_bg"])
        self.theme = theme

        default_time = datetime.datetime.now().strftime("%H:%M")

        self.entry = tk.Entry(self, width=9, bg=theme["entry_bg"], fg=theme["entry_fg"],
                              relief="solid", bd=1, insertbackground=theme["fg"])
        self.entry.pack(side="left", padx=(0, 5))
        self.entry.insert(0, default_time)

        self.btn = tk.Button(self, text="🕐", width=2, command=self.open_picker,
                             bg=theme["primary"], fg="white", relief="flat", cursor="hand2",
                             font=("", 9))
        self.btn.pack(side="left")

    def open_picker(self):
        current = self.get()
        try:
            datetime.datetime.strptime(current, "%H:%M")
        except:
            current = datetime.datetime.now().strftime("%H:%M")
        dialog = TimePicker(self.winfo_toplevel(), self.theme, current)
        self.wait_window(dialog)
        if dialog.result:
            self.set(dialog.result)

    def get(self):
        return self.entry.get()

    def set(self, v):
        self.entry.delete(0, "end")
        self.entry.insert(0, v)


# ===================== 悬浮球 =====================
class GlassFloatBall:
    def __init__(self, root, main_app, theme):
        self.root = root
        self.main_app = main_app
        self.theme = theme
        self.SIZE = 70
        self.RADIUS = self.SIZE // 2 - 2
        self.ripples = []
        self.raindrops = []
        self.animating = True
        self.monitors = get_monitors()
        self.update_work_areas()
        self.dragging = False
        self.pressing = False
        self.phase = 0

        self.ball = tk.Toplevel(root)
        self.ball.overrideredirect(True)
        self.ball.attributes("-topmost", True)
        self.ball.attributes("-alpha", 1.0)
        self.ball.config(bg="#000000")
        self.ball.attributes("-transparentcolor", "#000000")
        self.ball.geometry(f"{self.SIZE}x{self.SIZE}")
        self.ball.withdraw()

        self.canvas = tk.Canvas(self.ball, width=self.SIZE, height=self.SIZE,
                                bg="#000000", bd=0, highlightthickness=0)
        self.canvas.pack()
        self.x = self.monitors[0].x + 100
        self.y = self.monitors[0].y + (self.monitors[0].height - self.SIZE) // 2

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.show_main)
        self.animate()

    def update_work_areas(self):
        self.work_areas = []
        for m in get_monitors():
            wl, wt, wr, wb = get_work_area()
            l = max(m.x, wl)
            t = max(m.y, wt)
            r = min(m.x + m.width, wr)
            b = min(m.y + m.height, wb)
            self.work_areas.append((l, t, r, b))

    def animate(self):
        if self.animating:
            self.phase += 0.1
            if self.main_app.running:
                self.update_raindrops()
            else:
                self.update_ripples()
            self.draw_ball()
        self.root.after(40, self.animate)

    def update_ripples(self):
        if random.random() < 0.06:
            self.ripples.append({
                'r': 4,
                'max_r': self.RADIUS * 0.75,
                'speed': 1.5,
                'alpha': 255
            })
        new_r = []
        for r in self.ripples:
            r['r'] += r['speed']
            r['alpha'] = max(0, int(255 * (1 - r['r'] / r['max_r'])))
            if r['r'] < r['max_r']:
                new_r.append(r)
        self.ripples = new_r

    def update_raindrops(self):
        self.ripples.clear()
        if random.random() < 0.2:
            cx, cy = self.SIZE // 2, self.SIZE // 2
            x = random.randint(cx - 22, cx + 22)
            y = cy - 25
            self.raindrops.append({
                'x': x, 'y': y,
                'speed': random.uniform(3, 5),
                'len': random.randint(5, 9),
                'alpha': 255
            })
        new_d = []
        for d in self.raindrops:
            d['y'] += d['speed']
            if math.hypot(d['x'] - self.SIZE // 2, d['y'] - self.SIZE // 2) < self.RADIUS - 3:
                new_d.append(d)
        self.raindrops = new_d[:20]

    def draw_ball(self):
        img = Image.new("RGBA", (self.SIZE, self.SIZE), (255, 0, 255, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = self.SIZE // 2, self.SIZE // 2

        ball_color = self.theme.get("ball_color", (80, 180, 250))
        if self.main_app.running:
            ball_color = tuple(max(0, c - 15) for c in ball_color)
        if self.pressing:
            ball_color = tuple(min(255, c + 15) for c in ball_color)

        draw.ellipse((cx - self.RADIUS, cy - self.RADIUS,
                      cx + self.RADIUS, cy + self.RADIUS),
                     fill=ball_color)

        draw.ellipse((cx - self.RADIUS, cy - self.RADIUS,
                      cx + self.RADIUS, cy + self.RADIUS),
                     outline=(255, 255, 255, 60), width=1)

        if self.main_app.running:
            for d in self.raindrops:
                draw.line((d['x'], d['y'], d['x'], d['y'] + d['len']),
                          fill=(255, 255, 255, d['alpha']), width=1)
                head_y = d['y'] + d['len']
                if math.hypot(d['x'] - cx, head_y - cy) < self.RADIUS - 2:
                    draw.ellipse((d['x'] - 1, head_y - 1, d['x'] + 1, head_y + 1),
                                 fill=(255, 255, 255, d['alpha']))
        else:
            for r in self.ripples:
                radius = r['r']
                alpha = r['alpha']
                draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                             outline=(255, 255, 255, alpha), width=2)

        self.ball_img = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.ball_img, anchor="nw")

    def snap_to_edge(self):
        self.update_work_areas()
        best_x, best_y = self.x, self.y
        min_dist = float('inf')

        for l, t, r, b in self.work_areas:
            if l <= self.x <= r - self.SIZE and t <= self.y <= b - self.SIZE:
                return

            candidates = [
                (l + 5, max(t + 5, min(b - self.SIZE - 5, self.y))),
                (r - self.SIZE - 5, max(t + 5, min(b - self.SIZE - 5, self.y))),
                (max(l + 5, min(r - self.SIZE - 5, self.x)), t + 5),
                (max(l + 5, min(r - self.SIZE - 5, self.x)), b - self.SIZE - 5)
            ]

            for ex, ey in candidates:
                dist = math.sqrt((self.x - ex) ** 2 + (self.y - ey) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    best_x, best_y = ex, ey

        self.x, self.y = best_x, best_y
        self.ball.geometry(f"+{int(self.x)}+{int(self.y)}")

    def on_press(self, e):
        self.pressing = True
        self.start_x, self.start_y = e.x, e.y

    def on_drag(self, e):
        self.dragging = True
        self.x += e.x - self.start_x
        self.y += e.y - self.start_y
        self.ball.geometry(f"+{int(self.x)}+{int(self.y)}")

    def on_release(self, e):
        self.pressing = False
        self.dragging = False
        self.snap_to_edge()

    def show_main(self, e=None):
        self.root.after(0, self.main_app.deiconify)
        self.hide()

    def show(self):
        self.ball.deiconify()
        self.ball.geometry(f"+{int(self.x)}+{int(self.y)}")
        self.animating = True

    def hide(self):
        self.ball.withdraw()
        self.animating = False

    def update_theme(self, theme):
        self.theme = theme


# ===================== 主界面 =====================
class ScreenshotTool(tk.Tk):
    def __init__(self):
        super().__init__()

        self.withdraw()

        self.theme_manager = ThemeManager()
        self.theme = self.theme_manager.current
        self.dpi_scale = self._get_dpi_scale()
        self.font_size = max(10, min(13, int(11 * self.dpi_scale)))
        self.title_font_size = int(16 * self.dpi_scale)

        self.window_width = 720
        self.window_height = 800
        self.minsize(680, 750)

        self.title("分时段自动截屏工具")

        self.icon_path = resource_path("icon.ico")
        try:
            self.iconbitmap(self.icon_path)
        except:
            pass

        self.configure(bg=self.theme["bg"])
        self.resizable(True, True)

        self.fullscreen_flag = False
        self.running = False
        self.tray_icon = None
        self.save_path = tk.StringVar(value="未选择保存目录")
        self.default_interval = tk.StringVar(value="60")
        self.name_mode = tk.StringVar(value="时间戳")
        self.schedule_rules = []
        self.last_shot_count = 0
        self.last_total_size = 0

        self.bind("<F11>", self.toggle_fullscreen)
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.bind("<Unmap>", lambda e: self.minimize_to_tray() if self.state() == "iconic" else None)
        self.bind("<Map>", self.on_window_map)

        self.build_ui()
        self.apply_theme()

        self._center_window()
        self.update_idletasks()
        self.update()
        self.deiconify()

        self.float_ball = GlassFloatBall(self, self, self.theme)
        self.init_tray_icon()
        self.refresh_rule_list()
        self.update_monitor_info()
        self.update_ui_info()

        self.check_system_theme()

    def _get_dpi_scale(self):
        try:
            return self.winfo_fpixels('1i') / 96
        except:
            return 1.0

    def _center_window(self):
        self.update_idletasks()
        m = get_monitors()[0]

        self.geometry(f"{self.window_width}x{self.window_height}")

        x = m.x + (m.width - self.window_width) // 2
        y = m.y + (m.height - self.window_height) // 2

        if y < m.y:
            y = m.y + 10
        if y + self.window_height > m.y + m.height:
            y = m.y + m.height - self.window_height - 10

        self.geometry(f"+{x}+{y}")
        self.update()

    def check_system_theme(self):
        if self.theme_manager.sync_with_system():
            self.theme = self.theme_manager.current
            self.apply_theme()
            self.status_label.config(fg=self.theme["status_run"] if self.running else self.theme["status_stop"])
            if hasattr(self, 'float_ball'):
                self.float_ball.update_theme(self.theme)
            self.rule_listbox.update_theme(self.theme)
        self.after(2000, self.check_system_theme)

    def on_window_map(self, event):
        if hasattr(self, 'float_ball'):
            self.float_ball.hide()

    def apply_theme(self):
        t = self.theme
        self.configure(bg=t["bg"])

        # 更新主题按钮
        self.theme_btn.config(text="🌙" if not self.theme_manager.is_dark else "☀️",
                              bg=t["primary"])

        # 更新所有组件
        for w in self.winfo_children():
            self._apply_theme(w, t)

        # 专门更新状态标签
        self.status_label.config(bg=t["status_label_bg"],
                                 fg=t["status_stop"] if not self.running else t["status_run"])

        # 更新停止按钮
        if self.running:
            self.stop_btn.config(bg=t["stop_btn_enabled_bg"], fg=t["stop_btn_enabled_fg"])
        else:
            self.stop_btn.config(bg=t["stop_btn_disabled_bg"], fg=t["stop_btn_disabled_fg"])
            self.start_btn.config(bg=t["primary"], fg="white")

    def _apply_theme(self, w, t):
        try:
            if isinstance(w, (tk.Frame, tk.LabelFrame)):
                w.config(bg=t["frame_bg"])
                if isinstance(w, tk.LabelFrame):
                    w.config(fg=t["frame_fg"])
            elif isinstance(w, tk.Label):
                if w == self.status_label:
                    w.config(bg=t["status_label_bg"])
                else:
                    w.config(bg=w.master["bg"], fg=t["fg"])
            elif isinstance(w, tk.Entry):
                if w.cget('state') == 'readonly':
                    w.config(readonlybackground=t["entry_bg"], fg=t["path_entry_fg"])
                else:
                    w.config(bg=t["entry_bg"], fg=t["entry_fg"], relief="solid", bd=1,
                             insertbackground=t["fg"])
            elif isinstance(w, tk.Button):
                if w == self.stop_btn:
                    if w.cget('state') == 'disabled':
                        w.config(bg=t["stop_btn_disabled_bg"], fg=t["stop_btn_disabled_fg"])
                    else:
                        w.config(bg=t["stop_btn_enabled_bg"], fg=t["stop_btn_enabled_fg"])
                elif w == self.start_btn:
                    if w.cget('state') != 'disabled':
                        w.config(bg=t["primary"], fg="white")
                elif w == self.theme_btn:
                    w.config(bg=t["primary"])
                elif w not in [self.theme_btn]:
                    w.config(relief="flat", cursor="hand2")
            elif isinstance(w, tk.Checkbutton):
                w.config(bg=t["frame_bg"], fg=t["fg"], selectcolor=t["frame_bg"],
                         activebackground=t["frame_bg"])
            elif isinstance(w, ttk.Combobox):
                style = ttk.Style()
                style.map('TCombobox', fieldbackground=[('readonly', t["entry_bg"])])
                style.map('TCombobox', foreground=[('readonly', t["fg"])])
        except:
            pass
        for c in w.winfo_children():
            self._apply_theme(c, t)

    def toggle_theme(self):
        self.theme = self.theme_manager.toggle()
        self.apply_theme()
        if hasattr(self, 'float_ball'):
            self.float_ball.update_theme(self.theme)
        self.rule_listbox.update_theme(self.theme)
        self.refresh_rule_list()

    def check_rule_overlap(self, new_start, new_end):
        new_s = datetime.datetime.strptime(new_start, "%H:%M")
        new_e = datetime.datetime.strptime(new_end, "%H:%M")

        if new_e <= new_s:
            new_e += datetime.timedelta(days=1)

        for rule in self.schedule_rules:
            exist_s = datetime.datetime.strptime(rule["start"], "%H:%M")
            exist_e = datetime.datetime.strptime(rule["end"], "%H:%M")

            if exist_e <= exist_s:
                exist_e += datetime.timedelta(days=1)

            if new_s < exist_e and new_e > exist_s:
                return False, rule

        return True, None

    def check_rule_overlap_except(self, new_start, new_end, exclude_index):
        new_s = datetime.datetime.strptime(new_start, "%H:%M")
        new_e = datetime.datetime.strptime(new_end, "%H:%M")

        if new_e <= new_s:
            new_e += datetime.timedelta(days=1)

        for idx, rule in enumerate(self.schedule_rules):
            if idx == exclude_index:
                continue

            exist_s = datetime.datetime.strptime(rule["start"], "%H:%M")
            exist_e = datetime.datetime.strptime(rule["end"], "%H:%M")

            if exist_e <= exist_s:
                exist_e += datetime.timedelta(days=1)

            if new_s < exist_e and new_e > exist_s:
                return False, rule

        return True, None

    def add_schedule_rule(self):
        start = self.entry_start.get().strip()
        end = self.entry_end.get().strip()
        interval = self.entry_interval.get().strip()

        if not all([start, end, interval]):
            messagebox.showwarning("提示", "请填写完整信息")
            return

        try:
            datetime.datetime.strptime(start, "%H:%M")
            datetime.datetime.strptime(end, "%H:%M")
            interval = int(interval)
            if interval < 3:
                messagebox.showwarning("提示", "截图间隔不能小于3秒")
                return
        except ValueError:
            messagebox.showerror("格式错误", "时间格式应为 HH:MM，间隔为数字")
            return

        is_valid, conflict_rule = self.check_rule_overlap(start, end)
        if not is_valid:
            messagebox.showwarning(
                "时段冲突",
                f"新规则与现有规则时间重叠！\n\n"
                f"冲突规则：{conflict_rule['start']} ~ {conflict_rule['end']}"
            )
            return

        self.schedule_rules.append({"start": start, "end": end, "interval": interval})
        self.refresh_rule_list()

        self.entry_start.set(datetime.datetime.now().strftime("%H:%M"))
        self.entry_end.set("18:00")
        self.entry_interval.delete(0, "end")
        self.entry_interval.insert(0, "60")

    def delete_selected_rules(self):
        self.rule_listbox.finish_editing()

        selected = self.rule_listbox.get_selected_rules()
        if not selected:
            messagebox.showinfo("提示", "请先选中要删除的规则")
            return

        count = len(selected)
        if messagebox.askyesno("确认删除", f"确定要删除选中的 {count} 条规则吗？"):
            for idx in sorted(selected, reverse=True):
                if idx < len(self.schedule_rules):
                    del self.schedule_rules[idx]
            self.refresh_rule_list()
            messagebox.showinfo("成功", f"已删除 {count} 条规则")

    def delete_all_rules(self):
        self.rule_listbox.finish_editing()

        if not self.schedule_rules:
            messagebox.showinfo("提示", "暂无规则可删除")
            return

        count = len(self.schedule_rules)
        if messagebox.askyesno("确认删除", f"确定要删除全部 {count} 条规则吗？"):
            self.schedule_rules.clear()
            self.refresh_rule_list()
            messagebox.showinfo("成功", f"已删除全部 {count} 条规则")

    def refresh_rule_list(self):
        self.rule_listbox.refresh_rules(self.schedule_rules)

    def get_current_interval(self):
        now = datetime.datetime.now()
        now_str = now.strftime("%H:%M")
        now_dt = datetime.datetime.strptime(now_str, "%H:%M")

        matching = []
        for r in self.schedule_rules:
            s = datetime.datetime.strptime(r["start"], "%H:%M")
            e = datetime.datetime.strptime(r["end"], "%H:%M")

            if e <= s:
                e += datetime.timedelta(days=1)
                now_check = now_dt + datetime.timedelta(days=1) if now_dt < s else now_dt
            else:
                now_check = now_dt

            if s <= now_check <= e:
                matching.append(r["interval"])

        if matching:
            return min(matching)

        try:
            return int(self.default_interval.get())
        except:
            return 60

    def update_monitor_info(self):
        count = len(get_monitors())
        self.monitor_label.config(text=f"🖥️  检测到 {count} 个显示器")

    def get_disk_free_gb(self):
        try:
            path = self.save_path.get()
            if path == "未选择保存目录":
                return 0
            return shutil.disk_usage(path).free / (1024 ** 3)
        except:
            return 0

    def update_ui_info(self):
        free_gb = self.get_disk_free_gb()
        self.disk_label.config(text=f"💾  磁盘剩余 {free_gb:.1f} GB")

        if self.last_total_size > 0 and free_gb > 0:
            remain = int(free_gb * 1024 ** 3 / self.last_total_size)
            self.remain_label.config(text=f"📊  预计可截 {remain} 次")
        else:
            self.remain_label.config(text="📊  等待首次截图")

    def build_ui(self):
        main = tk.Frame(self, bg=self.theme["bg"])
        main.pack(fill="both", expand=True, padx=10, pady=8)

        # 标题栏 - 使用grid布局确保按钮居中
        tf = tk.Frame(main, bg=self.theme["bg"])
        tf.pack(fill="x", pady=(0, 5))

        # 使用grid布局让标题和按钮都在同一行且垂直居中
        tf.grid_columnconfigure(0, weight=1)
        tf.grid_columnconfigure(1, weight=0)

        tk.Label(tf, text="📸 分时段自动截屏工具", font=("", self.title_font_size, "bold"),
                 bg=self.theme["bg"], fg=self.theme["fg"]).grid(row=0, column=0, sticky="w")

        # 主题按钮 - 固定大小，文字居中
        self.theme_btn = tk.Button(tf, text="🌙" if not self.theme_manager.is_dark else "☀️",
                                   command=self.toggle_theme, width=3, height=1,
                                   bg=self.theme["primary"], fg="white", relief="flat", cursor="hand2",
                                   font=("", 11))
        self.theme_btn.grid(row=0, column=1, sticky="e", padx=(0, 5))

        # 保存设置
        pf = tk.LabelFrame(main, text="📁 保存设置", font=("", self.font_size, "bold"),
                           bg=self.theme["frame_bg"], fg=self.theme["frame_fg"])
        pf.pack(fill="x", pady=3)
        pr = tk.Frame(pf, bg=self.theme["frame_bg"])
        pr.pack(fill="x", padx=6, pady=6)
        tk.Entry(pr, textvariable=self.save_path, state="readonly",
                 font=("", self.font_size), width=35,
                 bg=self.theme["entry_bg"], fg=self.theme["path_entry_fg"],
                 readonlybackground=self.theme["entry_bg"],
                 relief="solid", bd=1).pack(side="left", fill="x", expand=True, padx=3)
        tk.Button(pr, text="浏览", command=self.select_path,
                  bg=self.theme["primary"], fg="white", padx=10, pady=2,
                  font=("", self.font_size - 1)).pack(side="left")

        # 截图设置
        sf = tk.LabelFrame(main, text="⚙️ 截图设置", font=("", self.font_size, "bold"),
                           bg=self.theme["frame_bg"], fg=self.theme["frame_fg"])
        sf.pack(fill="x", pady=3)
        sr = tk.Frame(sf, bg=self.theme["frame_bg"])
        sr.pack(fill="x", padx=6, pady=6)

        tk.Label(sr, text="默认间隔：", bg=self.theme["frame_bg"], fg=self.theme["fg"],
                 font=("", self.font_size)).pack(side="left")
        tk.Entry(sr, textvariable=self.default_interval, width=6,
                 font=("", self.font_size),
                 bg=self.theme["entry_bg"], fg=self.theme["entry_fg"],
                 relief="solid", bd=1).pack(side="left", padx=3)
        tk.Label(sr, text="秒", bg=self.theme["frame_bg"], fg=self.theme["fg"],
                 font=("", self.font_size)).pack(side="left")

        tk.Label(sr, text="命名方式：", bg=self.theme["frame_bg"], fg=self.theme["fg"],
                 font=("", self.font_size)).pack(side="left", padx=(12, 3))
        cb = ttk.Combobox(sr, textvariable=self.name_mode, values=["时间戳", "格式化时间"],
                          state="readonly", width=12, font=("", self.font_size))
        cb.pack(side="left")

        # 分时段规则
        rf = tk.LabelFrame(main, text="⏰ 分时段规则（点击✎编辑）", font=("", self.font_size, "bold"),
                           bg=self.theme["frame_bg"], fg=self.theme["frame_fg"])
        rf.pack(fill="both", expand=True, pady=3)

        inf = tk.Frame(rf, bg=self.theme["frame_bg"])
        inf.pack(fill="x", padx=6, pady=6)

        tk.Label(inf, text="开始：", bg=self.theme["frame_bg"], fg=self.theme["fg"],
                 font=("", self.font_size)).grid(row=0, column=0, padx=2)
        self.entry_start = TimeInput(inf, self.theme)
        self.entry_start.grid(row=0, column=1, padx=2)

        tk.Label(inf, text="结束：", bg=self.theme["frame_bg"], fg=self.theme["fg"],
                 font=("", self.font_size)).grid(row=0, column=2, padx=2)
        self.entry_end = TimeInput(inf, self.theme)
        self.entry_end.set("18:00")
        self.entry_end.grid(row=0, column=3, padx=2)

        tk.Label(inf, text="间隔：", bg=self.theme["frame_bg"], fg=self.theme["fg"],
                 font=("", self.font_size)).grid(row=0, column=4, padx=2)
        self.entry_interval = tk.Entry(inf, width=5, font=("", self.font_size),
                                       bg=self.theme["entry_bg"], fg=self.theme["entry_fg"],
                                       relief="solid", bd=1)
        self.entry_interval.grid(row=0, column=5, padx=2)
        self.entry_interval.insert(0, "60")
        tk.Label(inf, text="秒", bg=self.theme["frame_bg"], fg=self.theme["fg"],
                 font=("", self.font_size)).grid(row=0, column=6, padx=2)

        bf = tk.Frame(rf, bg=self.theme["frame_bg"])
        bf.pack(fill="x", padx=6, pady=3)

        tk.Button(bf, text="➕ 添加", command=self.add_schedule_rule,
                  bg=self.theme["primary"], fg="white", font=("", self.font_size - 1),
                  padx=6, pady=1, relief="flat", cursor="hand2").pack(side="left", padx=2)
        tk.Button(bf, text="🗑️ 删除选中", command=self.delete_selected_rules,
                  bg=self.theme["danger"], fg="white", font=("", self.font_size - 1),
                  padx=6, pady=1, relief="flat", cursor="hand2").pack(side="left", padx=2)
        tk.Button(bf, text="🧹 删除全部", command=self.delete_all_rules,
                  bg=self.theme["warning"], fg="white", font=("", self.font_size - 1),
                  padx=6, pady=1, relief="flat", cursor="hand2").pack(side="left", padx=2)

        self.rule_listbox = EditableRuleListbox(rf, self.theme, self.font_size, self)
        self.rule_listbox.pack(fill="both", expand=True, padx=6, pady=(2, 6))

        # 状态信息
        stf = tk.LabelFrame(main, text="📊 运行状态", font=("", self.font_size, "bold"),
                            bg=self.theme["frame_bg"], fg=self.theme["frame_fg"])
        stf.pack(fill="x", pady=3)
        str_frame = tk.Frame(stf, bg=self.theme["frame_bg"])
        str_frame.pack(fill="x", padx=6, pady=6)

        self.monitor_label = tk.Label(str_frame, text="🖥️  检测显示器中...",
                                      bg=self.theme["frame_bg"], fg=self.theme["fg"],
                                      font=("", self.font_size))
        self.monitor_label.grid(row=0, column=0, sticky="w", padx=6, pady=1)

        self.shot_count_label = tk.Label(str_frame, text="📷  0 张",
                                         bg=self.theme["frame_bg"], fg=self.theme["fg"],
                                         font=("", self.font_size))
        self.shot_count_label.grid(row=0, column=1, sticky="w", padx=6, pady=1)

        self.last_size_label = tk.Label(str_frame, text="📏  0 MB",
                                        bg=self.theme["frame_bg"], fg=self.theme["fg"],
                                        font=("", self.font_size))
        self.last_size_label.grid(row=1, column=0, sticky="w", padx=6, pady=1)

        self.disk_label = tk.Label(str_frame, text="💾  0 GB 可用",
                                   bg=self.theme["frame_bg"], fg=self.theme["fg"],
                                   font=("", self.font_size))
        self.disk_label.grid(row=1, column=1, sticky="w", padx=6, pady=1)

        self.remain_label = tk.Label(str_frame, text="📊  等待首次截图",
                                     bg=self.theme["frame_bg"], fg=self.theme["fg"],
                                     font=("", self.font_size))
        self.remain_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=6, pady=1)

        self.status_label = tk.Label(stf, text="● 已停止", fg=self.theme["status_stop"],
                                     bg=self.theme["status_label_bg"], font=("", self.font_size + 1, "bold"))
        self.status_label.pack(pady=5, fill="x")

        # 控制按钮
        ctrl_frame = tk.Frame(main, bg=self.theme["bg"])
        ctrl_frame.pack(pady=6)

        self.start_btn = tk.Button(ctrl_frame, text="▶ 开始截图", command=self.start,
                                   bg=self.theme["primary"], fg="white",
                                   font=("", self.font_size, "bold"),
                                   padx=18, pady=5, relief="flat", cursor="hand2")
        self.start_btn.pack(side="left", padx=6)

        self.stop_btn = tk.Button(ctrl_frame, text="⏹ 停止截图", command=self.stop,
                                  bg=self.theme["stop_btn_disabled_bg"],
                                  fg=self.theme["stop_btn_disabled_fg"],
                                  font=("", self.font_size, "bold"),
                                  padx=18, pady=5, relief="flat", cursor="hand2",
                                  state="disabled")
        self.stop_btn.pack(side="left", padx=6)

    def select_path(self):
        p = filedialog.askdirectory()
        if p:
            self.save_path.set(p)
            self.update_ui_info()

    def shot(self):
        while self.running:
            try:
                folder = os.path.join(self.save_path.get(), datetime.datetime.now().strftime("%Y-%m-%d"))
                os.makedirs(folder, exist_ok=True)
                name = (datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        if self.name_mode.get() == "格式化时间"
                        else str(int(time.time())))
                mons = get_monitors()
                total_size = 0

                for i, m in enumerate(mons, 1):
                    img = capture_screen_gdi(m.x, m.y, m.width, m.height)
                    path = os.path.join(folder, f"{name}_screen{i}.jpg")
                    img.save(path, "JPEG", quality=95, optimize=True)
                    total_size += os.path.getsize(path)

                self.last_total_size = total_size
                self.last_shot_count = len(mons)
                self.after(10, self.update_after_shot)

                interval = self.get_current_interval()
                time.sleep(max(3, interval))

            except Exception as e:
                print(f"截图异常: {e}")
                time.sleep(5)

    def update_after_shot(self):
        self.shot_count_label.config(text=f"📷  {self.last_shot_count} 张")
        last_mb = self.last_total_size / (1024 ** 2)
        self.last_size_label.config(text=f"📏  {last_mb:.1f} MB")
        self.update_ui_info()

    def start(self):
        if self.save_path.get() == "未选择保存目录":
            messagebox.showwarning("提示", "请先选择保存路径！")
            return

        self.running = True
        self.start_btn.config(state="disabled", bg=self.theme["stop_btn_disabled_bg"],
                              fg=self.theme["stop_btn_disabled_fg"])
        self.stop_btn.config(state="normal", bg=self.theme["stop_btn_enabled_bg"],
                             fg=self.theme["stop_btn_enabled_fg"])
        self.status_label.config(text="● 运行中", fg=self.theme["status_run"])
        threading.Thread(target=self.shot, daemon=True).start()

    def stop(self):
        self.running = False
        self.start_btn.config(state="normal", bg=self.theme["primary"], fg="white")
        self.stop_btn.config(state="disabled", bg=self.theme["stop_btn_disabled_bg"],
                             fg=self.theme["stop_btn_disabled_fg"])
        self.status_label.config(text="● 已停止", fg=self.theme["status_stop"])

    def init_tray_icon(self):
        def show(icon, item):
            self.after(0, self.deiconify)
            icon.stop()
            self.tray_icon = None

        def quit_app(icon, item):
            self.running = False
            self.after(0, self.destroy)
            icon.stop()

        try:
            img = Image.open(self.icon_path)
        except:
            img = Image.new("RGB", (32, 32), "#4A90E2" if not self.theme_manager.is_dark else "#388BFD")

        menu = Menu(Item("显示窗口", show), Item("退出", quit_app))
        self.tray_icon = Icon("ScreenshotTool", img, menu=menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def minimize_to_tray(self):
        self.withdraw()
        self.float_ball.show()

    def toggle_fullscreen(self, e=None):
        self.fullscreen_flag = not self.fullscreen_flag
        self.attributes("-fullscreen", self.fullscreen_flag)

    def close_app(self):
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()


if __name__ == "__main__":
    app = ScreenshotTool()
    app.mainloop()