"""
StarTops 节点提供者
支持 Consul 和 ConfigFile 两种节点获取方式
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx

from src.utils.logger import get_logger

logger = get_logger('node_provider')


# ===== 节点数据模型 =====

class NodeInfo:
    """节点信息"""
    
    def __init__(
        self,
        node_id: str,
        node_name: str,
        address: str,
        port: int,
        status: str = "unknown",
        is_current: bool = False
    ):
        self.node_id = node_id
        self.node_name = node_name
        self.address = address
        self.port = port
        self.status = status  # healthy, warning, error, unknown
        self.is_current = is_current
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "address": self.address,
            "port": self.port,
            "status": self.status,
            "is_current": self.is_current
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NodeInfo':
        """从字典创建"""
        return cls(
            node_id=data.get("node_id", ""),
            node_name=data.get("node_name", ""),
            address=data.get("address", ""),
            port=data.get("port", 8300),
            status=data.get("status", "unknown"),
            is_current=data.get("is_current", False)
        )


# ===== 节点提供者基类 =====

class NodeProvider(ABC):
    """节点提供者基类"""
    
    @abstractmethod
    async def get_nodes(self) -> List[NodeInfo]:
        """获取节点列表"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供者名称"""
        pass


# ===== ConfigFile 节点提供者 =====

class ConfigFileNodeProvider(NodeProvider):
    """从配置文件读取节点"""
    
    def __init__(self, config_file: str):
        """
        初始化
        
        Args:
            config_file: 节点配置文件路径
        """
        self.config_file = Path(config_file)
    
    async def get_nodes(self) -> List[NodeInfo]:
        """从配置文件读取节点"""
        if not self.config_file.exists():
            logger.warning(f"节点配置文件不存在：{self.config_file}")
            return []
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            nodes_data = data.get("nodes", [])
            nodes = [NodeInfo.from_dict(node) for node in nodes_data]
            
            logger.info(f"从配置文件读取 {len(nodes)} 个节点")
            return nodes
        
        except json.JSONDecodeError as e:
            logger.error(f"节点配置文件解析失败：{e}")
            return []
        except Exception as e:
            logger.error(f"读取节点配置文件失败：{e}")
            return []
    
    def get_provider_name(self) -> str:
        return "ConfigFile"


# ===== Consul 节点提供者 =====

class ConsulNodeProvider(NodeProvider):
    """从 Consul 服务发现获取节点"""
    
    def __init__(
        self,
        consul_host: str = "127.0.0.1",
        consul_port: int = 8500,
        service_name: str = "startops"
    ):
        """
        初始化
        
        Args:
            consul_host: Consul 地址
            consul_port: Consul 端口
            service_name: 服务名称
        """
        self.consul_host = consul_host
        self.consul_port = consul_port
        self.service_name = service_name
        self.base_url = f"http://{consul_host}:{consul_port}"
    
    async def get_nodes(self) -> List[NodeInfo]:
        """从 Consul 获取节点"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # 调用 Consul Catalog API
                url = f"{self.base_url}/v1/catalog/service/{self.service_name}"
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.error(f"Consul API 返回错误：{response.status_code}")
                    return []
                
                services = response.json()
                nodes = []
                
                for svc in services:
                    # 解析节点信息
                    node = NodeInfo(
                        node_id=svc.get("Node", ""),
                        node_name=svc.get("Node", ""),
                        address=svc.get("ServiceAddress") or svc.get("Address", ""),
                        port=svc.get("ServicePort", 8300),
                        status="healthy",  # Consul 返回的默认是健康的
                        is_current=False
                    )
                    nodes.append(node)
                
                logger.info(f"从 Consul 获取 {len(nodes)} 个节点")
                return nodes
        
        except httpx.ConnectError as e:
            logger.error(f"连接 Consul 失败：{e}")
            return []
        except Exception as e:
            logger.error(f"从 Consul 获取节点失败：{e}")
            return []
    
    def get_provider_name(self) -> str:
        return "Consul"


# ===== 节点提供者工厂 =====

class NodeProviderFactory:
    """节点提供者工厂"""
    
    @staticmethod
    def create_provider(
        provider_type: str,
        config_dir: Optional[str] = None,
        consul_config: Optional[Dict[str, Any]] = None
    ) -> NodeProvider:
        """
        创建节点提供者
        
        Args:
            provider_type: 提供者类型 ("Consul" 或 "ConfigFile")
            config_dir: 配置文件目录
            consul_config: Consul 配置
        
        Returns:
            NodeProvider 实例
        """
        if provider_type == "Consul":
            if not consul_config:
                consul_config = {
                    "host": "127.0.0.1",
                    "port": 8500,
                    "service_name": "startops"
                }
            
            return ConsulNodeProvider(
                consul_host=consul_config.get("host", "127.0.0.1"),
                consul_port=consul_config.get("port", 8500),
                service_name=consul_config.get("service_name", "startops")
            )
        
        else:  # 默认 ConfigFile
            if not config_dir:
                config_dir = Path(__file__).parent.parent / "configs"
            else:
                config_dir = Path(config_dir)
            
            config_file = config_dir / "nodes.json"
            return ConfigFileNodeProvider(str(config_file))


# ===== 便捷函数 =====

async def get_nodes(
    provider_type: str,
    config_dir: Optional[str] = None,
    consul_config: Optional[Dict[str, Any]] = None
) -> List[NodeInfo]:
    """
    获取节点列表（便捷函数）
    
    Args:
        provider_type: 提供者类型
        config_dir: 配置文件目录
        consul_config: Consul 配置
    
    Returns:
        节点列表
    """
    provider = NodeProviderFactory.create_provider(
        provider_type,
        config_dir,
        consul_config
    )
    
    return await provider.get_nodes()


def create_default_nodes_config(config_dir: Optional[str] = None) -> Path:
    """
    创建默认节点配置文件
    
    Args:
        config_dir: 配置文件目录
    
    Returns:
        配置文件路径
    """
    if not config_dir:
        config_dir = Path(__file__).parent.parent / "configs"
    else:
        config_dir = Path(config_dir)
    
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "nodes.json"
    
    default_config = {
        "nodes": [
            {
                "node_id": "node-1",
                "node_name": "节点 -1 (北京)",
                "address": "192.168.1.100",
                "port": 8300,
                "status": "healthy",
                "is_current": True
            },
            {
                "node_id": "node-2",
                "node_name": "节点 -2 (上海)",
                "address": "192.168.1.101",
                "port": 8300,
                "status": "healthy",
                "is_current": False
            }
        ]
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    return config_file
