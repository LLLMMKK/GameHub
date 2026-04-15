"""游戏自动扫描器 - 扫描指定目录下的 .exe 文件"""
import os
from core.game_model import Game
from utils.file_utils import get_exe_name, is_valid_exe


class GameScanner:
    """扫描本地目录查找游戏可执行文件"""

    # 常见非游戏 exe 排除列表
    EXCLUDE_PATTERNS = {
        # 安装/卸载/补丁
        "uninstall", "setup", "install", "crash", "report",
        "patch", "update", "migrate",
        # 运行时/驱动
        "redist", "vc_redist", "vcredist", "dxsetup", "directx",
        "dotnet", "framework", "xna", "fna",
        # 系统工具/服务
        "helper", "browser", "service", "daemon", "monitor",
        "config", "settings", "options", "registration",
        # 引擎/SDK 工具
        "unity", "unreal", "cryengine", "godot",
        "crashhandler", "crashreporter", "errorreporter",
        "subprocess", "worker", "spawn",
        # 常见工具 exe
        "7z", "7za", "winrar", "unrar",
        "ffmpeg", "ffprobe", "ffplay",
        "openssl", "curl", "wget",
        "node", "python", "pip",
        "cmd", "powershell",
        # 反作弊/DRM
        "eac", "easyanticheat", "battleye", "anticheat",
        "steam_api", "steamclient", "gameoverlay",
        "eos", "epiconline", "galaxyclient",
        # 通用小工具
        "notepad", "editor", "viewer", "converter",
        "log", "debug", "test", "benchmark",
        "proxy", "tunnel", "validator",
    }

    # 排除的文件名（精确匹配，不区分大小写）
    EXCLUDE_EXACT = {
        "launcher.exe", "config.exe", "settings.exe",
        "unityplayer.dll",  # 非 exe 但相关
    }

    def scan_directory(self, directory: str) -> list[Game]:
        """扫描目录，返回找到的游戏列表"""
        games = []
        seen_names = set()

        try:
            for root, dirs, files in os.walk(directory):
                # 跳过常见非游戏目录
                dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

                for filename in files:
                    if not filename.lower().endswith(".exe"):
                        continue
                    if self._should_skip_file(filename):
                        continue

                    exe_path = os.path.join(root, filename)

                    # 过小的 exe 很可能不是游戏（工具/辅助程序通常很小）
                    try:
                        fsize = os.path.getsize(exe_path)
                        if fsize < 512 * 1024:  # 小于 512KB 跳过
                            continue
                    except OSError:
                        continue
                    name = get_exe_name(exe_path)

                    # 去重
                    if name.lower() in seen_names:
                        continue
                    seen_names.add(name.lower())

                    game = Game(
                        name=name,
                        exe_path=exe_path,
                    )
                    games.append(game)

        except PermissionError:
            pass

        return games

    def _should_skip_file(self, filename: str) -> bool:
        # 精确匹配
        if filename.lower() in self.EXCLUDE_EXACT:
            return True
        # 模糊匹配（去掉分隔符后包含关键词）
        name_lower = filename.lower().replace(".", "").replace("_", "").replace("-", "")
        return any(p in name_lower for p in self.EXCLUDE_PATTERNS)

    def _should_skip_dir(self, dirname: str) -> bool:
        skip_dirs = {
            # 运行时/驱动
            "redist", "directx", "dotnet", "vc_redist", "_redist",
            "vcredist", "dxredist", "physx", "vcpp",
            # 引擎内部目录
            "engine", "unity", "unreal", "cryengine",
            # 工具/开发
            "tools", "tool", "bin", "utils", "utility",
            "sdk", "dev", "debug", "build",
            # 插件/模块
            "plugins", "plugin", "mods", "patch",
            # 系统/缓存/日志
            "cache", "temp", "tmp", "logs", "log",
            "backup", "save", "saves", "saved",
            # 反作弊
            "easyanticheat", "eac", "battleye",
            # 框架/库
            "lib", "libs", "library", "libraries",
            "frameworks", "runtime", "runtimes",
            "dependencies", "deps",
            # 其他非游戏
            "docs", "doc", "documentation",
            "locales", "lang", "languages",
            "fonts", "icons", "textures", "shaders",
            "audio", "video", "music", "sound",
            "data", "assets", "resource", "resources",
            "config", "cfg", "conf",
        }
        dl = dirname.lower()
        # 精确匹配
        if dl in skip_dirs:
            return True
        # 以 __ 或 . 开头的隐藏/特殊目录
        if dl.startswith(".") or dl.startswith("__"):
            return True
        return False
