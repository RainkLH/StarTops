#!/usr/bin/env python3
"""
Startops 一键启动脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    # 获取当前脚本所在目录
    script_dir = Path(__file__).parent.absolute()
    
    print("=" * 60)
    print("Startops 2.0 - 轻量级业务运维集成控制台")
    print("=" * 60)
    print()
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: Python版本过低，需要3.8或更高")
        sys.exit(1)
    
    print(f"✓ Python版本: {sys.version}")
    print(f"✓ 项目路径: {script_dir}")
    print()
    
    # 检查依赖
    print("检查依赖...")
    try:
        import fastapi
        import uvicorn
        import httpx
        print("✓ 所有依赖已安装")
    except ImportError as e:
        print(f"❌ 缺失依赖: {e}")
        print("\n正在安装依赖...")
        requirements_file = script_dir / "requirements.txt"
        if requirements_file.exists():
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                check=True
            )
            print("✓ 依赖安装完成")
        else:
            print("❌ 找不到requirements.txt文件")
            sys.exit(1)
    
    print()
    print("=" * 60)
    print("启动Startops服务...")
    print("=" * 60)
    print()
    print("访问地址: http://127.0.0.1:8000")
    print("按 Ctrl+C 停止服务")
    print()
    
    # 启动应用
    os.chdir(script_dir)
    try:
        subprocess.run(
            [sys.executable, "main.py"],
            cwd=script_dir
        )
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Startops已停止")
        print("=" * 60)
        sys.exit(0)

if __name__ == "__main__":
    main()
