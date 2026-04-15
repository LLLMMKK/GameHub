"""游戏时长追踪"""
from datetime import datetime
from core.game_model import GameDataStore, Game


class PlayTracker:
    """记录游戏启停时间和累计时长"""

    def __init__(self, store: GameDataStore):
        self.store = store
        self._active_sessions: dict[str, str] = {}  # game_id -> start_time (ISO)

    def start_session(self, game_id: str):
        """记录游戏启动"""
        start_time = datetime.now().isoformat()
        self._active_sessions[game_id] = start_time

        game = self.store.get_game(game_id)
        if game:
            game.add_play_record(start_time, None)
            game.is_running = True
            self.store.update_game(game)

    def end_session(self, game_id: str):
        """记录游戏退出，计算时长"""
        if game_id not in self._active_sessions:
            return

        end_time = datetime.now().isoformat()
        start_time = self._active_sessions.pop(game_id)

        game = self.store.get_game(game_id)
        if game:
            # 更新最后一条记录的 end_time
            for record in reversed(game.play_records):
                if record.get("start_time") == start_time and record.get("end_time") is None:
                    record["end_time"] = end_time
                    # 计算时长
                    start_dt = datetime.fromisoformat(start_time)
                    end_dt = datetime.fromisoformat(end_time)
                    duration = max(0, (end_dt - start_dt).total_seconds())
                    game.total_play_time += duration
                    break

            game.last_played = end_time
            game.is_running = False
            self.store.update_game(game)

    def is_tracking(self, game_id: str) -> bool:
        return game_id in self._active_sessions
