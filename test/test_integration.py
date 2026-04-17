"""
StarTops 集成测试脚本
测试通过 StarTops 管理 regex_tool 和 TextCollector 服务

测试内容:
1. 启动 StarTops
2. 通过 API 启动服务
3. 检查服务健康状态
4. 通过 API 停止服务
5. 验证服务页面配置
"""

import sys
import time
import requests
from pathlib import Path

# StarTops API 地址
STARTOPS_BASE = "http://127.0.0.1:8300"

def check_startops_running() -> bool:
    """检查 StarTops 是否运行"""
    try:
        resp = requests.get(f"{STARTOPS_BASE}/api/health", timeout=2)
        return resp.status_code == 200
    except:
        return False

def test_get_services():
    """测试 1: 获取服务列表"""
    print("=" * 60)
    print("测试 1: 获取服务列表")
    print("=" * 60)
    
    try:
        resp = requests.get(f"{STARTOPS_BASE}/api/services", timeout=5)
        resp.raise_for_status()
        
        data = resp.json()
        services = data.get("services", {})
        
        print(f"✓ 获取到 {len(services)} 个服务")
        
        # 检查是否有 regex_tool 和 TextCollector
        assert "regex_tool" in services, "缺少 regex_tool 服务"
        print("✓ regex_tool 服务已配置")
        
        assert "TextCollector" in services, "缺少 TextCollector 服务"
        print("✓ TextCollector 服务已配置")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        return False

def test_start_service(service_name: str) -> bool:
    """启动服务"""
    print(f"\n启动服务：{service_name}")
    
    try:
        resp = requests.post(
            f"{STARTOPS_BASE}/api/service/{service_name}/start",
            timeout=5
        )
        resp.raise_for_status()
        
        data = resp.json()
        if data.get("success"):
            print(f"✓ {service_name} 启动成功")
            return True
        else:
            print(f"✗ {service_name} 启动失败：{data.get('message')}")
            return False
    except Exception as e:
        print(f"✗ {service_name} 启动异常：{e}")
        return False

def test_service_health(service_name: str, service_url: str) -> bool:
    """测试服务健康状态"""
    print(f"检查 {service_name} 健康状态...")
    
    # 等待服务启动（增加等待时间）
    time.sleep(5)
    
    try:
        # 通过 StarTops API 检查
        resp = requests.get(
            f"{STARTOPS_BASE}/api/service/{service_name}",
            timeout=5
        )
        resp.raise_for_status()
        
        data = resp.json()
        service = data.get("service", {})
        status = service.get("status")
        
        print(f"✓ StarTops 状态：{status}")
        
        # 直接检查服务
        health_url = f"{service_url}/api/health"
        resp = requests.get(health_url, timeout=5)
        resp.raise_for_status()
        
        print(f"✓ 服务健康检查通过")
        return True
    except Exception as e:
        print(f"✗ 健康检查失败：{e}")
        return False

def test_stop_service(service_name: str) -> bool:
    """停止服务"""
    print(f"\n停止服务：{service_name}")
    
    try:
        resp = requests.post(
            f"{STARTOPS_BASE}/api/service/{service_name}/stop",
            timeout=5
        )
        resp.raise_for_status()
        
        data = resp.json()
        if data.get("success"):
            print(f"✓ {service_name} 停止成功")
            return True
        else:
            print(f"✗ {service_name} 停止失败：{data.get('message')}")
            return False
    except Exception as e:
        print(f"✗ {service_name} 停止异常：{e}")
        return False

def test_get_pages():
    """测试获取服务页面"""
    print("\n" + "=" * 60)
    print("测试：获取服务页面配置")
    print("=" * 60)
    
    try:
        resp = requests.get(f"{STARTOPS_BASE}/api/pages", timeout=5)
        resp.raise_for_status()
        
        data = resp.json()
        pages = data.get("pages", [])
        
        print(f"✓ 获取到 {len(pages)} 个页面")
        
        # 检查页面
        regex_page = next((p for p in pages if p.get("service_name") == "regex_tool"), None)
        if regex_page:
            print(f"✓ regex_tool 页面：{regex_page.get('page_name')}")
        
        text_page = next((p for p in pages if p.get("service_name") == "TextCollector"), None)
        if text_page:
            print(f"✓ TextCollector 页面：{text_page.get('page_name')}")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        return False

def run_integration_test():
    """运行集成测试"""
    print("\n" + "=" * 60)
    print("StarTops 集成测试")
    print("=" * 60 + "\n")
    
    # 检查 StarTops 是否运行
    if not check_startops_running():
        print("✗ StarTops 未运行！")
        print("请先启动 StarTops: cd /data/code/star-tops && python3 main.py")
        return False
    
    print("✓ StarTops 运行正常\n")
    
    tests_passed = 0
    tests_failed = 0
    
    # 测试 1: 获取服务列表
    if test_get_services():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 测试 2: 启动 regex_tool
    if test_start_service("regex_tool"):
        tests_passed += 1
        
        # 测试健康检查
        if test_service_health("regex_tool", "http://127.0.0.1:9393"):
            tests_passed += 1
        else:
            tests_failed += 1
        
        # 停止服务
        if test_stop_service("regex_tool"):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        tests_failed += 1
    
    # 测试 3: 启动 TextCollector
    if test_start_service("TextCollector"):
        tests_passed += 1
        
        # 测试健康检查
        if test_service_health("TextCollector", "http://127.0.0.1:9677"):
            tests_passed += 1
        else:
            tests_failed += 1
        
        # 停止服务
        if test_stop_service("TextCollector"):
            tests_passed += 1
        else:
            tests_failed += 1
    else:
        tests_failed += 1
    
    # 测试 4: 获取页面配置
    if test_get_pages():
        tests_passed += 1
    else:
        tests_failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果：{tests_passed} 通过，{tests_failed} 失败")
    print("=" * 60)
    
    return tests_failed == 0

if __name__ == "__main__":
    success = run_integration_test()
    sys.exit(0 if success else 1)
