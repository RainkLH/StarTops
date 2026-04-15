"""
网页终端测试脚本（跨平台）
测试终端的创建、输入输出、超时等功能

支持:
- Linux: 使用 pty
- Windows: 使用 subprocess
"""

import sys
import asyncio
import time
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.web_terminal import SimpleTerminal, create_terminal, get_terminal, close_terminal


def test_terminal_spawn():
    """测试终端创建"""
    print("=" * 60)
    print("测试 1: 终端创建")
    print("=" * 60)
    
    terminal = SimpleTerminal(timeout=60, max_lines=100)
    result = terminal.spawn()
    
    assert result == True, "终端创建失败"
    print(f"✓ 终端创建成功 (平台：{'Windows' if terminal.is_windows else 'Linux'})")
    
    assert terminal.running == True, "终端未运行"
    print("✓ 终端状态正确")
    
    terminal.close()
    print("✓ 测试 1 通过\n")
    return True


def test_terminal_write_read():
    """测试终端输入输出"""
    print("=" * 60)
    print("测试 2: 终端输入输出")
    print("=" * 60)
    
    terminal = SimpleTerminal(timeout=60, max_lines=100)
    terminal.spawn()
    
    # 等待终端启动
    time.sleep(0.5)
    
    # 发送命令（跨平台）
    if terminal.is_windows:
        terminal.write("echo Hello Terminal\n")
    else:
        terminal.write("echo 'Hello Terminal'\n")
    
    # 等待输出
    time.sleep(0.5)
    
    # 读取输出
    output = terminal.read()
    
    assert "Hello Terminal" in output, f"输出不包含期望内容：{output}"
    print(f"✓ 命令执行成功，输出：{output.strip()[:50]}")
    
    terminal.close()
    print("✓ 测试 2 通过\n")
    return True


def test_terminal_max_lines():
    """测试输出行数限制"""
    print("=" * 60)
    print("测试 3: 输出行数限制")
    print("=" * 60)
    
    terminal = SimpleTerminal(timeout=60, max_lines=100)
    terminal.spawn()
    
    time.sleep(0.5)
    
    # 发送产生多行输出的命令（跨平台）
    if terminal.is_windows:
        # Windows: 使用 for /L 循环
        terminal.write("for /L %i in (1,1,200) do @echo Line %i\n")
    else:
        # Linux: 使用 seq
        terminal.write("for i in $(seq 1 200); do echo \"Line $i\"; done\n")
    
    time.sleep(1)
    
    # 读取所有输出
    while True:
        output = terminal.read()
        if not output:
            break
    
    # 检查缓冲区大小
    assert len(terminal.output_buffer) <= 100, f"输出超过 100 行：{len(terminal.output_buffer)}"
    print(f"✓ 输出限制正确，当前缓冲区：{len(terminal.output_buffer)} 行")
    
    terminal.close()
    print("✓ 测试 3 通过\n")
    return True


async def test_terminal_timeout():
    """测试超时关闭"""
    print("=" * 60)
    print("测试 4: 超时关闭")
    print("=" * 60)
    
    # 创建 2 秒超时的终端
    terminal = SimpleTerminal(timeout=2, max_lines=100)
    terminal.spawn()
    
    print("✓ 终端创建成功，等待超时...")
    
    # 等待超时
    await asyncio.sleep(3)
    
    # 检查是否超时
    assert terminal.check_timeout() == True, "终端未超时"
    print("✓ 超时检测正确")
    
    terminal.close()
    print("✓ 测试 4 通过\n")
    return True


def test_global_terminal():
    """测试全局终端管理"""
    print("=" * 60)
    print("测试 5: 全局终端管理")
    print("=" * 60)
    
    # 创建终端
    terminal1 = create_terminal(timeout=60)
    assert terminal1 is not None, "创建终端失败"
    print("✓ 第一个终端创建成功")
    
    # 再创建一个（应该关闭前一个）
    terminal2 = create_terminal(timeout=60)
    assert terminal2 is not None, "创建第二个终端失败"
    print("✓ 第二个终端创建成功（第一个已自动关闭）")
    
    # 获取当前终端
    current = get_terminal()
    assert current == terminal2, "获取当前终端失败"
    print("✓ 获取当前终端正确")
    
    # 关闭终端
    close_terminal()
    assert get_terminal() is None, "关闭终端失败"
    print("✓ 关闭终端正确")
    
    print("✓ 测试 5 通过\n")
    return True


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("StarTops 网页终端测试（跨平台）")
    print("=" * 60 + "\n")
    
    tests = [
        ("终端创建", test_terminal_spawn),
        ("终端输入输出", test_terminal_write_read),
        ("输出行数限制", test_terminal_max_lines),
        ("超时关闭", test_terminal_timeout),
        ("全局终端管理", test_global_terminal),
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
