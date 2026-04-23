import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import datetime
import os
import sys
import time
import threading
import shutil
from PIL import Image, ImageTk, ImageDraw
import ctypes
from ctypes import wintypes
from pystray import Icon, MenuItem as Item, Menu
from screeninfo import get_monitors

# ===================== Windows GDI 截图核心（色彩修复版） =====================
user32 = ctypes.WinDLL('user32', use_last_error=True)
gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)

# Windows API 常量
SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB = 0
BI_BITFIELDS = 3  # 用于明确指定RGB掩码


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD)
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", wintypes.DWORD * 3)
    ]


def capture_screen_gdi(x, y, width, height):
    """
    用Windows GDI API截图，修复色彩失真问题
    """
    try:
        # 获取桌面DC
        hdc_screen = user32.GetDC(0)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        hbitmap = gdi32.CreateCompatibleBitmap(hdc_screen, width, height)
        gdi32.SelectObject(hdc_mem, hbitmap)

        # BitBlt 拷贝屏幕内容
        gdi32.BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, x, y, SRCCOPY)

        # 准备BITMAPINFO结构 - 关键：使用32位色深避免色彩失真
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height  # 负值表示自上而下
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32  # 使用32位色深
        bmi.bmiHeader.biCompression = BI_RGB
        bmi.bmiHeader.biSizeImage = width * height * 4

        # 分配缓冲区（32位 = 4字节/像素）
        buf_size = width * height * 4
        buf = ctypes.create_string_buffer(buf_size)

        # 获取像素数据
        gdi32.GetDIBits(hdc_mem, hbitmap, 0, height, buf, ctypes.byref(bmi), DIB_RGB_COLORS)

        # 清理资源
        gdi32.DeleteObject(hbitmap)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)

        # 转换为PIL Image并修复色彩通道顺序
        # Windows GDI返回的是BGRA格式，需要转换为RGBA
        img = Image.frombytes("RGBA", (width, height), buf, "raw", "BGRA")

        # 转换为RGB（丢弃Alpha通道）
        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
        rgb_img.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)

        return rgb_img

    except Exception as e:
        print(f"GDI截图异常: {e}，使用pyautogui备份方案")
        try:
            import pyautogui
            return pyautogui.screenshot(region=(x, y, width, height))
        except:
            # 最后的备用方案
            return Image.new("RGB", (width, height), (128, 128, 128))


# ===================== 资源路径处理 =====================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ===================== 系统API =====================
user32_old = ctypes.WinDLL('user32', use_last_error=True)
SM_CXSCREEN = 0
SPI_GETWORKAREA = 0x0030


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


def get_work_area():
    rect = RECT()
    user32_old.SystemParametersInfoA(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
    return rect.left, rect.top, rect.right, rect.bottom


def get_screen_info():
    """获取所有显示器信息"""
    monitors = get_monitors()
    return monitors


# ===================== 全局配置 =====================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


# ===================== 悬浮球 =====================
class FloatBall:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.SIZE = 60
        self.RADIUS = self.SIZE // 2 - 2

        self.work_left, self.work_top, self.work_right, self.work_bottom = get_work_area()
        self.SCREEN_TOTAL_WIDTH = user32_old.GetSystemMetrics(SM_CXSCREEN)
        self.is_dragging = False
        self.is_pressing = False

        self.ball = tk.Toplevel(root)
        self.ball.overrideredirect(True)
        self.ball.attributes("-topmost", True)
        self.ball.attributes("-alpha", 0.95)
        self.ball.config(bg="#000000")
        self.ball.attributes("-transparentcolor", "#000000")
        self.ball.geometry(f"{self.SIZE}x{self.SIZE}")
        self.ball.withdraw()

        self.canvas = tk.Canvas(self.ball, width=self.SIZE, height=self.SIZE, bg="#000000", bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 默认位置在主显示器
        self.x = self.work_left + 100
        self.y = self.work_top + (self.work_bottom - self.work_top) // 2 - self.SIZE // 2

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.show_main)
        self.render_loop()

    def draw_ball(self):
        img = Image.new("RGBA", (self.SIZE, self.SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy, r = self.SIZE // 2, self.SIZE // 2, self.RADIUS
        main_color = "#3A9BFF" if self.is_pressing else "#4DABFF"
        light_color = "#95D0FF" if self.is_pressing else "#86C8FF"
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=main_color, outline=light_color, width=1)
        return ImageTk.PhotoImage(img)

    def render_loop(self):
        self.canvas.delete("all")
        self.ball_img = self.draw_ball()
        self.canvas.create_image(0, 0, image=self.ball_img, anchor="nw")
        self.root.after(30, self.render_loop)

    def on_press(self, e):
        self.is_pressing = True
        self.start_x, self.start_y = e.x, e.y

    def on_drag(self, e):
        self.is_dragging = True
        self.x += e.x - self.start_x
        self.y += e.y - self.start_y
        self.ball.geometry(f"+{self.x}+{self.y}")

    def on_release(self, e):
        self.is_pressing = False
        self.is_dragging = False
        # 智能边界检测
        monitors = get_monitors()
        for monitor in monitors:
            if monitor.x <= self.x <= monitor.x + monitor.width - self.SIZE:
                if monitor.y <= self.y <= monitor.y + monitor.height - self.SIZE:
                    break
        else:
            # 如果不在任何显示器内，放回主显示器
            self.x = monitors[0].x + 100
            self.y = monitors[0].y + 100
        self.ball.geometry(f"+{self.x}+{self.y}")

    def show_main(self, e=None):
        self.main_app.deiconify()
        self.hide_ball()

    def show_ball(self):
        self.ball.deiconify()
        self.ball.geometry(f"+{self.x}+{self.y}")

    def hide_ball(self):
        self.ball.withdraw()


# ===================== 主界面（自适应分辨率版） =====================
class ScreenshotTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("分时段自动截屏工具（色彩修复版）")

        # 自适应窗口大小
        self.setup_window_size()
        self.resizable(True, True)
        self.minsize(500, 600)  # 设置最小窗口大小

        self.fullscreen_flag = False
        self.running = False
        self.tray_icon = None

        self.icon_path = resource_path("icon.ico")
        try:
            self.iconbitmap(self.icon_path)
        except:
            pass

        # 基础配置
        self.save_path = ctk.StringVar(value="未选择保存目录")
        self.default_interval = ctk.StringVar(value="60")
        self.name_mode = ctk.StringVar(value="时间戳")
        self.float_ball = FloatBall(self, self)

        # 实时状态
        self.monitor_count = 0
        self.last_shot_count = 0
        self.last_total_size = 0
        self.schedule_rules = []

        # 绑定事件
        self.bind("<F11>", self.toggle_fullscreen)
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.bind("<Unmap>", lambda e: self.minimize_to_tray() if self.state() == "iconic" else None)
        self.bind("<Map>", lambda e: self.float_ball.hide_ball())
        self.bind("<Configure>", self.on_window_configure)  # 窗口大小改变时调整布局

        # 构建UI
        self.build_ui()
        self.init_tray_icon()
        self.refresh_rule_list()
        self.update_monitor_info()

    def setup_window_size(self):
        """根据屏幕大小设置合适的窗口尺寸"""
        monitors = get_monitors()
        if monitors:
            primary = monitors[0]
            # 窗口大小为屏幕的40%，但不超过800x800
            width = min(int(primary.width * 0.4), 800)
            height = min(int(primary.height * 0.6), 700)
            self.geometry(f"{width}x{height}")

            # 居中显示
            x = primary.x + (primary.width - width) // 2
            y = primary.y + (primary.height - height) // 2
            self.geometry(f"+{x}+{y}")

    def on_window_configure(self, event):
        """窗口大小改变时的处理"""
        # 可以在这里添加自适应逻辑
        pass

    # ===================== 时段规则核心 =====================
    def validate_no_overlap(self, new_rule):
        """检查新规则是否与现有规则时间重叠"""
        new_start = datetime.datetime.strptime(new_rule['start'], "%H:%M")
        new_end = datetime.datetime.strptime(new_rule['end'], "%H:%M")

        if new_end <= new_start:
            new_end += datetime.timedelta(days=1)

        for rule in self.schedule_rules:
            exist_start = datetime.datetime.strptime(rule['start'], "%H:%M")
            exist_end = datetime.datetime.strptime(rule['end'], "%H:%M")

            if exist_end <= exist_start:
                exist_end += datetime.timedelta(days=1)

            if (new_start < exist_end and new_end > exist_start):
                return False, rule
        return True, None

    def add_schedule_rule(self):
        start = self.entry_start.get().strip()
        end = self.entry_end.get().strip()
        interval = self.entry_rule_interval.get().strip()

        if not start or not end or not interval:
            messagebox.showwarning("提示", "请填写完整：开始时间、结束时间、间隔秒数")
            return

        try:
            datetime.datetime.strptime(start, "%H:%M")
            datetime.datetime.strptime(end, "%H:%M")
            interval = int(interval)
            if interval < 3:
                messagebox.showwarning("提示", "间隔不能小于3秒")
                return
        except:
            messagebox.showerror("错误", "时间格式应为 HH:MM，间隔为数字")
            return

        new_rule = {"start": start, "end": end, "interval": interval}

        is_valid, conflict_rule = self.validate_no_overlap(new_rule)
        if not is_valid:
            messagebox.showwarning(
                "时段冲突",
                f"新规则与现有规则时间重叠！\n冲突规则：{conflict_rule['start']} ~ {conflict_rule['end']}"
            )
            return

        self.schedule_rules.append(new_rule)
        self.refresh_rule_list()

    def delete_selected_rule(self):
        selected = self.list_rules.curselection()
        if not selected:
            messagebox.showinfo("提示", "请先选中要删除的规则")
            return
        del self.schedule_rules[selected[0]]
        self.refresh_rule_list()

    def refresh_rule_list(self):
        self.list_rules.delete(0, tk.END)
        sorted_rules = sorted(self.schedule_rules, key=lambda x: x['start'])
        for rule in sorted_rules:
            self.list_rules.insert(tk.END, f"{rule['start']} ~ {rule['end']} | 间隔{rule['interval']}秒")
        self.schedule_rules = sorted_rules

    def get_current_interval(self):
        """获取当前时段对应的截图间隔"""
        now = datetime.datetime.now()
        now_str = now.strftime("%H:%M")
        now_dt = datetime.datetime.strptime(now_str, "%H:%M")

        matching_intervals = []
        for rule in self.schedule_rules:
            s_dt = datetime.datetime.strptime(rule['start'], "%H:%M")
            e_dt = datetime.datetime.strptime(rule['end'], "%H:%M")

            if e_dt <= s_dt:
                e_dt += datetime.timedelta(days=1)
                now_check = now_dt + datetime.timedelta(days=1) if now_dt < s_dt else now_dt
            else:
                now_check = now_dt

            if s_dt <= now_check <= e_dt:
                matching_intervals.append(rule['interval'])

        if matching_intervals:
            return min(matching_intervals)

        return int(self.default_interval.get())

    # ===================== 磁盘/显示器信息 =====================
    def update_monitor_info(self):
        monitors = get_monitors()
        self.monitor_count = len(monitors)
        if self.monitor_count >= 2:
            self.monitor_label.configure(text=f"🖥️  检测到 {self.monitor_count} 个显示器（含副屏）")
        elif self.monitor_count == 1:
            self.monitor_label.configure(text="🖥️  仅检测到主显示器")
        else:
            self.monitor_label.configure(text="🖥️  检测显示器中...")

    def get_disk_free_bytes(self):
        try:
            path = self.save_path.get()
            if path == "未选择保存目录":
                return 0
            return shutil.disk_usage(path).free
        except:
            return 0

    def update_ui_info(self):
        free_bytes = self.get_disk_free_bytes()
        free_gb = free_bytes / (1024 ** 3)
        self.disk_label.configure(text=f"💽  磁盘剩余：{free_gb:.1f} GB")

        if self.last_total_size <= 0:
            self.remain_label.configure(text="🔋  预计还可截：暂无数据")
        else:
            remain_times = int(free_bytes / self.last_total_size)
            self.remain_label.configure(text=f"🔋  预计还可截：{remain_times} 次")

    # ===================== UI构建（自适应布局） =====================
    def build_ui(self):
        # 主容器 - 使用pack布局，允许内容自适应
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # ========== 基础设置区 ==========
        path_frame = ctk.CTkFrame(main_container)
        path_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(path_frame, text="保存路径：").pack(side="left", padx=5)
        path_entry = ctk.CTkEntry(path_frame, textvariable=self.save_path, state="readonly")
        path_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(path_frame, text="选择", command=self.select_path, width=60).pack(side="left", padx=5)

        # 默认间隔和命名
        base_frame = ctk.CTkFrame(main_container)
        base_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(base_frame, text="默认间隔：").pack(side="left", padx=5)
        interval_entry = ctk.CTkEntry(base_frame, textvariable=self.default_interval, width=60)
        interval_entry.pack(side="left", padx=5)
        ctk.CTkLabel(base_frame, text="秒").pack(side="left", padx=2)

        ctk.CTkLabel(base_frame, text="命名：").pack(side="left", padx=(20, 5))
        name_combo = ctk.CTkComboBox(base_frame, variable=self.name_mode,
                                     values=["时间戳", "格式化时间"], width=120)
        name_combo.pack(side="left", padx=5)

        # ========== 分时段规则区 ==========
        rule_frame = ctk.CTkFrame(main_container)
        rule_frame.pack(fill="both", expand=True, pady=5)

        # 规则输入行 - 使用grid布局更紧凑
        input_frame = ctk.CTkFrame(rule_frame)
        input_frame.pack(fill="x", padx=5, pady=5)

        # 使用grid实现响应式布局
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(3, weight=1)
        input_frame.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(input_frame, text="开始：").grid(row=0, column=0, padx=2, pady=2, sticky="e")
        self.entry_start = ctk.CTkEntry(input_frame, width=70)
        self.entry_start.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        ctk.CTkLabel(input_frame, text="结束：").grid(row=0, column=2, padx=2, pady=2, sticky="e")
        self.entry_end = ctk.CTkEntry(input_frame, width=70)
        self.entry_end.grid(row=0, column=3, padx=2, pady=2, sticky="ew")

        ctk.CTkLabel(input_frame, text="间隔：").grid(row=0, column=4, padx=2, pady=2, sticky="e")
        self.entry_rule_interval = ctk.CTkEntry(input_frame, width=70)
        self.entry_rule_interval.grid(row=0, column=5, padx=2, pady=2, sticky="ew")

        # 按钮放在第二行
        btn_subframe = ctk.CTkFrame(input_frame, fg_color="transparent")
        btn_subframe.grid(row=1, column=0, columnspan=6, pady=5)

        ctk.CTkButton(btn_subframe, text="添加规则", command=self.add_schedule_rule, width=80).pack(side="left", padx=5)
        ctk.CTkButton(btn_subframe, text="删除选中", command=self.delete_selected_rule,
                      width=80, fg_color="#FF6B6B").pack(side="left", padx=5)

        # 规则列表
        list_frame = ctk.CTkFrame(rule_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 滚动条
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.list_rules = tk.Listbox(list_frame, height=4, selectbackground="#3A9BFF",
                                     yscrollcommand=scrollbar.set)
        self.list_rules.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.list_rules.yview)

        # 提示标签
        tip_label = ctk.CTkLabel(rule_frame, text="💡 规则按时间排序，不允许时段重叠",
                                 text_color="#5A5A5A", font=("", 10))
        tip_label.pack(pady=2)

        # ========== 状态信息区 ==========
        status_frame = ctk.CTkFrame(main_container)
        status_frame.pack(fill="x", pady=5)

        self.monitor_label = ctk.CTkLabel(status_frame, text="🖥️  检测显示器中...", text_color="#3A9BFF")
        self.monitor_label.pack(anchor="w", pady=2)

        self.shot_count_label = ctk.CTkLabel(status_frame, text="📷  本次已截：0 张", text_color="#2EAA73")
        self.shot_count_label.pack(anchor="w", pady=2)

        self.last_size_label = ctk.CTkLabel(status_frame, text="📏  上轮截图大小：0 MB", text_color="#5A5A5A")
        self.last_size_label.pack(anchor="w", pady=2)

        self.disk_label = ctk.CTkLabel(status_frame, text="💽  磁盘剩余：0 GB", text_color="#5A5A5A")
        self.disk_label.pack(anchor="w", pady=2)

        self.remain_label = ctk.CTkLabel(status_frame, text="🔋  预计还可截：暂无数据", text_color="#FF7D00")
        self.remain_label.pack(anchor="w", pady=2)

        self.status_label = ctk.CTkLabel(status_frame, text="● 已停止", text_color="#E53935", font=("", 12, "bold"))
        self.status_label.pack(pady=8)

        # ========== 控制按钮 ==========
        btn_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        btn_frame.pack(pady=10)

        self.start_btn = ctk.CTkButton(btn_frame, text="开始截图", command=self.start, width=120, height=35)
        self.start_btn.pack(side="left", padx=10)

        self.stop_btn = ctk.CTkButton(btn_frame, text="停止截图", command=self.stop, width=120, height=35,
                                      state="disabled", fg_color="#FF6B6B")
        self.stop_btn.pack(side="left", padx=10)

    def select_path(self):
        path = ctk.filedialog.askdirectory()
        if path:
            self.save_path.set(path)
            self.update_ui_info()

    def get_folder(self):
        folder = os.path.join(self.save_path.get(), datetime.datetime.now().strftime("%Y-%m-%d"))
        os.makedirs(folder, exist_ok=True)
        return folder

    # ===================== 截图核心（色彩修复版） =====================
    def shot(self):
        while self.running:
            try:
                save_folder = self.get_folder()
                base_name = datetime.datetime.now().strftime(
                    "%Y%m%d_%H%M%S") if self.name_mode.get() == "格式化时间" else str(int(time.time()))
                monitors = get_monitors()
                self.last_shot_count = len(monitors)
                saved_paths = []
                total_size = 0

                for idx, monitor in enumerate(monitors, 1):
                    # 使用修复后的GDI截图
                    img = capture_screen_gdi(monitor.x, monitor.y, monitor.width, monitor.height)

                    monitor_name = f"screen{idx}"
                    out_path = os.path.join(save_folder, f"{base_name}_{monitor_name}.jpg")

                    # 保存为高质量JPEG
                    img.save(out_path, "JPEG", quality=95, optimize=True)
                    saved_paths.append(out_path)

                # 计算总大小
                for p in saved_paths:
                    if os.path.exists(p):
                        total_size += os.path.getsize(p)
                self.last_total_size = total_size

                # 更新UI
                self.after(10, self.update_after_shot)

                # 等待
                current_interval = self.get_current_interval()
                time.sleep(max(3, current_interval))

            except Exception as e:
                print(f"截图异常: {e}")
                time.sleep(5)

    def update_after_shot(self):
        self.shot_count_label.configure(text=f"📷  本次已截：{self.last_shot_count} 张")
        last_mb = self.last_total_size / (1024 ** 2)
        self.last_size_label.configure(text=f"📏  上轮截图大小：{last_mb:.1f} MB")
        self.update_ui_info()

    def start(self):
        if self.save_path.get() == "未选择保存目录":
            messagebox.showwarning("提示", "请先选择保存路径！")
            return
        self.running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text="● 运行中", text_color="#2EAA73")
        threading.Thread(target=self.shot, daemon=True).start()

    def stop(self):
        self.running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="● 已停止", text_color="#E53935")

    def init_tray_icon(self):
        def show_window(icon, item):
            self.deiconify()
            icon.stop()
            self.tray_icon = None

        def quit_app(icon, item):
            self.running = False
            self.destroy()
            icon.stop()

        try:
            img = Image.open(self.icon_path)
        except:
            img = Image.new("RGB", (32, 32), "#4DABFF")
        menu = Menu(Item("显示窗口", show_window), Item("退出", quit_app))
        self.tray_icon = Icon("ScreenshotTool", img, menu=menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def minimize_to_tray(self):
        self.withdraw()
        self.float_ball.show_ball()
        if not self.tray_icon:
            self.init_tray_icon()

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