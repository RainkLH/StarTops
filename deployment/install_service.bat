@echo off
REM Startops Windows 系统服务安装脚本
REM 用于注册 Startops 为 Windows 服务
REM 
REM 用法:
REM   install_service.bat install      - 安装服务
REM   install_service.bat uninstall    - 卸载服务
REM   install_service.bat start        - 启动服务
REM   install_service.bat stop         - 停止服务
REM   install_service.bat status       - 查看服务状态

setlocal enabledelayedexpansion

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] 此脚本必须以管理员身份运行
    echo 请右键选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR:~0,-11%
set SERVICE_NAME=Startops
set DISPLAY_NAME=Startops 2.0 - Lightweight Ops Console
set PYTHON_PATH=%SystemRoot%\python.exe

REM 检查 Python 是否已安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo.
    pause
    exit /b 1
)

REM 获取 Python 路径
for /f "delims=" %%I in ('python -c "import sys; print(sys.executable)"') do set PYTHON_PATH=%%I

REM 检查参数
if "%1"=="" (
    call :show_help
    exit /b 0
)

if /i "%1"=="install" (
    call :install_service
) else if /i "%1"=="uninstall" (
    call :uninstall_service
) else if /i "%1"=="start" (
    call :start_service
) else if /i "%1"=="stop" (
    call :stop_service
) else if /i "%1"=="status" (
    call :show_status
) else (
    call :show_help
    exit /b 1
)

exit /b %errorlevel%

REM ================== 函数定义 ==================

:show_help
echo.
echo Startops Windows 系统服务管理脚本
echo.
echo 用法: %0 ^<命令^>
echo.
echo 可用命令:
echo   install     - 安装 Startops 系统服务
echo   uninstall   - 卸载 Startops 系统服务
echo   start       - 启动服务
echo   stop        - 停止服务
echo   status      - 显示服务状态
echo.
echo 示例:
echo   %0 install
echo   %0 status
echo   %0 uninstall
echo.
exit /b 0

:install_service
echo.
echo ========================================
echo 正在安装 Startops 系统服务...
echo ========================================
echo.

REM 检查依赖
echo [1/4] 检查 Python 依赖...
if exist "%PROJECT_DIR%requirements.txt" (
    python -m pip install -r "%PROJECT_DIR%requirements.txt" -q
    if %errorlevel% equ 0 (
        echo [✓] Python 依赖已安装
    ) else (
        echo [✗] Python 依赖安装失败
        exit /b 1
    )
) else (
    echo [!] 未找到 requirements.txt，跳过依赖安装
)

echo.
echo [2/4] 检查服务是否已存在...
sc query %SERVICE_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo [!] 服务已存在，将先卸载旧服务...
    sc stop %SERVICE_NAME% >nul 2>&1
    timeout /t 2 /nobreak >nul 2>&1
    sc delete %SERVICE_NAME% >nul 2>&1
)

echo.
echo [3/4] 注册新服务...
REM 使用 nssm (Non-Sucking Service Manager) 如果安装了
if exist "%PROGRAMFILES%\nssm\nssm.exe" (
    "%PROGRAMFILES%\nssm\nssm.exe" install %SERVICE_NAME% "%PYTHON_PATH%" "%PROJECT_DIR%main.py"
    "%PROGRAMFILES%\nssm\nssm.exe" set %SERVICE_NAME% AppDirectory "%PROJECT_DIR%"
    "%PROGRAMFILES%\nssm\nssm.exe" set %SERVICE_NAME% AppRestartDelay 5000
    echo [✓] 服务已通过 NSSM 注册
) else (
    REM 使用 Python 脚本创建服务包装
    echo 创建服务包装脚本...
    call :create_service_wrapper
    sc create %SERVICE_NAME% binPath= "%SCRIPT_DIR%Startops_service_wrapper.exe" displayname= "%DISPLAY_NAME%" start= auto
    if %errorlevel% equ 0 (
        echo [✓] 服务已注册
    ) else (
        echo [✗] 服务注册失败
        exit /b 1
    )
)

echo.
echo [4/4] 启动服务...
net start %SERVICE_NAME%
if %errorlevel% equ 0 (
    echo [✓] 服务已启动
) else (
    echo [!] 服务启动失败（可能需要稍后手动启动）
)

echo.
echo ========================================
echo Startops 系统服务安装完成！
echo ========================================
echo.
echo 后续命令:
echo   启动服务: net start %SERVICE_NAME%
echo   停止服务: net stop %SERVICE_NAME%
echo   卸载服务: %0 uninstall
echo.
exit /b 0

:uninstall_service
echo.
echo ========================================
echo 正在卸载 Startops 系统服务...
echo ========================================
echo.

echo [1/3] 检查服务...
sc query %SERVICE_NAME% >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 服务未安装
    exit /b 0
)

echo [2/3] 停止服务...
net stop %SERVICE_NAME% >nul 2>&1

echo [3/3] 删除服务...
sc delete %SERVICE_NAME%
if %errorlevel% equ 0 (
    echo [✓] 服务已删除
) else (
    echo [✗] 服务删除失败
    exit /b 1
)

echo.
echo ========================================
echo Startops 系统服务卸载完成！
echo ========================================
echo.
exit /b 0

:start_service
echo.
echo 启动服务: %SERVICE_NAME%...
net start %SERVICE_NAME%
if %errorlevel% equ 0 (
    echo [✓] 服务已启动
) else (
    echo [✗] 启动失败
    exit /b 1
)
exit /b 0

:stop_service
echo.
echo 停止服务: %SERVICE_NAME%...
net stop %SERVICE_NAME%
if %errorlevel% equ 0 (
    echo [✓] 服务已停止
) else (
    echo [✗] 停止失败
    exit /b 1
)
exit /b 0

:show_status
echo.
echo Startops 服务状态:
echo.
sc query %SERVICE_NAME%
exit /b 0

:create_service_wrapper
REM 此函数创建一个服务包装脚本
REM 在实际应用中，建议使用 NSSM 或 pywin32 来创建更完善的 Windows 服务
echo [!] 注意: 此方法仅为基础实现
echo     建议安装 NSSM (Non-Sucking Service Manager) 获得更好的服务管理
echo     下载地址: https://nssm.cc/download
exit /b 0
