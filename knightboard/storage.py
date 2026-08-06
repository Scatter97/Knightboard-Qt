from __future__ import annotations

import json
from pathlib import Path

import chess.pgn


DATA_DIR = Path.home() / ".knightboard"
GAMES_DIR = DATA_DIR / "games"
CONFIG_PATH = DATA_DIR / "config.json"


def ensure_dirs():
    GAMES_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_dirs()
    try:
        value = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(config: dict):
    ensure_dirs()
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def save_game(game: chess.pgn.Game) -> Path:
    ensure_dirs()
    stem = game.headers.get("Date", "game").replace(".", "-")
    path = GAMES_DIR / f"{stem}-{len(list(GAMES_DIR.glob('*.pgn'))) + 1}.pgn"
    path.write_text(str(game), encoding="utf-8")
    return path


def load_games():
    ensure_dirs()
    games = []
    for path in sorted(GAMES_DIR.glob("*.pgn"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with path.open(encoding="utf-8", errors="replace") as handle:
                game = chess.pgn.read_game(handle)
            if game:
                games.append((path, game))
        except OSError:
            continue
    return games
