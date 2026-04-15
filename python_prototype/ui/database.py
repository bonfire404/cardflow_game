import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "user_profile.db")

def init_db():
    """Initializes the SQLite database and migrates data if necessary."""
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the user_profile table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            avatar_idx INTEGER,
            wins INTEGER,
            losses INTEGER,
            coins INTEGER,
            rank TEXT,
            last_replenish INTEGER DEFAULT 0
        )
    ''')

    # Migration: Add last_replenish column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN last_replenish INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Enforce exactly one profile row (ID 1)
    cursor.execute("SELECT id FROM user_profile ORDER BY id ASC")
    rows = cursor.fetchall()
    
    if not rows:
        # Create the single mandatory profile row
        cursor.execute('''
            INSERT INTO user_profile (id, name, avatar_idx, wins, losses, coins, rank, last_replenish)
            VALUES (1, 'Player', 0, 0, 0, 10000, 'Beginner', 0)
        ''')
        conn.commit()
    elif len(rows) > 1:
        # Delete any accidental secondary profiles
        for r in rows[1:]:
            cursor.execute("DELETE FROM user_profile WHERE id = ?", (r[0],))
        conn.commit()

    conn.close()

def load_user_profile():
    """Loads the user profile from the SQLite database."""
    defaults = {
        "name": "Player",
        "avatar_idx": 0,
        "wins": 0,
        "losses": 0,
        "coins": 10000,
        "rank": "Beginner",
        "last_replenish": 0
    }

    if not os.path.exists(DB_PATH):
        init_db()

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profile WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            data = dict(row)
            if 'id' in data: del data['id']
            return data
    except Exception as e:
        print(f"Database load error: {e}")

    return defaults

def save_user_profile(stats_dict):
    """Saves the user profile to the SQLite database."""
    if not os.path.exists(DB_PATH):
        init_db()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Update the single profile row (ID 1)
        cursor.execute('''
            UPDATE user_profile SET
            name = ?, avatar_idx = ?, wins = ?, losses = ?, coins = ?, rank = ?, last_replenish = ?
            WHERE id = 1
        ''', (
            stats_dict.get("name", "Player"),
            stats_dict.get("avatar_idx", 0),
            stats_dict.get("wins", 0),
            stats_dict.get("losses", 0),
            stats_dict.get("coins", 10000),
            stats_dict.get("rank", "Beginner"),
            stats_dict.get("last_replenish", 0)
        ))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database save error: {e}")
