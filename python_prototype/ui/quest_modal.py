import pygame
import math
import os
import json
from ui.ui_components import Colors, Button, blur_surface
from ui.paths import get_resource_path, get_save_path

QUEST_FILE = get_save_path("quests.json")

class DailyQuestModal:
    def __init__(self, font_title, font_body, font_small):
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = font_small
        
        self.active = False
        self._target_active = False
        self.rect = pygame.Rect(0, 0, 700, 550) # Matching ProfileModal width, slightly shorter
        self.alpha = 0
        self._blurred_bg = None
        self.time_alive = 0.0
        
        # Load Sekuya for modal title (Matching ProfileModal)
        _sekuya_path = get_resource_path(os.path.join("assets", "fonts", "Sekuya", "Sekuya-Regular.ttf"))
        try:
            self.font_modal_title = pygame.font.Font(_sekuya_path, 34)
        except:
            self.font_modal_title = self.font_title
            
        # Load Quests from file or use defaults
        self.quests = self.load_progress()
        
        # Close Button (X) - Matching ProfileModal style
        self.close_btn_rect = pygame.Rect(0, 0, 30, 30)
        self.icon_close = None
        try:
            cross_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "cross.png"))
            self.icon_close = pygame.image.load(cross_path).convert_alpha()
            self.icon_close = pygame.transform.smoothscale(self.icon_close, (16, 16))
        except:
            self.icon_close = None
            
        # Claim Buttons for each quest
        self.claim_buttons = []
        for i in range(len(self.quests)):
            self.claim_buttons.append(Button(
                0, 0, 100, 35,
                "CLAIM", self.font_small,
                color=Colors.BTN_SUCCESS, hover_color=Colors.BTN_SUCCESS_HOVER,
                border_radius=8
            ))

    def load_progress(self):
        defaults = [
            {"id": 1, "desc": "Win 1 Game", "curr": 0, "goal": 1, "reward": 500, "claimed": False, "type": "win"},
            {"id": 2, "desc": "Play 3 Games", "curr": 0, "goal": 3, "reward": 1000, "claimed": False, "type": "play"},
            {"id": 3, "desc": "Reach 3 Win Streak", "curr": 0, "goal": 3, "reward": 2000, "claimed": False, "type": "streak"}
        ]
        if os.path.exists(QUEST_FILE):
            try:
                with open(QUEST_FILE, "r") as f:
                    return json.load(f)
            except:
                return defaults
        return defaults

    def save_progress(self):
        try:
            with open(QUEST_FILE, "w") as f:
                json.dump(self.quests, f)
        except Exception as e:
            print(f"Error saving quests: {e}")

    def update_quest(self, quest_type, value):
        for quest in self.quests:
            if quest["type"] == quest_type:
                if quest_type == "streak":
                    quest["curr"] += value
                else:
                    quest["curr"] = min(quest["goal"], quest["curr"] + value)
                    
        # Handle streak reset
        if quest_type == "streak_reset":
            for quest in self.quests:
                if quest["type"] == "streak" and not quest["claimed"]:
                    quest["curr"] = 0
                    
        self.save_progress()

    def open(self):
        self.active = True
        self._target_active = True
        self.alpha = 0
        self.time_alive = 0.0
        self._blurred_bg = None
        self.quests = self.load_progress()

    def close(self):
        self._target_active = False

    def update(self, dt, mouse_pos):
        if not self.active: return
        
        self.time_alive += dt
        speed = 10.0
        if self._target_active:
            self.alpha = min(255, self.alpha + speed * 60 * dt)
        else:
            self.alpha = max(0, self.alpha - speed * 80 * dt)
            if self.alpha <= 0:
                self.active = False

    def draw(self, screen, width, height):
        if not self.active: return
        
        if self._blurred_bg is None:
            self._blurred_bg = blur_surface(screen.copy(), factor=6, tint=(10, 8, 20), tint_alpha=180)

        ease = min(self.alpha / 255.0, 1.0)
        
        # Draw Background
        blur_alpha = int(255 * ease)
        if blur_alpha >= 250:
            screen.blit(self._blurred_bg, (0, 0))
        elif blur_alpha > 0:
            temp = self._blurred_bg.copy()
            temp.set_alpha(blur_alpha)
            screen.blit(temp, (0, 0))

        # Center rect
        self.rect.center = (width // 2, height // 2)
        
        # Bouncing effect on open
        bounce = math.sin(self.time_alive * 6) * max(0, 1.0 - self.time_alive * 3) * 20
        screen_y = self.rect.y + int(bounce)
        
        # Create Modal Surface (Matching ProfileModal gradient and mask)
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
        
        # Header (Matching ProfileModal)
        title_surf = self.font_modal_title.render("DAILY MISSIONS", True, Colors.TEXT_GOLD)
        modal_surf.blit(title_surf, (self.rect.w // 2 - title_surf.get_width() // 2, 20))
        pygame.draw.line(modal_surf, (255, 255, 255, 20), (25, 65), (self.rect.w - 25, 65), 1)
        
        # Close Button (Positioned relative to screen like ProfileModal, but drawn here for simplicity)
        self.close_btn_rect.topright = (self.rect.w - 20, 20)
        close_color = (220, 50, 50) if self.close_btn_rect.collidepoint(pygame.mouse.get_pos()[0] - self.rect.x, pygame.mouse.get_pos()[1] - screen_y) else (180, 40, 40)
        pygame.draw.circle(modal_surf, close_color, self.close_btn_rect.center, 15)
        if self.icon_close:
            modal_surf.blit(self.icon_close, (self.close_btn_rect.centerx - 8, self.close_btn_rect.centery - 8))
            
        # Draw Quests
        start_y = 100
        gap = 120
        for i, quest in enumerate(self.quests):
            qy = start_y + i * gap
            
            # Quest Card Background
            pygame.draw.rect(modal_surf, (30, 35, 55, 200), (40, qy, self.rect.w - 80, 100), border_radius=16)
            pygame.draw.rect(modal_surf, (255, 255, 255, 10), (40, qy, self.rect.w - 80, 100), width=1, border_radius=16)
            
            # Quest Desc
            desc_txt = self.font_body.render(quest["desc"], True, Colors.TEXT_WHITE)
            modal_surf.blit(desc_txt, (60, qy + 20))
            
            # Progress Text
            prog_txt = self.font_small.render(f"{quest['curr']}/{quest['goal']}", True, Colors.TEXT_MUTED)
            modal_surf.blit(prog_txt, (self.rect.w - 220, qy + 20))
            
            # Progress Bar
            bar_w = 400
            bar_h = 10
            bx = 60
            by = qy + 60
            pygame.draw.rect(modal_surf, (15, 20, 30), (bx, by, bar_w, bar_h), border_radius=bar_h//2)
            
            progress = min(1.0, quest["curr"] / quest["goal"])
            fill_w = int(bar_w * progress)
            if fill_w > 0:
                pygame.draw.rect(modal_surf, Colors.TEXT_GOLD, (bx, by, fill_w, bar_h), border_radius=bar_h//2)
                
            # Reward Text
            rew_txt = self.font_small.render(f"Reward: {quest['reward']} Coins", True, Colors.TEXT_GOLD)
            modal_surf.blit(rew_txt, (bx, by + 15))
            
            # Claim Button
            btn = self.claim_buttons[i]
            btn.rect.x = self.rect.x + self.rect.w - 170
            btn.rect.y = screen_y + qy + 30
            
            if quest["claimed"]:
                claimed_txt = self.font_body.render("CLAIMED", True, Colors.SAFE_GREEN)
                modal_surf.blit(claimed_txt, (self.rect.w - 150, qy + 35))
            elif quest["curr"] >= quest["goal"]:
                btn.update(pygame.mouse.get_pos(), 0.016)
                btn.draw(screen)
            else:
                pygame.draw.rect(modal_surf, (60, 65, 75), (self.rect.w - 170, qy + 30, btn.rect.w, btn.rect.h), border_radius=8)
                txt = self.font_small.render("CLAIM", True, (120, 125, 135))
                modal_surf.blit(txt, (self.rect.w - 170 + btn.rect.w//2 - txt.get_width()//2, qy + 30 + btn.rect.h//2 - txt.get_height()//2))

        # Blit modal to screen
        screen.blit(modal_surf, (self.rect.x, screen_y))

    def handle_click(self, event):
        if not self.active or not self._target_active: return None
        
        # Calculate screen_y for click detection
        bounce = math.sin(self.time_alive * 6) * max(0, 1.0 - self.time_alive * 3) * 20
        screen_y = self.rect.y + int(bounce)
        
        rel_pos = (event.pos[0] - self.rect.x, event.pos[1] - screen_y)
        
        if self.close_btn_rect.collidepoint(rel_pos):
            self.close()
            return {"type": "close"}
            
        for i, quest in enumerate(self.quests):
            if quest["curr"] >= quest["goal"] and not quest["claimed"]:
                btn = self.claim_buttons[i]
                if btn.is_clicked(event):
                    quest["claimed"] = True
                    self.save_progress()
                    return {"type": "claim", "amount": quest["reward"], "quest_id": quest["id"]}
                    
        if self.rect.collidepoint(event.pos):
            return {"type": "blocked"}
            
        return None
