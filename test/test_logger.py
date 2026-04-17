"""
日志系统测试脚本
测试日志的创建、级别配置、文件输出、轮转等功能
"""

import sys
import os
import time
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import (
    initialize_logger,
    get_logger,
    get_logs_dir,
    close_logger,
    LoggerService
)


def test_initialize_logger():
    """测试日志初始化"""
    print("=" * 60)
    print("测试 1: 日志初始化")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_logs"
    test_dir.mkdir(exist_ok=True)
    
    # 初始化日志
    service = initialize_logger(
        logs_dir=str(test_dir),
        log_level="DEBUG",
        log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        log_enabled=True
    )
    
    assert service is not None
    print("✓ 日志服务初始化成功")
    
    logs_dir = get_logs_dir()
    assert logs_dir == test_dir
    print(f"✓ 日志目录正确：{logs_dir}")
    
    # 清理
    close_logger()
    for f in test_dir.glob("*.log"):
        f.unlink()
    test_dir.rmdir()
    
    print("✓ 测试 1 通过\n")
    return True


def test_get_logger():
    """测试获取日志记录器"""
    print("=" * 60)
    print("测试 2: 获取日志记录器")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_logs"
    test_dir.mkdir(exist_ok=True)
    
    initialize_logger(
        logs_dir=str(test_dir),
        log_level="INFO",
        log_enabled=True
    )
    
    # 获取 logger
    logger = get_logger('test_app')
    assert logger is not None
    print("✓ 获取 logger 成功")
    
    # 测试日志输出
    logger.info("This is an info message")
    logger.debug("This is a debug message")  # 应该被过滤
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("✓ 日志输出成功")
    
    # 检查日志文件
    log_file = test_dir / "test_app.log"
    assert log_file.exists()
    print(f"✓ 日志文件已创建：{log_file}")
    
    # 检查日志内容
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "This is an info message" in content
    assert "This is a warning message" in content
    assert "This is an error message" in content
    assert "This is a debug message" not in content  # DEBUG 级别被过滤
    print("✓ 日志级别过滤正确")
    
    # 清理
    close_logger()
    for f in test_dir.glob("*.log"):
        f.unlink()
    test_dir.rmdir()
    
    print("✓ 测试 2 通过\n")
    return True


def test_log_levels():
    """测试日志级别设置"""
    print("=" * 60)
    print("测试 3: 日志级别设置")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_logs"
    test_dir.mkdir(exist_ok=True)
    
    # 测试 DEBUG 级别
    initialize_logger(
        logs_dir=str(test_dir),
        log_level="DEBUG",
        log_enabled=True
    )
    
    logger1 = get_logger('test_debug')
    logger1.debug("Debug message")
    logger1.info("Info message")
    
    close_logger()
    
    # 检查 DEBUG 日志
    log_file1 = test_dir / "test_debug.log"
    with open(log_file1, 'r', encoding='utf-8') as f:
        content1 = f.read()
    
    assert "Debug message" in content1
    print("✓ DEBUG 级别输出正确")
    
    # 测试 ERROR 级别
    initialize_logger(
        logs_dir=str(test_dir),
        log_level="ERROR",
        log_enabled=True
    )
    
    logger2 = get_logger('test_error')
    logger2.debug("Debug message")
    logger2.info("Info message")
    logger2.error("Error message")
    
    close_logger()
    
    # 检查 ERROR 日志
    log_file2 = test_dir / "test_error.log"
    with open(log_file2, 'r', encoding='utf-8') as f:
        content2 = f.read()
    
    assert "Debug message" not in content2
    assert "Info message" not in content2
    assert "Error message" in content2
    print("✓ ERROR 级别过滤正确")
    
    # 清理
    for f in test_dir.glob("*.log"):
        f.unlink()
    test_dir.rmdir()
    
    print("✓ 测试 3 通过\n")
    return True


def test_log_format():
    """测试日志格式配置"""
    print("=" * 60)
    print("测试 4: 日志格式配置")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_logs"
    test_dir.mkdir(exist_ok=True)
    
    custom_format = "[CUSTOM] %(name)s - %(levelname)s: %(message)s"
    
    initialize_logger(
        logs_dir=str(test_dir),
        log_level="INFO",
        log_format=custom_format,
        log_enabled=True
    )
    
    logger = get_logger('test_format')
    logger.info("Test message")
    
    close_logger()
    
    # 检查日志格式
    log_file = test_dir / "test_format.log"
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "[CUSTOM]" in content
    assert "test_format" in content
    assert "Test message" in content
    print("✓ 自定义日志格式正确")
    
    # 清理
    for f in test_dir.glob("*.log"):
        f.unlink()
    test_dir.rmdir()
    
    print("✓ 测试 4 通过\n")
    return True


def test_log_disabled():
    """测试禁用日志文件"""
    print("=" * 60)
    print("测试 5: 禁用日志文件")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_logs"
    test_dir.mkdir(exist_ok=True)
    
    initialize_logger(
        logs_dir=str(test_dir),
        log_level="INFO",
        log_enabled=False  # 禁用文件日志
    )
    
    logger = get_logger('test_disabled')
    logger.info("This should not be written to file")
    
    close_logger()
    
    # 检查日志文件未创建
    log_file = test_dir / "test_disabled.log"
    assert not log_file.exists()
    print("✓ 禁用文件日志后未创建日志文件")
    
    # 清理
    test_dir.rmdir()
    
    print("✓ 测试 5 通过\n")
    return True


def test_set_log_level():
    """测试动态修改日志级别"""
    print("=" * 60)
    print("测试 6: 动态修改日志级别")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_logs"
    test_dir.mkdir(exist_ok=True)
    
    initialize_logger(
        logs_dir=str(test_dir),
        log_level="ERROR",
        log_enabled=True
    )
    
    logger = get_logger('test_dynamic')
    logger.info("Before level change")  # 应该被过滤
    
    # 动态修改级别
    service = LoggerService()
    service.set_log_level("INFO")
    
    logger.info("After level change")  # 应该输出
    
    close_logger()
    
    # 检查日志内容
    log_file = test_dir / "test_dynamic.log"
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "Before level change" not in content
    assert "After level change" in content
    print("✓ 动态修改日志级别生效")
    
    # 清理
    for f in test_dir.glob("*.log"):
        f.unlink()
    test_dir.rmdir()
    
    print("✓ 测试 6 通过\n")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("StarTops 日志系统测试")
    print("=" * 60 + "\n")
    
    tests = [
        test_initialize_logger,
        test_get_logger,
        test_log_levels,
        test_log_format,
        test_log_disabled,
        test_set_log_level,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ 测试失败：{e}\n")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
