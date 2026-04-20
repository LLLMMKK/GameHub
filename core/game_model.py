"""游戏数据模型与数据管理"""
import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


# 预设分类
DEFAULT_CATEGORIES = ["全部", "最近游玩", "动作", "策略", "RPG", "冒险", "模拟", "体育", "竞速", "休闲", "Galgame", "其他"]


@dataclass
class PlayRecord:
    """单次游玩记录"""
    start_time: str  # ISO 格式
    end_time: Optional[str] = None

    @property
    def duration_seconds(self) -> float:
        if not self.end_time:
            return 0.0
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        return max(0, (end - start).total_seconds())


@dataclass
class Game:
    """游戏数据模型"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    exe_path: str = ""
    launch_args: str = ""
    category: str = "其他"
    cover_path: str = ""
    description: str = ""
    is_r18: bool = False
    total_play_time: float = 0.0  # 总游玩秒数
    last_played: Optional[str] = None  # ISO 格式
    play_records: list = field(default_factory=list)  # List[dict]
    added_time: str = field(default_factory=lambda: datetime.now().isoformat())
    is_running: bool = False

    def add_play_record(self, start_time: str, end_time: Optional[str] = None):
        record = {"start_time": start_time, "end_time": end_time}
        self.play_records.append(record)
        if end_time:
            self.total_play_time += PlayRecord(**record).duration_seconds
            self.last_played = end_time

    def format_play_time(self) -> str:
        hours = int(self.total_play_time // 3600)
        minutes = int((self.total_play_time % 3600) // 60)
        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        return f"{minutes}分钟"

    def format_last_played(self) -> str:
        if not self.last_played:
            return "从未游玩"
        dt = datetime.fromisoformat(self.last_played)
        now = datetime.now()
        delta = now - dt
        if delta.days == 0:
            return "今天"
        elif delta.days == 1:
            return "昨天"
        elif delta.days < 7:
            return f"{delta.days}天前"
        else:
            return dt.strftime("%Y-%m-%d")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "exe_path": self.exe_path,
            "launch_args": self.launch_args,
            "category": self.category,
            "cover_path": self.cover_path,
            "description": self.description,
            "is_r18": self.is_r18,
            "total_play_time": self.total_play_time,
            "last_played": self.last_played,
            "play_records": self.play_records,
            "added_time": self.added_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Game":
        game = cls()
        game.id = data.get("id", str(uuid.uuid4())[:8])
        game.name = data.get("name", "")
        game.exe_path = data.get("exe_path", "")
        game.launch_args = data.get("launch_args", "")
        game.category = data.get("category", "其他")
        game.cover_path = data.get("cover_path", "")
        game.description = data.get("description", "")
        game.is_r18 = data.get("is_r18", False)
        game.total_play_time = data.get("total_play_time", 0.0)
        game.last_played = data.get("last_played")
        game.play_records = data.get("play_records", [])
        game.added_time = data.get("added_time", datetime.now().isoformat())
        return game


class GameDataStore:
    """游戏数据持久化管理"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        self.data_dir = data_dir
        self.games_file = os.path.join(data_dir, "games.json")
        self.config_file = os.path.join(data_dir, "config.json")
        self.games: list[Game] = []
        self.categories: list[str] = list(DEFAULT_CATEGORIES)
        self.privacy_mode: bool = False
        self.default_search_engine: str = "baidu"
        self.default_game_dir: str = ""
        self._ensure_data_dir()
        self.load()

    def _ensure_data_dir(self):
        os.makedirs(self.data_dir, exist_ok=True)

    def load(self):
        # 加载配置
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.privacy_mode = config.get("privacy_mode", False)
                self.default_search_engine = config.get("default_search_engine", "baidu")
                self.default_game_dir = config.get("default_game_dir", "")
            except (json.JSONDecodeError, KeyError):
                pass

        # 加载游戏数据
        if os.path.exists(self.games_file):
            try:
                with open(self.games_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.games = [Game.from_dict(g) for g in data.get("games", [])]
                custom_cats = data.get("categories", [])
                for cat in custom_cats:
                    if cat not in self.categories:
                        self.categories.append(cat)
            except (json.JSONDecodeError, KeyError):
                self.games = []

    def save(self):
        self._ensure_data_dir()
        data = {
            "games": [g.to_dict() for g in self.games],
            "categories": self.categories,
        }
        with open(self.games_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.save_config()

    def save_config(self):
        self._ensure_data_dir()
        config = {"privacy_mode": self.privacy_mode, "default_search_engine": self.default_search_engine, "default_game_dir": self.default_game_dir}
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def add_game(self, game: Game) -> Game:
        self.games.append(game)
        self.save()
        return game

    def update_game(self, game: Game):
        for i, g in enumerate(self.games):
            if g.id == game.id:
                self.games[i] = game
                break
        self.save()

    def remove_game(self, game_id: str):
        self.games = [g for g in self.games if g.id != game_id]
        self.save()

    def get_game(self, game_id: str) -> Optional[Game]:
        for g in self.games:
            if g.id == game_id:
                return g
        return None

    def get_games_by_category(self, category: str) -> list[Game]:
        if category == "全部":
            return list(self.games)
        elif category == "最近游玩":
            recent = [g for g in self.games if g.last_played is not None]
            recent.sort(key=lambda g: g.last_played or "", reverse=True)
            return recent[:20]
        else:
            return [g for g in self.games if g.category == category]

    def search_games(self, query: str) -> list[Game]:
        q = query.lower().strip()
        if not q:
            return list(self.games)
        return [g for g in self.games if q in g.name.lower()]

    def add_category(self, name: str):
        if name and name not in self.categories:
            self.categories.append(name)
            self.save()

    def remove_category(self, name: str):
        if name in self.categories and name not in DEFAULT_CATEGORIES[:3]:
            self.categories.remove(name)
            for g in self.games:
                if g.category == name:
                    g.category = "其他"
            self.save()
