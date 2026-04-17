"""
Consul 集成测试脚本
测试 Consul 节点提供者的功能
"""

import sys
import asyncio
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.node_provider import ConsulNodeProvider, ConfigFileNodeProvider, NodeProviderFactory


async def test_consul_provider_connection():
    """测试 Consul 连接（无 Consul 环境时应该返回空列表）"""
    print("=" * 60)
    print("测试 1: Consul 连接测试")
    print("=" * 60)
    
    provider = ConsulNodeProvider(
        consul_host="127.0.0.1",
        consul_port=8500,
        service_name="startops"
    )
    
    nodes = await provider.get_nodes()
    
    # 无 Consul 环境时返回空列表
    print(f"✓ 获取节点：{len(nodes)} 个")
    print(f"✓ Provider 名称：{provider.get_provider_name()}")
    
    print("✓ 测试 1 通过\n")
    return True


async def test_consul_with_custom_config():
    """测试自定义 Consul 配置"""
    print("=" * 60)
    print("测试 2: 自定义 Consul 配置")
    print("=" * 60)
    
    provider = ConsulNodeProvider(
        consul_host="192.168.1.100",
        consul_port=8600,
        service_name="my-service"
    )
    
    assert provider.consul_host == "192.168.1.100"
    assert provider.consul_port == 8600
    assert provider.service_name == "my-service"
    print("✓ Consul 配置正确")
    
    nodes = await provider.get_nodes()
    print(f"✓ 获取节点：{len(nodes)} 个")
    
    print("✓ 测试 2 通过\n")
    return True


def test_factory_create_consul():
    """测试工厂创建 Consul 提供者"""
    print("=" * 60)
    print("测试 3: 工厂创建 Consul 提供者")
    print("=" * 60)
    
    provider = NodeProviderFactory.create_provider(
        provider_type="Consul",
        consul_config={
            "host": "127.0.0.1",
            "port": 8500,
            "service_name": "test"
        }
    )
    
    assert isinstance(provider, ConsulNodeProvider)
    assert provider.get_provider_name() == "Consul"
    print("✓ 工厂创建 Consul 提供者成功")
    
    print("✓ 测试 3 通过\n")
    return True


def test_factory_create_configfile():
    """测试工厂创建 ConfigFile 提供者"""
    print("=" * 60)
    print("测试 4: 工厂创建 ConfigFile 提供者")
    print("=" * 60)
    
    provider = NodeProviderFactory.create_provider(
        provider_type="ConfigFile"
    )
    
    assert isinstance(provider, ConfigFileNodeProvider)
    assert provider.get_provider_name() == "ConfigFile"
    print("✓ 工厂创建 ConfigFile 提供者成功")
    
    print("✓ 测试 4 通过\n")
    return True


async def test_consul_error_handling():
    """测试 Consul 错误处理"""
    print("=" * 60)
    print("测试 5: Consul 错误处理")
    print("=" * 60)
    
    # 测试无效地址
    provider = ConsulNodeProvider(
        consul_host="invalid-host",
        consul_port=8500,
        service_name="startops"
    )
    
    nodes = await provider.get_nodes()
    assert nodes == []
    print("✓ 无效地址返回空列表")
    
    # 测试超时
    provider = ConsulNodeProvider(
        consul_host="192.0.2.1",  # 测试保留地址
        consul_port=8500,
        service_name="startops"
    )
    
    nodes = await provider.get_nodes()
    assert nodes == []
    print("✓ 连接超时返回空列表")
    
    print("✓ 测试 5 通过\n")
    return True


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("StarTops Consul 集成测试")
    print("=" * 60 + "\n")
    
    tests = [
        ("Consul 连接测试", test_consul_provider_connection),
        ("自定义 Consul 配置", test_consul_with_custom_config),
        ("工厂创建 Consul 提供者", test_factory_create_consul),
        ("工厂创建 ConfigFile 提供者", test_factory_create_configfile),
        ("Consul 错误处理", test_consul_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for name, test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()
            
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {name} 测试失败：{e}\n")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
