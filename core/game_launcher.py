"""游戏启动器"""
import os
import shlex
import subprocess
import sys

from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class GameLauncher(QObject):
    """启动并监控游戏进程"""
    game_started = pyqtSignal(str)    # game_id
    game_exited = pyqtSignal(str)     # game_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._processes: dict[str, subprocess.Popen] = {}  # game_id -> process
        self._timer = QTimer(self)
        self._timer.setInterval(2000)  # 每2秒检查一次进程
        self._timer.timeout.connect(self._check_processes)

    def launch(self, game_id: str, exe_path: str, args: str = "") -> bool:
        """启动游戏，返回是否成功"""
        if not os.path.isfile(exe_path):
            return False

        if game_id in self._processes:
            # 游戏已在运行，尝试关闭
            self.terminate(game_id)
            return True

        try:
            is_batch = exe_path.lower().endswith((".bat", ".cmd"))
            cmd = exe_path if is_batch else [exe_path]
            if args and not is_batch:
                cmd.extend(shlex.split(args, posix=False))
            elif args:
                cmd = f'"{exe_path}" {args}'

            # Windows 下使用 CREATE_NEW_PROCESS_GROUP
            kwargs = {"shell": is_batch}
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

            process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(exe_path),
                **kwargs
            )
            self._processes[game_id] = process
            self.game_started.emit(game_id)

            if not self._timer.isActive():
                self._timer.start()

            return True
        except (OSError, subprocess.SubprocessError):
            return False

    def terminate(self, game_id: str):
        """终止游戏进程"""
        if game_id in self._processes:
            process = self._processes[game_id]
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception:
                pass
            finally:
                del self._processes[game_id]
                self.game_exited.emit(game_id)

    def is_running(self, game_id: str) -> bool:
        return game_id in self._processes

    def _check_processes(self):
        """检查游戏进程是否已退出"""
        exited = []
        for game_id, process in self._processes.items():
            ret = process.poll()
            if ret is not None:
                exited.append(game_id)

        for game_id in exited:
            del self._processes[game_id]
            self.game_exited.emit(game_id)

        if not self._processes:
            self._timer.stop()

    def shutdown_all(self):
        """关闭所有游戏"""
        for game_id in list(self._processes.keys()):
            self.terminate(game_id)
