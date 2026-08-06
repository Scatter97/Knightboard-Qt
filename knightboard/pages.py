from __future__ import annotations

import random
from datetime import date
from pathlib import Path

import chess
import chess.pgn
import chess.syzygy
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from .board import ChessBoardWidget
from .storage import load_config, load_games, save_config, save_game


class FeaturePage(QWidget):
    def __init__(self, title: str, description: str, go_home):
        super().__init__()
        self.layout = QVBoxLayout(self)
        back = QPushButton("←  Back to main menu")
        back.setObjectName("primary")
        back.setMaximumWidth(220)
        back.clicked.connect(go_home)
        self.layout.addWidget(back, 0, Qt.AlignLeft)
        heading = QLabel(title)
        heading.setObjectName("title")
        self.layout.addWidget(heading)
        text = QLabel(description)
        text.setObjectName("muted")
        text.setWordWrap(True)
        self.layout.addWidget(text)

    def card(self):
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 22, 22, 22)
        self.layout.addWidget(frame, 1)
        return layout


class HistoryPage(FeaturePage):
    def __init__(self, go_home):
        super().__init__("GAME HISTORY", "Saved PGN games stay on this device.", go_home)
        area = self.card()
        self.games = QListWidget()
        self.games.itemDoubleClicked.connect(self.open_game)
        refresh = QPushButton("REFRESH HISTORY")
        refresh.clicked.connect(self.reload)
        area.addWidget(self.games)
        area.addWidget(refresh)
        self.reload()

    def reload(self):
        self.games.clear()
        for path, game in load_games():
            h = game.headers
            item = f"{h.get('White','White')} vs {h.get('Black','Black')}  •  {h.get('Result','*')}  •  {h.get('Date','')}"
            self.games.addItem(item)
            self.games.item(self.games.count() - 1).setData(Qt.UserRole, str(path))
        if not self.games.count():
            self.games.addItem("No games saved yet.")

    def open_game(self, item):
        path = item.data(Qt.UserRole)
        if not path:
            return
        QMessageBox.information(self, "PGN", Path(path).read_text(encoding="utf-8", errors="replace"))


class Chess960Page(FeaturePage):
    def __init__(self, go_home):
        super().__init__("CHESS960", "Generate any legal Chess960 starting position.", go_home)
        area = self.card()
        self.board_widget = ChessBoardWidget()
        self.board_widget.interactive = False
        self.status = QLabel()
        self.status.setObjectName("muted")
        generate = QPushButton("GENERATE ANOTHER POSITION")
        generate.setObjectName("primary")
        generate.clicked.connect(self.generate)
        area.addWidget(self.board_widget)
        area.addWidget(self.status)
        area.addWidget(generate)
        self.generate()

    def generate(self):
        number = random.randrange(960)
        board = chess.Board.from_chess960_pos(number)
        self.board_widget.set_board(board)
        self.status.setText(f"Position #{number}  •  FEN: {board.fen()}")


class EndgamePage(FeaturePage):
    DEFAULT_FEN = "7k/8/8/8/8/8/4K3/5Q2 w - - 0 1"

    def __init__(self, go_home):
        super().__init__("ENDGAME EXPLORER", "Edit FEN positions and probe local Syzygy tablebases offline.", go_home)
        area = self.card()
        self.board_widget = ChessBoardWidget(chess.Board(self.DEFAULT_FEN))
        self.fen = QLineEdit(self.DEFAULT_FEN)
        self.result = QLabel("Choose a tablebase folder in Settings to enable exact probing.")
        self.result.setObjectName("muted")
        buttons = QHBoxLayout()
        load = QPushButton("LOAD FEN")
        clear = QPushButton("SAMPLE POSITION")
        probe = QPushButton("PROBE TABLEBASE")
        load.clicked.connect(self.load_fen)
        clear.clicked.connect(self.sample)
        probe.clicked.connect(self.probe)
        for button in (load, clear, probe): buttons.addWidget(button)
        area.addWidget(self.fen)
        area.addLayout(buttons)
        area.addWidget(self.board_widget)
        area.addWidget(self.result)

    def load_fen(self):
        ok, message = self.board_widget.set_fen(self.fen.text())
        self.result.setText(message)

    def sample(self):
        self.fen.setText(self.DEFAULT_FEN)
        self.load_fen()

    def probe(self):
        path = load_config().get("tablebase_path")
        if not path:
            self.result.setText("Select a Syzygy folder in Settings first.")
            return
        board = self.board_widget.board
        if len(board.piece_map()) > 7:
            self.result.setText("Syzygy supports positions with up to seven pieces.")
            return
        try:
            with chess.syzygy.open_tablebase(path) as tablebase:
                wdl = tablebase.probe_wdl(board)
                dtz = tablebase.probe_dtz(board)
            label = {2:"Win",1:"Cursed win",0:"Draw",-1:"Blessed loss",-2:"Loss"}.get(wdl,"Unknown")
            self.result.setText(f"Exact result for side to move: {label}  •  DTZ {dtz:+d}")
        except Exception as error:
            self.result.setText(f"Tablebase unavailable for this position: {error}")


class OpeningPage(FeaturePage):
    OPENINGS = {
        "": "Starting position",
        "e4": "King's Pawn Game", "d4": "Queen's Pawn Game", "c4": "English Opening", "Nf3": "Réti Opening",
        "e4 e5": "Open Game", "e4 c5": "Sicilian Defence", "e4 e6": "French Defence", "e4 c6": "Caro-Kann Defence",
        "d4 d5": "Closed Game", "d4 Nf6": "Indian Game", "e4 e5 Nf3 Nc6 Bb5": "Ruy Lopez",
        "e4 e5 Nf3 Nc6 Bc4": "Italian Game", "d4 d5 c4": "Queen's Gambit",
    }

    def __init__(self, go_home):
        super().__init__("OPENING EXPLORER", "Explore common opening names and legal continuations offline.", go_home)
        area = self.card()
        self.board_widget = ChessBoardWidget()
        self.board_widget.move_played.connect(self.update_opening)
        self.name = QLabel("Starting position")
        self.name.setObjectName("title")
        self.moves = QLabel()
        self.moves.setObjectName("muted")
        reset = QPushButton("RESET OPENING")
        reset.clicked.connect(self.reset)
        area.addWidget(self.name)
        area.addWidget(self.board_widget)
        area.addWidget(self.moves)
        area.addWidget(reset)
        self.update_opening()

    def update_opening(self, *_):
        replay = chess.Board()
        san = []
        for move in self.board_widget.board.move_stack:
            san.append(replay.san(move)); replay.push(move)
        key = " ".join(san)
        self.name.setText(self.OPENINGS.get(key, "Uncatalogued position"))
        legal = [self.board_widget.board.san(move) for move in list(self.board_widget.board.legal_moves)[:12]]
        self.moves.setText(f"Moves: {key or '—'}\nLegal continuations: {', '.join(legal)}")

    def reset(self):
        self.board_widget.set_board(chess.Board())
        self.update_opening()


class LocalGamePage(FeaturePage):
    def __init__(self, title, description, go_home, bot=False):
        super().__init__(title, description, go_home)
        self.bot = bot
        self.game = chess.pgn.Game()
        self.game.headers.update({"Event": title.title(), "Date": date.today().strftime("%Y.%m.%d"), "White":"White", "Black":"Knightboard Bot" if bot else "Black"})
        self.node = self.game
        area = self.card()
        self.board_widget = ChessBoardWidget()
        self.board_widget.move_played.connect(self.moved)
        self.status = QLabel("White to move")
        self.status.setObjectName("muted")
        row = QHBoxLayout()
        undo = QPushButton("UNDO")
        flip = QPushButton("FLIP BOARD")
        save = QPushButton("SAVE PGN")
        resign = QPushButton("RESIGN")
        undo.clicked.connect(self.board_widget.undo)
        flip.clicked.connect(self.board_widget.flip)
        save.clicked.connect(self.save)
        resign.clicked.connect(self.resign)
        for button in (undo, flip, save, resign): row.addWidget(button)
        area.addWidget(self.board_widget)
        area.addWidget(self.status)
        area.addLayout(row)

    def moved(self, move):
        self.node = self.node.add_variation(move)
        board = self.board_widget.board
        if board.is_game_over():
            self.game.headers["Result"] = board.result()
            self.status.setText(f"Game over: {board.result()}")
            return
        if self.bot and board.turn == chess.BLACK:
            QTimer.singleShot(450, self.bot_move)
        else:
            self.status.setText(f"{'White' if board.turn else 'Black'} to move")

    def bot_move(self):
        board = self.board_widget.board
        if board.is_game_over(): return
        move = random.choice(list(board.legal_moves))
        board.push(move)
        self.node = self.node.add_variation(move)
        self.board_widget.last_move = move
        self.board_widget.update()
        self.status.setText(f"Bot played {move.uci()}  •  White to move")

    def save(self):
        self.game.headers["Result"] = self.board_widget.board.result(claim_draw=True)
        path = save_game(self.game)
        self.status.setText(f"Saved to {path}")

    def resign(self):
        self.game.headers["Result"] = "0-1" if self.board_widget.board.turn else "1-0"
        self.status.setText(f"Resigned. Result {self.game.headers['Result']}")


class SettingsPage(FeaturePage):
    def __init__(self, go_home):
        super().__init__("SETTINGS & LIBRARIES", "Configure offline engines, tablebases, camera, and appearance.", go_home)
        area = self.card()
        form = QFormLayout()
        config = load_config()
        self.stockfish = QLineEdit(config.get("stockfish_path", ""))
        self.tablebase = QLineEdit(config.get("tablebase_path", ""))
        self.camera = QSpinBox(); self.camera.setRange(0, 20); self.camera.setValue(int(config.get("camera_index", 0)))
        self.theme = QComboBox(); self.theme.addItems(["Knightboard Dark", "High Contrast"])
        engine_pick = QPushButton("CHOOSE STOCKFISH")
        table_pick = QPushButton("CHOOSE TABLEBASE FOLDER")
        engine_pick.clicked.connect(self.pick_engine)
        table_pick.clicked.connect(self.pick_tablebase)
        form.addRow("Stockfish", self.stockfish); form.addRow("", engine_pick)
        form.addRow("Syzygy", self.tablebase); form.addRow("", table_pick)
        form.addRow("Camera index", self.camera); form.addRow("Theme", self.theme)
        save = QPushButton("SAVE SETTINGS"); save.setObjectName("primary"); save.clicked.connect(self.save)
        area.addLayout(form); area.addWidget(save)

    def pick_engine(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Stockfish")
        if path: self.stockfish.setText(path)

    def pick_tablebase(self):
        path = QFileDialog.getExistingDirectory(self, "Choose Syzygy folder")
        if path: self.tablebase.setText(path)

    def save(self):
        config = load_config(); config.update({"stockfish_path":self.stockfish.text(), "tablebase_path":self.tablebase.text(), "camera_index":self.camera.value(), "theme":self.theme.currentText()}); save_config(config)
        QMessageBox.information(self, "Knightboard", "Settings saved.")


class CameraPage(FeaturePage):
    def __init__(self, go_home):
        super().__init__("RECORD OTB GAME", "Camera preview stays inside Knightboard. OpenCV is used only for frame capture.", go_home)
        self.capture = None
        self.timer = QTimer(self); self.timer.timeout.connect(self.read_frame)
        area = self.card()
        self.preview = QLabel("Camera is stopped")
        self.preview.setAlignment(Qt.AlignCenter); self.preview.setMinimumHeight(420)
        self.status = QLabel("Select Start Camera to begin calibration and detection preview."); self.status.setObjectName("muted")
        row = QHBoxLayout()
        start = QPushButton("START CAMERA"); stop = QPushButton("STOP CAMERA")
        start.clicked.connect(self.start_camera); stop.clicked.connect(self.stop_camera)
        row.addWidget(start); row.addWidget(stop)
        area.addWidget(self.preview); area.addWidget(self.status); area.addLayout(row)

    def start_camera(self):
        try:
            import cv2
            self.capture = cv2.VideoCapture(int(load_config().get("camera_index", 0)))
            if not self.capture.isOpened(): raise RuntimeError("Camera could not be opened")
            self.timer.start(33); self.status.setText("Live camera preview • detection backend ready")
        except Exception as error: self.status.setText(str(error))

    def read_frame(self):
        import cv2
        ok, frame = self.capture.read() if self.capture else (False, None)
        if not ok: return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format_RGB888).copy()
        self.preview.setPixmap(QPixmap.fromImage(image).scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def stop_camera(self):
        self.timer.stop()
        if self.capture: self.capture.release(); self.capture = None
        self.preview.setText("Camera is stopped")

    def closeEvent(self, event):
        self.stop_camera(); super().closeEvent(event)
