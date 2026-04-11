import pygame
import random
import math
from .ui_components import Colors

class Lobby:
    def __init__(self, w, h, f_title, f_body):
        self.w, self.h = w, h
        self.font_title = f_title
        self.font_body = f_body
        self.font_small = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_micro = pygame.font.SysFont("Arial", 12, bold=True)
        self.time_acc = 0.0
        
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
        
        self.frame_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(self.frame_surf, (140, 110, 30), (50, 50), 32)
        pygame.draw.circle(self.frame_surf, (255, 215, 100), (50, 50), 30)
        pygame.draw.circle(self.frame_surf, (40, 35, 20), (50, 50), 27)
        
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
        except: self.coin_frame = None
        
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

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self.banner_rects):
                if r.collidepoint(event.pos) and self.modes[i][3]:
                    return i
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
            surface.blit(self.overlay_surf, (0, 0))
        else: surface.fill((20, 10, 0))

        # 2. Header
        surface.blit(self.header_surf, (0, 0))
        if self.coin_frame:
            cx, cy = 25, 0
            surface.blit(self.coin_frame, (cx, cy))
            balance_str = f"{stats['coins']:,}"
            pulse = int(200 + 55 * math.sin(self.time_acc * 5))
            glow_color = (max(0, min(255, 255 * (pulse/255))), max(0, min(255, 200 * (pulse/255))), 50)
            glow_txt = self.font_body.render(balance_str, True, glow_color)
            surface.blit(glow_txt, (cx + 150 - glow_txt.get_width() // 2, cy + 28))

        title_txt = self.font_title.render("MAMA'S GO", True, (255, 225, 150))
        surface.blit(title_txt, (self.w // 2 - title_txt.get_width() // 2, 15))

        # 3. Central Modes
        for i, (m_name, m_sub, m_color, active) in enumerate(self.modes):
            rect = self.banner_rects[i].copy()
            is_hover = (self.hover_idx == i and active)
            float_y = 10 * math.sin(self.time_acc * 2.5 + i * 0.7)
            rect.y += float_y
            if is_hover:
                rect.inflate_ip(14, 14)
                rect.y -= 10
            
            # Glassmorphism Body
            b_alpha = 180 if is_hover else 120
            b_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(b_surf, (20, 25, 45, b_alpha), (0, 0, rect.w, rect.h), border_radius=28)
            surface.blit(b_surf, rect.topleft)
            
            # Border
            border_color = (255, 215, 0, 200) if is_hover else (*m_color, 120) if active else (80, 80, 90, 80)
            pygame.draw.rect(surface, border_color, rect, width=2 if is_hover else 1, border_radius=28)

            icon_y = rect.y + 110
            if i < len(self.icons) and self.icons[i]:
                icon_img = self.icons[i]
                if is_hover: 
                    icon_img = pygame.transform.smoothscale(icon_img, (155, 155))
                    surface.blit(icon_img, (rect.centerx - 77, icon_y - 77))
                else: 
                    surface.blit(icon_img, (rect.centerx - 70, icon_y - 70))
            
            # Text
            name_color = (255, 255, 255) if active else (130, 130, 140)
            n_txt = self.font_body.render(m_name, True, name_color)
            surface.blit(n_txt, (rect.centerx - n_txt.get_width()//2, rect.bottom - 90))
            
            if not active:
                l_rect = pygame.Rect(rect.centerx - 45, rect.bottom - 135, 90, 24)
                pygame.draw.rect(surface, (40, 30, 20), l_rect, border_radius=12)
                l_txt = self.font_micro.render("COMING SOON", True, (160, 140, 120))
                surface.blit(l_txt, (l_rect.centerx - l_txt.get_width()//2, l_rect.centery - l_txt.get_height()//2))

        # 4. Vignette & Footer
        surface.blit(self.vignette_surf, (0, 0))
        surface.blit(self.footer_surf, (0, self.h - 80))

        # Footer Profile
        ax, ay = 25, self.h - 68
        surface.blit(self.frame_surf, (ax - 25, ay - 22))
        
        if avatar:
            surface.blit(self._get_masked_avatar(avatar), (ax - 1, ay + 2))
        else:
            pygame.draw.circle(surface, (60, 70, 90), (ax + 25, ay + 28), 26)

        # Dynamic Shine (Lightweight)
        angle = self.time_acc * 3.5
        sx = ax + 25 + 30 * math.cos(angle)
        sy = ay + 28 + 30 * math.sin(angle)
        surface.blit(self.shine_dot, (sx - 5, sy - 5))

        p_txt = self.font_body.render(name, True, (255, 255, 255))
        surface.blit(p_txt, (ax + 70, ay + 2))
        st_txt = self.font_micro.render(f"WINS: {stats['wins']}  LOSSES: {stats['losses']}", True, (200, 200, 220))
        surface.blit(st_txt, (ax + 70, ay + 28))
