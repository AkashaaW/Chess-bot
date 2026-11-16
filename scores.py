from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from uuid import uuid4

POINTS = {"win": 1, "draw": 0.5, "loss": 0}
DEFAULT_PATH = Path(__file__).with_name("scores.json")
# The previous scores.py was sometimes saved as scores.json on Windows.
MISNAMED_MODULE_HASH = "9467ced9caa2d96ff5d177e74ea0c1a4f53aea6112b207998b82e172e2c5c3cd"


class ScoreHistory:
    def __init__(self, path=DEFAULT_PATH):
        self.path = Path(path)
        self.games = []
        self.pending = []
        self.error = ""
        self.refresh()

    def record(self, difficulty, result):
        self.pending.append({
            "id": uuid4().hex,
            "date": datetime.now().astimezone().isoformat(timespec="seconds"),
            "difficulty": difficulty,
            "result": result,
        })
        self.refresh()

    def refresh(self):
        """Reload the file and retry any completed games that could not be saved."""
        try:
            games = self._read()
            if self.pending:
                stored_ids = {game.get("id") for game in games}
                additions = [game for game in self.pending if game["id"] not in stored_ids]
                if additions:
                    games.extend(additions)
                    self._write(games)
                self.pending.clear()
            self.games = games
            self.error = ""
        except ValueError:
            self.error = "Invalid scores.json. Your file was kept."
        except OSError:
            self.error = (
                "Could not save results. Reopen Scoreboard to retry."
                if self.pending else "Could not read scores.json."
            )

    def _read(self):
        try:
            original = self.path.read_bytes()
        except FileNotFoundError:
            return []
        contents = original.decode("utf-8-sig").strip()
        if not contents:
            return []
        normalized = contents.replace("\r\n", "\n")
        if sha256(normalized.encode("utf-8")).hexdigest() == MISNAMED_MODULE_HASH:
            backup = self.path.with_name("scores.json.python-backup")
            try:
                with backup.open("xb") as saved:
                    saved.write(original)
            except FileExistsError:
                if backup.read_bytes() != original:
                    raise ValueError("Score backup already exists")
            self._write([])
            return []

        games = json.loads(contents)
        if not isinstance(games, list) or not all(
            isinstance(game, dict)
            and ("id" not in game or isinstance(game["id"], str))
            and isinstance(game.get("date"), str)
            and isinstance(game.get("difficulty"), str)
            and isinstance(game.get("result"), str)
            and game["result"] in POINTS
            for game in games
        ):
            raise ValueError("Invalid score history")
        return games

    def _write(self, games):
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent, delete=False
            ) as temp:
                temp_path = Path(temp.name)
                json.dump(games, temp, indent=2)
                temp.write("\n")
            temp_path.replace(self.path)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def totals(self):
        totals = dict.fromkeys(POINTS, 0)
        for game in self.games:
            totals[game["result"]] += 1
        points = sum(POINTS[result] * count for result, count in totals.items())
        return totals, points
