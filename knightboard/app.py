from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from .pages import CameraPage, Chess960Page, EndgamePage, HistoryPage, LocalGamePage, OpeningPage, SettingsPage


class KnightboardApp(QWidget):
    FEATURES = (
        ("RECORD OTB GAME", "record", "Camera recording, clocks, and PGN."),
        ("GAME HISTORY", "history", "Saved games, review, and accuracy."),
        ("CHESS960", "chess960", "Generate a legal randomized starting position."),
        ("OPENING EXPLORER", "opening", "Offline opening names and legal moves."),
        ("ENDGAME EXPLORER", "endgame", "FEN positions and local Syzygy tablebases."),
        ("SETTINGS & LIBRARIES", "settings", "Camera, engine, and offline libraries."),
        ("VIRTUAL BOT GAME", "virtual_bot", "Play an offline game against a bot."),
        ("OTB BOT GAME", "otb_bot", "Play on a real board with bot assistance."),
    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Knightboard")
        self.resize(1100, 780)
        self.setMinimumSize(900, 650)
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
        header.addWidget(QLabel("OFFLINE CHESS STUDIO  •  Qt"))
        root.addLayout(header)
        self.pages["home"] = self.build_home()
        self.stack.addWidget(self.pages["home"])
        root.addWidget(self.stack, 1)
        self.setStyleSheet("""
            QWidget { background:#10131a; color:#eef2f7; }
            QLabel#brand { color:#f6c453; letter-spacing:2px; }
            QLabel#title { font-size:27px; font-weight:700; }
            QLabel#muted { color:#aab4c3; }
            QFrame#card { background:#191e28; border:1px solid #2b3443; border-radius:12px; }
            QPushButton { background:#202938; border:1px solid #344258; border-radius:9px; color:#f2f5f8; padding:14px; text-align:left; font-size:14px; }
            QPushButton:hover { background:#2a3850; border-color:#f6c453; }
            QPushButton#primary { background:#f6c453; color:#16191f; font-weight:700; }
            QLineEdit, QListWidget, QComboBox, QSpinBox { background:#0d1118; border:1px solid #344258; border-radius:6px; padding:9px; }
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
            button = QPushButton(f"{label}\n{description}")
            button.setMinimumHeight(78)
            button.clicked.connect(lambda checked=False, item=key: self.show_page(item))
            grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(grid)
        layout.addStretch()
        return page

    def show_page(self, key):
        if key == "home":
            self.stack.setCurrentWidget(self.pages["home"])
            return
        if key not in self.pages:
            home = lambda: self.show_page("home")
            factories = {
                "record": lambda: CameraPage(home),
                "history": lambda: HistoryPage(home),
                "chess960": lambda: Chess960Page(home),
                "opening": lambda: OpeningPage(home),
                "endgame": lambda: EndgamePage(home),
                "settings": lambda: SettingsPage(home),
                "virtual_bot": lambda: LocalGamePage("VIRTUAL BOT GAME", "Play offline against the Knightboard bot.", home, bot=True),
                "otb_bot": lambda: LocalGamePage("OTB BOT GAME", "Play and record a physical-board bot game.", home, bot=True),
            }
            self.pages[key] = factories[key]()
            self.stack.addWidget(self.pages[key])
        if key == "history":
            self.pages[key].reload()
        self.stack.setCurrentWidget(self.pages[key])

    def closeEvent(self, event):
        page = self.pages.get("record")
        if page:
            page.stop_camera()
        super().closeEvent(event)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = KnightboardApp()
    window.show()
    return app.exec()
