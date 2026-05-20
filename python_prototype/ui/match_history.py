import pygame
import math
import os
from ui.ui_components import Colors, blur_surface
from ui.paths import get_resource_path
from ui.database import get_match_history

class MatchHistoryModal:
    """Ultra-premium Match History modal showing the last 10 games with earnings, mode, and outcome."""
    
    def __init__(self, font_title, font_body, font_small):
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = font_small
        
        self.active = False
        self._target_active = False
        self.rect = pygame.Rect(0, 0, 720, 560)  # Standard premium size
        self.alpha = 0
        self._blurred_bg = None
        self.time_alive = 0.0
        
        # Load Sekuya font for title
        _sekuya_path = get_resource_path(os.path.join("assets", "fonts", "Sekuya", "Sekuya-Regular.ttf"))
        try:
            self.font_modal_title = pygame.font.Font(_sekuya_path, 34)
        except:
            self.font_modal_title = self.font_title
            
        # Close Button (X)
        self.close_btn_rect = pygame.Rect(0, 0, 30, 30)
        self.icon_close = None
        try:
            cross_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "cross.png"))
            self.icon_close = pygame.image.load(cross_path).convert_alpha()
            self.icon_close = pygame.transform.smoothscale(self.icon_close, (16, 16))
        except:
            self.icon_close = None
            
        self.history = []

    def open(self):
        self.active = True
        self._target_active = True
        self.alpha = 0
        self.time_alive = 0.0
        self._blurred_bg = None
        # Load from DB
        self.history = get_match_history(limit=10) or []

    def close(self):
        self._target_active = False

    def on_resize(self, w, h):
        self._blurred_bg = None

    def update(self, dt, mouse_pos):
        if not self.active: 
            return
        
        self.time_alive += dt
        speed = 10.0
        if self._target_active:
            self.alpha = min(255, self.alpha + speed * 60 * dt)
        else:
            self.alpha = max(0, self.alpha - speed * 80 * dt)
            if self.alpha <= 0:
                self.active = False

    def draw(self, screen, width, height):
        if not self.active: 
            return
        
        if self._blurred_bg is None:
            self._blurred_bg = blur_surface(screen.copy(), factor=6, tint=(10, 8, 20), tint_alpha=180)

        ease = min(self.alpha / 255.0, 1.0)
        blur_alpha = int(255 * ease)
        if blur_alpha >= 250:
            screen.blit(self._blurred_bg, (0, 0))
        elif blur_alpha > 0:
            temp = self._blurred_bg.copy()
            temp.set_alpha(blur_alpha)
            screen.blit(temp, (0, 0))

        # Center the modal on screen
        self.rect.center = (width // 2, height // 2)
        
        # Soft bounce animation on entry
        bounce = math.sin(self.time_alive * 6) * max(0, 1.0 - self.time_alive * 3) * 20
        screen_y = self.rect.y + int(bounce)
        
        # Modal surface with transparency support
        modal_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        
        # Premium dark gradient backdrop
        for row in range(self.rect.h):
            t = row / self.rect.h
            r = int(15 + 15 * t)
            g = int(18 + 12 * t)
            b = int(35 + 20 * t)
            a = 245
            pygame.draw.line(modal_surf, (r, g, b, a), (0, row), (self.rect.w, row))

        # Round the corners
        mask = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, self.rect.w, self.rect.h), border_radius=28)
        modal_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # Draw gold border
        pygame.draw.rect(modal_surf, (218, 175, 50, 120), (0, 0, self.rect.w, self.rect.h), width=2, border_radius=28)
        
        # Modal Title
        title_surf = self.font_modal_title.render("MATCH HISTORY", True, Colors.TEXT_GOLD)
        modal_surf.blit(title_surf, (self.rect.w // 2 - title_surf.get_width() // 2, 20))
        pygame.draw.line(modal_surf, (255, 255, 255, 20), (25, 65), (self.rect.w - 25, 65), 1)
        
        # Close Button X
        self.close_btn_rect.topright = (self.rect.w - 20, 20)
        mouse_pos = pygame.mouse.get_pos()
        close_hover = self.close_btn_rect.collidepoint(mouse_pos[0] - self.rect.x, mouse_pos[1] - screen_y)
        close_color = (220, 50, 50) if close_hover else (180, 40, 40)
        pygame.draw.circle(modal_surf, close_color, self.close_btn_rect.center, 15)
        if self.icon_close:
            modal_surf.blit(self.icon_close, (self.close_btn_rect.centerx - 8, self.close_btn_rect.centery - 8))

        # Draw history records
        start_y = 85
        row_h = 42
        gap = 4
        
        if not self.history:
            empty_txt = self.font_body.render("No matches played yet.", True, (150, 150, 160))
            modal_surf.blit(empty_txt, (self.rect.w // 2 - empty_txt.get_width() // 2, self.rect.h // 2 - 10))
        else:
            # Draw table header
            hdr_y = start_y
            hdr_font = self.font_small
            hdr_color = (130, 135, 150)
            
            col_x = [35, 195, 355, 470, 560, 650]
            headers = ["DATE & TIME", "MODE", "RESULT", "COINS", "RP", "XP"]
            for idx, name in enumerate(headers):
                lbl = hdr_font.render(name, True, hdr_color)
                # align coins/rp/xp right or center
                if idx >= 3:
                    modal_surf.blit(lbl, (col_x[idx] - lbl.get_width()//2, hdr_y))
                else:
                    modal_surf.blit(lbl, (col_x[idx], hdr_y))
            
            # Header line
            pygame.draw.line(modal_surf, (255, 255, 255, 15), (25, hdr_y + 22), (self.rect.w - 25, hdr_y + 22), 1)
            
            # Draw rows
            for i, record in enumerate(self.history):
                ry = hdr_y + 28 + i * (row_h + gap)
                
                # Alternate row colors
                row_bg = (24, 28, 44, 180) if i % 2 == 0 else (18, 22, 36, 120)
                pygame.draw.rect(modal_surf, row_bg, (25, ry, self.rect.w - 50, row_h), border_radius=8)
                
                # Check outcome colors
                is_win = record.get("result", "LOSE") == "WIN"
                outcome_color = (80, 220, 100) if is_win else (240, 80, 80)
                
                # Columns:
                # 1. Date & Time
                dt_str = record.get("timestamp", "")
                if len(dt_str) > 16:
                    dt_str = dt_str[:16].replace("T", " ") # Nicer format
                date_txt = self.font_small.render(dt_str, True, (200, 200, 210))
                modal_surf.blit(date_txt, (col_x[0] + 5, ry + row_h // 2 - date_txt.get_height() // 2))
                
                # 2. Mode
                mode_txt = self.font_small.render(record.get("mode", "CLASSIC"), True, (218, 175, 50))
                modal_surf.blit(mode_txt, (col_x[1], ry + row_h // 2 - mode_txt.get_height() // 2))
                
                # 3. Result
                res_txt = self.font_small.render(record.get("result", "LOSE"), True, outcome_color)
                modal_surf.blit(res_txt, (col_x[2], ry + row_h // 2 - res_txt.get_height() // 2))
                
                # 4. Coins
                coins_val = record.get("coins_change", 0)
                coins_sign = "+" if coins_val > 0 else ""
                coins_color = (100, 255, 100) if coins_val > 0 else ((255, 100, 100) if coins_val < 0 else (180, 180, 180))
                coins_txt = self.font_small.render(f"{coins_sign}{coins_val}", True, coins_color)
                modal_surf.blit(coins_txt, (col_x[3] - coins_txt.get_width() // 2, ry + row_h // 2 - coins_txt.get_height() // 2))
                
                # 5. RP
                rp_val = record.get("rp_change", 0)
                rp_sign = "+" if rp_val > 0 else ""
                rp_color = (100, 200, 255) if rp_val > 0 else ((255, 100, 100) if rp_val < 0 else (180, 180, 180))
                rp_txt = self.font_small.render(f"{rp_sign}{rp_val}", True, rp_color)
                modal_surf.blit(rp_txt, (col_x[4] - rp_txt.get_width() // 2, ry + row_h // 2 - rp_txt.get_height() // 2))
                
                # 6. XP
                xp_val = record.get("xp_change", 0)
                xp_sign = "+" if xp_val > 0 else ""
                xp_color = (255, 215, 0) if xp_val > 0 else (180, 180, 180)
                xp_txt = self.font_small.render(f"{xp_sign}{xp_val}", True, xp_color)
                modal_surf.blit(xp_txt, (col_x[5] - xp_txt.get_width() // 2, ry + row_h // 2 - xp_txt.get_height() // 2))

        # Blit the compiled modal surface
        screen.blit(modal_surf, (self.rect.x, screen_y))

    def handle_click(self, event):
        if not self.active or not self._target_active: 
            return None
            
        bounce = math.sin(self.time_alive * 6) * max(0, 1.0 - self.time_alive * 3) * 20
        screen_y = self.rect.y + int(bounce)
        
        rel_pos = (event.pos[0] - self.rect.x, event.pos[1] - screen_y)
        
        if self.close_btn_rect.collidepoint(rel_pos):
            self.close()
            return {"type": "close"}
            
        if self.rect.collidepoint(event.pos):
            return {"type": "blocked"}
            
        return None
