"""
配置可视化编辑测试脚本
测试配置的读取、渲染、保存等功能
"""

import sys
import json
import requests
from pathlib import Path

# StarTops API 地址
STARTOPS_BASE = "http://127.0.0.1:8300"

def test_get_configs():
    """测试 1: 获取配置列表"""
    print("=" * 60)
    print("测试 1: 获取配置列表")
    print("=" * 60)
    
    try:
        resp = requests.get(f"{STARTOPS_BASE}/api/configs", timeout=5)
        resp.raise_for_status()
        
        data = resp.json()
        configs = data.get("configs", [])
        
        print(f"✓ 获取到 {len(configs)} 个配置")
        
        for config in configs:
            print(f"  - {config['config_id']}: {config['config_name']}")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        return False

def test_get_config_form(config_id: str):
    """测试 2: 获取配置编辑表单"""
    print(f"\n测试 2: 获取 {config_id} 编辑表单")
    print("=" * 60)
    
    try:
        resp = requests.get(
            f"{STARTOPS_BASE}/api/config/{config_id}/form",
            timeout=5
        )
        resp.raise_for_status()
        
        data = resp.json()
        
        if data.get("success"):
            form_html = data.get("form_html", "")
            description = data.get("description", "")
            
            print(f"✓ 表单渲染成功")
            print(f"✓ 描述：{description}")
            print(f"✓ HTML 长度：{len(form_html)} 字符")
            
            # 检查是否包含必要的 HTML 元素
            assert "<form" in form_html, "缺少 form 标签"
            assert "<input" in form_html or "<select" in form_html, "缺少输入控件"
            print(f"✓ 表单结构正确")
            
            return True
        else:
            print(f"✗ 表单获取失败：{data.get('message')}")
            return False
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        return False

def test_get_config_data(config_id: str):
    """测试 3: 获取配置数据"""
    print(f"\n测试 3: 获取 {config_id} 配置数据")
    print("=" * 60)
    
    try:
        resp = requests.get(
            f"{STARTOPS_BASE}/api/config/{config_id}/data",
            timeout=5
        )
        resp.raise_for_status()
        
        data = resp.json()
        
        if data.get("success"):
            config_data = data.get("data", {})
            
            print(f"✓ 配置数据获取成功")
            print(f"✓ 数据键：{list(config_data.keys())}")
            
            return True, config_data
        else:
            print(f"✗ 配置数据获取失败：{data.get('message')}")
            return False, None
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        return False, None

def test_save_config(config_id: str, config_data: dict):
    """测试 4: 保存配置"""
    print(f"\n测试 4: 保存 {config_id} 配置")
    print("=" * 60)
    
    # 修改一个值用于测试
    if "server" in config_data and "debug" in config_data["server"]:
        original_value = config_data["server"]["debug"]
        config_data["server"]["debug"] = not original_value
        print(f"✓ 修改 debug: {original_value} -> {config_data['server']['debug']}")
    
    try:
        resp = requests.post(
            f"{STARTOPS_BASE}/api/config/{config_id}/save",
            json=config_data,
            timeout=5
        )
        resp.raise_for_status()
        
        data = resp.json()
        
        if data.get("success"):
            print(f"✓ 配置保存成功")
            print(f"✓ 消息：{data.get('message')}")
            return True
        else:
            print(f"✗ 配置保存失败：{data.get('message')}")
            return False
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        return False

def run_config_test():
    """运行配置测试"""
    print("\n" + "=" * 60)
    print("StarTops 配置可视化编辑测试")
    print("=" * 60 + "\n")
    
    tests_passed = 0
    tests_failed = 0
    
    # 测试 1: 获取配置列表
    if test_get_configs():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 测试 regex_tool 配置
    print("\n" + "=" * 60)
    print("测试 regex_tool 配置")
    print("=" * 60)
    
    # 测试 2: 获取表单
    if test_get_config_form("regex_tool_config"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 测试 3: 获取数据
    success, config_data = test_get_config_data("regex_tool_config")
    if success:
        tests_passed += 1
        
        # 测试 4: 保存配置
        if test_save_config("regex_tool_config", config_data):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        tests_failed += 1
    
    # 测试 TextCollector 配置
    print("\n" + "=" * 60)
    print("测试 TextCollector 配置")
    print("=" * 60)
    
    # 测试 2: 获取表单
    if test_get_config_form("TextCollector_config"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 测试 3: 获取数据
    success, config_data = test_get_config_data("TextCollector_config")
    if success:
        tests_passed += 1
        
        # 测试 4: 保存配置
        if test_save_config("TextCollector_config", config_data):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        tests_failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果：{tests_passed} 通过，{tests_failed} 失败")
    print("=" * 60)
    
    return tests_failed == 0

if __name__ == "__main__":
    success = run_config_test()
    sys.exit(0 if success else 1)
