"""Startops 自重启执行器。"""

import json
import os
import subprocess
from pathlib import Path
from typing import List

from src.utils.logger import get_logger

logger = get_logger("system_restart")


def _project_root() -> Path:
    """返回项目根目录。"""
    return Path(__file__).resolve().parent.parent


def _restart_script_path() -> Path:
    """根据平台获取重启脚本路径。"""
    script_name = "restart_startops.bat" if os.name == "nt" else "restart_startops.sh"
    return _project_root() / "deployment" / script_name


def _last_args_file_path() -> Path:
    """上次启动参数持久化文件路径。"""
    return _project_root() / "deployment" / "last_start_args.json"


def save_last_start_args(args: List[str]) -> bool:
    """保存上次启动参数，用于重启时复用。"""
    file_path = _last_args_file_path()
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({"args": args}, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved last start args to: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save last start args: {e}")
        return False


def load_last_start_args() -> List[str]:
    """读取上次启动参数。"""
    file_path = _last_args_file_path()
    if not file_path.exists():
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        args = data.get("args", [])
        if isinstance(args, list) and all(isinstance(item, str) for item in args):
            return args
        logger.warning(f"Invalid args format in {file_path}, fallback to empty args")
        return []
    except Exception as e:
        logger.error(f"Failed to read last start args: {e}")
        return []


def launch_restart_script(args: List[str]) -> bool:
    """异步拉起重启脚本并返回是否成功触发。"""
    script_path = _restart_script_path()
    if not script_path.exists():
        logger.error(f"Restart script not found: {script_path}")
        return False

    project_root = _project_root()

    try:
        if os.name == "nt":
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            subprocess.Popen(
                ["cmd", "/c", str(script_path)] + args,
                cwd=str(project_root),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
            )
        else:
            subprocess.Popen(
                ["/bin/sh", str(script_path)] + args,
                cwd=str(project_root),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )

        logger.info(f"Restart script launched: {script_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to launch restart script: {e}")
        return False
