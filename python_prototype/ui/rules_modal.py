import pygame
from ui.ui_components import Colors, blur_surface
from game.betting_configs import EconomyMode
import math
import time
import os
from ui.paths import get_resource_path

class RulesModal:
    def __init__(self, font_title, font_body, font_small):
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = font_small
        
        self.active = False
        self._target_active = False
        self.rect = pygame.Rect(0, 0, 800, 600) # Matching ProfileModal width/height style
        self.close_btn = pygame.Rect(0, 0, 30, 30)
        
        self.alpha = 0
        self._blurred_bg = None
        self.scroll_y = 0
        self.max_scroll = 500 # Will be calc'd
        self.time_alive = 0.0
        
        # Load Sekuya for modal title
        _sekuya_path = get_resource_path(os.path.join("assets", "fonts", "Sekuya", "Sekuya-Regular.ttf"))
        try:
            self.font_modal_title = pygame.font.Font(_sekuya_path, 34)
        except:
            self.font_modal_title = self.font_title
            
        # Load Close Icon
        try:
            cross_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "cross.png"))
            self.icon_close = pygame.image.load(cross_path).convert_alpha()
            self.icon_close = pygame.transform.smoothscale(self.icon_close, (16, 16))
        except:
            self.icon_close = None
        
        # Tabs
        self.tabs = ["HOW TO PLAY", "ECONOMY MODES", "SCORING & FIGHTING"]
        self.active_tab = "HOW TO PLAY"
        
    def toggle(self):
        if not self.active:
            self.active = True
            self._target_active = True
            self.alpha = 0
            self._blurred_bg = None
            self.scroll_y = 0
            self.time_alive = 0.0
        else:
            self._target_active = False
            
    def on_resize(self, width, height):
        self.rect.center = (width // 2, height // 2)
        self._blurred_bg = None
        
    def handle_scroll(self, scroll_amt):
        if not self.active: return
        self.scroll_y = max(0, min(self.scroll_y - scroll_amt * 25, self.max_scroll))
        
    def update(self, dt):
        if not self.active: return
        self.time_alive += dt
        speed = 10.0
        if self._target_active:
            self.alpha = min(255, self.alpha + speed * 60 * dt)
        else:
            self.alpha = max(0, self.alpha - speed * 80 * dt)
            if self.alpha <= 0:
                self.active = False
                
    def draw(self, screen, width, height, current_mode):
        if not self.active: return
        
        # 1. Capture and Blur Backdrop once
        if self._blurred_bg is None:
            self._blurred_bg = blur_surface(screen.copy(), factor=6, tint=(10, 8, 20), tint_alpha=180)

        # Alpha Fade
        ease = min(self.alpha / 255.0, 1.0)
        blur_alpha = int(255 * ease)
        if blur_alpha >= 250:
            screen.blit(self._blurred_bg, (0, 0))
        else:
            temp = self._blurred_bg.copy()
            temp.set_alpha(blur_alpha)
            screen.blit(temp, (0, 0))

        self.rect.center = (width // 2, height // 2)
        
        # Bouncing effect on open
        bounce = math.sin(self.time_alive * 6) * max(0, 1.0 - self.time_alive * 3) * 20
        screen_y = self.rect.y + int(bounce)
        
        # 2. Modal Surface with ProfileModal design
        modal_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        
        # Gradient background (Matching ProfileModal)
        for row in range(self.rect.h):
            t = row / self.rect.h
            r = int(15 + 15 * t)
            g = int(18 + 12 * t)
            b = int(35 + 20 * t)
            a = 245
            pygame.draw.line(modal_surf, (r, g, b, a), (0, row), (self.rect.w, row))

        # Round mask (Matching ProfileModal radius 28)
        mask = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, self.rect.w, self.rect.h), border_radius=28)
        modal_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # Border (Matching ProfileModal color and width)
        pygame.draw.rect(modal_surf, (218, 175, 50, 120), (0, 0, self.rect.w, self.rect.h), width=2, border_radius=28)
        
        # Header
        title_surf = self.font_modal_title.render("GAME MANUAL", True, Colors.TEXT_GOLD)
        modal_surf.blit(title_surf, (self.rect.w // 2 - title_surf.get_width() // 2, 20))
        pygame.draw.line(modal_surf, (255, 255, 255, 20), (25, 65), (self.rect.w - 25, 65), 1)
        
        # Render Tabs
        tab_start_x = 50
        for i, tab in enumerate(self.tabs):
            tab_rect = pygame.Rect(tab_start_x + i * 230, 80, 210, 40)
            
            color = (255, 255, 255) if tab == self.active_tab else (150, 150, 160)
            if tab == self.active_tab:
                pygame.draw.rect(modal_surf, (218, 175, 50, 40), tab_rect, border_radius=10)
                pygame.draw.rect(modal_surf, Colors.TEXT_GOLD, tab_rect, width=2, border_radius=10)
            else:
                pygame.draw.rect(modal_surf, (255, 255, 255, 10), tab_rect, border_radius=10)
            
            t_surf = self.font_small.render(tab, True, color)
            modal_surf.blit(t_surf, (tab_rect.centerx - t_surf.get_width()//2, tab_rect.centery - t_surf.get_height()//2))

        # Content Area
        content_rect = pygame.Rect(40, 140, self.rect.width - 80, 420)
        # Deep opaque background for perfect reading
        pygame.draw.rect(modal_surf, (10, 12, 25, 230), content_rect, border_radius=15)
        pygame.draw.rect(modal_surf, (218, 175, 50, 40), content_rect, width=1, border_radius=15)
        
        # Virtual Content Surface for Scrolling
        view_surf = pygame.Surface((content_rect.width - 20, 1000), pygame.SRCALPHA)
        
        # Handle integer mode mapping
        if isinstance(current_mode, int):
            mapping = {0: EconomyMode.HITTER, 1: EconomyMode.AGGRESSIVE, 2: EconomyMode.SUSTAINED}
            current_mode = mapping.get(current_mode, EconomyMode.HITTER)

        self._draw_detailed_lines(view_surf, current_mode)
        
        clip_rect = pygame.Rect(0, self.scroll_y, content_rect.width - 20, content_rect.height - 20)
        modal_surf.blit(view_surf, (content_rect.x + 10, content_rect.y + 10), area=clip_rect)
        
        # Scroll Indicator 
        if self.max_scroll > 0:
            scroll_p = self.scroll_y / self.max_scroll
            sh = 40
            sy = content_rect.y + 10 + (content_rect.height - 20 - sh) * scroll_p
            pygame.draw.rect(modal_surf, Colors.TEXT_GOLD, (content_rect.right - 8, sy, 4, sh), border_radius=2)

        # Close Button
        self.close_btn.topright = (self.rect.w - 20, 20)
        close_color = (220, 50, 50) if self.close_btn.collidepoint(pygame.mouse.get_pos()[0] - self.rect.x, pygame.mouse.get_pos()[1] - screen_y) else (180, 40, 40)
        pygame.draw.circle(modal_surf, close_color, self.close_btn.center, 15)
        if self.icon_close:
            modal_surf.blit(self.icon_close, (self.close_btn.centerx - 8, self.close_btn.centery - 8))

        # Blit modal to screen
        screen.blit(modal_surf, (self.rect.x, screen_y))

    def _draw_detailed_lines(self, surf, mode):
        cx, cy = 10, 5 # Relative to view_surf
        line_h = 28
        
        if self.active_tab == "HOW TO PLAY":
            lines = [
                ("THE BASICS", Colors.TEXT_GOLD),
                ("• Everyone starts with 12 cards (Dealer gets 13).", (255, 255, 255)),
                ("• Create MELDS to reduce your hand points.", (255, 255, 255)),
                ("• The goal is to have the lowest points or empty your hand.", (220, 220, 220)),
                ("", (0,0,0)),
                ("MELD TYPES", Colors.TEXT_GOLD),
                ("• THREE-OF-A-KIND: 3 cards of the same rank (e.g. 7-7-7).", (220, 220, 220)),
                ("• FOUR-OF-A-KIND: 4 cards of the same rank.", (220, 220, 220)),
                ("• STRAIGHT FLUSH: 3+ cards of same suit in sequence (e.g. 4-5-6 of Hearts).", (220, 220, 220)),
                ("• SAPAW (SAGASA): Add your cards to existing melds on the table.", (0, 255, 150)),
                ("", (0,0,0)),
                ("TURNS & ACTIONS", Colors.TEXT_GOLD),
                ("• DRAW: Take the top card from the DECK.", (255, 255, 255)),
                ("• CHOW: Take the DISCARDED card if it forms a meld with your hand.", (255, 255, 255)),
                ("• DROP: Lay down a meld on the table to reduce your points.", (220, 220, 220)),
                ("• DUMP: Throw 1 card away to end your turn.", (255, 255, 255)),
                ("", (0,0,0)),
                ("SPECIAL RULES", Colors.TEXT_GOLD),
                ("• BURN: If you have ZERO melds exposed when a fight is called", (255, 100, 100)),
                ("  or the deck runs out, you are BURNED and lose automatically!", (255, 100, 100)),
            ]
        elif self.active_tab == "ECONOMY MODES":
            lines = [
                ("TABLE RULES: " + mode.value.upper(), Colors.TEXT_GOLD),
                ("", (0,0,0)),
            ]
            if mode == EconomyMode.HITTER:
                lines += [
                    ("• ENTRY FEE: 100 coins ante + 200 for the Dealer.", (255, 255, 255)),
                    ("• THE BANKER POT: Everyone's extra bets go here.", (255, 255, 255)),
                    ("• WIN THE BOUNTY: You MUST win twice in a row as Dealer (Hitter).", (255, 215, 0)),
                    ("• BURN PENALTY: 100 coins lost if you have ZERO melds at end.", (255, 100, 100)),
                    ("• PROFIT: Main Pot is won by any regular winner.", (220, 220, 220)),
                ]
            elif mode == EconomyMode.AGGRESSIVE:
                lines += [
                    ("• ENTRY FEE: 300 coins for all + 300 for the Dealer.", (255, 255, 255)),
                    ("• TONG-ITS JACKPOT: Takes 100% of the Pot + 100 extra from all.", (0, 255, 150)),
                    ("• BANKER ADVANTAGE: Dealer wins all ties in Fights or Draws.", (255, 215, 0)),
                    ("• PENALTIES: Burn: 300 / Failed Fight Challenge: 600.", (255, 100, 100)),
                    ("• AGGRESSIVE: Stakes double every few rounds.", (220, 220, 240)),
                ]
            else: # SUSTAINED
                lines += [
                    ("• ENTRY FEE: 600 coins. Dealer adds 200 fee.", (255, 255, 255)),
                    ("• SUSTAINED STAKES: Winner takes 80% of pot, 20% stays for next round.", (255, 255, 255)),
                    ("• ACCUMULATION: The retained pot grows until a Tong-its is hit.", (255, 215, 0)),
                    ("• STRICT WINNING: Fights only allowed if you melded this turn.", (255, 100, 100)),
                    ("• ENDURANCE: High risk, massive long-term payouts.", (220, 220, 220)),
                ]
        else: # SCORING & FIGHTING
            lines = [
                ("CARD VALUES", Colors.TEXT_GOLD),
                ("• Aces: 1 point", (255, 255, 255)),
                ("• Numbered Cards (2-10): Face value", (255, 255, 255)),
                ("• Jacks, Queens, Kings: 10 points each", (255, 255, 255)),
                ("• Melded cards count as ZERO points.", (0, 255, 150)),
                ("", (0,0,0)),
                ("CHALLENGING (FIGHT)", Colors.TEXT_GOLD),
                ("• Click FIGHT on your turn if you have low points.", (255, 255, 255)),
                ("• You can only fight if you have exposed at least one meld.", (220, 220, 220)),
                ("• If someone challenges and has LOWER points, you lose double!", (255, 100, 100)),
                ("", (0,0,0)),
                ("WINNING CONDITIONS", Colors.TEXT_GOLD),
                ("• TONG-ITS: Empty all cards in your hand. Instant win!", (0, 255, 150)),
                ("• FIGHT: Lowest points when someone calls a fight.", (255, 255, 255)),
                ("• DRAW: Deck runs out; player with lowest points wins.", (220, 220, 220)),
            ]

        self.max_scroll = max(0, len(lines) * line_h - 380)

        for text, color in lines:
            if text == "":
                cy += line_h // 2
                continue
            txt_surf = self.font_body.render(text, True, color)
            surf.blit(txt_surf, (cx, cy))
            cy += line_h

    def handle_click(self, pos, width, height):
        if not self.active or not self._target_active: return
        
        self.rect.center = (width // 2, height // 2)
        
        # Bouncing effect calculation
        bounce = math.sin(self.time_alive * 6) * max(0, 1.0 - self.time_alive * 3) * 20
        screen_y = self.rect.y + int(bounce)
        
        rel_pos = (pos[0] - self.rect.x, pos[1] - screen_y)
        
        if self.close_btn.collidepoint(rel_pos):
            self._target_active = False
            return
            
        # Check tabs
        tab_start_x = 50
        for i, tab in enumerate(self.tabs):
            tab_rect = pygame.Rect(tab_start_x + i * 230, 80, 210, 40)
            if tab_rect.collidepoint(rel_pos):
                self.active_tab = tab
                self.scroll_y = 0
                return
