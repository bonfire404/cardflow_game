import pygame
import random
import math
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
        import os as _os
        _sekuya_path = _os.path.join(_os.path.dirname(__file__), "..", "..", "assets", "fonts", "Sekuya", "Sekuya-Regular.ttf")
        try: self.font_coins = pygame.font.Font(_sekuya_path, 22)
        except: self.font_coins = f_body
        self.time_acc = 0.0
        
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
            ("PLAY NOW", "CASINO CLASSIC", (255, 215, 0), True),
            ("AI ARENA", "BOT TRAINING", (180, 100, 255), True),
            ("FRIENDS", "SOCIAL LOUNGE", (0, 180, 255), False),
            ("ARENA", "RANKED GLORY", (255, 60, 60), False)
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
        import os
        lobby_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "images", "lobby")
        icon_files = ["play_now.png", "ai_arena.png", "friends.png", "arena_ranked.png"]
        for fn in icon_files:
            try:
                img = pygame.image.load(os.path.join(lobby_dir, fn)).convert_alpha()
                self.icons.append(pygame.transform.smoothscale(img, (140, 140)))
            except: self.icons.append(None)
            
        try:
            cf_path = os.path.join(lobby_dir, "currency_frame.png")
            self.coin_frame = pygame.image.load(cf_path).convert_alpha()
            self.coin_frame = pygame.transform.smoothscale(self.coin_frame, (240, 80))
        except:
            self.coin_frame = None
        
        self.selected_bet_idx = 0
        self.bet_values = [100, 300, 600]
        self.bet_rects = [] # Dynamic rects for the 3 bet buttons
        
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

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check bet selection for Casino Classic (index 0)
            if self.hover_idx == 0:
                for b_idx, b_rect in enumerate(self.bet_rects):
                    if b_rect.collidepoint(event.pos):
                        self.selected_bet_idx = b_idx
                        return None # Don't start game yet, just switch bet

            for i, r in enumerate(self.banner_rects):
                if r.collidepoint(event.pos) and self.modes[i][3]:
                    # Return both mode and selected bet
                    return {"mode_idx": i, "bet": self.bet_values[self.selected_bet_idx]}
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

        if self.coin_frame:
            cx, cy = 25, 0
            surface.blit(self.coin_frame, (cx, cy))
            balance_str = f"{stats['coins']:,}"
            glow_txt = self.font_coins.render(balance_str, True, (255, 215, 100))
            surface.blit(glow_txt, (cx + 150 - glow_txt.get_width() // 2, cy + 40 - glow_txt.get_height() // 2))

        # Sekuya Title with Glow
        main_title = "MAMA'S GO"
        title_pulse = int(230 + 25 * math.sin(self.time_acc * 3))
        title_txt = self.font_title.render(main_title, True, (255, 215, 50))
        # Shadow for depth
        shadow_txt = self.font_title.render(main_title, True, (20, 10, 0))
        tx = self.w // 2 - title_txt.get_width() // 2
        ty = 15
        surface.blit(shadow_txt, (tx + 2, ty + 2))
        surface.blit(title_txt, (tx, ty))

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
            
            # Premium Glass Card Body
            b_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            b_alpha = 200 if is_hover else 140
            
            # Per-row gradient for card body
            for row in range(rect.h):
                rt = row / rect.h
                rc = int(25 + 15 * rt)
                gc = int(30 + 15 * rt)
                bc = int(50 + 20 * rt)
                pygame.draw.line(b_surf, (rc, gc, bc, b_alpha), (0, row), (rect.w, row))
            
            # Round the corners
            mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.w, rect.h), border_radius=32)
            b_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            
            # Frosted glass highlight
            f_hl = pygame.Surface((rect.w, 80), pygame.SRCALPHA)
            pygame.draw.rect(f_hl, (255, 255, 255, 20 if is_hover else 12), (0, 0, rect.w, 80), border_radius=32)
            b_surf.blit(f_hl, (0, 0))
            
            surface.blit(b_surf, rect.topleft)
            
            # Animated Border
            bx_color = (255, 230, 100, 220) if is_hover else (*m_color, 140) if active else (100, 100, 110, 100)
            bw = 3 if is_hover else 2
            pygame.draw.rect(surface, bx_color, rect, width=bw, border_radius=32)

            # Decorative corner accents (top-left, top-right, bottom-left, bottom-right)
            if active:
                corner_len = 20
                corner_a = 200 if is_hover else 120
                cc = (*m_color[:3], corner_a) if not is_hover else (255, 230, 100, corner_a)
                # Top-left
                pygame.draw.line(surface, cc, (rect.x + 8, rect.y + 4), (rect.x + 8 + corner_len, rect.y + 4), 3)
                pygame.draw.line(surface, cc, (rect.x + 4, rect.y + 8), (rect.x + 4, rect.y + 8 + corner_len), 3)
                # Top-right
                pygame.draw.line(surface, cc, (rect.right - 8, rect.y + 4), (rect.right - 8 - corner_len, rect.y + 4), 3)
                pygame.draw.line(surface, cc, (rect.right - 4, rect.y + 8), (rect.right - 4, rect.y + 8 + corner_len), 3)
                # Bottom-left
                pygame.draw.line(surface, cc, (rect.x + 8, rect.bottom - 4), (rect.x + 8 + corner_len, rect.bottom - 4), 3)
                pygame.draw.line(surface, cc, (rect.x + 4, rect.bottom - 8), (rect.x + 4, rect.bottom - 8 - corner_len), 3)
                # Bottom-right
                pygame.draw.line(surface, cc, (rect.right - 8, rect.bottom - 4), (rect.right - 8 - corner_len, rect.bottom - 4), 3)
                pygame.draw.line(surface, cc, (rect.right - 4, rect.bottom - 8), (rect.right - 4, rect.bottom - 8 - corner_len), 3)

            icon_y = rect.y + 110
            if i < len(self.icons) and self.icons[i]:
                icon_img = self.icons[i]
                if is_hover: 
                    icon_img = pygame.transform.smoothscale(icon_img, (165, 165))
                    surface.blit(icon_img, (rect.centerx - 82, icon_y - 82))
                else: 
                    surface.blit(icon_img, (rect.centerx - 70, icon_y - 70))

            # Inner separator line between icon and text
            sep_y = rect.bottom - 120
            sep_s = pygame.Surface((rect.w - 40, 1), pygame.SRCALPHA)
            sep_s.fill((255, 255, 255, 30))
            surface.blit(sep_s, (rect.x + 20, sep_y))

            # --- NEW: Bet Selection (Only for Casino Classic index 0) ---
            if i == 0:
                self.bet_rects = []
                bw, bh = 60, 24
                total_bw = len(self.bet_values) * bw + (len(self.bet_values)-1) * 8
                sx = rect.centerx - total_bw // 2
                sy = sep_y - 45 # Positioned between icon and separator
                
                for b_idx, val in enumerate(self.bet_values):
                    b_rect = pygame.Rect(sx + b_idx * (bw + 8), sy, bw, bh)
                    self.bet_rects.append(b_rect)
                    is_sel = (self.selected_bet_idx == b_idx)
                    
                    # Button Body
                    bc = (255, 215, 50, 220) if is_sel else (40, 45, 60, 180)
                    if not is_sel and b_rect.collidepoint(pygame.mouse.get_pos()):
                        bc = (255, 230, 120, 140)
                    
                    pygame.draw.rect(surface, bc, b_rect, border_radius=12)
                    if is_sel:
                        # Glow for selected
                        glow = pygame.Surface((bw+8, bh+8), pygame.SRCALPHA)
                        pygame.draw.rect(glow, (255, 215, 50, 40), (0, 0, bw+8, bh+8), border_radius=15)
                        surface.blit(glow, (b_rect.x-4, b_rect.y-4))

                    # Text
                    tc = (20, 15, 0) if is_sel else (220, 220, 230)
                    v_txt = self.font_micro.render(str(val), True, tc)
                    surface.blit(v_txt, (b_rect.centerx - v_txt.get_width()//2, b_rect.centery - v_txt.get_height()//2))
            
            # Text Design
            name_color = (255, 255, 255) if active else (150, 150, 160)
            n_txt = self.font_body.render(m_name, True, name_color)
            surface.blit(n_txt, (rect.centerx - n_txt.get_width()//2, sep_y + 12))
            
            sub_txt = self.font_micro.render(m_sub, True, (180, 180, 200) if active else (110, 110, 120))
            surface.blit(sub_txt, (rect.centerx - sub_txt.get_width()//2, sep_y + 40))
            
            if not active:
                l_rect = pygame.Rect(rect.centerx - 50, rect.centery - 13, 100, 26)
                pygame.draw.rect(surface, (15, 12, 25, 200), l_rect, border_radius=13)
                pygame.draw.rect(surface, (100, 100, 120, 180), l_rect, width=1, border_radius=13)
                l_txt = self.font_micro.render("COMING SOON", True, (180, 180, 200))
                surface.blit(l_txt, (l_rect.centerx - l_txt.get_width()//2, l_rect.centery - l_txt.get_height()//2))

        # 4. Vignette & Footer
        surface.blit(self.vignette_surf, (0, 0))
        surface.blit(self.footer_surf, (0, self.h - 80))

        # Footer Profile Section
        ax, ay = 30, self.h - 65
        
        # Profile frame (static, no rotation)
        fx, fy = ax - 14, ay - 10
        surface.blit(self.frame_surf, (fx, fy))

        # Avatar glow pulse
        av_glow_a = int(25 + 15 * math.sin(self.time_acc * 3))
        pygame.draw.circle(surface, (255, 215, 100, av_glow_a), (fx + 40, fy + 40), 38)
        
        # Avatar inside the frame
        if avatar:
            surface.blit(self._get_masked_avatar(avatar), (fx + 14, fy + 14))
        else:
            pygame.draw.circle(surface, (60, 70, 90), (fx + 40, fy + 40), 26)

        # Player name and stats  
        text_x = fx + 90
        p_txt = self.font_body.render(name.upper(), True, (255, 255, 255))
        surface.blit(p_txt, (text_x, ay - 2))

        # Win/loss with cleaner formatting
        wins_surf = self.font_micro.render(f"W {stats['wins']}", True, (100, 255, 130))
        losses_surf = self.font_micro.render(f"L {stats['losses']}", True, (255, 120, 100))
        divider_surf = self.font_micro.render(" | ", True, (100, 100, 120))
        surface.blit(wins_surf, (text_x, ay + 26))
        surface.blit(divider_surf, (text_x + wins_surf.get_width(), ay + 26))
        surface.blit(losses_surf, (text_x + wins_surf.get_width() + divider_surf.get_width(), ay + 26))
