import random
from enum import Enum, auto


# ─── Module Constants ────────────────────────────────────────────────

RANK_ORDER = ['Ace', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King']
SUIT_ORDER = {'Hearts': 0, 'Diamonds': 1, 'Clubs': 2, 'Spades': 3}


class TurnPhase(Enum):
    """State machine phases for a single turn in Tong-its."""
    DRAW = auto()
    MELD = auto()       # Optional: player can drop melds or sapaw
    ACTION = auto()     # Optional: player can call fight
    DISCARD = auto()
    WAITING = auto()    # Not this player's turn


class GamePhase(Enum):
    """High-level game flow states."""
    SHUFFLING = auto()
    DEALING = auto()
    DEALER_DISCARD = auto()  # Dealer must throw first card
    PLAYING = auto()
    RESOLVING_FIGHT = auto() # Waiting for players to fold or fight
    GAME_OVER = auto()


class Card:
    def __init__(self, suit, rank, value):
        self.suit = suit
        self.rank = rank
        self.value = value

    def __repr__(self):
        return f"{self.rank} of {self.suit}"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        return hash((self.suit, self.rank))


class Deck:
    SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    RANKS = {
        'Ace': 1, '2': 2, '3': 3, '4': 4, '5': 5,
        '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'Jack': 10, 'Queen': 10, 'King': 10
    }

    def __init__(self):
        self.cards = [
            Card(suit, rank, value)
            for suit in self.SUITS
            for rank, value in self.RANKS.items()
        ]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop() if self.cards else None

    def remaining(self):
        return len(self.cards)


class Player:
    def __init__(self, name, is_human=False, level=1, rank="Wood", rp=0, xp=0, difficulty=None):
        self.name = name
        self.is_human = is_human
        self.level = level
        self.rank = rank
        self.rp = rp
        self.xp = xp
        self.difficulty = difficulty
        self.hand = []
        self.melds = []              # List of TableMeld objects owned by this player
        self.is_burned = True        # True until they drop at least one meld
        self.has_drawn = False       # Tracks if player drew this turn
        self.has_been_sapawed = False # True if anyone sapawed on this player's melds (can't call fight)
        self.forced_meld_card = None # Card from discard pile that MUST be melded immediately
        self.selected_cards = []     # UI state: currently selected cards in hand
        self.hand_groups = []        # List of ('meld'|'near'|'isolated'|'manual', count)
        self.manual_groups = []      # List of lists of cards manually grouped by the user

    def calculate_points(self):
        """Sum of values of cards remaining in hand, discounting any held valid melds (0 pts).
        Uses a greedy two-pass approach (sets then runs) instead of brute-force combinations.
        """
        if not self.hand:
            return 0

        hand = self.hand[:]
        used = set()  # indices of cards counted as part of melds

        # Pass 1: Find sets (3-4 cards of the same rank)
        from collections import defaultdict
        rank_groups = defaultdict(list)
        for i, c in enumerate(hand):
            rank_groups[c.rank].append(i)

        for rank, indices in rank_groups.items():
            if len(indices) >= 3:
                # Use all cards of this rank as a set (3 or 4)
                for idx in indices:
                    used.add(idx)

        # Pass 2: Find runs (3+ consecutive same-suit cards) from remaining
        suit_cards = defaultdict(list)
        for i, c in enumerate(hand):
            if i not in used:
                suit_cards[c.suit].append((RANK_ORDER.index(c.rank), i))

        for suit, cards_with_idx in suit_cards.items():
            cards_with_idx.sort(key=lambda x: x[0])
            # Find consecutive sequences
            run = [cards_with_idx[0]]
            for j in range(1, len(cards_with_idx)):
                if cards_with_idx[j][0] == run[-1][0] + 1:
                    run.append(cards_with_idx[j])
                else:
                    if len(run) >= 3:
                        for _, idx in run:
                            used.add(idx)
                    run = [cards_with_idx[j]]
            if len(run) >= 3:
                for _, idx in run:
                    used.add(idx)

        remaining_cards = [hand[i] for i in range(len(hand)) if i not in used]
        return sum(card.value for card in remaining_cards)

    def card_count(self):
        return len(self.hand)

    def sort_hand(self):
        """Basic sort by suit then rank."""
        self.hand.sort(key=lambda c: (
            SUIT_ORDER.get(c.suit, 4),
            RANK_ORDER.index(c.rank) if c.rank in RANK_ORDER else 99
        ))
        self.hand_groups = [('all', len(self.hand))]

    def sort_by_value(self, descending=True):
        """Sort hand by card rank. A-K (ascending) or K-A (descending)."""
        self.hand.sort(key=lambda c: (
            RANK_ORDER.index(c.rank) if c.rank in RANK_ORDER else 99,
            SUIT_ORDER.get(c.suit, 4)
        ), reverse=descending)
        self.hand_groups = [('all', len(self.hand))]
        self.manual_groups = []


    def group_hand(self):
        """
        Smart auto-sort: group cards into organized sections.
        1. Complete melds (ready to drop) — grouped together
        2. Near-melds (pairs close to becoming melds) — grouped together
        3. Isolated cards (discard candidates, sorted high value first)
        Stores group boundaries in self.hand_groups for UI gap rendering.
        """
        from itertools import combinations

        hand = self.hand[:]
        used = set()  # indices of cards already assigned to a group
        groups = []   # List of (group_type, [cards])

        # Phase 0: Manual Groups
        # First, clean up manual groups (remove cards no longer in hand)
        valid_manual = []
        for mg in self.manual_groups:
            present = [c for c in mg if c in hand]
            if len(present) >= 2:
                # Ensure we don't double-use cards across manual groups
                already_used = False
                for c in present:
                    if hand.index(c) in used:
                        already_used = True
                        break
                if not already_used:
                    valid_manual.append(present)
                    for c in present:
                        used.add(hand.index(c))
                    groups.append(('manual', present))
        self.manual_groups = valid_manual

        # Phase 1: Find complete melds (3-4 cards)
        all_melds = []
        for size in range(4, 2, -1):  # Try 4-card first
            for combo in combinations(range(len(hand)), size):
                cards = [hand[i] for i in combo]
                if Meld.is_valid_meld(cards):
                    points = sum(c.value for c in cards)
                    all_melds.append((combo, cards, points))

        # Sort by point value descending (biggest melds first)
        all_melds.sort(key=lambda m: m[2], reverse=True)

        # Greedily assign cards to melds (no overlap)
        for indices, cards, pts in all_melds:
            if not any(i in used for i in indices):
                for i in indices:
                    used.add(i)
                # Sort within group by suit then rank
                cards_sorted = sorted(cards, key=lambda c: (
                    SUIT_ORDER.get(c.suit, 4), RANK_ORDER.index(c.rank)
                ))
                groups.append(('meld', cards_sorted))

        # Phase 2: Find near-melds from remaining cards
        remaining_idx = [i for i in range(len(hand)) if i not in used]
        remaining = [(i, hand[i]) for i in remaining_idx]
        pair_used = set()

        # Same-rank pairs (potential sets)
        for a in range(len(remaining)):
            if remaining[a][0] in pair_used:
                continue
            for b in range(a + 1, len(remaining)):
                if remaining[b][0] in pair_used:
                    continue
                c1, c2 = remaining[a][1], remaining[b][1]
                if c1.rank == c2.rank:
                    pair_sorted = sorted([c1, c2], key=lambda c: SUIT_ORDER.get(c.suit, 4))
                    groups.append(('near', pair_sorted))
                    pair_used.add(remaining[a][0])
                    pair_used.add(remaining[b][0])
                    break

        # Consecutive same-suit pairs (potential runs)
        for a in range(len(remaining)):
            if remaining[a][0] in pair_used:
                continue
            for b in range(a + 1, len(remaining)):
                if remaining[b][0] in pair_used:
                    continue
                c1, c2 = remaining[a][1], remaining[b][1]
                if c1.suit == c2.suit:
                    r1 = RANK_ORDER.index(c1.rank)
                    r2 = RANK_ORDER.index(c2.rank)
                    if abs(r1 - r2) <= 2:  # Within 2 ranks = potential run
                        pair_sorted = sorted([c1, c2], key=lambda c: RANK_ORDER.index(c.rank))
                        groups.append(('near', pair_sorted))
                        pair_used.add(remaining[a][0])
                        pair_used.add(remaining[b][0])
                        break

        # Phase 3: Isolated cards (discard candidates — high value first)
        isolated = [hand[i] for i in remaining_idx if i not in pair_used]
        isolated.sort(key=lambda c: c.value, reverse=True)
        if isolated:
            groups.append(('isolated', isolated))

        # Rebuild hand in group order
        new_hand = []
        self.hand_groups = []
        for gtype, cards in groups:
            new_hand.extend(cards)
            self.hand_groups.append((gtype, len(cards)))
        self.hand = new_hand

    def add_manual_group(self, cards):
        """Add a specific selection of cards to manual groups."""
        if len(cards) < 2:
            return
        # Remove these cards from any existing manual groups they might be in
        new_cards = list(cards)
        for i in range(len(self.manual_groups) - 1, -1, -1):
            self.manual_groups[i] = [c for c in self.manual_groups[i] if c not in new_cards]
            if len(self.manual_groups[i]) < 2:
                self.manual_groups.pop(i)
        
        self.manual_groups.append(new_cards)
        self.group_hand()

    def remove_manual_group(self, cards):
        """Disbands a manual group if it exists."""
        # Find if these cards exactly match an existing manual group
        for i, mg in enumerate(self.manual_groups):
            if len(mg) == len(cards) and all(c in mg for c in cards):
                self.manual_groups.pop(i)
                self.group_hand()
                return True
        return False

    def reset_turn_state(self):
        self.has_drawn = False
        self.forced_meld_card = None
        self.selected_cards.clear()


class TableMeld:
    """A meld that has been dropped on the table."""
    def __init__(self, cards, owner, meld_type='set'):
        self.cards = list(cards)
        self.owner = owner
        self.meld_type = meld_type

    def can_sapaw(self, card):
        """Check if a card can be added to this meld while keeping it valid."""
        test_cards = self.cards + [card]
        if self.meld_type == 'set':
            return Meld.is_valid_set(test_cards)
        else:
            return Meld.is_valid_run(test_cards)

    def add_card(self, card):
        self.cards.append(card)
        if self.meld_type == 'run':
            self.cards.sort(key=lambda c: RANK_ORDER.index(c.rank))


class Meld:
    RANK_ORDER = RANK_ORDER  # Reference to module-level constant

    @staticmethod
    def is_valid_set(cards):
        """A valid set is 3 or 4 cards of the same rank."""
        if len(cards) < 3 or len(cards) > 4:
            return False
        return all(c.rank == cards[0].rank for c in cards)

    @staticmethod
    def is_valid_run(cards):
        """A valid run is 3+ consecutive cards of the same suit. Ace is LOW only."""
        if len(cards) < 3:
            return False
        if not all(c.suit == cards[0].suit for c in cards):
            return False
        try:
            sorted_cards = sorted(cards, key=lambda c: RANK_ORDER.index(c.rank))
        except ValueError:
            return False
        for i in range(1, len(sorted_cards)):
            curr_idx = RANK_ORDER.index(sorted_cards[i].rank)
            prev_idx = RANK_ORDER.index(sorted_cards[i - 1].rank)
            if curr_idx != prev_idx + 1:
                return False
        return True

    @staticmethod
    def is_valid_meld(cards):
        return Meld.is_valid_set(cards) or Meld.is_valid_run(cards)

    @staticmethod
    def get_meld_type(cards):
        if Meld.is_valid_set(cards):
            return 'set'
        if Meld.is_valid_run(cards):
            return 'run'
        return None
