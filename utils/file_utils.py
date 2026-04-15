"""文件操作工具"""
import os
import shutil
from pathlib import Path


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def copy_file(src: str, dst: str) -> str:
    ensure_dir(os.path.dirname(dst))
    shutil.copy2(src, dst)
    return dst


def get_exe_name(path: str) -> str:
    return Path(path).stem


def is_valid_exe(path: str) -> bool:
    return os.path.isfile(path) and path.lower().endswith(".exe")


def find_exes_in_dir(directory: str) -> list[str]:
    """扫描目录下的所有 .exe 文件"""
    results = []
    try:
        for root, _dirs, files in os.walk(directory):
            for f in files:
                if f.lower().endswith(".exe"):
                    results.append(os.path.join(root, f))
    except PermissionError:
        pass
    return results


def get_cover_dir(data_dir: str) -> str:
    path = os.path.join(data_dir, "covers")
    return ensure_dir(path)


def save_cover(src_path: str, game_id: str, data_dir: str) -> str:
    """复制封面图片到数据目录，返回新路径"""
    cover_dir = get_cover_dir(data_dir)
    ext = os.path.splitext(src_path)[1] or ".png"
    dst = os.path.join(cover_dir, f"{game_id}{ext}")
    return copy_file(src_path, dst)


def format_file_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
