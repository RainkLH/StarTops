"""
Startops 服务监控模块
负责各业务服务的监控注册、管理、健康检查、启动、停止、重启等功能
"""

import asyncio
import json
import os
import shlex
import subprocess
import time
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum
from pathlib import Path

import httpx

from src.utils.logger import get_logger

logger = get_logger('server_monitor')


class ServiceStatus(str, Enum):
    """服务状态枚举"""
    RUNNING = "Running"
    STOPPED = "Stopped"  # 手动停止状态
    STARTING = "Starting"  # 启动中
    STOPPING = "Stopping"  # 停止中
    ERROR = "Error"
    UNKNOWN = "Unknown"


class ServiceInfo:
    """服务信息类 - 用于结构化存储配置数据"""
    
    def __init__(
        self,
        name: str,
        url: str,
        health_check_interval: int,
        health_check_url: str,
        executor: str = "",
        app_dir: str = "",
        app_file_name: str = "",
        app_args: str = "",
        start_cmd: str = "",
        stop_cmd: str = "",
        description: str = "",
        keep_alive: bool = True,
        start_timeout: int = 45,
        stop_timeout: int = 45
    ):
        """
        初始化服务信息配置
        
        Args:
            name: 服务显示名称
            url: 服务访问地址
            health_check_interval: 健康检查间隔（秒）
            health_check_url: 健康检查端点
            executor: 程序启动器（如python、dotnet等）
            app_dir: 应用所在目录
            app_file_name: 应用文件名
            app_args: 应用启动参数，默认空
            start_cmd: 启动命令，优先级高于executor方案，默认空
            stop_cmd: 停止命令，优先级高于自动停止，默认空
            description: 服务描述
            keep_alive: 是否保持进程活跃
            start_timeout: 启动超时时间（秒），默认45
            stop_timeout: 停止超时时间（秒），默认45
        """
        self.name = name
        self.description = description
        self.url = url
        self.health_check_interval = health_check_interval
        self.health_check_url = health_check_url
        self.executor = executor
        self.app_dir = app_dir
        self.app_file_name = app_file_name
        self.app_args = app_args
        self.start_cmd = start_cmd
        self.stop_cmd = stop_cmd
        self.keep_alive = keep_alive
        self.start_timeout = start_timeout
        self.stop_timeout = stop_timeout


class Service(ServiceInfo):
    """服务类 - 继承ServiceInfo，添加实时监控属性"""
    
    def __init__(
        self,
        service_name: str,
        service_info: ServiceInfo
    ):
        """
        从ServiceInfo初始化Service
        
        Args:
            service_name: 服务名称（作为唯一标识）
            service_info: ServiceInfo实例
        """
        # 继承ServiceInfo的所有属性
        super().__init__(
            name=service_info.name,
            url=service_info.url,
            health_check_interval=service_info.health_check_interval,
            health_check_url=service_info.health_check_url,
            executor=service_info.executor,
            app_dir=service_info.app_dir,
            app_file_name=service_info.app_file_name,
            app_args=service_info.app_args,
            start_cmd=service_info.start_cmd,
            stop_cmd=service_info.stop_cmd,
            description=service_info.description,
            keep_alive=service_info.keep_alive,
            start_timeout=service_info.start_timeout,
            stop_timeout=service_info.stop_timeout
        )
        
        # 添加实时动态属性
        self.service_name = service_name  # 使用服务名作为唯一标识
        self.pid: Optional[int] = None
        self.status = ServiceStatus.UNKNOWN
        self.status_seted_time: Optional[str] = None
        self.last_check_time: Optional[str] = None
        self.is_manually_stopped = False
        self.message: Optional[str] = None  # 记录过程中的信息或失败信息
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "service_name": self.service_name,
            "name": self.name,
            "url": self.url,
            "health_check_url": self.health_check_url,
            "status": self.status.value,
            "pid": self.pid,
            "last_check_time": self.last_check_time,
            "description": self.description,
            "is_manually_stopped": self.is_manually_stopped,
            "guard_enabled": not self.is_manually_stopped,
            "keep_alive": self.keep_alive,
            "message": self.message
        }


class ServerMonitor:
    """服务监控管理器"""
    
    def __init__(self, check_interval: int = 30):
        """
        初始化服务监控管理器
        
        Args:
            check_interval: 健康检查间隔（秒），默认30秒
        """
        self.services: Dict[str, Service] = {}
        self.check_interval = check_interval
        self.monitor_task = None
        self.is_running = False
        self.config_file = Path(__file__).parent.parent / "configs" / "service_list.json"

    def _save_to_config(self) -> bool:
        """将当前服务配置持久化到配置文件"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            service_list = []
            for service_name in sorted(self.services.keys()):
                service = self.services[service_name]
                service_list.append({
                    "name": service.name,
                    "url": service.url,
                    "health_check_interval": service.health_check_interval,
                    "health_check_url": service.health_check_url,
                    "executor": service.executor,
                    "app_dir": service.app_dir,
                    "app_file_name": service.app_file_name,
                    "app_args": service.app_args,
                    "start_cmd": service.start_cmd,
                    "stop_cmd": service.stop_cmd,
                    "description": service.description,
                    "keep_alive": service.keep_alive,
                    "start_timeout": service.start_timeout,
                    "stop_timeout": service.stop_timeout
                })

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(service_list, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save service config file: {str(e)}")
            return False
    
    def initialize_service(self) -> "ServerMonitor":
        """
        从config/service_list.json初始化所有服务
        
        返回ServerMonitor对象自身，支持链式调用
        - 如果文件不存在，返回空列表
        - 如果文件解析失败，将文件改名为.json.error并生成新的空文件
        
        Returns:
            ServerMonitor: 返回self以支持链式调用
        """
        config_file = self.config_file
        self.services.clear()
        
        if not config_file.exists():
            logger.warning(f"Service config file not found: {config_file}")
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return self
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                service_list = json.load(f)
            
            for index, service_config in enumerate(service_list):
                try:
                    # 创建ServiceInfo对象
                    service_info = ServiceInfo(**service_config)
                    
                    # 使用服务名作为唯一标识
                    service_name = service_info.name
                    
                    # 创建Service实例
                    service = Service(service_name=service_name, service_info=service_info)
                    
                    # 初始化动态属性
                    # 1. 通过health_check_url检查服务状态
                    if service.health_check_url:
                        health_check_result = asyncio.run(self.check_health(service_name, service=service))
                    else:
                        service.status = ServiceStatus.UNKNOWN
                    
                    # 2. 获取进程PID
                    service.pid = self._get_process_pid(
                        service.app_dir,
                        service.app_file_name
                    )
                    
                    # 3. 如果状态为UNKNOWN，改为ERROR
                    if service.status == ServiceStatus.UNKNOWN:
                        service.status = ServiceStatus.ERROR
                    
                    # 4. 更新状态设置时间和最后检查时间
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    service.status_seted_time = current_time
                    service.last_check_time = current_time
                    
                    # 5. 初始化is_manually_stopped为false
                    service.is_manually_stopped = False
                    
                    # 存储服务
                    self.services[service_name] = service
                    logger.info(f"Service {service_name} initialized with status: {service.status.value}")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize service at index {index}: {str(e)}")
                    continue
            
            logger.info(f"Total {len(self.services)} services initialized")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse service config file: {str(e)}")
            # 改名为.json.error文件
            error_file = config_file.with_suffix('.json.error')
            if error_file.exists():
                error_file.unlink()
            config_file.rename(error_file)
            logger.info(f"Renamed corrupted file to: {error_file}")
            # 生成新的空列表文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            logger.info(f"Created new empty service list file: {config_file}")
        except Exception as e:
            logger.error(f"Error during service initialization: {str(e)}")
        
        return self
    
    def _get_process_pid(self, app_dir: str, app_file_name: str) -> Optional[int]:
        """
        获取进程PID
        
        使用pgrep命令查找匹配的进程
        
        Args:
            app_dir: 应用所在目录
            app_file_name: 应用文件名
            
        Returns:
            Optional[int]: 进程PID，如果不存在则返回None
        """
        if not app_file_name:
            return None

        try:
            # Windows系统使用tasklist，Linux/Unix使用pgrep
            if os.name == 'nt':  # Windows
                # 使用tasklist获取进程信息
                result = subprocess.run(
                    f'tasklist /FI "IMAGENAME eq {app_file_name}" /FO CSV',
                    capture_output=True,
                    text=True,
                    shell=True
                )
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        # CSV格式: "进程名","PID"
                        parts = lines[1].split(',')
                        if len(parts) >= 2:
                            pid_str = parts[1].strip('"')
                            return int(pid_str)
            else:  # Linux/Unix
                # 使用pgrep和pwdx查找进程
                cmd = f'pgrep -f "{app_file_name}" | xargs pwdx | grep "{app_dir}" | awk -F: \'{{print $1}}\''
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    shell=True
                )
                if result.stdout.strip():
                    pid_str = result.stdout.strip().split('\n')[0]
                    return int(pid_str)
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to get process PID for {app_file_name}: {str(e)}")
            return None
    
    def _process_exists(self, pid: int) -> bool:
        """
        检查指定PID的进程是否存在
        
        Args:
            pid: 进程ID
            
        Returns:
            bool: 进程是否存在
        """
        try:
            if os.name == 'nt':  # Windows
                # 使用tasklist检查进程是否存在
                result = subprocess.run(
                    f'tasklist /FI "PID eq {pid}" /FO CSV',
                    capture_output=True,
                    text=True,
                    shell=True
                )
                # 如果输出超过1行（包括header），说明进程存在
                return len(result.stdout.strip().split('\n')) > 1
            else:  # Linux/Unix
                # 使用kill -0检查进程存在性
                result = subprocess.run(
                    f'kill -0 {pid}',
                    capture_output=True,
                    shell=True
                )
                return result.returncode == 0
        except Exception as e:
            logger.debug(f"Failed to check if process {pid} exists: {str(e)}")
            return False
    
    def _build_start_command(self, service: Service) -> str:
        """
        构建启动命令
        
        优先级：start_cmd > executor + app_dir + app_file_name + app_args
        
        Args:
            service: Service对象
            
        Returns:
            str: 启动命令
        """
        if service.start_cmd:
            return service.start_cmd

        if not service.executor or not service.app_file_name:
            return ""
        
        # 使用executor方案构建启动命令
        app_path = os.path.join(service.app_dir, service.app_file_name)
        
        if service.app_args:
            return f'{service.executor} "{app_path}" {service.app_args}'
        else:
            return f'{service.executor} "{app_path}"'
    
    def _build_stop_command(self, service: Service) -> Optional[str]:
        """
        构建停止命令
        
        优先级：stop_cmd > 通过PID杀死进程
        
        Args:
            service: Service对象
            
        Returns:
            Optional[str]: 停止命令，无法自动构建时返回None
        """
        # 1. 如果有stop_cmd，直接返回
        if service.stop_cmd:
            return service.stop_cmd
        
        # 2. 如果没有pid，尝试获取pid
        if not service.pid and service.app_file_name:
            service.pid = self._get_process_pid(
                service.app_dir,
                service.app_file_name
            )
        
        # 3. 如果有pid，构建杀死进程的命令
        if service.pid:
            if os.name == 'nt':  # Windows
                return f'taskkill /PID {service.pid} /F'
            else:  # Linux/Unix
                return f'kill -9 {service.pid}'
        
        # 4. 无法自动构建停止命令
        return None
    
    def register_service(
        self,
        name: str,
        health_check_url: str,
        executor: str = "",
        app_dir: str = "",
        app_file_name: str = "",
        app_args: str = "",
        start_cmd: str = "",
        stop_cmd: str = "",
        url: str = "",
        health_check_interval: int = 10,
        description: str = "",
        keep_alive: bool = True,
        start_timeout: int = 45,
        stop_timeout: int = 45,
        persist: bool = True
    ) -> Service:
        """
        动态注册一个服务（用于运行时动态添加）
        
        Args:
            name: 服务名称（唯一标识）
            health_check_url: 健康检查端点
            executor: 程序启动器（如python、dotnet等），默认空
            app_dir: 应用所在目录，默认空
            app_file_name: 应用文件名，默认空
            app_args: 应用启动参数，默认空
            start_cmd: 启动命令，优先级高，默认空
            stop_cmd: 停止命令，默认空
            url: 服务地址，默认空
            health_check_interval: 健康检查间隔（秒），默认10
            description: 服务描述
            keep_alive: 是否自动保活，默认True
            start_timeout: 启动超时时间（秒），默认45
            stop_timeout: 停止超时时间（秒），默认45
            
        Returns:
            Service: 已注册的服务对象
        """
        if name in self.services:
            logger.warning(f"Service {name} already registered")
            return self.services[name]
        
        # 创建ServiceInfo
        service_info = ServiceInfo(
            name=name,
            url=url,
            health_check_interval=health_check_interval,
            health_check_url=health_check_url,
            executor=executor,
            app_dir=app_dir,
            app_file_name=app_file_name,
            app_args=app_args,
            start_cmd=start_cmd,
            stop_cmd=stop_cmd,
            description=description,
            keep_alive=keep_alive,
            start_timeout=start_timeout,
            stop_timeout=stop_timeout
        )
        
        # 创建Service
        service = Service(service_name=name, service_info=service_info)
        
        # 初始化时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        service.status_seted_time = current_time
        service.last_check_time = current_time
        
        self.services[name] = service

        if persist and not self._save_to_config():
            self.services.pop(name, None)
            raise RuntimeError("Failed to persist service config")

        logger.info(f"Service {name} registered successfully")
        return service

    def unregister_service(self, service_name: str) -> bool:
        """注销指定服务并同步更新配置文件"""
        if service_name not in self.services:
            logger.warning(f"Service {service_name} not found")
            return False

        service = self.services.pop(service_name)

        if not self._save_to_config():
            self.services[service_name] = service
            logger.error(f"Failed to persist config while unregistering service {service_name}")
            return False

        logger.info(f"Service {service_name} unregistered successfully")
        return True
    
    def get_service(self, service_name: str) -> Optional[Service]:
        """获取指定服务"""
        return self.services.get(service_name)
    
    def get_all_services(self) -> Dict[str, Service]:
        """获取所有服务"""
        return self.services.copy()
    
    async def check_health(
        self,
        service_name: str,
        service: Optional[Service] = None
    ) -> bool:
        """
        检查指定服务的健康状态
        
        Args:
            service_name: 服务名称
            service: Service对象（可选，用于初始化时传入临时Service）
            
        Returns:
            bool: 是否健康
        """
        if service is None:
            service = self.get_service(service_name)
        
        if not service:
            logger.warning(f"Service {service_name} not found")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(service.health_check_url)
                is_healthy = response.status_code == 200
                
                service.last_check_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                service.status = ServiceStatus.RUNNING if is_healthy else ServiceStatus.ERROR
                
                logger.debug(f"Service {service_name} health check: {'OK' if is_healthy else 'FAILED'}")
                return is_healthy
                
        except Exception as e:
            logger.debug(f"Health check failed for {service_name}: {str(e)}")
            service.status = ServiceStatus.ERROR
            service.last_check_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            service.message = f"Health check failed: {str(e)}"
            return False
    
    def start_service(self, service_name: str) -> bool:
        """
        启动指定服务
        
        1. 立即设置状态为Starting
        2. 异步执行启动命令
        3. 在start_timeout时间内轮询检查健康状态
        4. 成功则更新状态为Running，失败则为Unknown
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 是否成功执行启动命令
        """
        logger.info(f" ▶ Starting service: {service_name}")
        service = self.get_service(service_name)
        if not service:
            logger.error(f"Service {service_name} not found")
            return False
        
        # 构建启动命令
        cmd = self._build_start_command(service)
        if not cmd:
            service.message = "No start command or executor configured"
            logger.warning(service.message)
            return False
        
        # 1. 立即设置状态为Starting
        service.status = ServiceStatus.STARTING
        service.is_manually_stopped = False
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        service.status_seted_time = current_time
        service.message = "Service is starting..."
        logger.info(f"Service {service_name} starting...")
        
        # 2. 异步执行启动
        asyncio.create_task(self._async_start_service(service_name, cmd))
        return True
    
    async def _async_start_service(self, service_name: str, cmd: str):
        """
        异步执行服务启动及超时控制
        
        Args:
            service_name: 服务名称
            cmd: 启动命令
        """
        logger.info(f"Async start command for {service_name}: {cmd}")
        service = self.get_service(service_name)
        logger.info(f"Service {service_name} before start - PID: {service.pid}, Status: {service.status.value}")
        if not service:
            return
        
        try:
            logger.info(f"os.name {os.name}")
            # 执行启动命令
            if os.name == 'nt':  # Windows
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200                
                process = subprocess.Popen(
                    cmd,
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,                    
                    close_fds=True
                )
                service.pid = process.pid
            else:  # Linux/Unix
                working_dir = service.app_dir if service.app_dir and os.path.isdir(service.app_dir) else None
                cmd_args = shlex.split(cmd)
                process = subprocess.Popen(
                    cmd_args,
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    cwd=working_dir,
                    start_new_session=True,
                    close_fds=True
                )
                service.pid = process.pid
            
            logger.info(f"Service {service_name} start command executed: {cmd} (PID: {service.pid})")
            
            # 3. 在start_timeout时间内轮询检查健康状态
            timeout = service.start_timeout
            interval = 1  # 每1秒检查一次
            elapsed = 0
            
            while elapsed < timeout:
                await asyncio.sleep(interval)
                elapsed += interval
                
                # 如果pid为空，尝试通过pgrep查询
                if service.pid is None and service.app_file_name:
                    service.pid = self._get_process_pid(
                        service.app_dir,
                        service.app_file_name
                    )
                
                # 执行健康检查
                is_healthy = await self.check_health(service_name)
                
                if is_healthy:
                    service.status = ServiceStatus.RUNNING
                    service.message = "Service started successfully"
                    logger.info(f"Service {service_name} is running")
                    return
            
            # 超时后仍未成功
            service.status = ServiceStatus.UNKNOWN
            service.message = f"Start timeout after {timeout}s"
            logger.warning(service.message)
            
        except Exception as e:
            service.status = ServiceStatus.UNKNOWN
            service.message = f"Failed to start service: {str(e)}"
            logger.error(service.message)
    
    def stop_service(self, service_name: str) -> bool:
        """
        停止指定服务
        
        1. 立即设置状态为Stopping
        2. 异步执行停止命令
        3. 在stop_timeout时间内检查进程存活性和健康状态
        4. 确认停止后更新状态为Stopped
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 是否成功执行停止命令
        """
        logger.info(f" ■ Stopping service: {service_name}")
        service = self.get_service(service_name)
        if not service:
            logger.error(f"Service {service_name} not found")
            return False
        
        # 获取停止命令
        cmd = self._build_stop_command(service)
        if not cmd:
            service.message = "Stop command is not configured"
            logger.warning(service.message)
            return False
        
        # 1. 立即设置状态为Stopping
        service.status = ServiceStatus.STOPPING
        service.is_manually_stopped = True
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        service.status_seted_time = current_time
        service.message = "Service is stopping..."
        logger.info(f"Service {service_name} stopping...")
        
        # 2. 异步执行停止
        asyncio.create_task(self._async_stop_service(service_name, cmd))
        return True
    
    async def _async_stop_service(self, service_name: str, cmd: str):
        """
        异步执行服务停止及超时控制
        
        Args:
            service_name: 服务名称
            cmd: 停止命令
        """
        service = self.get_service(service_name)
        if not service:
            return
        
        try:
            # 执行停止命令
            subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                timeout=5
            )
            logger.info(f"Service {service_name} stop command executed: {cmd}")
            
            # 3. 在stop_timeout时间内检查进程存活性
            timeout = service.stop_timeout
            interval = 1  # 每1秒检查一次
            elapsed = 0
            
            while elapsed < timeout:
                await asyncio.sleep(interval)
                elapsed += interval
                
                # 如果pid有值，检查进程是否存在
                if service.pid:
                    if not self._process_exists(service.pid):
                        # 进程已结束
                        service.pid = None
                        service.status = ServiceStatus.STOPPED
                        service.message = "Service stopped successfully"
                        logger.info(f"Service {service_name} has stopped (process no longer exists)")
                        return
                else:
                    # 无pid，通过健康检查确认
                    try:
                        is_healthy = await self.check_health(service_name)
                        if not is_healthy:
                            # 健康检查失败，认为服务已停止
                            service.status = ServiceStatus.STOPPED
                            service.message = "Service stopped successfully (health check failed)"
                            logger.info(f"Service {service_name} stopped")
                            return
                    except:
                        # 健康检查异常，认为服务已停止
                        service.status = ServiceStatus.STOPPED
                        service.message = "Service stopped successfully"
                        logger.info(f"Service {service_name} stopped")
                        return
            
            # 超时后仍未确认停止
            service.status = ServiceStatus.UNKNOWN
            service.message = f"Stop timeout after {timeout}s"
            logger.warning(service.message)
            
        except subprocess.TimeoutExpired:
            service.status = ServiceStatus.UNKNOWN
            service.message = "Stop command timeout"
            logger.warning(service.message)
        except Exception as e:
            service.status = ServiceStatus.UNKNOWN
            service.message = f"Failed to stop service: {str(e)}"
            logger.error(service.message)
    
    def restart_service(self, service_name: str) -> bool:
        """
        重启指定服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 是否重启成功
        """
        if not self.stop_service(service_name):
            return False
        
        # 等待一会儿再启动
        time.sleep(1)
        
        return self.start_service(service_name)

    def set_guard(self, service_name: str, enabled: bool) -> bool:
        """设置服务守护开关"""
        service = self.get_service(service_name)
        if not service:
            logger.error(f"Service {service_name} not found")
            return False

        service.is_manually_stopped = not enabled
        service.message = f"Guard set to {enabled}"
        logger.info(f"Service {service_name} guard set to {enabled}")
        return True
    
    async def monitor_loop(self):
        """
        监控循环 - 定期检查所有服务的健康状态
        如果服务异常且非手动停止状态且keep_alive为true，则自动重启
        """
        logger.info("Monitor loop started")
        self.is_running = True
        
        while self.is_running:
            try:
                # 检查所有服务
                tasks = [
                    self.check_health(service_name)
                    for service_name in self.services.keys()
                ]
                
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # 检查失败的服务是否需要重启
                for service_name, service in self.services.items():
                    if (service.status == ServiceStatus.ERROR and 
                        not service.is_manually_stopped and
                        service.keep_alive):
                        logger.warning(f"Service {service_name} is down, attempting restart...")
                        self.start_service(service_name)
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    async def start_monitoring(self):
        """启动监控任务"""
        if self.monitor_task is None or self.monitor_task.done():
            self.monitor_task = asyncio.create_task(self.monitor_loop())
    
    async def stop_monitoring(self):
        """停止监控任务"""
        self.is_running = False
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
