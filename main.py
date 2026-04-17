"""
Startops 2.0 - 轻量级业务运维集成控制台
主程序入口，FastAPI 应用启动和路由定义

运行方式:
    python main.py
    python main.py -l 0.0.0.0 -p 8080
    python main.py --listen 192.168.1.100 --port 9000
    
按 Ctrl+C 退出程序
"""

import asyncio
import sys
import os
import argparse
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.startops_main import get_startops
from src.utils.logger import initialize_logger, get_logger, close_logger
from src.config_loader import ConfigLoader
from src.node_provider import get_nodes, create_default_nodes_config
from src.web_terminal import create_terminal, close_terminal
from src.system_restart import launch_restart_script, save_last_start_args, load_last_start_args

# 注意：日志将在 main() 函数中根据配置初始化
logger = None  # 占位，在 main() 中初始化

# 全局配置对象
config = None
restart_by_self = False
uvicorn_server = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    if logger is not None:
        logger.info("=" * 60)
        logger.info("Startops 2.0 启动中...")
        logger.info("=" * 60)

    # 启动监控任务
    await startops.start_monitoring()
    if logger is not None:
        logger.info("服务监控已启动")

    try:
        yield
    finally:
        if logger is not None:
            logger.info("=" * 60)
            logger.info("Startops 2.0 关闭中...")
            logger.info("=" * 60)

        # 停止监控任务
        await startops.stop_monitoring()
        if logger is not None:
            logger.info("服务监控已停止")

        # 关闭日志
        close_logger()

# 创建 FastAPI 应用
app = FastAPI(
    title="Startops 2.0",
    description="轻量级业务运维集成控制台",
    version="2.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取 Startops 实例
startops = get_startops()

# 挂载静态文件
static_path = Path(__file__).parent / "src" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# ===== 静态页面路由 =====

@app.get("/", response_class=HTMLResponse)
async def index():
    """主页面 - 多节点监控"""
    try:
        with open(Path(__file__).parent / "src" / "templates" / "index.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load index page: {str(e)}")
        return f"<h1>错误：{str(e)}</h1>"


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """仪表盘页面"""
    try:
        with open(Path(__file__).parent / "src" / "templates" / "dashboard.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load dashboard: {str(e)}")
        return f"<h1>错误：{str(e)}</h1>"


@app.get("/config/{config_id}", response_class=HTMLResponse)
async def config_edit_page(config_id: str):
    """配置编辑页面"""
    try:
        with open(Path(__file__).parent / "src" / "templates" / "edit_config.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load config page: {str(e)}")
        return f"<h1>错误：{str(e)}</h1>"


@app.get("/terminal", response_class=HTMLResponse)
async def terminal_page():
    """网页终端页面"""
    try:
        with open(Path(__file__).parent / "src" / "templates" / "terminal.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load terminal page: {str(e)}")
        return f"<h1>错误：{str(e)}</h1>"


# ===== API 路由 =====

# ===== 仪表盘 API =====

@app.get("/api/dashboard")
async def api_dashboard() -> Dict[str, Any]:
    """获取仪表盘数据"""
    try:
        data = startops.get_dashboard_data()
        return data
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/nodes")
async def api_get_nodes() -> Dict[str, Any]:
    """获取集群节点列表"""
    try:
        # 从配置获取节点提供者类型
        nodes_config = config.nodes
        provider_type = nodes_config.provider
        
        # 如果配置文件不存在，创建默认配置
        nodes_config_file = Path(__file__).parent / "configs" / "nodes.json"
        if not nodes_config_file.exists() and provider_type == "ConfigFile":
            logger.info(f"节点配置文件不存在，创建默认配置：{nodes_config_file}")
            create_default_nodes_config()
        
        # 获取节点列表
        nodes = await get_nodes(
            provider_type=provider_type,
            config_dir=str(Path(__file__).parent / "configs"),
            consul_config={
                "host": nodes_config.consul.host,
                "port": nodes_config.consul.port,
                "service_name": nodes_config.consul.service_name
            } if provider_type == "Consul" else None
        )
        
        return {
            "success": True,
            "total_nodes": len(nodes),
            "nodes": [node.to_dict() for node in nodes],
            "provider": provider_type
        }
    except Exception as e:
        logger.error(f"Error getting nodes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== 服务管理 API =====

@app.get("/api/services")
async def api_get_services() -> Dict[str, Any]:
    """获取所有服务"""
    try:
        services = startops.get_all_services()
        return {
            "success": True,
            "services": {sid: svc.to_dict() for sid, svc in services.items()}
        }
    except Exception as e:
        logger.error(f"Error getting services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/service/{service_name}")
async def api_get_service(service_name: str) -> Dict[str, Any]:
    """获取指定服务信息"""
    service = startops.get_service(service_name)
    if not service:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    return {
        "success": True,
        "service": service.to_dict()
    }


@app.post("/api/service/{service_name}/start")
async def api_start_service(service_name: str) -> Dict[str, Any]:
    """启动服务"""
    try:
        result = startops.start_service(service_name)
        if result:
            return {"success": True, "message": f"Service {service_name} started successfully"}
        else:
            return {"success": False, "message": f"Failed to start service {service_name}"}
    except Exception as e:
        logger.error(f"Error starting service {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/service/{service_name}/stop")
async def api_stop_service(service_name: str) -> Dict[str, Any]:
    """停止服务"""
    try:
        result = startops.stop_service(service_name)
        if result:
            return {"success": True, "message": f"Service {service_name} stopped successfully"}
        else:
            return {"success": False, "message": f"Failed to stop service {service_name}"}
    except Exception as e:
        logger.error(f"Error stopping service {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/service/{service_name}/restart")
async def api_restart_service(service_name: str) -> Dict[str, Any]:
    """重启服务"""
    try:
        result = startops.restart_service(service_name)
        if result:
            return {"success": True, "message": f"Service {service_name} restarted successfully"}
        else:
            return {"success": False, "message": f"Failed to restart service {service_name}"}
    except Exception as e:
        logger.error(f"Error restarting service {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/service/{service_name}/guard")
async def api_set_service_guard(service_name: str, request: Request) -> Dict[str, Any]:
    """设置服务守护开关"""
    try:
        data = await request.json()
        enabled = data.get("enabled")
        if enabled is None:
            raise HTTPException(status_code=400, detail="Missing 'enabled' field")

        result = startops.set_service_guard(service_name, bool(enabled))
        if result:
            return {"success": True, "message": "Guard updated"}
        return {"success": False, "message": "Failed to update guard"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting guard for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/service/register")
async def api_register_service(request: Request) -> Dict[str, Any]:
    """注册服务"""
    try:
        data = await request.json()
        # 必需字段检查
        required_fields = ["name", "url", "health_check_url"]
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            raise HTTPException(status_code=400, detail=f"缺少必需字段：{', '.join(missing)}")

        service = startops.register_service(
            name=data["name"],
            url=data["url"],
            health_check_url=data["health_check_url"],
            executor=data.get("executor", "python3"),
            app_dir=data.get("app_dir", ""),
            app_file_name=data.get("app_file_name", ""),
            app_args=data.get("app_args", ""),
            start_cmd=data.get("start_cmd", ""),
            stop_cmd=data.get("stop_cmd", ""),
            health_check_interval=data.get("health_check_interval", 30),
            description=data.get("description", ""),
            keep_alive=data.get("keep_alive", True),
            start_timeout=data.get("start_timeout", 45),
            stop_timeout=data.get("stop_timeout", 45)
        )

        return {"success": True, "service": service.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering service: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/service/unregister")
async def api_unregister_service(request: Request) -> Dict[str, Any]:
    """注销服务"""
    try:
        data = await request.json()
        service_name = data.get("service_name")
        if not service_name:
            raise HTTPException(status_code=400, detail="缺少必需字段：service_name")

        result = startops.unregister_service(service_name)
        if not result:
            raise HTTPException(status_code=404, detail="服务不存在或注销失败")

        return {
            "success": True,
            "message": "服务注销成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering service: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/service/{service_name}/health-check")
async def api_health_check(service_name: str) -> Dict[str, Any]:
    """检查服务健康状态"""
    try:
        result = await startops.check_service_health(service_name)
        service = startops.get_service(service_name)
        return {
            "success": True,
            "healthy": result,
            "service": service.to_dict() if service else None
        }
    except Exception as e:
        logger.error(f"Error checking health for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== 配置管理 API =====

@app.get("/api/config/{config_id}/form")
async def api_get_config_form(config_id: str) -> Dict[str, Any]:
    """获取配置编辑表单"""
    try:
        form_html = startops.render_config_form(
            config_id,
            form_action=f"/api/config/{config_id}/save",
            form_id=f"config-form-{config_id}"
        )
        
        if form_html is None:
            return {
                "success": False,
                "message": f"Config {config_id} not found"
            }
        
        config = startops.get_config(config_id)
        return {
            "success": True,
            "form_html": form_html,
            "description": config.description if config else ""
        }
    except Exception as e:
        logger.error(f"Error getting config form {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/{config_id}/data")
async def api_get_config_data(config_id: str) -> Dict[str, Any]:
    """获取配置数据"""
    try:
        data = startops.read_config_data(config_id)
        if data is None:
            raise HTTPException(status_code=404, detail=f"Config {config_id} not found")
        
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        logger.error(f"Error reading config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/configs")
async def api_get_configs() -> Dict[str, Any]:
    """获取所有配置"""
    try:
        configs = startops.get_all_configs()
        return {
            "success": True,
            "configs": [cfg.to_dict() for cfg in configs.values()]
        }
    except Exception as e:
        logger.error(f"Error getting configs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/{config_id}/save")
async def api_save_config(config_id: str, request: Request) -> Dict[str, Any]:
    """保存配置"""
    try:
        data = await request.json()
        
        # 验证配置
        is_valid, error_msg = startops.validate_config_data(config_id, data)
        if not is_valid:
            return {
                "success": False,
                "message": f"Validation error: {error_msg}"
            }
        
        # 保存配置
        result = startops.write_config_data(config_id, data)
        if result:
            return {
                "success": True,
                "message": f"Config {config_id} saved successfully"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to save config {config_id}"
            }
    except Exception as e:
        logger.error(f"Error saving config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/register")
async def api_register_config(request: Request) -> Dict[str, Any]:
    """注册配置文件"""
    try:
        data = await request.json()
        # 必需字段检查
        required_fields = ["config_id", "service_name", "config_name", "config_file_path"]
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            raise HTTPException(status_code=400, detail=f"缺少必需字段：{', '.join(missing)}")

        config = startops.register_config(
            config_id=data["config_id"],
            service_name=data["service_name"],
            config_name=data["config_name"],
            config_file_path=data["config_file_path"],
            meta_file_path=data.get("meta_file_path"),
            description=data.get("description", "")
        )

        return {"success": True, "config": config.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



# ===== 健康检查 API =====

@app.get("/api/health")
async def api_health() -> Dict[str, Any]:
    """健康检查端点"""
    return {
        "status": "healthy",
        "message": "Startops is running"
    }


# ===== 系统信息 API =====

@app.get("/api/system-info")
async def api_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    try:
        info = startops.get_system_info()
        return {
            "success": True,
            "info": info
        }
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _restart_startops_background(cli_args: list[str]):
    """后台触发重启脚本，随后退出当前进程。"""
    await asyncio.sleep(0.2)
    launched = launch_restart_script(cli_args)
    if not launched:
        logger.error("Failed to launch restart script, keep current process running")
        return

    await asyncio.sleep(0.6)
    os._exit(0)


async def _exit_current_process_background():
    """后台触发 Uvicorn 优雅退出，让 lifespan finally 正常执行。"""
    await asyncio.sleep(0.3)
    global uvicorn_server
    if uvicorn_server is None:
        logger.error("Uvicorn server instance not ready, cannot do graceful shutdown")
        return

    uvicorn_server.should_exit = True


@app.post("/api/system/restart")
async def api_restart_startops(request: Request) -> Dict[str, Any]:
    """重启当前节点上的 Startops 服务。"""
    try:
        data = await request.json()
        if data.get("confirmation_text") != "确认":
            raise HTTPException(status_code=400, detail="请手动输入“确认”后再执行重启")

        if restart_by_self:
            cli_args = load_last_start_args()
            if not cli_args:
                cli_args = list(sys.argv[1:])
            asyncio.create_task(_restart_startops_background(cli_args))
        else:
            logger.info("restart_by_self is disabled, exiting current process for external supervisor restart")
            asyncio.create_task(_exit_current_process_background())

        return {
            "success": True,
            "message": "Startops 重启流程已触发"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting startops: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pages")
async def api_get_pages() -> Dict[str, Any]:
    """获取所有服务页面"""
    try:
        pages = startops.get_all_pages()
        return {
            "success": True,
            "pages": [page.to_dict() for page in pages.values()]
        }
    except Exception as e:
        logger.error(f"Error getting pages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/page/register")
async def api_register_page(request: Request) -> Dict[str, Any]:
    """注册工具页面"""
    try:
        data = await request.json()
        # 必需字段检查
        required_fields = ["service_name", "page_name", "page_url"]
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            raise HTTPException(status_code=400, detail=f"缺少必需字段：{', '.join(missing)}")

        page = startops.register_page(
            service_name=data["service_name"],
            page_name=data["page_name"],
            page_url=data["page_url"],
            icon=data.get("icon", "🔧"),
            description=data.get("description", "")
        )

        return {"success": True, "page": page.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering page: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/page/unregister")
async def api_unregister_page(request: Request) -> Dict[str, Any]:
    """注销工具页面"""
    try:
        data = await request.json()
        required_fields = ["service_name", "page_name"]
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            raise HTTPException(status_code=400, detail=f"缺少必需字段：{', '.join(missing)}")

        result = startops.unregister_page(
            service_name=data["service_name"],
            page_name=data["page_name"]
        )

        if not result:
            raise HTTPException(status_code=404, detail="页面不存在或注销失败")

        return {
            "success": True,
            "message": "页面注销成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering page: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket):
    """网页终端 WebSocket"""
    # 检查终端是否启用
    if not config.terminal.enabled:
        await websocket.close(code=1003, reason="Terminal disabled")
        return
    
    # 创建终端
    terminal = create_terminal(
        shell=config.terminal.shell,
        timeout=config.terminal.timeout,
        max_lines=100
    )
    
    if not terminal:
        await websocket.close(code=1011, reason="Failed to create terminal")
        return
    
    await websocket.accept()
    logger.info("Terminal WebSocket connected")
    
    try:
        while terminal.running:
            # 读取终端输出
            output = terminal.read()
            if output:
                try:
                    await websocket.send_text(output)
                except:
                    break
            
            # 接收用户输入
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                if data:
                    terminal.write(data)
            except asyncio.TimeoutError:
                pass
            
            # 检查超时
            if terminal.check_timeout():
                await websocket.send_text("\n\n[Session timed out]")
                break
            
            await asyncio.sleep(0.01)
    
    except WebSocketDisconnect:
        logger.info("Terminal WebSocket disconnected")
    except Exception as e:
        logger.error(f"Terminal WebSocket error: {e}")
    finally:
        close_terminal()


# ===== 异常处理 =====

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error"
        }
    )


# ===== 主程序入口 =====

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Startops 2.0 - 轻量级业务运维集成控制台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                              # 使用配置文件启动
  python main.py -l 0.0.0.0                   # 命令行参数覆盖配置
  python main.py -p 9000                      # 使用端口 9000
  python main.py -l 0.0.0.0 -p 8080           # 监听所有网卡，端口 8080
  python main.py --listen 192.168.1.100 --port 9000  # 指定 IP 和端口
        """
    )
    
    parser.add_argument(
        '-l', '--listen',
        type=str,
        default=None,
        help='监听地址 (默认：从配置文件读取，无配置时为 127.0.0.1)'
    )
    
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=None,
        help='监听端口 (默认：从配置文件读取，无配置时为 8300)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        default=None,
        help='启用调试模式'
    )
    
    return parser.parse_args()

def main():
    """主函数"""
    global config, logger, restart_by_self, uvicorn_server
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 加载配置文件
    config_loader = ConfigLoader()
    config = config_loader.load_config()
    
    # 应用命令行参数覆盖
    command_line_args = {}
    startup_args = []
    if args.listen:
        command_line_args["host"] = args.listen
        startup_args.extend(["--listen", args.listen])
    if args.port:
        command_line_args["port"] = args.port
        startup_args.extend(["--port", str(args.port)])
    if args.debug:
        command_line_args["debug"] = args.debug
        startup_args.append("--debug")
    
    if command_line_args:
        config = config_loader.apply_command_line_args(command_line_args)

    restart_by_self = bool(config.server.restart_by_self)

    # 记录本次有效启动参数，供重启流程复用
    save_last_start_args(startup_args)
    
    # 创建配置和日志目录
    config_dir = Path(__file__).parent / "configs"
    config_dir.mkdir(exist_ok=True)
    
    logs_dir = Path(__file__).parent / "logs"
    if config.logs.enabled:
        logs_dir.mkdir(exist_ok=True)
    
    # 初始化日志系统（根据配置）
    initialize_logger(
        logs_dir=str(logs_dir) if config.logs.enabled else None,
        log_level=config.logs.level,
        log_format=config.logs.format,
        log_enabled=config.logs.enabled
    )
    logger = get_logger('main')
    
    logger.info("=" * 60)
    logger.info("Starting Startops 2.0...")
    logger.info(f"Listen address: {config.server.host}")
    logger.info(f"Listen port: {config.server.port}")
    logger.info(f"Debug mode: {config.server.debug}")
    logger.info(f"Logs enabled: {config.logs.enabled}")
    logger.info(f"Logs level: {config.logs.level}")
    logger.info(f"Config directory: {config_dir}")
    logger.info(f"Config file: {config_loader.config_file}")
    
    # 启动服务器
    logger.info(f"Starting FastAPI server on http://{config.server.host}:{config.server.port}")
    logger.info("Press Ctrl+C to shutdown")

    uvicorn_config = uvicorn.Config(
        app,
        host=config.server.host,
        port=config.server.port,
        log_level="debug" if config.server.debug else "info",
        access_log=True
    )
    uvicorn_server = uvicorn.Server(uvicorn_config)
    
    try:
        uvicorn_server.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        close_logger()
        sys.exit(0)

if __name__ == "__main__":
    main()
