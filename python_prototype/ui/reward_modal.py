import pygame
import math
from ui.ui_components import Colors, Button, blur_surface
import random

class DailyRewardModal:
    def __init__(self, font_title, font_body, font_small):
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = font_small
        
        self.active = False
        self._target_active = False
        self.rect = pygame.Rect(0, 0, 500, 350)
        self.alpha = 0
        self._blurred_bg = None
        self.time_alive = 0.0
        self.amount = 0

        # Claim Button
        btn_w, btn_h = 240, 50
        self.btn_claim = Button(
            0, 0, btn_w, btn_h,
            "AWESOME!", self.font_body,
            color=Colors.BTN_SUCCESS, hover_color=Colors.BTN_SUCCESS_HOVER,
            border_radius=12
        )
        
        # Particles
        self.particles = []

    def open(self, amount):
        self.active = True
        self._target_active = True
        self.alpha = 0
        self.time_alive = 0.0
        self.amount = amount
        self._blurred_bg = None
        
        # Reset particles for an explosion effect
        self.particles = []
        for _ in range(40):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 8)
            self.particles.append({
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'x': 250, # Center X
                'y': 150, # Center Y
                'life': random.uniform(0.5, 1.5),
                'size': random.uniform(3, 6),
                'color': random.choice([(255, 215, 0), (255, 255, 255), (255, 180, 50), (100, 255, 100)])
            })

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

        self.btn_claim.update(mouse_pos, dt)

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
        
        # Scale animation
        scale = 0.8 + 0.2 * ease
        if not self._target_active: scale = 1.0 + 0.1 * (1.0 - ease)
        
        # Bouncing effect on open
        bounce = math.sin(self.time_alive * 6) * max(0, 1.0 - self.time_alive * 3) * 20
        
        modal_w, modal_h = int(self.rect.w * scale), int(self.rect.h * scale)
        modal_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        
        # Panel Glass
        pygame.draw.rect(modal_surf, (20, 25, 45, 245), (0, 0, self.rect.w, self.rect.h), border_radius=20)
        pygame.draw.rect(modal_surf, Colors.TEXT_GOLD, (0, 0, self.rect.w, self.rect.h), width=3, border_radius=20)
        
        center_x, center_y = self.rect.w // 2, self.rect.h // 2 - 40

        # Glow behind text
        glow_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
        glow_alpha = int(50 + 20 * math.sin(self.time_alive * 4))
        pygame.draw.circle(glow_surf, (255, 215, 0, glow_alpha), (100, 100), 100)
        modal_surf.blit(glow_surf, (center_x - 100, center_y - 80))

        # Particles Update & Draw
        dt = 0.016 # approx 60fps
        for p in self.particles:
            p['x'] += p['dx']
            p['y'] += p['dy']
            p['dy'] += 0.2 # gravity
            p['life'] -= dt
            if p['life'] > 0:
                pygame.draw.circle(modal_surf, (*p['color'], int(255 * (p['life'] / 1.5))), (int(p['x']), int(p['y'])), int(p['size']))

        # Text
        txt1 = self.font_title.render("DAILY REWARD!", True, Colors.TEXT_GOLD)
        txt_shad = self.font_title.render("DAILY REWARD!", True, (0,0,0))
        
        modal_surf.blit(txt_shad, (center_x - txt1.get_width()//2 + 2, 42))
        modal_surf.blit(txt1, (center_x - txt1.get_width()//2, 40))
        
        txt2 = self.font_body.render("You ran out of coins...", True, Colors.TEXT_WHITE)
        modal_surf.blit(txt2, (center_x - txt2.get_width()//2, 100))
        
        amt_str = f"+{self.amount:,} COINS"
        txt3 = self.font_title.render(amt_str, True, Colors.SAFE_GREEN)
        modal_surf.blit(txt3, (center_x - txt3.get_width()//2, 140))
        
        txt4 = self.font_small.render("Come back tomorrow if you need more!", True, Colors.TEXT_MUTED)
        modal_surf.blit(txt4, (center_x - txt4.get_width()//2, 200))
        
        screen_y = self.rect.y + int(bounce)
        screen.blit(modal_surf, (self.rect.x, screen_y))

        # Draw button ON TOP of modal so click zones match exactly
        self.btn_claim.rect.centerx = width // 2
        self.btn_claim.rect.y = screen_y + self.rect.h - 80
        self.btn_claim.draw(screen)

    def handle_click(self, event):
        if not self.active or not self._target_active: return False
        
        if self.btn_claim.is_clicked(event):
            self.close()
            return True
            
        # Block clicks to underlying lobby
        if self.rect.collidepoint(event.pos):
            return True
            
        return False
