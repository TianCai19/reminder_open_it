#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

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
    "chrome_path": ""  # 例如：Mac: open -a /Applications/Google\\ Chrome.app %s
                       #       Win: C:/Program Files/Google/Chrome/Application/chrome.exe %s
}

class ReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("定时提醒 · 渐进间隔 (5→10→15)")
        self.root.geometry("680x360")

        # 状态
        self.running = False
        self.after_id = None
        self.elapsed = 0               # 已消耗的等待时间（秒）
        self.count = 0                 # 已打开次数
        self.seconds_until_next = 0    # 距离下次打开的倒计时（秒）
        self.pending_wait = 0          # 当前这轮计划等待（秒）

        # UI
        self._build_ui()
        self._set_defaults()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        frm = ttk.Frame(self.root)
        frm.pack(fill="both", expand=True, **pad)

        # URL
        ttk.Label(frm, text="目标 URL：").grid(row=0, column=0, sticky="e")
        self.url_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.url_var, width=60).grid(row=0, column=1, columnspan=3, sticky="we")

        # Chrome 路径（可选）
        ttk.Label(frm, text="Chrome 路径(可选)：").grid(row=1, column=0, sticky="e")
        self.chrome_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.chrome_var, width=60).grid(row=1, column=1, columnspan=3, sticky="we")

        # 参数
        ttk.Label(frm, text="总时长(分钟)：").grid(row=2, column=0, sticky="e")
        self.total_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.total_var, width=10).grid(row=2, column=1, sticky="w")

        ttk.Label(frm, text="第1次间隔(分钟)：").grid(row=3, column=0, sticky="e")
        self.first_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.first_var, width=10).grid(row=3, column=1, sticky="w")

        ttk.Label(frm, text="第2次间隔(分钟)：").grid(row=3, column=2, sticky="e")
        self.second_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.second_var, width=10).grid(row=3, column=3, sticky="w")

        ttk.Label(frm, text="后续固定(分钟)：").grid(row=4, column=0, sticky="e")
        self.subseq_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.subseq_var, width=10).grid(row=4, column=1, sticky="w")

        # 控制按钮
        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=4, sticky="we", pady=10)
        self.start_btn = ttk.Button(btns, text="启动", command=self.start)
        self.stop_btn = ttk.Button(btns, text="停止", command=self.stop, state="disabled")
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn.pack(side="left", padx=5)

        # 状态显示
        sep = ttk.Separator(frm, orient="horizontal")
        sep.grid(row=6, column=0, columnspan=4, sticky="we", pady=6)

        self.status_var = tk.StringVar(value="状态：待机")
        ttk.Label(frm, textvariable=self.status_var, font=("Helvetica", 11)).grid(row=7, column=0, columnspan=4, sticky="w")

        self.next_var = tk.StringVar(value="下次打开：--:--")
        ttk.Label(frm, textvariable=self.next_var, font=("Helvetica", 11)).grid(row=8, column=0, columnspan=4, sticky="w")

        self.count_var = tk.StringVar(value="已打开次数：0 次")
        ttk.Label(frm, textvariable=self.count_var).grid(row=9, column=0, columnspan=4, sticky="w")

        self.elapsed_var = tk.StringVar(value="已消耗/总时长：0:00 / 1:00")
        ttk.Label(frm, textvariable=self.elapsed_var).grid(row=10, column=0, columnspan=4, sticky="w")

        frm.columnconfigure(1, weight=1)
        frm.columnconfigure(3, weight=1)

    def _set_defaults(self):
        self.url_var.set(DEFAULTS["url"])
        self.total_var.set(str(DEFAULTS["total_min"]))
        self.first_var.set(str(DEFAULTS["first_min"]))
        self.second_var.set(str(DEFAULTS["second_min"]))
        self.subseq_var.set(str(DEFAULTS["subseq_min"]))
        self.chrome_var.set(DEFAULTS["chrome_path"])

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
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("状态：运行中")
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
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("状态：已停止")

    def _open_now(self):
        self.count += 1
        self.count_var.set(f"已打开次数：{self.count} 次")
        try:
            if self.browser:
                self.browser.open(self.url)
            else:
                webbrowser.open(self.url)
            self.status_var.set(f"状态：已打开 (第 {self.count} 次)")
        except Exception as e:
            self.status_var.set(f"状态：打开失败：{e}")

    def _schedule_next(self):
        # 计算下一次等待（遵循 5 → 10 → 15…）
        if self.count <= len(self.intervals):
            wait = self.intervals[self.count - 1]
        else:
            wait = self.subseq_sec

        # 如果等待后会超出总时长，就不再安排下一次
        if self.elapsed + wait >= self.total_sec:
            self.next_var.set("下次打开：无（总时长已达成）")
            # 到此就等待倒计时结束（若有）或直接停
            # 此处直接停止，因为我们在每次打开后立即安排下一次
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
        self.next_var.set(f"下次打开：{mm:02d}:{ss:02d}")

        # 已消耗/总时长
        total_mm, total_ss = divmod(self.total_sec, 60)
        el_mm, el_ss = divmod(self.elapsed, 60)
        self.elapsed_var.set(f"已消耗/总时长：{el_mm}:{el_ss:02d} / {total_mm}:{total_ss:02d}")

def main():
    root = tk.Tk()
    # 统一风格
    try:
        root.call("source", "sun-valley.tcl")  # 若无此主题会跳过
        ttk.Style().theme_use("sun-valley-dark")
    except Exception:
        pass
    ReminderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

