import pygame
import os
from ui.paths import get_resource_path

class ConfirmationModal:
    def __init__(self, font_title, font_body, font_small):
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = font_small
        self.is_open = False
        self.callback = None
        self.message = ""
        self.rect = pygame.Rect(0, 0, 450, 220)
        self.yes_rect = pygame.Rect(0, 0, 100, 40)
        self.no_rect = pygame.Rect(0, 0, 100, 40)
        
        # Load Icons
        try:
            checkmark_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "checkmark.png"))
            self.icon_yes = pygame.image.load(checkmark_path).convert_alpha()
            self.icon_yes = pygame.transform.smoothscale(self.icon_yes, (20, 20))
            
            cross_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "cross.png"))
            self.icon_no = pygame.image.load(cross_path).convert_alpha()
            self.icon_no = pygame.transform.smoothscale(self.icon_no, (20, 20))
        except Exception as e:
            print(f"Failed to load modal icons: {e}")
            self.icon_yes = None
            self.icon_no = None
        
    def open(self, message, callback):
        self.message = message
        self.callback = callback
        self.is_open = True
        
    def close(self):
        self.is_open = False
        
    def handle_event(self, event):
        if not self.is_open:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.yes_rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                self.close()
                return True
            elif self.no_rect.collidepoint(event.pos):
                self.close()
                return True
        return True # Intercept clicks when open
        
    def draw(self, surface, width, height):
        if not self.is_open:
            return
            
        # Draw overlay
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Draw modal box
        self.rect.center = (width // 2, height // 2)
        pygame.draw.rect(surface, (30, 35, 45), self.rect, border_radius=15)
        pygame.draw.rect(surface, (60, 65, 80), self.rect, width=2, border_radius=15)
        
        # Draw message
        lines = self.wrap_text(self.message, self.font_body, self.rect.w - 40)
        y = self.rect.y + 30
        for line in lines:
            txt = self.font_body.render(line, True, (240, 240, 245))
            surface.blit(txt, (self.rect.centerx - txt.get_width() // 2, y))
            y += 25
            
        # Draw buttons
        self.yes_rect.center = (self.rect.centerx - 70, self.rect.bottom - 45)
        self.no_rect.center = (self.rect.centerx + 70, self.rect.bottom - 45)
        
        # Yes Button
        bc_yes = (50, 120, 220)
        if self.yes_rect.collidepoint(pygame.mouse.get_pos()):
            bc_yes = (70, 140, 240)
        pygame.draw.rect(surface, bc_yes, self.yes_rect, border_radius=8)
        if self.icon_yes:
            surface.blit(self.icon_yes, (self.yes_rect.centerx - 10, self.yes_rect.centery - 10))
        else:
            txt_yes = self.font_small.render("Yes", True, (255, 255, 255))
            surface.blit(txt_yes, (self.yes_rect.centerx - txt_yes.get_width() // 2, self.yes_rect.centery - txt_yes.get_height() // 2))
        
        # No Button
        bc_no = (40, 45, 60)
        if self.no_rect.collidepoint(pygame.mouse.get_pos()):
            bc_no = (60, 65, 80)
        pygame.draw.rect(surface, bc_no, self.no_rect, border_radius=8)
        if self.icon_no:
            surface.blit(self.icon_no, (self.no_rect.centerx - 10, self.no_rect.centery - 10))
        else:
            txt_no = self.font_small.render("No", True, (220, 220, 230))
            surface.blit(txt_no, (self.no_rect.centerx - txt_no.get_width() // 2, self.no_rect.centery - txt_no.get_height() // 2))
        
    def wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            width, height = font.size(' '.join(current_line))
            if width > max_width:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines
