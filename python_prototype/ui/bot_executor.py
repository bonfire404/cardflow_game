"""Bot AI turn execution — extracted from main.py game loop."""

from game.ai_bot import RuleBasedAI
from game.models import TurnPhase, GamePhase
from ui.animation import Timer


def execute_bot_fight_responses(engine, player, ai_timer, dt):
    """
    Let bots respond to an active fight sequentially.
    
    Returns:
        Updated ai_timer (Timer or None).
    """
    if engine.game_phase != GamePhase.RESOLVING_FIGHT or engine.is_game_over:
        return ai_timer
    
    for bot_idx in [1, 2]:
        bot_player = engine.players[bot_idx]
        if bot_player not in engine.active_fight['responses'] and bot_player != engine.active_fight['caller']:
            if ai_timer is None:
                human_done = (player in engine.active_fight['responses'])
                delay = (0.2 + bot_idx * 0.15) if human_done else (0.5 + bot_idx * 0.3)
                ai_timer = Timer(delay)
            if ai_timer.update(dt):
                response = RuleBasedAI._should_respond_fight(engine, bot_player, engine.active_fight)
                engine.respond_to_fight(bot_player, response)
                ai_timer = None
            break  # Wait for this bot to finish deciding before moving to the next
    
    return ai_timer


def execute_bot_turn(engine, layout, flying_cards, particles, audio, ai_timer, dt,
                     game_state, calc_meld_zones_fn):
    """
    Execute one tick of bot AI turn logic (draw, meld/sapaw, discard).
    
    Args:
        engine: TongItsEngine instance
        layout: Layout dictionary
        flying_cards: List of flying card animation dicts (mutated in-place)
        particles: ParticleEmitter instance
        audio: AudioManager instance
        ai_timer: Current Timer or None
        dt: Delta time
        game_state: Current game state string
        calc_meld_zones_fn: Function to calculate meld zones for sapaw targeting
    
    Returns:
        tuple: (updated_ai_timer, updated_game_state)
    """
    is_player_turn = (engine.current_turn_index == 0)
    is_blocking = bool(flying_cards)
    
    if not ((game_state in ('playing', 'dealer_discard')) and not is_player_turn and not is_blocking):
        return ai_timer, game_state
    
    if not ai_timer:
        ai_timer = Timer(1.0)
    
    if not ai_timer.update(dt):
        return ai_timer, game_state
    
    bot = engine.get_current_player()
    pi = engine.current_turn_index
    
    # Step 0: Check for Fight (Pre-draw)
    if engine.current_phase == TurnPhase.DRAW and engine.game_phase != GamePhase.RESOLVING_FIGHT:
        if RuleBasedAI._should_call_fight(engine, bot):
            engine.call_fight(bot)
            if audio.sfx_fight: audio.sfx_fight.play()
            return None, game_state  # Reset timer for next phase
    
    # Step 1: Draw
    if engine.current_phase == TurnPhase.DRAW:
        bot_x = layout[f'bot{pi}_x']
        bot_y = layout[f'bot{pi}_y']
        if engine.discard_pile and engine._can_meld_with_discard(bot, engine.discard_pile[-1]):
            drawn_card = engine.discard_pile[-1]
            if engine.draw_from_discard(bot):
                if audio.sfx_draw: audio.sfx_draw.play()
                if not bot.hand:
                    particles.emit(layout[f'bot{pi}_meld_x'], layout[f'bot{pi}_meld_y'], count=30)
                else:
                    possible_melds = engine.get_possible_melds(bot)
                    possible_melds.sort(key=lambda x: len(x[0]), reverse=True)
                    meld_to_drop = None
                    for meld, mtype in possible_melds:
                        if drawn_card in meld:
                            meld_to_drop = meld
                            break

                    target_x = layout[f'bot{pi}_meld_x']
                    target_y = layout[f'bot{pi}_meld_y']

                    if meld_to_drop:
                        for i, c in enumerate(meld_to_drop):
                            flying_cards.append({
                                'start': (layout['discard_x'], layout['discard_y']) if c == drawn_card else (bot_x, bot_y),
                                'end': (target_x + i * 20, target_y),       
                                'elapsed': -i * 0.08, 'duration': 0.45, 'player_idx': pi,
                                'is_face_up': True, 'card': c
                            })
                        engine.drop_meld(bot, list(meld_to_drop))        
                        if audio.sfx_draw: audio.sfx_draw.play()
                        particles.emit(target_x, target_y, count=15)        
                    else:
                        flying_cards.append({
                            'start': (layout['discard_x'], layout['discard_y']),
                            'end': (bot_x, bot_y), 'elapsed': 0, 'duration': 0.4,
                            'player_idx': pi, 'is_face_up': True, 'card': drawn_card
                        })
        else:
            if engine.draw_from_deck(bot):
                if audio.sfx_draw: audio.sfx_draw.play()
                if not bot.hand:
                    particles.emit(layout[f'bot{pi}_meld_x'], layout[f'bot{pi}_meld_y'], count=30)
                else:
                    drawn_card = bot.hand[-1]
                    flying_cards.append({
                        'start': (layout['deck_x'], layout['deck_y']),  
                        'end': (bot_x, bot_y), 'elapsed': 0, 'duration': 0.4,
                        'player_idx': pi, 'is_face_up': False, 'card': drawn_card
                    })
        ai_timer = Timer(2.0)  # Wait for draw anim

    # Step 2: Meld/Action
    elif engine.current_phase == TurnPhase.MELD:
        dropped_any = False

        # Use the full strategic AI meld logic (handles holding, multiple drops, etc.)
        pre_meld_count = len(bot.melds)
        RuleBasedAI._do_melds(engine, bot)
        if engine.is_game_over:
            return None, game_state
        
        new_melds_dropped = len(bot.melds) - pre_meld_count
        if new_melds_dropped > 0:
            dropped_any = True
            # Animate the most recently dropped melds
            target_x = layout[f'bot{pi}_meld_x']
            target_y = layout[f'bot{pi}_meld_y']
            source_x = layout[f'bot{pi}_x']
            source_y = layout[f'bot{pi}_y']
            for m_idx in range(pre_meld_count, len(bot.melds)):
                tm = bot.melds[m_idx]
                for i, c in enumerate(tm.cards):
                    flying_cards.append({
                        'start': (source_x, source_y), 'end': (target_x + i * 20, target_y),
                        'elapsed': -i * 0.08, 'duration': 0.45, 'player_idx': pi,
                        'is_face_up': True, 'card': c
                    })
            if audio.sfx_draw: audio.sfx_draw.play()
            particles.emit(target_x, target_y, count=15)

        # Use strategic sapaw (with deception logic for HARD+ bots)
        pre_sapaw_melds = sum(len(tm.cards) for tm in engine.table_melds)
        RuleBasedAI._do_sapaw(engine, bot)
        if engine.is_game_over:
            return None, game_state
        
        post_sapaw_melds = sum(len(tm.cards) for tm in engine.table_melds)
        if post_sapaw_melds > pre_sapaw_melds:
            dropped_any = True
            if audio.sfx_sapaw: audio.sfx_sapaw.play()

        if not dropped_any:
            if engine.game_phase != GamePhase.RESOLVING_FIGHT and RuleBasedAI._should_call_fight(engine, bot):     
                engine.call_fight(bot)
                if audio.sfx_fight: audio.sfx_fight.play()

            engine.skip_to_discard()
            ai_timer = Timer(1.0)
        else:
            ai_timer = Timer(2.0)

    # Step 3: Discard
    elif engine.current_phase == TurnPhase.DISCARD:
        card = RuleBasedAI._choose_discard(engine, bot)
        if card:
            source_x = layout[f'bot{pi}_x']
            source_y = layout[f'bot{pi}_y']
            target_x = layout['discard_x']
            target_y = layout['discard_y']

            if engine.discard_card(bot, card):
                flying_cards.append({
                    'start': (source_x, source_y), 'end': (target_x, target_y),
                    'elapsed': 0, 'duration': 0.45, 'player_idx': pi,
                    'is_face_up': True, 'card': card
                })
                
                if game_state == 'dealer_discard':
                    game_state = 'playing'
        ai_timer = None
    
    return ai_timer, game_state
