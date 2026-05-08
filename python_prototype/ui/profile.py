import pygame
import math
import os
import time
from ui.ui_components import Colors, Button, blur_surface
from ui.paths import get_resource_path


class ProfileModal:
    """Premium profile editor with blur backdrop and gradient buttons."""

    def __init__(self, screen_w, screen_h, fonts=None):
        self.w, self.h = screen_w, screen_h
        self.active = False

        self.alpha = 0
        self.scale = 0
        self.target_active = False
        self._blurred_bg = None

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

        # Load Sekuya for modal title
        _sekuya_path = get_resource_path(os.path.join("assets", "fonts", "Sekuya", "Sekuya-Regular.ttf"))
        try:
            self.font_modal_title = pygame.font.Font(_sekuya_path, 34)
        except:
            self.font_modal_title = self.font_title

        self.player_name = "Player"
        self.temp_name = "Player"
        self.selected_avatar_idx = 0
        self.hovered_avatar_idx = -1
        self.avatars = []
        self.editing_name = False
        self.view_mode = "view" # "view" or "edit"

        # Button rects (custom gradient, not Button class)
        self._btn_w, self._btn_h = 130, 46
        self._btn_radius = 14
        btn_y = self.rect.y + self.rect.h - 68
        self.save_rect = pygame.Rect(self.rect.centerx - self._btn_w - 12, btn_y, self._btn_w, self._btn_h)
        self.cancel_rect = pygame.Rect(self.rect.centerx + 12, btn_y, self._btn_w, self._btn_h)
        self._save_hover = False
        self._cancel_hover = False

        # Close "X" button
        self.close_btn_rect = pygame.Rect(self.rect.right - 45, self.rect.y + 15, 30, 30)
        self._close_hover = False

        # Upload Button
        self.upload_rect = pygame.Rect(self.rect.centerx - 150, self.rect.y + 430, 300, 36)
        self._upload_hover = False

        # Pen Icon Rect
        self.pen_rect = pygame.Rect(0, 0, 0, 0)
        self._pen_hover = False

        self._load_avatars_from_assets()

    def _load_avatars_from_assets(self):
        """Load avatars from the project directory and process them into premium circular frames."""
        self.avatars = []
        assets_dir = get_resource_path('assets')
        avatars_dir = os.path.join(assets_dir, "images", "avatars")

        if os.path.exists(avatars_dir):
            for fn in sorted(os.listdir(avatars_dir)):
                if fn.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    try:
                        img = pygame.image.load(os.path.join(avatars_dir, fn)).convert_alpha()
                        self.avatars.append(self._process_avatar(img))
                    except:
                        pass

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

        iw, ih = img.get_size()
        crop_size = min(iw, ih)
        crop_rect = pygame.Rect((iw - crop_size) // 2, (ih - crop_size) // 2, crop_size, crop_size)
        cropped = img.subsurface(crop_rect)
        scaled = pygame.transform.smoothscale(cropped, (size - 6, size - 6))

        mask = pygame.Surface((size - 6, size - 6), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255), ((size - 6) // 2, (size - 6) // 2), (size - 6) // 2)

        target = pygame.Surface((size - 6, size - 6), pygame.SRCALPHA)
        target.blit(scaled, (0, 0))
        target.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        surf.blit(target, (3, 3))
        pygame.draw.circle(surf, (255, 215, 0, 180), (size // 2, size // 2), size // 2, width=2)

        return surf

    def on_resize(self, screen_w, screen_h):
        self.w, self.h = screen_w, screen_h
        self.rect = pygame.Rect(self.w // 2 - self.modal_w // 2, self.h // 2 - self.modal_h // 2, self.modal_w, self.modal_h)
        self._blurred_bg = None

        btn_y = self.rect.y + self.rect.h - 68
        self.save_rect.topleft = (self.rect.centerx - self._btn_w - 12, btn_y)
        self.cancel_rect.topleft = (self.rect.centerx + 12, btn_y)
        self.close_btn_rect = pygame.Rect(self.rect.right - 45, self.rect.y + 15, 30, 30)
        self.upload_rect.topleft = (self.rect.centerx - 150, self.rect.y + 430)

    def open(self, current_name, stats=None):
        self.active = True
        self.target_active = True
        self.player_name = current_name
        self.temp_name = current_name
        self.editing_name = False
        self.alpha = 0
        self.scale = 0.8
        self._blurred_bg = None
        self.stats = stats or {}
        self.view_mode = "view" # Default to view mode

    def close(self):
        self.target_active = False

    def update(self, dt, mouse_pos):
        speed = 25.0 # Increased from 8 to make it very snappy
        if self.target_active:
            self.alpha = min(255, self.alpha + speed * 40 * dt)
            self.scale = min(1.0, self.scale + speed * dt)
        else:
            # Close twice as fast as opening so it disappears immediately
            self.alpha = max(0, self.alpha - speed * 80 * dt)
            self.scale = max(0.8, self.scale - speed * 2 * dt)
            if self.alpha <= 0:
                self.active = False

        if not self.active:
            return

        # Hover detection
        self._save_hover = self.save_rect.collidepoint(mouse_pos)
        self._cancel_hover = self.cancel_rect.collidepoint(mouse_pos)
        self._close_hover = self.close_btn_rect.collidepoint(mouse_pos)
        self._upload_hover = self.upload_rect.collidepoint(mouse_pos)

        col1_x = self.rect.x + 40
        self.pen_rect = pygame.Rect(col1_x + 190, self.rect.y + 250, 30, 30)
        self._pen_hover = self.pen_rect.collidepoint(mouse_pos)

        self.hovered_avatar_idx = -1
        if self.view_mode == "edit":
            grid_cols = 3
            grid_start_x = self.rect.x + 360
            grid_start_y = self.rect.y + 260

            for idx in range(min(6, len(self.avatars))):
                row = idx // grid_cols
                col = idx % grid_cols
                ax = grid_start_x + col * 80
                ay = grid_start_y + row * 80
                if pygame.Rect(ax, ay, 70, 70).collidepoint(mouse_pos):
                    self.hovered_avatar_idx = idx
                    break

    def handle_event(self, event):
        if not self.active or not self.target_active:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.close_btn_rect.collidepoint(event.pos):
                self.close()
                return {"type": "cancel"}

            if self.view_mode == "view":
                if self.pen_rect.collidepoint(event.pos):
                    self.view_mode = "edit"
                    return None
            
            elif self.view_mode == "edit":
                if self.save_rect.collidepoint(event.pos):
                    self.view_mode = "view"
                    self.player_name = self.temp_name
                    return {"type": "save", "name": self.temp_name, "avatar_idx": self.selected_avatar_idx}

                if self.cancel_rect.collidepoint(event.pos):
                    self.view_mode = "view"
                    self.temp_name = self.player_name # Revert
                    return None

                if self.upload_rect.collidepoint(event.pos):
                    self._handle_upload()

                # Name Input collision
                name_box_rect = pygame.Rect(self.rect.x + 40, self.rect.y + 255, 220, 40)
                if name_box_rect.collidepoint(event.pos):
                    self.editing_name = True
                else:
                    self.editing_name = False

                if self.hovered_avatar_idx != -1:
                    self.selected_avatar_idx = self.hovered_avatar_idx

        if event.type == pygame.KEYDOWN and self.editing_name and self.view_mode == "edit":
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

    def _draw_gradient_btn(self, surface, rect, label, color_top, color_bot, is_hovered, icon=""):
        bw, bh = rect.w, rect.h
        br = self._btn_radius
        btn = pygame.Surface((bw, bh), pygame.SRCALPHA)

        for row in range(bh):
            t = row / bh
            r = int(color_top[0] + (color_bot[0] - color_top[0]) * t)
            g = int(color_top[1] + (color_bot[1] - color_top[1]) * t)
            b = int(color_top[2] + (color_bot[2] - color_top[2]) * t)
            pygame.draw.line(btn, (r, g, b, 235), (0, row), (bw, row))

        mask = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, bw, bh), border_radius=br)
        btn.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        shine = pygame.Surface((bw, bh // 3), pygame.SRCALPHA)
        pygame.draw.rect(shine, (255, 255, 255, 35 if not is_hovered else 55), (0, 0, bw, bh // 3), border_radius=br)
        btn.blit(shine, (0, 0))

        border_a = 80 if not is_hovered else 150
        pygame.draw.rect(btn, (255, 255, 255, border_a), (0, 0, bw, bh), width=2, border_radius=br)

        shadow = pygame.Surface((bw + 6, bh + 6), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 45), (0, 0, bw + 6, bh + 6), border_radius=br + 3)
        surface.blit(shadow, (rect.x - 3, rect.y - 1))

        if is_hovered:
            hglow = pygame.Surface((bw + 10, bh + 10), pygame.SRCALPHA)
            pygame.draw.rect(hglow, (*color_top, 35), (0, 0, bw + 10, bh + 10), border_radius=br + 5)
            surface.blit(hglow, (rect.x - 5, rect.y - 5))

        surface.blit(btn, rect.topleft)

        full_text = f"{icon}  {label}" if icon else label
        txt = self.font_btn.render(full_text, True, (255, 255, 255))
        txt_rect = txt.get_rect(center=rect.center)
        surface.blit(txt, txt_rect)

    def draw(self, surface):
        if not self.active:
            return

        # 1. Frosted blur backdrop (captured once when opened)
        if self._blurred_bg is None:
            self._blurred_bg = blur_surface(surface.copy(), factor=6, tint=(10, 8, 20), tint_alpha=180)

        ease = min(self.alpha / 255.0, 1.0)
        blur_alpha = int(255 * ease)
        if blur_alpha >= 250:
            surface.blit(self._blurred_bg, (0, 0))
        else:
            temp = self._blurred_bg.copy()
            temp.set_alpha(blur_alpha)
            surface.blit(temp, (0, 0))

        # 2. Modal Surface with Scale Animation
        modal_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)

        # Gradient background
        for row in range(self.rect.h):
            t = row / self.rect.h
            r = int(15 + 15 * t)
            g = int(18 + 12 * t)
            b = int(35 + 20 * t)
            a = int(min(self.alpha, 248) * 0.96)
            pygame.draw.line(modal_surf, (r, g, b, a), (0, row), (self.rect.w, row))

        # Round mask
        mask = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, self.rect.w, self.rect.h), border_radius=28)
        modal_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # Border
        pygame.draw.rect(modal_surf, (218, 175, 50, 120), (0, 0, self.rect.w, self.rect.h), width=2, border_radius=28)

        # --- Header ---
        title_str = "PLAYER PROFILE" if self.view_mode == "view" else "EDIT PROFILE"
        title_surf = self.font_modal_title.render(title_str, True, Colors.TEXT_GOLD)
        modal_surf.blit(title_surf, (self.rect.w // 2 - title_surf.get_width() // 2, 20))
        pygame.draw.line(modal_surf, (255, 255, 255, 20), (25, 65), (self.rect.w - 25, 65), 1)

        # Apply scaling and final blit
        if self.scale < 1.0:
            final_surf = pygame.transform.smoothscale(modal_surf, (int(self.rect.w * self.scale), int(self.rect.h * self.scale)))
            off_x = (self.rect.w - final_surf.get_width()) // 2
            off_y = (self.rect.h - final_surf.get_height()) // 2
            surface.blit(final_surf, (self.rect.x + off_x, self.rect.y + off_y))
            return
        else:
            surface.blit(modal_surf, self.rect.topleft)

        # Content (Drawn directly on surface for simplicity with global rects)
        px, py = self.rect.x, self.rect.y

        # Close "X" Button
        close_color = (180, 50, 50) if self._close_hover else (120, 40, 40)
        pygame.draw.circle(surface, close_color, self.close_btn_rect.center, 16)
        x_surf = self.font_small.render("X", True, (255, 255, 255))
        surface.blit(x_surf, (self.close_btn_rect.centerx - x_surf.get_width() // 2, self.close_btn_rect.centery - x_surf.get_height() // 2))

        # ================= LEFT COLUMN (Profile & Rank) =================
        col1_x = px + 40
        
        # 1. Large Selected Avatar
        if self.selected_avatar_idx < len(self.avatars):
            av = self.avatars[self.selected_avatar_idx]
            # Scale up for profile view
            av_large = pygame.transform.smoothscale(av, (120, 120))
            surface.blit(av_large, (col1_x + 50, py + 90))
            
        # 2. Name
        if self.view_mode == "view":
            txt_surf = self.font_body.render(self.player_name, True, Colors.TEXT_WHITE)
            surface.blit(txt_surf, (col1_x, py + 255))
            
            # Pen Icon
            pygame.draw.circle(surface, (60, 65, 85), self.pen_rect.center, 15)
            if self._pen_hover:
                pygame.draw.circle(surface, Colors.TEXT_GOLD, self.pen_rect.center, 15, 1)
            # Draw pencil
            cx, cy = self.pen_rect.center
            pygame.draw.line(surface, (220, 220, 220), (cx - 5, cy + 5), (cx + 5, cy - 5), 2)
            pygame.draw.polygon(surface, (220, 220, 220), [(cx + 3, cy - 7), (cx + 7, cy - 3), (cx + 7, cy - 7)])
            
            # 3. Rank Badge & RP (Only in view mode)
            from ui.assets_mgr import get_rank_badge
            rank_str = self.stats.get('rank', 'Wood')
            badge_surf = get_rank_badge(rank_str, "large")
            badge_surf = pygame.transform.smoothscale(badge_surf, (80, 80))
            surface.blit(badge_surf, (col1_x + 70, py + 310))
            
            rp = self.stats.get('rp', 0)
            rp_surf = self.font_body.render(f"{rank_str} - {rp} RP", True, (220, 220, 230))
            surface.blit(rp_surf, (col1_x + 110 - rp_surf.get_width()//2, py + 400))
            
        else:
            # Edit Mode Name Input
            name_label = self.font_small.render("DISPLAY NAME", True, (160, 160, 180))
            surface.blit(name_label, (col1_x, py + 230))
            
            box_w, box_h = 220, 40
            box_y = py + 255
            box_color = (30, 35, 55, 200) if not self.editing_name else (40, 50, 85, 230)
            pygame.draw.rect(surface, box_color, (col1_x, box_y, box_w, box_h), border_radius=10)
            border_col = Colors.TEXT_GOLD if self.editing_name else (70, 75, 95)
            pygame.draw.rect(surface, border_col, (col1_x, box_y, box_w, box_h), width=1, border_radius=10)
            
            cursor = "|" if (time.time() * 2 % 2 < 1 and self.editing_name) else ""
            txt_surf = self.font_body.render(self.temp_name + cursor, True, Colors.TEXT_WHITE)
            surface.blit(txt_surf, (col1_x + 10, box_y + box_h // 2 - txt_surf.get_height() // 2))

        # ================= RIGHT COLUMN (Stats & Grid) =================
        col2_x = px + 360
        
        if self.view_mode == "view":
            # 1. Game Stats
            stats_label = self.font_small.render("GAME STATS", True, (160, 160, 180))
            surface.blit(stats_label, (col2_x, py + 90))
            
            wins = self.stats.get('wins', 0)
            losses = self.stats.get('losses', 0)
            win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
            streak = self.stats.get('streak', 3)
            biggest_win = self.stats.get('biggest_win', 5000)
            
            stats_data = [
                f"Wins: {wins}",
                f"Losses: {losses}",
                f"Win Rate: {win_rate:.1f}%",
                f"Current Streak: {streak}",
                f"Biggest Win: {biggest_win} Coins"
            ]
            
            sy = py + 115
            for s in stats_data:
                s_surf = self.font_body.render(s, True, (210, 210, 220))
                surface.blit(s_surf, (col2_x, sy))
                sy += 25
        else:
            # 2. Avatar Selection Grid (Smaller)
            grid_label = self.font_small.render("SELECT AVATAR", True, (160, 160, 180))
            surface.blit(grid_label, (col2_x, py + 235))
            
            grid_cols = 3
            grid_start_y = py + 260
            
            for idx in range(min(6, len(self.avatars))):
                row = idx // grid_cols
                col = idx % grid_cols
                ax = col2_x + col * 80
                ay = grid_start_y + row * 80
                
                if idx == self.selected_avatar_idx or idx == self.hovered_avatar_idx:
                    glow_color = Colors.TEXT_GOLD if idx == self.selected_avatar_idx else (200, 200, 220)
                    pygame.draw.circle(surface, glow_color, (ax + 35, ay + 35), 38, width=2)
                    
                # Scale avatar down for grid
                av_small = pygame.transform.smoothscale(self.avatars[idx], (70, 70))
                surface.blit(av_small, (ax, ay))
                
            # 3. Upload Button
            upload_rect = pygame.Rect(col2_x, py + 425, 240, 36)
            self._draw_gradient_btn(
                surface, upload_rect, "UPLOAD CUSTOM",
                (55, 60, 80), (40, 45, 65), self._upload_hover, "+"
            )

        # Action Buttons (Only in edit mode)
        if self.view_mode == "edit":
            self._draw_gradient_btn(
                surface, self.save_rect, "SAVE",
                (50, 180, 90), (30, 130, 60), self._save_hover, ""
            )
            self._draw_gradient_btn(
                surface, self.cancel_rect, "CANCEL",
                (180, 55, 55), (130, 35, 35), self._cancel_hover, ""
            )
