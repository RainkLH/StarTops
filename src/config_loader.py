"""
StarTops 配置加载器
负责配置文件的读取、校验、命令行参数覆盖等功能
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_default_terminal_shell() -> str:
    """根据平台返回默认 shell。"""
    return "cmd.exe" if sys.platform == "win32" else "/bin/bash"


# ===== 配置数据模型 =====

class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = Field(default="127.0.0.1", description="监听地址")
    port: int = Field(default=8300, ge=1, le=65535, description="监听端口")
    debug: bool = Field(default=False, description="调试模式")
    restart_by_self: bool = Field(default=False, description="是否由进程自身完成重启")


class NodesConfig(BaseModel):
    """节点配置"""
    provider: str = Field(default="ConfigFile", description="节点获取方式：Consul 或 ConfigFile")
    
    class ConsulConfig(BaseModel):
        """Consul 配置"""
        host: str = Field(default="127.0.0.1", description="Consul 地址")
        port: int = Field(default=8500, ge=1, le=65535, description="Consul 端口")
        service_name: str = Field(default="startops", description="服务名称")
    
    consul: ConsulConfig = Field(default_factory=ConsulConfig, description="Consul 配置")


class LogsConfig(BaseModel):
    """日志配置"""
    enabled: bool = Field(default=True, description="是否启用日志文件")
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )


class TerminalConfig(BaseModel):
    """终端配置"""
    enabled: bool = Field(default=True, description="是否启用网页终端")
    shell: str = Field(default_factory=get_default_terminal_shell, description="Shell 程序")
    timeout: int = Field(default=300, ge=0, description="会话超时时间（秒）")
    allowed_commands: list[str] = Field(default_factory=list, description="命令白名单（空表示不限制）")


class StartopsConfig(BaseSettings):
    """StarTops 主配置"""
    
    model_config = SettingsConfigDict(
        env_prefix="STARTOPS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    server: ServerConfig = Field(default_factory=ServerConfig, description="服务器配置")
    nodes: NodesConfig = Field(default_factory=NodesConfig, description="节点配置")
    logs: LogsConfig = Field(default_factory=LogsConfig, description="日志配置")
    terminal: TerminalConfig = Field(default_factory=TerminalConfig, description="终端配置")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()


# ===== 配置加载器 =====

class ConfigLoader:
    """配置加载器"""
    
    DEFAULT_CONFIG = {
        "server": {
            "host": "127.0.0.1",
            "port": 8300,
            "debug": False,
            "restart_by_self": False
        },
        "nodes": {
            "provider": "ConfigFile",
            "consul": {
                "host": "127.0.0.1",
                "port": 8500,
                "service_name": "startops"
            }
        },
        "logs": {
            "enabled": True,
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "terminal": {
            "enabled": True,
            "shell": get_default_terminal_shell(),
            "timeout": 300,
            "allowed_commands": []
        }
    }
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_dir: 配置文件目录，默认为项目根目录的 configs/
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # 默认在项目根目录的 configs/
            self.config_dir = Path(__file__).parent.parent / "configs"
        
        self.config_file = self.config_dir / "startops.json"
        self.config: Optional[StartopsConfig] = None
    
    def ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def create_default_config(self) -> Path:
        """
        创建默认配置文件
        
        Returns:
            配置文件路径
        """
        self.ensure_config_dir()
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        
        return self.config_file
    
    def load_config(self) -> StartopsConfig:
        """
        加载配置文件
        
        Returns:
            配置对象
        """
        if self.config_file.exists():
            # 读取配置文件
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        else:
            # 配置文件不存在，创建默认配置
            self.create_default_config()
            config_data = self.DEFAULT_CONFIG.copy()

        # 自动修正 Windows 下常见的无效 shell 配置
        if sys.platform == 'win32':
            terminal_data = config_data.get("terminal", {})
            shell = str(terminal_data.get("shell", "")).strip()
            if not shell or shell.startswith('/'):
                terminal_data["shell"] = get_default_terminal_shell()
                config_data["terminal"] = terminal_data
        
        # 使用 pydantic 校验并创建配置对象
        self.config = StartopsConfig(**config_data)
        return self.config
    
    def apply_command_line_args(self, args: Dict[str, Any]) -> StartopsConfig:
        """
        应用命令行参数覆盖配置
        
        Args:
            args: 命令行参数字典，如 {"host": "0.0.0.0", "port": 9000}
        
        Returns:
            更新后的配置对象
        """
        if self.config is None:
            self.load_config()
        
        # 覆盖服务器配置
        if "host" in args and args["host"]:
            self.config.server.host = args["host"]
        if "port" in args and args["port"]:
            self.config.server.port = args["port"]
        if "debug" in args and args["debug"] is not None:
            self.config.server.debug = args["debug"]
        
        return self.config
    
    def get_config(self) -> StartopsConfig:
        """获取配置对象"""
        if self.config is None:
            self.load_config()
        return self.config
    
    def save_config(self, config: Optional[StartopsConfig] = None):
        """
        保存配置到文件
        
        Args:
            config: 配置对象，None 则使用当前配置
        """
        if config is None:
            config = self.get_config()
        
        self.ensure_config_dir()
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)


# ===== 便捷函数 =====

def get_config(
    config_dir: Optional[str] = None,
    command_line_args: Optional[Dict[str, Any]] = None
) -> StartopsConfig:
    """
    获取配置（加载 + 应用命令行参数）
    
    Args:
        config_dir: 配置文件目录
        command_line_args: 命令行参数
    
    Returns:
        配置对象
    """
    loader = ConfigLoader(config_dir)
    config = loader.load_config()
    
    if command_line_args:
        config = loader.apply_command_line_args(command_line_args)
    
    return config


def create_default_config_file(config_dir: Optional[str] = None) -> Path:
    """
    创建默认配置文件
    
    Args:
        config_dir: 配置文件目录
    
    Returns:
        配置文件路径
    """
    loader = ConfigLoader(config_dir)
    return loader.create_default_config()
