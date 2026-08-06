import chess

from knightboard.storage import load_config


def test_chess_rules_available():
    board = chess.Board()
    assert len(list(board.legal_moves)) == 20


def test_config_is_mapping():
    assert isinstance(load_config(), dict)
