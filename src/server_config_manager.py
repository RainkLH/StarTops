"""
Startops 服务配置管理模块
负责各业务服务自身的配置文件的注册、管理（文件路径、文件名等）
"""

import json
from pathlib import Path
from typing import Dict, Optional, Any, List
from src.utils.logger import get_logger

logger = get_logger('server_config_manager')


class ConfigFile:
    """配置文件信息类"""
    
    def __init__(
        self,
        config_id: str,
        service_name: str,
        config_name: str,
        config_file_path: str,
        meta_file_path: Optional[str] = None,
        description: str = ""
    ):
        """
        初始化配置文件信息
        
        Args:
            config_id: 配置唯一标识符
            service_name: 所属服务名称
            config_name: 配置名称
            config_file_path: 配置文件路径
            meta_file_path: 配置元数据文件路径（可选）
            description: 配置描述
        """
        self.config_id = config_id
        self.service_name = service_name
        self.config_name = config_name
        self.config_file_path = Path(config_file_path)
        self.meta_file_path = Path(meta_file_path) if meta_file_path else None
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "config_id": self.config_id,
            "service_name": self.service_name,
            "config_name": self.config_name,
            "config_file_path": str(self.config_file_path),
            "meta_file_path": str(self.meta_file_path) if self.meta_file_path else None,
            "description": self.description,
            "exists": self.config_file_path.exists()
        }


class ServerConfigManager:
    """服务配置管理器"""
    
    def __init__(self):
        """初始化服务配置管理器"""
        self.configs: Dict[str, ConfigFile] = {}
        self.service_configs: Dict[str, list] = {}  # service_name -> [config_id]
    
    def register_config(
        self,
        config_id: str,
        service_name: str,
        config_name: str,
        config_file_path: str,
        meta_file_path: Optional[str] = None,
        description: str = ""
    ) -> ConfigFile:
        """
        注册一个服务配置文件
        
        Args:
            config_id: 配置唯一标识符
            service_name: 所属服务名称
            config_name: 配置名称
            config_file_path: 配置文件路径
            meta_file_path: 配置元数据文件路径
            description: 配置描述
            
        Returns:
            ConfigFile: 已注册的配置对象
        """
        if config_id in self.configs:
            logger.warning(f"Config {config_id} already registered")
            return self.configs[config_id]
        
        config = ConfigFile(
            config_id=config_id,
            service_name=service_name,
            config_name=config_name,
            config_file_path=config_file_path,
            meta_file_path=meta_file_path,
            description=description
        )
        
        self.configs[config_id] = config
        
        # 维护服务配置索引
        if service_name not in self.service_configs:
            self.service_configs[service_name] = []
        self.service_configs[service_name].append(config_id)
        
        logger.info(f"Config {config_id} ({config_name}) registered for service {service_name}")
        return config
    
    def get_config(self, config_id: str) -> Optional[ConfigFile]:
        """获取指定配置"""
        return self.configs.get(config_id)
    
    def get_service_configs(self, service_name: str) -> List[ConfigFile]:
        """
        获取指定服务的所有配置
        
        Args:
            service_name: 服务名称
            
        Returns:
            list: 配置对象列表
        """
        config_ids = self.service_configs.get(service_name, [])
        return [self.configs[cid] for cid in config_ids if cid in self.configs]
    
    def get_all_configs(self) -> Dict[str, ConfigFile]:
        """获取所有配置"""
        return self.configs.copy()
    
    def read_config_file(self, config_id: str) -> Optional[Dict[str, Any]]:
        """
        读取配置文件内容
        
        Args:
            config_id: 配置ID
            
        Returns:
            dict: 配置内容，如果文件不存在或读取失败则返回None
        """
        config = self.get_config(config_id)
        if not config:
            logger.warning(f"Config {config_id} not found")
            return None
        
        try:
            if not config.config_file_path.exists():
                logger.warning(f"Config file not found: {config.config_file_path}")
                return None
            
            with open(config.config_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Config {config_id} loaded successfully")
            return data
            
        except Exception as e:
            logger.error(f"Failed to read config file {config_id}: {str(e)}")
            return None
    
    def read_meta_file(self, config_id: str) -> Optional[Dict[str, Any]]:
        """
        读取配置元数据文件内容
        
        Args:
            config_id: 配置ID
            
        Returns:
            dict: 元数据内容，如果文件不存在或读取失败则返回None
        """
        config = self.get_config(config_id)
        if not config:
            logger.warning(f"Config {config_id} not found")
            return None
        
        if not config.meta_file_path:
            logger.debug(f"Config {config_id} has no meta file path")
            return None
        
        try:
            if not config.meta_file_path.exists():
                logger.warning(f"Meta file not found: {config.meta_file_path}")
                return None
            
            with open(config.meta_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Meta file {config_id} loaded successfully")
            return data
            
        except Exception as e:
            logger.error(f"Failed to read meta file {config_id}: {str(e)}")
            return None
    
    def write_config_file(self, config_id: str, data: Dict[str, Any]) -> bool:
        """
        写入配置文件内容
        
        Args:
            config_id: 配置ID
            data: 要写入的数据
            
        Returns:
            bool: 是否成功写入
        """
        config = self.get_config(config_id)
        if not config:
            logger.warning(f"Config {config_id} not found")
            return False
        
        try:
            # 确保目录存在
            config.config_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Config {config_id} saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write config file {config_id}: {str(e)}")
            return False
    
    def validate_config(self, config_id: str, data: Dict[str, Any]) -> tuple[bool, str]:
        """
        根据元数据验证配置数据
        
        Args:
            config_id: 配置ID
            data: 要验证的数据
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        config = self.get_config(config_id)
        if not config:
            return False, f"Config {config_id} not found"
        
        meta = self.read_meta_file(config_id)
        if not meta:
            # 如果没有元数据，则认为有效
            return True, ""
        
        # 基础验证：检查必需字段
        for field_name, field_meta in meta.items():
            if field_meta.get("required", False) and field_name not in data:
                return False, f"Required field '{field_name}' is missing"
            
            if field_name in data:
                value = data[field_name]
                
                # 类型验证
                field_type = field_meta.get("type")
                if field_type == "number":
                    if not isinstance(value, (int, float)):
                        return False, f"Field '{field_name}' must be a number"
                    
                    # 范围验证
                    if "min" in field_meta and value < field_meta["min"]:
                        return False, f"Field '{field_name}' is below minimum value {field_meta['min']}"
                    if "max" in field_meta and value > field_meta["max"]:
                        return False, f"Field '{field_name}' is above maximum value {field_meta['max']}"
                
                elif field_type == "string":
                    if not isinstance(value, str):
                        return False, f"Field '{field_name}' must be a string"
                    
                    # 长度验证
                    if "min_length" in field_meta and len(value) < field_meta["min_length"]:
                        return False, f"Field '{field_name}' is too short"
                    if "max_length" in field_meta and len(value) > field_meta["max_length"]:
                        return False, f"Field '{field_name}' is too long"
        
        return True, ""
    
    def unregister_config(self, config_id: str) -> bool:
        """
        注销一个配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            bool: 是否成功注销
        """
        if config_id not in self.configs:
            logger.warning(f"Config {config_id} not found")
            return False
        
        config = self.configs.pop(config_id)
        
        # 从服务配置索引中删除
        if config.service_name in self.service_configs:
            self.service_configs[config.service_name].remove(config_id)
        
        logger.info(f"Config {config_id} unregistered")
        return True
