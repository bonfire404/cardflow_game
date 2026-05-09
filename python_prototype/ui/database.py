import sqlite3
import os
from ui.paths import get_save_path

DB_PATH = get_save_path("user_profile.db")

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
            rp INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            last_replenish INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            biggest_win INTEGER DEFAULT 0
        )
    ''')

    try:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN last_replenish INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN rp INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN xp INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN level INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN streak INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN biggest_win INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN coins INTEGER DEFAULT 100000")
    except sqlite3.OperationalError:
        pass

    # Enforce exactly one profile row (ID 1)
    cursor.execute("SELECT id FROM user_profile ORDER BY id ASC")
    rows = cursor.fetchall()
    
    if not rows:
        # Create the single mandatory profile row
        cursor.execute('''
            INSERT INTO user_profile (id, name, avatar_idx, wins, losses, coins, rank, rp, xp, level, last_replenish, streak, biggest_win)
            VALUES (1, 'Player', 0, 0, 0, 100000, 'Wood', 0, 0, 1, 0, 0, 0)
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
        "coins": 100000,
        "rank": "Wood",
        "rp": 0,
        "xp": 0,
        "level": 1,
        "last_replenish": 0,
        "streak": 0,
        "biggest_win": 0
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
            # Migrate old 'rank_points' to 'rp' if missing
            if 'rp' not in data and 'rank_points' in data:
                data['rp'] = data['rank_points']
            # Make sure new fields are present
            for k, v in defaults.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception as e:
        print(f"Database load error: {e}")

    return defaults

def update_progression(xp_gain, rp_gain=0):
    """Updates the user's XP and RP, calculates level/rank logic automatically."""
    profile = load_user_profile()
    profile['xp'] += xp_gain
    
    level = 1
    xp_remaining = profile['xp']
    while True:
        if level <= 10:
            req = 1000
        else:
            req = level * 150
            
        if xp_remaining >= req and level < 200:
            xp_remaining -= req
            level += 1
        else:
            break
    profile['level'] = level

    profile['rp'] = max(0, profile['rp'] + rp_gain)
    rp = profile['rp']
    if rp >= 5000:
        profile['rank'] = "Immortal"
    elif rp >= 4000:
        profile['rank'] = "Gold"
    elif rp >= 3000:
        profile['rank'] = "Silver"
    elif rp >= 2000:
        profile['rank'] = "Bronze"
    elif rp >= 1000:
        profile['rank'] = "Iron"
    else:
        profile['rank'] = "Wood"

    save_user_profile(profile)

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
            name = ?, avatar_idx = ?, wins = ?, losses = ?, coins = ?, rank = ?, rp = ?, xp = ?, level = ?, last_replenish = ?, streak = ?, biggest_win = ?
            WHERE id = 1
        ''', (
            stats_dict.get("name", "Player"),
            stats_dict.get("avatar_idx", 0),
            stats_dict.get("wins", 0),
            stats_dict.get("losses", 0),
            stats_dict.get("coins", 100000),
            stats_dict.get("rank", "Wood"),
            stats_dict.get("rp", 0),
            stats_dict.get("xp", 0),
            stats_dict.get("level", 1),
            stats_dict.get("last_replenish", 0),
            stats_dict.get("streak", 0),
            stats_dict.get("biggest_win", 0)
        ))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database save error: {e}")
