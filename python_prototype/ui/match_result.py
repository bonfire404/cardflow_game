"""Match result handling — extracted from main.py game-over transition."""

from ui.database import load_user_profile, save_user_profile, add_match_history_record
from ui.progression_manager import apply_rewards
from game.economy import EconomyManager
from game.betting_configs import BETTING_CONFIGS


def handle_match_end(engine, player_name, player_stats, profile_data,
                     chip_system, dealer_mgr, quest_modal, audio,
                     target_bet_limit, current_bet_amount, layout, player,
                     economy_mgr=None):
    """
    Process end-of-match: calculate payout, update stats, save profile, build floats.
    
    Args:
        engine: TongItsEngine (must have is_game_over == True)
        player_name: Human player's name
        player_stats: Dict of player stats (mutated in-place)
        profile_data: Full profile data dict (mutated in-place)
        chip_system: ChipSystem instance
        dealer_mgr: DealerManager instance
        quest_modal: DailyQuestModal instance
        audio: AudioManager instance
        target_bet_limit: Current bet limit
        current_bet_amount: Player's bet amount for this match
        layout: Layout dictionary
        player: Player object (engine.players[0])
        economy_mgr: Optional EconomyManager for mode-based payout rules
    
    Returns:
        dict with keys:
            'is_win': bool
            'payout': int
            'deltas': dict of {player_idx: coin_delta}
            'xp_gained': int
            'rp_gained': int
            'post_game_floats': list of float animation dicts
            'payout_details': dict with economy mode info (if economy_mgr used)
    """
    # Determine winner info
    dealer_has_won = (engine.winner and engine.players.index(engine.winner) == dealer_mgr.get_idx())
    dealer_streak = dealer_mgr.win_streak + (1 if dealer_has_won else 0)
    
    is_win = (engine.winner and engine.winner.name == player_name)
    
    # Play appropriate SFX
    if is_win:
        if audio.sfx_win: audio.sfx_win.play()
    else:
        if player.is_burned and audio.sfx_burned:
            audio.sfx_burned.play()
        elif audio.sfx_lose:
            audio.sfx_lose.play()
    
    # Calculate payout using EconomyManager if available, else fallback to legacy
    payout = 0
    deltas = {0: 0, 1: 0, 2: 0}
    payout_details = None
    
    if engine.winner:
        win_idx = engine.players.index(engine.winner)
        
        if economy_mgr is not None and isinstance(target_bet_limit, int):
            # --- NEW: Mode-based payout via EconomyManager ---
            win_method = getattr(engine, 'win_method', 'fight')
            caller_idx = None
            if hasattr(engine, 'active_fight') and engine.active_fight:
                caller = engine.active_fight.get('caller')
                if caller:
                    try:
                        caller_idx = engine.players.index(caller)
                    except ValueError:
                        caller_idx = None
            
            burned_indices = [i for i, p in enumerate(engine.players) if p.is_burned]
            
            deltas, payout_details = economy_mgr.resolve_payouts(
                winner_idx=win_idx,
                dealer_idx=engine.dealer_idx,
                win_streak=dealer_streak,
                win_method=win_method,
                caller_idx=caller_idx,
                burned_indices=burned_indices
            )
            
            payout = deltas[win_idx]
            
            # Reset banker pot if it was fully paid out
            if payout_details.get('banker_pot_payout', 0) >= chip_system.banker_pot:
                chip_system.reset_banker_pot()
        else:
            # --- LEGACY fallback for non-integer bet limits (EASY/MEDIUM/HARD) ---
            payout = chip_system.main_pot
            if dealer_has_won and dealer_streak >= 2:
                payout += chip_system.banker_pot
                chip_system.reset_banker_pot()
            deltas[win_idx] = payout
            for i in range(3):
                if i != win_idx:
                    deltas[i] = -(current_bet_amount * 3 if engine.dealer_idx == i else current_bet_amount)
    
    engine.payout = payout
    
    # Apply XP/RP rewards
    is_tongits = (getattr(engine, 'win_method', '') == 'tongits')
    xp_gained, rp_gained = apply_rewards(is_win, is_tongits, target_bet_limit)
    
    # Reload profile to get latest progression values
    updated_profile = load_user_profile()
    
    # Update stats
    if is_win:
        player_stats["wins"] += 1
        player_stats["streak"] += 1
        player_stats["biggest_win"] = max(player_stats.get("biggest_win", 0), payout)
        player_stats["coins"] += payout
        quest_modal.update_quest("win", 1)
        quest_modal.update_quest("streak", 1)
    else:
        player_stats["losses"] += 1
        player_stats["streak"] = 0
        quest_modal.update_quest("streak_reset", 0)
        # Deduct losses from coins based on economy deltas
        player_loss = abs(deltas.get(0, 0))
        if player_loss > 0 and not is_win:
            player_stats["coins"] = max(0, player_stats["coins"] - player_loss)
        
    quest_modal.update_quest("play", 1)

    # Sync progression values so they aren't overwritten
    player_stats["xp"] = updated_profile.get("xp", 0)
    player_stats["rp"] = updated_profile.get("rp", 0)
    player_stats["level"] = updated_profile.get("level", 1)
    player_stats["rank"] = updated_profile.get("rank", "Wood")

    profile_data.update(player_stats)
    save_user_profile(profile_data)

    # Save to Match History Table
    coins_change = deltas.get(0, 0)
    result_str = "WIN" if is_win else "LOSE"
    mode_str = "CASINO CLASSIC"
    if isinstance(target_bet_limit, str):
        mode_str = "AI ARENA"
    elif isinstance(target_bet_limit, int) and target_bet_limit >= 1000:
        mode_str = "RANK"

    add_match_history_record(
        mode=mode_str,
        result=result_str,
        coins_change=coins_change,
        rp_change=rp_gained,
        xp_change=xp_gained
    )
    
    mode_name = payout_details['mode'] if payout_details else 'Legacy'
    print(f"Match End [{mode_name}]: XP +{xp_gained}, RP {rp_gained:+}, Payout {payout}")

    # Build floating text animations for coin changes
    post_game_floats = []
    if engine.winner:
        for pid in range(3):
            px = layout['hand_center_x'] if pid == 0 else layout[f'bot{pid}_x']
            py = layout['hand_y'] if pid == 0 else layout[f'bot{pid}_y']
            
            delta = deltas.get(pid, 0)
            if delta > 0:
                post_game_floats.append({
                    'text': f"+{delta}", 'color': (100, 255, 100),
                    'x': px, 'y': py, 'life': 3.0, 'dy': -20
                })
            elif delta < 0:
                post_game_floats.append({
                    'text': f"{delta}", 'color': (255, 80, 80),
                    'x': px, 'y': py, 'life': 3.0, 'dy': -20
                })
    
    return {
        'is_win': is_win,
        'payout': payout,
        'deltas': deltas,
        'xp_gained': xp_gained,
        'rp_gained': rp_gained,
        'post_game_floats': post_game_floats,
        'payout_details': payout_details,
    }
