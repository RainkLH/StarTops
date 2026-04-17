"""
StarTops 网页终端模块（简化版）
提供简单的 Web 终端，用于查看文件、确认位置等短暂任务

功能特性:
- 跨平台支持（Linux/Windows）
- 输出限制 100 行
- 自动超时关闭
- 简单可靠

注意：
- Linux: 使用 pty 伪终端
- Windows: 使用 subprocess 子进程
"""

import os
import sys
import asyncio
import time
import shutil
import locale
import codecs
from typing import Optional, List
import uuid

from src.utils.logger import get_logger

logger = get_logger('web_terminal')

# 跨平台导入
import queue

if sys.platform != 'win32':
    import pty
    import select
    import signal
    import termios
    import struct
else:
    import subprocess
    import threading
    pty = None
    select = None
    signal = None


class SimpleTerminal:
    """简单终端类（跨平台）"""
    
    def __init__(self, shell: str = None, timeout: int = 60, max_lines: int = 100):
        """
        初始化
        
        Args:
            shell: Shell 程序（Linux: /bin/bash, Windows: cmd.exe）
            timeout: 超时时间（秒）
            max_lines: 最大输出行数
        """
        self.session_id = str(uuid.uuid4())
        
        self.shell = self._normalize_shell(shell)
        
        self.timeout = timeout
        self.max_lines = max_lines
        
        # Linux 专用
        self.fd: Optional[int] = None
        self.pid: Optional[int] = None
        
        # Windows 专用
        self.process: Optional['subprocess.Popen'] = None
        self.output_queue: queue.Queue = queue.Queue()
        self.read_thread: Optional['threading.Thread'] = None
        # Windows 终端统一使用 UTF-8，并在启动后主动切换代码页到 65001
        self.windows_encoding = 'utf-8' if sys.platform == 'win32' else 'utf-8'
        
        # 通用
        self.last_activity: float = 0
        self.output_buffer: List[str] = []
        self.running = False
        self.is_windows = sys.platform == 'win32'

    def _normalize_shell(self, shell: Optional[str]) -> str:
        """规范化 shell 配置，避免 Windows 下误配 Linux shell 导致启动失败。"""
        default_shell = 'cmd.exe' if sys.platform == 'win32' else '/bin/bash'
        candidate = (shell or '').strip()
        if not candidate:
            return default_shell

        if sys.platform == 'win32':
            # Windows 下常见的 Linux 风格路径直接回退，避免 /bin/bash 启动失败。
            if candidate.startswith('/'):
                logger.warning(f"Invalid shell for Windows: {candidate}, fallback to cmd.exe")
                return 'cmd.exe'

            exe = candidate.split()[0]
            if not os.path.isabs(exe) and shutil.which(exe) is None:
                logger.warning(f"Shell not found on Windows: {candidate}, fallback to cmd.exe")
                return 'cmd.exe'

        return candidate

    def _maybe_fix_windows_mojibake(self, text: str) -> str:
        """尝试修复 Windows 下常见的 UTF-8/GBK 互相误解码导致的乱码。"""
        if not self.is_windows or not text:
            return text

        try:
            repaired = text.encode('gbk', errors='ignore').decode('utf-8', errors='ignore')
            if not repaired:
                return text

            original_bad = text.count('�')
            repaired_bad = repaired.count('�')
            original_cjk = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
            repaired_cjk = sum(1 for ch in repaired if '\u4e00' <= ch <= '\u9fff')

            mojibake_markers = ('鍙', '褰', '瀵', '鎴', '锛', '銆', '浠', '鐨', '鏂')

            if repaired_bad < original_bad and len(repaired) >= 3:
                return repaired

            if any(marker in text for marker in mojibake_markers) and repaired_cjk >= 2:
                return repaired

            if repaired_bad <= original_bad and repaired_cjk > original_cjk:
                return repaired
        except Exception:
            return text

        return text
    
    def spawn(self) -> bool:
        """创建终端"""
        try:
            if self.is_windows:
                return self._spawn_windows()
            else:
                return self._spawn_linux()
        except Exception as e:
            logger.error(f"Failed to spawn terminal: {e}")
            return False
    
    def _spawn_linux(self) -> bool:
        """Linux: 创建伪终端"""
        self.pid, self.fd = pty.fork()
        
        if self.pid == 0:
            # 子进程执行 Shell
            os.execvp(self.shell, [self.shell])
        else:
            self.running = True
            self.last_activity = time.monotonic()
            logger.info(f"Terminal spawned (Linux): {self.session_id}")
            return True
        return False
    
    def _spawn_windows(self) -> bool:
        """Windows: 创建子进程"""
        try:
            # 创建子进程，使用 PIPE 捕获输出
            self.process = subprocess.Popen(
                self.shell,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0
            )

            # 统一代码页到 UTF-8，避免中文输出被本地代码页错误解码
            if self.process.stdin:
                self.process.stdin.write(b'chcp 65001>nul\r\n')
                self.process.stdin.flush()
            
            self.running = True
            self.last_activity = time.monotonic()
            
            # 启动读取线程
            self.read_thread = threading.Thread(target=self._read_windows_thread, daemon=True)
            self.read_thread.start()
            
            logger.info(f"Terminal spawned (Windows): {self.session_id}")
            return True
        except Exception as e:
            logger.error(f"Windows spawn failed: {e}")
            return False
    
    def _read_windows_thread(self):
        """Windows: 后台读取线程"""
        try:
            utf8_decoder = codecs.getincrementaldecoder('utf-8')('replace')
            while self.running and self.process:
                reader = self.process.stdout
                if hasattr(reader, 'read1'):
                    chunk = reader.read1(4096)
                else:
                    chunk = reader.read(4096)
                if not chunk:
                    break
                self.output_queue.put(utf8_decoder.decode(chunk))

            tail = utf8_decoder.decode(b'', final=True)
            if tail:
                self.output_queue.put(tail)
        except Exception as e:
            logger.error(f"Windows read error: {e}")
        finally:
            self.running = False
    
    def write(self, data: str) -> bool:
        """写入输入"""
        if not self.running:
            return False
        
        try:
            if self.is_windows:
                if self.process and self.process.stdin:
                    self.process.stdin.write(data.encode(self.windows_encoding, errors='replace'))
                    self.process.stdin.flush()
            else:
                if self.fd is not None:
                    os.write(self.fd, data.encode('utf-8'))
            
            self.last_activity = time.monotonic()
            return True
        except Exception as e:
            logger.error(f"Write error: {e}")
            return False
    
    def read(self) -> str:
        """读取输出（限制 100 行）"""
        if not self.running:
            return ""
        
        try:
            output = []
            
            if self.is_windows:
                # Windows: 从队列读取
                while not self.output_queue.empty():
                    output.append(self.output_queue.get_nowait())
            else:
                # Linux: 从 fd 读取
                if self.fd is not None:
                    ready, _, _ = select.select([self.fd], [], [], 0.01)
                    if ready:
                        data = os.read(self.fd, 4096).decode('utf-8', errors='replace')
                        output.append(data)
            
            if output:
                data = ''.join(output)
                data = self._maybe_fix_windows_mojibake(data)
                self.last_activity = time.monotonic()
                
                # 添加到缓冲区
                lines = data.split('\n')
                self.output_buffer.extend(lines)
                
                # 限制 100 行
                if len(self.output_buffer) > self.max_lines:
                    self.output_buffer = self.output_buffer[-self.max_lines:]
                
                return data
            
            return ""
        except Exception as e:
            logger.error(f"Read error: {e}")
            if not self.is_windows:
                self.running = False
            return ""
    
    def check_timeout(self) -> bool:
        """检查超时"""
        if self.timeout <= 0:
            return False
        
        elapsed = time.monotonic() - self.last_activity
        return elapsed > self.timeout
    
    def get_output(self) -> str:
        """获取所有输出"""
        return '\n'.join(self.output_buffer)
    
    def close(self):
        """关闭终端"""
        self.running = False
        
        if self.is_windows:
            # Windows: 关闭进程
            if self.process:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=2)
                except:
                    try:
                        self.process.kill()
                    except:
                        pass
        else:
            # Linux: 关闭 fd 和进程
            if self.fd is not None:
                try:
                    os.close(self.fd)
                except:
                    pass
            if self.pid is not None:
                try:
                    os.kill(self.pid, signal.SIGTERM)
                except:
                    pass
        
        logger.info(f"Terminal closed: {self.session_id}")


# 全局终端实例（单例，简单起见只允许一个终端）
_current_terminal: Optional[SimpleTerminal] = None


def create_terminal(shell: str = None, timeout: int = 60, max_lines: int = 100) -> Optional[SimpleTerminal]:
    """创建终端"""
    global _current_terminal
    
    # 如果已有终端，先关闭
    if _current_terminal is not None:
        _current_terminal.close()
    
    _current_terminal = SimpleTerminal(
        shell=shell,
        timeout=timeout,
        max_lines=max_lines
    )
    
    if not _current_terminal.spawn():
        _current_terminal = None
        return None
    
    return _current_terminal


def get_terminal() -> Optional[SimpleTerminal]:
    """获取当前终端"""
    return _current_terminal


def close_terminal():
    """关闭终端"""
    global _current_terminal
    if _current_terminal:
        _current_terminal.close()
        _current_terminal = None
