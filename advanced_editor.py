#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
import struct
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, colorchooser
import colorsys
import math
import json
import threading
import time
from typing import Tuple, List, Dict, Optional, Any, Callable
from PIL import Image, ImageTk, ImageDraw

class Config:
    # 窗口配置
    WINDOW_WIDTH = 1600
    WINDOW_HEIGHT = 1000
    WINDOW_MIN_WIDTH = 1500
    WINDOW_MIN_HEIGHT = 950
    
    # 关于窗口配置
    ABOUT_WINDOW_WIDTH = 900
    ABOUT_WINDOW_HEIGHT = 750
    ABOUT_WINDOW_MIN_WIDTH = 800
    ABOUT_WINDOW_MIN_HEIGHT = 650
    
    # 图片配置
    ABOUT_IMG_MAX_WIDTH = 700
    ABOUT_IMG_MAX_HEIGHT = 450
    
    # 颜色调整范围
    RED_FACTOR_MIN = 0.5
    RED_FACTOR_MAX = 2.0
    GREEN_FACTOR_MIN = 0.5
    GREEN_FACTOR_MAX = 2.0
    BLUE_FACTOR_MIN = 0.1
    BLUE_FACTOR_MAX = 1.5
    
    # 默认颜色调整
    DEFAULT_RED_FACTOR = 1.2
    DEFAULT_GREEN_FACTOR = 1.1
    DEFAULT_BLUE_FACTOR = 0.7
    
    # 默认渐变颜色
    DEFAULT_GRADIENT_START = (255, 100, 50)
    DEFAULT_GRADIENT_END = (100, 50, 255)
    
    # 动画配置
    ANIMATION_INTERVAL = 50
    RESIZE_DEBOUNCE_MS = 100
    
    # 特效参数默认值
    DEFAULT_TRAIL_LENGTH = 10
    DEFAULT_TRAIL_FADE = 0.8
    DEFAULT_BLINK_SPEED = 500
    DEFAULT_BREATHE_SPEED = 2000
    DEFAULT_RAINBOW_SPEED = 50
    DEFAULT_RIPPLE_WAVE = 0.5
    DEFAULT_PULSE_SPEED = 1000
    
    # 主题颜色
    THEME_BG = '#2b2b2b'
    THEME_ACCENT = '#ff6b35'
    THEME_DISABLED = '#888888'
    THEME_BUTTON_BG = '#444444'
    THEME_PREVIEW_BG = '#444444'

class AdvancedLightEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("灯光秀")
        self.root.configure(bg=Config.THEME_BG)
        self.root.minsize(Config.WINDOW_MIN_WIDTH, Config.WINDOW_MIN_HEIGHT)
        
        # 设置路径（兼容打包和非打包环境）
        if hasattr(sys, '_MEIPASS'):
            # 打包后使用临时目录
            BASE_DIR = sys._MEIPASS
            self.config_path = os.path.join(os.path.expanduser("~"), "editor_config.json")
        else:
            # 未打包时使用源目录
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.join(BASE_DIR, "editor_config.json")
        
        self.logo_path = os.path.join(BASE_DIR, "logo.png")
        self.about_path = os.path.join(BASE_DIR, "关于.png")
        self.ico_path = os.path.join(BASE_DIR, "logo.ico")
        
        # 程序居中显示
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = Config.WINDOW_WIDTH
        window_height = Config.WINDOW_HEIGHT
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 第一步：先设置基础的Tkinter图标
        try:
            if os.path.exists(self.ico_path):
                self.root.iconbitmap(self.ico_path)
                print(f"成功设置基础ico图标: {self.ico_path}")
            
            if os.path.exists(self.logo_path):
                icon_img = Image.open(self.logo_path)
                icon_photos = []
                for size in [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]:
                    resized = icon_img.resize(size, Image.Resampling.LANCZOS)
                    icon_photos.append(ImageTk.PhotoImage(resized))
                self.root.iconphoto(True, *icon_photos)
                self.logo_photos = icon_photos
                print(f"成功设置基础png图标: {self.logo_path}")
        except Exception as e:
            print(f"设置基础图标失败: {e}")
        
        # 更新窗口，确保窗口完全创建
        self.root.update()
        
        # 第二步：用Windows API设置应用程序ID和图标
        try:
            if sys.platform == 'win32':
                import ctypes
                from ctypes import wintypes
                
                # 设置应用程序用户模型ID
                myappid = 'light.editor.app.v1'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                print("成功设置应用程序ID")
                
                # 使用Windows API直接设置窗口图标
                if os.path.exists(self.ico_path):
                    hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                    if not hwnd:
                        hwnd = self.root.winfo_id()
                    print(f"获取到窗口句柄: {hwnd}")
                    
                    # 加载图标 - 小图标（任务栏）
                    hicon_small = ctypes.windll.shell32.ExtractIconW(0, self.ico_path, 0)
                    if hicon_small:
                        ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon_small)  # WM_SETICON, ICON_SMALL
                        print("成功设置小图标（任务栏）")
                    
                    # 加载图标 - 大图标（Alt+Tab）
                    hicon_big = ctypes.windll.shell32.ExtractIconW(0, self.ico_path, 0)
                    if hicon_big:
                        ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon_big)  # WM_SETICON, ICON_BIG
                        print("成功设置大图标（Alt+Tab）")
        except Exception as e:
            print(f"设置Windows图标失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 加载配置
        self.config = self.load_config()
        
        # 设置样式
        self.setup_styles()
        
        # 参数设置
        self.red_factor = Config.DEFAULT_RED_FACTOR
        self.green_factor = Config.DEFAULT_GREEN_FACTOR
        self.blue_factor = Config.DEFAULT_BLUE_FACTOR
        self.format_type = "RGBW"
        self.input_file = ""
        self.output_file = ""
        
        # 渐变色设置
        self.gradient_enabled = False
        self.gradient_start = Config.DEFAULT_GRADIENT_START
        self.gradient_end = Config.DEFAULT_GRADIENT_END
        self.gradient_type = "linear"
        
        # 特效设置
        self.effect_type = "none"
        self.effect_params = {
            'trail_length': Config.DEFAULT_TRAIL_LENGTH,
            'trail_fade': Config.DEFAULT_TRAIL_FADE,
            'blink_speed': Config.DEFAULT_BLINK_SPEED,
            'breathe_speed': Config.DEFAULT_BREATHE_SPEED,
            'rainbow_speed': Config.DEFAULT_RAINBOW_SPEED,
            'ripple_wave': Config.DEFAULT_RIPPLE_WAVE,
            'pulse_speed': Config.DEFAULT_PULSE_SPEED
        }
        
        # 动画相关
        self.animation_running = False
        self.animation_frame = 0
        
        # 转换状态
        self.convert_in_progress = False
        self.convert_cancel_requested = False
        
        # 窗口调整优化相关
        self.resize_timer = None
        self.is_resizing = False
        
        # 性能优化状态
        self._gradient_dirty = True
        self._bar_ids = []
        self._color_update_timer = None
        self._last_about_pos = None
        self._last_progress = -1
        self._auto_scroll_log = True
        
        # 预缓存
        self._gradient_image = None
        self._gradient_photo = None
        
        # 预设颜色（RGB值）
        self.preset_colors = {
            "柔和暖光": (255, 200, 150),
            "温馨黄光": (255, 180, 80),
            "日落橙光": (255, 140, 50),
            "烛光效果": (255, 100, 30),
            "自然白光": (255, 255, 255),
            "冷白光": (230, 240, 255),
            "月光蓝": (180, 200, 255),
            "森林绿": (150, 255, 150),
            "浪漫紫": (200, 150, 255),
            "节日红": (255, 100, 100),
            "海洋蓝": (100, 180, 255),
            "日落金": (255, 220, 100)
        }
        
        # 直接设置主界面
        self.setup_main_ui()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {}
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if isinstance(config, dict):
                        return {**default_config, **config}
        except json.JSONDecodeError:
            print("配置文件解析错误，使用默认配置")
        except Exception as e:
            print(f"加载配置失败: {e}")
        return default_config
    
    def save_config(self) -> None:
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def show_about(self) -> None:
        """显示关于窗口"""
        # 先计算初始位置
        win_w, win_h = Config.ABOUT_WINDOW_WIDTH, Config.ABOUT_WINDOW_HEIGHT
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        initial_x = root_x + (root_w - win_w) // 2
        initial_y = root_y + (root_h - win_h) // 2
        
        # 创建窗口（直接到目标位置，隐藏显示
        about_window = tk.Toplevel(self.root)
        about_window.title("关于 - 灯光秀")
        about_window.configure(bg=Config.THEME_BG)
        about_window.minsize(Config.ABOUT_WINDOW_MIN_WIDTH, Config.ABOUT_WINDOW_MIN_HEIGHT)
        about_window.geometry(f"{win_w}x{win_h}+{initial_x}+{initial_y}")
        about_window.withdraw()
        
        # 设置图标
        try:
            if os.path.exists(self.ico_path):
                about_window.iconbitmap(self.ico_path)
        except Exception as e:
            print(f"关于窗口图标设置失败: {e}")
        
        # 永久居中于主窗口
        def center_about():
            if about_window and about_window.winfo_exists():
                root_x = self.root.winfo_rootx()
                root_y = self.root.winfo_rooty()
                root_w = self.root.winfo_width()
                root_h = self.root.winfo_height()
                curr_w = about_window.winfo_width()
                curr_h = about_window.winfo_height()
                if curr_w <= 1: curr_w = win_w
                if curr_h <= 1: curr_h = win_h
                x = root_x + (root_w - curr_w) // 2
                y = root_y + (root_h - curr_h) // 2
                new_pos = (x, y)
                if new_pos != self._last_about_pos:
                    about_window.geometry(f"+{x}+{y}")
                    self._last_about_pos = new_pos
                about_window.after(500, center_about)
        
        # 标题
        title_label = tk.Label(about_window, text="✨ 灯光秀", 
                              font=('微软雅黑', 20, 'bold'), 
                              fg=Config.THEME_ACCENT, bg=Config.THEME_BG)
        title_label.pack(pady=(20, 10))
        
        # 图片区域
        try:
            img = Image.open(self.about_path)
            img_width, img_height = img.size
            max_width = Config.ABOUT_IMG_MAX_WIDTH
            max_height = Config.ABOUT_IMG_MAX_HEIGHT
            
            ratio = min(max_width / img_width, max_height / img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.about_photo = ImageTk.PhotoImage(img)
            
            canvas = tk.Canvas(about_window, width=new_width, height=new_height, 
                              bg=Config.THEME_BG, highlightthickness=0)
            canvas.pack(pady=10, expand=True)
            canvas.create_image(new_width//2, new_height//2, anchor='center', image=self.about_photo)
        except Exception as e:
            print(f"无法加载图片: {e}")
            error_label = tk.Label(about_window, text="图片加载失败", 
                                  font=('微软雅黑', 12), fg=Config.THEME_DISABLED, bg=Config.THEME_BG)
            error_label.pack(pady=50)
        
        # 信息区域
        info_frame = tk.Frame(about_window, bg=Config.THEME_BG)
        info_frame.pack(pady=10)
        
        tk.Label(info_frame, text="功能说明：", font=('微软雅黑', 14, 'bold'), 
                fg=Config.THEME_ACCENT, bg=Config.THEME_BG).pack(pady=5)
        
        features = [
            "• 12种预设颜色模式",
            "• 自定义颜色调整（RGB通道）",
            "• 6种特效效果（拖尾、闪烁、呼吸、彩虹、波纹、脉冲）",
            "• 渐变色功能",
            "• 实时预览"
        ]
        
        for feature in features:
            tk.Label(info_frame, text=feature, font=('微软雅黑', 11), 
                    fg='white', bg=Config.THEME_BG).pack(anchor='w', pady=2)
        
        # 关闭按钮
        close_btn = tk.Button(about_window, text="关闭", 
                             bg='#666', fg='white', font=('微软雅黑', 12),
                             relief=tk.FLAT, cursor='hand2', padx=30, pady=8,
                             command=about_window.destroy)
        close_btn.pack(pady=15)
        
        # 显示窗口并开始居中
        about_window.deiconify()
        center_about()
    
    def setup_styles(self) -> None:
        """设置现代UI样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置样式
        style.configure('TFrame', background=Config.THEME_BG)
        style.configure('TLabel', background=Config.THEME_BG, foreground='white', font=('微软雅黑', 10))
        style.configure('TButton', font=('微软雅黑', 9), padding=4)
        style.configure('TLabelframe', background=Config.THEME_BG, foreground='white')
        style.configure('TLabelframe.Label', background=Config.THEME_BG, foreground=Config.THEME_ACCENT)
        style.configure('TCombobox', font=('微软雅黑', 10))
        style.configure('TRadiobutton', background=Config.THEME_BG, foreground='white')
        style.configure('TCheckbutton', background=Config.THEME_BG, foreground='white')
        
        # 自定义按钮样式
        style.configure('Primary.TButton', background=Config.THEME_ACCENT, foreground='white')
        style.configure('Success.TButton', background='#28a745', foreground='white')
        style.configure('Info.TButton', background='#17a2b8', foreground='white')
    
    def get_contrast_color(self, bg_color: Tuple[int, int, int]) -> str:
        """根据背景色计算对比度合适的文字颜色"""
        r, g, b = bg_color
        # 计算亮度
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        # 亮背景用黑字，暗背景用白字
        return '#000000' if luminance > 0.5 else '#ffffff'
    
    def setup_main_ui(self) -> None:
        """设置主界面"""
        main_container = ttk.Frame(self.root, padding="15")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 顶部：标题和菜单按钮
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(top_frame, text="✨ 灯光秀", 
                              font=('微软雅黑', 20, 'bold'), 
                              fg=Config.THEME_ACCENT, bg=Config.THEME_BG)
        title_label.pack(side=tk.LEFT)
        
        btn_container = tk.Frame(top_frame, bg=Config.THEME_BG)
        btn_container.pack(side=tk.RIGHT)
        
        about_btn = tk.Button(btn_container, text="📋 关于", 
                             bg=Config.THEME_BUTTON_BG, fg='white', font=('微软雅黑', 10),
                             relief=tk.FLAT, cursor='hand2', padx=15, pady=5,
                             command=self.show_about)
        about_btn.pack(side=tk.LEFT)
        
        # 创建左右分栏
        left_frame = ttk.Frame(main_container, width=520)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        right_frame = ttk.Frame(main_container, width=600)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        right_frame.pack_propagate(False)
        
        # 左侧：控制面板
        self.setup_control_panel(left_frame)
        
        # 右侧：预览面板
        self.setup_preview_panel(right_frame)
        
        # 开始动画
        self.start_preview_animation()
        
        # 绑定窗口调整优化事件
        self.root.bind('<Configure>', self.on_window_configure)
    
    def on_window_configure(self, event: Any) -> None:
        """窗口调整事件处理（优化性能）"""
        # 只对主窗口事件响应
        if event.widget == self.root:
            self.is_resizing = True
            # 取消之前的定时器
            if self.resize_timer:
                self.root.after_cancel(self.resize_timer)
            # 设置新的定时器，只在调整停止后更新
            self.resize_timer = self.root.after(Config.RESIZE_DEBOUNCE_MS, self.on_resize_end)
    
    def on_resize_end(self) -> None:
        """窗口调整结束，恢复完整更新"""
        self.is_resizing = False
        self.resize_timer = None
        # 更新预览
        self.update_current_color_preview()
    
    def setup_control_panel(self, parent: Any) -> None:
        """设置控制面板"""
        # 文件选择
        file_frame = ttk.LabelFrame(parent, text="📁 文件操作", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        file_btn_frame = ttk.Frame(file_frame)
        file_btn_frame.pack(fill=tk.X)
        
        ttk.Button(file_btn_frame, text="选择灯光文件", 
                  command=self.select_file, style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(file_btn_frame, text="✨ 创建新文件", 
                  command=self.create_new_file, style='Info.TButton').pack(side=tk.LEFT, padx=(0, 10))
        
        self.file_label = ttk.Label(file_btn_frame, text="未选择文件", 
                                   font=('微软雅黑', 9), foreground='#888')
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 预设模式（带颜色背景和对比度优化）
        preset_frame = ttk.LabelFrame(parent, text="🎨 预设模式", padding="10")
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.setup_preset_buttons(preset_frame)
        
        # 渐变色设置
        gradient_frame = ttk.LabelFrame(parent, text="🌈 渐变色设置", padding="10")
        gradient_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.setup_gradient_controls(gradient_frame)
        
        # 参数调整
        param_frame = ttk.LabelFrame(parent, text="🔧 颜色调整", padding="10")
        param_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.setup_parameter_controls(param_frame)
        
        # 特效设置
        effect_frame = ttk.LabelFrame(parent, text="✨ 特效选择", padding="10")
        effect_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.setup_effect_controls(effect_frame)
        
        # 操作按钮
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        button_frame = ttk.Frame(action_frame)
        button_frame.pack(fill=tk.X)
        
        self.convert_button = ttk.Button(button_frame, text="⚡ 开始转换", 
                  command=self.convert_file, style='Success.TButton')
        self.convert_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_button = ttk.Button(button_frame, text="⛔ 取消转换", 
                  command=self.cancel_conversion, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="🔄 重置参数", 
                  command=self.reset_parameters).pack(side=tk.LEFT)
        
        # 进度条
        progress_frame = ttk.Frame(action_frame)
        progress_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(progress_frame, text="转换进度:").pack(side=tk.LEFT, padx=(0, 10))
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def setup_preset_buttons(self, parent: Any) -> None:
        """设置预设按钮（带颜色背景和对比度优化）"""
        preset_grid = ttk.Frame(parent)
        preset_grid.pack(fill=tk.X)
        
        presets = [
            ("柔和暖光", self.load_preset_warm),
            ("温馨黄光", self.load_preset_yellow),
            ("日落橙光", self.load_preset_orange),
            ("烛光效果", self.load_preset_candle),
            ("自然白光", self.load_preset_natural),
            ("冷白光", self.load_preset_cool),
            ("月光蓝", self.load_preset_moonlight),
            ("森林绿", self.load_preset_forest),
            ("浪漫紫", self.load_preset_purple),
            ("节日红", self.load_preset_red),
            ("海洋蓝", self.load_preset_ocean),
            ("日落金", self.load_preset_golden)
        ]
        
        self.preset_buttons = {}
        
        for i, (text, command) in enumerate(presets):
            row = i // 3
            col = i % 3
            
            color = self.preset_colors.get(text, (100, 100, 100))
            hex_color = self.rgb_to_hex(*color)
            text_color = self.get_contrast_color(color)
            
            btn_frame = tk.Frame(preset_grid, bg='#2b2b2b', padx=2, pady=2)
            btn_frame.grid(row=row, column=col, sticky='ew')
            
            btn = tk.Button(btn_frame, text=text, 
                           command=lambda c=command, t=text: self.apply_preset(c, t),
                           bg=hex_color, fg=text_color, 
                           font=('微软雅黑', 9, 'bold'),
                           relief=tk.RAISED, padx=8, pady=8, 
                           cursor='hand2', borderwidth=2)
            btn.pack(fill=tk.BOTH, expand=True)
            
            self.preset_buttons[text] = btn
        
        for i in range(3):
            preset_grid.columnconfigure(i, weight=1)
    
    def setup_gradient_controls(self, parent: Any) -> None:
        """设置渐变色控制"""
        gradient_toggle_frame = ttk.Frame(parent)
        gradient_toggle_frame.pack(fill=tk.X, pady=5)
        
        self.gradient_var = tk.BooleanVar(value=False)
        gradient_check = ttk.Checkbutton(gradient_toggle_frame, text="启用渐变色", 
                                          variable=self.gradient_var, command=self.toggle_gradient)
        gradient_check.pack(side=tk.LEFT)
        
        color_select_frame = ttk.Frame(parent)
        color_select_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(color_select_frame, text="起始颜色:").pack(side=tk.LEFT, padx=(0, 5))
        self.gradient_start_canvas = tk.Canvas(color_select_frame, width=40, height=25, 
                                                 bg=self.rgb_to_hex(*self.gradient_start), 
                                                 highlightthickness=1, highlightbackground='#555',
                                                 cursor='hand2')
        self.gradient_start_canvas.pack(side=tk.LEFT, padx=(0, 10))
        self.gradient_start_canvas.bind('<Button-1>', lambda e: self.choose_gradient_color('start'))
        
        ttk.Button(color_select_frame, text="选择", 
                  command=lambda: self.choose_gradient_color('start')).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(color_select_frame, text="结束颜色:").pack(side=tk.LEFT, padx=(0, 5))
        self.gradient_end_canvas = tk.Canvas(color_select_frame, width=40, height=25, 
                                               bg=self.rgb_to_hex(*self.gradient_end), 
                                               highlightthickness=1, highlightbackground='#555',
                                               cursor='hand2')
        self.gradient_end_canvas.pack(side=tk.LEFT, padx=(0, 10))
        self.gradient_end_canvas.bind('<Button-1>', lambda e: self.choose_gradient_color('end'))
        
        ttk.Button(color_select_frame, text="选择", 
                  command=lambda: self.choose_gradient_color('end')).pack(side=tk.LEFT)
        
        type_frame = ttk.Frame(parent)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="渐变类型:").pack(side=tk.LEFT)
        self.gradient_type_var = tk.StringVar(value="线性渐变")
        gradient_type_combo = ttk.Combobox(type_frame, textvariable=self.gradient_type_var, 
                                          values=["线性渐变", "径向渐变"], state="readonly", width=10)
        gradient_type_combo.pack(side=tk.LEFT, padx=(10, 0))
        gradient_type_combo.bind("<<ComboboxSelected>>", self.update_gradient_type)
    
    def toggle_gradient(self) -> None:
        """切换渐变色启用状态"""
        self.gradient_enabled = self.gradient_var.get()
        self._gradient_dirty = True
        self.log_message(f"渐变色: {'已启用' if self.gradient_enabled else '已禁用'}")
        self.update_gradient_preview()
        self.update_current_color_preview()
    
    def choose_gradient_color(self, which: str) -> None:
        """选择渐变色颜色"""
        initial_color = self.gradient_start if which == 'start' else self.gradient_end
        initial_hex = self.rgb_to_hex(*initial_color)
        
        color_result = colorchooser.askcolor(title=f"选择{'起始' if which == 'start' else '结束'}颜色", 
                                            initialcolor=initial_hex)
        
        if color_result[0]:
            new_color = (int(color_result[0][0]), int(color_result[0][1]), int(color_result[0][2]))
            
            if which == 'start':
                self.gradient_start = new_color
                self.gradient_start_canvas.config(bg=color_result[1])
            else:
                self.gradient_end = new_color
                self.gradient_end_canvas.config(bg=color_result[1])
            
            self._gradient_dirty = True
            self.log_message(f"已选择{'起始' if which == 'start' else '结束'}颜色: {color_result[1]}")
            self.update_gradient_preview()
            self.update_current_color_preview()
    
    def update_gradient_type(self, event: Optional[Any] = None) -> None:
        """更新渐变类型"""
        type_text = self.gradient_type_var.get()
        self.gradient_type = "linear" if type_text == "线性渐变" else "radial"
        self._gradient_dirty = True
        self.log_message(f"渐变类型: {type_text}")
        self.update_gradient_preview()
    
    def apply_preset(self, command: Callable[[], None], name: str) -> None:
        """应用预设"""
        command()
        self.highlight_preset_button(name)
    
    def highlight_preset_button(self, active_name: str) -> None:
        """高亮选中的预设按钮"""
        for name, btn in self.preset_buttons.items():
            if name == active_name:
                btn.config(relief=tk.SUNKEN, borderwidth=3)
            else:
                btn.config(relief=tk.RAISED, borderwidth=2)
    
    def setup_parameter_controls(self, parent: Any) -> None:
        """设置参数控制"""
        red_frame = ttk.Frame(parent)
        red_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(red_frame, text="红色增强:", foreground='#ff6b6b').pack(side=tk.LEFT)
        self.red_scale = ttk.Scale(red_frame, from_=0.5, to=2.0, orient=tk.HORIZONTAL)
        self.red_scale.set(self.red_factor)
        self.red_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        
        self.red_label = ttk.Label(red_frame, text=f"{self.red_factor:.2f}", width=5)
        self.red_label.pack(side=tk.RIGHT)
        
        green_frame = ttk.Frame(parent)
        green_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(green_frame, text="绿色调整:", foreground='#6bff6b').pack(side=tk.LEFT)
        self.green_scale = ttk.Scale(green_frame, from_=0.5, to=2.0, orient=tk.HORIZONTAL)
        self.green_scale.set(self.green_factor)
        self.green_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        
        self.green_label = ttk.Label(green_frame, text=f"{self.green_factor:.2f}", width=5)
        self.green_label.pack(side=tk.RIGHT)
        
        blue_frame = ttk.Frame(parent)
        blue_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(blue_frame, text="蓝色减弱:", foreground='#6b6bff').pack(side=tk.LEFT)
        self.blue_scale = ttk.Scale(blue_frame, from_=0.1, to=1.5, orient=tk.HORIZONTAL)
        self.blue_scale.set(self.blue_factor)
        self.blue_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        
        self.blue_label = ttk.Label(blue_frame, text=f"{self.blue_factor:.2f}", width=5)
        self.blue_label.pack(side=tk.RIGHT)
        
        self.red_scale.configure(command=self.update_red_label)
        self.green_scale.configure(command=self.update_green_label)
        self.blue_scale.configure(command=self.update_blue_label)
        
        format_frame = ttk.Frame(parent)
        format_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(format_frame, text="文件格式:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value=self.format_type)
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var, 
                                  values=["RGBW", "RGBA", "RGB565"], state="readonly", width=10)
        format_combo.pack(side=tk.LEFT, padx=(10, 0))
    
    def setup_effect_controls(self, parent: Any) -> None:
        """设置特效控制"""
        effect_select_frame = ttk.Frame(parent)
        effect_select_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(effect_select_frame, text="选择特效:").pack(side=tk.LEFT)
        
        self.effect_var = tk.StringVar(value="none")
        effects = [
            ("无特效", "none"),
            ("拖尾特效", "trail"),
            ("闪烁特效", "blink"),
            ("呼吸特效", "breathe"),
            ("彩虹渐变", "rainbow"),
            ("波纹特效", "ripple"),
            ("脉冲特效", "pulse")
        ]
        
        for i, (text, value) in enumerate(effects):
            rb = ttk.Radiobutton(effect_select_frame, text=text, variable=self.effect_var, 
                                value=value, command=self.update_effect_selection)
            rb.pack(side=tk.LEFT, padx=5)
        
        self.effect_params_frame = ttk.LabelFrame(parent, text="⚙️ 特效参数", padding="10")
        self.effect_params_frame.pack(fill=tk.X, pady=5)
        
        self.update_effect_params_ui()
    
    def update_effect_selection(self) -> None:
        """更新特效选择"""
        self.effect_type = self.effect_var.get()
        self.update_effect_params_ui()
        self.update_current_color_preview()
        self.log_message(f"已选择特效: {self.get_effect_name(self.effect_type)}")
    
    def get_effect_name(self, effect_type: str) -> str:
        """获取特效名称"""
        names = {
            'none': '无特效',
            'trail': '拖尾特效',
            'blink': '闪烁特效',
            'breathe': '呼吸特效',
            'rainbow': '彩虹渐变',
            'ripple': '波纹特效',
            'pulse': '脉冲特效'
        }
        return names.get(effect_type, '未知特效')
    
    def update_effect_params_ui(self) -> None:
        """更新特效参数UI"""
        for widget in self.effect_params_frame.winfo_children():
            widget.destroy()
        
        effect = self.effect_type
        
        if effect == 'trail':
            ttk.Label(self.effect_params_frame, text="拖尾长度:").grid(row=0, column=0, sticky='w', pady=5)
            self.trail_length_scale = ttk.Scale(self.effect_params_frame, from_=1, to=50, orient=tk.HORIZONTAL)
            self.trail_length_scale.set(self.effect_params['trail_length'])
            self.trail_length_scale.grid(row=0, column=1, sticky='ew', padx=10, pady=5)
            self.trail_length_label = ttk.Label(self.effect_params_frame, text=str(self.effect_params['trail_length']), width=4)
            self.trail_length_label.grid(row=0, column=2, pady=5)
            self.trail_length_scale.configure(command=self.update_trail_length)
            
            ttk.Label(self.effect_params_frame, text="衰减强度:").grid(row=1, column=0, sticky='w', pady=5)
            self.trail_fade_scale = ttk.Scale(self.effect_params_frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL)
            self.trail_fade_scale.set(self.effect_params['trail_fade'])
            self.trail_fade_scale.grid(row=1, column=1, sticky='ew', padx=10, pady=5)
            self.trail_fade_label = ttk.Label(self.effect_params_frame, text=f"{self.effect_params['trail_fade']:.2f}", width=4)
            self.trail_fade_label.grid(row=1, column=2, pady=5)
            self.trail_fade_scale.configure(command=self.update_trail_fade)
            
            self.effect_params_frame.columnconfigure(1, weight=1)
        
        elif effect == 'blink':
            ttk.Label(self.effect_params_frame, text="闪烁速度 (ms):").grid(row=0, column=0, sticky='w', pady=5)
            self.blink_speed_scale = ttk.Scale(self.effect_params_frame, from_=100, to=2000, orient=tk.HORIZONTAL)
            self.blink_speed_scale.set(self.effect_params['blink_speed'])
            self.blink_speed_scale.grid(row=0, column=1, sticky='ew', padx=10, pady=5)
            self.blink_speed_label = ttk.Label(self.effect_params_frame, text=str(self.effect_params['blink_speed']), width=4)
            self.blink_speed_label.grid(row=0, column=2, pady=5)
            self.blink_speed_scale.configure(command=self.update_blink_speed)
            
            self.effect_params_frame.columnconfigure(1, weight=1)
        
        elif effect == 'breathe':
            ttk.Label(self.effect_params_frame, text="呼吸速度 (ms):").grid(row=0, column=0, sticky='w', pady=5)
            self.breathe_speed_scale = ttk.Scale(self.effect_params_frame, from_=500, to=5000, orient=tk.HORIZONTAL)
            self.breathe_speed_scale.set(self.effect_params['breathe_speed'])
            self.breathe_speed_scale.grid(row=0, column=1, sticky='ew', padx=10, pady=5)
            self.breathe_speed_label = ttk.Label(self.effect_params_frame, text=str(self.effect_params['breathe_speed']), width=4)
            self.breathe_speed_label.grid(row=0, column=2, pady=5)
            self.breathe_speed_scale.configure(command=self.update_breathe_speed)
            
            self.effect_params_frame.columnconfigure(1, weight=1)
        
        elif effect == 'rainbow':
            ttk.Label(self.effect_params_frame, text="彩虹速度:").grid(row=0, column=0, sticky='w', pady=5)
            self.rainbow_speed_scale = ttk.Scale(self.effect_params_frame, from_=10, to=200, orient=tk.HORIZONTAL)
            self.rainbow_speed_scale.set(self.effect_params['rainbow_speed'])
            self.rainbow_speed_scale.grid(row=0, column=1, sticky='ew', padx=10, pady=5)
            self.rainbow_speed_label = ttk.Label(self.effect_params_frame, text=str(self.effect_params['rainbow_speed']), width=4)
            self.rainbow_speed_label.grid(row=0, column=2, pady=5)
            self.rainbow_speed_scale.configure(command=self.update_rainbow_speed)
            
            self.effect_params_frame.columnconfigure(1, weight=1)
        
        elif effect == 'ripple':
            ttk.Label(self.effect_params_frame, text="波纹密度:").grid(row=0, column=0, sticky='w', pady=5)
            self.ripple_wave_scale = ttk.Scale(self.effect_params_frame, from_=0.1, to=2.0, orient=tk.HORIZONTAL)
            self.ripple_wave_scale.set(self.effect_params['ripple_wave'])
            self.ripple_wave_scale.grid(row=0, column=1, sticky='ew', padx=10, pady=5)
            self.ripple_wave_label = ttk.Label(self.effect_params_frame, text=f"{self.effect_params['ripple_wave']:.2f}", width=4)
            self.ripple_wave_label.grid(row=0, column=2, pady=5)
            self.ripple_wave_scale.configure(command=self.update_ripple_wave)
            
            self.effect_params_frame.columnconfigure(1, weight=1)
        
        elif effect == 'pulse':
            ttk.Label(self.effect_params_frame, text="脉冲速度 (ms):").grid(row=0, column=0, sticky='w', pady=5)
            self.pulse_speed_scale = ttk.Scale(self.effect_params_frame, from_=200, to=3000, orient=tk.HORIZONTAL)
            self.pulse_speed_scale.set(self.effect_params['pulse_speed'])
            self.pulse_speed_scale.grid(row=0, column=1, sticky='ew', padx=10, pady=5)
            self.pulse_speed_label = ttk.Label(self.effect_params_frame, text=str(self.effect_params['pulse_speed']), width=4)
            self.pulse_speed_label.grid(row=0, column=2, pady=5)
            self.pulse_speed_scale.configure(command=self.update_pulse_speed)
            
            self.effect_params_frame.columnconfigure(1, weight=1)
        
        else:
            ttk.Label(self.effect_params_frame, text="当前特效无参数", foreground='#888').pack()
    
    def update_trail_length(self, value: str) -> None:
        self.effect_params['trail_length'] = int(float(value))
        self.trail_length_label.config(text=str(self.effect_params['trail_length']))
    
    def update_trail_fade(self, value: str) -> None:
        self.effect_params['trail_fade'] = float(value)
        self.trail_fade_label.config(text=f"{self.effect_params['trail_fade']:.2f}")
    
    def update_blink_speed(self, value: str) -> None:
        self.effect_params['blink_speed'] = int(float(value))
        self.blink_speed_label.config(text=str(self.effect_params['blink_speed']))
    
    def update_breathe_speed(self, value: str) -> None:
        self.effect_params['breathe_speed'] = int(float(value))
        self.breathe_speed_label.config(text=str(self.effect_params['breathe_speed']))
    
    def update_rainbow_speed(self, value: str) -> None:
        self.effect_params['rainbow_speed'] = int(float(value))
        self.rainbow_speed_label.config(text=str(self.effect_params['rainbow_speed']))
    
    def update_ripple_wave(self, value: str) -> None:
        self.effect_params['ripple_wave'] = float(value)
        self.ripple_wave_label.config(text=f"{self.effect_params['ripple_wave']:.2f}")
    
    def update_pulse_speed(self, value: str) -> None:
        self.effect_params['pulse_speed'] = int(float(value))
        self.pulse_speed_label.config(text=str(self.effect_params['pulse_speed']))
    
    def setup_preview_panel(self, parent: Any) -> None:
        """设置预览面板"""
        gradient_preview_frame = ttk.LabelFrame(parent, text="🌈 渐变色预览", padding="10")
        gradient_preview_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.gradient_preview_canvas = tk.Canvas(gradient_preview_frame, height=90, 
                                                 bg='#646464', highlightthickness=1, highlightbackground='#555')
        self.gradient_preview_canvas.pack(fill=tk.X)
        
        current_frame = ttk.LabelFrame(parent, text="🎨 当前设置颜色", padding="10")
        current_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.current_color_canvas = tk.Canvas(current_frame, height=90, 
                                              bg='#646464', highlightthickness=1, highlightbackground='#555')
        self.current_color_canvas.pack(fill=tk.X)
        
        dynamic_frame = ttk.LabelFrame(parent, text="🌀 动态效果预览", padding="10")
        dynamic_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.dynamic_canvas = tk.Canvas(dynamic_frame, bg='#1a1a1a', highlightthickness=0)
        self.dynamic_canvas.pack(fill=tk.BOTH, expand=True)
        
        info_frame = ttk.LabelFrame(parent, text="📋 特效信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.effect_info_label = ttk.Label(info_frame, text="当前特效: 无特效\n参数: 无", 
                                          font=('微软雅黑', 9))
        self.effect_info_label.pack(fill=tk.X)
        
        log_frame = ttk.LabelFrame(parent, text="📝 操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=7, bg='#1a1a1a', 
                                                 fg='#00ff00', font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
    
    def log_message(self, message: str, auto_scroll: bool = False) -> None:
        """添加日志消息（性能优化，默认不自动滚动）"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"• {message}\n")
        if auto_scroll or self._auto_scroll_log:
            self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _debounce_color_update(self) -> None:
        """防抖更新颜色预览"""
        if self._color_update_timer:
            self.root.after_cancel(self._color_update_timer)
        
        def update():
            self.update_current_color_preview()
        
        self._color_update_timer = self.root.after(100, update)
    
    def update_red_label(self, value: str) -> None:
        """更新红色标签"""
        self.red_factor = float(value)
        self.red_label.config(text=f"{self.red_factor:.2f}")
        self._debounce_color_update()
    
    def update_green_label(self, value: str) -> None:
        """更新绿色标签"""
        self.green_factor = float(value)
        self.green_label.config(text=f"{self.green_factor:.2f}")
        self._debounce_color_update()
    
    def update_blue_label(self, value: str) -> None:
        """更新蓝色标签"""
        self.blue_factor = float(value)
        self.blue_label.config(text=f"{self.blue_factor:.2f}")
        self._debounce_color_update()
    
    def load_preset_warm(self) -> None:
        self.load_preset(1.15, 1.05, 0.8, "柔和暖光")
    
    def load_preset_yellow(self) -> None:
        self.load_preset(1.3, 1.2, 0.6, "温馨黄光")
    
    def load_preset_orange(self) -> None:
        self.load_preset(1.4, 1.1, 0.5, "日落橙光")
    
    def load_preset_candle(self) -> None:
        self.load_preset(1.5, 1.0, 0.4, "烛光效果")
    
    def load_preset_natural(self) -> None:
        self.load_preset(1.0, 1.0, 1.0, "自然白光")
    
    def load_preset_cool(self) -> None:
        self.load_preset(0.8, 0.9, 1.2, "冷白光")
    
    def load_preset_moonlight(self) -> None:
        self.load_preset(0.7, 0.8, 1.3, "月光蓝")
    
    def load_preset_forest(self) -> None:
        self.load_preset(0.8, 1.3, 0.7, "森林绿")
    
    def load_preset_purple(self) -> None:
        self.load_preset(1.2, 0.8, 1.2, "浪漫紫")
    
    def load_preset_red(self) -> None:
        self.load_preset(1.5, 0.7, 0.7, "节日红")
    
    def load_preset_ocean(self) -> None:
        self.load_preset(0.7, 0.9, 1.4, "海洋蓝")
    
    def load_preset_golden(self) -> None:
        self.load_preset(1.3, 1.1, 0.5, "日落金")
    
    def load_preset(self, red: float, green: float, blue: float, name: str) -> None:
        """加载预设参数"""
        self.red_scale.set(red)
        self.green_scale.set(green)
        self.blue_scale.set(blue)
        self.red_factor = red
        self.green_factor = green
        self.blue_factor = blue
        self.red_label.config(text=f"{red:.2f}")
        self.green_label.config(text=f"{green:.2f}")
        self.blue_label.config(text=f"{blue:.2f}")
        self.log_message(f"已加载预设: {name}")
        self.update_current_color_preview()
    
    def reset_parameters(self) -> None:
        """重置参数"""
        self.load_preset(1.2, 1.1, 0.7, "默认暖光")
        self.effect_var.set("none")
        self.effect_type = "none"
        self.gradient_var.set(False)
        self.gradient_enabled = False
        self.update_effect_params_ui()
        self.highlight_preset_button(None)
        self.log_message("参数已重置")
    
    def select_file(self) -> None:
        """选择灯光文件"""
        filename = filedialog.askopenfilename(
            title="选择灯光文件",
            filetypes=[("BIN files", "*.bin"), ("All files", "*.*")]
        )
        if filename:
            self.input_file = filename
            self.file_label.config(text=os.path.basename(filename))
            self.log_message(f"已选择文件: {os.path.basename(filename)}")
    
    def create_new_file(self) -> None:
        """创建新文件"""
        # 显示创建新文件的对话框
        create_window = tk.Toplevel(self.root)
        create_window.title("创建新灯光文件")
        create_window.configure(bg=Config.THEME_BG)
        create_window.resizable(False, False)
        
        # 居中显示
        win_w, win_h = 480, 480
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        initial_x = root_x + (root_w - win_w) // 2
        initial_y = root_y + (root_h - win_h) // 2
        create_window.geometry(f"{win_w}x{win_h}+{initial_x}+{initial_y}")
        
        # 设置图标
        try:
            if os.path.exists(self.ico_path):
                create_window.iconbitmap(self.ico_path)
        except Exception as e:
            print(f"创建窗口图标设置失败: {e}")
        
        content = tk.Frame(create_window, bg=Config.THEME_BG)
        content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # 标题
        title_label = tk.Label(content, text="✨ 创建新文件", 
                              font=('微软雅黑', 16, 'bold'), 
                              fg=Config.THEME_ACCENT, bg=Config.THEME_BG)
        title_label.pack(pady=(0, 15))
        
        # 像素数量
        pixel_frame = tk.Frame(content, bg=Config.THEME_BG)
        pixel_frame.pack(fill=tk.X, pady=8)
        
        tk.Label(pixel_frame, text="像素数量:", font=('微软雅黑', 12), 
                fg='white', bg=Config.THEME_BG).pack(side=tk.LEFT)
        
        pixel_var = tk.StringVar(value="10000")
        pixel_entry = tk.Entry(pixel_frame, textvariable=pixel_var, 
                              font=('微软雅黑', 12), width=15)
        pixel_entry.pack(side=tk.LEFT, padx=10)
        
        tk.Label(pixel_frame, text="个", font=('微软雅黑', 12), 
                fg='#888', bg=Config.THEME_BG).pack(side=tk.LEFT)
        
        # 快速设置按钮
        quick_frame = tk.Frame(content, bg=Config.THEME_BG)
        quick_frame.pack(fill=tk.X, pady=8)
        
        tk.Label(quick_frame, text="快速设置:", font=('微软雅黑', 10), 
                fg='#aaa', bg=Config.THEME_BG).pack(side=tk.LEFT, padx=(0, 10))
        
        quick_sizes = [1000, 5000, 10000, 50000, 100000]
        for size in quick_sizes:
            btn = tk.Button(quick_frame, text=str(size), 
                          bg='#444', fg='white', font=('微软雅黑', 9),
                          relief=tk.FLAT, cursor='hand2', padx=8, pady=3,
                          command=lambda s=size: pixel_var.set(str(s)))
            btn.pack(side=tk.LEFT, padx=3)
        
        # 保存路径
        path_frame = tk.Frame(content, bg=Config.THEME_BG)
        path_frame.pack(fill=tk.X, pady=8)
        
        tk.Label(path_frame, text="保存位置:", font=('微软雅黑', 12), 
                fg='white', bg=Config.THEME_BG).pack(side=tk.LEFT)
        
        # 默认路径：D:\灯光
        default_dir = r"D:\灯光"
        if not os.path.exists(default_dir):
            os.makedirs(default_dir, exist_ok=True)
        default_path = os.path.join(default_dir, "new_light.bin")
        output_path_var = tk.StringVar(value=default_path)
        path_entry = tk.Entry(path_frame, textvariable=output_path_var, 
                             font=('微软雅黑', 10), width=25)
        path_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # 说明
        info_label = tk.Label(content, text="使用当前设置的颜色、特效和渐变色\n（未选择预设时使用当前参数）", 
                             font=('微软雅黑', 10), fg='#888', bg=Config.THEME_BG)
        info_label.pack(pady=12)
        
        # 按钮
        btn_frame = tk.Frame(content, bg=Config.THEME_BG)
        btn_frame.pack(pady=(15, 0))
        
        def do_create():
            try:
                pixel_count = int(pixel_var.get())
                if pixel_count <= 0:
                    raise ValueError("像素数量必须大于0")
                output_path = output_path_var.get()
                if not output_path:
                    raise ValueError("请输入保存位置")
                
                # 检查是否为文件夹，如果是则添加默认文件名
                if os.path.isdir(output_path):
                    output_path = os.path.join(output_path, "new_light.bin")
                # 检查是否有扩展名，如果没有则添加
                elif not os.path.splitext(output_path)[1]:
                    output_path = output_path + ".bin"
                
                create_window.destroy()
                
                # 开始创建新文件
                self.creating_new_file = True
                self.new_file_pixel_count = pixel_count
                self.new_file_output_path = output_path
                
                threading.Thread(target=self.create_new_file_thread, daemon=True).start()
                
            except ValueError as e:
                messagebox.showerror("错误", str(e))
        
        create_btn = tk.Button(btn_frame, text="✓ 创建", 
                             bg=Config.THEME_ACCENT, fg='white', font=('微软雅黑', 12, 'bold'),
                             relief=tk.FLAT, cursor='hand2', padx=30, pady=10,
                             command=do_create)
        create_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="取消", 
                             bg='#666', fg='white', font=('微软雅黑', 12),
                             relief=tk.FLAT, cursor='hand2', padx=30, pady=10,
                             command=create_window.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def create_new_file_thread(self) -> None:
        """后台线程创建新文件"""
        try:
            self.convert_in_progress = True
            self.convert_cancel_requested = False
            
            def init_ui():
                self.convert_button.config(state=tk.DISABLED)
                self.cancel_button.config(state=tk.NORMAL)
                self.progress_bar['value'] = 0
                self.progress_label['text'] = "0%"
            
            self.root.after(0, init_ui)
            
            self.root.after(0, lambda: self.log_message(f"开始创建新文件，像素数: {self.new_file_pixel_count:,}"))
            
            format_type = self.format_var.get()
            if format_type in ["RGBW", "RGBA"]:
                bytes_per_pixel = 4
            elif format_type == "RGB565":
                bytes_per_pixel = 2
            else:
                bytes_per_pixel = 4
            
            total_pixels = self.new_file_pixel_count
            adjusted_colors = []
            
            # 生成颜色
            for i in range(total_pixels):
                if self.convert_cancel_requested:
                    self.root.after(0, lambda: self.log_message("❌ 创建已取消"))
                    self.root.after(0, self.reset_convert_ui)
                    return
                
                if self.gradient_enabled:
                    ratio = i / (total_pixels - 1) if total_pixels > 1 else 0
                    r = int(self.gradient_start[0] + (self.gradient_end[0] - self.gradient_start[0]) * ratio)
                    g = int(self.gradient_start[1] + (self.gradient_end[1] - self.gradient_start[1]) * ratio)
                    b = int(self.gradient_start[2] + (self.gradient_end[2] - self.gradient_start[2]) * ratio)
                else:
                    r = max(0, min(255, int(180 * self.red_factor)))
                    g = max(0, min(255, int(180 * self.green_factor)))
                    b = max(0, min(255, int(180 * self.blue_factor)))
                
                adjusted_colors.append([r, g, b])
                
                if i % 10000 == 0:
                    progress = int(i / total_pixels * 50)
                    self.root.after(0, lambda v=progress: self.update_progress(v))
            
            # 应用特效
            final_colors = adjusted_colors
            if self.effect_type == 'trail':
                self.root.after(0, lambda: self.log_message("🎨 应用拖尾特效..."))
                final_colors = self.apply_trail_effect_file(adjusted_colors)
            elif self.effect_type == 'blink':
                self.root.after(0, lambda: self.log_message("🎨 应用闪烁特效..."))
                final_colors = self.apply_blink_effect_file(adjusted_colors)
            elif self.effect_type == 'breathe':
                self.root.after(0, lambda: self.log_message("🎨 应用呼吸特效..."))
                final_colors = self.apply_breathe_effect_file(adjusted_colors)
            elif self.effect_type == 'rainbow':
                self.root.after(0, lambda: self.log_message("🎨 应用彩虹特效..."))
                final_colors = self.apply_rainbow_effect_file(adjusted_colors)
            elif self.effect_type == 'ripple':
                self.root.after(0, lambda: self.log_message("🎨 应用波纹特效..."))
                final_colors = self.apply_ripple_effect_file(adjusted_colors)
            elif self.effect_type == 'pulse':
                self.root.after(0, lambda: self.log_message("🎨 应用脉冲特效..."))
                final_colors = self.apply_pulse_effect_file(adjusted_colors)
            
            converted_data = bytearray()
            
            # 生成文件数据
            for i, color in enumerate(final_colors):
                if self.convert_cancel_requested:
                    self.root.after(0, lambda: self.log_message("❌ 创建已取消"))
                    self.root.after(0, self.reset_convert_ui)
                    return
                
                r, g, b = color
                
                if format_type == "RGBW":
                    warm_w = max(0, min(255, int((r + g + b) / 3 * 1.1)))
                    converted_data.extend([r, g, b, warm_w])
                elif format_type == "RGBA":
                    a = 255
                    converted_data.extend([r, g, b, a])
                elif format_type == "RGB565":
                    r_565 = max(0, min(31, (r * 31) // 255))
                    g_565 = max(0, min(63, (g * 63) // 255))
                    b_565 = max(0, min(31, (b * 31) // 255))
                    rgb565 = (r_565 << 11) | (g_565 << 5) | b_565
                    converted_data.extend(struct.pack('>H', rgb565))
                
                if i % 10000 == 0:
                    progress = 50 + int(i / total_pixels * 45)
                    self.root.after(0, lambda v=progress: self.update_progress(v))
            
            # 保存文件
            save_dir = os.path.dirname(self.new_file_output_path)
            if save_dir and not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
            
            with open(self.new_file_output_path, 'wb') as f:
                f.write(converted_data)
            
            self.root.after(0, lambda: self.update_progress(100))
            self.root.after(0, lambda: self.log_message(f"✅ 文件创建成功: {os.path.basename(self.new_file_output_path)}"))
            self.root.after(0, lambda: messagebox.showinfo("成功", 
                                f"新文件创建成功！\n\n保存位置: {self.new_file_output_path}\n像素数: {total_pixels:,}"))
            self.root.after(0, self.reset_convert_ui)
            
        except Exception as e:
            error_msg = f"创建文件失败: {e}"
            self.root.after(0, lambda: self.log_message(f"❌ {error_msg}"))
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            self.root.after(0, self.reset_convert_ui)
    
    def rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """将RGB转换为十六进制颜色代码"""
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def update_gradient_preview(self) -> None:
        """更新渐变色预览（使用PIL生成图片，性能优化）"""
        width = self.gradient_preview_canvas.winfo_width()
        height = self.gradient_preview_canvas.winfo_height()
        
        if width < 10 or height < 10:
            return
        
        if self.gradient_enabled:
            # 使用PIL生成渐变色图片
            img = Image.new('RGB', (width, height))
            pixels = img.load()
            
            # 线性渐变
            for x in range(width):
                ratio = x / width
                r = int(self.gradient_start[0] + (self.gradient_end[0] - self.gradient_start[0]) * ratio)
                g = int(self.gradient_start[1] + (self.gradient_end[1] - self.gradient_start[1]) * ratio)
                b = int(self.gradient_start[2] + (self.gradient_end[2] - self.gradient_start[2]) * ratio)
                for y in range(height):
                    pixels[x, y] = (r, g, b)
            
            self._gradient_image = img
            self._gradient_photo = ImageTk.PhotoImage(img)
            self.gradient_preview_canvas.delete("all")
            self.gradient_preview_canvas.create_image(0, 0, anchor='nw', image=self._gradient_photo)
        else:
            self.gradient_preview_canvas.config(bg='#444444')
            self.gradient_preview_canvas.delete("all")
            self.gradient_preview_canvas.create_text(width//2, height//2, 
                                                    text="请启用渐变色以预览", 
                                                    fill='#888888', font=('微软雅黑', 10))
    
    def update_current_color_preview(self) -> None:
        """更新当前设置颜色预览"""
        base_r, base_g, base_b = 180, 180, 180
        
        r = max(0, min(255, int(base_r * self.red_factor)))
        g = max(0, min(255, int(base_g * self.green_factor)))
        b = max(0, min(255, int(base_b * self.blue_factor)))
        
        hex_color = self.rgb_to_hex(r, g, b)
        self.current_color_canvas.config(bg=hex_color)
        
        info_text = f"当前特效: {self.get_effect_name(self.effect_type)}\n"
        info_text += f"渐变色: {'已启用' if self.gradient_enabled else '未启用'}\n"
        info_text += f"颜色设置: R×{self.red_factor:.2f} G×{self.green_factor:.2f} B×{self.blue_factor:.2f}"
        self.effect_info_label.config(text=info_text)
    
    def start_preview_animation(self) -> None:
        """开始预览动画"""
        self.animation_running = True
        self.animate_preview()
    
    def animate_preview(self) -> None:
        """动画预览（带窗口调整优化）"""
        if not self.animation_running:
            return
        
        # 窗口调整期间降低更新频率
        if self.is_resizing:
            self.animation_frame += 1
            # 只偶尔更新（每5帧一次）
            if self.animation_frame % 5 == 0:
                self.update_dynamic_preview()
            # 不更新渐变预览
            self.root.after(100, self.animate_preview)  # 降低帧率
        else:
            self.animation_frame += 1
            self.update_dynamic_preview()
            if self._gradient_dirty:
                self.update_gradient_preview()
                self._gradient_dirty = False
            self.root.after(50, self.animate_preview)
    
    def update_dynamic_preview(self) -> None:
        """更新动态预览"""
        width = self.dynamic_canvas.winfo_width()
        height = self.dynamic_canvas.winfo_height()
        
        if width < 10 or height < 10:
            return
        
        num_bars = 60
        bar_width = width / num_bars
        
        # 复用对象，不重建
        if len(self._bar_ids) != num_bars:
            self.dynamic_canvas.delete("all")
            self._bar_ids = []
            for i in range(num_bars):
                x1 = i * bar_width
                rect_id = self.dynamic_canvas.create_rectangle(x1, 0, x1 + bar_width, height, outline="")
                self._bar_ids.append(rect_id)
        
        # 更新颜色
        for i, rect_id in enumerate(self._bar_ids):
            if self.gradient_enabled:
                ratio = i / (num_bars - 1)
                r = int(self.gradient_start[0] + (self.gradient_end[0] - self.gradient_start[0]) * ratio)
                g = int(self.gradient_start[1] + (self.gradient_end[1] - self.gradient_start[1]) * ratio)
                b = int(self.gradient_start[2] + (self.gradient_end[2] - self.gradient_start[2]) * ratio)
            else:
                r = max(0, min(255, int(180 * self.red_factor)))
                g = max(0, min(255, int(180 * self.green_factor)))
                b = max(0, min(255, int(180 * self.blue_factor)))
            
            r, g, b = self.apply_effect_to_color(r, g, b, i, num_bars)
            
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            hex_color = self.rgb_to_hex(r, g, b)
            self.dynamic_canvas.itemconfig(rect_id, fill=hex_color)
    
    def apply_effect_to_color(self, r: int, g: int, b: int, index: int, total: int) -> Tuple[int, int, int]:
        """对颜色应用特效"""
        effect = self.effect_type
        frame = self.animation_frame
        
        if effect == 'none':
            return r, g, b
        
        elif effect == 'trail':
            trail_length = self.effect_params['trail_length']
            trail_fade = self.effect_params['trail_fade']
            
            offset = (frame + index) % trail_length
            fade_factor = trail_fade ** offset
            
            return int(r * fade_factor), int(g * fade_factor), int(b * fade_factor)
        
        elif effect == 'blink':
            blink_speed = self.effect_params['blink_speed']
            blink_phase = (frame * 50) % blink_speed
            blink_value = 0.3 + 0.7 * abs((blink_phase / blink_speed) - 0.5) * 2
            
            return int(r * blink_value), int(g * blink_value), int(b * blink_value)
        
        elif effect == 'breathe':
            breathe_speed = self.effect_params['breathe_speed']
            breathe_phase = (frame * 50) % breathe_speed
            breathe_value = 0.4 + 0.6 * (1 - abs((breathe_phase / breathe_speed) - 0.5) * 2)
            
            return int(r * breathe_value), int(g * breathe_value), int(b * breathe_value)
        
        elif effect == 'rainbow':
            rainbow_speed = self.effect_params['rainbow_speed']
            hue = ((frame + index) * rainbow_speed / 1000) % 1.0
            
            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            return int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
        
        elif effect == 'ripple':
            ripple_wave = self.effect_params['ripple_wave']
            wave_phase = (frame + index * ripple_wave) * 0.1
            wave_value = 0.5 + 0.5 * math.sin(wave_phase)
            
            return int(r * wave_value), int(g * wave_value), int(b * wave_value)
        
        elif effect == 'pulse':
            pulse_speed = self.effect_params['pulse_speed']
            pulse_phase = (frame * 50) % pulse_speed
            pulse_value = 0.5 + 0.5 * math.sin((pulse_phase / pulse_speed) * math.pi * 2)
            
            return int(r * pulse_value), int(g * pulse_value), int(b * pulse_value)
        
        return r, g, b
    
    def apply_trail_effect_file(self, colors: List[List[int]]) -> List[List[int]]:
        """应用拖尾特效到文件"""
        if len(colors) < self.effect_params['trail_length']:
            return colors
        
        result = []
        for i in range(len(colors)):
            trail_colors = colors[max(0, i - self.effect_params['trail_length'] + 1):i + 1]
            
            mixed_color = [0, 0, 0]
            total_weight = 0
            
            for j, color in enumerate(reversed(trail_colors)):
                weight = self.effect_params['trail_fade'] ** j
                for k in range(3):
                    mixed_color[k] += color[k] * weight
                total_weight += weight
            
            if total_weight > 0:
                mixed_color = [max(0, min(255, int(c / total_weight))) for c in mixed_color]
                result.append(mixed_color)
            else:
                result.append(colors[i])
        
        return result
    
    def apply_blink_effect_file(self, colors: List[List[int]]) -> List[List[int]]:
        """应用闪烁特效到文件"""
        result = []
        blink_speed = self.effect_params['blink_speed']
        
        for i, color in enumerate(colors):
            r, g, b = color
            phase = (i * 100) % blink_speed
            value = 0.3 + 0.7 * abs((phase / blink_speed) - 0.5) * 2
            
            new_r = max(0, min(255, int(r * value)))
            new_g = max(0, min(255, int(g * value)))
            new_b = max(0, min(255, int(b * value)))
            
            result.append([new_r, new_g, new_b])
        
        return result
    
    def apply_breathe_effect_file(self, colors: List[List[int]]) -> List[List[int]]:
        """应用呼吸特效到文件"""
        result = []
        breathe_speed = self.effect_params['breathe_speed']
        
        for i, color in enumerate(colors):
            r, g, b = color
            phase = (i * 100) % breathe_speed
            value = 0.4 + 0.6 * (1 - abs((phase / breathe_speed) - 0.5) * 2)
            
            new_r = max(0, min(255, int(r * value)))
            new_g = max(0, min(255, int(g * value)))
            new_b = max(0, min(255, int(b * value)))
            
            result.append([new_r, new_g, new_b])
        
        return result
    
    def apply_rainbow_effect_file(self, colors: List[List[int]]) -> List[List[int]]:
        """应用彩虹特效到文件"""
        result = []
        rainbow_speed = self.effect_params['rainbow_speed']
        
        for i, color in enumerate(colors):
            hue = (i * rainbow_speed / len(colors)) % 1.0
            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            
            new_r = max(0, min(255, int(rgb[0] * 255)))
            new_g = max(0, min(255, int(rgb[1] * 255)))
            new_b = max(0, min(255, int(rgb[2] * 255)))
            
            result.append([new_r, new_g, new_b])
        
        return result
    
    def apply_ripple_effect_file(self, colors: List[List[int]]) -> List[List[int]]:
        """应用波纹特效到文件"""
        result = []
        ripple_wave = self.effect_params['ripple_wave']
        
        for i, color in enumerate(colors):
            r, g, b = color
            wave_phase = i * ripple_wave * 0.1
            wave_value = 0.5 + 0.5 * math.sin(wave_phase)
            
            new_r = max(0, min(255, int(r * wave_value)))
            new_g = max(0, min(255, int(g * wave_value)))
            new_b = max(0, min(255, int(b * wave_value)))
            
            result.append([new_r, new_g, new_b])
        
        return result
    
    def apply_pulse_effect_file(self, colors: List[List[int]]) -> List[List[int]]:
        """应用脉冲特效到文件"""
        result = []
        pulse_speed = self.effect_params['pulse_speed']
        
        for i, color in enumerate(colors):
            r, g, b = color
            phase = (i * 100) % pulse_speed
            value = 0.5 + 0.5 * math.sin((phase / pulse_speed) * math.pi * 2)
            
            new_r = max(0, min(255, int(r * value)))
            new_g = max(0, min(255, int(g * value)))
            new_b = max(0, min(255, int(b * value)))
            
            result.append([new_r, new_g, new_b])
        
        return result
    
    def cancel_conversion(self) -> None:
        """取消转换"""
        self.convert_cancel_requested = True
        self.log_message("⛔ 正在取消转换...")
    
    def update_progress(self, value: int, text: Optional[str] = None) -> None:
        """更新进度条（节流优化，每5%才更新）"""
        if value - self._last_progress >= 5 or value == 100:
            self.progress_bar['value'] = value
            self.progress_label['text'] = f"{value}%"
            self._last_progress = value
            if text:
                self.log_message(text, auto_scroll=True)
    
    def convert_file(self) -> None:
        """执行文件转换（后台线程）"""
        if not self.input_file:
            messagebox.showwarning("警告", "请先选择灯光文件")
            return
        
        if self.convert_in_progress:
            messagebox.showwarning("警告", "转换正在进行中")
            return
        
        self.convert_in_progress = True
        self.convert_cancel_requested = False
        self.convert_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.progress_bar['value'] = 0
        self.progress_label['text'] = "0%"
        
        threading.Thread(target=self.convert_file_thread, daemon=True).start()
    
    def convert_file_thread(self) -> None:
        """后台线程执行文件转换"""
        try:
            base_name = os.path.splitext(self.input_file)[0]
            self.output_file = f"{base_name}_new.bin"
            
            with open(self.input_file, 'rb') as f:
                original_data = f.read()
            
            format_type = self.format_var.get()
            if format_type in ["RGBW", "RGBA"]:
                bytes_per_pixel = 4
            elif format_type == "RGB565":
                bytes_per_pixel = 2
            else:
                bytes_per_pixel = 4
            
            converted_data = bytearray()
            total_pixels = len(original_data) // bytes_per_pixel
            
            self.root.after(0, lambda: self.log_message(f"开始转换 {total_pixels:,} 个像素..."))
            
            all_colors = []
            for i in range(total_pixels):
                if self.convert_cancel_requested:
                    self.root.after(0, lambda: self.log_message("❌ 转换已取消"))
                    self.root.after(0, self.reset_convert_ui)
                    return
                
                start_idx = i * bytes_per_pixel
                pixel_data = original_data[start_idx:start_idx + bytes_per_pixel]
                
                if format_type in ["RGBW", "RGBA"]:
                    r, g, b = pixel_data[0], pixel_data[1], pixel_data[2]
                    all_colors.append([r, g, b])
                
                if i % 10000 == 0:
                    progress = int(i / total_pixels * 20)
                    self.root.after(0, lambda v=progress: self.update_progress(v))
            
            adjusted_colors = []
            for i, color in enumerate(all_colors):
                if self.convert_cancel_requested:
                    self.root.after(0, lambda: self.log_message("❌ 转换已取消"))
                    self.root.after(0, self.reset_convert_ui)
                    return
                
                if self.gradient_enabled:
                    ratio = i / (total_pixels - 1)
                    r = int(self.gradient_start[0] + (self.gradient_end[0] - self.gradient_start[0]) * ratio)
                    g = int(self.gradient_start[1] + (self.gradient_end[1] - self.gradient_start[1]) * ratio)
                    b = int(self.gradient_start[2] + (self.gradient_end[2] - self.gradient_start[2]) * ratio)
                else:
                    r, g, b = color
                    r = max(0, min(255, int(r * self.red_factor)))
                    g = max(0, min(255, int(g * self.green_factor)))
                    b = max(0, min(255, int(b * self.blue_factor)))
                
                adjusted_colors.append([r, g, b])
                
                if i % 10000 == 0:
                    progress = 20 + int(i / total_pixels * 40)
                    self.root.after(0, lambda v=progress: self.update_progress(v))
            
            final_colors = adjusted_colors
            if self.effect_type == 'trail':
                self.root.after(0, lambda: self.log_message("🎨 应用拖尾特效..."))
                final_colors = self.apply_trail_effect_file(adjusted_colors)
            elif self.effect_type == 'blink':
                self.root.after(0, lambda: self.log_message("🎨 应用闪烁特效..."))
                final_colors = self.apply_blink_effect_file(adjusted_colors)
            elif self.effect_type == 'breathe':
                self.root.after(0, lambda: self.log_message("🎨 应用呼吸特效..."))
                final_colors = self.apply_breathe_effect_file(adjusted_colors)
            elif self.effect_type == 'rainbow':
                self.root.after(0, lambda: self.log_message("🎨 应用彩虹特效..."))
                final_colors = self.apply_rainbow_effect_file(adjusted_colors)
            elif self.effect_type == 'ripple':
                self.root.after(0, lambda: self.log_message("🎨 应用波纹特效..."))
                final_colors = self.apply_ripple_effect_file(adjusted_colors)
            elif self.effect_type == 'pulse':
                self.root.after(0, lambda: self.log_message("🎨 应用脉冲特效..."))
                final_colors = self.apply_pulse_effect_file(adjusted_colors)
            
            for i, color in enumerate(final_colors):
                if self.convert_cancel_requested:
                    self.root.after(0, lambda: self.log_message("❌ 转换已取消"))
                    self.root.after(0, self.reset_convert_ui)
                    return
                
                r, g, b = color
                
                start_idx = i * bytes_per_pixel
                pixel_data = original_data[start_idx:start_idx + bytes_per_pixel]
                
                if format_type == "RGBW":
                    w = pixel_data[3]
                    warm_w = max(0, min(255, int(w * 1.1)))
                    converted_data.extend([r, g, b, warm_w])
                elif format_type == "RGBA":
                    a = pixel_data[3]
                    converted_data.extend([r, g, b, a])
                elif format_type == "RGB565":
                    r_565 = max(0, min(31, (r * 31) // 255))
                    g_565 = max(0, min(63, (g * 63) // 255))
                    b_565 = max(0, min(31, (b * 31) // 255))
                    
                    rgb565 = (r_565 << 11) | (g_565 << 5) | b_565
                    converted_data.extend(struct.pack('>H', rgb565))
                
                if i % 10000 == 0:
                    progress = 60 + int(i / total_pixels * 35)
                    self.root.after(0, lambda v=progress: self.update_progress(v))
            
            with open(self.output_file, 'wb') as f:
                f.write(converted_data)
            
            self.root.after(0, lambda: self.update_progress(100))
            self.root.after(0, lambda: self.log_message(f"✅ 转换完成! 输出文件: {os.path.basename(self.output_file)}"))
            self.root.after(0, lambda: messagebox.showinfo("完成", 
                              f"灯光转换完成!\n\n"
                              f"📁 输出文件: {os.path.basename(self.output_file)}\n"
                              f"🌈 渐变色: {'已启用' if self.gradient_enabled else '未启用'}\n"
                              f"✨ 特效: {self.get_effect_name(self.effect_type)}\n"
                              f"💡 提示: 在灯光控制软件中使用新文件"))
            self.root.after(0, self.reset_convert_ui)
            
        except Exception as e:
            error_msg = f"文件转换失败: {e}"
            self.root.after(0, lambda: self.log_message(f"❌ {error_msg}"))
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            self.root.after(0, self.reset_convert_ui)
    
    def reset_convert_ui(self) -> None:
        """重置转换界面"""
        self.convert_in_progress = False
        self.convert_cancel_requested = False
        self.convert_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)

def main() -> None:
    root = tk.Tk()
    app = AdvancedLightEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
