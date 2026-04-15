"""
可视化注册功能测试脚本
测试服务、配置、页面的可视化注册功能
"""

import sys
import requests
from pathlib import Path

# StarTops API 地址
STARTOPS_BASE = "http://127.0.0.1:8300"

def test_register_service():
    """测试 1: 注册服务"""
    print("=" * 60)
    print("测试 1: 服务注册")
    print("=" * 60)
    
    service_data = {
        "name": "test_service_api",
        "url": "http://127.0.0.1:9999",
        "health_check_url": "http://127.0.0.1:9999/health",
        "executor": "python3",
        "app_dir": "/data/code/test_service",
        "app_file_name": "main.py",
        "app_args": "",
        "start_cmd": "",
        "stop_cmd": "",
        "description": "通过 API 注册的测试服务",
        "keep_alive": False,
        "health_check_interval": 30,
        "start_timeout": 45,
        "stop_timeout": 45
    }
    
    try:
        resp = requests.post(
            f"{STARTOPS_BASE}/api/service/register",
            json=service_data,
            timeout=5
        )
        resp.raise_for_status()
        
        data = resp.json()
        if data.get("success"):
            print(f"✓ 服务注册成功")
            print(f"✓ 服务名：{data['service']['name']}")
            print(f"✓ URL: {data['service']['url']}")
            return True
        else:
            print(f"✗ 服务注册失败：{data.get('message')}")
            return False
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        return False

def test_register_config():
    """测试 2: 注册配置"""
    print("\n" + "=" * 60)
    print("测试 2: 配置注册")
    print("=" * 60)
    
    config_data = {
        "config_id": "test_config_api",
        "service_name": "test_service_api",
        "config_name": "测试配置文件",
        "config_file_path": "/data/code/star-tops/mock/test_config.json",
        "meta_file_path": "/data/code/star-tops/mock/test_config.meta.json",
        "description": "通过 API 注册的测试配置"
    }
    
    try:
        resp = requests.post(
            f"{STARTOPS_BASE}/api/config/register",
            json=config_data,
            timeout=5
        )
        resp.raise_for_status()
        
        data = resp.json()
        if data.get("success"):
            print(f"✓ 配置注册成功")
            print(f"✓ 配置 ID: {data['config']['config_id']}")
            print(f"✓ 配置名：{data['config']['config_name']}")
            return True
        else:
            print(f"✗ 配置注册失败：{data.get('message')}")
            return False
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        return False

def test_register_page():
    """测试 3: 注册页面"""
    print("\n" + "=" * 60)
    print("测试 3: 页面注册")
    print("=" * 60)
    
    page_data = {
        "service_name": "test_service_api",
        "page_name": "测试页面",
        "page_url": "http://127.0.0.1:9999/dashboard",
        "icon": "🧪",
        "description": "通过 API 注册的测试页面"
    }
    
    try:
        resp = requests.post(
            f"{STARTOPS_BASE}/api/page/register",
            json=page_data,
            timeout=5
        )
        resp.raise_for_status()
        
        data = resp.json()
        if data.get("success"):
            print(f"✓ 页面注册成功")
            print(f"✓ 页面名：{data['page']['page_name']}")
            print(f"✓ URL: {data['page']['page_url']}")
            print(f"✓ 图标：{data['page']['icon']}")
            return True
        else:
            print(f"✗ 页面注册失败：{data.get('message')}")
            return False
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        return False

def test_consul_nodes():
    """测试 4: Consul 节点发现"""
    print("\n" + "=" * 60)
    print("测试 4: Consul 节点发现")
    print("=" * 60)
    
    try:
        resp = requests.get(f"{STARTOPS_BASE}/api/nodes", timeout=5)
        resp.raise_for_status()
        
        data = resp.json()
        if data.get("success"):
            provider = data.get("provider", "Unknown")
            nodes = data.get("nodes", [])
            
            print(f"✓ 节点提供者：{provider}")
            print(f"✓ 发现节点数：{len(nodes)}")
            
            for node in nodes:
                print(f"  - {node['node_name']} ({node['address']}:{node['port']})")
            
            return True
        else:
            print(f"✗ 节点获取失败：{data.get('message')}")
            return False
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("StarTops 可视化注册功能测试")
    print("=" * 60 + "\n")
    
    tests = [
        ("服务注册", test_register_service),
        ("配置注册", test_register_config),
        ("页面注册", test_register_page),
        ("Consul 节点发现", test_consul_nodes),
    ]
    
    passed = 0
    failed = 0
    
    for name, test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {name} 测试失败：{e}\n")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
