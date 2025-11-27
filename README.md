# reminder_open_it （Web 版）

Web 重构版：后端 FastAPI 负责计时与触发提醒，前端纯 HTML/JS 提供现代化 UI。功能保持一致：渐进间隔提醒、音效提示、history.json 持久化、今日 24 小时热力方块、历史表格、配置管理。

## 核心功能
- 渐进间隔提醒：第 1/2 次自定义，后续固定间隔，到达总时长停止。
- 后端触发：在本机用 `webbrowser` 打开目标 URL，可选自定义浏览器路径。
- 音效提示：pygame 播放默认或自定义音效（需本机声音权限）。
- history.json 持久化：历史表格 + 今日 24 小时热力图（前端绘制）。
- 前后端分离：API 控制启动/停止/配置/历史，前端每秒轮询状态，8 秒刷新历史。

## 技术架构
- 后端：FastAPI + uvicorn，REST API（/api/config, /api/start, /api/stop, /api/status, /api/history, /api/history/clear），线程驱动计时与提醒。
- 计时逻辑：后台线程维护倒计时、累计时长、提醒次数与进度；立即触发首个提醒。
- 音效/浏览：`webbrowser` 打开 URL；`pygame.mixer` 播放音效（后台线程避免阻塞）。
- 持久化：`config.json` 与 `history.json` 读写，最大 500 条历史保留。
- 前端：`web/index.html`，纯原生 HTML/CSS/JS，深色渐变 UI，启动/停止、配置、状态、今日 24h 热力格子、历史表格、清空/刷新操作。
- AI 鼓励（可选）：集成 OpenRouter（GPT-5 Mini 等），基于最近记录生成一句鼓励。需要本地配置 API Key。

## 快速开始
```bash
pip install -r requirements.txt                # 安装依赖（FastAPI + uvicorn + pygame 等）
APP_PORT=8765 python web_reminder.py           # 启动本地服务，默认 http://localhost:8765
# 浏览器打开 http://localhost:8765 即可操作
```

## 文件结构
- `web_reminder.py`：FastAPI 服务与计时引擎。
- `web/index.html`：前端页面与交互逻辑。
- `config.json` / `history.json`：运行时生成/更新的配置与历史（已列入 .gitignore）。
- 其他分支：`main`（Tk/ttk 版），`pyqt-rewrite`（PyQt 版）。
- `openrouter.key.example`：OpenRouter Key 示例；实际 Key 放 `openrouter.key`（已忽略）或环境变量。
- `start_app.py`：本地一键启动（含自动打开浏览器），用于打包为 macOS .app 的入口。

## 可选：启用 OpenRouter AI 鼓励
- 安装依赖已包含 `openai`。
- 将 API Key 写入同级的 `openrouter.key`（文件已被忽略），或导出 `OPENROUTER_API_KEY` 环境变量。
- 默认模型 `openai/gpt-5-mini`，可在后端调整；前端有“AI 鼓励”按钮调用 `/api/llm/encourage`。
- 专属聊天助手：访问 `/chat.html`，可选择模型、时间范围（日/周/月上下文）、提示模板（总结/反思/建议）、查看完整上下文 prompt 与 token usage。

## 架构权衡
- Web 版：UI 自由度高、易扩展为多端访问；需本地服务常驻，浏览器自动开新页可能受弹窗策略限制。
- Tk/ttk：轻量、零外部依赖，原生外观朴素；复杂动画/布局受限。
- PyQt：外观现代、控件丰富、可自绘；依赖体积较大、学习/打包成本略高。

## 打包为 macOS 应用（示例）
- 入口：`start_app.py`（内部启动 uvicorn 绑定 127.0.0.1:8765 并自动打开浏览器）。
- 推荐 PyInstaller 命令：
  ```
  pyinstaller --noconfirm --windowed --name ReminderWeb \\
    --add-data \"web/*:web\" start_app.py
  ```
  打包后 `dist/ReminderWeb.app` 可直接使用。实际 key 放 `openrouter.key` 或环境变量，不要打进 .app。

## 部署与纯前端的区别
- 本方案的“后端”是本机常驻的 FastAPI 进程，负责计时/打开浏览器/播放音效/读写历史；前端只是调用这些 API。没有这个后端，浏览器无法在你的电脑上打开应用或播放本地音效。
- 纯前端（如把 `web/` 静态页部署到 Vercel）无法提供持久计时与本地打开/声音；只能当作展示界面，或改写为浏览器内的计时提醒（Web Notifications/Service Worker），放弃服务器侧动作。
- 如果需要远程访问：前端可以部署到 Vercel 等静态托管，但后端必须自托管在一台长期运行的主机上，前端通过公网访问该后端。

## 注意
- 需在有桌面/默认浏览器的环境运行，浏览器可能阻止频繁弹窗，可根据浏览器策略调整或改用通知方案。
- 音效播放依赖 pygame，如不可用会自动降级为静默。

## 许可证
MIT License
