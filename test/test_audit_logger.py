"""
操作审计日志测试脚本
"""

import sys
import os
import shutil
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.audit_logger import AuditLogger, initialize_audit_logger, get_audit_logger, log_audit


def test_audit_logger_init():
    """测试审计日志器初始化"""
    print("=" * 60)
    print("测试 1: 审计日志器初始化")
    print("=" * 60)
    
    test_dir = Path(__file__).parent / "test_audit"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    audit = AuditLogger(str(test_dir))
    
    assert audit.logs_dir.exists()
    print(f"✓ 日志目录创建：{audit.logs_dir}")
    
    assert audit.log_file.parent.exists()
    print(f"✓ 日志文件路径：{audit.log_file}")
    
    # 清理
    shutil.rmtree(test_dir)
    
    print("✓ 测试 1 通过\n")
    return True


def test_log_service_action():
    """测试记录服务操作"""
    print("=" * 60)
    print("测试 2: 记录服务操作")
    print("=" * 60)
    
    test_dir = Path(__file__).parent / "test_audit"
    audit = AuditLogger(str(test_dir))
    
    # 记录服务启动
    audit.log_service_action(
        service_name="ai_service",
        action="start",
        status="success",
        details={"pid": 1234}
    )
    
    # 记录服务停止
    audit.log_service_action(
        service_name="ai_service",
        action="stop",
        status="success"
    )
    
    # 验证日志
    logs = audit.get_logs()
    assert len(logs) == 2
    assert logs[0]["action"] == "start"
    assert logs[1]["action"] == "stop"
    print(f"✓ 记录 {len(logs)} 条服务操作日志")
    
    # 清理
    shutil.rmtree(test_dir)
    
    print("✓ 测试 2 通过\n")
    return True


def test_log_config_change():
    """测试记录配置变更"""
    print("=" * 60)
    print("测试 3: 记录配置变更")
    print("=" * 60)
    
    test_dir = Path(__file__).parent / "test_audit"
    audit = AuditLogger(str(test_dir))
    
    audit.log_config_change(
        config_name="app_config",
        changes={"port": 8080, "debug": True}
    )
    
    logs = audit.get_logs()
    assert len(logs) == 1
    assert logs[0]["action"] == "update"
    assert logs[0]["resource_type"] == "config"
    print(f"✓ 记录配置变更：{logs[0]['details']}")
    
    # 清理
    shutil.rmtree(test_dir)
    
    print("✓ 测试 3 通过\n")
    return True


def test_log_terminal_command():
    """测试记录终端命令"""
    print("=" * 60)
    print("测试 4: 记录终端命令")
    print("=" * 60)
    
    test_dir = Path(__file__).parent / "test_audit"
    audit = AuditLogger(str(test_dir))
    
    # 正常命令
    audit.log_terminal_command(
        command="ls -la",
        status="success",
        blocked=False
    )
    
    # 被拦截的命令
    audit.log_terminal_command(
        command="rm -rf /",
        status="denied",
        blocked=True
    )
    
    logs = audit.get_logs()
    assert len(logs) == 2
    assert logs[0]["details"]["blocked"] == False
    assert logs[1]["details"]["blocked"] == True
    print(f"✓ 记录 {len(logs)} 条终端命令日志")
    
    # 清理
    shutil.rmtree(test_dir)
    
    print("✓ 测试 4 通过\n")
    return True


def test_global_audit_logger():
    """测试全局审计日志器"""
    print("=" * 60)
    print("测试 5: 全局审计日志器")
    print("=" * 60)
    
    test_dir = Path(__file__).parent / "test_audit"
    
    # 初始化全局日志器
    initialize_audit_logger(str(test_dir))
    
    audit = get_audit_logger()
    assert audit is not None
    print("✓ 获取全局审计日志器成功")
    
    # 使用便捷函数
    log_audit(
        action="test",
        resource_type="test",
        resource_name="test_resource",
        status="success"
    )
    
    logs = audit.get_logs()
    assert len(logs) == 1
    print(f"✓ 便捷函数记录成功：{len(logs)} 条")
    
    # 清理
    shutil.rmtree(test_dir)
    
    print("✓ 测试 5 通过\n")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("StarTops 操作审计日志测试")
    print("=" * 60 + "\n")
    
    tests = [
        test_audit_logger_init,
        test_log_service_action,
        test_log_config_change,
        test_log_terminal_command,
        test_global_audit_logger,
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
