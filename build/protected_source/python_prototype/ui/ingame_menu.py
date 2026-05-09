import pygame

class InGameMenu:
    def __init__(self, font_title, font_body):
        self.font_title = font_title
        self.font_body = font_body
        self.is_open = False
        
        # Menu state: "main" or "settings"
        self.state = "main"
        
        self.sound_on = True
        self.bgm_on = True
        
        # Panel dimensions (same as a medium modal)
        self.w = 360
        self.h = 400
        self.rect = pygame.Rect(0, 0, self.w, self.h)
        
        # 3 Buttons
        self.btn1_rect = pygame.Rect(0, 0, 240, 50)
        self.btn2_rect = pygame.Rect(0, 0, 240, 50)
        self.btn3_rect = pygame.Rect(0, 0, 240, 50)
        
    def toggle(self):
        self.is_open = not self.is_open
        if self.is_open:
            self.state = "main" # Reset to main menu when opening
        
    def handle_event(self, event):
        if not self.is_open:
            return None
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "main":
                if self.btn1_rect.collidepoint(event.pos):
                    self.is_open = False
                    return "resume"
                elif self.btn2_rect.collidepoint(event.pos):
                    self.state = "settings"
                    return "open_settings"
                elif self.btn3_rect.collidepoint(event.pos):
                    self.is_open = False
                    return "leave"
            elif self.state == "settings":
                if self.btn1_rect.collidepoint(event.pos):
                    self.sound_on = not self.sound_on
                    return "toggle_sound"
                elif self.btn2_rect.collidepoint(event.pos):
                    self.bgm_on = not self.bgm_on
                    return "toggle_bgm"
                elif self.btn3_rect.collidepoint(event.pos):
                    self.state = "main"
                    return "back"
                    
        return "intercept" # Intercept clicks when open
        
    def draw(self, surface, width, height):
        if not self.is_open:
            return
            
        # 1. Dim Background
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        # 2. Draw Menu Box (Premium Glassmorphism)
        self.rect.center = (width // 2, height // 2)
        px, py = self.rect.x, self.rect.y
        
        panel_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for row in range(self.h):
            rt = row / self.h
            # Dark blue/purple gradient similar to Profile Modal
            rc = int(25 + 10 * (1 - rt))
            gc = int(30 + 15 * (1 - rt))
            bc = int(55 + 20 * (1 - rt))
            pygame.draw.line(panel_surf, (rc, gc, bc, 245), (0, row), (self.w, row))
            
        # Rounded corners mask
        mask = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, self.w, self.h), border_radius=24)
        panel_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        # Border
        pygame.draw.rect(panel_surf, (255, 215, 100, 60), (0, 0, self.w, self.h), width=2, border_radius=24)
        surface.blit(panel_surf, (px, py))
        
        # 3. Title
        title_str = "PAUSED" if self.state == "main" else "SETTINGS"
        txt_title = self.font_title.render(title_str, True, (255, 215, 100))
        surface.blit(txt_title, (self.rect.centerx - txt_title.get_width() // 2, py + 30))
        
        # 4. Buttons Positioning
        self.btn1_rect.center = (self.rect.centerx, py + 130)
        self.btn2_rect.center = (self.rect.centerx, py + 210)
        self.btn3_rect.center = (self.rect.centerx, py + 290)
        
        # 5. Render Buttons based on state
        mouse_pos = pygame.mouse.get_pos()
        
        if self.state == "main":
            self._draw_btn(surface, self.btn1_rect, "Resume", (50, 120, 220), mouse_pos)
            self._draw_btn(surface, self.btn2_rect, "Settings", (40, 45, 60), mouse_pos)
            self._draw_btn(surface, self.btn3_rect, "Back to Lobby", (200, 50, 50), mouse_pos)
        elif self.state == "settings":
            snd_str = f"Sound: {'ON' if self.sound_on else 'OFF'}"
            bgm_str = f"BGM: {'ON' if self.bgm_on else 'OFF'}"
            
            self._draw_btn(surface, self.btn1_rect, snd_str, (50, 120, 220) if self.sound_on else (100, 100, 100), mouse_pos)
            self._draw_btn(surface, self.btn2_rect, bgm_str, (50, 120, 220) if self.bgm_on else (100, 100, 100), mouse_pos)
            self._draw_btn(surface, self.btn3_rect, "Back", (40, 45, 60), mouse_pos)

    def _draw_btn(self, surface, rect, text, color, mouse_pos):
        # Hover effect
        draw_color = color
        if rect.collidepoint(mouse_pos):
            draw_color = (min(255, color[0] + 20), min(255, color[1] + 20), min(255, color[2] + 20))
            
        pygame.draw.rect(surface, draw_color, rect, border_radius=12)
        pygame.draw.rect(surface, (255, 255, 255, 30), rect, width=1, border_radius=12)
        
        txt_surf = self.font_body.render(text, True, (255, 255, 255))
        surface.blit(txt_surf, (rect.centerx - txt_surf.get_width() // 2, rect.centery - txt_surf.get_height() // 2))
