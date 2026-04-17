"""
Startops 日志服务模块
提供日志的创建、格式化、实例化等功能

功能特性:
- 支持日志文件输出
- 按日期分割日志文件
- 日志级别配置
- 日志格式配置
- 日志轮转（可选）
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from typing import Optional


class LoggerService:
    """日志服务类"""
    
    _instance = None
    _loggers = {}
    _logs_dir: Optional[Path] = None
    _log_level: int = logging.INFO
    _log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    _log_enabled: bool = True
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(
        self,
        logs_dir: Optional[str] = None,
        log_level: str = "INFO",
        log_format: Optional[str] = None,
        log_enabled: bool = True
    ):
        """
        初始化日志服务
        
        Args:
            logs_dir: 日志目录路径
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: 日志格式
            log_enabled: 是否启用日志文件
        """
        if logs_dir:
            self._logs_dir = Path(logs_dir)
            self._logs_dir.mkdir(parents=True, exist_ok=True)
        else:
            self._logs_dir = Path(__file__).parent.parent.parent / "logs"
            self._logs_dir.mkdir(exist_ok=True)
        
        # 设置日志级别
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        self._log_level = level_map.get(log_level.upper(), logging.INFO)
        
        # 设置日志格式
        if log_format:
            self._log_format = log_format
        
        # 设置是否启用日志文件
        self._log_enabled = log_enabled
        
        return self
    
    def get_logger(self, name: str, level: Optional[int] = None):
        """
        获取或创建日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别，None 则使用全局配置
            
        Returns:
            Logger: 日志记录器实例
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(level or self._log_level)
        
        # 清除已存在的处理器（避免重复）
        logger.handlers.clear()
        
        # 控制台处理器（始终启用）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level or self._log_level)
        console_formatter = logging.Formatter(
            self._log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器（如果启用）
        if self._log_enabled and self._logs_dir:
            # 按日期分割的日志文件
            log_file = self._logs_dir / f"{name}.log"
            
            # 使用 TimedRotatingFileHandler 实现日志轮转
            file_handler = TimedRotatingFileHandler(
                log_file,
                when='D',  # 按天轮转
                interval=1,
                backupCount=7,  # 保留 7 天的日志
                encoding='utf-8',
                atTime=None,
                utc=False
            )
            file_handler.setLevel(level or self._log_level)
            file_handler.setFormatter(console_formatter)
            file_handler.suffix = "%Y-%m-%d"  # 日期后缀格式
            
            logger.addHandler(file_handler)
        
        self._loggers[name] = logger
        return logger
    
    def get_logs_dir(self) -> Optional[Path]:
        """获取日志目录"""
        return self._logs_dir
    
    def set_log_level(self, level: str):
        """
        设置全局日志级别
        
        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        self._log_level = level_map.get(level.upper(), logging.INFO)
        
        # 更新所有已存在的 logger
        for logger in self._loggers.values():
            logger.setLevel(self._log_level)
            for handler in logger.handlers:
                handler.setLevel(self._log_level)
    
    def close(self):
        """关闭所有日志处理器"""
        for logger in self._loggers.values():
            for handler in logger.handlers:
                handler.close()
        self._loggers.clear()


# 全局日志服务实例
_logger_service: Optional[LoggerService] = None


def initialize_logger(
    logs_dir: Optional[str] = None,
    log_level: str = "INFO",
    log_format: Optional[str] = None,
    log_enabled: bool = True
) -> LoggerService:
    """
    初始化全局日志服务
    
    Args:
        logs_dir: 日志目录路径
        log_level: 日志级别
        log_format: 日志格式
        log_enabled: 是否启用日志文件
    
    Returns:
        LoggerService: 日志服务实例
    """
    global _logger_service
    _logger_service = LoggerService()
    _logger_service.initialize(
        logs_dir=logs_dir,
        log_level=log_level,
        log_format=log_format,
        log_enabled=log_enabled
    )
    return _logger_service


def get_logger(name: str, level: Optional[int] = None):
    """
    快速获取日志记录器的便捷函数
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        Logger: 日志记录器实例
    """
    global _logger_service
    if _logger_service is None:
        # 自动初始化
        _logger_service = LoggerService()
        _logger_service.initialize()
    
    return _logger_service.get_logger(name, level)


def get_logs_dir() -> Optional[Path]:
    """获取日志目录"""
    global _logger_service
    if _logger_service:
        return _logger_service.get_logs_dir()
    return None


def close_logger():
    """关闭所有日志处理器"""
    global _logger_service
    if _logger_service:
        _logger_service.close()
