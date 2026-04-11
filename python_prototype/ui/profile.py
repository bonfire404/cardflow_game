import pygame
import math
import os
import time
from ui.ui_components import Colors, Button
from ui.animation import Animation, ease_out_back, ease_in_out_quad

class ProfileModal:
    def __init__(self, screen_w, screen_h, fonts=None):
        self.w, self.h = screen_w, screen_h
        self.active = False
        
        # State for animations
        self.alpha = 0
        self.scale = 0
        self.target_active = False
        
        # Modal Dimensions
        self.modal_w = 700
        self.modal_h = 550
        self.rect = pygame.Rect(self.w // 2 - self.modal_w // 2, self.h // 2 - self.modal_h // 2, self.modal_w, self.modal_h)
        
        # Fonts
        if fonts:
            self.font_title = fonts.get('title', pygame.font.SysFont("Arial", 32, bold=True))
            self.font_body = fonts.get('body', pygame.font.SysFont("Arial", 22))
            self.font_small = fonts.get('small', pygame.font.SysFont("Arial", 18))
            self.font_btn = fonts.get('btn', pygame.font.SysFont("Arial", 18, bold=True))
        else:
            self.font_title = pygame.font.SysFont("Arial", 32, bold=True)
            self.font_body = pygame.font.SysFont("Arial", 22)
            self.font_small = pygame.font.SysFont("Arial", 18)
            self.font_btn = pygame.font.SysFont("Arial", 18, bold=True)
            
        self.player_name = "Player"
        self.temp_name = "Player"
        self.selected_avatar_idx = 0
        self.hovered_avatar_idx = -1
        self.avatars = []
        self.editing_name = False
        
        # UI Buttons
        btn_y = self.rect.y + self.rect.h - 70
        self.save_btn = Button(self.rect.centerx - 120, btn_y, 110, 45, "SAVE", self.font_btn, color=Colors.BTN_SUCCESS, hover_color=Colors.BTN_SUCCESS_HOVER)
        self.cancel_btn = Button(self.rect.centerx + 10, btn_y, 110, 45, "CANCEL", self.font_btn, color=Colors.BTN_DANGER, hover_color=Colors.BTN_DANGER_HOVER)
        
        # Decorative "X" close button
        self.close_btn_rect = pygame.Rect(self.rect.right - 45, self.rect.y + 15, 30, 30)
        
        # Upload Button
        self.upload_btn = Button(self.rect.centerx - 150, self.rect.y + 430, 300, 35, "UPLOAD CUSTOM", self.font_small, color=(60, 65, 85), hover_color=(80, 85, 110))
        
        self._load_avatars_from_assets()

    def _load_avatars_from_assets(self):
        """Load avatars from the project directory and process them into premium circular frames."""
        self.avatars = []
        assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets'))
        avatars_dir = os.path.join(assets_dir, "images", "avatars")
        
        if os.path.exists(avatars_dir):
            for fn in sorted(os.listdir(avatars_dir)):
                if fn.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    try:
                        img = pygame.image.load(os.path.join(avatars_dir, fn)).convert_alpha()
                        self.avatars.append(self._process_avatar(img))
                    except: pass
        
        # Add a few default fallbacks if empty
        if not self.avatars:
            for i in range(5):
                surf = pygame.Surface((90, 90), pygame.SRCALPHA)
                color = [(100, 150, 255), (255, 100, 150), (150, 255, 100), (255, 200, 100), (200, 100, 255)][i % 5]
                pygame.draw.circle(surf, color, (45, 45), 42)
                pygame.draw.circle(surf, (255, 255, 255, 100), (45, 45), 45, width=2)
                self.avatars.append(surf)

    def _process_avatar(self, img):
        """Scale and mask image into a premium circular profile pic."""
        size = 90
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Center crop and scale
        iw, ih = img.get_size()
        crop_size = min(iw, ih)
        crop_rect = pygame.Rect((iw - crop_size) // 2, (ih - crop_size) // 2, crop_size, crop_size)
        cropped = img.subsurface(crop_rect)
        scaled = pygame.transform.smoothscale(cropped, (size-6, size-6))
        
        # Create circular mask
        mask = pygame.Surface((size-6, size-6), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255), ((size-6)//2, (size-6)//2), (size-6)//2)
        
        # Apply mask
        target = pygame.Surface((size-6, size-6), pygame.SRCALPHA)
        target.blit(scaled, (0, 0))
        target.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        surf.blit(target, (3, 3))
        # Outer ring
        pygame.draw.circle(surf, (255, 215, 0, 180), (size//2, size//2), size//2, width=2)
        
        return surf

    def on_resize(self, screen_w, screen_h):
        """Update modal and button positions when screen size changes."""
        self.w, self.h = screen_w, screen_h
        self.rect = pygame.Rect(self.w // 2 - self.modal_w // 2, self.h // 2 - self.modal_h // 2, self.modal_w, self.modal_h)
        
        # Recalculate component positions
        btn_y = self.rect.y + self.rect.h - 70
        self.save_btn.rect.topleft = (self.rect.centerx - 120, btn_y)
        self.cancel_btn.rect.topleft = (self.rect.centerx + 10, btn_y)
        self.close_btn_rect = pygame.Rect(self.rect.right - 45, self.rect.y + 15, 30, 30)
        self.upload_btn.rect.topleft = (self.rect.centerx - 150, self.rect.y + 430)

    def open(self, current_name):
        self.active = True
        self.target_active = True
        self.temp_name = current_name
        self.editing_name = False
        # Initial animation state
        self.alpha = 0
        self.scale = 0.8

    def close(self):
        self.target_active = False

    def update(self, dt, mouse_pos):
        # Handle Fade/Scale Animations
        speed = 8.0
        if self.target_active:
            self.alpha = min(255, self.alpha + speed * 40 * dt)
            self.scale = min(1.0, self.scale + speed * dt)
        else:
            self.alpha = max(0, self.alpha - speed * 40 * dt)
            self.scale = max(0.8, self.scale - speed * dt)
            if self.alpha <= 0:
                self.active = False

        if not self.active: return

        # Update buttons
        self.save_btn.update(mouse_pos, dt)
        self.cancel_btn.update(mouse_pos, dt)
        self.upload_btn.update(mouse_pos, dt)

        # Avatar hover detection
        self.hovered_avatar_idx = -1
        grid_cols = 5
        grid_start_x = self.rect.x + 85
        grid_start_y = self.rect.y + 210
        
        for idx in range(len(self.avatars)):
            row = idx // grid_cols
            col = idx % grid_cols
            ax = grid_start_x + col * 110
            ay = grid_start_y + row * 110
            if pygame.Rect(ax, ay, 90, 90).collidepoint(mouse_pos):
                self.hovered_avatar_idx = idx
                break

    def handle_event(self, event):
        if not self.active or not self.target_active: return None
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.save_btn.is_clicked(event):
                self.close()
                return {"type": "save", "name": self.temp_name, "avatar_idx": self.selected_avatar_idx}
            
            if self.cancel_btn.is_clicked(event) or self.close_btn_rect.collidepoint(event.pos):
                self.close()
                return {"type": "cancel"}
            
            if self.upload_btn.is_clicked(event):
                self._handle_upload()

            # Name Input collision
            name_box_rect = pygame.Rect(self.rect.centerx - 150, self.rect.y + 115, 300, 45)
            if name_box_rect.collidepoint(event.pos):
                self.editing_name = True
            else:
                self.editing_name = False

            # Avatar Selection
            if self.hovered_avatar_idx != -1:
                self.selected_avatar_idx = self.hovered_avatar_idx

        if event.type == pygame.KEYDOWN and self.editing_name:
            if event.key == pygame.K_BACKSPACE:
                self.temp_name = self.temp_name[:-1]
            elif event.key == pygame.K_RETURN:
                self.editing_name = False
            else:
                if len(self.temp_name) < 15 and event.unicode.isprintable():
                    self.temp_name += event.unicode
        
        return None

    def _handle_upload(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp")])
            root.destroy()
            
            if file_path and os.path.exists(file_path):
                custom_img = pygame.image.load(file_path).convert_alpha()
                processed = self._process_avatar(custom_img)
                self.avatars.append(processed)
                self.selected_avatar_idx = len(self.avatars) - 1
        except Exception as e:
            print(f"Error loading custom avatar: {e}")

    def draw(self, surface):
        if not self.active: return
            
        # 1. Dimmer Overlay
        overlay_alpha = int(self.alpha * 0.7)
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((5, 8, 15, overlay_alpha))
        surface.blit(overlay, (0, 0))
        
        # 2. Modal Surface with Scale Animation
        modal_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        
        # Modern Glassmorphism Backdrop
        bg_alpha = int(self.alpha * 0.95)
        # Deep base
        pygame.draw.rect(modal_surf, (15, 20, 35, bg_alpha), (0, 0, self.rect.w, self.rect.h), border_radius=30)
        # Inner Gloss/Glass shine
        pygame.draw.rect(modal_surf, (255, 255, 255, 15), (2, 2, self.rect.w-4, self.rect.h-4), border_radius=28)
        # Gold Border
        pygame.draw.rect(modal_surf, (218, 165, 32, 100), (0, 0, self.rect.w, self.rect.h), width=2, border_radius=30)
        
        # --- Header ---
        header_h = 60
        # Header separator
        pygame.draw.line(modal_surf, (255, 255, 255, 25), (30, header_h), (self.rect.w - 30, header_h), 1)
        
        # Title
        title_surf = self.font_title.render("AGENT IDENTITY", True, Colors.TEXT_GOLD)
        modal_surf.blit(title_surf, (self.rect.w // 2 - title_surf.get_width() // 2, 15))
        
        # --- Body Content ---
        # Section Label: Name
        name_label = self.font_small.render("OPERATIVE NAME", True, (160, 160, 180))
        modal_surf.blit(name_label, (self.rect.w // 2 - 150, 90))
        
        # Name Input Field
        box_w, box_h = 300, 50
        box_rect = pygame.Rect(self.rect.w // 2 - 150, 115, box_w, box_h)
        box_color = (25, 30, 50, 200) if not self.editing_name else (40, 50, 90, 220)
        pygame.draw.rect(modal_surf, box_color, (box_rect.x, box_rect.y, box_w, box_h), border_radius=12)
        border_col = (Colors.TEXT_GOLD if self.editing_name else (80, 80, 100))
        pygame.draw.rect(modal_surf, border_col, (box_rect.x, box_rect.y, box_w, box_h), width=2, border_radius=12)
        
        # Text in Box
        cursor = "|" if (time.time() * 2 % 2 < 1 and self.editing_name) else ""
        txt_surf = self.font_body.render(self.temp_name + cursor, True, Colors.TEXT_WHITE)
        modal_surf.blit(txt_surf, (box_rect.x + 15, box_rect.centery - txt_surf.get_height() // 2))
        
        # Section Label: Avatar
        av_label = self.font_small.render("SELECT PROFILE AVATAR", True, (160, 160, 180))
        modal_surf.blit(av_label, (self.rect.w // 2 - 150, 185))
        
        # Apply scaling and final blit
        if self.scale < 1.0:
            final_surf = pygame.transform.smoothscale(modal_surf, (int(self.rect.w * self.scale), int(self.rect.h * self.scale)))
            off_x = (self.rect.w - final_surf.get_width()) // 2
            off_y = (self.rect.h - final_surf.get_height()) // 2
            surface.blit(final_surf, (self.rect.x + off_x, self.rect.y + off_y))
        else:
            surface.blit(modal_surf, self.rect.topleft)
            
            # --- Interactive Elements (Need to be drawn on main surface for mouse interaction sync or offset) ---
            # Close "X" Button
            pygame.draw.circle(surface, (150, 40, 40, self.alpha), self.close_btn_rect.center, 15)
            x_surf = self.font_small.render("X", True, (255, 255, 255))
            surface.blit(x_surf, (self.close_btn_rect.centerx - x_surf.get_width() // 2, self.close_btn_rect.centery - x_surf.get_height() // 2))
            
            # Avatar Grid
            grid_cols = 5
            grid_start_x = self.rect.x + 85
            grid_start_y = self.rect.y + 210
            
            for idx in range(min(10, len(self.avatars))):
                row = idx // grid_cols
                col = idx % grid_cols
                ax = grid_start_x + col * 110
                ay = grid_start_y + row * 110
                
                # Draw Hover/Selection Glow
                if idx == self.selected_avatar_idx or idx == self.hovered_avatar_idx:
                    p = int(5 * math.sin(time.time() * 6)) if idx == self.selected_avatar_idx else 0
                    glow_color = Colors.TEXT_GOLD if idx == self.selected_avatar_idx else (255, 255, 255, 100)
                    pygame.draw.circle(surface, glow_color, (ax + 45, ay + 45), 48 + p, width=3)
                
                # Draw Avatar
                surface.blit(self.avatars[idx], (ax, ay))
            
            # Action Buttons
            self.upload_btn.draw(surface)
            self.save_btn.draw(surface)
            self.cancel_btn.draw(surface)
