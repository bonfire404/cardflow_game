# 🃏 Cardflow — Complete Setup & Build Guide

> This guide walks you through everything you need to run, test, and build the Cardflow game from scratch. Follow each section in order.

---

## 📋 Before You Start (Prerequisites)

Make sure you have these installed on your computer:

| Software | Version | How to Check | Download |
| :--- | :--- | :--- | :--- |
| **Python** | 3.14 or higher | Open terminal → type `python.exe --version` | [python.org](https://www.python.org/downloads/) |
| **Git Bash** | Any version | Should already be installed | [git-scm.com](https://git-scm.com/) |

> ⚠️ **IMPORTANT**: Throughout this guide, always use `python.exe` instead of `python` when typing commands in Git Bash. This is because our Windows username has a space in it ("BONFIRE BASE"), and `python` will break in Git Bash. Using `python.exe` avoids this problem entirely.

---

## 🔧 Step 1: Install Dependencies

Open **Git Bash** and navigate to the project folder:

```bash
cd /c/Users/Project/cardflow_game
```

Then install the game's only external dependency — **pygame-ce** (Community Edition):

```bash
python.exe -m pip install pygame-ce
```

You should see output ending with:
```
Successfully installed pygame-ce-2.5.7
```

> 💡 **What is pygame-ce?** It's the game engine library that handles graphics, sound, and input. We use the "Community Edition" because the original `pygame` doesn't support Python 3.14 yet.

---

## 🎮 Step 2: Run the Game (Development Mode)
This is how you play the game while you're still developing it. No building needed — it runs directly from your source code.

```bash
python.exe -m python_prototype.ui.main
```

The game window should appear in fullscreen. Press `Alt+F4` or use the in-game menu to quit.

> 💡 **When to use this:** Every time you want to test changes you've made to the code. This is the fastest way to see your changes in action.

---

## 📦 Step 3: Build for Production (Create the .EXE)

When you're ready to share the game (e.g., submit for school, upload to itch.io), you need to build a standalone `.exe` file that runs on any Windows PC — even without Python installed.

### 3A. Install PyInstaller (One-Time Only)

```bash
python.exe -m pip install pyinstaller
```

### 3B. Generate the Security Manifest

This scans all critical game files and creates a "fingerprint" of each one. When the game starts, it checks these fingerprints to make sure no one has tampered with the files.

```bash
python.exe -m python_prototype.generate_manifest
```

You should see output like this:
```
==================================================
  Cardflow Integrity Manifest Generator
==================================================

Scanning critical files...
  [OK] python_prototype\game\engine.py
  [OK] python_prototype\game\ai_bot.py
  [OK] python_prototype\game\economy.py
  ... (more files)

Manifest saved to: integrity.manifest
Total files protected: 7
```

> ⚠️ **IMPORTANT**: You MUST run this command every time before building. If you skip this step, the security integrity checks won't work in your final EXE.

### 3C. Build the EXE

```bash
pyinstaller --clean --noconfirm Cardflow.spec
```

This will take 1-3 minutes. When it finishes, you'll see:
```
Building EXE from EXE-00.toc completed successfully.
```

### 3D. Find Your Game

Your finished game is located at:

```
cardflow_game/
  └── dist/
      └── Cardflow.exe   ← This is your game! (double-click to play)
```

You can copy `Cardflow.exe` to any Windows computer and it will run — no Python installation needed.

---

## 🔒 Security Features

The game includes three layers of protection to prevent cheating and code theft:

### Layer 1: HMAC-Signed Save Files
**What it does:** Every time the game saves your profile (coins, rank, wins), it creates a cryptographic signature alongside it.

**How it protects you:** If someone opens the save database with a tool like "DB Browser for SQLite" and changes their coins from 1,000 to 999,999,999 — the game will detect the tampering on next launch and **reset their profile back to defaults** (100,000 coins).

### Layer 2: SHA-256 File Integrity Checks
**What it does:** Before building the EXE (Step 3B above), we generate a "fingerprint" (SHA-256 hash) of every critical game file.

**How it protects you:** If someone extracts the EXE and modifies `ai_bot.py` or `engine.py` to cheat, the fingerprints won't match and the game will flag it.

**Files that are protected:**
- `engine.py` — The Tong-Its game rules
- `ai_bot.py` — The AI bot's decision-making brain
- `economy.py` — The coin economy system
- `betting_configs.py` — Bet amounts and limits
- `database.py` — How profiles are stored
- `progression_manager.py` — XP, leveling, and ranking
- `chips.py` — The chip/betting visuals

### Layer 3: Anti-Debug Detection
**What it does:** Checks if someone is running the game inside a debugger or code inspection tool (like pdb or PyCharm's debugger).

**How it protects you:** Makes it harder for someone to step through your code line-by-line to understand how it works.

---

## 🔁 Quick Reference — Command Cheat Sheet

| What you want to do | Command |
| :--- | :--- |
| **Install dependencies** | `python.exe -m pip install pygame-ce` |
| **Play the game (dev mode)** | `python.exe -m python_prototype.ui.main` |
| **Generate security manifest** | `python.exe -m python_prototype.generate_manifest` |
| **Build the EXE** | `pyinstaller --clean --noconfirm Cardflow.spec` |

### Full Production Build (copy-paste all 3 lines):
```bash
python.exe -m python_prototype.generate_manifest
pyinstaller --clean --noconfirm Cardflow.spec
echo "Done! Your game is at dist/Cardflow.exe"
```

---

## ❓ Troubleshooting

| Problem | What You See | How to Fix |
| :--- | :--- | :--- |
| **pygame not installed** | `ModuleNotFoundError: No module named 'pygame'` | Run `python.exe -m pip install pygame-ce` |
| **Path error in Git Bash** | `bash: /c/Users/BONFIRE: Is a directory` | Use `python.exe` instead of `python` |
| **Save tampering detected** | `[Security] Save data tampering detected!` | This means someone edited the save file. Profile was auto-reset to defaults. |
| **Deprecation warning** | `DeprecationWarning: pygame.image.fromstring` | Ignore this — it does not affect the game at all |
| **PyInstaller not found** | `pyinstaller: command not found` | Run `python.exe -m pip install pyinstaller` first |
| **Manifest missing** | No `integrity.manifest` file | Run `python.exe -m python_prototype.generate_manifest` |
