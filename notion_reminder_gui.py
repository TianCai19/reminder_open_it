#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
try:
    import winsound  # Windows音效支持
except ImportError:
    winsound = None

"""
Python 定时提醒 GUI
- 启动后立即打开一次 URL
- 之后按 5 分钟 → 10 分钟 → 每次 15 分钟 的间隔打开
- 直到总时长(默认 60 分钟)被消耗完
- 支持可选 Chrome 路径；未填写时使用系统默认浏览器
"""

DEFAULTS = {
    "url": "https://www.notion.so/codetwice/Aug-18-2497c4668c0d8021a532fbbfa641a265",
    "total_min": 60,
    "first_min": 5,
    "second_min": 10,
    "subseq_min": 15,
    "chrome_path": "",  # 例如：Mac: open -a /Applications/Google\\ Chrome.app %s
                       #       Win: C:/Program Files/Google/Chrome/Application/chrome.exe %s
    "sound_enabled": True,  # 音效开关
}

# 应用主题配色
COLORS = {
    "primary": "#2563eb",      # 蓝色主色调
    "primary_dark": "#1d4ed8", # 深蓝色
    "secondary": "#10b981",    # 绿色辅助色
    "warning": "#f59e0b",      # 橙色警告
    "danger": "#ef4444",       # 红色危险
    "success": "#22c55e",      # 绿色成功
    "info": "#06b6d4",         # 青色信息
    "light": "#f8fafc",        # 浅色背景
    "dark": "#1e293b",         # 深色背景
    "text_primary": "#1f2937", # 主要文字
    "text_secondary": "#6b7280", # 次要文字
}

class SoundPlayer:
    """简单的音效播放器，支持跨平台"""
    def __init__(self):
        self.enabled = DEFAULTS["sound_enabled"]
    
    def _beep_linux_mac(self, frequency=800, duration=0.1):
        """Linux/Mac 音效实现"""
        try:
            # 尝试使用系统beep
            os.system(f"beep -f {frequency} -l {int(duration*1000)} 2>/dev/null")
        except:
            # 备用方案：打印响铃字符
            print('\a', end='', flush=True)
    
    def _beep_windows(self, frequency=800, duration=0.1):
        """Windows 音效实现"""
        if winsound:
            try:
                winsound.Beep(int(frequency), int(duration*1000))
            except:
                print('\a', end='', flush=True)
        else:
            print('\a', end='', flush=True)
    
    def play_sound(self, sound_type="default"):
        """播放音效"""
        if not self.enabled:
            return
        
        def play():
            try:
                if sound_type == "start":
                    # 启动音：上升音调
                    frequencies = [440, 554, 659]
                    for freq in frequencies:
                        self._play_beep(freq, 0.1)
                        time.sleep(0.05)
                elif sound_type == "stop":
                    # 停止音：下降音调
                    frequencies = [659, 554, 440]
                    for freq in frequencies:
                        self._play_beep(freq, 0.1)
                        time.sleep(0.05)
                elif sound_type == "open":
                    # 打开音：双重提示音
                    self._play_beep(800, 0.1)
                    time.sleep(0.1)
                    self._play_beep(1000, 0.1)
                elif sound_type == "warning":
                    # 警告音：急促的嘟嘟声
                    for _ in range(3):
                        self._play_beep(1200, 0.1)
                        time.sleep(0.1)
                elif sound_type == "complete":
                    # 完成音：欢快的音调
                    frequencies = [523, 659, 784, 1047]
                    for freq in frequencies:
                        self._play_beep(freq, 0.15)
                        time.sleep(0.05)
                else:
                    # 默认提示音
                    self._play_beep(800, 0.2)
            except Exception:
                pass  # 音效失败不影响主功能
        
        # 在后台线程播放音效，避免阻塞UI
        threading.Thread(target=play, daemon=True).start()
    
    def _play_beep(self, frequency, duration):
        """根据平台播放音效"""
        try:
            import platform
            if platform.system() == "Windows":
                self._beep_windows(frequency, duration)
            else:
                self._beep_linux_mac(frequency, duration)
        except:
            print('\a', end='', flush=True)
    
    def toggle(self):
        """切换音效开关"""
        self.enabled = not self.enabled
        return self.enabled

class ReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 定时提醒 · 智能渐进间隔")
        self.root.geometry("720x420")
        self.root.configure(bg=COLORS["light"])
        
        # 设置窗口图标和样式
        try:
            self.root.iconbitmap(default='assets/icon.ico')
        except:
            pass
        
        # 音效系统
        self.sound_player = SoundPlayer()

        # 状态
        self.running = False
        self.after_id = None
        self.elapsed = 0               # 已消耗的等待时间（秒）
        self.count = 0                 # 已打开次数
        self.seconds_until_next = 0    # 距离下次打开的倒计时（秒）
        self.pending_wait = 0          # 当前这轮计划等待（秒）

        # UI样式配置
        self._configure_styles()
        
        # UI
        self._build_ui()
        self._set_defaults()
        
        # 启动时的欢迎音效
        self.root.after(500, lambda: self.sound_player.play_sound("default"))
    
    def _configure_styles(self):
        """配置应用样式主题"""
        style = ttk.Style()
        
        # 尝试设置现代主题
        try:
            # 优先尝试使用现代主题
            available_themes = style.theme_names()
            if 'clam' in available_themes:
                style.theme_use('clam')
            elif 'alt' in available_themes:
                style.theme_use('alt')
        except:
            pass
        
        # 自定义样式配置
        style.configure('Title.TLabel', 
                       font=('Helvetica', 16, 'bold'),
                       foreground=COLORS["primary"],
                       background=COLORS["light"])
        
        style.configure('Heading.TLabel',
                       font=('Helvetica', 12, 'bold'),
                       foreground=COLORS["text_primary"],
                       background=COLORS["light"])
        
        style.configure('Status.TLabel',
                       font=('Helvetica', 11),
                       foreground=COLORS["text_secondary"],
                       background=COLORS["light"])
        
        style.configure('Primary.TButton',
                       font=('Helvetica', 10, 'bold'),
                       foreground='white',
                       background=COLORS["primary"])
        
        style.configure('Success.TButton',
                       font=('Helvetica', 10, 'bold'),
                       foreground='white',
                       background=COLORS["success"])
        
        style.configure('Danger.TButton',
                       font=('Helvetica', 10, 'bold'),
                       foreground='white',
                       background=COLORS["danger"])
        
        style.configure('Info.TProgressbar',
                       background=COLORS["info"],
                       troughcolor=COLORS["light"],
                       borderwidth=1)
        
        # Frame样式
        style.configure('Card.TFrame',
                       background=COLORS["light"],
                       borderwidth=1,
                       relief='solid')
        
        style.configure('Header.TFrame',
                       background=COLORS["primary"],
                       borderwidth=0)

    def _build_ui(self):
        # 主容器
        main_frame = ttk.Frame(self.root, style='Card.TFrame')
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题区域
        header_frame = ttk.Frame(main_frame, style='Header.TFrame')
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_label = ttk.Label(header_frame, 
                               text="🎯 智能定时提醒系统", 
                               style='Title.TLabel')
        title_label.pack(pady=10)
        
        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="⚙️ 配置参数", padding=10)
        config_frame.pack(fill="x", pady=(0, 10))
        
        # URL配置
        url_frame = ttk.Frame(config_frame)
        url_frame.pack(fill="x", pady=2)
        ttk.Label(url_frame, text="🌐 目标网址：", style='Heading.TLabel').pack(side="left")
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=('Consolas', 10))
        url_entry.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Chrome路径配置
        chrome_frame = ttk.Frame(config_frame)
        chrome_frame.pack(fill="x", pady=2)
        ttk.Label(chrome_frame, text="🌏 浏览器路径(可选)：", style='Heading.TLabel').pack(side="left")
        self.chrome_var = tk.StringVar()
        chrome_entry = ttk.Entry(chrome_frame, textvariable=self.chrome_var, font=('Consolas', 9))
        chrome_entry.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # 时间参数配置
        time_frame = ttk.Frame(config_frame)
        time_frame.pack(fill="x", pady=5)
        
        # 第一行：总时长
        row1 = ttk.Frame(time_frame)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="⏱️ 总时长(分钟)：", style='Heading.TLabel').grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.total_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.total_var, width=8, font=('Arial', 10, 'bold')).grid(row=0, column=1, sticky="w")
        
        # 第二行：间隔配置
        row2 = ttk.Frame(time_frame)
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="🔄 第1次间隔：", style='Status.TLabel').grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.first_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.first_var, width=6).grid(row=0, column=1, sticky="w")
        ttk.Label(row2, text="min", style='Status.TLabel').grid(row=0, column=2, sticky="w", padx=(2, 15))
        
        ttk.Label(row2, text="🔄 第2次间隔：", style='Status.TLabel').grid(row=0, column=3, sticky="w", padx=(0, 5))
        self.second_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.second_var, width=6).grid(row=0, column=4, sticky="w")
        ttk.Label(row2, text="min", style='Status.TLabel').grid(row=0, column=5, sticky="w", padx=(2, 15))
        
        ttk.Label(row2, text="🔄 后续固定：", style='Status.TLabel').grid(row=0, column=6, sticky="w", padx=(0, 5))
        self.subseq_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.subseq_var, width=6).grid(row=0, column=7, sticky="w")
        ttk.Label(row2, text="min", style='Status.TLabel').grid(row=0, column=8, sticky="w", padx=(2, 0))
        
        # 控制按钮区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=10)
        
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(side="left")
        
        self.start_btn = ttk.Button(buttons_frame, text="🚀 启动", 
                                   command=self.start, style='Primary.TButton')
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(buttons_frame, text="⏹️ 停止", 
                                  command=self.stop, style='Danger.TButton', 
                                  state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        # 音效开关
        sound_frame = ttk.Frame(control_frame)
        sound_frame.pack(side="right")
        
        self.sound_var = tk.BooleanVar(value=DEFAULTS["sound_enabled"])
        sound_check = ttk.Checkbutton(sound_frame, text="🔊 音效", 
                                     variable=self.sound_var,
                                     command=self._toggle_sound)
        sound_check.pack(side="right", padx=10)
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(main_frame, text="📊 运行状态", padding=10)
        status_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # 主要状态信息
        status_info_frame = ttk.Frame(status_frame)
        status_info_frame.pack(fill="x", pady=(0, 10))
        
        self.status_var = tk.StringVar(value="状态：💤 待机中")
        self.status_label = ttk.Label(status_info_frame, textvariable=self.status_var, 
                                     font=("Helvetica", 12, "bold"),
                                     foreground=COLORS["info"])
        self.status_label.pack(anchor="w")
        
        # 进度条区域
        progress_frame = ttk.Frame(status_frame)
        progress_frame.pack(fill="x", pady=5)
        
        ttk.Label(progress_frame, text="⏳ 总体进度：", style='Status.TLabel').pack(anchor="w")
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                           variable=self.progress_var,
                                           length=400)
        self.progress_bar.pack(fill="x", pady=2)
        
        # 倒计时进度条
        ttk.Label(progress_frame, text="⏱️ 当前倒计时：", style='Status.TLabel').pack(anchor="w", pady=(10, 0))
        self.countdown_var = tk.DoubleVar()
        self.countdown_bar = ttk.Progressbar(progress_frame,
                                            variable=self.countdown_var,
                                            length=400)
        self.countdown_bar.pack(fill="x", pady=2)
        
        # 详细信息显示
        details_frame = ttk.Frame(status_frame)
        details_frame.pack(fill="x", pady=(10, 0))
        
        # 使用网格布局显示详细信息
        self.next_var = tk.StringVar(value="⏰ 下次打开：--:--")
        ttk.Label(details_frame, textvariable=self.next_var, 
                 font=("Helvetica", 11), foreground=COLORS["warning"]).grid(row=0, column=0, sticky="w", pady=2)
        
        self.count_var = tk.StringVar(value="🔢 已打开次数：0 次")
        ttk.Label(details_frame, textvariable=self.count_var,
                 font=("Helvetica", 11), foreground=COLORS["success"]).grid(row=1, column=0, sticky="w", pady=2)
        
        self.elapsed_var = tk.StringVar(value="📊 已消耗/总时长：0:00 / 1:00")
        ttk.Label(details_frame, textvariable=self.elapsed_var,
                 font=("Helvetica", 11), foreground=COLORS["primary"]).grid(row=2, column=0, sticky="w", pady=2)
        
        # 确保网格布局的权重
        details_frame.columnconfigure(0, weight=1)

    def _set_defaults(self):
        self.url_var.set(DEFAULTS["url"])
        self.total_var.set(str(DEFAULTS["total_min"]))
        self.first_var.set(str(DEFAULTS["first_min"]))
        self.second_var.set(str(DEFAULTS["second_min"]))
        self.subseq_var.set(str(DEFAULTS["subseq_min"]))
        self.chrome_var.set(DEFAULTS["chrome_path"])
        self.sound_var.set(DEFAULTS["sound_enabled"])
    
    def _toggle_sound(self):
        """切换音效开关"""
        enabled = self.sound_player.toggle()
        if enabled:
            self.sound_player.play_sound("default")
        # 更新默认设置
        DEFAULTS["sound_enabled"] = enabled

    # 业务逻辑 --------------------------------------------------------------

    def start(self):
        if self.running:
            return
        try:
            url = self.url_var.get().strip()
            if not (url.startswith("http://") or url.startswith("https://")):
                raise ValueError("URL 必须以 http(s):// 开头")

            total_min = int(self.total_var.get())
            first_min = int(self.first_var.get())
            second_min = int(self.second_var.get())
            subseq_min = int(self.subseq_var.get())
            if min(total_min, first_min, second_min, subseq_min) <= 0:
                raise ValueError("所有时间必须为正整数")

            self.url = url
            self.total_sec = total_min * 60
            self.intervals = [first_min * 60, second_min * 60]
            self.subseq_sec = subseq_min * 60

            # 浏览器
            self.chrome_path = self.chrome_var.get().strip()
            self.browser = None
            if self.chrome_path:
                try:
                    self.browser = webbrowser.get(self.chrome_path)
                except Exception as e:
                    messagebox.showwarning("浏览器注册失败", f"无法使用提供的 Chrome 路径。\n将改用系统默认浏览器。\n\n详细：{e}")
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
        
        # UI状态更新
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("状态：🚀 启动中...")
        self.status_label.config(foreground=COLORS["success"])
        
        # 初始化进度条
        self.progress_var.set(0)
        self.countdown_var.set(100)
        
        # 播放启动音效
        self.sound_player.play_sound("start")
        
        # 启动流程
        self._open_now()        # 启动即打开一次
        self._schedule_next()   # 安排下一次
        self._tick()            # 开启 1s 心跳

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.after_id:
            try:
                self.root.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None
        
        # UI状态更新
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("状态：⏹️ 已停止")
        self.status_label.config(foreground=COLORS["danger"])
        
        # 重置进度条
        self.countdown_var.set(0)
        
        # 播放停止音效
        self.sound_player.play_sound("stop")

    def _open_now(self):
        self.count += 1
        self.count_var.set(f"🔢 已打开次数：{self.count} 次")
        try:
            if self.browser:
                self.browser.open(self.url)
            else:
                webbrowser.open(self.url)
            self.status_var.set(f"状态：✅ 已打开 (第 {self.count} 次)")
            self.status_label.config(foreground=COLORS["success"])
            
            # 播放打开音效
            self.sound_player.play_sound("open")
            
        except Exception as e:
            self.status_var.set(f"状态：❌ 打开失败：{e}")
            self.status_label.config(foreground=COLORS["danger"])

    def _schedule_next(self):
        # 计算下一次等待（遵循 5 → 10 → 15…）
        if self.count <= len(self.intervals):
            wait = self.intervals[self.count - 1]
        else:
            wait = self.subseq_sec

        # 如果等待后会超出总时长，就不再安排下一次
        if self.elapsed + wait >= self.total_sec:
            self.next_var.set("⏰ 下次打开：无（总时长已达成）")
            # 播放完成音效
            self.sound_player.play_sound("complete")
            self.status_var.set("状态：🎉 任务完成！")
            self.status_label.config(foreground=COLORS["success"])
            self.stop()
            return

        self.pending_wait = wait
        self.seconds_until_next = wait
        self._refresh_time_labels()

    def _tick(self):
        if not self.running:
            return
        # 每秒更新一次倒计时
        if self.seconds_until_next > 0:
            self.seconds_until_next -= 1
            
            # 在倒计时最后10秒播放警告音
            if self.seconds_until_next == 10:
                self.sound_player.play_sound("warning")
                self.status_var.set("状态：⚠️ 即将打开（10秒倒计时）")
                self.status_label.config(foreground=COLORS["warning"])
            elif self.seconds_until_next == 5:
                self.status_var.set("状态：⚠️ 即将打开（5秒倒计时）")
            elif self.seconds_until_next == 0:
                self.status_var.set("状态：🔄 正在准备打开...")
                
            self._refresh_time_labels()
            self.after_id = self.root.after(1000, self._tick)
        else:
            # 本轮等待结束，累计并执行
            self.elapsed += self.pending_wait
            self._open_now()
            self._schedule_next()
            self.after_id = self.root.after(1000, self._tick)

    # UI 辅助 --------------------------------------------------------------

    def _refresh_time_labels(self):
        # 下次打开倒计时
        mm, ss = divmod(self.seconds_until_next, 60)
        self.next_var.set(f"⏰ 下次打开：{mm:02d}:{ss:02d}")

        # 已消耗/总时长
        total_mm, total_ss = divmod(self.total_sec, 60)
        el_mm, el_ss = divmod(self.elapsed, 60)
        self.elapsed_var.set(f"📊 已消耗/总时长：{el_mm}:{el_ss:02d} / {total_mm}:{total_ss:02d}")
        
        # 更新进度条
        if self.total_sec > 0:
            # 总体进度
            total_progress = (self.elapsed / self.total_sec) * 100
            self.progress_var.set(total_progress)
            
            # 当前倒计时进度（反向显示，剩余时间越少进度越高）
            if self.pending_wait > 0:
                countdown_progress = ((self.pending_wait - self.seconds_until_next) / self.pending_wait) * 100
                self.countdown_var.set(countdown_progress)
            else:
                self.countdown_var.set(0)

def main():
    root = tk.Tk()
    # 设置应用基本属性
    root.resizable(True, True)
    root.minsize(700, 400)
    
    # 创建应用实例
    app = ReminderApp(root)
    
    # 启动事件循环
    root.mainloop()

if __name__ == "__main__":
    main()

