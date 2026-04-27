"""游戏自动扫描器 - 扫描指定目录下的 .exe 文件"""
import os
from core.game_model import Game
from utils.file_utils import get_exe_name, is_valid_exe


class GameScanner:
    """扫描本地目录查找游戏可执行文件"""

    # 常见非游戏 exe 排除列表（模糊匹配，去掉分隔符后包含即排除）
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
        # 激活/注册/验证
        "activate", "activation", "validate", "reg", "register",
        # 版本检查/更新器
        "vercheck", "checkupdate", "version",
        # 加载器/注入器
        "loader", "injector",
        # 运行时
        "runtime",
    }

    # 排除的文件名（精确匹配，不区分大小写）
    EXCLUDE_EXACT = {
        "launcher.exe", "config.exe", "settings.exe",
        "registration.exe", "activate.exe", "validate.exe",
        "update.exe", "updater.exe", "patcher.exe",
    }

    # 同名目录启发豁免 — 如果 exe 文件名与所在目录名相同，即使匹配了 EXCLUDE_PATTERNS 也不排除
    # 因为 Game/Game.exe 这种结构大概率是游戏主程序
    SAME_NAME_EXEMPT_PATTERNS = {
        "game", "app", "play", "run", "start", "launch",
    }

    def scan_directory(self, directory: str) -> list[Game]:
        """扫描目录，返回找到的游戏列表"""
        games = []
        seen_paths = set()

        try:
            for root, dirs, files in os.walk(directory):
                # 跳过常见非游戏目录
                dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

                for filename in files:
                    exe_path = os.path.join(root, filename)
                    if not is_valid_exe(exe_path):
                        continue

                    norm_path = os.path.normpath(exe_path).lower()
                    if norm_path in seen_paths:
                        continue
                    seen_paths.add(norm_path)

                    # 过小的 exe 很可能不是游戏（辅助程序通常很小）；脚本启动器不按体积过滤。
                    if filename.lower().endswith(".exe"):
                        try:
                            fsize = os.path.getsize(exe_path)
                            if fsize < 100 * 1024:  # 小于 100KB 跳过
                                continue
                        except OSError:
                            continue

                    # 同名目录启发：如果 exe 文件名与所在目录名相同，更可能是游戏主程序
                    dir_name = os.path.basename(root)
                    stem = os.path.splitext(filename)[0]
                    same_name = stem.lower() == dir_name.lower()

                    if self._should_skip_file(filename, same_name_hint=same_name):
                        continue

                    name = get_exe_name(exe_path)

                    game = Game(
                        name=name,
                        exe_path=exe_path,
                    )
                    games.append(game)

        except PermissionError:
            pass

        return games

    def _should_skip_file(self, filename: str, same_name_hint: bool = False) -> bool:
        # 精确匹配
        if filename.lower() in self.EXCLUDE_EXACT:
            # 同名目录启发豁免：如 Game/Game.exe 不应被排除
            if same_name_hint:
                stem = os.path.splitext(filename)[0].lower()
                if stem in self.SAME_NAME_EXEMPT_PATTERNS:
                    return False
            return True
        # 模糊匹配（去掉分隔符后包含关键词）
        name_lower = filename.lower().replace(".", "").replace("_", "").replace("-", "")

        # 同名目录启发：如果 exe 与目录同名，对常见游戏关键词放宽过滤
        if same_name_hint:
            stem = os.path.splitext(filename)[0].lower()
            if stem in self.SAME_NAME_EXEMPT_PATTERNS:
                return False

        return any(p in name_lower for p in self.EXCLUDE_PATTERNS)

    def _should_skip_dir(self, dirname: str) -> bool:
        skip_dirs = {
            # 运行时/驱动
            "redist", "directx", "dotnet", "vc_redist", "_redist",
            "vcredist", "dxredist", "physx", "vcpp",
            # 引擎内部目录
            "engine", "unity", "unreal", "cryengine",
            # 开发/调试
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
            "frameworks", "runtimes",
            "dependencies", "deps",
            # 文档/本地化
            "docs", "doc", "documentation",
            "locales", "lang", "languages",
            "fonts", "icons", "shaders",
            # 配置
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
