#!/bin/sh
# Startops 自重启脚本 (Linux/macOS)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 给当前实例留出返回 API 响应和退出的时间
sleep 1

cd "$PROJECT_DIR" || exit 1
nohup python3 main.py "$@" >/dev/null 2>&1 &

exit 0
