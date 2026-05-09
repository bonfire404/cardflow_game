# Cardflow - Developer Guide

## 1. Development Mode
To run the game during development:
```bash
python -m python_prototype.ui.main
```

---

## 2. Production Builds

### A. Protected Build (Recommended for itch.io)
This obfuscates your core logic (Engine, AI, Database) to prevent code theft.
```bash
# Step 1: Obfuscate core files
pyarmor gen -O build/obfuscated python_prototype/game/engine.py python_prototype/game/ai_bot.py python_prototype/ui/database.py python_prototype/ui/progression_manager.py

# Step 2: Assemble and Build
pyinstaller --clean --noconfirm Cardflow_protected.spec
```
*   **Protection**: Code is scrambled and unreadable.
*   **Branding**: Custom taskbar icon and window icon embedded.
*   **Output**: `dist/Cardflow.exe`

### B. Fast Build (For Internal Testing)
Quickly generates an EXE without obfuscation.
```bash
pyinstaller --clean --noconfirm Cardflow.spec
```

---

## 3. Important Notes
*   **Starting Coins**: Set to **100,000**.
*   **Level Locking**: Rank mode is locked based on player level (implemented in `lobby.py`).
*   **Branding**: The Windows taskbar icon fix is applied in `main.py` before `pygame.init()`.
