"""游戏时长追踪"""
from datetime import datetime
from core.game_model import GameDataStore, Game


class PlayTracker:
    """记录游戏启停时间和累计时长"""

    def __init__(self, store: GameDataStore):
        self.store = store
        self._active_sessions: dict[str, str | tuple] = {}  # game_id -> start_time (ISO) or (start_time, record_index)

    def start_session(self, game_id: str):
        """记录游戏启动"""
        start_time = datetime.now().isoformat()
        self._active_sessions[game_id] = start_time

        game = self.store.get_game(game_id)
        if game:
            game.add_play_record(start_time, None)
            # 记录本条 record 在 play_records 中的索引，避免 end_session 遍历
            self._active_sessions[game_id] = (start_time, len(game.play_records) - 1)
            game.is_running = True
            self.store.update_game(game)

    def end_session(self, game_id: str):
        """记录游戏退出，计算时长"""
        if game_id not in self._active_sessions:
            return

        session_data = self._active_sessions.pop(game_id)
        # 兼容旧数据：可能是 str (start_time) 或 tuple (start_time, record_index)
        if isinstance(session_data, tuple):
            start_time, record_idx = session_data
        else:
            start_time = session_data
            record_idx = -1

        end_time = datetime.now().isoformat()

        game = self.store.get_game(game_id)
        if game:
            if 0 <= record_idx < len(game.play_records):
                record = game.play_records[record_idx]
                if record.get("start_time") == start_time and record.get("end_time") is None:
                    record["end_time"] = end_time
                    start_dt = datetime.fromisoformat(start_time)
                    end_dt = datetime.fromisoformat(end_time)
                    game.total_play_time += max(0, (end_dt - start_dt).total_seconds())
            else:
                for record in reversed(game.play_records):
                    if record.get("start_time") == start_time and record.get("end_time") is None:
                        record["end_time"] = end_time
                        start_dt = datetime.fromisoformat(start_time)
                        end_dt = datetime.fromisoformat(end_time)
                        game.total_play_time += max(0, (end_dt - start_dt).total_seconds())
                        break

            game.last_played = end_time
            game.is_running = False
            self.store.update_game(game)

    def is_tracking(self, game_id: str) -> bool:
        return game_id in self._active_sessions
