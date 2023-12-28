import ctypes
import os
import subprocess
import threading
import queue
import time
from enum import IntFlag

import tkinter as tk
from PIL import Image, ImageTk

# 路径定义
_C_HOME_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'c')
_C_LIBWINDOW_HOME_PATH = os.path.join(_C_HOME_PATH, 'window')
_C_LIBWINDOW_TMP_PATH = os.path.join(_C_LIBWINDOW_HOME_PATH, 'tmp')
_LIBWINDOW_DLL_FILE = os.path.join(_C_LIBWINDOW_HOME_PATH, "build/libwindow.dylib")
_LIBWINDOW_CODE_FILE = os.path.join(_C_LIBWINDOW_HOME_PATH, "src/window_osx.c")

# 首次需编译自定义库 (MacOS)
if not os.path.exists(_LIBWINDOW_DLL_FILE):
    with open(_LIBWINDOW_CODE_FILE, 'r') as file:
        # 读取C源码
        c_code = file.read()

        # 编译C代码到动态链接库
        # `-Wno-deprecated-declarations`: 忽略警告 `warning: 'kUTTypePNG' is deprecated: first deprecated in macOS 12.0 - Use UTTypePNG instead`
        gcc = subprocess.Popen(["gcc", "-Wno-deprecated-declarations", "-framework", "ApplicationServices", "-shared", "-o", _LIBWINDOW_DLL_FILE, "-x", "c", "-"], stdin=subprocess.PIPE)
        gcc.communicate(c_code.encode("utf-8"))

# 编译不成功的话, 就没必要继续了
if not os.path.exists(_LIBWINDOW_DLL_FILE):
    print('编译自定义库失败')
    os._exit(0)

# 加载自定义链接库
lib = ctypes.cdll.LoadLibrary(_LIBWINDOW_DLL_FILE)

# C代码返回的窗口信息结构
class WindowInfo(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_long),
        ("name", ctypes.c_char * 256),
        ("rect", ctypes.c_float * 4),

        ("pid", ctypes.c_int),
        ("ownerName", ctypes.c_char * 256),

        ("layer", ctypes.c_long),
    ]

# 获取窗口列表信息
get_window_list = lib.get_window_list
get_window_list.argtypes = [ctypes.POINTER(WindowInfo), ctypes.c_uint, ctypes.c_uint, ctypes.c_long, ctypes.c_int]
get_window_list.restype = ctypes.c_int

# 单窗口截图
get_window_screenshot = lib.get_window_screenshot
get_window_screenshot.argtypes = [ctypes.c_long, ctypes.c_float * 4, ctypes.c_char_p]
get_window_screenshot.restype = ctypes.c_bool

# 多窗口合并截图
get_window_screenshots = lib.get_window_screenshots
get_window_screenshots.argtypes = [ctypes.POINTER(ctypes.c_long), ctypes.c_int, ctypes.c_float * 4, ctypes.c_char_p]
get_window_screenshots.restype = ctypes.c_int


# CGWindowListOption 映射
class CGWindowListOption(IntFlag):
    kCGWindowListOptionAll = 0
    kCGWindowListOptionOnScreenOnly = (1 << 0)
    kCGWindowListOptionOnScreenAboveWindow = (1 << 1)
    kCGWindowListOptionOnScreenBelowWindow = (1 << 2)
    kCGWindowListOptionIncludingWindow = (1 << 3)
    kCGWindowListExcludeDesktopElements = (1 << 4)

# kCGNullWindowID 映射
KCG_NULL_WINDOW_ID = 0


class ImageLoader(threading.Thread):
    def __init__(self, img_queue, img_path):
        super().__init__(daemon=True)
        self.img_queue = img_queue
        self.img_path = img_path

    def run(self):
        img = Image.open(self.img_path)
        self.img_queue.put(img)


class ResizableImage(tk.LabelFrame):
    def __init__(self, master=None, img_path:str=None, title:str=None, onClick:callable=None):
        super().__init__(master)

        self.config(text=title)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.img_path = img_path

        self.img_queue = queue.Queue()
        self.img_loader = ImageLoader(self.img_queue, self.img_path)
        self.img_loader.start()

        self.selected = False
        self.img_loaded = False
        self.last_resize_time = 0

        self.img_label = tk.Label(self)
        self.img_label.grid(sticky='nsew')
        
        if onClick:
            self.img_label.bind("<Button-1>", onClick)
        
        # 设置全区域响应交互
        self.grid_propagate(False)

        # 绑定重绘
        self.bind("<Configure>", self.resize)

        # 初始绘制
        self.after_idle(self.set_initial_size)

    def set_initial_size(self):
        width, height = self.winfo_width(), self.winfo_height()
        self.resize_image(width, height)

    def resize(self, e):
        width, height = e.width, e.height
        self.resize_image(width, height)

    def resize_image(self, width, height):
        if width <= 1 or height <= 1:
            return

        if not self.img_loaded:
            try:
                self.img = self.img_queue.get_nowait()
                self.ratio = self.img.width / self.img.height
                self.img_loaded = True
            except queue.Empty:
                return

        # add delay to prevent frequent resize_image
        current_time = time.time()
        if current_time - self.last_resize_time < 0.2:
            return
        self.last_resize_time = current_time

        new_height = int(width / self.ratio if width / self.ratio < height else height)
        new_width = int(new_height * self.ratio)

        image = self.img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(image)
        self.img_label.configure(image=self.tk_img)
    
    def set_select(self, yes:bool=False):
        if yes:
            # self.config(foreground='#0a6eb7')
            self.img_label.config(background='#0a6eb7')
            self.selected = True
        else:
            # self.config(foreground='white')
            self.img_label.config(background='#333333')
            self.selected = False


class Application(tk.Frame):
    def __init__(self, master=None, windows:WindowInfo=None, col_num=2):
        super().__init__(master)

        self.pack(fill='both', expand=True)

        self.col_num = col_num
        self.windows = windows
        self.cells = []

        self.create_widgets()

    def create_widgets(self):
        for i, w in enumerate(self.windows):
            row = i // self.col_num
            col = i % self.col_num

            def onClick(e, i=i, w=w):
                print(f'点击了窗口[{i}]: {e}, {w.name.decode("utf-8")}')
                self.select_widget(i)

            img_path = os.path.join(_C_LIBWINDOW_TMP_PATH, f"window_{i:02}.png")
            cell = ResizableImage(self, img_path=img_path, title=w.name.decode("utf-8"), onClick=onClick)
            cell.grid(row=row, column=col, sticky='nsew')
            self.cells.append(cell)

            # 更新grid权重
            self.rowconfigure(row, weight=1)
            self.columnconfigure(col, weight=1)

    def select_widget(self, index:int):
        for i, w in enumerate(self.cells):
            w.set_select(i == index)


def main():
#     output = subprocess.check_output(["./window"])
#     for line in output.decode("utf-8").split("\n"):
#         if line:
#             print(line)

    # 窗口选项
    option = CGWindowListOption.kCGWindowListOptionOnScreenOnly
    # 关联窗口ID
    relativeToWindow = KCG_NULL_WINDOW_ID
    # 选择 0 层的就够用了
    layer = 0

    # 查询窗口列表
    windows = (WindowInfo * 100)()
    total = get_window_list(windows, option, relativeToWindow, layer, len(windows))
    for i in range(total):
        print(f"窗口[{i}]: ")
        print(f'- layer: {windows[i].layer}')
        print(f"- id: {windows[i].id}")
        print(f'- name: {windows[i].name.decode("utf-8")}',)
        print(f"- rect: {windows[i].rect[0]}, {windows[i].rect[1]}, {windows[i].rect[2]}, {windows[i].rect[3]}")
        print(f"- pid: {windows[i].pid}")
        print(f'- ownerName: {windows[i].ownerName.decode("utf-8")}',)
        print(f"-----------------------------------")

    
    if not os.path.exists(_C_LIBWINDOW_TMP_PATH):
        os.path.mkdir(_C_LIBWINDOW_TMP_PATH)

    # 单窗口 独立截图
    for i in range(total):
        if (get_window_screenshot(windows[i].id, windows[i].rect, os.path.join(_C_LIBWINDOW_TMP_PATH, f"window_{i:02}.png").encode("utf-8"))):
            print(f"窗口[{i}]: 截图成功")
        else:
            print(f"窗口[{i}]: 截图失败")



    # 多窗口 合并截图
    ids = [w.id for w in windows]
    c_ids = (ctypes.c_long * len(ids))(*ids)
    bounds = [0, 0, 0, 0] # 等价于 CGRectNull
    # bounds = [0, 0, sys.float_info.max, sys.float_info.max] # 等价于 CGRectNull
    # bounds = [0, 0, 512, 512] # 自定义区域
    c_bounds = (ctypes.c_float * 4)(*bounds)
    if (get_window_screenshots(c_ids, total, c_bounds, os.path.join(_C_LIBWINDOW_TMP_PATH, f"window_all.png").encode("utf-8"))):
        print(f"多窗口合并: 截图成功 {bounds}")
    else:
        print(f"多窗口合并: 截图失败 {bounds}")

    # 可视化交互展示窗口查询结果
    root = tk.Tk()
    root.geometry("800x600")
    root.title("分享窗口选择器")

    app = Application(master=root, windows=windows[:total], col_num=4)
    app.mainloop()

if __name__ == "__main__":
    main()
