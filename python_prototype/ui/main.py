import sys, os, math, pygame, random, json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from game.engine import TongItsEngine
from game.ai_bot import RuleBasedAI
from game.models import TurnPhase, GamePhase, Meld as MC, RANK_ORDER
from ui.animation import (AnimationManager, Animation, Timer, ParticleEmitter,
                           ease_out_cubic, ease_out_back, ease_in_out_quad, linear)
from ui.ui_components import (Colors, Button, PhaseIndicator, Badge, PlayerPanel,
                               GameOverOverlay, MeldDisplay, FightResolutionOverlay)
from ui.lobby import Lobby
from ui.profile import ProfileModal
from ui.dealer import DealerManager

# --- Gendered Identity Pools ---
MALE_NAMES = ["Juan", "Rico", "Dingdong", "Vhong", "Isko", "Vico", "Bong", "Ping", "Manny", "Iloy", "Gardo", "Ador"]
FEMALE_NAMES = ["Maria", "Liza", "Marian", "Anne", "Karylle", "Leni", "Korina", "Darna", "Narda", "Inday", "Nena"]

def get_card_filename(card):
    suit = card.suit.lower()
    rank = card.rank
    rank_map = {
        'Ace': 'ace', 
        'Jack': 'jack', 
        'Queen': 'queen', 
        'King': 'king'
    }
    rank_str = rank_map.get(rank, rank)
    if rank_str.isdigit() and len(rank_str) == 1:
        rank_str = f"0{rank_str}"
    elif rank_str == '10':
        rank_str = '10'
    return f"{suit}_{rank_str}.png"

def draw_hand_ribbon(surface, rects, text="", is_front=True):
    """Draws a premium ribbon wrap around a set of card rects."""
    if not rects: return
    
    # Calculate bounding box
    min_x = min(r.x for r in rects)
    max_x = max(r.x + r.w for r in rects)
    min_y = min(r.y for r in rects)
    max_y = max(r.y + r.h for r in rects)
    
    rw = (max_x - min_x)
    rh = 30
    rx = min_x
    screen_h = surface.get_height()
    ry = (screen_h - 170) + 85 - rh // 2
    
    ribbon_color = Colors.RIBBON_RED
    shadow_color = Colors.RIBBON_SHADOW
    gold_trim = Colors.RIBBON_GOLD
    
    if not is_front:
      
        back_surf = pygame.Surface((rw + 12, rh + 4), pygame.SRCALPHA)
        pygame.draw.rect(back_surf, shadow_color, (0, 2, rw + 12, rh), border_radius=4)
       
        pygame.draw.polygon(back_surf, shadow_color, [(0, 0), (15, rh//2), (0, rh)])
        pygame.draw.polygon(back_surf, shadow_color, [(rw+12, 0), (rw+12-15, rh//2), (rw+12, rh)])
        surface.blit(back_surf, (rx - 6, ry - 2))
    else:
        
        front_surf = pygame.Surface((rw, rh), pygame.SRCALPHA)
        
        pygame.draw.rect(front_surf, ribbon_color, (0, 0, rw, rh), border_radius=2)
        pygame.draw.rect(front_surf, (255, 255, 255, 40), (0, 0, rw, 2))
        pygame.draw.rect(front_surf, (0, 0, 0, 40), (0, rh-2, rw, 2))      
        
        pygame.draw.line(front_surf, gold_trim, (0, 4), (rw, 4), 1)
        pygame.draw.line(front_surf, gold_trim, (0, rh-5), (rw, rh-5), 1)
        
        # Shine effect
        shine = pygame.Surface((rw, rh), pygame.SRCALPHA)
        pygame.draw.rect(shine, (255, 255, 255, 30), (rw//4, 0, rw//2, rh))
        front_surf.blit(shine, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

        surface.blit(front_surf, (rx, ry))
        
        # Label
        if text:
            try:
               
                f = pygame.font.SysFont("Arial", 14, bold=True)
                txt_surf = f.render(text.upper(), True, gold_trim)
                surface.blit(txt_surf, (rx + rw//2 - txt_surf.get_width()//2, ry + rh//2 - txt_surf.get_height()//2))
            except: pass

# --- Profile Persistence ---
PROFILE_FILE = "user_profile.json"

def save_user_profile(stats_dict):
    try:
        with open(PROFILE_FILE, "w") as f:
            json.dump(stats_dict, f)
    except Exception as e:
        print(f"Save error: {e}")

def load_user_profile():
    defaults = {
        "name": "Player",
        "avatar_idx": 0,
        "wins": 0,
        "losses": 0,
        "coins": 10000,
        "rank": "Beginner"
    }
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r") as f:
                data = json.load(f)
                # Merge with defaults for robustness
                for k, v in defaults.items():
                    if k not in data: data[k] = v
                return data
        except Exception as e:
            print(f"Load error: {e}")
    return defaults

def main():
    pygame.init()
    # Default windowed resolution (1280x720)
    WIDTH, HEIGHT = 1280, 720
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Mama's Go — Tong-its")

    # Initialize variables used in on_resize closure early
    background_raw = background = None
    lobby_bkg_raw = lobby_bkg = None
    lobby = None
    profile_modal = None
    phase_indicator = None
    game_over_overlay = None
    fight_resolution_overlay = None
    layout = None
    
    # Turn Timing & State Tracking
    TURN_LIMIT = 15.0
    turn_timer = TURN_LIMIT
    last_turn_state = (0, None)
    meld_hit_zones = []

    def on_resize(w, h):
        nonlocal WIDTH, HEIGHT, screen, background, lobby_bkg, layout, lobby
        nonlocal profile_modal, phase_indicator, game_over_overlay, fight_resolution_overlay
        WIDTH, HEIGHT = w, h
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        
        # Scale backgrounds
        if background_raw:
            background = pygame.transform.scale(background_raw, (WIDTH, HEIGHT))
        if lobby_bkg_raw:
            lobby_bkg = pygame.transform.scale(lobby_bkg_raw, (WIDTH, HEIGHT))
            
        # Update managers and UI
        layout = calc_layout()
        lobby.w, lobby.h = WIDTH, HEIGHT
        lobby.recalc_banners()
        profile_modal.on_resize(WIDTH, HEIGHT)
        phase_indicator.x = WIDTH // 2
        
        if game_over_overlay:
            game_over_overlay.reposition(WIDTH, HEIGHT)
        if fight_resolution_overlay:
            fight_resolution_overlay.on_resize(WIDTH, HEIGHT)

    # ── Assets ────────────────────────────────────────────────────
    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets'))
    
    bg_pool = ["clean_card_table.png", "mahogany_card_table.png"]

    def refresh_background():
        nonlocal background_raw, background
        try:
            selected = random.choice(bg_pool)
            bg_path = os.path.join(assets_dir, "images", selected)
            background_raw = pygame.image.load(bg_path).convert()
            background = pygame.transform.scale(background_raw, (WIDTH, HEIGHT))
        except Exception as e:
            print(f"Bkg error: {e}")
            background_raw = background = None

    refresh_background()

    # Lobby Background (specific)
    try:
        lb_bkg_path = os.path.join(assets_dir, "images", "casino_lobby_bg.png")
        lobby_bkg_raw = pygame.image.load(lb_bkg_path).convert()
        lobby_bkg = pygame.transform.scale(lobby_bkg_raw, (WIDTH, HEIGHT))
    except:
        lobby_bkg_raw = lobby_bkg = None

    card_back_path = os.path.join(assets_dir, "Casino", "Cards", "back04.png")
    try: card_back_raw = pygame.image.load(card_back_path).convert_alpha()
    except Exception: card_back_raw = None

    # Dealer Manager
    dealer_mgr = DealerManager(assets_dir)

    avatars_dir = os.path.join(assets_dir, "images", "avatars")
    av_pools = {'male': [], 'female': [], 'any': []}
    
    if os.path.exists(avatars_dir):
        for fn in os.listdir(avatars_dir):
            if fn.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                try:
                    img = pygame.image.load(os.path.join(avatars_dir, fn)).convert_alpha()
                    fn_lower = fn.lower()
                    if any(k in fn_lower for k in ['female', 'women', 'girl', 'lady', 'p_female']): 
                        av_pools['female'].append(img)
                    elif any(k in fn_lower for k in ['male', 'man', 'boy', 'guy', 'men', 'p_male']): 
                        av_pools['male'].append(img)
                    else: 
                        av_pools['any'].append(img)
                except: pass
    
    for g in ['male', 'female']:
        if not av_pools[g]: av_pools[g] = av_pools['any']

    cards_dir = os.path.join(assets_dir, "Casino", "Cards")
    card_image_cache = {}
    CARD_SCALE = 0.55 
    BASE_CARD_W = BASE_CARD_H = 0

    def get_card_image(card, scale=CARD_SCALE):
        nonlocal BASE_CARD_W, BASE_CARD_H
        fname = get_card_filename(card)
        key = (fname, scale)
        if key not in card_image_cache:
            try:
                raw = pygame.image.load(os.path.join(cards_dir, fname)).convert_alpha()
                w, h = int(raw.get_width()*scale), int(raw.get_height()*scale)
                card_image_cache[key] = pygame.transform.scale(raw, (w, h))
                if BASE_CARD_W == 0: BASE_CARD_W, BASE_CARD_H = w, h
            except Exception: card_image_cache[key] = None
        return card_image_cache[key]

    def get_card_back(scale=CARD_SCALE):
        if not card_back_raw: return None
        key = ('_back', scale)
        if key not in card_image_cache:
            w, h = int(card_back_raw.get_width()*scale), int(card_back_raw.get_height()*scale)
            card_image_cache[key] = pygame.transform.scale(card_back_raw, (w, h))
        return card_image_cache[key]

    # Pre-warm card dims
    _d = __import__('game.models', fromlist=['Deck']).Deck()
    if _d.cards: get_card_image(_d.cards[0])
    del _d

    # ── Fonts ─────────────────────────────────────────────────────
    fonts_dir = os.path.join(assets_dir, "fonts")
    def load_font(name_query, size):
        
        for root, dirs, files in os.walk(fonts_dir):
            for fn in files:
                if name_query.lower() in fn.lower() and fn.endswith(('.ttf','.otf')):
                    try: return pygame.font.Font(os.path.join(root, fn), size)
                    except: pass
        return pygame.font.SysFont("Arial", size)

    font_title = load_font("Sora-Bold", 40)
    font_body = load_font("Inter_24pt-Medium", 20)
    font_small = load_font("Inter_18pt-Regular", 16)
    font_btn = load_font("Inter_18pt-SemiBold", 18)
    font_phase = load_font("JetBrainsMono", 16)
    
    # ── Profile & Stats Loading ───────────────────────────────────
    profile_data = load_user_profile()
    player_name = profile_data["name"]
    p_av_idx = profile_data["avatar_idx"]
    player_stats = {
        "coins": profile_data["coins"],
        "rank": profile_data["rank"],
        "wins": profile_data["wins"],
        "losses": profile_data["losses"]
    }

    # ── Engine ────────────────────────────────────────────────────
 
    def generate_npc(exclude_names=None, exclude_avatars=None):
        if exclude_names is None: exclude_names = []
        if exclude_avatars is None: exclude_avatars = []
        
        gender = random.choice(['male', 'female'])
        # Ensure name uniqueness
        pool_names = MALE_NAMES if gender == 'male' else FEMALE_NAMES
        available_names = [n for n in pool_names if n not in exclude_names]
        if not available_names: available_names = pool_names
        name = random.choice(available_names)

        # Ensure avatar uniqueness
        p_avs = av_pools[gender] if av_pools[gender] else av_pools['any']
        available_avatars = [a for a in p_avs if a not in exclude_avatars]
        if not available_avatars: available_avatars = p_avs # Fallback
        avatar = random.choice(available_avatars) if available_avatars else None
        
        return name, avatar

    # Player / Avatar Setup
    profile_fonts = {'title': font_title, 'body': font_body, 'small': font_small, 'btn': font_btn}
    profile_modal = ProfileModal(WIDTH, HEIGHT, fonts=profile_fonts)
    profile_modal.selected_avatar_idx = p_av_idx
    current_avatar = profile_modal.avatars[p_av_idx] if p_av_idx < len(profile_modal.avatars) else None
    
    # Bots (NPCs with real human names)
    bot1_info = generate_npc(exclude_names=[player_name], exclude_avatars=[current_avatar])
    bot2_info = generate_npc(exclude_names=[player_name, bot1_info[0]], 
                             exclude_avatars=[current_avatar, bot1_info[1]])

    dealer_mgr.randomize()
    engine = TongItsEngine([player_name, bot1_info[0], bot2_info[0]], dealer_idx=dealer_mgr.get_idx())
    engine.initialize_game()
    assigned_avatars = [current_avatar, bot1_info[1], bot2_info[1]]

    anim_mgr = AnimationManager()
    particles = ParticleEmitter()
    lobby_particles = ParticleEmitter() # Dedicated for lobby
    ai_timer = None
    AI_THINK_DELAY = 0.7

    # ── State ─────────────────────────────────────────────────────
    game_state = 'lobby' # Start in Lobby
    lobby = Lobby(WIDTH, HEIGHT, font_title, font_body)
    shuffle_timer = 0.0
    SHUFFLE_DURATION = 2.2
    deal_order = []
    for r in range(12): deal_order.extend([1, 2, 0])
    deal_order.append(0)
    dealt_count = 0
    dealt_per_player = [0, 0, 0]
    deal_timer = 0.0
    DEAL_INTERVAL = 0.08
    DEAL_FLY_TIME = 0.22
    flying_cards = []

    # ── State ─────────────────────────────────────────────────────
    selected_cards = []
    hovered_card = None
    dragging_card = None
    drag_offset = (0,0)
    drag_pos = (0,0)
    card_visual_pos = {} 
    mouse_down_pos = None
    mouse_down_card = None
    is_dragging = False
    DRAG_THRESHOLD = 8
    # --- Unified Game Start/Restart Helper ---
    def start_new_game(target_state='shuffling', is_play_again=False):
        nonlocal engine, bot1_info, bot2_info, assigned_avatars, game_state, shuffle_timer, deal_order
        nonlocal dealt_count, dealt_per_player, deal_timer, flying_cards, ai_timer, selected_cards
        nonlocal game_over_overlay, fight_resolution_overlay, turn_timer, last_turn_state, meld_hit_zones
        
        # Dealer Logic via Manager
        # Only randomize when starting fresh from lobby, not on Play Again
        if not is_play_again and target_state == 'shuffling':
            dealer_mgr.randomize()
            
        cur_dealer_idx = dealer_mgr.get_idx()

        # Refresh Bots ONLY if starting fresh from lobby
        if not is_play_again:
            bot1_info = generate_npc(exclude_names=[player_name], exclude_avatars=[current_avatar])
            bot2_info = generate_npc(exclude_names=[player_name, bot1_info[0]], 
                                     exclude_avatars=[current_avatar, bot1_info[1]])
        
        # Initialize Engine with sync'd names and current dealer
        engine = TongItsEngine([player_name, bot1_info[0], bot2_info[0]], dealer_idx=cur_dealer_idx)
        engine.initialize_game()
        
        # Sync Avatars (Player may have changed)
        assigned_avatars[0] = current_avatar
        assigned_avatars[1] = bot1_info[1]
        assigned_avatars[2] = bot2_info[1]
        
        # Reset State Variables
        game_state = target_state
        shuffle_timer = 0.0
        
        # Calculate deal order using DealerManager
        deal_order = dealer_mgr.get_deal_sequence()
        
        dealt_count = 0
        dealt_per_player = [0, 0, 0]
        deal_timer = 0.0
        flying_cards.clear()
        ai_timer = None
        selected_cards.clear()
        game_over_overlay = None
        fight_resolution_overlay = None
        turn_timer = TURN_LIMIT
        last_turn_state = (engine.current_turn_index, engine.current_phase)
        meld_hit_zones = []
        refresh_background()

    # ── UI Components ─────────────────────────────────────────────
    phase_indicator = PhaseIndicator(WIDTH // 2, 8, font_phase)
    badge_comp = Badge(font_small)
    player_panel = PlayerPanel(font_body, font_small)
    btn_sort = Button(0, 0, 120, 35, "Auto Sort", font_btn, color=(60,60,90), hover_color=(80,80,120))
    btn_drop_meld = Button(0, 0, 140, 40, "Drop Meld", font_btn,
                           color=Colors.BTN_SUCCESS, hover_color=Colors.BTN_SUCCESS_HOVER)
    btn_call_fight = Button(0, 0, 140, 40, "Fight!", font_btn,
                            color=Colors.BTN_DANGER, hover_color=Colors.BTN_DANGER_HOVER)
    btn_group = Button(0, 0, 120, 35, "Group", font_btn,
                        color=(50, 80, 100), hover_color=(70, 110, 140))

    def calc_layout():
        return {
            'width': WIDTH, 'height': HEIGHT,
            'hand_y': HEIGHT - 170, 'hand_center_x': WIDTH // 2,
            'deck_x': WIDTH//2-140, 'deck_y': HEIGHT//2-145,
            'discard_x': WIDTH//2+60, 'discard_y': HEIGHT//2-145,
            'bot1_x': WIDTH-200, 'bot1_y': 90,
            'bot2_x': 200, 'bot2_y': 90,
            'player_meld_y': HEIGHT-315,
            'bot1_meld_x': WIDTH-300, 'bot1_meld_y': 190,
            'bot2_meld_x': 40, 'bot2_meld_y': 190,
            'btn_bar_y': HEIGHT-55, 'btn_bar_x': WIDTH//2,
            'dealer_anchors': [
                (100, HEIGHT - 100),              # Player (Bottom Left Bumper)
                (WIDTH - 100, 80),                # Bot 1 (Top Right Bumper)
                (100, 80)                         # Bot 2 (Top Left Bumper)
            ]
        }
    layout = calc_layout()

    def calc_meld_zones(player_melds, start_x, start_y, max_w=260):
        """Calculate bounding rects for each meld group for hit detection."""
        zones = []
        if not player_melds: return zones
        cs = 0.45  
        cw = int((BASE_CARD_W or 60)*cs)
        ch = int((BASE_CARD_H or 84)*cs)
        overlap_x = int(cw*0.35) 
        overlap_y = 6 
        mx, my = start_x, start_y
        for tm in player_melds:
            diag_h = (len(tm.cards)-1)*overlap_y
            meld_w = (len(tm.cards)-1)*overlap_x + cw
            # Wrapping logic with horizontal spread
            if mx+meld_w > start_x+max_w and mx > start_x:
                mx = start_x; my += ch + 25 # more vertical space
            zones.append((tm, pygame.Rect(mx, my, meld_w, ch + diag_h)))
            mx += meld_w + 14 
        return zones

    def draw_player_melds(surface, player_melds, start_x, start_y, max_w=260):
        zones = calc_meld_zones(player_melds, start_x, start_y, max_w)
        cs = 0.45
        cw = int((BASE_CARD_W or 60)*cs)
        ch = int((BASE_CARD_H or 84)*cs)
        overlap_x = int(cw*0.35)
        overlap_y = 6
        
        # Don't draw cards that are currently flying
        flying_card_objects = {fc['card'] for fc in flying_cards if fc.get('card')}
        
        for tm, rect in zones:
            for i, card in enumerate(tm.cards):
                if card in flying_card_objects:
                    continue
                img = get_card_image(card)
                if img:
                    scaled = pygame.transform.scale(img, (cw, ch))
                    surface.blit(scaled, (rect.x + i*overlap_x, rect.y + i*overlap_y))
        return zones

    clock = pygame.time.Clock()
    show_discard_modal = False
    
    running = True

    # ══════════════════════════════════════════════════════════════
    while running:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        # ── LOBBY ─────────────────────────────────────────────────
        if game_state == 'lobby':
            screen.fill((10, 15, 30))
            
            # Subtle background dust/stars (Now Golden/Celebratory)
            if random.random() < 0.08:
                p_colors = [(255, 215, 0), (255, 255, 180), (200, 160, 50)]
                lobby_particles.emit(random.randint(0, WIDTH), random.randint(0, HEIGHT), 
                                    count=1, colors=p_colors, speed=12, lifetime=2.5, gravity=False)
            
            lobby_particles.update(dt)
            lobby.update(dt, mouse_pos)
            lobby.draw(screen, player_name, current_avatar, player_stats, lobby_bkg)
            lobby_particles.draw(screen)
            
            # Update and Draw Profile Modal on top
            if profile_modal.active:
                profile_modal.update(dt, mouse_pos)
                profile_modal.draw(screen)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                
                # --- Profile Modal Interception ---
                if profile_modal.active:
                    resp = profile_modal.handle_event(event)
                    if resp and resp["type"] == "save":
                        player_name = resp["name"]
                        p_av_idx = resp["avatar_idx"]
                        current_avatar = profile_modal.avatars[p_av_idx]
                        
                        # Update and Save
                        profile_data["name"] = player_name
                        profile_data["avatar_idx"] = p_av_idx
                        save_user_profile(profile_data)
                    continue

                if event.type == pygame.VIDEORESIZE:
                    on_resize(event.w, event.h)
                
                # Trigger Profile on Avatar Click
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Avatar area: Bottom Left (25, H-68, 65, 65)
                    avatar_rect = pygame.Rect(25, HEIGHT - 68, 65, 65)
                    if avatar_rect.collidepoint(event.pos):
                        profile_modal.open(player_name)
                        continue

                sel_mode = lobby.handle_event(event)
                if sel_mode is not None:
                    # Sync Profile and Start Game
                    start_new_game(target_state='shuffling')
            
            pygame.display.flip()
            continue
        player = engine.players[0]
        current_player = engine.get_current_player()
        is_player_turn = (engine.current_turn_index == 0)
        is_blocking = anim_mgr.is_any_blocking() or bool(flying_cards)
        CW = BASE_CARD_W or 60
        CH = BASE_CARD_H or 84

        # --- Turn Timer Logic ---
        if not engine.is_game_over and game_state not in ('shuffling', 'dealing') and engine.game_phase != GamePhase.RESOLVING_FIGHT:
            # Only reset timer when the active player CHANGES, not on every phase move
            if engine.current_turn_index != last_turn_state[0]:
                turn_timer = TURN_LIMIT
                last_turn_state = (engine.current_turn_index, engine.current_phase)
            else:
                # Keep tracking phase for secondary logic, but don't reset timer
                last_turn_state = (engine.current_turn_index, engine.current_phase)
            
            turn_timer -= dt
            
            # Force action on timeout
            if turn_timer <= 0:
                # SMART TIMEOUT: Resolve all remaining turn steps immediately
                curr_p = engine.get_current_player()
                
                # 1. Force Draw if they haven't drawn yet
                if engine.current_phase == TurnPhase.DRAW:
                    engine.draw_from_deck(curr_p)
                
                # 2. Skip Melds/Actions if in those phases (including right after a forced draw)
                if engine.current_phase in (TurnPhase.MELD, TurnPhase.ACTION):
                    engine.skip_to_discard()
                
                # 3. Force Discard the highest card to end the turn
                if engine.current_phase == TurnPhase.DISCARD or is_dealer_phase:
                    if curr_p.hand:
                        highest_card = max(curr_p.hand, key=lambda c: RANK_ORDER.index(c.rank))
                        engine.discard_card(curr_p, highest_card)
                
                # Turn ends, next frame will reset timer for next player index

        # ── SHUFFLING ─────────────────────────────────────────────
        if game_state == 'shuffling':
            shuffle_timer += dt
            if shuffle_timer >= SHUFFLE_DURATION: game_state = 'dealing'
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: running = False
                elif ev.type == pygame.VIDEORESIZE:
                    on_resize(ev.w, ev.h)
            screen.fill((0, 0, 0))
            if background: screen.blit(background, (0,0))
            else: screen.fill(Colors.TABLE_GREEN)
            cb = get_card_back()
            if cb:
                cx, cy = WIDTH // 2 - cb.get_width() // 2, HEIGHT // 2 - cb.get_height() // 2
                p = min(shuffle_timer / SHUFFLE_DURATION, 1.0)
                
                # Draw a "shadow" for the deck with proper transparency for a 3D effect
                sh_w, sh_h = cb.get_size()
                shadow_surf = pygame.Surface((sh_w, sh_h), pygame.SRCALPHA)
                pygame.draw.rect(shadow_surf, (0, 0, 0, 70), (0, 0, sh_w, sh_h), border_radius=6)
                screen.blit(shadow_surf, (cx + 6, cy + 6))

                if p < 0.2:
                    # Phase 1: Split (Move apart)
                    sp = p / 0.2
                    offset = ease_out_cubic(sp) * 140
                    # Left segment
                    surf_l = pygame.transform.rotate(cb, -8 * sp)
                    screen.blit(surf_l, (cx - offset, cy - 10 * sp))
                    # Right segment
                    surf_r = pygame.transform.rotate(cb, 8 * sp)
                    screen.blit(surf_r, (cx + offset, cy - 10 * sp))
                
                elif p < 0.8:
                    # Phase 2: Riffle (Interleaving)
                    rp = (p - 0.2) / 0.6
                    max_offset = 140
                    
                    # Main stacks remain at sides
                    surf_l = pygame.transform.rotate(cb, -8)
                    surf_r = pygame.transform.rotate(cb, 8)
                    screen.blit(surf_l, (cx - max_offset, cy - 10))
                    screen.blit(surf_r, (cx + max_offset, cy - 10))
                    
                    # Animate individual cards "flicking" to center
                    num_riffle_cards = 16
                    for i in range(num_riffle_cards):
                        # Each card has its own start time within the riffle phase
                        card_start = (i / num_riffle_cards) * 0.7
                        card_p = max(0, min(1.0, (rp - card_start) / 0.3))
                        
                        if 0 < card_p < 1.0:
                            is_left = (i % 2 == 0)
                            side = -1 if is_left else 1
                            # Parabolic arc
                            arc_y = -60 * math.sin(card_p * math.pi)
                            tx = cx + (side * max_offset * (1.0 - card_p))
                            ty = cy - 10 + (10 * card_p) + arc_y
                            angle = side * 8 * (1.0 - card_p)
                            
                            flight_surf = pygame.transform.rotate(cb, angle)
                            screen.blit(flight_surf, (tx, ty))
                    
                    # Center stack building up
                    if rp > 0.1:
                        stack_h = int(rp * 8)
                        for s in range(stack_h):
                            screen.blit(cb, (cx, cy - s * 2))

                else:
                    # Phase 3: Square Up (Combine and bounce)
                    sqp = (p - 0.8) / 0.2
                    final_offset = 140 * (1.0 - ease_out_cubic(sqp))
                    
                    if final_offset > 5:
                        surf_l = pygame.transform.rotate(cb, -8 * (1.0 - sqp))
                        surf_r = pygame.transform.rotate(cb, 8 * (1.0 - sqp))
                        screen.blit(surf_l, (cx - final_offset, cy))
                        screen.blit(surf_r, (cx + final_offset, cy))
                    
                    # Main stack with a "squish" effect on landing
                    squish = 1.0 + 0.1 * math.sin(sqp * math.pi) if sqp < 1.0 else 1.0
                    if squish != 1.0:
                        w, h = cb.get_size()
                        sq_surf = pygame.transform.scale(cb, (int(w * (2 - squish)), int(h * squish)))
                        screen.blit(sq_surf, (cx - (sq_surf.get_width()-w)//2, cy + (h - sq_surf.get_height())))
                    else:
                        screen.blit(cb, (cx, cy))

            txt_str = "SHUFFLING..."
            txt = font_title.render(txt_str, True, Colors.TEXT_GOLD)
            
            # Premium animation: Vertical float + Alpha pulse
            float_y = 8 * math.sin(shuffle_timer * 4)
            alpha = int(180 + 75 * math.sin(shuffle_timer * 6))
            txt.set_alpha(alpha)
            
            txt_x = WIDTH // 2 - txt.get_width() // 2
            txt_y = HEIGHT // 2 + 100 + float_y
            
            # Draw shadow for "premium" depth
            shadow_surf = font_title.render(txt_str, True, (20, 10, 0))
            shadow_surf.set_alpha(alpha // 2)
            screen.blit(shadow_surf, (txt_x + 3, txt_y + 3))
            
            screen.blit(txt, (txt_x, txt_y))
            pygame.display.flip(); continue

        # ── DEALING ───────────────────────────────────────────────
        if game_state == 'dealing':
            deal_timer += dt
            while deal_timer >= DEAL_INTERVAL and dealt_count < len(deal_order):
                pi = deal_order[dealt_count]
                cn = dealt_per_player[pi]
                if pi == 0:
                    ov = min(35, (WIDTH-300)//max(cn+1,1))
                    tx = layout['hand_center_x']-(13*ov)//2+cn*ov; ty = layout['hand_y']; face = True
                elif pi == 1:
                    tx = layout['bot1_x']-100+cn*18; ty = layout['bot1_y']; face = False
                else:
                    tx = layout['bot2_x']-100+cn*18; ty = layout['bot2_y']; face = False
                co = engine.deal_sequence[dealt_count][1] if dealt_count < len(engine.deal_sequence) else None
                flying_cards.append({'start':(layout['deck_x'],layout['deck_y']),'end':(tx,ty),
                    'elapsed':0.0,'duration':DEAL_FLY_TIME,'player_idx':pi,'is_face_up':face,'card':co})
                dealt_per_player[pi] += 1; dealt_count += 1; deal_timer -= DEAL_INTERVAL
            for fc in flying_cards: fc['elapsed'] += dt
            if dealt_count >= len(deal_order) and all(fc['elapsed']>=fc['duration'] for fc in flying_cards):
                game_state = 'dealer_discard'; flying_cards.clear()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: running = False
                elif ev.type == pygame.VIDEORESIZE:
                    on_resize(ev.w, ev.h)
            screen.fill((0, 0, 0))
            if background: screen.blit(background,(0,0))
            else: screen.fill(Colors.TABLE_GREEN)
            cb = get_card_back()
            small_cb = get_card_back(0.75 * CARD_SCALE)
            cbs = get_card_back(0.6 * CARD_SCALE)
            if small_cb:
                sw, sh = small_cb.get_width(), small_cb.get_height()
                rv = 52-dealt_count
                for o in [4,2,0]:
                    if rv > 0: screen.blit(small_cb, (layout['deck_x']-o, layout['deck_y']-o))
            for pi2 in range(3):
                cnt = dealt_per_player[pi2]
                fc_cnt = sum(1 for f in flying_cards if f['player_idx']==pi2 and f['elapsed']<f['duration'])
                landed = cnt - fc_cnt
                if pi2 == 0:
                    ov = min(35,(WIDTH-300)//max(landed,1))
                    sx = layout['hand_center_x']-(landed*ov)//2
                    for i in range(landed):
                        c = engine.players[0].hand[i] if i < len(engine.players[0].hand) else None
                        if c:
                            im = get_card_image(c)
                            if im: screen.blit(im,(sx+i*ov,layout['hand_y']))
                elif cbs:
                    bx = layout['bot1_x'] if pi2==1 else layout['bot2_x']
                    by = layout['bot1_y'] if pi2==1 else layout['bot2_y']
                    # Use the common spacing logic for dealing
                    for i in range(landed): screen.blit(cbs,(bx-60+i*14,by))
            for fc in flying_cards:
                if fc['elapsed'] >= fc['duration']: continue
                t = min(fc['elapsed']/fc['duration'],1.0); e = ease_out_cubic(t)
                cx2 = fc['start'][0]+(fc['end'][0]-fc['start'][0])*e
                cy2 = fc['start'][1]+(fc['end'][1]-fc['start'][1])*e
                
                # Interpolate scale for cards (e.g. from pile size to target size)
                pile_scale = 0.75 * CARD_SCALE
                hand_scale = CARD_SCALE
                bot_target_scale = 0.6 * CARD_SCALE
                
                if fc['is_face_up']:
                    current_scale = pile_scale + (hand_scale - pile_scale) * e
                else:
                    current_scale = pile_scale + (bot_target_scale - pile_scale) * e
                
                if fc['is_face_up'] and fc['card']:
                    im = get_card_image(fc['card'], current_scale)
                    if im: screen.blit(im,(int(cx2),int(cy2)))
                else: 
                    fly_cb = get_card_back(current_scale)
                    if fly_cb: screen.blit(fly_cb,(int(cx2),int(cy2)))

            pygame.display.flip(); continue

        # ══════════════════════════════════════════════════════════
        # GAMEPLAY STATES
        # ══════════════════════════════════════════════════════════
        is_dealer_phase = (game_state == 'dealer_discard')
        hand = player.hand
        groups = player.hand_groups if player.hand_groups else [('all', len(hand))]
        GROUP_GAP = 18
        num_gaps = max(len(groups) - 1, 0)
        card_overlap = min(60, (WIDTH - 200 - GROUP_GAP * num_gaps) // max(len(hand), 1))
        hand_total_w = card_overlap * max(len(hand) - 1, 0) + CW + GROUP_GAP * num_gaps
        hand_start_x = layout['hand_center_x'] - hand_total_w // 2

        # Build group boundaries for gap insertion
        group_starts = []  # index in hand where each group starts
        idx = 0
        for gtype, count in groups:
            group_starts.append(idx)
            idx += count

        hand_rects = []
        accumulated_gap = 0
        g_idx = 0
        for i, card in enumerate(hand):
            # Insert gap when crossing into a new group
            if g_idx + 1 < len(group_starts) and i == group_starts[g_idx + 1]:
                accumulated_gap += GROUP_GAP
                g_idx += 1
            img = get_card_image(card)
            if img:
                w, h = img.get_size()
                rx = hand_start_x + i * card_overlap + accumulated_gap
                ry = layout['hand_y']
                if card in selected_cards: ry -= 20
                elif card == hovered_card and not dragging_card: ry -= 10
                hand_rects.append((card, pygame.Rect(rx, ry, w, h), img))

        # Pile rects for click detection
        small_cb2 = get_card_back(0.75 * CARD_SCALE)
        sw2, sh2 = small_cb2.get_width() if small_cb2 else CW, small_cb2.get_height() if small_cb2 else CH
        pile_closed_rect = pygame.Rect(layout['deck_x'], layout['deck_y'], sw2, sh2)
        sc = min(3, len(engine.discard_pile)) if engine.discard_pile else 0
        dx2_top = layout['discard_x'] + (sc - 1) * 2 if sc > 0 else layout['discard_x']
        dy2_top = layout['discard_y'] - (sc - 1) * 2 if sc > 0 else layout['discard_y']
        pile_discard_rect = pygame.Rect(dx2_top, dy2_top, sw2, sh2)

        # Pre-compute meld hit zones for sapaw
        meld_hit_zones = []
        if player.melds:
            meld_hit_zones += calc_meld_zones(player.melds, max(100, layout['hand_center_x'] - 400), layout['player_meld_y'], 800)
        meld_hit_zones += calc_meld_zones(engine.players[1].melds, layout['bot1_meld_x'], layout['bot1_meld_y'], 280)
        meld_hit_zones += calc_meld_zones(engine.players[2].melds, layout['bot2_meld_x'], layout['bot2_meld_y'], 280)

        # Pile hover detection
        in_playable_phase = (engine.game_phase == GamePhase.PLAYING or engine.game_phase == GamePhase.DEALER_DISCARD)
        hover_closed_pile = pile_closed_rect.collidepoint(mouse_pos) and is_player_turn and engine.current_phase == TurnPhase.DRAW and in_playable_phase
        can_draw_discard = engine.discard_pile and engine.current_phase == TurnPhase.DRAW and is_player_turn and in_playable_phase and engine._can_meld_with_discard(player, engine.discard_pile[-1]) if engine.discard_pile else False
        hover_discard_pile = pile_discard_rect.collidepoint(mouse_pos) and can_draw_discard

        eatable_hand_cards = set()
        if can_draw_discard and engine.discard_pile:
            import itertools
            target_card = engine.discard_pile[-1]
            # Fast check combinations up to 4 cards that can meld with the discarded card
            for i in range(2, min(5, len(player.hand) + 1)):
                for combo in itertools.combinations(player.hand, i):
                    if MC.is_valid_meld(list(combo) + [target_card]):
                        eatable_hand_cards.update(combo)

        # Phase indicator
        if is_dealer_phase: 
            if engine.current_phase == TurnPhase.MELD: phase_indicator.set_phase('BANKER MELD')
            else: phase_indicator.set_phase('BANKER DISCARD')
        elif is_player_turn and not engine.is_game_over: phase_indicator.set_phase(engine.current_phase.name)
        else: phase_indicator.set_phase('WAITING')

        # Button updates
        btn_sort.rect.topleft = (WIDTH-140, layout['hand_y']-45)
        btn_sort.update(mouse_pos, dt)

        # Only consider selected cards that are still in the player's hand
        # (Fixing bug where dropped/discarded cards could stay in the selected list)
        selected_in_hand = [c for c in selected_cards if c in player.hand]

        btn_group.rect.topleft = (WIDTH-270, layout['hand_y']-45)
        
        # Check if selection matches an existing manual group EXACTLY
        is_ungroup_candidate = False
        if selected_in_hand:
            for mg in player.manual_groups:
                if len(mg) == len(selected_in_hand) and all(c in mg for c in selected_in_hand):
                    is_ungroup_candidate = True
                    break
        
        if is_ungroup_candidate:
            btn_group.text = "Ungroup"
            btn_group.color = (130, 80, 50) # Brownish/orange for ungrouping
            btn_group.hover_color = (160, 110, 70)
            btn_group.enabled = True
        else:
            btn_group.text = "Group"
            btn_group.color = (50, 80, 100)
            btn_group.hover_color = (70, 110, 140)
            btn_group.enabled = len(selected_in_hand) >= 3
            
        btn_group.update(mouse_pos, dt)
        can_meld = len(selected_in_hand) >= 3 and MC.is_valid_meld(selected_in_hand)

        # Check if forced meld card is missing
        if player.forced_meld_card and player.forced_meld_card not in selected_cards:
             # Check if they have ANY other meld they are dropping,
             # in which case they still need to meld the forced one!
             pass

        show_drop = is_player_turn and engine.current_phase == TurnPhase.MELD and not engine.is_game_over
        btn_drop_meld.rect.topleft = (WIDTH-150, layout['hand_y'])
        btn_drop_meld.enabled = can_meld

        # Add a subtle pulse to Drop Meld button when ready
        if can_meld:
            p = int(15 * math.sin(pygame.time.get_ticks() * 0.01))
            btn_drop_meld.color = (Colors.BTN_SUCCESS[0]+p, Colors.BTN_SUCCESS[1]+p, Colors.BTN_SUCCESS[2]+p)
        else:
            btn_drop_meld.color = Colors.BTN_SUCCESS

        if show_drop: btn_drop_meld.update(mouse_pos, dt)

        show_fight = is_player_turn and engine.can_player_fight(player) and not engine.is_game_over
        btn_call_fight.rect.topleft = (WIDTH-150, layout['hand_y']+45)
        if show_fight: btn_call_fight.update(mouse_pos, dt)

        if engine.is_game_over and game_state != 'game_over':
            game_state = 'game_over'
            game_over_overlay = GameOverOverlay(WIDTH, HEIGHT, font_title, font_body, font_btn)
            
            # --- Record Stats ---
            is_win = (engine.winner and engine.winner.name == player_name)
            if is_win:
                player_stats["wins"] += 1
                player_stats["coins"] += 1000 # Win bonus
            else:
                player_stats["losses"] += 1
                player_stats["coins"] = max(0, player_stats["coins"] - 500) # Loss penalty

            # Sync to persistent data and save
            profile_data.update(player_stats)
            save_user_profile(profile_data)

        if game_state == 'game_over' and game_over_overlay:
            game_over_overlay.update(dt, mouse_pos)
            
        if engine.game_phase == GamePhase.RESOLVING_FIGHT:
            if not fight_resolution_overlay:
                fight_resolution_overlay = FightResolutionOverlay(WIDTH, HEIGHT, font_title, font_body, font_btn)
            fight_resolution_overlay.update(dt, mouse_pos)

        # ── Events ────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.VIDEORESIZE:
                on_resize(event.w, event.h)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_state == 'game_over' and game_over_overlay:
                    if game_over_overlay.play_again_btn.is_clicked(event):
                        start_new_game(target_state='shuffling', is_play_again=True)
                        continue
                    elif game_over_overlay.lobby_btn.is_clicked(event):
                        start_new_game(target_state='lobby')
                        continue

                if engine.game_phase == GamePhase.RESOLVING_FIGHT and fight_resolution_overlay:
                    if player not in engine.active_fight['responses']:
                        # The user needs to respond
                        if fight_resolution_overlay.btn_fight.is_clicked(event):
                            engine.respond_to_fight(player, 'fight')
                        elif fight_resolution_overlay.btn_fold.is_clicked(event):
                            engine.respond_to_fight(player, 'fold')
                    continue

                if engine.is_game_over:
                    continue

                if btn_sort.is_clicked(event): player.group_hand(); selected_cards.clear(); continue
                if btn_group.is_clicked(event):
                    if btn_group.text == "Ungroup":
                        player.remove_manual_group(selected_in_hand)
                    else:
                        player.add_manual_group(selected_in_hand)
                    selected_cards.clear()
                    continue
                
                # Check discard pile modal override
                if show_discard_modal:
                    modal_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 125, 400, 250)
                    if not modal_rect.collidepoint(event.pos):
                        show_discard_modal = False
                    continue

                # Check normal gameplay interactions (only during regular play)
                if is_player_turn and not is_blocking and in_playable_phase:
                    if show_drop and btn_drop_meld.is_clicked(event):
                        # Recalculate filtered selection for safety
                        sel_in_hand = [c for c in selected_cards if c in player.hand]
                        if len(sel_in_hand) >= 3 and MC.is_valid_meld(sel_in_hand):
                            for i, mc in enumerate(sel_in_hand):
                                flying_cards.append({
                                    'start': (layout['hand_center_x'], layout['hand_y']),
                                    'end': (layout['hand_center_x']-100+i*22, layout['player_meld_y']),
                                    'elapsed': -i * 0.08, 'duration': 0.45, 'player_idx': 0, 'is_face_up': True, 'card': mc
                                })
                            if engine.drop_meld(player, list(sel_in_hand)):      
                                particles.emit(layout['hand_center_x'],layout['player_meld_y'],count=25,speed=200)
                                selected_cards.clear()
                        continue
                    if show_fight and btn_call_fight.is_clicked(event): engine.call_fight(player); continue

                    # Click on closed pile → draw
                    if engine.current_phase == TurnPhase.DRAW and not is_dealer_phase:
                        if pile_closed_rect.collidepoint(event.pos):
                            # Pre-draw state to detect auto-tongit win
                            prev_card_count = len(player.hand)
                            if engine.draw_from_deck(player):
                                if not player.hand: # Auto-tongit triggered
                                    # Play some particles and don't try to access hand[-1]
                                    particles.emit(layout['hand_center_x'], layout['hand_y'], count=40)
                                else:
                                    drawn_card = player.hand[-1]
                                    flying_cards.append({
                                        'start': (layout['deck_x'], layout['deck_y']),  
                                        'end': (layout['hand_center_x'], layout['hand_y']),
                                        'elapsed': 0, 'duration': 0.4, 'player_idx': 0, 'is_face_up': False, 'card': drawn_card
                                    })
                                continue
                        if can_draw_discard and pile_discard_rect.collidepoint(event.pos):
                            target_card = engine.discard_pile[-1]
                            if engine.draw_from_discard(player):
                                if not player.hand: # Auto-tongit triggered
                                    particles.emit(layout['hand_center_x'], layout['hand_y'], count=40)
                                else:
                                    drawn_card = player.hand[-1]
                                    possible_melds = engine.get_possible_melds(player)      
                                    meld_to_drop = None
                                    for meld, mtype in possible_melds:
                                        if drawn_card in meld:
                                            meld_to_drop = meld
                                            break

                                    target_x = max(100, layout['hand_center_x'] - 400)      
                                    target_y = layout['player_meld_y']

                                    if meld_to_drop:
                                        for i, c in enumerate(meld_to_drop):
                                            flying_cards.append({
                                                'start': (layout['discard_x'], layout['discard_y']) if c == drawn_card else (layout['hand_center_x'], layout['hand_y']),    
                                                'end': (target_x + i * 20, target_y),       
                                                'elapsed': 0, 'duration': 0.45, 'player_idx': 0,
                                                'is_face_up': True, 'card': c
                                            })
                                        engine.drop_meld(player, list(meld_to_drop))
                                        particles.emit(target_x, target_y, count=15)
                                    else:
                                        flying_cards.append({
                                            'start': (layout['discard_x'], layout['discard_y']),
                                            'end': (layout['hand_center_x'], layout['hand_y']),
                                            'elapsed': 0, 'duration': 0.4, 'player_idx': 0, 'is_face_up': True, 'card': drawn_card
                                        })
                                continue

                # Click discard pile to show modal (only if not drawing/eating)
                if pile_discard_rect.collidepoint(event.pos) and not can_draw_discard and engine.discard_pile:
                    # Check if we clicked a card in hand first (they shouldn't overlap, but to be safe)
                    if not any(rect.collidepoint(event.pos) for c, rect, img in hand_rects):
                        show_discard_modal = True
                        continue

                # Start potential drag on card
                mx,my = event.pos
                mouse_down_pos = (mx,my); is_dragging = False; mouse_down_card = None
                
                # Check for cards in hand even if it's not our turn (for arrangement)
                for card,rect,img in reversed(hand_rects):
                    if rect.collidepoint(mx,my):
                        mouse_down_card = card
                        drag_offset = (rect.x-mx, rect.y-my)
                        drag_pos = (rect.x, rect.y)
                        break

            elif event.type == pygame.MOUSEMOTION:
                mx,my = event.pos
                if mouse_down_card and not is_dragging:
                    if mouse_down_pos:
                        dx = mx-mouse_down_pos[0]; dy = my-mouse_down_pos[1]    
                        if (dx*dx+dy*dy) > DRAG_THRESHOLD*DRAG_THRESHOLD:       
                            is_dragging = True; dragging_card = mouse_down_card 
                if is_dragging and dragging_card:
                    drag_pos = (mx+drag_offset[0], my+drag_offset[1])
                else:
                    hovered_card = None
                    
                    for card,rect,img in reversed(hand_rects):
                        if rect.collidepoint(mx,my): hovered_card = card; break

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:      
                if is_dragging and dragging_card:
                    mx,my = event.pos
                    dropped = False

                    if is_player_turn and not is_blocking:
                        
                        if engine.current_phase in (TurnPhase.DRAW, TurnPhase.MELD):
                            for tm, mrect in meld_hit_zones:
                                expanded_rect = pygame.Rect(mrect.x - 20, mrect.y - 20, mrect.w + 40, mrect.h + 40)
                                if expanded_rect.collidepoint(mx,my) and tm.can_sapaw(dragging_card):
                                    if engine.sapaw(player, dragging_card, tm):     
                                        dropped = True
                                    break

                        discard_rect = pygame.Rect(layout['discard_x'] - 40, layout['discard_y'] - 40, CW + 80, CH + 80)
                        if not dropped and discard_rect.collidepoint(mx, my):       
                            if is_dealer_phase:
                                if engine.dealer_initial_discard(dragging_card):    
                                    flying_cards.append({
                                        'start': (mx, my), 'end': (layout['discard_x'], layout['discard_y']),
                                        'elapsed': 0, 'duration': 0.35, 'player_idx': 0, 'is_face_up': True, 'card': dragging_card
                                    })
                                    game_state = 'playing'
                                    dropped = True
                            else:
                                if engine.discard_card(player, dragging_card):      
                                    flying_cards.append({
                                        'start': (mx, my), 'end': (layout['discard_x'], layout['discard_y']),
                                        'elapsed': 0, 'duration': 0.35, 'player_idx': 0, 'is_face_up': True, 'card': dragging_card
                                    })
                                    dropped = True

                    # 3. Arrange hand via drag and drop
                    if not dropped:
                        fc = len(player.hand)
                        if fc > 0:
                            hand_spacing = min(40, (WIDTH - 200) // fc)     
                            start_x = layout['hand_center_x'] - (fc * hand_spacing) // 2
                            drop_idx = (mx - start_x + (hand_spacing // 2)) // hand_spacing
                            drop_idx = max(0, min(fc - 1, drop_idx))
                            
                            if dragging_card in player.hand:
                                player.hand.remove(dragging_card)
                                player.hand.insert(drop_idx, dragging_card)     
                                player.group_hand()

                    dragging_card = None
                elif mouse_down_card and not is_dragging:
                    # Click (not drag) → select/deselect for meld
                    # banker can select melds immediately, others must draw first
                    can_select = (engine.current_phase in (TurnPhase.MELD, TurnPhase.DISCARD) or is_dealer_phase)
                    if can_select:
                        card = mouse_down_card
                        # ... (existing selection logic)
                        group_subset = None
                        idx = player.hand.index(card)
                        curr_cnt = 0
                        for gtype, gcount in player.hand_groups:
                            if curr_cnt <= idx < curr_cnt + gcount:
                                if gtype == 'meld' or gtype == 'manual':
                                    group_subset = player.hand[curr_cnt : curr_cnt + gcount]
                                break
                            curr_cnt += gcount

                        if group_subset and card not in selected_cards:
                            for c in group_subset:
                                if c not in selected_cards: selected_cards.append(c)
                        elif group_subset and card in selected_cards:
                            for c in group_subset:
                                if c in selected_cards: selected_cards.remove(c)
                        else:
                            if card in selected_cards: selected_cards.remove(card)
                            else: selected_cards.append(card)
                mouse_down_pos = None; mouse_down_card = None; is_dragging = False

# ── AI Fight Responses ──────────────────────────────────────────────      
        if engine.game_phase == GamePhase.RESOLVING_FIGHT and not engine.is_game_over:
            # Let bots respond
            for bot_idx in [1, 2]:
                bot_player = engine.players[bot_idx]
                if bot_player not in engine.active_fight['responses'] and bot_player != engine.active_fight['caller']:
                    if ai_timer is None: ai_timer = Timer(1.5 + bot_idx * 0.5)
                    if ai_timer.update(dt):
                        response = RuleBasedAI._should_respond_fight(engine, bot_player, engine.active_fight)
                        engine.respond_to_fight(bot_player, response)
                        ai_timer = None
                        break # One bot at a time

        # ── AI TURNS ──────────────────────────────────────────────────
        if (game_state in ('playing', 'dealer_discard')) and not is_player_turn and not is_blocking:
            if not ai_timer: ai_timer = Timer(1.0)
            if ai_timer.update(dt):
                bot = engine.get_current_player()
                pi = engine.current_turn_index

                # Step 0: Check for Fight (Pre-draw)
                if engine.current_phase == TurnPhase.DRAW:
                    if RuleBasedAI._should_call_fight(engine, bot):
                        engine.call_fight(bot)
                        ai_timer = None # Reset for next phase
                        continue

                # Step 1: Draw
                if engine.current_phase == TurnPhase.DRAW:
                    bot_x = layout[f'bot{pi}_x']
                    bot_y = layout[f'bot{pi}_y']
                    if engine.discard_pile and engine._can_meld_with_discard(bot, engine.discard_pile[-1]):
                        # Bot draws from discard pile
                        drawn_card = engine.discard_pile[-1]
                        if engine.draw_from_discard(bot):
                            if not bot.hand:
                                particles.emit(layout[f'bot{pi}_meld_x'], layout[f'bot{pi}_meld_y'], count=30)
                            else:
                                possible_melds = engine.get_possible_melds(bot)
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
                                    particles.emit(target_x, target_y, count=15)        
                                else:
                                    flying_cards.append({
                                        'start': (layout['discard_x'], layout['discard_y']),
                                        'end': (bot_x, bot_y), 'elapsed': 0, 'duration': 0.4,
                                        'player_idx': pi, 'is_face_up': True, 'card': drawn_card
                                    })
                    else:
                        # Visual: Fly from deck to bot
                        if engine.draw_from_deck(bot):
                            if not bot.hand:
                                particles.emit(layout[f'bot{pi}_meld_x'], layout[f'bot{pi}_meld_y'], count=30)
                            else:
                                drawn_card = bot.hand[-1]
                                flying_cards.append({
                                    'start': (layout['deck_x'], layout['deck_y']),  
                                    'end': (bot_x, bot_y), 'elapsed': 0, 'duration': 0.4,
                                    'player_idx': pi, 'is_face_up': False, 'card': drawn_card
                                })
                    ai_timer = Timer(2.0) # Wait for draw anim

                # Step 2: Meld/Action
                elif engine.current_phase == TurnPhase.MELD:
                    better_ai = RuleBasedAI()
                    dropped_any = False

                    # Try melds
                    melds_to_drop = better_ai._find_best_melds(bot)
                    if melds_to_drop:
                        cards, mtype = melds_to_drop[0]
                        source_x = layout[f'bot{pi}_x']
                        source_y = layout[f'bot{pi}_y']
                        target_x = layout[f'bot{pi}_meld_x']
                        target_y = layout[f'bot{pi}_meld_y']
                        for i, c in enumerate(cards):
                            flying_cards.append({
                                'start': (source_x, source_y), 'end': (target_x+i*20, target_y),
                                'elapsed': -i * 0.08, 'duration': 0.45, 'player_idx': pi,
                                'is_face_up': True, 'card': c
                            })
                        engine.drop_meld(bot, cards)
                        particles.emit(target_x, target_y, count=15)
                        dropped_any = True

                    # Try sapaw
                    sapaw_options = engine.get_sapaw_options(bot)
                    if not dropped_any and sapaw_options:
                        card, meld = sapaw_options[0]
                        source_x = layout[f'bot{pi}_x']
                        source_y = layout[f'bot{pi}_y']

                        target_x, target_y = layout['discard_x'], layout['discard_y'] - 100
                        for p_idx, p in enumerate(engine.players):
                            bx = max(100, layout['hand_center_x'] - 400) if p_idx == 0 else layout[f'bot{p_idx}_meld_x']
                            by = layout['player_meld_y'] if p_idx == 0 else layout[f'bot{p_idx}_meld_y']
                            bw = 800 if p_idx == 0 else 280
                            hz = calc_meld_zones(p.melds, bx, by, bw)
                            for zm, zrect in hz:
                                if zm == meld:
                                    target_x, target_y = zrect.x, zrect.y       
                                    break

                        engine.sapaw(bot, card, meld)
                        flying_cards.append({
                           'start': (source_x, source_y), 'end': (target_x, target_y),
                           'elapsed': 0, 'duration': 0.4, 'player_idx': pi,     
                           'is_face_up': True, 'card': card
                        })
                        dropped_any = True

                    if not dropped_any:
                        # Try to call a fight if AI thinks it's a good idea and can
                        if RuleBasedAI._should_call_fight(engine, bot):     
                            engine.call_fight(bot)

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
                            # If bot was banker, move game state to playing
                            if game_state == 'dealer_discard':
                                game_state = 'playing'
                    ai_timer = None

        # ══════════════════════════════════════════════════════════
        # RENDERING
        # ══════════════════════════════════════════════════════════
        if background: screen.blit(background,(0,0))
        else: screen.fill(Colors.TABLE_GREEN)

        cb = get_card_back()
        small_cb = get_card_back(0.75 * CARD_SCALE)
        sw, sh = small_cb.get_width(), small_cb.get_height() if small_cb else (CW, CH)

        # ── Closed Pile ───────────────────────────────────────────
        if small_cb and engine.deck.remaining() > 0:
            base_pile_scale = 0.75 * CARD_SCALE
            scale_factor = base_pile_scale
            if is_player_turn and engine.current_phase == TurnPhase.DRAW and not is_dealer_phase:
                # Pulsing growing animation for the deck
                scale_factor = base_pile_scale + 0.05 * math.sin(pygame.time.get_ticks() * 0.008)
            
            anim_cb = get_card_back(scale_factor) if scale_factor != base_pile_scale else small_cb
            anim_w, anim_h = anim_cb.get_width() if anim_cb else sw, anim_cb.get_height() if anim_cb else sh
            
            ctx = layout['deck_x'] - int((anim_w - sw) / 2)
            cty = layout['deck_y'] - int((anim_h - sh) / 2)

            for o in [4,2,0]: screen.blit(anim_cb, (ctx-o, cty-o))
            badge_comp.draw(screen, ctx+anim_w//2, cty-12,
                           str(engine.deck.remaining()), bg_color=(30,30,50,230), text_color=Colors.TEXT_GOLD)
            if hover_closed_pile:
                gl = pygame.Surface((anim_w+16,anim_h+16),pygame.SRCALPHA)
                p2 = int(40 + 40 * math.sin(pygame.time.get_ticks() * 0.008))
                pygame.draw.rect(gl,(255,215,0,p2+40),(0,0,anim_w+16,anim_h+16),width=4,border_radius=10)
                screen.blit(gl,(ctx-8,cty-8))
            elif is_player_turn and engine.current_phase == TurnPhase.DRAW and not is_dealer_phase:
                # Outline pulsing hint
                gl = pygame.Surface((anim_w+12,anim_h+12),pygame.SRCALPHA)
                p2 = int(20 + 20 * math.sin(pygame.time.get_ticks() * 0.008))
                pygame.draw.rect(gl,(255,215,0,p2),(0,0,anim_w+12,anim_h+12),width=2,border_radius=8)
                screen.blit(gl,(ctx-6,cty-6))
        lbl = font_small.render("Closed",True,Colors.TEXT_MUTED)
        screen.blit(lbl,(layout['deck_x']+(sw-lbl.get_width())//2, layout['deck_y']+sh+4))

        # ── Discard Pile ──────────────────────────────────────────
        dx2,dy2 = layout['discard_x'], layout['discard_y']
        if engine.discard_pile:
            for i in range(sc):
                idx = len(engine.discard_pile)-sc+i
                im = get_card_image(engine.discard_pile[idx], 0.75 * CARD_SCALE)
                if im:
                    o = i * 2  # Bottom cards are drawn first, at 0, 0, then layered up and right
                    screen.blit(im,(dx2+o,dy2-o))
            if hover_discard_pile:
                gl = pygame.Surface((sw+12,sh+12),pygame.SRCALPHA)
                p2 = int(40 + 40 * math.sin(pygame.time.get_ticks() * 0.01))
                pygame.draw.rect(gl,(100,255,100,p2+40),(0,0,sw+12,sh+12),width=4,border_radius=8)
                screen.blit(gl,(dx2_top-6,dy2_top-6))
            elif can_draw_discard:
                # Glowing animation to indicate eatable
                gl = pygame.Surface((sw+12,sh+12),pygame.SRCALPHA)
                p2 = int(40 + 30 * math.sin(pygame.time.get_ticks() * 0.008))  
                pygame.draw.rect(gl,(100,255,100,p2),(0,0,sw+12,sh+12),width=3,border_radius=8)
                screen.blit(gl,(dx2_top-6,dy2_top-6))
        else:
            if small_cb:
                em = pygame.Surface((sw, sh),pygame.SRCALPHA)
                pygame.draw.rect(em,(255,255,255,30),(0,0,sw,sh),width=2,border_radius=4)
                screen.blit(em,(dx2,dy2))
        lbl2 = font_small.render("Discard",True,Colors.TEXT_MUTED)
        screen.blit(lbl2,(dx2+(sw-lbl2.get_width())//2,dy2+sh+4))

        # ── Bots ──────────────────────────────────────────────────
        for bi in [1,2]:
            bot = engine.players[bi]
            bx = layout['bot1_x'] if bi==1 else layout['bot2_x']
            by = layout['bot1_y'] if bi==1 else layout['bot2_y']
            # Draw bot cards - back during play, face-up at game over
            flying_toward_bot = sum(1 for fc in flying_cards if fc.get('card') in bot.hand)
            bot_hand_to_show = [c for c in bot.hand if not any(fc.get('card') == c for fc in flying_cards)]
            fc2 = len(bot_hand_to_show)
            bsc = 0.6 * CARD_SCALE 
            
            if engine.is_game_over:
                # Show cards for transparency
                fs = min(25, 200//max(fc2,1)) # Wider spacing for face-up
                fsx = bx - (fc2*fs)//2
                for i, card in enumerate(bot_hand_to_show):
                    im = get_card_image(card, bsc)
                    if im:
                        a = (i-fc2//2)*(3 if bi==1 else -3)
                        r = pygame.transform.rotate(im, a)
                        screen.blit(r, (fsx+i*fs, by+abs(i-fc2//2)*5))
            elif cb:
                # Show card backs
                cbs_bot = pygame.transform.scale(cb, (int(CW*bsc/CARD_SCALE), int(CH*bsc/CARD_SCALE)))
                fs = min(12, 140//max(fc2,1))
                fsx = bx - (fc2*fs)//2
                for i in range(fc2):
                    a = (i-fc2//2)*(3 if bi==1 else -3)
                    r = pygame.transform.rotate(cbs_bot, a)
                    screen.blit(r, (fsx+i*fs, by+abs(i-fc2//2)*2))
            player_panel.draw(screen, bx, by-45, bot, is_active=(engine.current_turn_index==bi),
                              show_points=engine.is_game_over, 
                              avatar_surf=assigned_avatars[bi],
                              show_burned=(engine.is_game_over or (engine.last_event and engine.last_event['type'] == 'fight')),
                              timer_progress=max(0, turn_timer / TURN_LIMIT) if engine.current_turn_index == bi else 0)
      
            bmx = layout['bot1_meld_x'] if bi==1 else layout['bot2_meld_x']
            bmy = layout['bot1_meld_y'] if bi==1 else layout['bot2_meld_y']
            if bot.melds: draw_player_melds(screen, bot.melds, bmx, bmy, 280)

        # ── Player's Melds (above hand - spread wider) ────────────
        if player.melds:
            meld_start_x = max(100, layout['hand_center_x'] - 400)
            draw_player_melds(screen, player.melds, meld_start_x, layout['player_meld_y'], max_w=800)

        # ── Sapaw drop target highlight during drag ──────────────
        if dragging_card and engine.current_phase in (TurnPhase.DRAW, TurnPhase.MELD):
            for tm, mrect in meld_hit_zones:
                if mrect.collidepoint(mouse_pos) and tm.can_sapaw(dragging_card):
                    gl = pygame.Surface((mrect.w+6,mrect.h+6),pygame.SRCALPHA)
                    pygame.draw.rect(gl,(80,255,120,100),(0,0,mrect.w+6,mrect.h+6),width=3,border_radius=4)
                    screen.blit(gl,(mrect.x-3,mrect.y-3))

        # ── Player Hand ──────────────────────────────────────────
        LERP_SPEED = 12.0
        flying_card_objects_hand = {fc['card'] for fc in flying_cards if fc.get('card')}
        
       
        ribbon_groups = []
        
        if len(selected_in_hand) >= 3 and MC.is_valid_meld(selected_in_hand):
             current_subgroup = []
             for card, rect, img in hand_rects:
                 if card in selected_in_hand:
                     current_subgroup.append(rect)
                 else:
                     if len(current_subgroup) >= 1:
                         ribbon_groups.append({'rects': current_subgroup, 'label': 'Meld Ready', 'front_only': False})
                         current_subgroup = []
             if len(current_subgroup) >= 1:
                 ribbon_groups.append({'rects': current_subgroup, 'label': 'Meld Ready', 'front_only': False})
        
        
        h_idx = 0
        for gtype, count in groups:
            if (gtype == 'meld' or gtype == 'manual') and count >= 3:
                group_cards = hand[h_idx : h_idx + count]
                group_rects_all = [r for c,r,i in hand_rects[h_idx : h_idx + count]]
                
                label = 'Meld Group' if gtype == 'meld' else 'Saved Group'
                
                
                temp_idx = 0
                while temp_idx <= count - 3:
                    found_meld = False
                  
                    if gtype == 'manual':
                        actual_rects = group_rects_all
                        is_sub = any(all(gr in rg['rects'] for gr in actual_rects) for rg in ribbon_groups)
                        if not is_sub:
                            ribbon_groups.append({'rects': actual_rects, 'label': label, 'front_only': False})
                        h_idx += count
                        found_meld = True
                        break

                    for length in range(count - temp_idx, 2, -1):
                        sub_cards = group_cards[temp_idx : temp_idx + length]
                        if MC.is_valid_meld(sub_cards):
                            actual_rects = group_rects_all[temp_idx : temp_idx + length]
                            
                            is_sub = any(all(gr in rg['rects'] for gr in actual_rects) for rg in ribbon_groups)
                            if not is_sub:
                                ribbon_groups.append({'rects': actual_rects, 'label': label, 'front_only': False})
                            temp_idx += length
                            found_meld = True
                            break
                    if not found_meld:
                        temp_idx += 1
            if gtype != 'manual': h_idx += count

      
        for rg in ribbon_groups:
            if not rg.get('front_only'):
                draw_hand_ribbon(screen, rg['rects'], is_front=False)

       
        for i, (card, rect, img) in enumerate(hand_rects):
            
            c_id = id(card)
            if c_id not in card_visual_pos:
                start_x = layout['deck_x'] if engine.current_phase == TurnPhase.DRAW else rect.x
                start_y = layout['deck_y'] if engine.current_phase == TurnPhase.DRAW else rect.y
                card_visual_pos[c_id] = [start_x, start_y]

            curr = card_visual_pos[c_id]
            curr[0] += (rect.x - curr[0]) * LERP_SPEED * dt
            curr[1] += (rect.y - curr[1]) * LERP_SPEED * dt

            if card == dragging_card or (card in flying_card_objects_hand): 
              
                pass
            else:
                draw_x, draw_y = curr

              
                if card in selected_cards:
                    gl = pygame.Surface((rect.w+8,rect.h+8),pygame.SRCALPHA)
                    is_ribboned = any(rect in rg['rects'] for rg in ribbon_groups)
                    if not is_ribboned:
                        pygame.draw.rect(gl,Colors.CARD_SELECTED,(0,0,rect.w+8,rect.h+8),border_radius=8)
                        screen.blit(gl,(draw_x-4,draw_y-4))
                    else:
                        pygame.draw.rect(gl,(255,215,0,120),(0,0,rect.w+8,rect.h+8),width=3,border_radius=8)
                        screen.blit(gl,(draw_x-4,draw_y-4))
                elif card == hovered_card:
                    gl = pygame.Surface((rect.w+4,rect.h+4),pygame.SRCALPHA)
                    pygame.draw.rect(gl,Colors.CARD_HOVER,(0,0,rect.w+4,rect.h+4),border_radius=4)
                    screen.blit(gl,(draw_x-2,draw_y-2))
                
                if card in eatable_hand_cards:
                    gl = pygame.Surface((rect.w+8,rect.h+8),pygame.SRCALPHA)       
                    p2 = int(50+40*math.sin(pygame.time.get_ticks()*0.008))
                    pygame.draw.rect(gl,(100,255,100,p2),(0,0,rect.w+8,rect.h+8),border_radius=6,width=3)
                    screen.blit(gl,(draw_x-4,draw_y-4))

                if card == player.forced_meld_card:
                    gl = pygame.Surface((rect.w+10,rect.h+10),pygame.SRCALPHA)
                    p2 = int(60+40*math.sin(pygame.time.get_ticks()*0.005))
                    pygame.draw.rect(gl,(255,100,50,p2),(0,0,rect.w+10,rect.h+10),border_radius=6)
                    screen.blit(gl,(draw_x-5,draw_y-5))
                
                screen.blit(img, (draw_x, draw_y))

           
            for ribbon_g in ribbon_groups:
                if rect == ribbon_g['rects'][-1]:
                    draw_hand_ribbon(screen, ribbon_g['rects'], text=ribbon_g['label'], is_front=True)

        # ── Dragged Card ─────────────────────────────────────────
        if dragging_card:
            im = get_card_image(dragging_card)
            if im:
                a = max(-12,min(12,(drag_pos[0]-layout['hand_center_x'])*0.04))
                screen.blit(pygame.transform.rotate(im,a),drag_pos)
                if drag_pos[1] < layout['hand_y']-50:
                    ht = font_small.render("Release to Discard",True,Colors.TEXT_GOLD)
                    screen.blit(ht,(drag_pos[0],drag_pos[1]-25))

        # ── Player Panel ─────────────────────────────────────────
        player_panel.draw(screen, WIDTH//2, HEIGHT-68, player, is_active=is_player_turn, show_points=True,
                          avatar_surf=assigned_avatars[0],
                          show_burned=(engine.is_game_over or (engine.last_event and engine.last_event['type'] == 'fight')),
                          timer_progress=max(0, turn_timer / TURN_LIMIT) if is_player_turn else 0)

        # ── Buttons ──────────────────────────────────────────────
        btn_sort.draw(screen)
        btn_group.draw(screen)
        if show_drop: btn_drop_meld.draw(screen)
        if show_fight: btn_call_fight.draw(screen)

      

        # ── Forced Meld Warning ──────────────────────────────────
        if is_player_turn and engine.has_forced_meld_pending(player):
            w2 = font_small.render("You MUST meld the card drawn from Discard!", True, Colors.TEXT_RED)
            screen.blit(w2,(WIDTH//2-w2.get_width()//2, layout['hand_y']-55))

        # ── Flying Cards ─────────────────────────────────────────
        surviving_flying = []
        for fc in flying_cards:
            fc['elapsed'] += dt
            t = min(fc['elapsed'] / max(fc['duration'], 0.001), 1.0)
            e = ease_out_cubic(t)
            cx2 = fc['start'][0] + (fc['end'][0] - fc['start'][0]) * e
            cy2 = fc['start'][1] + (fc['end'][1] - fc['start'][1]) * e

          
            if fc['elapsed'] < fc['duration']:
                surviving_flying.append(fc)
            
                f_scale = 0.75 * CARD_SCALE
                im = get_card_image(fc['card'], f_scale) if fc['is_face_up'] and fc['card'] else get_card_back(f_scale)
                if im: 
                    screen.blit(im, (int(cx2), int(cy2)))
        flying_cards = surviving_flying

        particles.draw(screen)
        
        # ── Dealer Chip (Drawn late to be on top of cards) ────────
        d_idx = dealer_mgr.get_idx()
        if d_idx < len(layout['dealer_anchors']):
            dx, dy = layout['dealer_anchors'][d_idx]
            dealer_mgr.draw(screen, dx, dy)
        
        if engine.game_phase == GamePhase.RESOLVING_FIGHT and fight_resolution_overlay:
            fight_resolution_overlay.draw(screen, engine.active_fight, player.calculate_points(), engine.players)

        if game_state=='game_over' and game_over_overlay:
            # Pull statuses from the fight event if applicable
            fight_statuses = None
            if engine.last_event and engine.last_event['type'] == 'fight':
                fight_statuses = engine.last_event['data'].get('statuses')
                
            game_over_overlay.draw(screen, engine.winner, engine.win_method, engine.get_scores(), engine, get_card_image, statuses=fight_statuses)

        if show_discard_modal:
            # Dim and blur the screen behind the modal
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((5, 10, 20, 200))
            screen.blit(overlay, (0, 0))

            # Adaptive Modal Size
            modal_w = min(1000, int(WIDTH * 0.85))
            modal_h = min(600, int(HEIGHT * 0.8))
            modal_x = WIDTH // 2 - modal_w // 2
            modal_y = HEIGHT // 2 - modal_h // 2
            
            # Modal Background with glassmorphism style
            pygame.draw.rect(screen, (30, 35, 50, 245), (modal_x, modal_y, modal_w, modal_h), border_radius=20)
            pygame.draw.rect(screen, Colors.TEXT_GOLD, (modal_x, modal_y, modal_w, modal_h), width=2, border_radius=20)

            # Title
            title_txt = font_title.render("Discard History", True, Colors.TEXT_GOLD)
            screen.blit(title_txt, (WIDTH // 2 - title_txt.get_width() // 2, modal_y + 25))
            
            # Separator Line
            pygame.draw.line(screen, (100, 100, 150, 100), (modal_x + 50, modal_y + 85), (modal_x + modal_w - 50, modal_y + 85), 2)

            # Grid Layout for cards
            c_startX = modal_x + 40
            c_startY = modal_y + 110
            
            total_cards = len(engine.discard_pile)
            if total_cards > 0:
                cols = 10 if total_cards > 10 else total_cards
                rows = (total_cards + cols - 1) // cols
                
                # Available area for cards
                avail_w = modal_w - 80
                avail_h = modal_h - 150
                
                # Target card size (preserve aspect ratio)
                card_aspect = 1.4 # typical H/W ratio
                target_w = min(80, avail_w // cols - 10)
                target_h = int(target_w * card_aspect)
                
                # Check if height exceeds available space and shrink if necessary
                if (target_h + 10) * rows > avail_h:
                    target_h = avail_h // rows - 10
                    target_w = int(target_h / card_aspect)

                for i, card in enumerate(engine.discard_pile):
                    # Draw in chronological order (oldest first)
                    col = i % cols
                    row = i // cols
                    cx = c_startX + col * (target_w + 10)
                    cy = c_startY + row * (target_h + 10)
                    
                    img = get_card_image(card)
                    if img:
                        scaled = pygame.transform.smoothscale(img, (target_w, target_h))
                        # Subtle card shadow
                        shadow = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
                        shadow.fill((0,0,0,80))
                        screen.blit(shadow, (cx + 3, cy + 3))
                        screen.blit(scaled, (cx, cy))
                      

        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()
