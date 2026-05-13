from .models import Meld, TurnPhase
from itertools import combinations
import random


# ─── Session Memory ──────────────────────────────────────────────────────────

class GameMemory:
    """
    Persists across rounds within a play session.
    Tracks discards, fight behaviour, and player tendencies per bot.
    """

    def __init__(self):
        self.seen_discards: set = set()          # every card ever seen in any discard pile
        self.player_discards: dict = {}          # player_name -> [Card, ...]
        self.fight_calls: dict = {}              # player_name -> int
        self.rounds_observed: int = 0

    # ── sync / record ────────────────────────────────────────────────────────

    def sync(self, engine):
        """Pull new discard-pile cards into memory. Call at start of every turn."""
        for card in engine.discard_pile:
            self.seen_discards.add(card)

    def record_discard(self, player_name: str, card):
        self.player_discards.setdefault(player_name, []).append(card)

    def record_fight_call(self, player_name: str):
        self.fight_calls[player_name] = self.fight_calls.get(player_name, 0) + 1

    def new_round(self):
        self.rounds_observed += 1

    # ── queries ──────────────────────────────────────────────────────────────

    def get_aggression(self, player_name: str) -> float:
        """0.0 = passive, 1.0 = very aggressive. Based on fight-call frequency."""
        rounds = max(self.rounds_observed, 1)
        fights = self.fight_calls.get(player_name, 0)
        return min((fights / rounds) * 3.0, 1.0)

    def estimate_hand_strength(self, player, engine) -> float:
        """
        Memory-informed point estimate for an opponent.
        Refines the flat card_count × avg_value heuristic using their
        discard history (high discards → low remaining avg value, etc.)
        and dead-card counts.
        """
        card_count = player.card_count()
        if card_count == 0:
            return 0.0

        has_melds = len(player.melds) > 0
        base_avg = 5.0 if has_melds else 6.0

        # Refine from discard history
        their_discards = self.player_discards.get(player.name, [])
        if len(their_discards) >= 2:
            d_avg = sum(c.value for c in their_discards) / len(their_discards)
            if d_avg >= 8:        # shed high cards → hand is cheap
                base_avg = max(3.0, base_avg - 2.0)
            elif d_avg >= 6:
                base_avg = max(4.0, base_avg - 1.0)
            elif d_avg <= 3:      # kept big cards, discarded small
                base_avg = min(8.0, base_avg + 1.5)

        # Dead-card pressure: many cards of the same suit seen discarded
        # means opponent is less likely to have a connected hand in that suit
        dead_by_suit: dict = {}
        for c in self.seen_discards:
            dead_by_suit[c.suit] = dead_by_suit.get(c.suit, 0) + 1
        max_dead = max(dead_by_suit.values()) if dead_by_suit else 0
        if max_dead >= 5:          # one suit heavily depleted
            base_avg = max(3.0, base_avg - 0.5)

        return round(card_count * base_avg)

    def is_dead(self, card) -> bool:
        """True if this card has already been discarded (can't be in anyone's hand)."""
        return card in self.seen_discards


# ─── Main AI ─────────────────────────────────────────────────────────────────

class RuleBasedAI:
    """
    Rule-based AI for Filipino Tong-its.
    Improvements over baseline:
      • Card memory     – tracks every discard seen this session
      • Opponent model  – refines point estimates from discard history
      • Adaptive hold   – meld-hold % rises with player aggression
      • Bluff fight     – HARD bots apply pressure on passive players
      • Dead-card discard – prefers to throw cards already seen (safe)
      • Sapaw deception  – HARD bots hold low-value cards for longer
    """

    # Class-level registry so memory outlives individual engine instances
    _memory_store: dict = {}   # bot_player_name -> GameMemory

    @classmethod
    def get_memory(cls, player_name: str) -> GameMemory:
        if player_name not in cls._memory_store:
            cls._memory_store[player_name] = GameMemory()
        return cls._memory_store[player_name]

    @classmethod
    def reset_memory(cls, player_name: str = None):
        if player_name:
            cls._memory_store.pop(player_name, None)
        else:
            cls._memory_store.clear()

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _diff(player) -> str:
        d = getattr(player, 'difficulty', 'MEDIUM') or 'MEDIUM'
        return d.upper()

    @staticmethod
    def _factor(player) -> float:
        d = RuleBasedAI._diff(player)
        return 1.5 if d == 'EASY' else (0.7 if d == 'HARD' else 1.0)

    @staticmethod
    def _human_players(engine, bot):
        """Opponents with no difficulty attribute set (i.e. the human player)."""
        return [p for p in engine.players
                if p != bot and not getattr(p, 'difficulty', None)]

    # ── public entry point ───────────────────────────────────────────────────

    @staticmethod
    def take_turn(engine, player):
        if engine.is_game_over:
            return

        mem = RuleBasedAI.get_memory(player.name)
        mem.sync(engine)

        if engine.is_dealer_initial_discard:
            RuleBasedAI._do_banker_initial_turn(engine, player)
            return

        # Phase 0 – Fight or pre-draw sapaw
        if RuleBasedAI._should_call_fight(engine, player):
            diff = RuleBasedAI._diff(player)
            hesitate = 0.05 if diff == 'HARD' else 0.15
            if random.random() > hesitate:
                mem.record_fight_call(player.name)
                engine.call_fight(player)
                return

        # Phase 1 – Draw
        RuleBasedAI._do_draw(engine, player)
        if engine.is_game_over:
            return

        # Phase 2 – Forced meld (drew from discard)
        if player.forced_meld_card is not None:
            RuleBasedAI._do_forced_meld(engine, player)
            if engine.is_game_over:
                return

        # Phase 3 – Drop melds
        RuleBasedAI._do_melds(engine, player)
        if engine.is_game_over:
            return

        # Phase 4 – Sapaw
        RuleBasedAI._do_sapaw(engine, player)
        if engine.is_game_over:
            return

        # Phase 5 – Discard
        RuleBasedAI._do_discard(engine, player)

    # ── dealer initial turn ──────────────────────────────────────────────────

    @staticmethod
    def _do_banker_initial_turn(engine, player):
        RuleBasedAI._do_melds(engine, player)
        if engine.is_game_over:
            return
        RuleBasedAI._do_sapaw(engine, player)
        if engine.is_game_over:
            return
        card = RuleBasedAI._choose_discard(engine, player)
        engine.dealer_initial_discard(card)

    # ── draw ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _do_draw(engine, player):
        if engine.discard_pile:
            top = engine.discard_pile[-1]
            if engine._can_meld_with_discard(player, top):
                # Skip pickup if low points + can fight right after draw from deck
                if player.calculate_points() <= 10 and engine.can_player_fight(player):
                    pass
                else:
                    if engine.draw_from_discard(player):
                        return
        engine.draw_from_deck(player)

    # ── forced meld ──────────────────────────────────────────────────────────

    @staticmethod
    def _do_forced_meld(engine, player):
        forced = player.forced_meld_card
        if forced is None:
            return
        for size in range(3, len(player.hand) + 1):
            for combo in combinations(player.hand, size):
                cards = list(combo)
                if forced in cards and Meld.get_meld_type(cards):
                    engine.drop_meld(player, cards)
                    return

    # ── meld detection ───────────────────────────────────────────────────────

    @staticmethod
    def _find_best_melds(player):
        hand = player.hand[:]
        all_melds = []
        for size in range(3, len(hand) + 1):
            for combo in combinations(hand, size):
                cards = list(combo)
                mtype = Meld.get_meld_type(cards)
                if mtype:
                    all_melds.append((cards, mtype, sum(c.value for c in cards)))
        all_melds.sort(key=lambda m: m[2], reverse=True)

        selected, used = [], set()
        for cards, mtype, pts in all_melds:
            ids = set(id(c) for c in cards)
            if not ids & used:
                selected.append((cards, mtype))
                used |= ids
        return selected

    @staticmethod
    def _do_melds(engine, player):
        """
        Strategic meld dropping.
        Adaptive: HARD bots raise hold % when the human player fights frequently.
        """
        melds_to_drop = RuleBasedAI._find_best_melds(player)
        if not melds_to_drop:
            return

        deck_rem = engine.deck.remaining()
        hand_size = len(player.hand)
        has_melds = len(player.melds) > 0
        diff = RuleBasedAI._diff(player)

        total_meld_cards = sum(len(m[0]) for m in melds_to_drop)

        # Always Tong-its immediately
        if total_meld_cards == hand_size:
            for cards, mtype in melds_to_drop:
                engine.drop_meld(player, cards)
            return

        should_hold = False

        if deck_rem > 25:
            if diff == 'EASY':
                hold_chance, wait_chance = 0.30, 0.10
            elif diff == 'HARD':
                hold_chance, wait_chance = 0.90, 0.50
                # Adaptive: raise hold if human is aggressive
                mem = RuleBasedAI.get_memory(player.name)
                for hp in RuleBasedAI._human_players(engine, player):
                    aggression = mem.get_aggression(hp.name)
                    hold_chance = min(0.98, hold_chance + aggression * 0.08)
            else:
                hold_chance, wait_chance = 0.75, 0.30

            if has_melds and random.random() < hold_chance:
                should_hold = True
            elif not has_melds and random.random() < wait_chance:
                should_hold = True

        elif deck_rem > 12:
            rem_after = hand_size - total_meld_cards
            if has_melds and rem_after <= 2 and random.random() < 0.60:
                should_hold = True

        for cards, mtype in melds_to_drop:
            if not has_melds:
                engine.drop_meld(player, cards)
                has_melds = True
                if should_hold:
                    break
            elif not should_hold:
                engine.drop_meld(player, cards)
                if engine.is_game_over:
                    return

    # ── sapaw ────────────────────────────────────────────────────────────────

    @staticmethod
    def _do_sapaw(engine, player):
        """
        Sapaw with deception.
        HARD bots hold low-value cards more often to fake a heavy hand.
        """
        diff = RuleBasedAI._diff(player)
        deck_rem = engine.deck.remaining()
        changed = True

        while changed:
            changed = False
            options = engine.get_sapaw_options(player)
            if not options:
                break
            options.sort(key=lambda o: o[0].value, reverse=True)

            for card, meld in options:
                if card not in player.hand:
                    continue
                # Deception hold
                hold_thr = 0.65 if diff == 'HARD' else 0.50
                if deck_rem > 25 and card.value < 7 and len(player.melds) > 0:
                    if random.random() < hold_thr:
                        continue
                if engine.sapaw(player, card, meld):
                    changed = True
                    if engine.is_game_over:
                        return

    # ── fight decision ───────────────────────────────────────────────────────

    @staticmethod
    def _should_call_fight(engine, player):
        """
        Fight decision with pressure-bluff for HARD bots.
        If the human player is passive (rarely fights back), HARD bots will
        occasionally call a fight slightly above their confidence threshold
        to put psychological pressure.
        """
        if not engine.can_player_fight(player):
            return False

        points = player.calculate_points()
        deck_rem = engine.deck.remaining()
        factor = RuleBasedAI._factor(player)
        diff = RuleBasedAI._diff(player)

        if points <= 5 * factor:
            return True
        if deck_rem < 10 and points <= 15 * factor:
            return True

        avg_opp = sum(p.card_count() for p in engine.players if p != player) / 2
        if player.card_count() <= 5 and points <= 10 * factor:
            if avg_opp > player.card_count() + 3:
                return True

        burned = sum(1 for p in engine.players if p != player and p.is_burned)
        if burned >= 1 and points <= 12 * factor:
            return True

        # HARD-only: pressure bluff on passive human
        if diff == 'HARD':
            mem = RuleBasedAI.get_memory(player.name)
            for hp in RuleBasedAI._human_players(engine, player):
                if mem.get_aggression(hp.name) < 0.2 and deck_rem < 20:
                    if points <= 10 * factor and random.random() < 0.20:
                        return True

        return False

    @staticmethod
    def _should_respond_fight(engine, player, fight_context):
        """
        Respond to a fight call.
        HARD: uses GameMemory to build a refined point estimate for the caller.
        EASY/MEDIUM: uses original flat heuristic.
        """
        caller = fight_context['caller']
        my_points = player.calculate_points()
        if player.is_burned:
            return 'fold'

        factor = RuleBasedAI._factor(player)
        diff = RuleBasedAI._diff(player)

        # Point estimate for caller
        if diff == 'HARD':
            mem = RuleBasedAI.get_memory(player.name)
            est_caller = mem.estimate_hand_strength(caller, engine)
        else:
            c_cards = caller.card_count()
            est_caller = c_cards * 5 if len(caller.melds) > 0 else c_cards * 6

        other = [p for p in engine.players if p != player and p != caller]

        if my_points <= 5 * factor:
            return 'fight'
        if my_points < est_caller:
            return 'fight'
        if my_points <= est_caller + 5 * factor:
            if player.card_count() <= caller.card_count():
                return 'fight'
            if my_points <= 15 * factor:
                return 'fight'

        burned_opp = sum(1 for p in other if p.is_burned)
        if burned_opp >= 1 and my_points <= 20 * factor:
            return 'fight'
        if my_points <= 25 * factor:
            if player.card_count() < caller.card_count():
                return 'fight'
            if player.card_count() == caller.card_count() and my_points <= 18 * factor:
                return 'fight'
        if my_points <= 35 * factor:
            if player.card_count() < caller.card_count() - 2:
                return 'fight'

        return 'fold'

    # ── discard ──────────────────────────────────────────────────────────────

    @staticmethod
    def _do_discard(engine, player):
        if not player.hand:
            return
        card = RuleBasedAI._choose_discard(engine, player)
        if card:
            # Record in memory so opponent modeling gets richer over time
            RuleBasedAI.get_memory(player.name).record_discard(player.name, card)
            engine.discard_card(player, card)

    @staticmethod
    def _choose_discard(engine, player):
        """
        Smart discard with memory-aware dead-card bonus.
        HARD: dead cards (already seen in discard pile) are preferred —
              safe to throw without giving new information.
        """
        hand = player.hand[:]
        if not hand:
            return None
        if len(hand) == 1:
            return hand[0]

        diff = RuleBasedAI._diff(player)

        # Easy bots: 40% random
        if diff == 'EASY' and random.random() < 0.40:
            return random.choice(hand)

        mem = RuleBasedAI.get_memory(player.name) if diff == 'HARD' else None
        scores = {}

        for card in hand:
            score = card.value * 2

            # 1. Keep cards in melds
            in_meld = any(
                card in combo and Meld.is_valid_meld(list(combo))
                for combo in combinations(hand, 3)
            )
            if in_meld:
                score -= 100

            # 2. Connectivity penalty (keep connected cards)
            connections = 0
            for other in hand:
                if card is other:
                    continue
                if card.rank == other.rank:
                    connections += 20
                if card.suit == other.suit:
                    from .models import RANK_ORDER
                    r1 = RANK_ORDER.index(card.rank)
                    r2 = RANK_ORDER.index(other.rank)
                    if abs(r1 - r2) == 1:
                        connections += 15
                    elif abs(r1 - r2) == 2:
                        connections += 10
            score -= connections

            # 3. Avoid giving opponents a sapaw
            for tmeld in engine.table_melds:
                if tmeld.owner != player and tmeld.can_sapaw(card):
                    score -= 30

            # 4. Early high-card bonus
            if card.value == 10 and engine.deck.remaining() > 30:
                score += 5

            # 5. [HARD] Dead-card bonus: safe to discard, adds no info
            if mem and mem.is_dead(card):
                score += 20

            scores[id(card)] = (score, card)

        best_id = max(scores, key=lambda cid: scores[cid][0])
        return scores[best_id][1]
