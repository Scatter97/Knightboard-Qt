from __future__ import annotations

import chess
from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


PIECES = {
    "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟",
}


class ChessBoardWidget(QWidget):
    """Reusable interactive chessboard for every Knightboard game page."""

    move_played = Signal(object)
    position_changed = Signal(str)

    def __init__(self, board: chess.Board | None = None, parent=None):
        super().__init__(parent)
        self.board = board or chess.Board()
        self.flipped = False
        self.selected: chess.Square | None = None
        self.last_move: chess.Move | None = None
        self.interactive = True
        self.setMinimumSize(420, 420)
        self.setFocusPolicy(Qt.StrongFocus)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(600, 600)

    def set_board(self, board: chess.Board):
        self.board = board
        self.selected = None
        self.last_move = board.peek() if board.move_stack else None
        self.update()
        self.position_changed.emit(board.fen())

    def set_fen(self, fen: str) -> tuple[bool, str]:
        try:
            board = chess.Board(fen)
            if not board.is_valid():
                return False, "The position is not a valid legal chess position."
        except ValueError as error:
            return False, str(error)
        self.set_board(board)
        return True, "Position loaded."

    def flip(self):
        self.flipped = not self.flipped
        self.update()

    def undo(self):
        if self.board.move_stack:
            self.board.pop()
            self.selected = None
            self.last_move = self.board.peek() if self.board.move_stack else None
            self.update()
            self.position_changed.emit(self.board.fen())

    def board_rect(self) -> QRect:
        side = min(self.width(), self.height())
        return QRect((self.width() - side) // 2, (self.height() - side) // 2, side, side)

    def square_at(self, point: QPoint) -> chess.Square | None:
        rect = self.board_rect()
        if not rect.contains(point):
            return None
        cell = rect.width() / 8
        display_file = min(7, int((point.x() - rect.x()) / cell))
        display_rank = min(7, int((point.y() - rect.y()) / cell))
        file_index = 7 - display_file if self.flipped else display_file
        rank_index = display_rank if self.flipped else 7 - display_rank
        return chess.square(file_index, rank_index)

    def display_coords(self, square: chess.Square) -> tuple[int, int]:
        file_index = chess.square_file(square)
        rank_index = chess.square_rank(square)
        if self.flipped:
            return 7 - file_index, rank_index
        return file_index, 7 - rank_index

    def mousePressEvent(self, event):
        if not self.interactive or event.button() != Qt.LeftButton:
            return
        square = self.square_at(event.position().toPoint())
        if square is None:
            return
        if self.selected is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected = square
                self.update()
            return
        move = chess.Move(self.selected, square)
        piece = self.board.piece_at(self.selected)
        if piece and piece.piece_type == chess.PAWN and chess.square_rank(square) in (0, 7):
            move = chess.Move(self.selected, square, promotion=chess.QUEEN)
        if move in self.board.legal_moves:
            self.board.push(move)
            self.last_move = move
            self.selected = None
            self.update()
            self.move_played.emit(move)
            self.position_changed.emit(self.board.fen())
        else:
            target = self.board.piece_at(square)
            self.selected = square if target and target.color == self.board.turn else None
            self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.board_rect()
        cell = rect.width() / 8
        light, dark = QColor("#e6d8b8"), QColor("#6f8255")
        selected, legal, last = QColor("#f6c453"), QColor("#8ecf76"), QColor("#d6b95d")
        legal_targets = set()
        if self.selected is not None:
            legal_targets = {m.to_square for m in self.board.legal_moves if m.from_square == self.selected}
        for square in chess.SQUARES:
            x_index, y_index = self.display_coords(square)
            square_rect = QRect(int(rect.x() + x_index * cell), int(rect.y() + y_index * cell), int(cell + 1), int(cell + 1))
            base = light if (chess.square_file(square) + chess.square_rank(square)) % 2 else dark
            painter.fillRect(square_rect, base)
            if self.last_move and square in (self.last_move.from_square, self.last_move.to_square):
                painter.fillRect(square_rect, last)
            if square == self.selected:
                painter.fillRect(square_rect, selected)
            if square in legal_targets:
                painter.setBrush(legal)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(square_rect.center(), max(5, int(cell * .13)), max(5, int(cell * .13)))
            piece = self.board.piece_at(square)
            if piece:
                painter.setPen(QPen(QColor("#11151b") if piece.color else QColor("#050608")))
                painter.setFont(QFont("Segoe UI Symbol", max(18, int(cell * .68))))
                painter.drawText(square_rect, Qt.AlignCenter, PIECES[piece.symbol()])
        painter.end()
