import pygame
import os
import math
from ui.paths import get_resource_path
from ui.ui_components import Colors, blur_surface

class SettingsModal:
    def __init__(self, font_title, font_body, font_small, set_bgm_callback=None, set_sfx_callback=None):
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = font_small
        self.is_open = False
        
        # Matching ProfileModal design and layout
        self.rect = pygame.Rect(0, 0, 700, 500) # 700 wide like ProfileModal
        self.alpha = 0
        self._blurred_bg = None
        self.time_alive = 0.0
        
        # Load Sekuya for modal title
        _sekuya_path = get_resource_path(os.path.join("assets", "fonts", "Sekuya", "Sekuya-Regular.ttf"))
        try:
            self.font_modal_title = pygame.font.Font(_sekuya_path, 34)
        except:
            self.font_modal_title = self.font_title
            
        self.close_btn_rect = pygame.Rect(0, 0, 30, 30)
        
        self.set_bgm_callback = set_bgm_callback
        self.set_sfx_callback = set_sfx_callback
        
        # Volume states (0.0 to 1.0)
        self.bgm_volume = 0.5
        self.sfx_volume = 0.5
        
        self.is_dragging_bgm = False
        self.is_dragging_sfx = False
        
        # Slider positions
        self.slider_w = 300
        self.slider_h = 10
        self.bgm_slider_rect = pygame.Rect(0, 0, self.slider_w, self.slider_h)
        self.sfx_slider_rect = pygame.Rect(0, 0, self.slider_w, self.slider_h)
        
        # Load Icons
        try:
            cross_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "cross.png"))
            self.icon_close = pygame.image.load(cross_path).convert_alpha()
            self.icon_close = pygame.transform.smoothscale(self.icon_close, (16, 16))
        except Exception as e:
            print(f"Failed to load settings icons: {e}")
            self.icon_close = None
            
    def open(self):
        self.is_open = True
        self.alpha = 0
        self.time_alive = 0.0
        self._blurred_bg = None
        # Load current volume from Channel 7
        try:
            self.bgm_volume = pygame.mixer.Channel(7).get_volume()
        except:
            self.bgm_volume = 0.5
            
    def close(self):
        self.is_open = False
        self.is_dragging_bgm = False
        self.is_dragging_sfx = False
        
    def handle_event(self, event):
        if not self.is_open:
            return False
            
        bounce = math.sin(self.time_alive * 6) * max(0, 1.0 - self.time_alive * 3) * 20
        screen_y = self.rect.y + int(bounce)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rel_pos = (event.pos[0] - self.rect.x, event.pos[1] - screen_y)
            
            if self.close_btn_rect.collidepoint(rel_pos):
                self.close()
                return True
                
            # Check BGM slider
            bgm_knob_x = self.bgm_slider_rect.x + int(self.bgm_volume * self.slider_w)
            bgm_knob_rect = pygame.Rect(bgm_knob_x - 10, self.bgm_slider_rect.centery - 10, 20, 20)
            if bgm_knob_rect.collidepoint(event.pos):
                self.is_dragging_bgm = True
                return True
                
            # Check SFX slider
            sfx_knob_x = self.sfx_slider_rect.x + int(self.sfx_volume * self.slider_w)
            sfx_knob_rect = pygame.Rect(sfx_knob_x - 10, self.sfx_slider_rect.centery - 10, 20, 20)
            if sfx_knob_rect.collidepoint(event.pos):
                self.is_dragging_sfx = True
                return True
                
            # Click on track to jump
            if self.bgm_slider_rect.collidepoint(event.pos):
                self.bgm_volume = (event.pos[0] - self.bgm_slider_rect.x) / self.slider_w
                self.bgm_volume = max(0.0, min(1.0, self.bgm_volume))
                self.apply_volumes()
                self.is_dragging_bgm = True
                return True
                
            if self.sfx_slider_rect.collidepoint(event.pos):
                self.sfx_volume = (event.pos[0] - self.sfx_slider_rect.x) / self.slider_w
                self.sfx_volume = max(0.0, min(1.0, self.sfx_volume))
                self.apply_volumes()
                self.is_dragging_sfx = True
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging_bgm = False
            self.is_dragging_sfx = False
            
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging_bgm:
                self.bgm_volume = (event.pos[0] - self.bgm_slider_rect.x) / self.slider_w
                self.bgm_volume = max(0.0, min(1.0, self.bgm_volume))
                self.apply_volumes()
            elif self.is_dragging_sfx:
                self.sfx_volume = (event.pos[0] - self.sfx_slider_rect.x) / self.slider_w
                self.sfx_volume = max(0.0, min(1.0, self.sfx_volume))
                self.apply_volumes()
                
        if hasattr(event, 'pos'):
            return self.rect.collidepoint(event.pos)
        return False
        
    def apply_volumes(self):
        if self.set_bgm_callback:
            self.set_bgm_callback(self.bgm_volume)
        if self.set_sfx_callback:
            self.set_sfx_callback(self.sfx_volume)
            
    def update(self, dt, mouse_pos):
        if not self.is_open: return
        self.time_alive += dt
        if self.alpha < 255:
            self.alpha = min(255, self.alpha + 15)

    def draw(self, screen, width, height):
        if not self.is_open:
            return
            
        if self.alpha < 255:
            self.alpha = min(255, self.alpha + 15)
            
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
        
        # Header
        title_surf = self.font_modal_title.render("GAME SETTINGS", True, Colors.TEXT_GOLD)
        modal_surf.blit(title_surf, (self.rect.w // 2 - title_surf.get_width() // 2, 20))
        pygame.draw.line(modal_surf, (255, 255, 255, 20), (25, 65), (self.rect.w - 25, 65), 1)
        
        # Close Button
        self.close_btn_rect.topright = (self.rect.w - 20, 20)
        close_color = (220, 50, 50) if self.close_btn_rect.collidepoint(pygame.mouse.get_pos()[0] - self.rect.x, pygame.mouse.get_pos()[1] - screen_y) else (180, 40, 40)
        pygame.draw.circle(modal_surf, close_color, self.close_btn_rect.center, 15)
        if self.icon_close:
            modal_surf.blit(self.icon_close, (self.close_btn_rect.centerx - 8, self.close_btn_rect.centery - 8))
            
        # Draw Content
        cx = 50
        
        # BGM Slider
        bgm_label = self.font_body.render("Music Volume", True, (255, 255, 255))
        modal_surf.blit(bgm_label, (cx, 100))
        
        self.bgm_slider_rect.x = self.rect.x + cx + 200
        self.bgm_slider_rect.y = screen_y + 110
        pygame.draw.rect(modal_surf, (30, 35, 55), (cx + 200, 110, self.slider_w, self.slider_h), border_radius=self.slider_h//2)
        
        bgm_fill_w = int(self.slider_w * self.bgm_volume)
        if bgm_fill_w > 0:
            pygame.draw.rect(modal_surf, Colors.TEXT_GOLD, (cx + 200, 110, bgm_fill_w, self.slider_h), border_radius=self.slider_h//2)
            
        bgm_knob_x = cx + 200 + bgm_fill_w
        pygame.draw.circle(modal_surf, (255, 255, 255), (bgm_knob_x, 115), 10)
        
        # SFX Slider
        sfx_label = self.font_body.render("Sound Effects", True, (255, 255, 255))
        modal_surf.blit(sfx_label, (cx, 180))
        
        self.sfx_slider_rect.x = self.rect.x + cx + 200
        self.sfx_slider_rect.y = screen_y + 190
        pygame.draw.rect(modal_surf, (30, 35, 55), (cx + 200, 190, self.slider_w, self.slider_h), border_radius=self.slider_h//2)
        
        sfx_fill_w = int(self.slider_w * self.sfx_volume)
        if sfx_fill_w > 0:
            pygame.draw.rect(modal_surf, Colors.TEXT_GOLD, (cx + 200, 190, sfx_fill_w, self.slider_h), border_radius=self.slider_h//2)
            
        sfx_knob_x = cx + 200 + sfx_fill_w
        pygame.draw.circle(modal_surf, (255, 255, 255), (sfx_knob_x, 195), 10)
        
        # Credits or other info could go here...
        credits_title = self.font_body.render("Credits", True, Colors.TEXT_GOLD)
        modal_surf.blit(credits_title, (cx, 260))
        
        credits_lines = [
            "PROJECT MANAGER: LOUISE JAN CARLO TABALDO",
            "LEAD DEVELOPER: BON JURY PECAOCO",
            "GAME DESIGNER: CHONA MAE GREGORIO, CRISTINA GERTOS",
            "TECHNICAL WRITER: JAMAICA NAZARENO"
        ]
        
        for i, line in enumerate(credits_lines):
            line_surf = self.font_small.render(line, True, (200, 200, 200))
            modal_surf.blit(line_surf, (cx, 300 + i * 25))
            
        # Branding
        brand_txt1 = self.font_small.render("A ", True, (255, 255, 255))
        brand_txt2 = self.font_small.render("BONFIRE BASE", True, (255, 128, 0))
        brand_txt3 = self.font_small.render(" Studios Production", True, (255, 255, 255))
        
        by_pos = 430
        modal_surf.blit(brand_txt1, (cx, by_pos))
        modal_surf.blit(brand_txt2, (cx + brand_txt1.get_width(), by_pos))
        modal_surf.blit(brand_txt3, (cx + brand_txt1.get_width() + brand_txt2.get_width(), by_pos))

        # Blit modal to screen
        screen.blit(modal_surf, (self.rect.x, screen_y))
