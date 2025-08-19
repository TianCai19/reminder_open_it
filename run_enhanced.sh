#!/bin/bash

# 智能提醒助手 - Enhanced 版本启动脚本

echo "🔔 智能提醒助手 - Enhanced 版本"
echo "=================================="
echo

# 获取脚本所在目录
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# 检查Python是否可用
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 python3 命令"
    echo "请先安装 Python 3"
    exit 1
fi

echo "✅ Python 3 已找到"

# 检查依赖
echo "🔍 检查依赖..."

# 检查核心依赖
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 错误：tkinter 不可用"
    echo "请安装 tkinter 支持"
    exit 1
fi

# 检查可选依赖
echo "📦 检查可选依赖..."

python3 -c "import pygame" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✅ pygame - 音效功能可用"
else
    echo "  ⚠️  pygame - 音效功能将被禁用"
fi

python3 -c "import ttkthemes" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✅ ttkthemes - 主题功能可用"
else
    echo "  ⚠️  ttkthemes - 将使用默认主题"
fi

echo

# 检查是否存在增强版文件
if [ ! -f "notion_reminder_enhanced.py" ]; then
    echo "❌ 错误：未找到 notion_reminder_enhanced.py 文件"
    exit 1
fi

echo "🚀 启动应用..."
python3 notion_reminder_enhanced.py

echo
echo "👋 应用已退出"
