from enum import Enum

class EconomyMode(Enum):
    HITTER = "Hitter's Bounty"    # 100 Bet
    AGGRESSIVE = "Aggressive Casino" # 300 Bet
    SUSTAINED = "Sustained Economy"  # 600 Bet
    HIGH_STAKES = "High Stakes"      # 1000 Bet
    VIP = "VIP Lounge"              # 5000 Bet
    LEGENDARY = "Legendary Table"   # 10000 Bet

BETTING_CONFIGS = {
    100: {
        "mode": EconomyMode.HITTER,
        "table_img": "clean_card_table.png",
        "base_ante": 100,
        "banker_bounty": 200, # Banker puts 2x bounty
        "rules": {
            "hitter_streak_required": 2,
            "burn_penalty": 100,
            "house_edge": False, # Ties resolved normally
            "jackpot_fee": 0,
            "fight_payout_split": 1.0 # 100% to winner
        }
    },
    300: {
        "mode": EconomyMode.AGGRESSIVE,
        "table_img": "mahogany_card_table.png",
        "base_ante": 300, # Stake is 300
        "banker_bounty": 600, # Banker pays 2x-3x (600 coins)
        "rules": {
            "hitter_streak_required": 999, # Not used in stats for bounty
            "burn_penalty": 300, # Proportional
            "house_edge": True, # Banker wins ties in Draw/Fight
            "jackpot_fee": 100, # Paid by each loser on Tong-Its
            "fight_payout_split": 1.0,
            "failed_fight_penalty": 600 # Double ante
        }
    },
    600: {
        "mode": EconomyMode.SUSTAINED,
        "table_img": "mahogany_ruby_table.png",
        "base_ante": 600, # Stake is 600
        "banker_bounty": 200, # Banker adds 200 coin Dealer Fee
        "rules": {
            "hitter_streak_required": 2,
            "burn_penalty": 0,
            "house_edge": False,
            "jackpot_fee": 0,
            "fight_payout_split": 0.8, # 80% to winner, 20% to next Banker Pot
            "bounty_ban_games": 2 # Burned players banned from Banker Pot for 2 games
        }
    },
    1000: {
        "mode": EconomyMode.HIGH_STAKES,
        "table_img": "mahogany_ruby_table.png",
        "base_ante": 1000,
        "banker_bounty": 500,
        "rules": {
            "hitter_streak_required": 2,
            "burn_penalty": 0,
            "house_edge": False,
            "jackpot_fee": 0,
            "fight_payout_split": 0.8,
            "bounty_ban_games": 2
        }
    },
    5000: {
        "mode": EconomyMode.VIP,
        "table_img": "mahogany_ruby_table.png",
        "base_ante": 5000,
        "banker_bounty": 1000,
        "rules": {
            "hitter_streak_required": 2,
            "burn_penalty": 0,
            "house_edge": False,
            "jackpot_fee": 0,
            "fight_payout_split": 0.8,
            "bounty_ban_games": 2
        }
    },
    10000: {
        "mode": EconomyMode.LEGENDARY,
        "table_img": "mahogany_ruby_table.png",
        "base_ante": 10000,
        "banker_bounty": 2000,
        "rules": {
            "hitter_streak_required": 2,
            "burn_penalty": 0,
            "house_edge": False,
            "jackpot_fee": 0,
            "fight_payout_split": 0.8,
            "bounty_ban_games": 2
        }
    }
}
