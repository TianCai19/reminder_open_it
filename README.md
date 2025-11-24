# reminder_open_it

智能提醒助手，支持渐进式间隔提醒、音效提示、历史持久化与当天 24 小时热力方块展示。`main` 分支采用 Tk/ttk；`pyqt-rewrite` 分支提供 PyQt 重构版，两套方案互不影响。

## 核心功能（本分支：Tk/ttk）
- 渐进间隔提醒：第 1/2 次自定义，后续固定间隔，累计到总时长自动停止。
- 立即打开目标 URL，可指定浏览器路径。
- 音效提醒（pygame），支持自定义音效文件与测试。
- history.json 持久化；历史表格 + 今日 24 小时热力方块（Canvas 自绘）。
- 折叠式体验：运行时自动折叠配置/音效面板，停止后展开。

## 技术架构
- UI：Tkinter + ttk，自定义样式；热力方块使用 `Canvas` 绘制。
- 计时：`root.after` 每秒心跳；管理倒计时、累计时长与提醒次数。
- 浏览与音效：`webbrowser` 打开 URL；`pygame.mixer` 播放自定义或默认音效，线程触发避免阻塞。
- 持久化：`config.json` 保存配置；`history.json` 保存时间戳/计数/状态/URL，驱动历史表格与热力图。
- 文件：`notion_reminder_gui.py`（Tk 主程序）、`history.json`/`config.json`（运行时生成）、`assets/`（资源）。

## 分支与架构权衡
- Tk/ttk（当前）：轻量、零外部依赖（除了 pygame）；易打包；原生控件外观普通，复杂 UI/动画受限。
- PyQt（`pyqt-rewrite`）：控件丰富、绘制能力强、外观更现代；依赖体积大；学习/打包成本略高。
- Web 壳（可选未来方向，如 Tauri/Electron + 本地服务）：UI 自由度最高，前端生态丰富；需要前后端协作与更大运行体积。

## 快速开始
```bash
pip install -r requirements.txt          # 安装依赖
python notion_reminder_gui.py            # 前台运行 Tk 版

# 使用 PyQt 版（在 pyqt-rewrite 分支）
git checkout pyqt-rewrite
python notion_reminder_pyqt.py
```

## 贡献
欢迎提交 Issue / PR，或基于不同架构提出改进方案。

## 许可证
MIT License
