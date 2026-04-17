"""
节点提供者测试脚本
测试 ConfigFile 和 Consul 两种节点获取方式
"""

import sys
import json
import asyncio
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.node_provider import (
    NodeInfo,
    ConfigFileNodeProvider,
    ConsulNodeProvider,
    NodeProviderFactory,
    get_nodes,
    create_default_nodes_config
)


def test_node_info():
    """测试 NodeInfo 数据模型"""
    print("=" * 60)
    print("测试 1: NodeInfo 数据模型")
    print("=" * 60)
    
    node = NodeInfo(
        node_id="node-1",
        node_name="测试节点",
        address="192.168.1.100",
        port=8300,
        status="healthy",
        is_current=True
    )
    
    # 测试 to_dict
    node_dict = node.to_dict()
    assert node_dict["node_id"] == "node-1"
    assert node_dict["node_name"] == "测试节点"
    assert node_dict["address"] == "192.168.1.100"
    assert node_dict["port"] == 8300
    assert node_dict["status"] == "healthy"
    assert node_dict["is_current"] == True
    print("✓ to_dict 正确")
    
    # 测试 from_dict
    node2 = NodeInfo.from_dict(node_dict)
    assert node2.node_id == node.node_id
    assert node2.node_name == node.node_name
    assert node2.address == node.address
    print("✓ from_dict 正确")
    
    print("✓ 测试 1 通过\n")
    return True


async def test_config_file_provider():
    """测试 ConfigFile 节点提供者"""
    print("=" * 60)
    print("测试 2: ConfigFile 节点提供者")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_nodes"
    test_dir.mkdir(exist_ok=True)
    
    # 创建测试节点配置文件
    config_file = test_dir / "nodes.json"
    test_data = {
        "nodes": [
            {
                "node_id": "node-1",
                "node_name": "测试节点 1",
                "address": "192.168.1.100",
                "port": 8300,
                "status": "healthy"
            },
            {
                "node_id": "node-2",
                "node_name": "测试节点 2",
                "address": "192.168.1.101",
                "port": 8301,
                "status": "warning"
            }
        ]
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    # 测试读取
    provider = ConfigFileNodeProvider(str(config_file))
    nodes = await provider.get_nodes()
    
    assert len(nodes) == 2, f"节点数量错误：{len(nodes)}"
    assert nodes[0].node_name == "测试节点 1"
    assert nodes[1].port == 8301
    print(f"✓ 成功读取 {len(nodes)} 个节点")
    
    # 测试文件不存在
    provider2 = ConfigFileNodeProvider(str(test_dir / "not_exist.json"))
    nodes2 = await provider2.get_nodes()
    assert len(nodes2) == 0
    print("✓ 文件不存在时返回空列表")
    
    # 清理
    config_file.unlink()
    test_dir.rmdir()
    
    print("✓ 测试 2 通过\n")
    return True


def test_create_default_nodes_config():
    """测试创建默认节点配置"""
    print("=" * 60)
    print("测试 3: 创建默认节点配置")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_nodes"
    test_dir.mkdir(exist_ok=True)
    
    # 创建默认配置
    config_file = create_default_nodes_config(str(test_dir))
    
    assert config_file.exists(), "配置文件未创建"
    print(f"✓ 配置文件已创建：{config_file}")
    
    # 验证内容
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert "nodes" in data
    assert len(data["nodes"]) > 0
    print(f"✓ 配置文件包含 {len(data['nodes'])} 个节点")
    
    # 清理
    config_file.unlink()
    test_dir.rmdir()
    
    print("✓ 测试 3 通过\n")
    return True


def test_node_provider_factory():
    """测试节点提供者工厂"""
    print("=" * 60)
    print("测试 4: 节点提供者工厂")
    print("=" * 60)
    
    # 测试 ConfigFile 提供者
    provider1 = NodeProviderFactory.create_provider("ConfigFile")
    assert isinstance(provider1, ConfigFileNodeProvider)
    assert provider1.get_provider_name() == "ConfigFile"
    print("✓ ConfigFile 提供者创建成功")
    
    # 测试 Consul 提供者
    provider2 = NodeProviderFactory.create_provider(
        "Consul",
        consul_config={"host": "127.0.0.1", "port": 8500, "service_name": "test"}
    )
    assert isinstance(provider2, ConsulNodeProvider)
    assert provider2.get_provider_name() == "Consul"
    print("✓ Consul 提供者创建成功")
    
    # 测试默认提供者
    provider3 = NodeProviderFactory.create_provider("Unknown")
    assert isinstance(provider3, ConfigFileNodeProvider)
    print("✓ 未知类型默认使用 ConfigFile")
    
    print("✓ 测试 4 通过\n")
    return True


async def test_get_nodes_async():
    """测试便捷函数 get_nodes"""
    print("=" * 60)
    print("测试 5: get_nodes 便捷函数")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = Path(__file__).parent / "test_nodes"
    test_dir.mkdir(exist_ok=True)
    
    # 创建测试配置
    config_file = test_dir / "nodes.json"
    test_data = {
        "nodes": [
            {"node_id": "1", "node_name": "节点 1", "address": "1.1.1.1", "port": 80}
        ]
    }
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f)
    
    # 测试 ConfigFile 模式
    nodes = await get_nodes(
        provider_type="ConfigFile",
        config_dir=str(test_dir)
    )
    
    assert len(nodes) == 1
    assert nodes[0].address == "1.1.1.1"
    print("✓ ConfigFile 模式获取成功")
    
    # 测试 Consul 模式（应该返回空列表，因为没有 Consul 服务）
    nodes2 = await get_nodes(
        provider_type="Consul",
        consul_config={"host": "127.0.0.1", "port": 8500}
    )
    # Consul 不可用时返回空列表
    print(f"✓ Consul 模式返回 {len(nodes2)} 个节点（无 Consul 服务）")
    
    # 清理
    config_file.unlink()
    test_dir.rmdir()
    
    print("✓ 测试 5 通过\n")
    return True


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("StarTops 节点提供者测试")
    print("=" * 60 + "\n")
    
    tests = [
        ("NodeInfo 数据模型", test_node_info, False),
        ("ConfigFile 节点提供者", test_config_file_provider, True),
        ("创建默认节点配置", test_create_default_nodes_config, False),
        ("节点提供者工厂", test_node_provider_factory, False),
        ("get_nodes 便捷函数", test_get_nodes_async, True),
    ]
    
    passed = 0
    failed = 0
    
    for name, test, is_async in tests:
        try:
            if is_async:
                result = await test()
            else:
                result = test()
            
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {name} 测试失败：{e}\n")
            failed += 1
    
    print("=" * 60)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
