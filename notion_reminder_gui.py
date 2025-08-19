#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import json
import threading

# 音效支持
try:
    import pygame
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
    print("警告：pygame未安装，音效功能将被禁用")

# 主题支持
try:
    from ttkthemes import ThemedStyle
    THEMES_AVAILABLE = True
except ImportError:
    THEMES_AVAILABLE = False
    print("注意：ttkthemes未安装，将使用默认主题")

"""
Python 定时提醒 GUI - 增强版
- 美化界面设计，现代化UI风格
- 音效提醒功能
- 进度条显示
- 可保存/加载设置
- 更丰富的状态显示
- 动画效果
"""

# 默认配置
DEFAULTS = {
    "url": "https://www.notion.so/codetwice/Aug-18-2497c4668c0d8021a532fbbfa641a265",
    "total_min": 60,
    "first_min": 5,
    "second_min": 10,
    "subseq_min": 15,
    "chrome_path": "",
    "sound_enabled": True,
    "sound_file": "",
    "theme": "equilux"
}

class SoundManager:
    """音效管理器"""
    def __init__(self):
        self.enabled = SOUND_AVAILABLE
        self.initialized = False
        if self.enabled:
            try:
                pygame.mixer.init()
                self.initialized = True
            except Exception as e:
                print(f"音频初始化失败: {e}")
                self.enabled = False
        
    def play_notification(self, sound_file=None):
        """播放提醒音效"""
        if not self.enabled or not self.initialized:
            return
            
        try:
            if sound_file and os.path.exists(sound_file):
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
            else:
                # 播放系统默认提示音
                # 在macOS上可以使用系统命令
                if sys.platform == 'darwin':
                    os.system('afplay /System/Library/Sounds/Glass.aiff')
                elif sys.platform == 'win32':
                    import winsound
                    winsound.MessageBeep(winsound.MB_OK)
                else:
                    # Linux使用系统bell
                    os.system('echo -e "\\a"')
        except Exception as e:
            print(f"播放音效失败: {e}")

class ConfigManager:
    """配置管理器"""
    def __init__(self):
        self.config_file = Path(__file__).parent / "config.json"
        
    def load_config(self):
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认值和加载的配置
                result = DEFAULTS.copy()
                result.update(config)
                return result
        except Exception as e:
            print(f"加载配置失败: {e}")
        return DEFAULTS.copy()
    
    def save_config(self, config):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

class ReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📋 智能提醒助手 - Enhanced")
        self.root.geometry("800x650")
        self.root.minsize(700, 600)
        
        # 设置应用图标（如果可用）
        try:
            # 这里可以设置应用图标
            pass
        except:
            pass
        
        # 初始化管理器
        self.sound_manager = SoundManager()
        self.config_manager = ConfigManager()
        
        # 加载配置
        self.config = self.config_manager.load_config()
        
        # 状态变量
        self.running = False
        self.after_id = None
        self.elapsed = 0
        self.count = 0
        self.seconds_until_next = 0
        self.pending_wait = 0
        self.animation_after_id = None
        
        # 设置主题
        self._setup_theme()
        
        # 构建UI
        self._build_ui()
        self._load_settings()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _setup_theme(self):
        """设置主题"""
        if THEMES_AVAILABLE:
            try:
                style = ThemedStyle(self.root)
                available_themes = style.theme_names()
                theme = self.config.get('theme', 'equilux')
                if theme in available_themes:
                    style.set_theme(theme)
                else:
                    style.set_theme('equilux')
                self.style = style
            except Exception as e:
                print(f"主题设置失败: {e}")
                self.style = ttk.Style()
        else:
            self.style = ttk.Style()
            
        # 自定义样式
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """设置自定义样式"""
        # 主要按钮样式
        self.style.configure(
            "Primary.TButton",
            padding=(20, 10),
            font=('Helvetica', 11, 'bold')
        )
        
        # 标题标签样式
        self.style.configure(
            "Title.TLabel",
            font=('Helvetica', 14, 'bold'),
            padding=(0, 10)
        )
        
        # 状态标签样式
        self.style.configure(
            "Status.TLabel",
            font=('Helvetica', 12),
            padding=(5, 5)
        )
        
        # 大数字显示样式
        self.style.configure(
            "BigNumber.TLabel",
            font=('Helvetica', 18, 'bold'),
            padding=(10, 5)
        )

    def _build_ui(self):
        """构建用户界面"""
        # 主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题区域
        self._create_header(main_container)
        
        # 配置区域
        self._create_config_section(main_container)
        
        # 控制区域
        self._create_control_section(main_container)
        
        # 状态显示区域
        self._create_status_section(main_container)
        
        # 音效设置区域
        self._create_sound_section(main_container)
        
    def _create_header(self, parent):
        """创建标题区域"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # 标题
        title_label = ttk.Label(
            header_frame, 
            text="🔔 智能提醒助手", 
            style="Title.TLabel"
        )
        title_label.pack()
        
        # 子标题
        subtitle_label = ttk.Label(
            header_frame,
            text="渐进间隔提醒 · 专注学习好帮手",
            font=('Helvetica', 10)
        )
        subtitle_label.pack()
        
        # 分隔线
        separator = ttk.Separator(header_frame, orient='horizontal')
        separator.pack(fill='x', pady=(10, 0))
        
    def _create_config_section(self, parent):
        """创建配置区域"""
        config_frame = ttk.LabelFrame(parent, text="📝 基础配置", padding=15)
        config_frame.pack(fill="x", pady=(0, 15))
        
        # URL配置
        url_frame = ttk.Frame(config_frame)
        url_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(url_frame, text="目标网址：").pack(anchor="w")
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=('Helvetica', 10))
        url_entry.pack(fill="x", pady=(5, 0))
        
        # Chrome路径配置
        chrome_frame = ttk.Frame(config_frame)
        chrome_frame.pack(fill="x", pady=(0, 10))
        
        chrome_label_frame = ttk.Frame(chrome_frame)
        chrome_label_frame.pack(fill="x")
        
        ttk.Label(chrome_label_frame, text="浏览器路径（可选）：").pack(side="left")
        
        browse_btn = ttk.Button(
            chrome_label_frame, 
            text="📁 浏览", 
            command=self._browse_chrome,
            width=8
        )
        browse_btn.pack(side="right")
        
        self.chrome_var = tk.StringVar()
        chrome_entry = ttk.Entry(chrome_frame, textvariable=self.chrome_var, font=('Helvetica', 10))
        chrome_entry.pack(fill="x", pady=(5, 0))
        
        # 时间配置
        time_frame = ttk.Frame(config_frame)
        time_frame.pack(fill="x")
        
        # 第一行：总时长
        time_row1 = ttk.Frame(time_frame)
        time_row1.pack(fill="x", pady=(0, 5))
        
        ttk.Label(time_row1, text="总时长：").pack(side="left")
        self.total_var = tk.StringVar()
        ttk.Entry(time_row1, textvariable=self.total_var, width=8).pack(side="left", padx=(5, 2))
        ttk.Label(time_row1, text="分钟").pack(side="left")
        
        # 第二行：间隔配置
        time_row2 = ttk.Frame(time_frame)
        time_row2.pack(fill="x")
        
        ttk.Label(time_row2, text="第1次：").pack(side="left")
        self.first_var = tk.StringVar()
        ttk.Entry(time_row2, textvariable=self.first_var, width=6).pack(side="left", padx=(5, 2))
        ttk.Label(time_row2, text="分").pack(side="left", padx=(0, 10))
        
        ttk.Label(time_row2, text="第2次：").pack(side="left")
        self.second_var = tk.StringVar()
        ttk.Entry(time_row2, textvariable=self.second_var, width=6).pack(side="left", padx=(5, 2))
        ttk.Label(time_row2, text="分").pack(side="left", padx=(0, 10))
        
        ttk.Label(time_row2, text="后续：").pack(side="left")
        self.subseq_var = tk.StringVar()
        ttk.Entry(time_row2, textvariable=self.subseq_var, width=6).pack(side="left", padx=(5, 2))
        ttk.Label(time_row2, text="分").pack(side="left")
        
    def _create_control_section(self, parent):
        """创建控制区域"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill="x", pady=(0, 15))
        
        # 主要控制按钮
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack()
        
        self.start_btn = ttk.Button(
            btn_frame, 
            text="🚀 启动提醒", 
            command=self.start,
            style="Primary.TButton",
            width=15
        )
        self.start_btn.pack(side="left", padx=(0, 10))
        
        self.stop_btn = ttk.Button(
            btn_frame, 
            text="⏹ 停止", 
            command=self.stop,
            state="disabled",
            width=15
        )
        self.stop_btn.pack(side="left", padx=(0, 10))
        
        # 设置按钮
        settings_btn = ttk.Button(
            btn_frame,
            text="⚙️ 保存配置",
            command=self._save_settings,
            width=15
        )
        settings_btn.pack(side="left")
        
    def _create_status_section(self, parent):
        """创建状态显示区域"""
        status_frame = ttk.LabelFrame(parent, text="📊 运行状态", padding=15)
        status_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # 当前状态
        self.status_var = tk.StringVar(value="待机中...")
        status_label = ttk.Label(
            status_frame, 
            textvariable=self.status_var,
            style="Status.TLabel"
        )
        status_label.pack(pady=(0, 10))
        
        # 倒计时显示区域
        countdown_frame = ttk.Frame(status_frame)
        countdown_frame.pack(fill="x", pady=(0, 15))
        
        # 下次提醒倒计时
        next_frame = ttk.Frame(countdown_frame)
        next_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(next_frame, text="下次提醒：").pack(side="left")
        self.next_var = tk.StringVar(value="--:--")
        ttk.Label(next_frame, textvariable=self.next_var, style="BigNumber.TLabel").pack(side="left")
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            countdown_frame,
            mode='determinate',
            variable=self.progress_var,
            length=400
        )
        self.progress_bar.pack(fill="x", pady=(5, 10))
        
        # 统计信息
        stats_frame = ttk.Frame(status_frame)
        stats_frame.pack(fill="x")
        
        # 左侧统计
        left_stats = ttk.Frame(stats_frame)
        left_stats.pack(side="left", fill="x", expand=True)
        
        self.count_var = tk.StringVar(value="已提醒：0 次")
        ttk.Label(left_stats, textvariable=self.count_var).pack(anchor="w")
        
        self.elapsed_var = tk.StringVar(value="已用时：0:00 / 1:00")
        ttk.Label(left_stats, textvariable=self.elapsed_var).pack(anchor="w")
        
    def _create_sound_section(self, parent):
        """创建音效设置区域"""
        sound_frame = ttk.LabelFrame(parent, text="🔊 音效设置", padding=10)
        sound_frame.pack(fill="x")
        
        # 音效开关
        sound_control_frame = ttk.Frame(sound_frame)
        sound_control_frame.pack(fill="x", pady=(0, 10))
        
        self.sound_enabled_var = tk.BooleanVar()
        sound_check = ttk.Checkbutton(
            sound_control_frame,
            text="启用提醒音效",
            variable=self.sound_enabled_var,
            command=self._toggle_sound
        )
        sound_check.pack(side="left")
        
        # 测试音效按钮
        test_sound_btn = ttk.Button(
            sound_control_frame,
            text="🔊 测试",
            command=self._test_sound,
            width=8
        )
        test_sound_btn.pack(side="right")
        
        # 自定义音效文件
        sound_file_frame = ttk.Frame(sound_frame)
        sound_file_frame.pack(fill="x")
        
        sound_file_label_frame = ttk.Frame(sound_file_frame)
        sound_file_label_frame.pack(fill="x")
        
        ttk.Label(sound_file_label_frame, text="自定义音效文件：").pack(side="left")
        
        browse_sound_btn = ttk.Button(
            sound_file_label_frame,
            text="📁 选择",
            command=self._browse_sound_file,
            width=8
        )
        browse_sound_btn.pack(side="right")
        
        self.sound_file_var = tk.StringVar()
        sound_file_entry = ttk.Entry(sound_file_frame, textvariable=self.sound_file_var, font=('Helvetica', 9))
        sound_file_entry.pack(fill="x", pady=(5, 0))
        
    def _browse_chrome(self):
        """浏览选择Chrome浏览器路径"""
        if sys.platform == 'darwin':
            # macOS
            filename = filedialog.askopenfilename(
                title="选择浏览器应用",
                filetypes=[("应用程序", "*.app"), ("所有文件", "*.*")],
                initialdir="/Applications"
            )
        elif sys.platform == 'win32':
            # Windows
            filename = filedialog.askopenfilename(
                title="选择浏览器程序",
                filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
                initialdir="C:/Program Files"
            )
        else:
            # Linux
            filename = filedialog.askopenfilename(
                title="选择浏览器程序",
                filetypes=[("所有文件", "*.*")],
                initialdir="/usr/bin"
            )
            
        if filename:
            self.chrome_var.set(filename)
            
    def _browse_sound_file(self):
        """浏览选择音效文件"""
        filename = filedialog.askopenfilename(
            title="选择音效文件",
            filetypes=[
                ("音频文件", "*.wav *.mp3 *.ogg *.m4a"),
                ("WAV文件", "*.wav"),
                ("MP3文件", "*.mp3"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.sound_file_var.set(filename)
            
    def _toggle_sound(self):
        """切换音效开关"""
        # 可以在这里添加额外的逻辑
        pass
        
    def _test_sound(self):
        """测试音效"""
        if self.sound_enabled_var.get():
            sound_file = self.sound_file_var.get().strip()
            if not sound_file:
                sound_file = None
            self.sound_manager.play_notification(sound_file)
        else:
            messagebox.showinfo("提示", "请先启用音效功能")
            
    def _load_settings(self):
        """加载设置到界面"""
        self.url_var.set(self.config.get('url', DEFAULTS['url']))
        self.total_var.set(str(self.config.get('total_min', DEFAULTS['total_min'])))
        self.first_var.set(str(self.config.get('first_min', DEFAULTS['first_min'])))
        self.second_var.set(str(self.config.get('second_min', DEFAULTS['second_min'])))
        self.subseq_var.set(str(self.config.get('subseq_min', DEFAULTS['subseq_min'])))
        self.chrome_var.set(self.config.get('chrome_path', DEFAULTS['chrome_path']))
        self.sound_enabled_var.set(self.config.get('sound_enabled', DEFAULTS['sound_enabled']))
        self.sound_file_var.set(self.config.get('sound_file', DEFAULTS['sound_file']))
        
    def _save_settings(self):
        """保存当前设置"""
        try:
            self.config['url'] = self.url_var.get().strip()
            self.config['total_min'] = int(self.total_var.get())
            self.config['first_min'] = int(self.first_var.get())
            self.config['second_min'] = int(self.second_var.get())
            self.config['subseq_min'] = int(self.subseq_var.get())
            self.config['chrome_path'] = self.chrome_var.get().strip()
            self.config['sound_enabled'] = self.sound_enabled_var.get()
            self.config['sound_file'] = self.sound_file_var.get().strip()
            
            self.config_manager.save_config(self.config)
            messagebox.showinfo("成功", "配置已保存！")
        except ValueError as e:
            messagebox.showerror("错误", "配置格式错误，请检查数值输入")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败：{str(e)}")
            
    def start(self):
        """启动提醒"""
        if self.running:
            return
            
        try:
            # 验证输入
            url = self.url_var.get().strip()
            if not (url.startswith("http://") or url.startswith("https://")):
                raise ValueError("URL 必须以 http:// 或 https:// 开头")
            
            total_min = int(self.total_var.get())
            first_min = int(self.first_var.get())
            second_min = int(self.second_var.get())
            subseq_min = int(self.subseq_var.get())
            
            if min(total_min, first_min, second_min, subseq_min) <= 0:
                raise ValueError("所有时间必须为正整数")
            
            # 设置参数
            self.url = url
            self.total_sec = total_min * 60
            self.intervals = [first_min * 60, second_min * 60]
            self.subseq_sec = subseq_min * 60
            
            # 浏览器设置
            self.chrome_path = self.chrome_var.get().strip()
            self.browser = None
            if self.chrome_path:
                try:
                    self.browser = webbrowser.get(self.chrome_path)
                except Exception as e:
                    messagebox.showwarning("浏览器设置", f"无法使用指定浏览器路径，将使用默认浏览器。\n{str(e)}")
                    self.browser = None
            
        except Exception as e:
            messagebox.showerror("参数错误", str(e))
            return
        
        # 初始化状态
        self.running = True
        self.elapsed = 0
        self.count = 0
        self.seconds_until_next = 0
        self.pending_wait = 0
        
        # 更新UI
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("🟢 运行中...")
        
        # 立即打开一次
        self._open_now()
        # 安排下一次
        self._schedule_next()
        # 开始计时
        self._tick()
        
    def stop(self):
        """停止提醒"""
        if not self.running:
            return
            
        self.running = False
        
        # 取消定时器
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
            
        if self.animation_after_id:
            self.root.after_cancel(self.animation_after_id)
            self.animation_after_id = None
        
        # 更新UI
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("⏹ 已停止")
        self.progress_var.set(0)
        
    def _open_now(self):
        """立即打开URL"""
        self.count += 1
        self.count_var.set(f"已提醒：{self.count} 次")
        
        try:
            if self.browser:
                self.browser.open(self.url)
            else:
                webbrowser.open(self.url)
                
            self.status_var.set(f"🔔 第 {self.count} 次提醒已触发")
            
            # 播放音效
            if self.sound_enabled_var.get():
                sound_file = self.sound_file_var.get().strip()
                if not sound_file:
                    sound_file = None
                threading.Thread(target=lambda: self.sound_manager.play_notification(sound_file), daemon=True).start()
                
        except Exception as e:
            self.status_var.set(f"❌ 打开失败：{str(e)}")
            
    def _schedule_next(self):
        """安排下一次提醒"""
        # 计算等待时间
        if self.count <= len(self.intervals):
            wait = self.intervals[self.count - 1]
        else:
            wait = self.subseq_sec
            
        # 检查是否会超出总时长
        if self.elapsed + wait >= self.total_sec:
            self.next_var.set("已完成所有提醒")
            self.stop()
            messagebox.showinfo("完成", "所有提醒已完成！")
            return
            
        self.pending_wait = wait
        self.seconds_until_next = wait
        self._update_display()
        
    def _tick(self):
        """定时器心跳"""
        if not self.running:
            return
            
        if self.seconds_until_next > 0:
            self.seconds_until_next -= 1
            self._update_display()
            self.after_id = self.root.after(1000, self._tick)
        else:
            # 时间到，执行提醒
            self.elapsed += self.pending_wait
            self._open_now()
            self._schedule_next()
            if self.running:  # 如果还在运行中
                self.after_id = self.root.after(1000, self._tick)
                
    def _update_display(self):
        """更新显示"""
        # 更新倒计时显示
        mm, ss = divmod(self.seconds_until_next, 60)
        self.next_var.set(f"{mm:02d}:{ss:02d}")
        
        # 更新进度条
        if self.pending_wait > 0:
            progress = ((self.pending_wait - self.seconds_until_next) / self.pending_wait) * 100
            self.progress_var.set(progress)
        
        # 更新已用时间
        total_mm, total_ss = divmod(self.total_sec, 60)
        el_mm, el_ss = divmod(self.elapsed, 60)
        self.elapsed_var.set(f"已用时：{el_mm}:{el_ss:02d} / {total_mm}:{total_ss:02d}")
        
    def _on_closing(self):
        """关闭窗口时的处理"""
        self.stop()
        self.root.destroy()

def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置窗口居中
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"+{x}+{y}")
    
    # 创建应用
    app = ReminderApp(root)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    main()
