import random
from ui.database import update_progression

RANKS = ["Wood", "Iron", "Bronze", "Silver", "Gold", "Immortal"]

def get_match_rewards(is_win, is_tongits=False):
    """Returns (xp, rp) based on match result."""
    if is_win:
        if is_tongits:
            return 200, 35
        return 150, 25
    return 30, -10

def generate_bot_profile(bet_limit):
    """Generates a realistic rank, level, and stats for a bot based on the room's bet limit."""
    # Determine Rank Pool
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

    return {
        "rank": rank,
        "level": level,
        "xp": total_xp,
        "rp": rp,
        "wins": wins,
        "losses": losses
    }



def apply_rewards(is_win, is_tongits=False):
    """Calculates and applies XP/RP to the user profile."""
    xp, rp = get_match_rewards(is_win, is_tongits)
    # database.py handles the actual saving and level-up logic
    update_progression(xp, rp)
    return xp, rp
