#!/bin/bash
# Startops 一键启动脚本 (Linux/Mac)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "============================================================"
echo "Startops 2.0 - 轻量级业务运维集成控制台"
echo "============================================================"
echo ""

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python版本: $PYTHON_VERSION"
echo "✓ 项目路径: $SCRIPT_DIR"
echo ""

# 检查依赖
echo "检查依赖..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "正在安装依赖..."
    python3 -m pip install -r "$SCRIPT_DIR/requirements.txt"
    echo "✓ 依赖安装完成"
else
    echo "✓ 所有依赖已安装"
fi

echo ""
echo "============================================================"
echo "启动Startops服务..."
echo "============================================================"
echo ""
echo "访问地址: http://127.0.0.1:8000"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动应用
cd "$SCRIPT_DIR"
python3 main.py

echo ""
echo "============================================================"
echo "Startops已停止"
echo "============================================================"
echo ""
