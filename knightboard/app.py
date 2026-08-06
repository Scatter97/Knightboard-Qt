from __future__ import annotations

import random
import sys

import chess
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget


class KnightboardApp(QWidget):
    FEATURES = (
        ("RECORD OTB GAME", "record", "Camera recording, clocks, and PGN."),
        ("GAME HISTORY", "history", "Saved games, review, and accuracy."),
        ("CHESS960", "chess960", "Generate a legal randomized starting position."),
        ("OPENING EXPLORER", "opening", "Offline opening names and move explorer."),
        ("ENDGAME EXPLORER", "endgame", "FEN positions and local tablebases."),
        ("SETTINGS & LIBRARIES", "settings", "Camera, engine, and offline libraries."),
        ("VIRTUAL BOT GAME", "virtual_bot", "Play an offline game against a bot."),
        ("OTB BOT GAME", "otb_bot", "Play on a real board with bot assistance."),
    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Knightboard")
        self.resize(1050, 740)
        self.setMinimumSize(850, 600)
        self.pages = {}
        self.stack = QStackedWidget()
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 25, 30, 25)
        header = QHBoxLayout()
        brand = QLabel("KNIGHTBOARD")
        brand.setObjectName("brand")
        brand.setFont(QFont("Arial", 22, QFont.Bold))
        header.addWidget(brand)
        header.addStretch()
        header.addWidget(QLabel("OFFLINE CHESS STUDIO  •  Qt rebuild"))
        root.addLayout(header)
        self.pages["home"] = self.build_home()
        self.stack.addWidget(self.pages["home"])
        root.addWidget(self.stack, 1)
        self.setStyleSheet("""
            QWidget { background:#10131a; color:#eef2f7; }
            QLabel#brand { color:#f6c453; letter-spacing:2px; }
            QLabel#title { font-size:28px; font-weight:700; }
            QLabel#muted { color:#aab4c3; }
            QFrame#card { background:#191e28; border:1px solid #2b3443; border-radius:12px; }
            QPushButton { background:#202938; border:1px solid #344258; border-radius:9px; color:#f2f5f8; padding:15px; text-align:left; font-size:14px; }
            QPushButton:hover { background:#2a3850; border-color:#f6c453; }
            QPushButton#primary { background:#f6c453; color:#16191f; font-weight:700; }
        """)

    def build_home(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Your offline chess studio")
        title.setObjectName("title")
        layout.addWidget(title)
        subtitle = QLabel("Every feature opens inside this one Knightboard window.")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)
        grid = QGridLayout()
        for index, (label, key, description) in enumerate(self.FEATURES):
            button = QPushButton(f"{label}\\n{description}")
            button.setMinimumHeight(78)
            button.clicked.connect(lambda checked=False, item=key: self.show_page(item))
            grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(grid)
        layout.addStretch()
        return page

    def show_page(self, key):
        if key not in self.pages:
            self.pages[key] = self.build_chess960() if key == "chess960" else self.build_feature(key)
            self.stack.addWidget(self.pages[key])
        self.stack.setCurrentWidget(self.pages[key])

    def base_page(self, key):
        label, _, description = next(item for item in self.FEATURES if item[1] == key)
        page = QWidget()
        layout = QVBoxLayout(page)
        back = QPushButton("←  Back to main menu")
        back.setObjectName("primary")
        back.setMaximumWidth(220)
        back.clicked.connect(lambda: self.show_page("home"))
        layout.addWidget(back, 0, Qt.AlignLeft)
        title = QLabel(label)
        title.setObjectName("title")
        layout.addWidget(title)
        text = QLabel(description)
        text.setObjectName("muted")
        layout.addWidget(text)
        return page, layout

    def build_feature(self, key):
        page, layout = self.base_page(key)
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        message = QLabel("This Qt-native feature is next in the rebuild.")
        message.setObjectName("muted")
        card_layout.addWidget(message)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def build_chess960(self):
        page, layout = self.base_page("chess960")
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        position = QLabel()
        position.setObjectName("title")
        board_view = QLabel()
        board_view.setFont(QFont("Consolas", 18))
        board_view.setAlignment(Qt.AlignCenter)
        board_view.setStyleSheet("background:#0d1118; border:1px solid #344258; padding:16px;")
        fen = QLabel()
        fen.setObjectName("muted")
        generate = QPushButton("GENERATE ANOTHER POSITION")
        generate.setObjectName("primary")
        def refresh():
            number = random.randrange(960)
            board = chess.Board.from_chess960_pos(number)
            pieces = {"r":"♜","n":"♞","b":"♝","q":"♛","k":"♚","p":"♟","R":"♖","N":"♘","B":"♗","Q":"♕","K":"♔","P":"♙"}
            rows = []
            for rank in range(7, -1, -1):
                rows.append(f"{rank + 1}  " + "  ".join(pieces.get(piece.symbol(), "·") if (piece := board.piece_at(rank * 8 + file)) else "·" for file in range(8)))
            rows.append("   a  b  c  d  e  f  g  h")
            position.setText(f"Position #{number}")
            board_view.setText("\\n".join(rows))
            fen.setText(f"FEN: {board.fen()}")
        generate.clicked.connect(refresh)
        refresh()
        for widget in (position, board_view, fen, generate): card_layout.addWidget(widget)
        layout.addWidget(card)
        layout.addStretch()
        return page


def main():
    app = QApplication(sys.argv)
    window = KnightboardApp()
    window.show()
    sys.exit(app.exec())
