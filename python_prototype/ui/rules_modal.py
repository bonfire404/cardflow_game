import pygame
from ui.ui_components import Colors, blur_surface
import math
import time

class RulesModal:
    def __init__(self, font_title, font_body, font_small):
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = font_small
        
        self.active = False
        self._target_active = False
        self.rect = pygame.Rect(0, 0, 800, 550)
        self.close_btn = pygame.Rect(0, 0, 40, 40)
        
        self.alpha = 0
        self._blurred_bg = None
        self.scroll_y = 0
        self.max_scroll = 500 # Will be calc'd
        
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
        else:
            self._target_active = False
            
    def on_resize(self, width, height):
        self.rect.center = (width // 2, height // 2)
        self._blurred_bg = None
        
    def handle_scroll(self, scroll_amt):
        if not self.active: return
        self.scroll_y = max(0, min(self.scroll_y - scroll_amt * 25, self.max_scroll))
        
    def update(self, dt):
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
        
        # 2. Glassmorphic Main Frame with scaling
        scale = 0.9 + 0.1 * ease
        modal_w, modal_h = int(self.rect.w * scale), int(self.rect.h * scale)
        modal_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        
        # Draw into modal_surf
        pygame.draw.rect(modal_surf, (15, 20, 35, 245), (0, 0, self.rect.w, self.rect.h), border_radius=25)
        pygame.draw.rect(modal_surf, Colors.TEXT_GOLD, (0, 0, self.rect.w, self.rect.h), width=3, border_radius=25)
        
        # Title
        title_surf = self.font_title.render("GAME MANUAL", True, Colors.TEXT_GOLD)
        modal_surf.blit(title_surf, (self.rect.width//2 - title_surf.get_width()//2, 30))
        
        # Render Tabs
        tab_start_x = 50
        for i, tab in enumerate(self.tabs):
            tab_rect = pygame.Rect(tab_start_x + i * 200, 90, 180, 40)
            
            color = (255, 255, 255) if tab == self.active_tab else (150, 150, 160)
            if tab == self.active_tab:
                pygame.draw.rect(modal_surf, (255, 215, 0, 40), tab_rect, border_radius=10)
                pygame.draw.rect(modal_surf, Colors.TEXT_GOLD, tab_rect, width=2, border_radius=10)
            
            t_surf = self.font_small.render(tab, True, color)
            modal_surf.blit(t_surf, (tab_rect.centerx - t_surf.get_width()//2, tab_rect.centery - t_surf.get_height()//2))

        # Content Area
        content_rect = pygame.Rect(40, 150, self.rect.width - 80, 360)
        # Deep opaque background for perfect reading
        pygame.draw.rect(modal_surf, (10, 12, 25, 255), content_rect, border_radius=15)
        
        # 3. Virtual Content Surface for Scrolling
        view_surf = pygame.Surface((content_rect.width - 20, 1000), pygame.SRCALPHA)
        self._draw_detailed_lines(view_surf, current_mode)
        
        clip_rect = pygame.Rect(0, self.scroll_y, content_rect.width - 20, content_rect.height - 20)
        modal_surf.blit(view_surf, (content_rect.x + 10, content_rect.y + 10), area=clip_rect)
        
        # Gold frame on top of content
        pygame.draw.rect(modal_surf, (255, 215, 0, 40), content_rect, width=2, border_radius=15)
        
        # Scroll Indicator 
        if self.max_scroll > 0:
            scroll_p = self.scroll_y / self.max_scroll
            sh = 40
            sy = content_rect.y + 10 + (content_rect.height - 20 - sh) * scroll_p
            pygame.draw.rect(modal_surf, Colors.TEXT_GOLD, (content_rect.right - 8, sy, 4, sh), border_radius=2)

        screen.blit(modal_surf, self.rect.topleft)

        # Close Button (Drawn ABSOLUTELY LAST on top layer)
        self.close_btn.center = (self.rect.right - 25, self.rect.top + 25)
        pygame.draw.circle(screen, (255, 30, 30), self.close_btn.center, 22)
        pygame.draw.circle(screen, (255, 255, 255), self.close_btn.center, 22, width=3)
        
        x_font = pygame.font.SysFont("Arial", 24, bold=True)
        sh_cross = x_font.render("X", True, (0, 0, 0, 150))
        screen.blit(sh_cross, (self.close_btn.centerx - sh_cross.get_width()//2 + 2, self.close_btn.centery - sh_cross.get_height()//2 + 2))
        cross = x_font.render("X", True, (255, 255, 255))
        screen.blit(cross, (self.close_btn.centerx - cross.get_width()//2, self.close_btn.centery - cross.get_height()//2))

    def _draw_detailed_lines(self, surf, mode):
        cx, cy = 10, 5 # Relative to view_surf
        line_h = 28
        
        if self.active_tab == "HOW TO PLAY":
            lines = [
                ("THE BASICS", Colors.TEXT_GOLD),
                ("• Everyone starts with 12 cards (Dealer gets 13).", (255, 255, 255)),
                ("• Create MELDS to reduce your hand points.", (255, 255, 255)),
                ("", (0,0,0)),
                ("MELD TYPES", Colors.TEXT_GOLD),
                ("• THREE-OF-A-KIND: 3 cards of the same rank (e.g. 7-7-7).", (220, 220, 220)),
                ("• STRAIGHT FLUSH: 3+ cards of same suit in sequence (e.g. 4-5-6 of Hearts).", (220, 220, 220)),
                ("• SAPAW (SAGASA): Add your cards to existing melds on the table.", (0, 255, 150)),
                ("", (0,0,0)),
                ("TURNS & DRAWING", Colors.TEXT_GOLD),
                ("• DRAW: Take from the DECK or the DISCARD (if you can meld it immediately).", (255, 255, 255)),
                ("• DUMP: Throw 1 card away to end your turn.", (255, 255, 255)),
                ("", (0,0,0)),
                ("WINNING", Colors.TEXT_GOLD),
                ("• TONG-ITS: Empty all cards instantly. Total victory!", (0, 255, 150)),
                ("• FIGHT: If you think your points are lowest, challenge everyone.", (255, 255, 255)),
                ("• DRAW: Deck runs out; lowest hand points on table win.", (220, 220, 220)),
            ]
        elif self.active_tab == "ECONOMY MODES":
            from game.betting_configs import EconomyMode
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
                    ("• BOUNTY BAN: Being burned bans you from winning the pot for 2 games.", (255, 100, 100)),
                    ("• HOUSE RULES: No cash penalty for burn (staying in the game).", (0, 255, 150)),
                    ("• COLD STREAK: Failed fights in 600 mode ban you for 1 game.", (220, 220, 220)),
                ]
        else: # SCORING & FIGHTING
            lines = [
                ("POINT VALUES", Colors.TEXT_GOLD),
                ("• ACES: 1 Point", (255, 255, 255)),
                ("• 2-9: Cards represent their Face Value.", (255, 255, 255)),
                ("• 10, JACK, QUEEN, KING: 10 Points Each.", (255, 255, 255)),
                ("", (0,0,0)),
                ("CALLING A FIGHT", Colors.TEXT_GOLD),
                ("• You can call a FIGHT if you think you have lowest points.", (255, 255, 255)),
                ("• RULE: Cannot Fight on turn 1, or if a Sapaw was just done to your meld.", (255, 100, 100)),
                ("• DRAW: Highest point holder when deck is empty must pay winner.", (220, 220, 220)),
                ("", (0,0,0)),
                ("BEING 'BURNED'", Colors.TEXT_GOLD),
                ("• If you have NO MELDS on the table when someone wins: BURNED.", (255, 100, 100)),
                ("• Burned players pay the penalty and can't collect pots.", (255, 100, 100)),
                ("", (0,0,0)),
                ("STRATEGY TIP", Colors.TEXT_GOLD),
                ("• Group your cards into potential Sets early to avoid burning.", (0, 255, 150)),
                ("• Don't call a fight if a bot has a very small hand!", (220, 220, 220)),
            ]

        self.max_scroll = max(0, len(lines) * line_h - 340)

        for i, (text, color) in enumerate(lines):
            if text == "": continue
            f = self.font_body if text.isupper() else self.font_small
            s = f.render(text, True, color)
            surf.blit(s, (cx, cy + i * line_h))

        for i, (text, color) in enumerate(lines):
            if text == "": continue
            f = self.font_body if text.isupper() else self.font_small
            s = f.render(text, True, color)
            surf.blit(s, (cx, cy + i * line_h))

    def handle_click(self, pos, width, height):
        if not self.active: return False
        
        # Relative pos
        rx, ry = pos[0] - self.rect.x, pos[1] - self.rect.y
        
        # Check close button
        if self.close_btn.collidepoint(pos):
            self.active = False
            return True
        
        # Check tabs
        tab_start_x = 50
        for i, tab in enumerate(self.tabs):
            tab_rect = pygame.Rect(tab_start_x + i * 200, 90, 180, 40)
            if tab_rect.collidepoint(rx, ry):
                self.active_tab = tab
                return True
                
        # Block clicks to game items underneath
        if self.rect.collidepoint(pos):
            return True
            
        return False
