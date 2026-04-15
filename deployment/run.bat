@echo off
REM Startops 一键启动脚本 (Windows)

chcp 65001 > nul

echo.
echo ============================================================
echo Startops 2.0 - 轻量级业务运维集成控制台
echo ============================================================
echo.

REM 检查Python是否安装
python --version > nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo 正在启动Startops...
echo.

REM 安装依赖
echo 检查依赖...
pip list | findstr "fastapi" > nul
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo ============================================================
echo Startops 已启动
echo ============================================================
echo.
echo 访问地址: http://127.0.0.1:8000
echo 按 Ctrl+C 停止服务
echo.

REM 启动应用
python main.py

echo.
echo ============================================================
echo Startops 已停止
echo ============================================================
echo.

pause
