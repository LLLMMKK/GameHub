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
    """从 exe 路径推导游戏名称，优先使用父目录名"""
    stem = Path(path).stem.lower()
    # 泛用名列表 — 这些 exe 名不像游戏名，应取父目录名
    generic_names = {
        "game", "start", "launch", "play", "run", "app",
        "main", "loader", "client", "application", "与工具一同启动",
    }
    if stem not in generic_names:
        return Path(path).stem

    # exe 名是泛用名，向上查找像游戏名的目录
    parts = Path(path).parts
    # 从直接父目录开始，跳过也是泛用名的目录
    generic_dirs = generic_names | {
        "bin", "game", "games", "app", "apps",
        "launcher", "build", "release", "debug",
        "x64", "x86", "win64", "win32", "windows",
        "data", "assets", "resource", "resources",
    }
    for dir_name in reversed(parts[:-1]):
        if dir_name.lower() not in generic_dirs:
            return dir_name
    # 全部目录名都是泛用的，回退到 exe 名
    return Path(path).stem


def is_valid_exe(path: str) -> bool:
    return os.path.isfile(path) and path.lower().endswith((".exe", ".bat", ".cmd"))


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
