"""
Startops 服务页面管理模块
负责各业务服务自身的维护、监控页面（URL）的注册和管理
"""

import json
from pathlib import Path
from typing import Dict, Optional, Any
from src.utils.logger import get_logger

logger = get_logger('server_pages_manager')


class ServerPage:
    """服务页面信息类"""
    
    def __init__(
        self,
        service_name: str,
        page_name: str,
        page_url: str,
        icon: str = "🔧",
        description: str = ""
    ):
        """
        初始化服务页面信息
        
        Args:
            service_name: 所属服务名称
            page_name: 页面显示名称
            page_url: 页面URL
            icon: 页面图标，默认为齿轮
            description: 页面描述
        """
        self.service_name = service_name
        self.page_name = page_name
        self.page_url = page_url
        self.icon = icon
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "service_name": self.service_name,
            "page_name": self.page_name,
            "page_url": self.page_url,
            "icon": self.icon,
            "description": self.description
        }
    
    def key(self) -> str:
        """获取页面唯一键"""
        return f"{self.service_name}:{self.page_name}"


class ServerPagesManager:
    """服务页面管理器"""
    
    def __init__(self):
        """初始化服务页面管理器"""
        self.pages: Dict[str, ServerPage] = {}
        self.service_pages: Dict[str, list] = {}  # service_name -> [page_id]
        self.config_file = Path(__file__).parent.parent / "configs" / "service_pages.json"

    def _save_to_config(self) -> bool:
        """将当前页面信息持久化到配置文件"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            pages_data = [self.pages[key].to_dict() for key in sorted(self.pages.keys())]
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(pages_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save service pages config: {str(e)}")
            return False

    def get_page(self, page_id: str) -> Optional[ServerPage]:
        """根据页面ID获取页面"""
        return self.pages.get(page_id)

    def initialize_service(self) -> 'ServerPagesManager':
        """
        从config/service_pages.json初始化所有服务页面
        
        返回ServerPagesManager对象自身，支持链式调用
        - 如果文件不存在，返回空列表
        - 如果文件解析失败，将文件改名为.json.error并生成新的空文件        
        Returns:
            ServerPagesManager: 返回self以支持链式调用
        """
        config_file = self.config_file
        self.pages.clear()
        self.service_pages.clear()
        
        # 如果文件不存在，创建空配置文件
        if not config_file.exists():
            logger.warning(f"Service pages config file not found: {config_file}")
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return self
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                pages_data = json.load(f)
            
            if not isinstance(pages_data, list):
                raise ValueError("Service pages config must be a list")
            
            # 注册所有页面
            for page_data in pages_data:
                try:
                    self.register_page(
                        service_name=page_data.get("service_name", ""),
                        page_name=page_data.get("page_name", ""),
                        page_url=page_data.get("page_url", ""),
                        icon=page_data.get("icon", "🔧"),
                        description=page_data.get("description", ""),
                        persist=False
                    )
                except Exception as e:
                    logger.error(f"Error registering page from config: {str(e)}")
                    continue
            
            logger.info(f"Loaded {len(self.pages)} service pages from config")
            
        except json.JSONDecodeError as e:
            # JSON解析失败，重命名文件并创建新的空文件
            logger.error(f"Failed to parse service pages config: {str(e)}")
            error_file = config_file.with_suffix('.json.error')
            config_file.rename(error_file)
            logger.info(f"Renamed corrupted file to {error_file}")
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            logger.info(f"Created new empty config file: {config_file}")
            
        except Exception as e:
            logger.error(f"Error initializing service pages: {str(e)}")
        
        return self
    
    def register_page(
        self,
        service_name: str,
        page_name: str,
        page_url: str,
        icon: str = "🔧",
        description: str = "",
        persist: bool = True
    ) -> ServerPage:
        """
        注册一个服务页面
        
        Args:
            service_name: 所属服务名称
            page_name: 页面名称
            page_url: 页面URL
            icon: 页面图标
            description: 页面描述
            
        Returns:
            ServerPage: 已注册的页面对象
        """
        page_id = f"{service_name}:{page_name}"
        if page_id in self.pages:
            logger.warning(f"Page {page_id} already registered")
            return self.pages[page_id]

        page = ServerPage(
            service_name=service_name,
            page_name=page_name,
            page_url=page_url,
            icon=icon,
            description=description
        )

        self.pages[page_id] = page

        # 维护服务页面索引
        if service_name not in self.service_pages:
            self.service_pages[service_name] = []
        self.service_pages[service_name].append(page_id)

        if persist and not self._save_to_config():
            # 保存失败时回滚内存状态
            self.pages.pop(page_id, None)
            if service_name in self.service_pages and page_id in self.service_pages[service_name]:
                self.service_pages[service_name].remove(page_id)
                if not self.service_pages[service_name]:
                    self.service_pages.pop(service_name, None)
            raise RuntimeError("Failed to persist service pages config")
        
        logger.info(f"Page {page.key()} registered for service {service_name}")
        return page
        
    def get_service_pages(self, service_name: str) -> list:
        """
        获取指定服务的所有页面
        
        Args:
            service_name: 服务名称
            
        Returns:
            list: 页面对象列表
        """
        page_ids = self.service_pages.get(service_name, [])
        return [self.pages[pid] for pid in page_ids if pid in self.pages]
    
    def get_all_pages(self) -> Dict[str, ServerPage]:
        """获取所有页面"""
        return self.pages.copy()
    
    def unregister_page(self, service_name: str, page_name: str) -> bool:
        """
        注销一个页面
        
        Args:
            page_id: 页面ID
            
        Returns:
            bool: 是否成功注销
        """
        page_id = f"{service_name}:{page_name}"
        if page_id not in self.pages:
            logger.warning(f"Page {page_id} not found")
            return False
        
        page = self.pages.pop(page_id)
        
        # 从服务页面索引中删除
        if page.service_name in self.service_pages:
            if page_id in self.service_pages[page.service_name]:
                self.service_pages[page.service_name].remove(page_id)
            if not self.service_pages[page.service_name]:
                self.service_pages.pop(page.service_name, None)

        if not self._save_to_config():
            # 保存失败时回滚内存状态
            self.pages[page_id] = page
            if page.service_name not in self.service_pages:
                self.service_pages[page.service_name] = []
            if page_id not in self.service_pages[page.service_name]:
                self.service_pages[page.service_name].append(page_id)
            logger.error(f"Failed to persist config while unregistering {page_id}")
            return False
        
        logger.info(f"Page {page_id} unregistered")
        return True
    
    def update_page_url(self, service_name: str, page_name: str, new_url: str) -> bool:
        """
        更新页面URL
        
        Args:
            page_id: 页面ID
            new_url: 新的URL
            
        Returns:
            bool: 是否成功更新
        """
        page_id = f"{service_name}:{page_name}"
        page = self.get_page(page_id)
        if not page:
            logger.warning(f"Page {page_id} not found")
            return False
        
        old_url = page.page_url
        page.page_url = new_url

        if not self._save_to_config():
            # 保存失败时回滚内存状态
            page.page_url = old_url
            logger.error(f"Failed to persist config while updating page URL: {page_id}")
            return False

        logger.info(f"Page {page_id} URL updated to {new_url}")
        return True
