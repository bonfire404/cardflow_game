from .models import Deck, Player, Meld, TableMeld, TurnPhase, GamePhase


class TongItsEngine:
    def __init__(self, player_names, dealer_idx=0, house_edge=False):
        self.deck = Deck()
        self.players = [
            Player(name, is_human=(i == 0))
            for i, name in enumerate(player_names)
        ]
        self.discard_pile = []
        self.table_melds = []           # All melds on the table
        self.dealer_idx = dealer_idx    # Added dealer_idx
        self.house_edge = house_edge    # Proposal 2 rule
        self.current_turn_index = dealer_idx # Banker starts
        self.current_phase = TurnPhase.WAITING
        self.game_phase = GamePhase.SHUFFLING
        self.is_game_over = False
        self.winner = None
        self.win_method = None          # 'tongits', 'fight', 'deck_empty', 'spread'
        self.turn_number = 0

        # Dealer first turn tracking
        self.is_dealer_initial_discard = False

        # Dealing sequence for UI animation
        self.deal_sequence = []         # List of (player_index, card) in order dealt

        # Event log for UI feedback
        self.last_event = None

        # Fight state mechanism
        self.active_fight = None # {'caller': Player, 'responses': {Player: 'fight'/'fold'}}

    # ─── Initialization ──────────────────────────────────────────────

    def initialize_game(self):
        """
        Filipino Tong-its dealing:
        - Dealer gets 13 cards
        - Others get 12 each
        - Deal order: left of dealer first
        - Remaining cards = Closed Pile (draw pile)
        - NO initial discard from deck — dealer discards from hand first
        """
        self.deal_sequence = []

        # Determine deal order: left of dealer first
        # For 3 players: (dealer+1)%3, (dealer+2)%3, dealer
        others = [(self.dealer_idx + 1) % 3, (self.dealer_idx + 2) % 3]
        deal_round_order = others + [self.dealer_idx]

        # Deal 12 rounds
        for r in range(12):
            for p_idx in deal_round_order:
                card = self.deck.draw()
                if card:
                    self.players[p_idx].hand.append(card)
                    self.deal_sequence.append((p_idx, card))

        # 13th card to dealer
        card = self.deck.draw()
        if card:
            self.players[self.dealer_idx].hand.append(card)
            self.deal_sequence.append((self.dealer_idx, card))

        # Sort bots' hands for consistency, but leave human unsorted initially
        # The human is assumed to be player 0
        for i, p in enumerate(self.players):
            if i != 0:
                p.group_hand()
            else:
                # Just initialize hand groups for correct rendering
                p.hand_groups = [('all', len(p.hand))]

        # Check for Spread (extremely rare: all cards form melds after deal)
        if self._check_spread(self.players[0]):
            return

        # Dealer starts: can meld or sapaw before first discard
        self.is_dealer_initial_discard = True
        self.current_turn_index = self.dealer_idx
        self.players[self.dealer_idx].has_drawn = True # Banker starting with 13 cards counts as having drawn
        self.current_phase = TurnPhase.MELD
        self.game_phase = GamePhase.DEALER_DISCARD
        self.active_fight = None
        self.turn_number = 1
        self._emit_event('game_start', {})

    def _check_spread(self, player):
        """Check if a player has all cards in melds right after dealing (Spread)."""
        from itertools import combinations

        hand = player.hand[:]
        if len(hand) < 12:
            return False

        # Try to find a combination of non-overlapping melds that covers all cards
        # This is a simplified check — just see if all cards can form melds
        melds_found = self._find_covering_melds(hand)
        if melds_found is not None:
            # Instant win
            for meld_cards, mtype in melds_found:
                table_meld = TableMeld(meld_cards, player, mtype)
                self.table_melds.append(table_meld)
                player.melds.append(table_meld)
            player.hand.clear()
            player.is_burned = False
            self.is_game_over = True
            self.winner = player
            self.win_method = 'spread'
            self.game_phase = GamePhase.GAME_OVER
            self._emit_event('spread', {'winner': player})
            return True
        return False

    def _find_covering_melds(self, hand):
        """Try to find non-overlapping melds that cover ALL cards in hand."""
        from itertools import combinations

        if not hand:
            return []

        # Try all possible first melds
        for size in range(3, min(len(hand) + 1, 5)):
            for combo in combinations(range(len(hand)), size):
                cards = [hand[i] for i in combo]
                mtype = Meld.get_meld_type(cards)
                if mtype:
                    remaining = [hand[i] for i in range(len(hand)) if i not in combo]
                    sub_result = self._find_covering_melds(remaining)
                    if sub_result is not None:
                        return [(cards, mtype)] + sub_result
        return None

    # ─── Turn Flow ───────────────────────────────────────────────────

    def get_current_player(self):
        return self.players[self.current_turn_index]

    def next_turn(self):
        """Advance to the next player's turn."""
        if self.deck.remaining() == 0:
            self.end_game_deck_empty()
            return
            
        current = self.get_current_player()
        current.reset_turn_state()
        self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
        self.current_phase = TurnPhase.DRAW
        self.game_phase = GamePhase.PLAYING
        self.turn_number += 1

    def skip_to_discard(self):
        """Skip meld phase, go directly to discard."""
        self.current_phase = TurnPhase.DISCARD

    # ─── Dealer Initial Discard ──────────────────────────────────────

    def dealer_initial_discard(self, card):
        """
        Dealer's very first action: discard one card to start the Discard Pile.
        No draw phase. Dealer goes from 13 cards to 12 cards.
        """
        player = self.players[0]
        if card not in player.hand:
            return False

        player.hand.remove(card)
        self.discard_pile.append(card)
        self.is_dealer_initial_discard = False

        self._emit_event('dealer_discard', {'player': player, 'card': card})

        # Check tongits (won't happen with 12 cards, but safety)
        if not player.hand:
            self._declare_tongits(player)
            return True

        # Move to next player (left of dealer)
        self.next_turn()
        return True

    # ─── Draw Actions ────────────────────────────────────────────────

    def _check_and_trigger_tongits(self, player):
        """
        Check if the player's entire hand can be formed into melds.
        If yes, automatically drop them and declare Tong-its.
        """
        if not player.hand:
            self._declare_tongits(player)
            return True

        covering_melds = self._find_covering_melds(player.hand)
        if covering_melds:
            for meld_cards, mtype in covering_melds:
                # Manually add these to the table to reflect automatic 'clearing'
                table_meld = TableMeld(meld_cards, player, mtype)
                self.table_melds.append(table_meld)
                player.melds.append(table_meld)
                player.is_burned = False
            
            player.hand.clear()
            if player.forced_meld_card:
                player.forced_meld_card = None
                
            self._declare_tongits(player)
            return True
        return False

    def draw_from_deck(self, player):
        """Draw the top card from the Closed Pile."""
        if self.current_phase != TurnPhase.DRAW or self.game_phase != GamePhase.PLAYING:
            return False
        if player.has_drawn:
            return False

        card = self.deck.draw()
        if card is None:
            self.end_game_deck_empty()
            return False

        player.hand.append(card)
        player.has_drawn = True
        self._emit_event('draw_deck', {'player': player, 'card': card})

        # Check for auto-win (Spread/Tongits)
        if self._check_and_trigger_tongits(player):
            return True

        self.current_phase = TurnPhase.MELD
        return True

    def draw_from_discard(self, player):
        """
        Draw from the Discard Pile.
        RULE: You MUST immediately form a meld with this card and expose it.
        """
        if self.current_phase != TurnPhase.DRAW or self.game_phase != GamePhase.PLAYING:
            return False
        if player.has_drawn:
            return False
        if not self.discard_pile:
            return False

        top_card = self.discard_pile[-1]

        # Validate: can this card form a meld with hand cards?
        if not self._can_meld_with_discard(player, top_card):
            return False

        self.discard_pile.pop()
        player.hand.append(top_card)
        player.has_drawn = True
        player.forced_meld_card = top_card  # MUST meld this card before discard

        self._emit_event('draw_discard', {'player': player, 'card': top_card})

        # Check for auto-win (Spread/Tongits)
        if self._check_and_trigger_tongits(player):
            return True

        self.current_phase = TurnPhase.MELD
        return True

    def _can_meld_with_discard(self, player, discard_card):
        """Check if picking up this card allows forming a meld."""
        from itertools import combinations
        test_hand = player.hand + [discard_card]

        for size in range(3, len(test_hand) + 1):
            for combo in combinations(test_hand, size):
                if discard_card in combo:
                    if Meld.is_valid_meld(list(combo)):
                        return True
        return False

    # ─── Meld Actions ────────────────────────────────────────────────

    def drop_meld(self, player, cards):
        """
        Drop a meld (lapag) from the player's hand onto the table.
        Placed beside the player who dropped it.
        """
        if self.current_phase != TurnPhase.MELD:
            return False
        if not player.has_drawn:
            return False

        meld_type = Meld.get_meld_type(cards)
        if meld_type is None:
            return False

        for card in cards:
            if card not in player.hand:
                return False

        for card in cards:
            player.hand.remove(card)

        table_meld = TableMeld(cards, player, meld_type)
        self.table_melds.append(table_meld)
        player.melds.append(table_meld)
        player.is_burned = False
        
        # Dropping a new meld clears the sapaw restriction!
        player.has_been_sapawed = False

        # Clear forced meld if the required card is in this meld
        if player.forced_meld_card and player.forced_meld_card in cards:
            player.forced_meld_card = None

        self._emit_event('meld_drop', {
            'player': player,
            'cards': cards,
            'meld_type': meld_type
        })

        # Check for auto-win (Spread/Tongits)
        if self._check_and_trigger_tongits(player):
            return True

        return True

    def sapaw(self, player, card, target_meld):
        """
        Add a card to an existing table meld (sapaw / laying off).
        RULE: If you sapaw on an opponent, that opponent cannot fight you this round.
        """
        if self.current_phase not in (TurnPhase.DRAW, TurnPhase.MELD):
            return False
        if card not in player.hand:
            return False
        if not target_meld.can_sapaw(card):
            return False

        player.hand.remove(card)
        target_meld.add_card(card)

        # Track sapaw restriction: if sapawing on opponent's meld
        if target_meld.owner != player:
            target_meld.owner.has_been_sapawed = True

        self._emit_event('sapaw', {
            'player': player,
            'card': card,
            'target_meld': target_meld,
            'target_owner': target_meld.owner
        })

        # Check for auto-win (Spread/Tongits)
        if self._check_and_trigger_tongits(player):
            return True

        player.is_burned = False # Connecting clears the burned status
        return True

    # ─── Discard Action ──────────────────────────────────────────────

    def discard_card(self, player, card):
        """Discard a card to end the turn."""
        if self.current_phase not in (TurnPhase.MELD, TurnPhase.ACTION, TurnPhase.DISCARD):
            return False
        if card not in player.hand:
            return False
        if not player.has_drawn:
            return False

        # RULE: If player drew from discard pile, they MUST meld that card first
        if player.forced_meld_card is not None:
            return False  # Can't discard until forced meld is done

        player.hand.remove(card)
        self.discard_pile.append(card)

        self._emit_event('discard', {'player': player, 'card': card})

        # If hand is completely empty, or all remaining cards form valid melds (0 points),
        # the player has no unmatched cards and therefore wins by Tong-its!
        if not player.hand or player.calculate_points() == 0:
            self._declare_tongits(player)
            return True

        if not self.is_game_over:
            player.has_been_sapawed = False # Restriction clears AFTER the turn ends
            self.next_turn()

        return True

    # ─── Fight / Tong-its ────────────────────────────────────────────

    def call_fight(self, caller):
        """
        Call a fight (challenge).
        RULES:
        - Must have at least 1 meld on the table
        - Must NOT be burned
        - No one has sapawed on your melds this round
        """
        if caller.is_burned:
            return False
        if caller.has_been_sapawed:
            return False
        if not caller.melds:
            return False

        # Initialize the fight state
        self.game_phase = GamePhase.RESOLVING_FIGHT
        self.active_fight = {
            'caller': caller,
            'responses': {},  # player -> 'fight'/'fold'
        }
        
        # Burned players or players with NO melds (0 points down) automatically fold/burn
        for p in self.players:
            if p != caller:
                if p.is_burned or len(p.melds) == 0:
                    p.is_burned = True  # Enforce burned status if they had 0 melds and someone fights
                    self.active_fight['responses'][p] = 'fold'
        
        self._emit_event('fight_called', {'caller': caller})
        
        # Check if we should immediately resolve it (if all others are burned)
        self._check_fight_resolution()
        
        return True

    def respond_to_fight(self, player, response: str):
        """
        Respond to a called fight with 'fight' (challenge) or 'fold'.
        """
        if self.game_phase != GamePhase.RESOLVING_FIGHT or not self.active_fight:
            return False
            
        if player == self.active_fight['caller']:
            return False
            
        self.active_fight['responses'][player] = response
        self._emit_event('fight_response', {'player': player, 'response': response})
        self._check_fight_resolution()
        return True
        
    def _check_fight_resolution(self):
        if not self.active_fight:
            return
            
        caller = self.active_fight['caller']
        responses = self.active_fight['responses']
        
        # Determine if all non-caller players have responded
        all_responded = all(p in responses for p in self.players if p != caller)
        
        if all_responded:
            # Resolve the fight
            self.is_game_over = True
            
            # Find eligible players (caller + anyone who fought)
            eligible = [caller]
            for p, resp in responses.items():
                if resp == 'fight' and not p.is_burned:
                    eligible.append(p)
            
            # Find winner based on points
            best = min(eligible, key=lambda p: p.calculate_points())
            
            # Tie breaker: If tied, challengers usually win against caller (or non-caller closest to caller)
            # For simplicity, if caller tied with a challenger, challenger wins.
            tied_players = [p for p in eligible if p.calculate_points() == best.calculate_points()]
            if len(tied_players) > 1:
                # Proposal 2: House Edge Tie-Breaker
                banker = self.players[self.dealer_idx]
                if self.house_edge and banker in tied_players:
                    best = banker
                else:
                    # Traditional tie-break: challenger wins over caller
                    best_challenger = next((p for p in tied_players if p != caller), tied_players[0])
                    best = best_challenger
                
            self.winner = best
            self.win_method = 'fight_won' if best == caller else 'fight_lost'
            self.game_phase = GamePhase.GAME_OVER
            
            # Calculate final statuses for UI
            player_statuses = {}
            for p in self.players:
                if p == best:
                    player_statuses[p.name] = "WINNER"
                elif p == caller:
                    player_statuses[p.name] = "CALLER"
                elif p in responses:
                    resp = responses[p]
                    if resp == 'fight':
                        player_statuses[p.name] = "CHALLENGED"
                    else:
                        # Distinguish between folded and burned
                        if p.is_burned:
                            player_statuses[p.name] = "BURNED"
                        else:
                            player_statuses[p.name] = "FOLDED"
                else:
                    # Should not happen if all responded, but safety Check
                    if p.is_burned:
                        player_statuses[p.name] = "BURNED"
                    else:
                        player_statuses[p.name] = "FOLDED"

            self._emit_event('fight', {
                'caller': caller,
                'winner': best,
                'scores': {p.name: p.calculate_points() for p in self.players},
                'statuses': player_statuses
            })
    def _declare_tongits(self, player):
        """A player emptied their hand and wins outright."""
        self.is_game_over = True
        self.winner = player
        self.win_method = 'tongits'
        self.game_phase = GamePhase.GAME_OVER
        self._emit_event('tongits', {'winner': player})

    def end_game_deck_empty(self):
        """Closed pile is empty — lowest points wins."""
        self.is_game_over = True
        self.win_method = 'deck_empty'
        self.game_phase = GamePhase.GAME_OVER

        eligible = [p for p in self.players if not p.is_burned]
        if not eligible:
            eligible = self.players

        min_points = min(p.calculate_points() for p in eligible)
        tied_players = [p for p in eligible if p.calculate_points() == min_points]
        
        if len(tied_players) > 1 and self.house_edge:
            banker = self.players[self.dealer_idx]
            if banker in tied_players:
                self.winner = banker
            else:
                self.winner = tied_players[0]
        else:
            self.winner = tied_players[0]

        self._emit_event('deck_empty', {
            'winner': self.winner,
            'scores': {p.name: p.calculate_points() for p in self.players}
        })

    # ─── Queries ─────────────────────────────────────────────────────

    def can_player_fight(self, player):
        """Check if a player is eligible to call fight."""
        if self.current_phase not in (TurnPhase.DRAW, TurnPhase.MELD, TurnPhase.ACTION):
            return False
        if self.deck.remaining() == 0:
            return False # NEW: Cannot fight if deck is empty
        if player.has_drawn:
            return False # NEW: Cannot fight if already drawn a card this turn
        if player.is_burned:
            return False
        if player.has_been_sapawed:
            return False
        if not player.melds:
            return False
        return True

    def has_forced_meld_pending(self, player):
        """Check if player still needs to meld the discard-drawn card."""
        return player.forced_meld_card is not None

    def get_possible_melds(self, player):
        """Find all valid melds in a player's hand."""
        from itertools import combinations
        valid = []
        for size in range(3, len(player.hand) + 1):
            for combo in combinations(player.hand, size):
                cards = list(combo)
                mtype = Meld.get_meld_type(cards)
                if mtype:
                    valid.append((cards, mtype))
        return valid

    def get_sapaw_options(self, player):
        """Find all valid sapaw opportunities for a player."""
        options = []
        for card in player.hand:
            for meld in self.table_melds:
                if meld.can_sapaw(card):
                    options.append((card, meld))
        return options

    def get_scores(self):
        return {p.name: p.calculate_points() for p in self.players}

    # ─── Events ──────────────────────────────────────────────────────

    def _emit_event(self, event_type, data):
        self.last_event = {
            'type': event_type,
            'data': data,
            'turn': self.turn_number,
        }
