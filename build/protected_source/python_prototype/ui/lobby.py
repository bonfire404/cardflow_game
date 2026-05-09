import pygame
import random
import math
import os
from ui.paths import get_resource_path
from .ui_components import Colors

class Lobby:
    """Ultra-premium cinematic lobby with animated particles, Sekuya font, and modern glassmorphism banners."""

    def __init__(self, w, h, f_title, f_body, f_game_title=None):
        self.w, self.h = w, h
        self.font_title = f_game_title if f_game_title else f_title
        self.font_body = f_body
        self.font_small = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_micro = pygame.font.SysFont("Arial", 12, bold=True)
        # Load a smaller Sekuya for coin balance
        _sekuya_path = get_resource_path(os.path.join("assets", "fonts", "Sekuya", "Sekuya-Regular.ttf"))
        try: self.font_coins = pygame.font.Font(_sekuya_path, 28)
        except: self.font_coins = f_body
        self.time_acc = 0.0
        
        # Load app logo
        _logo_path = get_resource_path(os.path.join("assets", "images", "cardflow_logo.png"))
        try:
            self.logo_img = pygame.image.load(_logo_path).convert_alpha()
        except:
            self.logo_img = None
            
        # --- Particle System ---
        self.particles = []
        for _ in range(50):
            self.particles.append({
                'x': random.uniform(0, w),
                'y': random.uniform(0, h),
                'speed': random.uniform(20, 60),
                'size': random.uniform(1, 4),
                'alpha': random.randint(100, 255)
            })
        self.modes = [
            ("CASINO CLASSIC", "1 VS 2 BOTS", (0, 180, 255), True),
            ("AI ARENA", "BOT TRAINING", (255, 60, 60), True),
            ("RANK", "COMPETITIVE RANKED MODE", (255, 215, 0), True)
        ]
        
        self.banner_w = 260
        self.banner_h = 400
        self.banner_rects = []
        self.hover_idx = -1
        
        # --- Persistent Surfaces (FIX LAG) ---
        self.header_surf = pygame.Surface((w, 80), pygame.SRCALPHA)
        self.header_surf.fill((0, 0, 0, 150))
        pygame.draw.line(self.header_surf, (255, 215, 100), (0, 79), (w, 79), 2)
        
        self.overlay_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        self.overlay_surf.fill((10, 5, 0, 30))
        
        self.vignette_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(self.vignette_surf, (40, 20, 0, 60), (0, 0, w, h), width=150)
        
        self.footer_surf = pygame.Surface((w, 80), pygame.SRCALPHA)
        self.footer_surf.fill((0, 0, 0, 220))
        pygame.draw.line(self.footer_surf, (100, 100, 120), (0, 0), (w, 0), 1)
        
        self.frame_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
        # Multi-ring profile frame
        pygame.draw.circle(self.frame_surf, (120, 90, 20, 80), (40, 40), 38)  # Outer shadow
        pygame.draw.circle(self.frame_surf, (200, 170, 60), (40, 40), 36)     # Gold outer
        pygame.draw.circle(self.frame_surf, (255, 225, 120), (40, 40), 34)    # Gold highlight
        pygame.draw.circle(self.frame_surf, (180, 145, 40), (40, 40), 34, 2)  # Gold edge
        pygame.draw.circle(self.frame_surf, (25, 25, 35), (40, 40), 30)       # Dark inset
        pygame.draw.circle(self.frame_surf, (45, 42, 55), (40, 40), 28)       # Inner bg
        
        self.shine_dot = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.shine_dot, (255, 255, 255, 200), (5, 5), 5)

        # Avatar Cache
        self.cached_avatar_img = None
        self.cached_avatar_surf = None
        
        # Load Icons
        self.icons = []
        lobby_dir = get_resource_path(os.path.join("assets", "images", "lobby"))
        icon_files = ["classic_mode.png", "ai_mode.png", "rank_mode.png"]
        for fn in icon_files:
            try:
                img = pygame.image.load(os.path.join(lobby_dir, fn)).convert_alpha()
                self.icons.append(pygame.transform.smoothscale(img, (140, 140)))
            except: self.icons.append(None)
            
        # Load Help Icons (White and Black for hover)
        try:
            help_white_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "information.png"))
            self.icon_help_white = pygame.image.load(help_white_path).convert_alpha()
            self.icon_help_white = pygame.transform.smoothscale(self.icon_help_white, (24, 24))
            
            help_black_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "Black", "2x", "information.png"))
            self.icon_help_black = pygame.image.load(help_black_path).convert_alpha()
            self.icon_help_black = pygame.transform.smoothscale(self.icon_help_black, (24, 24))
        except:
            self.icon_help_white = None
            self.icon_help_black = None
            
        # Load Settings Icons
        try:
            gear_white_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "gear.png"))
            self.icon_gear_white = pygame.image.load(gear_white_path).convert_alpha()
            self.icon_gear_white = pygame.transform.smoothscale(self.icon_gear_white, (24, 24))
            
            gear_black_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "Black", "2x", "gear.png"))
            self.icon_gear_black = pygame.image.load(gear_black_path).convert_alpha()
            self.icon_gear_black = pygame.transform.smoothscale(self.icon_gear_black, (24, 24))
        except:
            self.icon_gear_white = None
            self.icon_gear_black = None
            
        # Load Quit Icons
        try:
            exit_white_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "exit.png"))
            self.icon_exit_white = pygame.image.load(exit_white_path).convert_alpha()
            self.icon_exit_white = pygame.transform.smoothscale(self.icon_exit_white, (24, 24))
            
            exit_black_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "Black", "2x", "exit.png"))
            self.icon_exit_black = pygame.image.load(exit_black_path).convert_alpha()
            self.icon_exit_black = pygame.transform.smoothscale(self.icon_exit_black, (24, 24))
        except:
            self.icon_exit_white = None
            self.icon_exit_black = None
            
        # Load Quest Icons
        try:
            quest_white_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "medal1.png"))
            self.icon_quest_white = pygame.image.load(quest_white_path).convert_alpha()
            self.icon_quest_white = pygame.transform.smoothscale(self.icon_quest_white, (24, 24))
            
            quest_black_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "Black", "2x", "medal1.png"))
            self.icon_quest_black = pygame.image.load(quest_black_path).convert_alpha()
            self.icon_quest_black = pygame.transform.smoothscale(self.icon_quest_black, (24, 24))
        except:
            self.icon_quest_white = None
            self.icon_quest_black = None
            self.icon_gear_black = None
            
        # Load Center Icons
        self.center_icons = []
        icons_dir = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x"))
        center_icon_files = ["multiplayer.png", "singleplayer.png", "trophy.png"]
        for fn in center_icon_files:
            try:
                img = pygame.image.load(os.path.join(icons_dir, fn)).convert_alpha()
                self.center_icons.append(pygame.transform.smoothscale(img, (80, 80)))
            except: self.center_icons.append(None)
            
        try:
            cf_path = os.path.join(lobby_dir, "currency_frame.png")
            self.coin_frame_orig = pygame.image.load(cf_path).convert_alpha()
        except:
            self.coin_frame_orig = None
        
        self.selected_bets = {0: 0, 1: 0, 2: 0}
        self.mode_bets = {
            0: [100, 300, 600],
            1: ["EASY", "MEDIUM", "HARD"],
            2: [1000, 5000, 10000]
        }
        self.bet_rects_map = {} # Map mode_idx -> list of button rects
        
        self.help_btn_rect = pygame.Rect(0,0,0,0)
        self.recalc_banners()

    def recalc_banners(self):
        """Recalculate all bounding boxes and decorative surfaces for responsiveness."""
        # 1. Background Surfaces
        self.header_surf = pygame.Surface((self.w, 80), pygame.SRCALPHA)
        self.header_surf.fill((0, 0, 0, 150))
        pygame.draw.line(self.header_surf, (255, 215, 100), (0, 79), (self.w, 79), 2)
        
        self.overlay_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.overlay_surf.fill((10, 5, 0, 30))
        
        self.vignette_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.rect(self.vignette_surf, (40, 20, 0, 60), (0, 0, self.w, self.h), width=150)
        
        self.footer_surf = pygame.Surface((self.w, 80), pygame.SRCALPHA)
        self.footer_surf.fill((0, 0, 0, 220))
        pygame.draw.line(self.footer_surf, (100, 100, 120), (0, 0), (self.w, 0), 1)

        # 2. Layout Positioning
        self.banner_rects = []
        gap = 40
        total_w = len(self.modes) * self.banner_w + (len(self.modes) - 1) * gap
        start_x = self.w // 2 - total_w // 2
        
        # Help & Settings Button Position (Top Right)
        bw_h = 46
        self.help_btn_rect = pygame.Rect(self.w - bw_h - 20, 18, bw_h, bw_h)
        self.settings_btn_rect = pygame.Rect(self.w - (bw_h * 2) - 30, 18, bw_h, bw_h)
        
        # Quit & Quest Buttons (Bottom Right)
        self.quit_btn_rect = pygame.Rect(self.w - bw_h - 20, self.h - 65, bw_h, bw_h)
        self.quest_btn_rect = pygame.Rect(self.w - (bw_h * 2) - 30, self.h - 65, bw_h, bw_h)
        
        start_y = self.h // 2 - self.banner_h // 2 + 20
        for i in range(len(self.modes)):
            self.banner_rects.append(pygame.Rect(start_x + i * (self.banner_w + gap), start_y, self.banner_w, self.banner_h))

    def update(self, dt, m_pos):
        self.time_acc += dt
        self.hover_idx = -1
        for i, r in enumerate(self.banner_rects):
            if r.inflate(10, 10).collidepoint(m_pos):
                self.hover_idx = i
                break
        
        # Update particles
        for p in self.particles:
            p['y'] -= p['speed'] * dt
            if p['y'] < -10:
                p['y'] = self.h + 10
                p['x'] = random.uniform(0, self.w)

    def handle_event(self, event, stats=None):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check Profile Click
            ax, ay = 30, self.h - 65
            profile_rect = pygame.Rect(ax, ay, 200, 52)
            if profile_rect.collidepoint(event.pos):
                return {"type": "profile"}

            # Check Help Button
            if self.help_btn_rect.collidepoint(event.pos):
                return {"type": "help"}

            # Check Settings Button
            if self.settings_btn_rect.collidepoint(event.pos):
                return {"type": "settings"}
                
            # Check Quit Button
            if self.quit_btn_rect.collidepoint(event.pos):
                return {"type": "quit"}

            # Check Quest Button
            if self.quest_btn_rect.collidepoint(event.pos):
                return {"type": "quest"}


            # Check bet selection for modes that support it
            reqs = {
                0: {300: 5, 600: 10},
                2: {1000: 10, 5000: 30, 10000: 50}
            }
            player_level = stats.get('level', 1) if stats else 1

            if self.hover_idx in self.mode_bets:
                for b_idx, b_rect in enumerate(self.bet_rects_map.get(self.hover_idx, [])):
                    if b_rect.collidepoint(event.pos):
                        # Check if locked
                        mode_reqs = reqs.get(self.hover_idx, {})
                        mode_bet_list = self.mode_bets.get(self.hover_idx, [100])
                        val = mode_bet_list[b_idx]
                        req_lvl = mode_reqs.get(val, 1)
                        
                        if self.hover_idx == 2 and player_level < req_lvl:
                            # Hard lock Rank Mode
                            return None
                            
                        self.selected_bets[self.hover_idx] = b_idx
                        return None # Switch bet, don't start game

            for i, r in enumerate(self.banner_rects):
                if self.modes[i][3]:
                    play_rect = pygame.Rect(r.centerx - 70, r.bottom - 55, 140, 42)
                    if play_rect.collidepoint(event.pos):
                        # Get selected bet for this mode, or default to 0
                        mode_bet_list = self.mode_bets.get(i, [100])
                        sel_idx = self.selected_bets.get(i, 0)
                        val = mode_bet_list[sel_idx]
                        
                        # Check lock for Classic Mode and Rank Mode
                        mode_reqs = reqs.get(i, {})
                        req_lvl = mode_reqs.get(val, 1)
                        if player_level < req_lvl:
                            if i == 0: # Classic Mode (Soft lock/Warning)
                                return {"type": "warning_modal", "mode_idx": i, "bet": val, "req_lvl": req_lvl}
                            elif i == 2: # Rank Mode (Hard lock)
                                return None # Completely ignore clicks
                            
                        return {"mode_idx": i, "bet": val}
        return None

    def _get_masked_avatar(self, avatar):
        if avatar == self.cached_avatar_img and self.cached_avatar_surf:
            return self.cached_avatar_surf
        self.cached_avatar_img = avatar
        
        av_scaled = pygame.transform.smoothscale(avatar, (52, 52))
        mask = pygame.Surface((52, 52), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255), (26, 26), 26)
        av_scaled.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        self.cached_avatar_surf = av_scaled
        return self.cached_avatar_surf

    def draw(self, surface, name, avatar, stats, lb_bg):
        # 1. Background
        if lb_bg: 
            surface.blit(lb_bg, (0, 0))
            overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            overlay.fill((8, 5, 20, 140)) # Deeper, more cinematic tint
            surface.blit(overlay, (0, 0))
        else: surface.fill((15, 10, 25))

        # --- Draw Particles ---
        for p in self.particles:
            a = int(p['alpha'] * (0.6 + 0.4 * math.sin(self.time_acc * 2 + p['x'])))
            pygame.draw.circle(surface, (255, 255, 255, max(0, min(a, 255))), (int(p['x']), int(p['y'])), int(p['size']))

        # 2. Header
        surface.blit(self.header_surf, (0, 0))
        
        # Animated sweep light on header
        sweep_x = int((self.time_acc * 150) % (self.w + 400)) - 200
        sweep_surf = pygame.Surface((200, 80), pygame.SRCALPHA)
        for col in range(200):
            sa = int(25 * math.sin(col / 200 * math.pi))
            pygame.draw.line(sweep_surf, (255, 255, 255, sa), (col, 0), (col, 80))
        surface.blit(sweep_surf, (sweep_x, 0))

        if self.coin_frame_orig:
            balance_str = f"{stats.get('coins', 0):,}"
            
            # Modernized text: Pure White with a subtle Gold Glow/Shadow
            shadow_color = (150, 110, 20) # Deep gold shadow
            main_color = (255, 255, 255)  # Crisp white text
            
            gap = 3 # 3 pixels gap for visible difference
            
            # Render main text with gaps
            main_surfs = [self.font_coins.render(char, True, main_color) for char in balance_str]
            total_w = sum(s.get_width() for s in main_surfs) + gap * (len(balance_str) - 1)
            main_txt = pygame.Surface((total_w, main_surfs[0].get_height()), pygame.SRCALPHA)
            x_offset = 0
            for s in main_surfs:
                main_txt.blit(s, (x_offset, 0))
                x_offset += s.get_width() + gap
                
            # Render shadow text with gaps
            shadow_surfs = [self.font_coins.render(char, True, shadow_color) for char in balance_str]
            shadow_txt = pygame.Surface((total_w, shadow_surfs[0].get_height()), pygame.SRCALPHA)
            x_offset = 0
            for s in shadow_surfs:
                shadow_txt.blit(s, (x_offset, 0))
                x_offset += s.get_width() + gap
                
            # Auto-adjust frame width with more padding
            frame_w = max(210, total_w + 80)
            coin_frame = pygame.transform.smoothscale(self.coin_frame_orig, (frame_w, 80))
            
            cx, cy = 25, 10
            surface.blit(coin_frame, (cx, cy))
            
            # Centering for the auto-adjusted frame
            tx = cx + frame_w // 2 - total_w // 2
            ty = cy + 40 - main_txt.get_height() // 2

            
            # Draw shadow then main text
            surface.blit(shadow_txt, (tx + 2, ty + 2))
            surface.blit(main_txt, (tx, ty))

        # Stylized Game Title: CARDFL(ICON)W
        part1 = "CARDFL"
        part2 = "W"
        
        txt_p1 = self.font_title.render(part1, True, (225, 40, 40))
        txt_p2 = self.font_title.render(part2, True, (225, 40, 40))
        
        sh_b1 = self.font_title.render(part1, True, (10, 5, 5))
        sh_b2 = self.font_title.render(part2, True, (10, 5, 5))
        sh_w1 = self.font_title.render(part1, True, (240, 240, 240))
        sh_w2 = self.font_title.render(part2, True, (240, 240, 240))
        
        icon_h = txt_p1.get_height()
        icon_w = icon_h
        icon_scaled = None
        
        if self.logo_img:
            img_rect = self.logo_img.get_rect()
            aspect = img_rect.w / img_rect.h
            icon_w = int(icon_h * aspect)
            icon_scaled = pygame.transform.smoothscale(self.logo_img, (icon_w, icon_h))
        else:
            # Fallback to letter O
            txt_o = self.font_title.render("O", True, (225, 40, 40))
            sh_bo = self.font_title.render("O", True, (10, 5, 5))
            sh_wo = self.font_title.render("O", True, (240, 240, 240))
            icon_w = txt_o.get_width()
            
        gap = -12
        total_w = txt_p1.get_width() + icon_w + txt_p2.get_width() + gap * 2
        
        tx = self.w // 2 - total_w // 2
        ty = 15
        
        # Draw Part 1
        surface.blit(sh_b1, (tx + 3, ty + 3))
        surface.blit(sh_w1, (tx - 1, ty - 1))
        surface.blit(txt_p1, (tx, ty))
        
        x_offset = tx + txt_p1.get_width() + gap
        
        # Draw Icon or Fallback O
        if icon_scaled:
            surface.blit(icon_scaled, (x_offset, ty))
        else:
            surface.blit(sh_bo, (x_offset + 3, ty + 3))
            surface.blit(sh_wo, (x_offset - 1, ty - 1))
            surface.blit(txt_o, (x_offset, ty))
            
        x_offset += icon_w + gap
        
        # Draw Part 2
        surface.blit(sh_b2, (x_offset + 3, ty + 3))
        surface.blit(sh_w2, (x_offset - 1, ty - 1))
        surface.blit(txt_p2, (x_offset, ty))

        # 3. Central Modes
        for i, (m_name, m_sub, m_color, active) in enumerate(self.modes):
            rect = self.banner_rects[i].copy()
            is_hover = (self.hover_idx == i and active)
            float_y = 12 * math.sin(self.time_acc * 1.8 + i * 0.9)
            rect.y += float_y
            
            # Subtle glow behind card if active
            if active:
                ga = 30 if is_hover else 15
                gs = pygame.Surface((rect.w + 40, rect.h + 40), pygame.SRCALPHA)
                pygame.draw.rect(gs, (*m_color, ga), (0, 0, rect.w + 40, rect.h + 40), border_radius=40)
                surface.blit(gs, (rect.x - 20, rect.y - 20))

            if is_hover:
                rect.inflate_ip(16, 16)
                rect.y -= 15
            
            # --- Card Frame (Image-based) ---
            if i < len(self.icons) and self.icons[i]:
                # Scale and draw the provided card frame
                if i == 0: # Casino Classic
                    frame_img = pygame.transform.smoothscale(self.icons[i], (rect.w + 20, rect.h + 20))
                    blit_pos = (rect.x - 10, rect.y - 10)
                else:
                    frame_img = pygame.transform.smoothscale(self.icons[i], (rect.w, rect.h))
                    blit_pos = rect.topleft
                
                # Draw backdrop inside the frame so it's not transparent (Inset by 15px)
                bg_surf = pygame.Surface((rect.w - 30, rect.h - 30), pygame.SRCALPHA)
                pygame.draw.rect(bg_surf, (15, 12, 25, 220), (0, 0, rect.w - 30, rect.h - 30), border_radius=20)
                surface.blit(bg_surf, (rect.x + 15, rect.y + 15))
                
                # Apply hover transparency or glow
                if is_hover:
                    # Optional: Add a slight gold glow behind the card on hover
                    glow_surf = pygame.Surface((rect.w + 20, rect.h + 20), pygame.SRCALPHA)
                    pygame.draw.rect(glow_surf, (255, 215, 100, 40), (0, 0, rect.w + 20, rect.h + 20), border_radius=32)
                    surface.blit(glow_surf, (rect.x - 10, rect.y - 10))
                
                surface.blit(frame_img, blit_pos)
            else:
                # Fallback to Premium Glass Card Body if image missing
                b_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                b_alpha = 200 if is_hover else 140
                for row in range(rect.h):
                    rt = row / rect.h
                    rc, gc, bc = int(25 + 15 * rt), int(30 + 15 * rt), int(50 + 20 * rt)
                    pygame.draw.line(b_surf, (rc, gc, bc, b_alpha), (0, row), (rect.w, row))
                
                mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.w, rect.h), border_radius=32)
                b_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                surface.blit(b_surf, rect.topleft)
                
                # Fallback Border
                bx_color = (255, 230, 100, 220) if is_hover else (*m_color, 140) if active else (100, 100, 110, 100)
                pygame.draw.rect(surface, bx_color, rect, width=3 if is_hover else 2, border_radius=32)

            # Draw Center Icon
            if i < len(self.center_icons) and self.center_icons[i]:
                icon_img = self.center_icons[i]
                
                # Calculate space for icon (above separator and bet buttons)
                icon_space_h = rect.h - 165 if i in self.mode_bets else rect.h - 120
                cy = rect.y + icon_space_h // 2
                cx = rect.centerx
                
                ix = cx - icon_img.get_width() // 2
                iy = cy - icon_img.get_height() // 2
                
                # Draw Glow behind icon
                glow_size = icon_img.get_width() + 40
                glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*m_color, 40), (glow_size//2, glow_size//2), glow_size//2)
                surface.blit(glow_surf, (cx - glow_size//2, cy - glow_size//2))
                
                # Draw Icon
                surface.blit(icon_img, (ix, iy))

            # Inner separator line between icon and text
            sep_y = rect.bottom - 120
            sep_s = pygame.Surface((rect.w - 40, 1), pygame.SRCALPHA)
            sep_s.fill((255, 255, 255, 30))
            surface.blit(sep_s, (rect.x + 20, sep_y))

            # --- Bet Selection (For modes defined in mode_bets) ---
            if i in self.mode_bets:
                mode_bet_rects = []
                bw, bh = 60, 24
                mode_vals = self.mode_bets[i]
                total_bw = len(mode_vals) * bw + (len(mode_vals)-1) * 8
                sx = rect.centerx - total_bw // 2
                sy = sep_y - 45 # Positioned between icon/artwork and separator
                
                # Level requirements
                reqs = {
                    0: {300: 5, 600: 10},
                    2: {1000: 10, 5000: 30, 10000: 50}
                }
                player_level = stats.get('level', 1) if stats else 1
                
                for b_idx, val in enumerate(mode_vals):
                    b_rect = pygame.Rect(sx + b_idx * (bw + 8), sy, bw, bh)
                    mode_bet_rects.append(b_rect)
                    is_sel = (self.selected_bets.get(i, 0) == b_idx)
                    
                    # Check if locked (only hard lock Rank mode i == 2)
                    mode_reqs = reqs.get(i, {})
                    req_lvl = mode_reqs.get(val, 1)
                    is_locked = (player_level < req_lvl)
                    
                    # Button Body
                    if i == 2 and is_locked:
                        bc = (60, 60, 70, 150) # Grayed out
                        tc = (120, 120, 130)
                        is_sel = False # Cannot be selected
                    else:
                        bc = (255, 215, 50, 220) if is_sel else (40, 45, 60, 180)
                        if not is_sel and b_rect.collidepoint(pygame.mouse.get_pos()):
                            bc = (255, 230, 120, 140)
                        tc = (20, 15, 0) if is_sel else (220, 220, 230)
                    
                    pygame.draw.rect(surface, bc, b_rect, border_radius=12)
                    if is_sel:
                        # Glow for selected
                        glow = pygame.Surface((bw+8, bh+8), pygame.SRCALPHA)
                        pygame.draw.rect(glow, (255, 215, 50, 40), (0, 0, bw+8, bh+8), border_radius=15)
                        surface.blit(glow, (b_rect.x-4, b_rect.y-4))
 
                    # Text (Using 'k' shorthand for large values)
                    if i == 2 and is_locked:
                        txt_val = f"Lv{req_lvl}"
                    else:
                        if isinstance(val, str):
                            txt_val = val
                        else:
                            txt_val = f"{val//1000}k" if val >= 1000 else str(val)
                        
                    v_txt = self.font_micro.render(txt_val, True, tc)
                    surface.blit(v_txt, (b_rect.centerx - v_txt.get_width()//2, b_rect.centery - v_txt.get_height()//2))
                
                self.bet_rects_map[i] = mode_bet_rects
            
            # Text Design
            name_color = (255, 255, 255) if active else (150, 150, 160)
            n_txt = self.font_body.render(m_name, True, name_color)
            surface.blit(n_txt, (rect.centerx - n_txt.get_width()//2, sep_y + 12))
            
            sub_txt = self.font_micro.render(m_sub, True, (180, 180, 200) if active else (110, 110, 120))
            surface.blit(sub_txt, (rect.centerx - sub_txt.get_width() // 2, sep_y + 35))
            
            if not active:
                l_rect = pygame.Rect(rect.centerx - 50, rect.centery - 13, 100, 26)
                pygame.draw.rect(surface, (15, 12, 25, 200), l_rect, border_radius=13)
                pygame.draw.rect(surface, (100, 100, 120, 180), l_rect, width=1, border_radius=13)
                l_txt = self.font_micro.render("COMING SOON", True, (180, 180, 200))
                surface.blit(l_txt, (l_rect.centerx - l_txt.get_width()//2, l_rect.centery - l_txt.get_height()//2))
            else:
                # Determine if button is locked
                reqs = {
                    0: {300: 5, 600: 10},
                    2: {1000: 10, 5000: 30, 10000: 50}
                }
                player_level = stats.get('level', 1) if stats else 1
                mode_bet_list = self.mode_bets.get(i, [100])
                sel_idx = self.selected_bets.get(i, 0)
                sel_val = mode_bet_list[sel_idx]
                mode_reqs = reqs.get(i, {})
                req_lvl = mode_reqs.get(sel_val, 1)
                is_btn_locked = (player_level < req_lvl)

                play_rect = pygame.Rect(rect.centerx - 70, rect.bottom - 55, 140, 42)
                m_pos = pygame.mouse.get_pos()
                btn_hover = play_rect.collidepoint(m_pos) and not is_btn_locked
                
                # Modern gradient/gloss button
                btn_surface = pygame.Surface((play_rect.w, play_rect.h), pygame.SRCALPHA)
                
                # Dynamic colors based on mode theme
                m_r, m_g, m_b = m_color
                if is_btn_locked:
                    base_color = (60, 60, 70)
                    dark_color = (40, 40, 50)
                elif btn_hover:
                    base_color = (min(255, m_r + 40), min(255, m_g + 40), min(255, m_b + 40))
                    dark_color = (max(0, m_r - 20), max(0, m_g - 20), max(0, m_b - 20))
                else:
                    base_color = m_color
                    dark_color = (max(0, m_r - 80), max(0, m_g - 80), max(0, m_b - 80))
                
                # Vertical gradient
                for y in range(play_rect.h):
                    t = y / play_rect.h
                    r = int(base_color[0] * (1-t) + dark_color[0] * t)
                    g = int(base_color[1] * (1-t) + dark_color[1] * t)
                    b = int(base_color[2] * (1-t) + dark_color[2] * t)
                    pygame.draw.line(btn_surface, (r, g, b, 255), (0, y), (play_rect.w, y))
                    
                # Glass highlight
                hl_rect = pygame.Rect(2, 2, play_rect.w - 4, play_rect.h // 2)
                pygame.draw.rect(btn_surface, (255, 255, 255, 60 if btn_hover else 30), hl_rect, border_radius=18)
                
                # Border
                border_color = (200, 255, 200, 180) if not is_btn_locked else (100, 100, 110, 100)
                pygame.draw.rect(btn_surface, border_color, (0, 0, play_rect.w, play_rect.h), width=2, border_radius=20)
                
                # Apply rounded mask
                mask = pygame.Surface((play_rect.w, play_rect.h), pygame.SRCALPHA)
                pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, play_rect.w, play_rect.h), border_radius=20)
                btn_surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                
                # Drop shadow
                shadow = pygame.Surface((play_rect.w + 6, play_rect.h + 8), pygame.SRCALPHA)
                pygame.draw.rect(shadow, (0, 0, 0, 80), (0, 0, shadow.get_width(), shadow.get_height()), border_radius=22)
                surface.blit(shadow, (play_rect.x - 3, play_rect.y - 1))
                
                surface.blit(btn_surface, play_rect)
                
                # Dynamic text sizing/coloring
                if is_btn_locked:
                    p_text = f"LOCKED (LV{req_lvl})"
                    text_font = self.font_micro # Use smaller font for level requirement
                else:
                    p_text = "P L A Y" if btn_hover else "PLAY"
                    text_font = self.font_body
                
                p_txt = text_font.render(p_text, True, (255, 255, 255) if not is_btn_locked else (150, 150, 160))
                # Text Shadow
                sh_col = (max(0, m_r - 120), max(0, m_g - 120), max(0, m_b - 120)) if not is_btn_locked else (20, 20, 25)
                p_shadow = text_font.render(p_text, True, sh_col)
                
                cx = play_rect.centerx - p_txt.get_width()//2
                cy = play_rect.centery - p_txt.get_height()//2
                surface.blit(p_shadow, (cx + 1, cy + 2))
                surface.blit(p_txt, (cx, cy))

        # 4. Vignette & Footer
        surface.blit(self.vignette_surf, (0, 0))
        surface.blit(self.footer_surf, (0, self.h - 80))

        # Footer Profile Section
        ax, ay = 30, self.h - 65
        
        # Footer Profile Section (Minimalist)
        ax, ay = 30, self.h - 65
        
        # Avatar (Minimalist round, no cover)
        if avatar:
            surface.blit(self._get_masked_avatar(avatar), (ax, ay))
        else:
            pygame.draw.circle(surface, (60, 70, 90), (ax + 26, ay + 26), 26)

        # Player name
        text_x = ax + 65
        p_txt = self.font_body.render(name.upper(), True, (255, 255, 255))
        surface.blit(p_txt, (text_x, ay + 10))
        
        # Level beside name
        level = stats.get('level', 1)
        lvl_txt = self.font_small.render(f"LVL {level}", True, (150, 160, 180))
        surface.blit(lvl_txt, (text_x + p_txt.get_width() + 10, ay + 14))


        # 4. Draw Help Button ('?')
        hb = self.help_btn_rect
        m_pos = pygame.mouse.get_pos()
        hb_hover = hb.collidepoint(m_pos)
        
        # Draw background circle
        bc = (255, 215, 50) if hb_hover else (40, 45, 60, 180)
        pygame.draw.circle(surface, bc, hb.center, hb.w // 2)
        
        # Draw border
        pygame.draw.circle(surface, (255, 255, 255, 200), hb.center, hb.w // 2, width=2)
        
        # Draw '?' icon or fallback to text
        if hb_hover and self.icon_help_black:
            surface.blit(self.icon_help_black, (hb.centerx - 12, hb.centery - 12))
        elif not hb_hover and self.icon_help_white:
            surface.blit(self.icon_help_white, (hb.centerx - 12, hb.centery - 12))
        else:
            try:
                f_help = pygame.font.SysFont("Arial", 24, bold=True)
            except:
                f_help = self.font_body
            tc = (20, 15, 0) if hb_hover else (220, 220, 230)
            txt_help = f_help.render("?", True, tc)
            surface.blit(txt_help, (hb.centerx - txt_help.get_width()//2, hb.centery - txt_help.get_height()//2))

        # 5. Draw Settings Button
        sb = self.settings_btn_rect
        sb_hover = sb.collidepoint(m_pos)
        
        # Draw background circle
        bc = (255, 215, 50) if sb_hover else (40, 45, 60, 180)
        pygame.draw.circle(surface, bc, sb.center, sb.w // 2)
        
        # Draw border
        pygame.draw.circle(surface, (255, 255, 255, 200), sb.center, sb.w // 2, width=2)
        
        # Draw gear icon
        if sb_hover and self.icon_gear_black:
            surface.blit(self.icon_gear_black, (sb.centerx - 12, sb.centery - 12))
        elif not sb_hover and self.icon_gear_white:
            surface.blit(self.icon_gear_white, (sb.centerx - 12, sb.centery - 12))

        # 6. Draw Quit Button
        qb = self.quit_btn_rect
        qb_hover = qb.collidepoint(m_pos)
        bc = (255, 50, 50) if qb_hover else (40, 45, 60, 180)
        pygame.draw.circle(surface, bc, qb.center, qb.w // 2)
        pygame.draw.circle(surface, (255, 255, 255, 200), qb.center, qb.w // 2, width=2)
        
        if qb_hover and self.icon_exit_black:
            surface.blit(self.icon_exit_black, (qb.centerx - 12, qb.centery - 12))
        elif not qb_hover and self.icon_exit_white:
            surface.blit(self.icon_exit_white, (qb.centerx - 12, qb.centery - 12))
        else:
            txt = self.font_small.render("EXIT", True, (255, 255, 255))
            surface.blit(txt, (qb.centerx - txt.get_width()//2, qb.centery - txt.get_height()//2))
            
        # 7. Draw Quest Button
        qsb = self.quest_btn_rect
        qsb_hover = qsb.collidepoint(m_pos)
        bc = (255, 215, 50) if qsb_hover else (40, 45, 60, 180)
        pygame.draw.circle(surface, bc, qsb.center, qsb.w // 2)
        pygame.draw.circle(surface, (255, 255, 255, 200), qsb.center, qsb.w // 2, width=2)
        
        if qsb_hover and self.icon_quest_black:
            surface.blit(self.icon_quest_black, (qsb.centerx - 12, qsb.centery - 12))
        elif not qsb_hover and self.icon_quest_white:
            surface.blit(self.icon_quest_white, (qsb.centerx - 12, qsb.centery - 12))
        else:
            txt = self.font_small.render("!", True, (255, 255, 255))
            surface.blit(txt, (qsb.centerx - txt.get_width()//2, qsb.centery - txt.get_height()//2))
