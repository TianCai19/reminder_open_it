#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动本地服务并打开浏览器。
- 使用 APP_PORT 环境变量可调整端口，默认 8765。
- 读取 openrouter.key / 环境变量，以支持 LLM 功能。
"""
import threading
import time
import webbrowser
import os
from pathlib import Path
import uvicorn

DEFAULT_PORT = int(os.getenv("APP_PORT", "8765"))
BASE_DIR = Path(__file__).parent


def run_server():
    uvicorn.run(
        "web_reminder:app",
        host="127.0.0.1",
        port=DEFAULT_PORT,
        reload=False,
    )


def main():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(1.5)
    webbrowser.open(f"http://127.0.0.1:{DEFAULT_PORT}")
    # 保持主线程存活
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
