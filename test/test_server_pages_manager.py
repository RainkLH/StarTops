"""
服务页面管理器测试脚本
测试页面配置初始化、持久化以及失败回滚行为
"""

import sys
import json
import shutil
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.server_pages_manager import ServerPagesManager


def create_test_manager(test_dir: Path) -> ServerPagesManager:
    """创建测试用管理器"""
    manager = ServerPagesManager()
    manager.config_file = test_dir / "service_pages.json"
    return manager


def cleanup_test_dir(test_dir: Path):
    """清理测试目录"""
    if test_dir.exists():
        shutil.rmtree(test_dir)


def test_initialize_service_from_config():
    """测试从配置文件初始化页面"""
    print("=" * 60)
    print("测试 1: 从配置文件初始化页面")
    print("=" * 60)

    test_dir = Path(__file__).parent / "test_pages_manager"
    cleanup_test_dir(test_dir)
    test_dir.mkdir(exist_ok=True)

    config_file = test_dir / "service_pages.json"
    config_data = [
        {
            "service_name": "svc1",
            "page_name": "监控页",
            "page_url": "http://127.0.0.1:9001/dashboard",
            "icon": "📊",
            "description": "服务 1 页面"
        },
        {
            "service_name": "svc2",
            "page_name": "管理页",
            "page_url": "http://127.0.0.1:9002/admin",
            "icon": "⚙",
            "description": "服务 2 页面"
        }
    ]
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

    manager = create_test_manager(test_dir)
    manager.initialize_service()

    assert len(manager.get_all_pages()) == 2, f"页面数量错误：{len(manager.get_all_pages())}"
    svc1_pages = manager.get_service_pages("svc1")
    assert len(svc1_pages) == 1, f"svc1 页面数量错误：{len(svc1_pages)}"
    assert svc1_pages[0].page_url == "http://127.0.0.1:9001/dashboard"
    print("✓ 初始化成功，页面数据已加载到内存")

    cleanup_test_dir(test_dir)
    print("✓ 测试 1 通过\n")
    return True


def test_register_page_persists_config():
    """测试注册页面时写回配置文件"""
    print("=" * 60)
    print("测试 2: 注册页面写回配置文件")
    print("=" * 60)

    test_dir = Path(__file__).parent / "test_pages_manager"
    cleanup_test_dir(test_dir)
    test_dir.mkdir(exist_ok=True)

    manager = create_test_manager(test_dir)
    manager.initialize_service()
    page = manager.register_page(
        service_name="svc_register",
        page_name="测试页",
        page_url="http://127.0.0.1:9100/page",
        icon="T",
        description="注册测试"
    )

    with open(manager.config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert page.page_name == "测试页"
    assert len(data) == 1, f"配置文件页面数量错误：{len(data)}"
    assert data[0]["service_name"] == "svc_register"
    assert data[0]["page_url"] == "http://127.0.0.1:9100/page"
    print("✓ 注册页面后已同步写回配置文件")

    cleanup_test_dir(test_dir)
    print("✓ 测试 2 通过\n")
    return True


def test_unregister_page_persists_config():
    """测试注销页面时写回配置文件"""
    print("=" * 60)
    print("测试 3: 注销页面写回配置文件")
    print("=" * 60)

    test_dir = Path(__file__).parent / "test_pages_manager"
    cleanup_test_dir(test_dir)
    test_dir.mkdir(exist_ok=True)

    manager = create_test_manager(test_dir)
    manager.initialize_service()
    manager.register_page("svc_unregister", "测试页", "http://127.0.0.1:9200/page")

    result = manager.unregister_page("svc_unregister", "测试页")
    with open(manager.config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert result == True, "注销页面失败"
    assert len(data) == 0, f"注销后配置文件未清空：{len(data)}"
    assert len(manager.get_all_pages()) == 0, f"内存页面未删除：{len(manager.get_all_pages())}"
    print("✓ 注销页面后已同步更新配置文件")

    cleanup_test_dir(test_dir)
    print("✓ 测试 3 通过\n")
    return True


def test_update_page_url_persists_config():
    """测试更新页面 URL 时写回配置文件"""
    print("=" * 60)
    print("测试 4: 更新页面 URL 写回配置文件")
    print("=" * 60)

    test_dir = Path(__file__).parent / "test_pages_manager"
    cleanup_test_dir(test_dir)
    test_dir.mkdir(exist_ok=True)

    manager = create_test_manager(test_dir)
    manager.initialize_service()
    manager.register_page("svc_update", "测试页", "http://127.0.0.1:9300/old")

    result = manager.update_page_url("svc_update", "测试页", "http://127.0.0.1:9300/new")
    with open(manager.config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert result == True, "更新页面 URL 失败"
    assert data[0]["page_url"] == "http://127.0.0.1:9300/new"
    assert manager.get_page("svc_update:测试页").page_url == "http://127.0.0.1:9300/new"
    print("✓ 更新页面 URL 后已同步写回配置文件")

    cleanup_test_dir(test_dir)
    print("✓ 测试 4 通过\n")
    return True


def test_register_page_rollback_on_save_failure():
    """测试注册页面保存失败时回滚内存状态"""
    print("=" * 60)
    print("测试 5: 注册页面保存失败回滚")
    print("=" * 60)

    test_dir = Path(__file__).parent / "test_pages_manager"
    cleanup_test_dir(test_dir)
    test_dir.mkdir(exist_ok=True)

    manager = create_test_manager(test_dir)
    manager.initialize_service()
    manager._save_to_config = lambda: False

    try:
        manager.register_page("svc_fail", "失败页", "http://127.0.0.1:9400/page")
        print("✗ 注册页面应该抛出异常")
        cleanup_test_dir(test_dir)
        return False
    except RuntimeError:
        pass

    assert "svc_fail:失败页" not in manager.get_all_pages(), "保存失败后内存未回滚"
    assert manager.get_service_pages("svc_fail") == [], "保存失败后索引未回滚"
    print("✓ 注册页面保存失败时已正确回滚内存")

    cleanup_test_dir(test_dir)
    print("✓ 测试 5 通过\n")
    return True


def test_unregister_and_update_rollback_on_save_failure():
    """测试注销和更新保存失败时回滚状态"""
    print("=" * 60)
    print("测试 6: 注销和更新保存失败回滚")
    print("=" * 60)

    test_dir = Path(__file__).parent / "test_pages_manager"
    cleanup_test_dir(test_dir)
    test_dir.mkdir(exist_ok=True)

    manager = create_test_manager(test_dir)
    manager.initialize_service()
    manager.register_page("svc_rollback", "测试页", "http://127.0.0.1:9500/original")

    manager._save_to_config = lambda: False

    update_result = manager.update_page_url("svc_rollback", "测试页", "http://127.0.0.1:9500/new")
    assert update_result == False, "更新失败时应返回 False"
    assert manager.get_page("svc_rollback:测试页").page_url == "http://127.0.0.1:9500/original", "更新失败后 URL 未回滚"

    unregister_result = manager.unregister_page("svc_rollback", "测试页")
    assert unregister_result == False, "注销失败时应返回 False"
    assert manager.get_page("svc_rollback:测试页") is not None, "注销失败后页面未回滚"
    assert len(manager.get_service_pages("svc_rollback")) == 1, "注销失败后索引未回滚"
    print("✓ 注销和更新保存失败时已正确回滚")

    cleanup_test_dir(test_dir)
    print("✓ 测试 6 通过\n")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("StarTops 服务页面管理器测试")
    print("=" * 60 + "\n")

    tests = [
        test_initialize_service_from_config,
        test_register_page_persists_config,
        test_unregister_page_persists_config,
        test_update_page_url_persists_config,
        test_register_page_rollback_on_save_failure,
        test_unregister_and_update_rollback_on_save_failure,
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