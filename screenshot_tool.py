import tkinter as tk
import customtkinter as ctk
import pyautogui
import datetime
import os
import time
import threading
import random
import math
from PIL import ImageDraw, ImageTk, Image
import ctypes
from ctypes import wintypes

# ===================== 系统API获取工作区信息 =====================
user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.GetSystemMetrics.restype = ctypes.c_int
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
SM_CXSCREEN = 0
SPI_GETWORKAREA = 0x0030

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

def get_work_area():
    rect = RECT()
    user32.SystemParametersInfoA(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
    return rect.left, rect.top, rect.right, rect.bottom

# ===================== 全局配置 =====================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ===================== 悬浮球（固定30px×30px + 贴边+动画） =====================
class FloatBall:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        # 核心修改：固定悬浮球大小 30px × 30px
        self.SIZE = 60
        self.RADIUS = self.SIZE // 2 - 2

        self.work_left, self.work_top, self.work_right, self.work_bottom = get_work_area()
        self.SCREEN_TOTAL_WIDTH = user32.GetSystemMetrics(SM_CXSCREEN)
        self.is_dragging = False
        self.is_pressing = False
        self.raindrops = []
        self.water_ripples = []

        # 悬浮球窗口（固定30x30）
        self.ball = tk.Toplevel(root)
        self.ball.overrideredirect(True)
        self.ball.attributes("-topmost", True)
        self.ball.attributes("-alpha", 0.95)
        self.ball.config(bg="#000000")
        self.ball.attributes("-transparentcolor", "#000000")
        self.ball.geometry(f"{self.SIZE}x{self.SIZE}")
        self.ball.withdraw()

        # 画布固定30x30
        self.canvas = tk.Canvas(self.ball, width=self.SIZE, height=self.SIZE, bg="#000000", bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 初始位置
        self.x = self.work_left + 100
        self.y = self.work_top + (self.work_bottom - self.work_top) // 2 - self.SIZE // 2

        # 事件绑定
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.show_main)
        self.render_loop()

    def draw_ball(self):
        img = Image.new("RGBA", (self.SIZE, self.SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy, r = self.SIZE//2, self.SIZE//2, self.RADIUS
        main_color = "#3A9BFF" if self.is_pressing else "#4DABFF"
        light_color = "#95D0FF" if self.is_pressing else "#86C8FF"
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=main_color, outline=light_color, width=1)
        return ImageTk.PhotoImage(img)

    def render_loop(self):
        self.canvas.delete("all")
        self.ball_img = self.draw_ball()
        self.canvas.create_image(0, 0, image=self.ball_img, anchor="nw")
        if self.main_app.running:
            self.draw_rain_in_circle()
        else:
            self.draw_water()
        self.root.after(30, self.render_loop)

    # 适配30px的雨滴动画
    def draw_rain_in_circle(self):
        cx, cy = self.SIZE//2, self.SIZE//2
        if random.random() < 0.3:
            px = random.randint(2, self.SIZE-2)
            py = 0
            if math.hypot(px-cx, py-cy) <= self.RADIUS:
                self.raindrops.append([px, py, 2])
        new_drops = []
        for x,y,s in self.raindrops:
            ny = y + 2
            if math.hypot(x-cx, ny-cy) <= self.RADIUS:
                self.canvas.create_line(x,y,x,ny, fill="#ffffff", width=1)
                new_drops.append([x, ny, s])
        self.raindrops = new_drops[-15:]

    # 适配30px的波纹动画
    def draw_water(self):
        cx, cy = self.SIZE//2, self.SIZE//2
        self.canvas.create_oval(cx-2, cy-2, cx+2, cy+2, fill="#ffffff")
        if random.random() < 0.15:
            self.water_ripples.append([cx, cy, 0])
        new_ripples = []
        for x,y,r in self.water_ripples:
            if r < self.RADIUS-2:
                self.canvas.create_oval(x-r, y-r, x+r, y+r, outline="#ffffff", width=1)
                new_ripples.append([x, y, r + 0.5])
        self.water_ripples = new_ripples[-10:]

    def on_press(self, e):
        self.is_pressing = True
        self.start_x, self.start_y = e.x, e.y

    def on_drag(self, e):
        self.is_dragging = True
        self.x += e.x - self.start_x
        self.y += e.y - self.start_y
        self.ball.geometry(f"+{self.x}+{self.y}")

    # 贴边逻辑（适配30px小尺寸）
    def on_release(self, e):
        self.is_pressing = False
        self.is_dragging = False
        # 上下避让任务栏
        if self.y < self.work_top + 5:
            self.y = self.work_top + 5
        if self.y > self.work_bottom - self.SIZE -5:
            self.y = self.work_bottom - self.SIZE -5
        # 左右边缘遮挡强制贴边
        if self.x < -5:
            self.x = self.work_left + 5
        elif self.x > self.SCREEN_TOTAL_WIDTH - self.SIZE +5:
            self.x = self.SCREEN_TOTAL_WIDTH - self.SIZE -5
        else:
            if self.x < self.work_left +20:
                self.x = self.work_left +5
            elif self.x > self.work_right - self.SIZE -20:
                self.x = self.work_right - self.SIZE -5
        self.ball.geometry(f"+{self.x}+{self.y}")

    def show_main(self, e=None):
        self.main_app.deiconify()
        self.hide_ball()
    def show_ball(self):
        self.ball.deiconify()
        self.ball.geometry(f"+{self.x}+{self.y}")
    def hide_ball(self):
        self.ball.withdraw()

# ===================== 主界面（无修改） =====================
class ScreenshotTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("screenshot")
        self.resizable(True, True)
        self.fullscreen_flag = False
        self.running = False

        # 核心参数
        self.save_path = ctk.StringVar(value="未选择保存目录")
        self.interval = ctk.StringVar(value="60")
        self.name_mode = ctk.StringVar(value="时间戳")
        self.float_ball = FloatBall(self, self)

        # 绑定事件
        self.bind("<F11>", self.toggle_fullscreen)
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.bind("<Unmap>", lambda e: self.float_ball.show_ball() if self.state() == "iconic" else None)
        self.bind("<Map>", lambda e: self.float_ball.hide_ball())
        self.build_ui()

    def toggle_fullscreen(self, e=None):
        self.fullscreen_flag = not self.fullscreen_flag
        self.attributes("-fullscreen", self.fullscreen_flag)

    def build_ui(self):
        # 保存路径
        path_frame = ctk.CTkFrame(self)
        path_frame.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(path_frame, text="保存路径：").pack(side="left", padx=5)
        ctk.CTkEntry(path_frame, textvariable=self.save_path, state="readonly").pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(path_frame, text="选择", command=self.select_path, width=60).pack(side="left", padx=5)

        # 参数设置
        param_frame = ctk.CTkFrame(self)
        param_frame.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(param_frame, text="截屏间隔：").pack(side="left", padx=5)
        ctk.CTkEntry(param_frame, textvariable=self.interval, width=60).pack(side="left", padx=5)
        ctk.CTkLabel(param_frame, text="秒").pack(side="left", padx=2)
        ctk.CTkLabel(param_frame, text="命名方式：").pack(side="left", padx=10)
        ctk.CTkComboBox(param_frame, variable=self.name_mode, values=["时间戳","格式化时间"], width=120).pack(side="left", padx=5)

        # 状态
        self.status_label = ctk.CTkLabel(self, text="● 已停止", text_color="#E53935")
        self.status_label.pack(pady=8)

        # 控制按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)
        self.start_btn = ctk.CTkButton(btn_frame, text="开始", command=self.start, width=100)
        self.start_btn.pack(side="left", padx=10)
        self.stop_btn = ctk.CTkButton(btn_frame, text="停止", command=self.stop, width=100, state="disabled", fg_color="#FF6B6B")
        self.stop_btn.pack(side="left", padx=10)

    def select_path(self):
        path = ctk.filedialog.askdirectory()
        if path:
            self.save_path.set(path)

    def get_folder(self):
        folder = os.path.join(self.save_path.get(), datetime.datetime.now().strftime("%Y-%m-%d"))
        os.makedirs(folder, exist_ok=True)
        return folder

    def shot(self):
        while self.running:
            try:
                img = pyautogui.screenshot()
                name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") if self.name_mode.get() == "格式化时间" else str(int(time.time()))
                img.save(os.path.join(self.get_folder(), f"{name}.jpg"), quality=95)
                time.sleep(max(3, int(self.interval.get())))
            except:
                break

    def start(self):
        if self.save_path.get() == "未选择保存目录":
            tk.messagebox.showwarning("提示","请先选择保存路径！")
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

    def close_app(self):
        self.running = False
        self.destroy()

if __name__ == "__main__":
    app = ScreenshotTool()
    app.mainloop()