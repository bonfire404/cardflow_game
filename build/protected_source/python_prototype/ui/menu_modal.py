import pygame
import math
import os
import time
from ui.ui_components import Colors, blur_surface

class MenuModal:
    """Mid-game menu modal with options to return to lobby, see rules, or resume."""

    def __init__(self, screen_w, screen_h, fonts=None):
        self.w, self.h = screen_w, screen_h
        self.active = False

        self.alpha = 0
        self.scale = 0
        self.target_active = False
        self._blurred_bg = None

        # Modal Dimensions
        self.modal_w = 400
        self.modal_h = 450
        self.rect = pygame.Rect(self.w // 2 - self.modal_w // 2, self.h // 2 - self.modal_h // 2, self.modal_w, self.modal_h)

        # Fonts
        if fonts:
            self.font_title = fonts.get('title', pygame.font.SysFont("Arial", 32, bold=True))
            self.font_btn = fonts.get('btn', pygame.font.SysFont("Arial", 22, bold=True))
            self.font_small = fonts.get('small', pygame.font.SysFont("Arial", 16))
        else:
            self.font_title = pygame.font.SysFont("Arial", 32, bold=True)
            self.font_btn = pygame.font.SysFont("Arial", 22, bold=True)
            self.font_small = pygame.font.SysFont("Arial", 16)

        # Buttons
        self.buttons = []
        self._update_button_rects()

    def _update_button_rects(self):
        bw, bh = 280, 55
        start_y = self.rect.y + 120
        spacing = 70
        
        self.buttons = [
            {"label": "CONTINUE", "rect": pygame.Rect(self.rect.centerx - bw//2, start_y, bw, bh), "action": "resume", "hover": False, "color": (50, 150, 255)},
            {"label": "GAME RULES", "rect": pygame.Rect(self.rect.centerx - bw//2, start_y + spacing, bw, bh), "action": "rules", "hover": False, "color": (218, 175, 50)},
            {"label": "QUIT TO LOBBY", "rect": pygame.Rect(self.rect.centerx - bw//2, start_y + spacing * 2, bw, bh), "action": "lobby", "hover": False, "color": (220, 60, 60)},
        ]

    def on_resize(self, screen_w, screen_h):
        self.w, self.h = screen_w, screen_h
        self.rect.center = (self.w // 2, self.h // 2)
        self._update_button_rects()
        self._blurred_bg = None

    def open(self):
        self.active = True
        self.target_active = True
        self.alpha = 0
        self.scale = 0.85
        self._blurred_bg = None

    def close(self):
        self.target_active = False

    def update(self, dt, mouse_pos):
        speed = 12.0
        if self.target_active:
            self.alpha = min(255, self.alpha + speed * 50 * dt)
            self.scale = min(1.0, self.scale + speed * 0.8 * dt)
        else:
            self.alpha = max(0, self.alpha - speed * 80 * dt)
            self.scale = max(0.85, self.scale - speed * 1.5 * dt)
            if self.alpha <= 0:
                self.active = False

        if not self.active: return

        for btn in self.buttons:
            btn["hover"] = btn["rect"].collidepoint(mouse_pos)

    def handle_event(self, event):
        if not self.active or not self.target_active: return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn["hover"]:
                    if btn["action"] == "resume":
                        self.close()
                    return btn["action"]
            
            # Click outside to close
            if not self.rect.collidepoint(event.pos):
                self.close()
                return "resume"

        return None

    def draw(self, surface):
        if not self.active: return

        # 1. Background Blur
        if self._blurred_bg is None:
            self._blurred_bg = blur_surface(surface.copy(), factor=6, tint=(10, 12, 20), tint_alpha=200)

        ease = min(self.alpha / 255.0, 1.0)
        blur_alpha = int(255 * ease)
        if blur_alpha >= 250:
            surface.blit(self._blurred_bg, (0, 0))
        else:
            temp = self._blurred_bg.copy()
            temp.set_alpha(blur_alpha)
            surface.blit(temp, (0, 0))

        # 2. Modal Frame
        modal_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        
        # Deep backdrop
        pygame.draw.rect(modal_surf, (20, 25, 45, 240), (0, 0, self.rect.w, self.rect.h), border_radius=30)
        # Gold border
        pygame.draw.rect(modal_surf, Colors.TEXT_GOLD, (0, 0, self.rect.w, self.rect.h), width=2, border_radius=30)
        
        # Header separator
        pygame.draw.line(modal_surf, (255, 255, 255, 30), (40, 90), (self.rect.w - 40, 90), 1)

        # Title
        title_surf = self.font_title.render("MENU", True, Colors.TEXT_GOLD)
        modal_surf.blit(title_surf, (self.rect.w//2 - title_surf.get_width()//2, 35))

        # Apply scaling
        if self.scale < 1.0:
            final_surf = pygame.transform.smoothscale(modal_surf, (int(self.rect.w * self.scale), int(self.rect.h * self.scale)))
            surface.blit(final_surf, (self.rect.centerx - final_surf.get_width()//2, self.rect.centery - final_surf.get_height()//2))
        else:
            surface.blit(modal_surf, self.rect.topleft)
            
            # Buttons
            for btn in self.buttons:
                rect = btn["rect"]
                color = btn["color"]
                is_hover = btn["hover"]
                
                # Button Shadow
                pygame.draw.rect(surface, (0, 0, 0, 80), (rect.x + 3, rect.y + 3, rect.w, rect.h), border_radius=15)
                
                # Button Background
                b_color = [min(255, c + 30) if is_hover else c for c in color]
                pygame.draw.rect(surface, b_color, rect, border_radius=15)
                pygame.draw.rect(surface, (255, 255, 255, 60), rect, width=2, border_radius=15)
                
                # Gloss
                if is_hover:
                    gloss = pygame.Surface((rect.w, rect.h//2), pygame.SRCALPHA)
                    pygame.draw.rect(gloss, (255, 255, 255, 40), (0, 0, rect.w, rect.h//2), border_top_left_radius=15, border_top_right_radius=15)
                    surface.blit(gloss, rect.topleft)

                # Text
                label_surf = self.font_btn.render(btn["label"], True, (255, 255, 255))
                surface.blit(label_surf, (rect.centerx - label_surf.get_width()//2, rect.centery - label_surf.get_height()//2))
