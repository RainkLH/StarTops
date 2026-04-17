"""
配置加载器测试脚本
测试配置文件的创建、读取、命令行参数覆盖等功能
"""

import sys
import json
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import ConfigLoader, get_config, create_default_config_file


def test_create_default_config():
    """测试创建默认配置文件"""
    print("=" * 60)
    print("测试 1: 创建默认配置文件")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_config"
    test_dir.mkdir(exist_ok=True)
    
    loader = ConfigLoader(config_dir=str(test_dir))
    config_file = loader.create_default_config()
    
    assert config_file.exists(), "配置文件未创建"
    print(f"✓ 配置文件已创建：{config_file}")
    
    # 验证文件内容
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert "server" in data, "缺少 server 配置"
    assert "nodes" in data, "缺少 nodes 配置"
    assert "logs" in data, "缺少 logs 配置"
    assert "terminal" in data, "缺少 terminal 配置"
    print("✓ 配置文件结构正确")
    
    # 清理
    config_file.unlink()
    test_dir.rmdir()
    
    print("✓ 测试 1 通过\n")
    return True


def test_load_config():
    """测试加载配置文件"""
    print("=" * 60)
    print("测试 2: 加载配置文件")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_config"
    test_dir.mkdir(exist_ok=True)
    
    loader = ConfigLoader(config_dir=str(test_dir))
    
    # 加载配置（会自动创建默认配置）
    config = loader.load_config()
    
    assert config is not None, "配置加载失败"
    print("✓ 配置加载成功")
    
    # 验证配置值
    assert config.server.host == "127.0.0.1", f"host 错误：{config.server.host}"
    assert config.server.port == 8300, f"port 错误：{config.server.port}"
    assert config.logs.enabled == True, f"logs.enabled 错误：{config.logs.enabled}"
    assert config.terminal.enabled == True, f"terminal.enabled 错误：{config.terminal.enabled}"
    print("✓ 配置值正确")
    
    # 清理
    loader.config_file.unlink()
    test_dir.rmdir()
    
    print("✓ 测试 2 通过\n")
    return True


def test_command_line_override():
    """测试命令行参数覆盖"""
    print("=" * 60)
    print("测试 3: 命令行参数覆盖")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_config"
    test_dir.mkdir(exist_ok=True)
    
    loader = ConfigLoader(config_dir=str(test_dir))
    config = loader.load_config()
    
    # 应用命令行参数覆盖
    config = loader.apply_command_line_args({
        "host": "0.0.0.0",
        "port": 9000,
        "debug": True
    })
    
    assert config.server.host == "0.0.0.0", f"host 未被覆盖：{config.server.host}"
    assert config.server.port == 9000, f"port 未被覆盖：{config.server.port}"
    assert config.server.debug == True, f"debug 未被覆盖：{config.server.debug}"
    print("✓ 命令行参数覆盖成功")
    
    # 清理
    loader.config_file.unlink()
    test_dir.rmdir()
    
    print("✓ 测试 3 通过\n")
    return True


def test_get_config():
    """测试便捷函数 get_config"""
    print("=" * 60)
    print("测试 4: get_config 便捷函数")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_config"
    test_dir.mkdir(exist_ok=True)
    
    # 使用便捷函数加载配置
    config = get_config(
        config_dir=str(test_dir),
        command_line_args={"host": "192.168.1.100", "port": 8080}
    )
    
    assert config is not None, "配置加载失败"
    assert config.server.host == "192.168.1.100", f"host 错误：{config.server.host}"
    assert config.server.port == 8080, f"port 错误：{config.server.port}"
    print("✓ get_config 函数工作正常")
    
    # 清理
    config_file = Path(test_dir) / "startops.json"
    config_file.unlink()
    test_dir.rmdir()
    
    print("✓ 测试 4 通过\n")
    return True


def test_config_validation():
    """测试配置校验"""
    print("=" * 60)
    print("测试 5: 配置校验")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_config"
    test_dir.mkdir(exist_ok=True)
    
    # 创建无效配置（端口超出范围）
    invalid_config = {
        "server": {
            "host": "127.0.0.1",
            "port": 99999,  # 无效端口
            "debug": False
        },
        "nodes": {"provider": "ConfigFile"},
        "logs": {"enabled": True, "level": "INFO"},
        "terminal": {"enabled": True}
    }
    
    config_file = Path(test_dir) / "startops.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(invalid_config, f, indent=2)
    
    try:
        loader = ConfigLoader(config_dir=str(test_dir))
        config = loader.load_config()
        print("✗ 配置校验失败：应该抛出异常")
        return False
    except Exception as e:
        print(f"✓ 配置校验正确捕获错误：{type(e).__name__}")
    
    # 清理
    config_file.unlink()
    test_dir.rmdir()
    
    print("✓ 测试 5 通过\n")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("StarTops 配置加载器测试")
    print("=" * 60 + "\n")
    
    tests = [
        test_create_default_config,
        test_load_config,
        test_command_line_override,
        test_get_config,
        test_config_validation,
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
            failed += 1
    
    print("=" * 60)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
