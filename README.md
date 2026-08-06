# Knightboard

Knightboard is an offline-first chess client rebuilt from the ground up with Qt.

## Status

The current Qt-native foundation includes single-window navigation, an interactive chessboard, PGN history and saving, Chess960, opening and endgame explorers, local Syzygy probing, settings, virtual/OTB bot game boards, and an embedded camera preview. OpenCV is used only for camera frame processing, never for visible application windows.

## Run

```powershell
python -m pip install -r requirements.txt
python -m knightboard
```

On Windows you can also run `run_windows.bat`.
