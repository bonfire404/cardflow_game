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
        view_surf = pygame.Surface((content_rect.width - 20, 1200), pygame.SRCALPHA)
        
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
                ("• The Dealer (Banker) takes the first turn.", (255, 255, 255)),
                ("• Create MELDS to reduce your hand points.", (255, 255, 255)),
                ("• The goal is to have the lowest points or empty your hand.", (220, 220, 220)),
                ("", (0,0,0)),
                ("MELD TYPES", Colors.TEXT_GOLD),
                ("• SET: 3 or 4 cards of the same rank (e.g. 7♥ 7♦ 7♣).", (220, 220, 220)),
                ("• RUN (Straight): 3+ cards of same suit in sequence", (220, 220, 220)),
                ("  (e.g. 4♥ 5♥ 6♥). Ace is LOW only (A-2-3, not Q-K-A).", (220, 220, 220)),
                ("• SAPAW: Add your card to an existing meld on the table.", (0, 255, 150)),
                ("", (0,0,0)),
                ("TURNS & ACTIONS", Colors.TEXT_GOLD),
                ("• DRAW: Take the top card from the DECK (closed pile).", (255, 255, 255)),
                ("• CHOW: Take the top DISCARD pile card. You MUST", (255, 255, 255)),
                ("  immediately meld it before you can discard.", (255, 200, 100)),
                ("• DROP: Lay down a valid meld from your hand.", (220, 220, 220)),
                ("• DISCARD: Throw 1 card to end your turn.", (255, 255, 255)),
                ("", (0,0,0)),
                ("IMPORTANT RULES", Colors.TEXT_GOLD),
                ("• BURN: If you have ZERO melds exposed when a FIGHT", (255, 100, 100)),
                ("  is called or the deck runs out, you are BURNED and", (255, 100, 100)),
                ("  lose automatically!", (255, 100, 100)),
                ("• SAPAW BLOCK: If someone sapaws on YOUR meld,", (255, 200, 100)),
                ("  you CANNOT call a fight until your next turn.", (255, 200, 100)),
                ("• FIGHT TIMING: You can only call a fight BEFORE", (255, 200, 100)),
                ("  drawing a card on your turn.", (255, 200, 100)),
                ("• Dropping a new meld clears the sapaw restriction.", (200, 200, 220)),
            ]
        elif self.active_tab == "ECONOMY MODES":
            lines = [
                ("CURRENT TABLE: " + mode.value.upper(), Colors.TEXT_GOLD),
                ("", (0,0,0)),
            ]
            if mode == EconomyMode.HITTER:
                lines += [
                    ("HITTER'S BOUNTY (100 Table)", (255, 215, 0)),
                    ("• ENTRY: 100 coins each. Dealer adds 200 bounty.", (255, 255, 255)),
                    ("• MAIN POT: All entry fees (300 total). Winner takes all.", (255, 255, 255)),
                    ("• BANKER POT: Dealer's 200 bounty accumulates here.", (220, 220, 220)),
                    ("• HITTER BONUS: Win 2x in a row as Dealer to claim", (255, 215, 0)),
                    ("  the entire Banker Pot!", (255, 215, 0)),
                    ("• BURN PENALTY: 100 coins deducted if burned.", (255, 100, 100)),
                    ("• TIES: Challenger wins over the caller in a tie.", (200, 200, 220)),
                ]
            elif mode == EconomyMode.AGGRESSIVE:
                lines += [
                    ("AGGRESSIVE CASINO (300 Table)", (255, 215, 0)),
                    ("• ENTRY: 300 coins each. Dealer adds 600 bounty.", (255, 255, 255)),
                    ("• MAIN POT: All entry fees (900 total). Winner takes all.", (255, 255, 255)),
                    ("• TONG-ITS JACKPOT: Winner takes full Banker Pot", (0, 255, 150)),
                    ("  + 100 coin jackpot fee from each loser.", (0, 255, 150)),
                    ("• HOUSE EDGE: Dealer wins ALL ties in Fights or Draws.", (255, 215, 0)),
                    ("• BURN PENALTY: 300 coins if burned.", (255, 100, 100)),
                    ("• FAILED FIGHT: Caller loses 600 coins if they lose.", (255, 100, 100)),
                ]
            elif mode == EconomyMode.SUSTAINED:
                lines += [
                    ("SUSTAINED ECONOMY (600 Table)", (255, 215, 0)),
                    ("• ENTRY: 600 coins each. Dealer adds 200 fee.", (255, 255, 255)),
                    ("• MAIN POT: All entry fees (1800 total).", (255, 255, 255)),
                    ("• FIGHT WIN: Winner takes 80% of pot. 20% stays", (255, 255, 255)),
                    ("  in the Banker Pot for next round.", (220, 220, 220)),
                    ("• TONG-ITS: Winner takes 100% of pot + full Banker Pot.", (255, 215, 0)),
                    ("• ACCUMULATION: Banker Pot grows each round until", (0, 255, 150)),
                    ("  someone hits a Tong-its and claims it all!", (0, 255, 150)),
                    ("• NO BURN PENALTY: Burns don't cost extra coins.", (200, 200, 220)),
                    ("• BOUNTY BAN: Burned players can't win the Banker", (255, 100, 100)),
                    ("  Pot for the next 2 rounds.", (255, 100, 100)),
                ]
            else:
                # HIGH STAKES / VIP / LEGENDARY (Rank modes)
                mode_name = mode.value.upper()
                lines += [
                    (f"{mode_name} (Ranked)", (255, 215, 0)),
                    ("• Same rules as Sustained Economy.", (255, 255, 255)),
                    ("• ENTRY: Varies by table (1k / 5k / 10k).", (255, 255, 255)),
                    ("• FIGHT WIN: 80% pot to winner, 20% stays.", (220, 220, 220)),
                    ("• TONG-ITS: Full pot + full Banker Pot to winner.", (255, 215, 0)),
                    ("• BOUNTY BAN: Burned = banned from Banker Pot 2 rounds.", (255, 100, 100)),
                    ("• LEAVER PENALTY: Quitting mid-match costs XP and RP.", (255, 100, 100)),
                    ("", (0,0,0)),
                    ("RANKED REQUIREMENTS", Colors.TEXT_GOLD),
                    ("• 1,000 Table: Level 10+", (200, 200, 220)),
                    ("• 5,000 Table: Level 30+", (200, 200, 220)),
                    ("• 10,000 Table: Level 50+", (200, 200, 220)),
                ]
        else: # SCORING & FIGHTING
            lines = [
                ("CARD VALUES (Points)", Colors.TEXT_GOLD),
                ("• Ace: 1 point", (255, 255, 255)),
                ("• 2 through 9: Face value (2-9 points)", (255, 255, 255)),
                ("• 10, Jack, Queen, King: 10 points each", (255, 255, 255)),
                ("• Cards in exposed melds count as 0 points.", (0, 255, 150)),
                ("• Cards in your HAND that form valid melds are also", (0, 255, 150)),
                ("  counted as 0 points when calculating your score.", (0, 255, 150)),
                ("", (0,0,0)),
                ("CALLING A FIGHT", Colors.TEXT_GOLD),
                ("• You can call FIGHT at the start of your turn,", (255, 255, 255)),
                ("  BEFORE drawing a card.", (255, 200, 100)),
                ("• You MUST have at least 1 exposed meld on the table.", (255, 255, 255)),
                ("• You CANNOT fight if someone sapawed on your melds", (220, 220, 220)),
                ("  this round (until you drop a new meld).", (220, 220, 220)),
                ("• Other players choose to FIGHT (challenge) or FOLD.", (220, 220, 220)),
                ("• Players with NO melds are automatically BURNED.", (255, 100, 100)),
                ("", (0,0,0)),
                ("FIGHT RESOLUTION", Colors.TEXT_GOLD),
                ("• Lowest hand points wins among eligible players.", (255, 255, 255)),
                ("• TIE-BREAKER: Challenger wins over the caller.", (255, 200, 100)),
                ("• HOUSE EDGE (Aggressive mode only): Dealer wins ties.", (255, 200, 100)),
                ("", (0,0,0)),
                ("WINNING CONDITIONS", Colors.TEXT_GOLD),
                ("• TONG-ITS: Empty your entire hand. Instant win!", (0, 255, 150)),
                ("• FIGHT: Lowest points when someone calls a fight.", (255, 255, 255)),
                ("• DRAW: Deck runs out — lowest points wins.", (220, 220, 220)),
                ("• SPREAD: All dealt cards form valid melds. Instant win!", (0, 255, 150)),
                ("  (Extremely rare)", (150, 150, 170)),
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
