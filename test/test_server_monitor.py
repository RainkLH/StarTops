"""
服务监控管理器测试脚本
测试服务配置初始化、持久化以及失败回滚行为
"""

import sys
import json
import shutil
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.server_monitor import ServerMonitor


def create_test_monitor(test_dir: Path) -> ServerMonitor:
    """创建测试用监控器"""
    monitor = ServerMonitor(check_interval=5)
    monitor.config_file = test_dir / "service_list.json"
    return monitor


def cleanup_test_dir(test_dir: Path):
    """清理测试目录"""
    if test_dir.exists():
        shutil.rmtree(test_dir)


def test_initialize_service_from_config():
    """测试从配置文件初始化服务"""
    print("=" * 60)
    print("测试 1: 从配置文件初始化服务")
    print("=" * 60)

    test_dir = Path(__file__).parent / "test_server_monitor"
    cleanup_test_dir(test_dir)
    test_dir.mkdir(exist_ok=True)

    config_file = test_dir / "service_list.json"
    config_data = [
        {
            "name": "svc1",
            "url": "http://127.0.0.1:9001",
            "health_check_interval": 30,
            "health_check_url": "",
            "executor": "python",
            "app_dir": "",
            "app_file_name": "",
            "app_args": "",
            "start_cmd": "",
            "stop_cmd": "",
            "description": "服务 1",
            "keep_alive": True,
            "start_timeout": 45,
            "stop_timeout": 45
        }
    ]
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

    monitor = create_test_monitor(test_dir)
    monitor.initialize_service()

    assert len(monitor.get_all_services()) == 1, f"服务数量错误：{len(monitor.get_all_services())}"
    assert monitor.get_service("svc1") is not None, "服务未加载到内存"
    print("✓ 初始化成功，服务数据已加载到内存")

    cleanup_test_dir(test_dir)
    print("✓ 测试 1 通过\n")
    return True


def test_register_service_persists_config():
    """测试注册服务时写回配置文件"""
    print("=" * 60)
    print("测试 2: 注册服务写回配置文件")
    print("=" * 60)

    test_dir = Path(__file__).parent / "test_server_monitor"
    cleanup_test_dir(test_dir)
    test_dir.mkdir(exist_ok=True)

    monitor = create_test_monitor(test_dir)
    monitor.initialize_service()
    service = monitor.register_service(
        name="svc_register",
        url="http://127.0.0.1:9100",
        health_check_url="http://127.0.0.1:9100/health",
        description="注册测试",
        keep_alive=False,
        start_timeout=30,
        stop_timeout=30
    )

    with open(monitor.config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert service.name == "svc_register"
    assert len(data) == 1, f"配置文件服务数量错误：{len(data)}"
    assert data[0]["name"] == "svc_register"
    assert data[0]["health_check_url"] == "http://127.0.0.1:9100/health"
    print("✓ 注册服务后已同步写回配置文件")

    cleanup_test_dir(test_dir)
    print("✓ 测试 2 通过\n")
    return True


def test_unregister_service_persists_config():
    """测试注销服务时写回配置文件"""
    print("=" * 60)
    print("测试 3: 注销服务写回配置文件")
    print("=" * 60)

    test_dir = Path(__file__).parent / "test_server_monitor"
    cleanup_test_dir(test_dir)
    test_dir.mkdir(exist_ok=True)

    monitor = create_test_monitor(test_dir)
    monitor.initialize_service()
    monitor.register_service(
        name="svc_unregister",
        url="http://127.0.0.1:9200",
        health_check_url="http://127.0.0.1:9200/health"
    )

    result = monitor.unregister_service("svc_unregister")
    with open(monitor.config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert result == True, "注销服务失败"
    assert len(data) == 0, f"注销后配置文件未清空：{len(data)}"
    assert monitor.get_service("svc_unregister") is None, "内存服务未删除"
    print("✓ 注销服务后已同步更新配置文件")

    cleanup_test_dir(test_dir)
    print("✓ 测试 3 通过\n")
    return True


def test_register_service_rollback_on_save_failure():
    """测试注册服务保存失败时回滚内存状态"""
    print("=" * 60)
    print("测试 4: 注册服务保存失败回滚")
    print("=" * 60)

    test_dir = Path(__file__).parent / "test_server_monitor"
    cleanup_test_dir(test_dir)
    test_dir.mkdir(exist_ok=True)

    monitor = create_test_monitor(test_dir)
    monitor.initialize_service()
    monitor._save_to_config = lambda: False

    try:
        monitor.register_service(
            name="svc_fail",
            url="http://127.0.0.1:9300",
            health_check_url="http://127.0.0.1:9300/health"
        )
        print("✗ 注册服务应该抛出异常")
        cleanup_test_dir(test_dir)
        return False
    except RuntimeError:
        pass

    assert monitor.get_service("svc_fail") is None, "保存失败后内存未回滚"
    print("✓ 注册服务保存失败时已正确回滚内存")

    cleanup_test_dir(test_dir)
    print("✓ 测试 4 通过\n")
    return True


def test_unregister_service_rollback_on_save_failure():
    """测试注销服务保存失败时回滚内存状态"""
    print("=" * 60)
    print("测试 5: 注销服务保存失败回滚")
    print("=" * 60)

    test_dir = Path(__file__).parent / "test_server_monitor"
    cleanup_test_dir(test_dir)
    test_dir.mkdir(exist_ok=True)

    monitor = create_test_monitor(test_dir)
    monitor.initialize_service()
    monitor.register_service(
        name="svc_rollback",
        url="http://127.0.0.1:9400",
        health_check_url="http://127.0.0.1:9400/health"
    )
    monitor._save_to_config = lambda: False

    result = monitor.unregister_service("svc_rollback")
    assert result == False, "注销失败时应返回 False"
    assert monitor.get_service("svc_rollback") is not None, "注销失败后内存未回滚"
    print("✓ 注销服务保存失败时已正确回滚内存")

    cleanup_test_dir(test_dir)
    print("✓ 测试 5 通过\n")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("StarTops 服务监控管理器测试")
    print("=" * 60 + "\n")

    tests = [
        test_initialize_service_from_config,
        test_register_service_persists_config,
        test_unregister_service_persists_config,
        test_register_service_rollback_on_save_failure,
        test_unregister_service_rollback_on_save_failure,
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