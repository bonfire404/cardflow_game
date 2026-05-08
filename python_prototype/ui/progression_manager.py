import random
from ui.database import update_progression

RANKS = ["Wood", "Iron", "Bronze", "Silver", "Gold", "Immortal"]

def get_match_rewards(is_win, is_tongits=False, bet_limit=100):
    """Returns (xp, rp) based on match result and bet limit."""
    # Calculate RP multiplier based on bet limit or difficulty
    if isinstance(bet_limit, str):
        if bet_limit == "EASY":
            mult = 1.0
        elif bet_limit == "MEDIUM":
            mult = 1.5
        elif bet_limit == "HARD":
            mult = 2.0
        else:
            mult = 1.0
    else:
        if bet_limit <= 100:
            mult = 1.0
        elif bet_limit <= 300:
            mult = 1.5
        elif bet_limit <= 600:
            mult = 2.0
        else:
            # For custom high stakes tables
            mult = 2.0 + (bet_limit - 600) / 2000.0

    if is_win:
        if is_tongits:
            return 200, int(35 * mult)
        return 150, int(25 * mult)
    
    # Losses also lose more RP in high stakes!
    return 30, int(-10 * mult)


def generate_bot_profile(bet_limit):
    """Generates a realistic rank, level, and stats for a bot based on the room's bet limit or difficulty."""
    # Determine Rank Pool
    if isinstance(bet_limit, str):
        diff = bet_limit.upper()
        if diff == "EASY":
            pool = ["Wood", "Iron"]
            lvl_range = (1, 5)
        elif diff == "MEDIUM":
            pool = ["Iron", "Bronze"]
            lvl_range = (5, 10)
        elif diff == "HARD":
            pool = ["Bronze", "Silver"]
            lvl_range = (10, 20)
        else:
            pool = ["Gold", "Immortal"]
            lvl_range = (40, 100)
    else:
        if bet_limit <= 300:
            pool = ["Wood", "Iron"]
            lvl_range = (1, 5)
        elif bet_limit <= 600:
            pool = ["Iron", "Bronze"]
            lvl_range = (5, 10)
        elif bet_limit <= 1000:
            pool = ["Bronze", "Silver"]
            lvl_range = (10, 20)
        elif bet_limit <= 5000:
            pool = ["Silver", "Gold"]
            lvl_range = (20, 40)
        else:
            pool = ["Gold", "Immortal"]
            lvl_range = (40, 100)

    rank = random.choice(pool)
    level = random.randint(*lvl_range)

    # Generate realistic RP based on rank
    if rank == "Immortal":
        rp = random.randint(5000, 10000)
    elif rank == "Gold":
        rp = random.randint(4000, 4999)
    elif rank == "Silver":
        rp = random.randint(3000, 3999)
    elif rank == "Bronze":
        rp = random.randint(2000, 2999)
    elif rank == "Iron":
        rp = random.randint(1000, 1999)
    else: # Wood
        rp = random.randint(0, 999)

    
    # Calculate base XP for the level
    total_xp = 0
    for l in range(1, level):
        req = 1000 if l <= 10 else l * 150
        total_xp += req
        
    # Add random progress within the level
    current_req = 1000 if level <= 10 else level * 150
    total_xp += random.randint(0, current_req - 1)
    
    # Simulate realistic wins and losses based on level
    # Higher level = more games played
    total_games = level * random.randint(5, 15)
    # Win rate usually hovers around 45-55% for bots
    win_rate = random.uniform(0.45, 0.55)
    wins = int(total_games * win_rate)
    losses = total_games - wins

    profile = {
        "rank": rank,
        "level": level,
        "xp": total_xp,
        "rp": rp,
        "wins": wins,
        "losses": losses
    }
    if isinstance(bet_limit, str):
        profile["difficulty"] = bet_limit.upper()
    return profile



def apply_rewards(is_win, is_tongits=False, bet_limit=100):
    """Calculates and applies XP/RP to the user profile."""
    xp, rp = get_match_rewards(is_win, is_tongits, bet_limit)
    # database.py handles the actual saving and level-up logic
    update_progression(xp, rp)
    return xp, rp

def apply_leaver_penalty(is_ranked):
    """Applies penalties for leaving a game."""
    if not is_ranked:
        return 0, 0
        
    xp = -500
    rp = -100
    update_progression(xp, rp)
    return xp, rp
