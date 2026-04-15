"""
Startops 核心逻辑模块
程序主要逻辑、各模块调度、接口封装
"""

from typing import Dict, Optional, Any, List
from src.server_monitor import ServerMonitor, Service
from src.server_pages_manager import ServerPagesManager, ServerPage
from src.server_config_manager import ServerConfigManager, ConfigFile
from src.config_editor_render import ConfigEditorRenderer
from src.utils.logger import get_logger

logger = get_logger('startops')


class Startops:
    """Startops 核心管理类"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化Startops"""
        if not hasattr(self, 'initialized'):
            self.server_monitor = ServerMonitor(check_interval=30).initialize_service()
            self.pages_manager = ServerPagesManager().initialize_service()
            self.config_manager = ServerConfigManager()
            self.renderer = ConfigEditorRenderer()
            self.initialized = True
            logger.info("Startops initialized")
    
    # ===== 服务监控相关方法 =====
    
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
        stop_timeout: int = 45
    ) -> Service:
        """注册服务"""
        return self.server_monitor.register_service(
            name=name,
            health_check_url=health_check_url,
            executor=executor,
            app_dir=app_dir,
            app_file_name=app_file_name,
            app_args=app_args,
            start_cmd=start_cmd,
            stop_cmd=stop_cmd,
            url=url,
            health_check_interval=health_check_interval,
            description=description,
            keep_alive=keep_alive,
            start_timeout=start_timeout,
            stop_timeout=stop_timeout
        )

    def unregister_service(self, service_name: str) -> bool:
        """注销服务"""
        return self.server_monitor.unregister_service(service_name)
    
    def get_service(self, service_name: str) -> Optional[Service]:
        """获取服务"""
        return self.server_monitor.get_service(service_name)
    
    def get_all_services(self) -> Dict[str, Service]:
        """获取所有服务"""
        return self.server_monitor.get_all_services()
    
    def get_services_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务的状态信息"""
        services = self.server_monitor.get_all_services()
        return {sname: svc.to_dict() for sname, svc in services.items()}
    
    async def check_service_health(self, service_name: str) -> bool:
        """检查服务健康状态"""
        return await self.server_monitor.check_health(service_name)
    
    def start_service(self, service_name: str) -> bool:
        """启动服务"""
        return self.server_monitor.start_service(service_name)
    
    def stop_service(self, service_name: str) -> bool:
        """停止服务"""
        return self.server_monitor.stop_service(service_name)
    
    def restart_service(self, service_name: str) -> bool:
        """重启服务"""
        return self.server_monitor.restart_service(service_name)

    def set_service_guard(self, service_name: str, enabled: bool) -> bool:
        """设置服务守护开关"""
        return self.server_monitor.set_guard(service_name, enabled)
    
    async def start_monitoring(self):
        """启动监控任务"""
        await self.server_monitor.start_monitoring()
    
    async def stop_monitoring(self):
        """停止监控任务"""
        await self.server_monitor.stop_monitoring()
    
    # ===== 服务页面相关方法 =====
    
    def register_page(
        self,
        service_name: str,
        page_name: str,
        page_url: str,
        icon: str = "🔧",
        description: str = ""
    ) -> ServerPage:
        """注册服务页面"""
        return self.pages_manager.register_page(
            service_name, page_name, page_url, icon, description
        )
        
    def get_service_pages(self, service_name: str) -> List[ServerPage]:
        """获取服务的所有页面"""
        return self.pages_manager.get_service_pages(service_name)
    
    def get_all_pages(self) -> Dict[str, ServerPage]:
        """获取所有页面"""
        return self.pages_manager.get_all_pages()
    
    def unregister_page(self, service_name: str, page_name: str) -> bool:
        """注销页面"""
        return self.pages_manager.unregister_page(service_name, page_name)

    def update_page_url(self, service_name: str, page_name: str, new_url: str) -> bool:
        """更新页面URL"""
        return self.pages_manager.update_page_url(service_name, page_name, new_url)
    
    # ===== 配置管理相关方法 =====
    
    def register_config(
        self,
        config_id: str,
        service_name: str,
        config_name: str,
        config_file_path: str,
        meta_file_path: Optional[str] = None,
        description: str = ""
    ) -> ConfigFile:
        """注册配置"""
        return self.config_manager.register_config(
            config_id, service_name, config_name, config_file_path,
            meta_file_path, description
        )
    
    def get_config(self, config_id: str) -> Optional[ConfigFile]:
        """获取配置"""
        return self.config_manager.get_config(config_id)
    
    def get_service_configs(self, service_name: str) -> List[ConfigFile]:
        """获取服务的所有配置"""
        return self.config_manager.get_service_configs(service_name)

    def get_all_configs(self) -> Dict[str, ConfigFile]:
        """获取所有配置"""
        return self.config_manager.get_all_configs()
    
    def read_config_data(self, config_id: str) -> Optional[Dict[str, Any]]:
        """读取配置数据"""
        return self.config_manager.read_config_file(config_id)
    
    def read_config_meta(self, config_id: str) -> Optional[Dict[str, Any]]:
        """读取配置元数据"""
        return self.config_manager.read_meta_file(config_id)
    
    def write_config_data(self, config_id: str, data: Dict[str, Any]) -> bool:
        """写入配置数据"""
        return self.config_manager.write_config_file(config_id, data)
    
    def validate_config_data(self, config_id: str, data: Dict[str, Any]) -> tuple:
        """验证配置数据"""
        return self.config_manager.validate_config(config_id, data)
    
    def unregister_config(self, config_id: str) -> bool:
        """注销配置"""
        return self.config_manager.unregister_config(config_id)
    
    # ===== 配置编辑器相关方法 =====
    
    def render_config_form(
        self,
        config_id: str,
        form_action: str = "",
        form_id: str = "config-form"
    ) -> Optional[str]:
        """
        渲染配置编辑表单
        
        Args:
            config_id: 配置ID
            form_action: 表单提交的URL
            form_id: 表单ID
            
        Returns:
            str: 表单HTML代码，如果配置不存在则返回None
        """
        config_data = self.read_config_data(config_id)
        if config_data is None:
            logger.warning(f"Config {config_id} not found or cannot be read")
            return None
        
        meta_data = self.read_config_meta(config_id)
        
        return self.renderer.render_form_html(
            config_data, meta_data, form_action, form_id
        )
    
    def render_config_field(
        self,
        field_name: str,
        field_value: Any,
        field_meta: Optional[Dict[str, Any]] = None
    ) -> str:
        """渲染单个配置字段"""
        return self.renderer.render_form_field(field_name, field_value, field_meta)
    
    # ===== 信息获取相关方法 =====
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "services_count": len(self.server_monitor.get_all_services()),
            "pages_count": len(self.pages_manager.get_all_pages()),
            "configs_count": len(self.config_manager.get_all_configs()),
            "services_status": self.get_services_status()
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表盘数据"""
        services = self.server_monitor.get_all_services()
        
        return {
            "total_services": len(services),
            "running_services": sum(
                1 for s in services.values()
                if s.status.value == "Running"
            ),
            "stopped_services": sum(
                1 for s in services.values()
                if s.status.value == "Stopped"
            ),
            "error_services": sum(
                1 for s in services.values()
                if s.status.value == "Error"
            ),
            "services": [s.to_dict() for s in services.values()]
        }


# 全局实例
_startops = Startops()


def get_startops() -> Startops:
    """获取Startops全局实例"""
    return _startops
