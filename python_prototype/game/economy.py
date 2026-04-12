from .betting_configs import EconomyMode, BETTING_CONFIGS

class EconomyManager:
    """Manages the betting, pots, and penalties for the Hitter's Bounty system."""
    
    def __init__(self, bet_level=100):
        self.bet_level = bet_level
        self.config = BETTING_CONFIGS.get(bet_level, BETTING_CONFIGS[100])
        self.mode = self.config["mode"]
        
        self.base_ante = self.config["base_ante"]
        self.banker_pot = 0
        self.main_pot = 0
        
        # Tracking for Proposal 3: Cold Streak / Bounty Ban
        # { player_idx: num_games_remaining }
        self.bounty_bans = {0: 0, 1: 0, 2: 0}
        
    def calculate_entry_fee(self, is_dealer):
        """Returns the total coins a player must put on the table."""
        if is_dealer:
            return self.base_ante + self.config["banker_bounty"]
        return self.base_ante

    def start_round(self, dealer_idx):
        """Initializes the pots for a new round."""
        # Main Pot: 3 players * base_ante
        self.main_pot = self.base_ante * 3
        
        # Banker adds bounty to the existing Banker Pot
        self.banker_pot += self.config["banker_bounty"]
        
        # Update bounty bans (only counts down at the start of a round)
        for p_idx in self.bounty_bans:
            if self.bounty_bans[p_idx] > 0:
                self.bounty_bans[p_idx] -= 1
        
    def resolve_payouts(self, winner_idx, dealer_idx, win_streak, win_method, caller_idx, burned_indices):
        """
        Calculates the final coin changes for all players.
        Returns: { player_index: coin_delta }, payout_details
        """
        deltas = {0: 0, 1: 0, 2: 0}
        details = {
            'main_pot': self.main_pot,
            'banker_pot_payout': 0,
            'penalties_collected': 0,
            'total_won': 0,
            'mode': self.mode.value
        }

        # 1. Base Payout (Main Pot)
        winner_payout = self.main_pot
        rules = self.config["rules"]
        
        # 2. Banker Pot (Bounty) Logic
        can_win_bounty = True
        
        # Proposal 3: check for bounty ban
        if self.mode == EconomyMode.SUSTAINED:
            if self.bounty_bans.get(winner_idx, 0) > 0:
                can_win_bounty = False

        if can_win_bounty:
            if self.mode == EconomyMode.HITTER:
                # Only paid if winner is the dealer and has a streak of 2+
                if winner_idx == dealer_idx and win_streak >= rules["hitter_streak_required"]:
                    payout = int(self.banker_pot * rules["fight_payout_split"])
                    winner_payout += payout
                    details['banker_pot_payout'] = payout
                    self.banker_pot -= payout
            
            elif self.mode == EconomyMode.AGGRESSIVE:
                # Winner takes EVERYTHING if it's a Tongue-its or if Banker wins via Draw
                is_tongits = 'tongits' in win_method.lower()
                is_banker_draw = (winner_idx == dealer_idx and 'deck_empty' in win_method.lower())
                
                if is_tongits or is_banker_draw:
                    winner_payout += self.banker_pot
                    details['banker_pot_payout'] = self.banker_pot
                    self.banker_pot = 0
            
            elif self.mode == EconomyMode.SUSTAINED:
                # Fight wins split the bounty pot (80% winner, 20% stays)
                is_tongits = 'tongits' in win_method.lower()
                is_fight = 'fight' in win_method.lower()
                
                if is_tongits:
                    winner_payout += self.banker_pot
                    details['banker_pot_payout'] = self.banker_pot
                    self.banker_pot = 0
                elif is_fight:
                    payout = int(self.banker_pot * rules["fight_payout_split"])
                    winner_payout += payout
                    details['banker_pot_payout'] = payout
                    self.banker_pot -= payout # 20% stays

        # 3. Penalties (Burned / Fight Failure / Jackpot)
        penalty_total = 0
        
        # Burned Penalty
        for b_idx in burned_indices:
            if b_idx != winner_idx:
                p_fee = rules["burn_penalty"]
                deltas[b_idx] -= p_fee
                penalty_total += p_fee
                
                # Proposal 3: Apply bounty ban
                if self.mode == EconomyMode.SUSTAINED and rules.get("bounty_ban_games", 0) > 0:
                    self.bounty_bans[b_idx] = rules["bounty_ban_games"]
        
        # Fight failure
        if 'fight' in win_method.lower() and caller_idx is not None and caller_idx != winner_idx:
            f_penalty = rules.get("failed_fight_penalty", rules["burn_penalty"])
            deltas[caller_idx] -= f_penalty
            penalty_total += f_penalty
            
        # Proposal 2: Jackpot Fee for Tong-Its
        if self.mode == EconomyMode.AGGRESSIVE and 'tongits' in win_method.lower():
            jackpot = rules["jackpot_fee"]
            for p_idx in [0, 1, 2]:
                if p_idx != winner_idx:
                    deltas[p_idx] -= jackpot
                    penalty_total += jackpot
            
        # Add all penalties to winner's payout
        winner_payout += penalty_total
        deltas[winner_idx] = winner_payout
        
        details['penalties_collected'] = penalty_total
        details['total_won'] = winner_payout
        
        return deltas, details

    def reset_all(self):
        self.banker_pot = 0
        self.main_pot = 0
        self.bounty_bans = {0: 0, 1: 0, 2: 0}

