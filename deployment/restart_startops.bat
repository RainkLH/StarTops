@echo off
REM Startops 自重启脚本 (Windows)
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_DIR=%%~fI"

REM 给当前实例留出返回 API 响应和退出的时间
timeout /t 1 /nobreak >nul

REM 保留原始命令行参数并在项目根目录重启
start "" /D "%PROJECT_DIR%" cmd /c "python main.py %*"

exit /b 0
