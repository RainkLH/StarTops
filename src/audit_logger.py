"""
StarTops 操作审计日志模块
记录关键操作日志，用于审计和追溯

功能特性:
- 服务启停操作记录
- 配置修改操作记录
- 终端命令执行记录
- 文件存储，支持轮转
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.utils.logger import get_logger

logger = get_logger('audit')


class AuditLogger:
    """审计日志器"""
    
    def __init__(self, logs_dir: str, max_age_days: int = 30):
        """
        初始化
        
        Args:
            logs_dir: 日志目录
            max_age_days: 日志保留天数
        """
        self.logs_dir = Path(logs_dir) / "audit"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_days = max_age_days
        
        # 审计日志文件（按日期分割）
        self.log_file = self.logs_dir / f"audit_{datetime.now().strftime('%Y-%m-%d')}.log"
        
        # 配置审计日志处理器
        self._setup_logger()
    
    def _setup_logger(self):
        """配置审计日志处理器"""
        self.audit_logger = logging.getLogger('audit')
        self.audit_logger.setLevel(logging.INFO)
        
        # 清除已有处理器
        self.audit_logger.handlers.clear()
        
        # 文件处理器
        handler = logging.FileHandler(self.log_file, encoding='utf-8')
        handler.setLevel(logging.INFO)
        
        # 简洁格式（JSON 每行一条）
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        
        self.audit_logger.addHandler(handler)
    
    def log(
        self,
        action: str,
        resource_type: str,
        resource_name: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None
    ):
        """
        记录审计日志
        
        Args:
            action: 操作类型 (create, update, delete, start, stop, restart, execute)
            resource_type: 资源类型 (service, config, terminal, node)
            resource_name: 资源名称
            status: 操作状态 (success, failure, denied)
            details: 详细信息
            user: 操作用户（可选）
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "resource_type": resource_type,
            "resource_name": resource_name,
            "status": status,
            "details": details or {},
            "user": user or "system"
        }
        
        self.audit_logger.info(json.dumps(entry, ensure_ascii=False))
    
    def log_service_action(
        self,
        service_name: str,
        action: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """记录服务操作日志"""
        self.log(
            action=action,
            resource_type="service",
            resource_name=service_name,
            status=status,
            details=details
        )
    
    def log_config_change(
        self,
        config_name: str,
        changes: Dict[str, Any],
        status: str = "success"
    ):
        """记录配置变更日志"""
        self.log(
            action="update",
            resource_type="config",
            resource_name=config_name,
            status=status,
            details={"changes": changes}
        )
    
    def log_terminal_command(
        self,
        command: str,
        status: str,
        blocked: bool = False
    ):
        """记录终端命令执行日志"""
        action = "execute"
        if blocked:
            status = "denied"
        
        self.log(
            action=action,
            resource_type="terminal",
            resource_name="web_terminal",
            status=status,
            details={"command": command, "blocked": blocked}
        )
    
    def log_node_action(
        self,
        node_name: str,
        action: str,
        status: str
    ):
        """记录节点操作日志"""
        self.log(
            action=action,
            resource_type="node",
            resource_name=node_name,
            status=status
        )
    
    def get_logs(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        读取审计日志
        
        Args:
            date: 日期（YYYY-MM-DD），None 表示今天
        
        Returns:
            日志条目列表
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        log_file = self.logs_dir / f"audit_{date}.log"
        
        if not log_file.exists():
            return []
        
        logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    logs.append(json.loads(line.strip()))
                except:
                    continue
        
        return logs
    
    def cleanup_old_logs(self):
        """清理过期日志"""
        import os
        import time
        
        cutoff = time.time() - (self.max_age_days * 24 * 60 * 60)
        
        for log_file in self.logs_dir.glob("audit_*.log"):
            if log_file.stat().st_mtime < cutoff:
                try:
                    log_file.unlink()
                    logger.info(f"Deleted old audit log: {log_file}")
                except Exception as e:
                    logger.error(f"Failed to delete audit log: {e}")


# 全局审计日志器实例
_audit_logger: Optional[AuditLogger] = None


def initialize_audit_logger(logs_dir: str) -> AuditLogger:
    """初始化全局审计日志器"""
    global _audit_logger
    _audit_logger = AuditLogger(logs_dir)
    return _audit_logger


def get_audit_logger() -> Optional[AuditLogger]:
    """获取全局审计日志器"""
    return _audit_logger


def log_audit(*args, **kwargs):
    """便捷函数：记录审计日志"""
    if _audit_logger:
        _audit_logger.log(*args, **kwargs)
