================================================================================
                           CARDFLOW  (BACKEND)
================================================================================


PRODUCT INFORMATION
-------------------
  Title:        CardFlow
  Developer:    BONFIRE BASE Studio
  Publisher:    BONFIRE BASE Studio


================================================================================

OVERVIEW
--------
CardFlow is a digital implementation of the traditional Filipino card game
Tong-its, produced by BONFIRE BASE Studio.

This backend package contains the core game engine, AI logic, economy system,
data persistence, and security modules.


BACKEND ARCHITECTURE
--------------------
The backend is organized under the "python_prototype" directory and is split
into three main layers:

  1. GAME LOGIC (python_prototype/game/)
     - engine.py          Core Tong-its rules, turn flow, and win conditions
     - models.py          Data models (Card, Deck, Player, Meld, TableMeld)
     - ai_bot.py          Rule-based AI with strategic play-style simulation
     - economy.py         Coin economy, pot management, and payout resolution
     - betting_configs.py Bet levels, modes (Hitter / Aggressive / Sustained)

  2. DATA & PERSISTENCE (python_prototype/ui/)
     - database.py        SQLite CRUD for user profiles and match history
     - progression_manager.py  XP, leveling, and rank progression logic
     - crypto_utils.py    File encryption/decryption (machine-bound XOR cipher)
     - security.py        HMAC signing, SHA-256 integrity, anti-debug checks
     - paths.py           Cross-platform path resolution for save data

  3. LOCAL DATA FILES (python_prototype/db/)
     - user_profile.db    SQLite database for player profile and match history
     - profile.sig        HMAC signature file for tamper detection
     - achievements.json  Achievement definitions and progress
     - quests.json        Quest definitions and tracking
     - settings.json      User preferences (audio, display, etc.)

DATA STACK USED:

  The backend uses two data formats for local file-based persistence.
  No external database server is used — all data lives as local files
  on the user's machine.

  SQLite (Local File-Based Storage)
    Used for structured, relational data that requires querying and updating.
    Player profiles (name, coins, rank, wins, losses, XP, level) and match
    history records are stored in an SQLite file (user_profile.db).

    IMPORTANT: SQLite is NOT a traditional database server. It is a
    serverless, zero-configuration, single-file storage engine that is
    part of the Python standard library. There is no database server
    running, no network connection, and no installation required.
    The entire database is a single local file (user_profile.db) read
    and written directly by the application — functionally identical
    to reading/writing a JSON or TXT file, but with the added benefit
    of SQL queries for structured data like match history records.

    SQLite was chosen over plain JSON for profile data because:
      - Player profiles require frequent partial updates (e.g., updating
        only the coin balance after a match, not rewriting the entire file)
      - Match history is an append-only log that benefits from SQL queries
        (e.g., "get the last 10 matches sorted by date")
      - SQLite handles concurrent read/write safely, preventing data
        corruption if the game crashes mid-save

  JSON (Configuration Files)
    Used for flat configuration and definition data that does not require
    complex queries. Achievement definitions, quest tracking, and user
    settings (audio volume, display preferences) are stored as JSON files.
    JSON was chosen for its human-readable structure and simplicity for
    data that is loaded once at startup and saved on change.


================================================================================

ABOUT THE "db" FOLDER (python_prototype/db/)
---------------------------------------------
The "db" folder contains the application's local save data and configuration
files.

You may notice that some files in this folder appear as unreadable binary data
rather than plain text. This is intentional and expected behavior.

WHY THE FILES LOOK ENCRYPTED:

  The game implements a multi-layer security system to protect users and ensure
  fair gameplay. All save data files are encrypted at rest using a machine-bound
  XOR stream cipher. This means:

  1. ANTI-CHEAT PROTECTION
     Player profiles (coins, rank, wins, level) are stored in an SQLite
     database (user_profile.db) that is encrypted after every save operation.
     This prevents players from manually editing their coin balance, rank,
     or win count using tools like "DB Browser for SQLite."

  2. TAMPER DETECTION (HMAC Signing)
     Every time the game saves a profile, it generates an HMAC-SHA256
     cryptographic signature (profile.sig) alongside the database. When
     the game loads, it re-computes the signature and compares it against
     the stored one. If any value has been modified outside the game, the
     mismatch is detected and the profile is automatically reset to
     default values.

  3. MACHINE-BOUND ENCRYPTION
     The encryption key is derived from the machine's identity, meaning
     save files cannot simply be copied to another computer to bypass
     security. Each installation produces uniquely encrypted data.

  4. USER DATA SAFETY
     Encryption ensures that sensitive user data (play history, settings,
     progression) is not exposed as plain text on disk, protecting user
     privacy even if the files are accessed outside the application.

FILES IN THIS FOLDER:

  user_profile.db    Player profile and match history (encrypted SQLite)
  profile.sig        HMAC-SHA256 signature for tamper detection (encrypted)
  achievements.json  Achievement definitions and progress tracking
  quests.json        Quest definitions and completion status
  settings.json      User preferences (audio volume, display options)

NOTE:
  The game automatically decrypts these files at runtime when it needs to
  read or write data, and re-encrypts them immediately after. They do not
  need to be decrypted manually. The data structure and security logic are
  documented in the database.py and security.py source files.

  Running the game at least once will generate the save files fresh on the
  local machine in a readable-then-encrypted cycle.


================================================================================

PLAYING THE GAME
----------------
A live build of the game is available for play and demonstration:

  Project Link:  https://bonfire69.itch.io/cardflow

The live version represents the most recent stable release.



INTELLECTUAL PROPERTY NOTICE
-----------------------------
CardFlow is the property of BONFIRE BASE Studio.

Certain proprietary assets, tools, infrastructure, and supporting systems remain
the intellectual property of BONFIRE BASE Studio and are not included in this
package.


================================================================================

CONTACT
-------
For full code requests you can contact BONFIRE BASE Studio directly:
https://bonfire.base69.studio


================================================================================

                  (c) 2026 BONFIRE BASE Studio. All Rights Reserved.

================================================================================
