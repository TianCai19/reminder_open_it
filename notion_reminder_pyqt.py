#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt 版提醒助手
- 渐进间隔提醒：第1/2次单独间隔，之后固定间隔，累计到总时长停止
- 立即打开目标 URL，并可指定浏览器路径
- 音效提醒（pygame）
- 历史持久化：history.json；显示表格 + “今天”24 小时热力方块
- 折叠面板：运行时自动折叠配置/音效面板
"""

import sys
import os
import json
import webbrowser
import threading
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from PyQt5 import QtCore, QtGui, QtWidgets

# 音效支持
try:
    import pygame
    SOUND_AVAILABLE = True
except Exception:
    SOUND_AVAILABLE = False

# 默认配置
DEFAULTS = {
    "url": "https://www.notion.so/",
    "total_min": 60,
    "first_min": 5,
    "second_min": 10,
    "subseq_min": 15,
    "chrome_path": "",
    "sound_enabled": True,
    "sound_file": "default_reminder.mp3",
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
            except Exception:
                self.enabled = False

    def play_notification(self, sound_file=None):
        if not self.enabled or not self.initialized:
            return
        try:
            if sound_file and os.path.exists(sound_file):
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
            elif os.path.exists("default_reminder.mp3"):
                pygame.mixer.music.load("default_reminder.mp3")
                pygame.mixer.music.play()
        except Exception:
            pass


class ConfigManager:
    def __init__(self):
        self.config_file = Path(__file__).parent / "config.json"

    def load(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                result = DEFAULTS.copy()
                result.update(data)
                return result
        except Exception:
            pass
        return DEFAULTS.copy()

    def save(self, config):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


class HistoryManager:
    def __init__(self, max_records=500):
        self.history_file = Path(__file__).parent / "history.json"
        self.max_records = max_records
        self.records = []
        self.load()

    def load(self):
        try:
            if self.history_file.exists():
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self.records = data[-self.max_records :]
        except Exception:
            self.records = []
        return self.records

    def add(self, record):
        self.records.append(record)
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records :]
        self._persist()
        return self.records

    def clear(self):
        self.records = []
        self._persist()

    def _persist(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


class CollapsibleSection(QtWidgets.QWidget):
    """简单折叠面板"""

    def __init__(self, title, content_widget):
        super().__init__()
        self.content = content_widget
        self.toggle_btn = QtWidgets.QToolButton(text=title, checkable=True, checked=True)
        self.toggle_btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.toggle_btn.setArrowType(QtCore.Qt.DownArrow)
        self.toggle_btn.clicked.connect(self._on_toggled)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggle_btn)
        layout.addWidget(self.content)

    def _on_toggled(self, checked):
        self.content.setVisible(checked)
        self.toggle_btn.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)

    def set_collapsed(self, collapsed: bool):
        checked = not collapsed
        self.toggle_btn.setChecked(checked)
        self._on_toggled(checked)


class HourlyHeatmap(QtWidgets.QWidget):
    """今日 24 小时热力方块"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.counts = defaultdict(int)
        self.palette = ["#ebedf0", "#d2f4d1", "#86e29b", "#3fbf74", "#14834f"]
        self.setMinimumHeight(140)

    def set_counts(self, counts):
        self.counts = counts or defaultdict(int)
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        width = self.width()
        margin = 16
        hours = 24
        gap = 8
        cell = max(16, int((width - margin * 2 - gap * (hours - 1)) / hours))
        start_x = (width - (cell * hours + gap * (hours - 1))) // 2
        y0 = 30

        def color_for(count):
            if count == 0:
                return self.palette[0]
            if count == 1:
                return self.palette[1]
            if count <= 3:
                return self.palette[2]
            if count <= 6:
                return self.palette[3]
            return self.palette[4]

        for hour in range(hours):
            x = start_x + hour * (cell + gap)
            rect = QtCore.QRectF(x, y0, cell, cell)
            painter.setBrush(QtGui.QColor(color_for(self.counts.get(hour, 0))))
            painter.setPen(QtGui.QColor("#d0d7de"))
            painter.drawRoundedRect(rect, 3, 3)

            if hour % 6 == 0 or hour == 23:
                painter.setPen(QtGui.QColor("#666"))
                painter.drawText(
                    x,
                    y0 + cell + 14,
                    cell,
                    14,
                    QtCore.Qt.AlignCenter,
                    f"{hour:02d}",
                )

        painter.setPen(QtGui.QColor("#666"))
        painter.drawText(margin, y0 - 12, datetime.now().strftime("今天 %m-%d"))

        # 图例
        legend_y = y0 + cell + 30
        legend_items = [("0", 0), ("1", 1), ("2-3", 2), ("4-6", 4), ("7+", 7)]
        for idx, (label, count) in enumerate(legend_items):
            x = margin + idx * (cell * 2)
            painter.setBrush(QtGui.QColor(color_for(count)))
            painter.setPen(QtGui.QColor("#d0d7de"))
            painter.drawRoundedRect(QtCore.QRectF(x, legend_y, cell, cell), 3, 3)
            painter.setPen(QtGui.QColor("#666"))
            painter.drawText(x + cell + 6, legend_y + cell - 2, label)


class ReminderWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📋 PyQt 智能提醒助手")
        self.resize(900, 760)
        self.config_manager = ConfigManager()
        self.history_manager = HistoryManager()
        self.sound_manager = SoundManager()
        self.config = self.config_manager.load()

        self.running = False
        self.elapsed = 0
        self.count = 0
        self.seconds_until_next = 0
        self.pending_wait = 0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._tick)

        self._build_ui()
        self._load_settings()
        self._refresh_history_view()

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setSpacing(12)

        # 配置
        config_content = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(config_content)
        form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.url_edit = QtWidgets.QLineEdit()
        form.addRow("目标网址", self.url_edit)

        chrome_row = QtWidgets.QHBoxLayout()
        self.chrome_edit = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton("浏览")
        browse_btn.clicked.connect(self._browse_chrome)
        chrome_row.addWidget(self.chrome_edit)
        chrome_row.addWidget(browse_btn)
        chrome_widget = QtWidgets.QWidget()
        chrome_widget.setLayout(chrome_row)
        form.addRow("浏览器路径", chrome_widget)

        self.total_spin = QtWidgets.QSpinBox()
        self.total_spin.setRange(1, 24 * 60)
        form.addRow("总时长(分)", self.total_spin)

        self.first_spin = QtWidgets.QSpinBox()
        self.first_spin.setRange(1, 120)
        self.second_spin = QtWidgets.QSpinBox()
        self.second_spin.setRange(1, 120)
        self.subseq_spin = QtWidgets.QSpinBox()
        self.subseq_spin.setRange(1, 240)

        interval_widget = QtWidgets.QWidget()
        interval_layout = QtWidgets.QHBoxLayout(interval_widget)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_layout.addWidget(QtWidgets.QLabel("第1次"))
        interval_layout.addWidget(self.first_spin)
        interval_layout.addSpacing(8)
        interval_layout.addWidget(QtWidgets.QLabel("第2次"))
        interval_layout.addWidget(self.second_spin)
        interval_layout.addSpacing(8)
        interval_layout.addWidget(QtWidgets.QLabel("后续"))
        interval_layout.addWidget(self.subseq_spin)
        form.addRow("间隔配置", interval_widget)

        self.config_section = CollapsibleSection("📝 基础配置 (运行时自动折叠)", config_content)
        layout.addWidget(self.config_section)

        # 控制按钮
        btn_row = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("🚀 启动")
        self.stop_btn = QtWidgets.QPushButton("⏹ 停止")
        self.stop_btn.setEnabled(False)
        self.save_btn = QtWidgets.QPushButton("💾 保存配置")
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.save_btn)
        btn_widget = QtWidgets.QWidget()
        btn_widget.setLayout(btn_row)
        layout.addWidget(btn_widget)

        # 状态区域
        status_group = QtWidgets.QGroupBox("📊 状态")
        status_layout = QtWidgets.QGridLayout(status_group)
        self.status_label = QtWidgets.QLabel("待机中")
        self.next_label = QtWidgets.QLabel("--:--")
        self.elapsed_label = QtWidgets.QLabel("已用时：0:00 / 0:00")
        self.count_label = QtWidgets.QLabel("已提醒：0 次")
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)

        status_layout.addWidget(QtWidgets.QLabel("当前状态"), 0, 0)
        status_layout.addWidget(self.status_label, 0, 1, 1, 2)
        status_layout.addWidget(QtWidgets.QLabel("下次提醒"), 1, 0)
        status_layout.addWidget(self.next_label, 1, 1)
        status_layout.addWidget(self.count_label, 1, 2)
        status_layout.addWidget(QtWidgets.QLabel("时间"), 2, 0)
        status_layout.addWidget(self.elapsed_label, 2, 1, 1, 2)
        status_layout.addWidget(self.progress, 3, 0, 1, 3)
        layout.addWidget(status_group)

        # 音效
        sound_content = QtWidgets.QWidget()
        sound_layout = QtWidgets.QFormLayout(sound_content)
        self.sound_checkbox = QtWidgets.QCheckBox("启用音效")
        sound_layout.addRow(self.sound_checkbox)

        sound_row = QtWidgets.QHBoxLayout()
        self.sound_edit = QtWidgets.QLineEdit()
        sound_browse = QtWidgets.QPushButton("选择文件")
        sound_browse.clicked.connect(self._browse_sound)
        test_btn = QtWidgets.QPushButton("测试音效")
        test_btn.clicked.connect(self._test_sound)
        sound_row.addWidget(self.sound_edit)
        sound_row.addWidget(sound_browse)
        sound_row.addWidget(test_btn)
        sound_widget = QtWidgets.QWidget()
        sound_widget.setLayout(sound_row)
        sound_layout.addRow("自定义音效", sound_widget)
        self.sound_section = CollapsibleSection("🔊 音效设置", sound_content)
        layout.addWidget(self.sound_section)

        # 历史 + 热力
        history_group = QtWidgets.QGroupBox("📜 历史与习惯")
        h_layout = QtWidgets.QVBoxLayout(history_group)
        self.heatmap = HourlyHeatmap()
        h_layout.addWidget(QtWidgets.QLabel("今天 24 小时提醒热力：越深表示次数越多"))
        h_layout.addWidget(self.heatmap)

        table_row = QtWidgets.QHBoxLayout()
        clear_btn = QtWidgets.QPushButton("清空记录")
        clear_btn.clicked.connect(self._clear_history)
        table_row.addStretch()
        table_row.addWidget(clear_btn)
        h_layout.addLayout(table_row)

        self.table = QtWidgets.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["时间", "状态/链接"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        h_layout.addWidget(self.table)
        layout.addWidget(history_group, stretch=1)

        # 连接信号
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.save_btn.clicked.connect(self._save_settings)

    def _load_settings(self):
        c = self.config
        self.url_edit.setText(c.get("url", DEFAULTS["url"]))
        self.chrome_edit.setText(c.get("chrome_path", DEFAULTS["chrome_path"]))
        self.total_spin.setValue(int(c.get("total_min", DEFAULTS["total_min"])))
        self.first_spin.setValue(int(c.get("first_min", DEFAULTS["first_min"])))
        self.second_spin.setValue(int(c.get("second_min", DEFAULTS["second_min"])))
        self.subseq_spin.setValue(int(c.get("subseq_min", DEFAULTS["subseq_min"])))
        self.sound_checkbox.setChecked(bool(c.get("sound_enabled", DEFAULTS["sound_enabled"])))
        self.sound_edit.setText(c.get("sound_file", DEFAULTS["sound_file"]))

    def _browse_chrome(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择浏览器程序")
        if path:
            self.chrome_edit.setText(path)

    def _browse_sound(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择音效文件",
            "",
            "Audio Files (*.wav *.mp3 *.ogg *.m4a);;All Files (*)",
        )
        if path:
            self.sound_edit.setText(path)

    def _test_sound(self):
        if not self.sound_checkbox.isChecked():
            QtWidgets.QMessageBox.information(self, "提示", "请先启用音效开关")
            return
        self.sound_manager.play_notification(self.sound_edit.text().strip() or None)

    def _save_settings(self):
        try:
            cfg = {
                "url": self.url_edit.text().strip(),
                "chrome_path": self.chrome_edit.text().strip(),
                "total_min": int(self.total_spin.value()),
                "first_min": int(self.first_spin.value()),
                "second_min": int(self.second_spin.value()),
                "subseq_min": int(self.subseq_spin.value()),
                "sound_enabled": self.sound_checkbox.isChecked(),
                "sound_file": self.sound_edit.text().strip(),
            }
            self.config = cfg
            self.config_manager.save(cfg)
            QtWidgets.QMessageBox.information(self, "成功", "配置已保存")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "错误", f"保存配置失败：{e}")

    def _validate_inputs(self):
        url = self.url_edit.text().strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("URL 必须以 http:// 或 https:// 开头")
        total = int(self.total_spin.value()) * 60
        first = int(self.first_spin.value()) * 60
        second = int(self.second_spin.value()) * 60
        subseq = int(self.subseq_spin.value()) * 60
        if min(total, first, second, subseq) <= 0:
            raise ValueError("时间必须为正整数")
        return url, total, [first, second], subseq

    def start(self):
        if self.running:
            return
        try:
            self.url, self.total_sec, self.intervals, self.subseq_sec = self._validate_inputs()
            self.chrome_path = self.chrome_edit.text().strip()
            self.browser = None
            if self.chrome_path:
                try:
                    self.browser = webbrowser.get(self.chrome_path)
                except Exception:
                    self.browser = None
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "参数错误", str(e))
            return

        self.running = True
        self.elapsed = 0
        self.count = 0
        self.seconds_until_next = 0
        self.pending_wait = 0
        self.status_label.setText("运行中")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.config_section.set_collapsed(True)
        self.sound_section.set_collapsed(True)

        self._open_now()
        self._schedule_next()
        self.timer.start(1000)

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("已停止")
        self.progress.setValue(0)
        self.config_section.set_collapsed(False)
        self.sound_section.set_collapsed(False)

    def _open_now(self):
        self.count += 1
        self.count_label.setText(f"已提醒：{self.count} 次")
        success = True
        try:
            if self.browser:
                self.browser.open(self.url)
            else:
                webbrowser.open(self.url)
            if self.sound_checkbox.isChecked():
                sf = self.sound_edit.text().strip() or None
                threading.Thread(target=lambda: self.sound_manager.play_notification(sf), daemon=True).start()
            self.status_label.setText(f"第 {self.count} 次提醒已触发")
        except Exception as e:
            success = False
            self.status_label.setText(f"打开失败: {e}")
        finally:
            self._record_history(success)

    def _schedule_next(self):
        if self.count <= len(self.intervals):
            wait = self.intervals[self.count - 1]
        else:
            wait = self.subseq_sec

        if self.elapsed + wait >= self.total_sec:
            self.next_label.setText("完成")
            self.stop()
            QtWidgets.QMessageBox.information(self, "完成", "所有提醒已完成")
            return

        self.pending_wait = wait
        self.seconds_until_next = wait
        self._update_display()

    def _tick(self):
        if not self.running:
            return
        if self.seconds_until_next > 0:
            self.seconds_until_next -= 1
            self._update_display()
        else:
            self.elapsed += self.pending_wait
            self._open_now()
            self._schedule_next()

    def _update_display(self):
        mm, ss = divmod(self.seconds_until_next, 60)
        self.next_label.setText(f"{mm:02d}:{ss:02d}")
        if self.pending_wait > 0:
            progress = int((self.pending_wait - self.seconds_until_next) / self.pending_wait * 100)
            self.progress.setValue(progress)

        total_mm, total_ss = divmod(self.total_sec, 60)
        el_mm, el_ss = divmod(self.elapsed, 60)
        self.elapsed_label.setText(f"已用时：{el_mm}:{el_ss:02d} / {total_mm}:{total_ss:02d}")

    def _record_history(self, success=True):
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "count": self.count,
            "url": getattr(self, "url", ""),
            "status": "success" if success else "failed",
        }
        self.history_manager.add(entry)
        self._refresh_history_view()

    def _clear_history(self):
        if QtWidgets.QMessageBox.question(self, "确认", "确定清空所有记录？") != QtWidgets.QMessageBox.Yes:
            return
        self.history_manager.clear()
        self._refresh_history_view()

    def _refresh_history_view(self):
        records = self.history_manager.records[-20:]
        self.table.setRowCount(len(records))
        for row, rec in enumerate(reversed(records)):
            ts = self._format_timestamp(rec.get("timestamp"))
            status = rec.get("status", "success")
            prefix = "✅" if status == "success" else "⚠️"
            detail = rec.get("url") or "提醒已触发"
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(ts))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(f"{prefix} {detail}"))

        counts = defaultdict(int)
        today = datetime.now().date()
        for rec in self.history_manager.records:
            dt = self._parse_timestamp(rec.get("timestamp"))
            if not dt or dt.date() != today:
                continue
            counts[dt.hour] += 1
        self.heatmap.set_counts(counts)

    def _parse_timestamp(self, ts):
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return None

    def _format_timestamp(self, ts):
        dt = self._parse_timestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M") if dt else "--"


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = ReminderWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
