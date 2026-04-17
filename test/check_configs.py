"""
配置文件完整性检查脚本
检查所有配置文件的字段完整性
"""

import sys
import json
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
CONFIGS_DIR = PROJECT_ROOT / "configs"

# 必需字段定义
SERVICE_LIST_REQUIRED_FIELDS = [
    "name",
    "url",
    "health_check_url",
    "health_check_interval",
    "executor",
    "app_dir",
    "app_file_name",
    "description",
    "keep_alive",
    "start_timeout",
    "stop_timeout"
]

SERVICE_PAGES_REQUIRED_FIELDS = [
    "service_name",
    "page_name",
    "page_url",
    "icon",
    "description"
]

NODES_REQUIRED_FIELDS = [
    "node_id",
    "node_name",
    "address",
    "port",
    "status"
]

CONFIG_LIST_REQUIRED_FIELDS = [
    "config_id",
    "service_name",
    "config_name",
    "config_file_path",
    "description"
]


def check_json_file(file_path: Path, required_fields: list, item_name: str) -> bool:
    """检查 JSON 配置文件"""
    print(f"\n检查 {item_name}: {file_path.name}")
    print("-" * 60)
    
    if not file_path.exists():
        print(f"⚠️  文件不存在")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 确保是列表
        if not isinstance(data, list):
            data = [data]
        
        all_valid = True
        for i, item in enumerate(data):
            missing_fields = []
            for field in required_fields:
                if field not in item:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ 第 {i+1} 项缺少字段：{', '.join(missing_fields)}")
                all_valid = False
            else:
                print(f"✅ 第 {i+1} 项 [{item.get('name', item.get('config_id', 'N/A'))}] 字段完整")
        
        if all_valid:
            print(f"✅ 所有 {len(data)} 项配置都完整")
        
        return all_valid
    
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败：{e}")
        return False
    except Exception as e:
        print(f"❌ 读取失败：{e}")
        return False


def check_all_configs():
    """检查所有配置文件"""
    print("=" * 60)
    print("StarTops 配置文件完整性检查")
    print("=" * 60)
    
    checks = [
        (CONFIGS_DIR / "service_list.json", SERVICE_LIST_REQUIRED_FIELDS, "服务列表配置"),
        (CONFIGS_DIR / "service_pages.json", SERVICE_PAGES_REQUIRED_FIELDS, "服务页面配置"),
        (CONFIGS_DIR / "nodes.json", NODES_REQUIRED_FIELDS, "节点配置"),
        (CONFIGS_DIR / "config_list.json", CONFIG_LIST_REQUIRED_FIELDS, "配置文件列表"),
    ]
    
    passed = 0
    failed = 0
    
    for file_path, required_fields, item_name in checks:
        if check_json_file(file_path, required_fields, item_name):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"检查结果：{passed} 通过，{failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = check_all_configs()
    sys.exit(0 if success else 1)
