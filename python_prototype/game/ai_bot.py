from .models import Meld, TurnPhase
from itertools import combinations
import random


class RuleBasedAI:
    """
    Rule-based AI for Filipino Tong-its.

    Priority order:
    1. Draw (prefer deck; draw from discard only if it completes a meld)
    2. Drop all available melds to avoid being burned
    3. If drew from discard, MUST meld the drawn card first
    4. Sapaw onto table melds to reduce hand points
    5. Consider calling fight if hand points are low
    6. Discard the most strategic card
    """

    @staticmethod
    def take_turn(engine, player):
        """Execute a complete AI turn following Tong-its rules."""
        if engine.is_game_over:
            return

        # Special case: banker's/dealer's initial turn (13 cards, no draw)
        if engine.is_dealer_initial_discard:
            RuleBasedAI._do_banker_initial_turn(engine, player)
            return

        # ── Phase 0: INITIAL ACTIONS (Fight/Sapaw) ────────────────
        if RuleBasedAI._should_call_fight(engine, player):
            # Calculate a "confidence score" before calling
            if random.random() < 0.85: # 15% chance to hesitate/wait
                engine.call_fight(player)
                return

        # Sapaw pre-draw is allowed! Reducing hand points early helps with fight decisions later
        RuleBasedAI._do_sapaw(engine, player)
        if engine.is_game_over:
            return

        # ── Phase 1: DRAW ─────────────────────────────────────────
        RuleBasedAI._do_draw(engine, player)
        if engine.is_game_over:
            return

        # ── Phase 2: FORCED MELD (if drew from discard) ───────────
        if player.forced_meld_card is not None:
            RuleBasedAI._do_forced_meld(engine, player)
            if engine.is_game_over:
                return

        # ── Phase 3: DROP OTHER MELDS ─────────────────────────────
        RuleBasedAI._do_melds(engine, player)
        if engine.is_game_over:
            return

        # ── Phase 4: SAPAW ──────────────────────────────────────
        RuleBasedAI._do_sapaw(engine, player)
        if engine.is_game_over:
            return

       
    
        RuleBasedAI._do_discard(engine, player)

    # ─── Dealer Initial Discard ──────────────────────────────────────

    @staticmethod
    def _do_banker_initial_turn(engine, player):
        """Banker's first action: meld/sapaw then discard to start the pile."""
        # The banker already has 13 cards (effectively "drawn")
        
        # Phase 1: Try melds
        RuleBasedAI._do_melds(engine, player)
        if engine.is_game_over:
            return
            
        # Phase 2: Try sapaw (rare at start)
        RuleBasedAI._do_sapaw(engine, player)
        if engine.is_game_over:
            return
            
        # Phase 3: Discard to end turn
        card = RuleBasedAI._choose_discard(engine, player)
        engine.dealer_initial_discard(card)

    # ─── Draw Logic ──────────────────────────────────────────────────

    @staticmethod
    def _do_draw(engine, player):
        """
        Decide whether to draw from closed pile or discard pile.
        Smart logic: Passing on a discard pickup if planning to Fight.
        """
        if engine.discard_pile:
            top_discard = engine.discard_pile[-1]
            if engine._can_meld_with_discard(player, top_discard):
                # STRATEGIC CHECK:
                # If we have very low points (< 10), we might want to FIGHT this turn.
                # Drawing from discard PREVENTS fighting. 
                # So if points are low, we skip the discard and draw from deck to fight.
                if player.calculate_points() <= 10 and engine.can_player_fight(player):
                    # Skip discard, drawing from deck allows CALLING FIGHT immediately after
                    pass 
                else:
                    success = engine.draw_from_discard(player)
                    if success:
                        return

        # Default: draw from closed pile
        engine.draw_from_deck(player)

    # ─── Forced Meld (after drawing from discard) ────────────────────

    @staticmethod
    def _do_forced_meld(engine, player):
        """Must meld the card drawn from the discard pile."""
        forced = player.forced_meld_card
        if forced is None:
            return

        # Find a meld containing the forced card
        for size in range(3, len(player.hand) + 1):
            for combo in combinations(player.hand, size):
                cards = list(combo)
                if forced in cards:
                    mtype = Meld.get_meld_type(cards)
                    if mtype:
                        engine.drop_meld(player, cards)
                        return

    # ─── Meld Detection & Dropping ───────────────────────────────────

    @staticmethod
    def _find_best_melds(player):
        """Find the best non-overlapping set of melds to drop."""
        all_melds = []
        hand = player.hand[:]

        for size in range(3, len(hand) + 1):
            for combo in combinations(hand, size):
                cards = list(combo)
                mtype = Meld.get_meld_type(cards)
                if mtype:
                    points = sum(c.value for c in cards)
                    all_melds.append((cards, mtype, points))

        all_melds.sort(key=lambda m: m[2], reverse=True)

        selected = []
        used_cards = set()
        for cards, mtype, points in all_melds:
            card_set = set(id(c) for c in cards)
            if not card_set & used_cards:
                selected.append((cards, mtype))
                used_cards |= card_set

        return selected

    @staticmethod
    def _do_melds(engine, player):
        """Strategic meld dropping. Bots will now 'hold' melds to trick players or go for Tong-its."""
        melds_to_drop = RuleBasedAI._find_best_melds(player)
        if not melds_to_drop:
            return

        deck_rem = engine.deck.remaining()
        hand_size = len(player.hand)
        has_melds_on_table = len(player.melds) > 0
        
        # Rules and Safety Check:
        # 1. If we can TONG-ITS right now (clear hand), do it.
        total_meld_cards = sum(len(m[0]) for m in melds_to_drop)
        is_tongits_win = (total_meld_cards == hand_size)
        
        if is_tongits_win:
            for cards, mtype in melds_to_drop:
                engine.drop_meld(player, cards)
            return

        # 2. Deception / Strategy Logic:
        should_hold = False
        
        # Early game: High chance to hold melds to look 'dangerous' or wait for better runs
        diff = getattr(player, 'difficulty', 'MEDIUM')
        if deck_rem > 25:
            hold_chance = 0.75
            wait_chance = 0.30
            if diff == 'EASY':
                hold_chance = 0.30
                wait_chance = 0.10
            elif diff == 'HARD':
                hold_chance = 0.90
                wait_chance = 0.50

            # 75% chance to hold if we already have one safety meld down
            if has_melds_on_table and random.random() < hold_chance:
                should_hold = True
            # Even if no melds down, 30% chance to wait (high risk/reward)
            elif not has_melds_on_table and random.random() < wait_chance:
                should_hold = True
                
        # Mid game: Holding to 'wait' for a Tong-its (if only 1-2 cards away)
        elif deck_rem > 12:
            rem_after_drop = hand_size - total_meld_cards
            if has_melds_on_table and rem_after_drop <= 2 and random.random() < 0.60:
                should_hold = True

        # Execute Strategic Drops
        for cards, mtype in melds_to_drop:
            # CRITICAL: Always try to drop at least one meld to avoid being 'Burned' 
            # and to allow 'Calling Fight' later.
            if not has_melds_on_table:
                engine.drop_meld(player, cards)
                has_melds_on_table = True
                # If we were told to hold, stop after the first 'Safety' meld
                if should_hold: break
            
            elif not should_hold:
                # Normal behavior: drop if not holding
                engine.drop_meld(player, cards)
                if engine.is_game_over: return

    # ─── Sapaw Logic ─────────────────────────────────────────────────

    @staticmethod
    def _do_sapaw(engine, player):
        """Sapaw onto table melds. Strategic bots may hold small cards to hide hand strength."""
        changed = True
        deck_rem = engine.deck.remaining()
        
        while changed:
            changed = False
            options = engine.get_sapaw_options(player)
            if not options:
                break

            # Sort options by card value (highest first)
            options.sort(key=lambda o: o[0].value, reverse=True)
            
            for card, meld in options:
                if card in player.hand:
                    # Strategy: If it's early game and card is low value (e.g. < 7),
                    # the bot might hold it to keep its hand looking 'heavy'
                    if deck_rem > 25 and card.value < 7 and len(player.melds) > 0:
                        if random.random() < 0.50: # 50% chance to hold 'garbage' for deception
                            continue

                    success = engine.sapaw(player, card, meld)
                    if success:
                        changed = True
                        if engine.is_game_over:
                            return

    # ─── Difficulty Helper ───────────────────────────────────────────

    @staticmethod
    def _get_difficulty_factor(player):
        diff = getattr(player, 'difficulty', 'MEDIUM')
        if not diff:
            diff = 'MEDIUM'
        diff = diff.upper()
        if diff == "EASY":
            return 1.5  # More reckless
        elif diff == "HARD":
            return 0.7  # More cautious
        else:
            return 1.0

    # ─── Fight Decision ──────────────────────────────────────────────

    @staticmethod
    def _should_call_fight(engine, player):
        """
        Decide whether to call fight based on hand points, deck size, and opponent status.
        Uses a more aggressive 'Tong-its' playstyle.
        """
        if not engine.can_player_fight(player):
            return False

        points = player.calculate_points()
        deck_remaining = engine.deck.remaining()
        factor = RuleBasedAI._get_difficulty_factor(player)
        
        # 1. Immediate Win: extremely low points
        if points <= 5 * factor:
            return True
            
        # 2. Aggressive Late Game: If deck is running low
        if deck_remaining < 10 and points <= 15 * factor:
            return True

        # 3. Stratregic Mid-Game:
        # Check if we have significantly lower points than likely opponents
        avg_opponent_cards = sum(p.card_count() for p in engine.players if p != player) / 2
        
        # If we have very few cards (e.g. 3-4) and points are decent (e.g. < 10)
        if player.card_count() <= 5 and points <= 10 * factor:
            # If opponents have many cards (e.g. > 8), they likely have high points
            if avg_opponent_cards > player.card_count() + 3:
                return True

        # 4. Burned status check:
        # If someone is burned, our chances increase since they can't challenge
        burned_count = sum(1 for p in engine.players if p != player and p.is_burned)
        if burned_count >= 1 and points <= 12 * factor:
            return True

        return False

    @staticmethod
    def _should_respond_fight(engine, player, fight_context):
        """Decide whether to fight (challenge) or fold.
        
        FIXED: Previous logic used a blind threshold (>20 = fold) which caused
        bots to fold even when they had the lowest points and would win.
        New logic estimates opponent points and compares directly.
        """
        caller = fight_context['caller']
        my_points = player.calculate_points()
        
        # Never challenge if burned (auto-fold is handled by engine, but safety check)
        if player.is_burned:
            return 'fold'
            
        factor = RuleBasedAI._get_difficulty_factor(player)
        
        # Estimate caller's points using visible info:
        # Cards in hand × estimated average value per card
        # Bots with melds tend to have lower avg value remaining
        caller_cards = caller.card_count()
        caller_has_melds = len(caller.melds) > 0
        
        # Heuristic: avg card value ~5-6 for players with melds (they shed high cards)
        # avg ~6-7 for players without melds
        if caller_has_melds:
            estimated_caller_pts = caller_cards * 5
        else:
            estimated_caller_pts = caller_cards * 6
        
        # Check other opponents too — if ALL fold, we only compete vs caller
        other_opponents = [p for p in engine.players if p != player and p != caller]
        
        # 1. Extreme confidence: very low points, always fight
        if my_points <= 5 * factor:
            return 'fight'
        
        # 2. Clear advantage: our points are lower than estimated caller points
        if my_points < estimated_caller_pts:
            return 'fight'
        
        # 3. Competitive range: similar points, factor in card count advantage
        if my_points <= estimated_caller_pts + 5 * factor:
            # If we have fewer or equal cards, we likely have lower value cards
            if player.card_count() <= caller_cards:
                return 'fight'
            # Close enough to gamble
            if my_points <= 15 * factor:
                return 'fight'
        
        # 4. Check if opponents are burned (fewer challengers = better odds)
        burned_opponents = sum(1 for p in other_opponents if p.is_burned)
        if burned_opponents >= 1 and my_points <= 20 * factor:
            return 'fight'
        
        # 5. Moderate points but not terrible — compare card counts as tiebreaker
        if my_points <= 25 * factor:
            if player.card_count() < caller_cards:
                return 'fight'
            if player.card_count() == caller_cards and my_points <= 18 * factor:
                return 'fight'
        
        # 6. High points — only fight if we suspect caller has even more
        if my_points <= 35 * factor:
            if player.card_count() < caller_cards - 2:
                return 'fight'  # Significantly fewer cards = likely lower points
        
        # Default: fold if points are genuinely high and no card count advantage
        return 'fold'

    # ─── Discard Logic ───────────────────────────────────────────────

    @staticmethod
    def _do_discard(engine, player):
        """Discard the most strategic card."""
        if not player.hand:
            return
        card_to_discard = RuleBasedAI._choose_discard(engine, player)
        engine.discard_card(player, card_to_discard)

    @staticmethod
    def _choose_discard(engine, player):
        """
        Smart discard selection:
        - Penalizes cards that are 'connected' or part of potential melds.
        - Prioritizes high value cards if they are 'garbage'.
        - Checks for opponent sapaw safety.
        """
        hand = player.hand[:]
        if not hand: return None
        if len(hand) == 1: return hand[0]

        # Easy bots: 40% chance to discard a random card (making them easier)
        if getattr(player, 'difficulty', 'MEDIUM') == 'EASY' and random.random() < 0.40:
            return random.choice(hand)

        scores = {}
        for card in hand:
            # Baseline: higher value = better to discard
            score = card.value * 2 
            
            # 1. Penalty: Part of a full meld (Highest priority to keep)
            is_in_meld = False
            for combo in combinations(hand, 3):
                if card in combo and Meld.is_valid_meld(list(combo)):
                    is_in_meld = True
                    break
            if is_in_meld: score -= 100

            # 2. Penalty: Connectivity (Potential melds)
            # Check for pairs or near-runs
            connections = 0
            for other in hand:
                if card == other: continue
                # Same rank
                if card.rank == other.rank: connections += 20
                # Same suit, near rank
                if card.suit == other.suit:
                    from .models import RANK_ORDER
                    r1 = RANK_ORDER.index(card.rank)
                    r2 = RANK_ORDER.index(other.rank)
                    if abs(r1 - r2) == 1: connections += 15 # Consecutive
                    if abs(r1 - r2) == 2: connections += 10 # Gap of one

            score -= connections

            # 3. Penalty: Avoid giving opponents a sapaw
            for tmeld in engine.table_melds:
                if tmeld.owner != player and tmeld.can_sapaw(card):
                    score -= 30 # Heavy penalty: don't help others reduce points

            # 4. Bonus: Discarding dangerous high cards early
            if card.value == 10 and engine.deck.remaining() > 30:
                score += 5 # Get rid of Jacks/Queens/Kings early if not connected

            scores[id(card)] = (score, card)

        # Pick the highest score (the card we want to lose most)
        best_id = max(scores, key=lambda cid: scores[cid][0])
        return scores[best_id][1]
