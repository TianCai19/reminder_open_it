# reminder_open_it (PyQt 版本)

PyQt 重构版的智能提醒助手，提供渐进间隔提醒、音效提示、历史持久化与今日 24 小时热力方块展示，并将配置/音效面板折叠以保持界面简洁。本分支保留核心功能但 UI 架构改为 PyQt。

## 核心功能
- 渐进间隔提醒：第 1/2 次自定义，后续固定间隔，达总时长自动停止。
- 立即打开目标 URL，可指定浏览器路径。
- 音效提醒（pygame），可自定义音效文件并测试。
- history.json 持久化；历史表格 + 今日 24 小时热力方块。
- 折叠面板：运行时自动折叠配置/音效面板，停止后展开。

## 技术架构
- UI：PyQt5（`QMainWindow` + `QTimer` + 自绘控件），折叠面板用 `QToolButton` 控制内容显隐，自绘热力方块基于 `QPainter`。
- 计时与状态：`QTimer` 1s 心跳管理倒计时、累积时长与提醒次数。
- 浏览与音效：`webbrowser` 打开 URL；`pygame.mixer` 播放自定义或默认音效，独立线程触发播放避免阻塞。
- 持久化：`config.json` 保存配置；`history.json` 记录时间戳/计数/状态/URL，用于表格与热力图。
- 代码位置：主要逻辑集中在 `notion_reminder_pyqt.py`，保持单文件便于理解和打包。
- 分支隔离：`pyqt-rewrite` 分支使用 PyQt；`main` 分支保留 Tk/ttk 版本。

## 快速开始
```bash
pip install -r requirements.txt   # 如镜像缺包可改用 -i https://pypi.org/simple
python notion_reminder_pyqt.py    # 在有桌面环境的终端前台运行
```

## 主要文件
- `notion_reminder_pyqt.py`：PyQt 版主程序、UI 与业务逻辑。
- `requirements.txt`：包含 PyQt5、pygame 等依赖。
- `config.json` / `history.json`：运行时生成的配置与历史数据。

## 许可
MIT License
