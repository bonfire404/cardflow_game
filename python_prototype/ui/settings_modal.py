import pygame
import os
import math
from ui.paths import get_resource_path
from ui.ui_components import Colors, blur_surface


class SettingsModal:
    """Premium tabbed settings modal with Audio, About, and Legal sections."""

    # ── Tab Constants ──
    TAB_AUDIO = 0
    TAB_ABOUT = 1
    TAB_LEGAL = 2
    TAB_NAMES = ["Audio", "About", "Legal"]

    # ── TOS / Privacy Text ──
    TOS_TEXT = [
        "TERMS OF SERVICE",
        "",
        "Last Updated: May 2026",
        "",
        "1. ACCEPTANCE OF TERMS",
        "By accessing and playing CardFlow, you acknowledge",
        "that this game is an academic project developed for",
        "CPROG 2 (Computer Programming 2) and agree to",
        "these terms.",
        "",
        "2. ACADEMIC PURPOSE",
        "CardFlow is a non-commercial, educational project",
        "created as a course requirement. It is not intended",
        "for commercial distribution or monetary gain.",
        "",
        "3. GAME CURRENCY",
        "All in-game currency (coins, chips) is virtual and",
        "holds no real-world monetary value. No real money",
        "is involved in any transaction within this game.",
        "",
        "4. NO WARRANTY",
        "This software is provided 'as is' without warranty",
        "of any kind. The developers are not liable for any",
        "damages arising from the use of this software.",
        "",
        "5. INTELLECTUAL PROPERTY",
        "All original code, assets, and design elements are",
        "the property of the development team. Third-party",
        "assets are used under their respective licenses.",
        "",
        "6. FAIR USE",
        "This project incorporates educational fair-use",
        "principles for any referenced materials.",
    ]

    PRIVACY_TEXT = [
        "PRIVACY POLICY",
        "",
        "Last Updated: May 2026",
        "",
        "1. DATA COLLECTION",
        "CardFlow does NOT collect, transmit, or share any",
        "personal data. All game data is stored locally on",
        "your device only.",
        "",
        "2. LOCAL STORAGE",
        "Player profiles, settings, and game progress are",
        "saved in a local SQLite database and JSON files",
        "on your computer. No cloud services are used.",
        "",
        "3. NO ANALYTICS",
        "This game does not use any analytics, tracking,",
        "or telemetry services. Your gameplay is entirely",
        "private.",
        "",
        "4. NO NETWORK ACCESS",
        "CardFlow operates entirely offline. No internet",
        "connection is required or used at any point.",
        "",
        "5. CONTACT",
        "For questions about this project, contact",
        "BONFIRE BASE at bonfire@base69.studio",
        "or visit https://bonfire.base69.studio",
    ]

    def __init__(self, font_title, font_body, font_small, set_bgm_callback=None, set_sfx_callback=None, toggle_fullscreen_callback=None):
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = font_small
        self.is_open = False

        # Modal dimensions (larger for tabbed layout)
        self.rect = pygame.Rect(0, 0, 750, 560)
        self.alpha = 0
        self._blurred_bg = None
        self.time_alive = 0.0

        # Load Sekuya for modal title
        _sekuya_path = get_resource_path(os.path.join("assets", "fonts", "Sekuya", "Sekuya-Regular.ttf"))
        try:
            self.font_modal_title = pygame.font.Font(_sekuya_path, 34)
            self.font_tab = pygame.font.Font(_sekuya_path, 18)
        except Exception:
            self.font_modal_title = self.font_title
            self.font_tab = self.font_body

        self.close_btn_rect = pygame.Rect(0, 0, 30, 30)

        self.set_bgm_callback = set_bgm_callback
        self.set_sfx_callback = set_sfx_callback

        # Volume states (0.0 to 1.0)
        self.bgm_volume = 0.5
        self.sfx_volume = 0.5
        self._prev_bgm_volume = 0.5  # For mute restore
        self._prev_sfx_volume = 0.5

        self.is_dragging_bgm = False
        self.is_dragging_sfx = False

        # Slider positions
        self.slider_w = 340
        self.slider_h = 10
        self.bgm_slider_rect = pygame.Rect(0, 0, self.slider_w, self.slider_h)
        self.sfx_slider_rect = pygame.Rect(0, 0, self.slider_w, self.slider_h)

        # Mute toggle button rects
        self.bgm_mute_rect = pygame.Rect(0, 0, 36, 36)
        self.sfx_mute_rect = pygame.Rect(0, 0, 36, 36)

        # Tab state
        self.active_tab = self.TAB_AUDIO
        self.tab_rects = []
        self.tab_underline_x = 0.0  # Animated underline position
        self.tab_underline_target_x = 0.0

        # Legal tab scroll
        self.legal_scroll = 0
        self.legal_max_scroll = 0

        # Load Icons
        try:
            cross_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "cross.png"))
            self.icon_close = pygame.image.load(cross_path).convert_alpha()
            self.icon_close = pygame.transform.smoothscale(self.icon_close, (16, 16))
        except Exception:
            self.icon_close = None

        # Load speaker icons
        try:
            speaker_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "musicOn.png"))
            self.icon_speaker_on = pygame.image.load(speaker_path).convert_alpha()
            self.icon_speaker_on = pygame.transform.smoothscale(self.icon_speaker_on, (20, 20))
        except Exception:
            self.icon_speaker_on = None

        try:
            mute_path = get_resource_path(os.path.join("assets", "game_icons", "PNG", "White", "2x", "musicOff.png"))
            self.icon_speaker_off = pygame.image.load(mute_path).convert_alpha()
            self.icon_speaker_off = pygame.transform.smoothscale(self.icon_speaker_off, (20, 20))
        except Exception:
            self.icon_speaker_off = None

        # Display mode selector
        self.DISPLAY_MODES = [
            {"label": "FULLSCREEN", "size": None, "fullscreen": True},
            {"label": "1280 x 720", "size": (1280, 720), "fullscreen": False},
            {"label": "1024 x 576", "size": (1024, 576), "fullscreen": False},
            {"label": "960 x 540", "size": (960, 540), "fullscreen": False},
        ]
        self.active_display_idx = 0  # Starts fullscreen
        self.toggle_fullscreen_callback = toggle_fullscreen_callback
        self.display_btn_rect = pygame.Rect(0, 0, 200, 40)
        self.display_prev_rect = pygame.Rect(0, 0, 30, 30)
        self.display_next_rect = pygame.Rect(0, 0, 30, 30)

    def open(self, bgm_volume=None, sfx_volume=None):
        """Open modal. Pass persisted volumes from AudioManager."""
        self.is_open = True
        self.alpha = 0
        self.time_alive = 0.0
        self._blurred_bg = None
        self.active_tab = self.TAB_AUDIO
        self.legal_scroll = 0

        # Use passed-in persisted volumes (from AudioManager) instead of channel state
        if bgm_volume is not None:
            self.bgm_volume = bgm_volume
        if sfx_volume is not None:
            self.sfx_volume = sfx_volume

        # Store for mute restore
        if self.bgm_volume > 0.01:
            self._prev_bgm_volume = self.bgm_volume
        if self.sfx_volume > 0.01:
            self._prev_sfx_volume = self.sfx_volume

    def close(self):
        self.is_open = False
        self.is_dragging_bgm = False
        self.is_dragging_sfx = False

    def _toggle_mute_bgm(self):
        """Toggle BGM mute on/off."""
        if self.bgm_volume > 0.01:
            self._prev_bgm_volume = self.bgm_volume
            self.bgm_volume = 0.0
        else:
            self.bgm_volume = self._prev_bgm_volume if self._prev_bgm_volume > 0.01 else 0.5
        self.apply_volumes()

    def _toggle_mute_sfx(self):
        """Toggle SFX mute on/off."""
        if self.sfx_volume > 0.01:
            self._prev_sfx_volume = self.sfx_volume
            self.sfx_volume = 0.0
        else:
            self.sfx_volume = self._prev_sfx_volume if self._prev_sfx_volume > 0.01 else 0.5
        self.apply_volumes()

    def handle_event(self, event):
        if not self.is_open:
            return False

        bounce = math.sin(self.time_alive * 6) * max(0, 1.0 - self.time_alive * 3) * 20
        screen_y = self.rect.y + int(bounce)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rel_pos = (event.pos[0] - self.rect.x, event.pos[1] - screen_y)

            # Close button
            if self.close_btn_rect.collidepoint(rel_pos):
                self.close()
                return True

            # Tab clicks
            for i, tr in enumerate(self.tab_rects):
                if tr.collidepoint(rel_pos):
                    self.active_tab = i
                    self.legal_scroll = 0
                    return True

            if self.active_tab == self.TAB_AUDIO:
                # Mute toggle buttons (absolute coords)
                if self.bgm_mute_rect.collidepoint(event.pos):
                    self._toggle_mute_bgm()
                    return True
                if self.sfx_mute_rect.collidepoint(event.pos):
                    self._toggle_mute_sfx()
                    return True

                # BGM slider
                bgm_knob_x = self.bgm_slider_rect.x + int(self.bgm_volume * self.slider_w)
                bgm_knob_rect = pygame.Rect(bgm_knob_x - 12, self.bgm_slider_rect.centery - 12, 24, 24)
                if bgm_knob_rect.collidepoint(event.pos):
                    self.is_dragging_bgm = True
                    return True

                # SFX slider
                sfx_knob_x = self.sfx_slider_rect.x + int(self.sfx_volume * self.slider_w)
                sfx_knob_rect = pygame.Rect(sfx_knob_x - 12, self.sfx_slider_rect.centery - 12, 24, 24)
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

                # Display mode arrows
                if self.display_prev_rect.collidepoint(event.pos):
                    self.active_display_idx = (self.active_display_idx - 1) % len(self.DISPLAY_MODES)
                    self._apply_display_mode()
                    return True
                if self.display_next_rect.collidepoint(event.pos):
                    self.active_display_idx = (self.active_display_idx + 1) % len(self.DISPLAY_MODES)
                    self._apply_display_mode()
                    return True
                # Click on the display label area also cycles forward
                if self.display_btn_rect.collidepoint(event.pos):
                    self.active_display_idx = (self.active_display_idx + 1) % len(self.DISPLAY_MODES)
                    self._apply_display_mode()
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

        # Scroll for legal tab
        if self.active_tab == self.TAB_LEGAL:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up
                    self.legal_scroll = max(0, self.legal_scroll - 30)
                    return True
                elif event.button == 5:  # Scroll down
                    self.legal_scroll = min(self.legal_max_scroll, self.legal_scroll + 30)
                    return True

        if hasattr(event, 'pos'):
            return self.rect.collidepoint(event.pos)
        return False

    def apply_volumes(self):
        if self.set_bgm_callback:
            self.set_bgm_callback(self.bgm_volume)
        if self.set_sfx_callback:
            self.set_sfx_callback(self.sfx_volume)

    def _apply_display_mode(self):
        """Fire the display mode callback with current mode info."""
        mode = self.DISPLAY_MODES[self.active_display_idx]
        if self.toggle_fullscreen_callback:
            self.toggle_fullscreen_callback(mode["fullscreen"], mode["size"])

    def update(self, dt, mouse_pos):
        if not self.is_open:
            return
        self.time_alive += dt
        if self.alpha < 255:
            self.alpha = min(255, self.alpha + 15)

        # Animate tab underline
        if self.tab_rects:
            target_rect = self.tab_rects[self.active_tab]
            self.tab_underline_target_x = target_rect.x
            self.tab_underline_x += (self.tab_underline_target_x - self.tab_underline_x) * min(1.0, dt * 12)

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

        # Create Modal Surface
        modal_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)

        # Gradient background
        for row in range(self.rect.h):
            t = row / self.rect.h
            r = int(15 + 15 * t)
            g = int(18 + 12 * t)
            b = int(35 + 20 * t)
            a = 245
            pygame.draw.line(modal_surf, (r, g, b, a), (0, row), (self.rect.w, row))

        # Round mask
        mask = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, self.rect.w, self.rect.h), border_radius=28)
        modal_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # Border
        pygame.draw.rect(modal_surf, (218, 175, 50, 120), (0, 0, self.rect.w, self.rect.h), width=2, border_radius=28)

        # ── Header ──
        title_surf = self.font_modal_title.render("GAME SETTINGS", True, Colors.TEXT_GOLD)
        modal_surf.blit(title_surf, (self.rect.w // 2 - title_surf.get_width() // 2, 18))

        # Close Button
        self.close_btn_rect.topright = (self.rect.w - 20, 18)
        mouse_pos = pygame.mouse.get_pos()
        close_rel = (mouse_pos[0] - self.rect.x, mouse_pos[1] - screen_y)
        close_hover = self.close_btn_rect.collidepoint(close_rel)
        close_color = (220, 50, 50) if close_hover else (180, 40, 40)
        pygame.draw.circle(modal_surf, close_color, self.close_btn_rect.center, 15)
        if self.icon_close:
            modal_surf.blit(self.icon_close, (self.close_btn_rect.centerx - 8, self.close_btn_rect.centery - 8))

        # ── Tab Bar ──
        tab_y = 60
        tab_w = 140
        tab_gap = 10
        total_tab_w = len(self.TAB_NAMES) * tab_w + (len(self.TAB_NAMES) - 1) * tab_gap
        tab_start_x = self.rect.w // 2 - total_tab_w // 2

        self.tab_rects = []
        for i, name in enumerate(self.TAB_NAMES):
            tx = tab_start_x + i * (tab_w + tab_gap)
            tr = pygame.Rect(tx, tab_y, tab_w, 32)
            self.tab_rects.append(tr)

            is_active = (self.active_tab == i)
            tab_rel = (mouse_pos[0] - self.rect.x, mouse_pos[1] - screen_y)
            is_hover = tr.collidepoint(tab_rel) and not is_active

            if is_active:
                tc = Colors.TEXT_GOLD
            elif is_hover:
                tc = (200, 200, 210)
            else:
                tc = (140, 140, 160)

            tab_txt = self.font_tab.render(name.upper(), True, tc)
            modal_surf.blit(tab_txt, (tr.centerx - tab_txt.get_width() // 2, tr.centery - tab_txt.get_height() // 2))

        # Animated gold underline
        active_tr = self.tab_rects[self.active_tab]
        underline_x = self.tab_underline_x
        pygame.draw.rect(modal_surf, Colors.TEXT_GOLD, (int(underline_x), tab_y + 34, tab_w, 3), border_radius=2)

        # Separator line under tabs
        pygame.draw.line(modal_surf, (255, 255, 255, 20), (25, tab_y + 40), (self.rect.w - 25, tab_y + 40), 1)

        # ── Content Area ──
        content_y = tab_y + 50
        cx = 50

        if self.active_tab == self.TAB_AUDIO:
            self._draw_audio_tab(modal_surf, screen, cx, content_y, screen_y)
        elif self.active_tab == self.TAB_ABOUT:
            self._draw_about_tab(modal_surf, cx, content_y)
        elif self.active_tab == self.TAB_LEGAL:
            self._draw_legal_tab(modal_surf, cx, content_y)

        # Version - bottom right
        version_surf = self.font_small.render("v1.0.1", True, (100, 105, 120))
        modal_surf.blit(version_surf, (self.rect.w - version_surf.get_width() - 30, self.rect.h - version_surf.get_height() - 18))

        # Blit modal to screen
        screen.blit(modal_surf, (self.rect.x, screen_y))

    def _draw_audio_tab(self, modal_surf, screen, cx, content_y, screen_y):
        """Draw Audio settings: BGM/SFX sliders with mute toggles and percentage."""
        mouse_pos = pygame.mouse.get_pos()

        # ── Section: Music Volume ──
        section_y = content_y + 10

        # Section header with icon indicator
        header_color = Colors.TEXT_GOLD
        bgm_label = self.font_body.render("Music Volume", True, (255, 255, 255))
        modal_surf.blit(bgm_label, (cx, section_y))

        # Percentage display
        bgm_pct = f"{int(self.bgm_volume * 100)}%"
        pct_surf = self.font_small.render(bgm_pct, True, Colors.TEXT_GOLD)
        modal_surf.blit(pct_surf, (cx + self.slider_w + 120, section_y + 42))

        # Mute toggle button (absolute screen coords for hit detection)
        mute_btn_local_x = cx
        mute_btn_local_y = section_y + 36
        self.bgm_mute_rect.x = self.rect.x + mute_btn_local_x
        self.bgm_mute_rect.y = screen_y + mute_btn_local_y

        bgm_muted = self.bgm_volume <= 0.01
        mute_hover = self.bgm_mute_rect.collidepoint(mouse_pos)
        mute_bg = (60, 40, 40) if bgm_muted else ((60, 65, 80) if mute_hover else (35, 40, 55))
        pygame.draw.rect(modal_surf, mute_bg, (mute_btn_local_x, mute_btn_local_y, 36, 36), border_radius=8)
        pygame.draw.rect(modal_surf, (255, 255, 255, 40), (mute_btn_local_x, mute_btn_local_y, 36, 36), width=1, border_radius=8)

        # Speaker icon or fallback text
        icon = self.icon_speaker_off if bgm_muted else self.icon_speaker_on
        if icon:
            modal_surf.blit(icon, (mute_btn_local_x + 8, mute_btn_local_y + 8))
        else:
            sym = "🔇" if bgm_muted else "🔊"
            sym_surf = self.font_small.render("M" if bgm_muted else "♪", True, (255, 80, 80) if bgm_muted else (255, 255, 255))
            modal_surf.blit(sym_surf, (mute_btn_local_x + 10, mute_btn_local_y + 8))

        # BGM Slider
        slider_local_x = cx + 50
        slider_local_y = section_y + 45
        self.bgm_slider_rect.x = self.rect.x + slider_local_x
        self.bgm_slider_rect.y = screen_y + slider_local_y

        # Track background
        pygame.draw.rect(modal_surf, (30, 35, 55), (slider_local_x, slider_local_y, self.slider_w, self.slider_h), border_radius=self.slider_h // 2)

        # Filled portion
        bgm_fill_w = int(self.slider_w * self.bgm_volume)
        if bgm_fill_w > 0:
            # Gradient fill effect
            fill_surf = pygame.Surface((bgm_fill_w, self.slider_h), pygame.SRCALPHA)
            for col in range(bgm_fill_w):
                t = col / max(1, self.slider_w)
                r = int(180 + 75 * t)
                g = int(140 + 75 * t)
                b = int(20 + 30 * t)
                pygame.draw.line(fill_surf, (r, g, b, 255), (col, 0), (col, self.slider_h))
            mask_s = pygame.Surface((bgm_fill_w, self.slider_h), pygame.SRCALPHA)
            pygame.draw.rect(mask_s, (255, 255, 255, 255), (0, 0, bgm_fill_w, self.slider_h), border_radius=self.slider_h // 2)
            fill_surf.blit(mask_s, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            modal_surf.blit(fill_surf, (slider_local_x, slider_local_y))

        # Knob with glow
        knob_x = slider_local_x + bgm_fill_w
        knob_cy = slider_local_y + self.slider_h // 2
        # Glow
        glow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 215, 50, 40), (15, 15), 15)
        modal_surf.blit(glow_surf, (knob_x - 15, knob_cy - 15))
        # Knob
        pygame.draw.circle(modal_surf, (255, 255, 255), (knob_x, knob_cy), 10)
        pygame.draw.circle(modal_surf, Colors.TEXT_GOLD, (knob_x, knob_cy), 7)

        # ── Section: Sound Effects ──
        section_y2 = section_y + 100

        sfx_label = self.font_body.render("Sound Effects", True, (255, 255, 255))
        modal_surf.blit(sfx_label, (cx, section_y2))

        # Percentage display
        sfx_pct = f"{int(self.sfx_volume * 100)}%"
        pct_surf2 = self.font_small.render(sfx_pct, True, Colors.TEXT_GOLD)
        modal_surf.blit(pct_surf2, (cx + self.slider_w + 120, section_y2 + 42))

        # Mute toggle button
        mute2_local_x = cx
        mute2_local_y = section_y2 + 36
        self.sfx_mute_rect.x = self.rect.x + mute2_local_x
        self.sfx_mute_rect.y = screen_y + mute2_local_y

        sfx_muted = self.sfx_volume <= 0.01
        mute2_hover = self.sfx_mute_rect.collidepoint(mouse_pos)
        mute2_bg = (60, 40, 40) if sfx_muted else ((60, 65, 80) if mute2_hover else (35, 40, 55))
        pygame.draw.rect(modal_surf, mute2_bg, (mute2_local_x, mute2_local_y, 36, 36), border_radius=8)
        pygame.draw.rect(modal_surf, (255, 255, 255, 40), (mute2_local_x, mute2_local_y, 36, 36), width=1, border_radius=8)

        icon2 = self.icon_speaker_off if sfx_muted else self.icon_speaker_on
        if icon2:
            modal_surf.blit(icon2, (mute2_local_x + 8, mute2_local_y + 8))
        else:
            sym_surf2 = self.font_small.render("M" if sfx_muted else "♪", True, (255, 80, 80) if sfx_muted else (255, 255, 255))
            modal_surf.blit(sym_surf2, (mute2_local_x + 10, mute2_local_y + 8))

        # SFX Slider
        slider2_local_x = cx + 50
        slider2_local_y = section_y2 + 45
        self.sfx_slider_rect.x = self.rect.x + slider2_local_x
        self.sfx_slider_rect.y = screen_y + slider2_local_y

        pygame.draw.rect(modal_surf, (30, 35, 55), (slider2_local_x, slider2_local_y, self.slider_w, self.slider_h), border_radius=self.slider_h // 2)

        sfx_fill_w = int(self.slider_w * self.sfx_volume)
        if sfx_fill_w > 0:
            fill_surf2 = pygame.Surface((sfx_fill_w, self.slider_h), pygame.SRCALPHA)
            for col in range(sfx_fill_w):
                t = col / max(1, self.slider_w)
                r = int(180 + 75 * t)
                g = int(140 + 75 * t)
                b = int(20 + 30 * t)
                pygame.draw.line(fill_surf2, (r, g, b, 255), (col, 0), (col, self.slider_h))
            mask_s2 = pygame.Surface((sfx_fill_w, self.slider_h), pygame.SRCALPHA)
            pygame.draw.rect(mask_s2, (255, 255, 255, 255), (0, 0, sfx_fill_w, self.slider_h), border_radius=self.slider_h // 2)
            fill_surf2.blit(mask_s2, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            modal_surf.blit(fill_surf2, (slider2_local_x, slider2_local_y))

        knob2_x = slider2_local_x + sfx_fill_w
        knob2_cy = slider2_local_y + self.slider_h // 2
        glow_surf2 = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf2, (255, 215, 50, 40), (15, 15), 15)
        modal_surf.blit(glow_surf2, (knob2_x - 15, knob2_cy - 15))
        pygame.draw.circle(modal_surf, (255, 255, 255), (knob2_x, knob2_cy), 10)
        pygame.draw.circle(modal_surf, Colors.TEXT_GOLD, (knob2_x, knob2_cy), 7)

        # ── Audio Info Hint ──
        hint_y = section_y2 + 115
        pygame.draw.line(modal_surf, (255, 255, 255, 15), (cx, hint_y), (self.rect.w - cx, hint_y), 1)
        hint_text = self.font_small.render("Audio settings are saved automatically.", True, (120, 125, 140))
        modal_surf.blit(hint_text, (cx, hint_y + 10))

        # ── Fullscreen / Display Mode Selector ──
        fs_y = hint_y + 40
        fs_label = self.font_body.render("Display Mode", True, (255, 255, 255))
        modal_surf.blit(fs_label, (cx, fs_y))

        # Current mode display with left/right arrows
        mode_info = self.DISPLAY_MODES[self.active_display_idx]
        mode_label = mode_info["label"]
        is_fs = mode_info["fullscreen"]

        row_y = fs_y + 34
        row_h = 38
        row_w = 300

        # Container
        pygame.draw.rect(modal_surf, (28, 32, 50), (cx, row_y, row_w, row_h), border_radius=10)
        pygame.draw.rect(modal_surf, (255, 255, 255, 30), (cx, row_y, row_w, row_h), width=1, border_radius=10)

        # Left arrow "<"
        arrow_w = 30
        left_arrow_x = cx
        self.display_prev_rect.x = self.rect.x + left_arrow_x
        self.display_prev_rect.y = screen_y + row_y
        self.display_prev_rect.w = arrow_w
        self.display_prev_rect.h = row_h

        prev_hover = self.display_prev_rect.collidepoint(mouse_pos)
        prev_color = Colors.TEXT_GOLD if prev_hover else (180, 180, 195)
        prev_surf = self.font_body.render("◀", True, prev_color)
        modal_surf.blit(prev_surf, (left_arrow_x + 6, row_y + row_h // 2 - prev_surf.get_height() // 2))

        # Right arrow ">"
        right_arrow_x = cx + row_w - arrow_w
        self.display_next_rect.x = self.rect.x + right_arrow_x
        self.display_next_rect.y = screen_y + row_y
        self.display_next_rect.w = arrow_w
        self.display_next_rect.h = row_h

        next_hover = self.display_next_rect.collidepoint(mouse_pos)
        next_color = Colors.TEXT_GOLD if next_hover else (180, 180, 195)
        next_surf = self.font_body.render("▶", True, next_color)
        modal_surf.blit(next_surf, (right_arrow_x + 6, row_y + row_h // 2 - next_surf.get_height() // 2))

        # Center label area (clickable to cycle)
        label_x = cx + arrow_w
        label_w = row_w - arrow_w * 2
        self.display_btn_rect.x = self.rect.x + label_x
        self.display_btn_rect.y = screen_y + row_y
        self.display_btn_rect.w = label_w
        self.display_btn_rect.h = row_h

        # Status indicator dot
        dot_color = (80, 220, 100) if is_fs else (100, 180, 255)
        dot_cx = cx + arrow_w + 14
        dot_cy = row_y + row_h // 2
        pygame.draw.circle(modal_surf, dot_color, (dot_cx, dot_cy), 5)
        # Glow
        glow_s = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (*dot_color, 50), (9, 9), 9)
        modal_surf.blit(glow_s, (dot_cx - 9, dot_cy - 9))

        # Mode text
        mode_txt_color = (200, 255, 200) if is_fs else (180, 210, 255)
        mode_surf = self.font_body.render(mode_label, True, mode_txt_color)
        modal_surf.blit(mode_surf, (cx + row_w // 2 - mode_surf.get_width() // 2 + 5, row_y + row_h // 2 - mode_surf.get_height() // 2))

        # Sub-hint
        sub_hint = "Native resolution" if is_fs else "Windowed mode"
        sub_surf = self.font_small.render(sub_hint, True, (100, 105, 120))
        modal_surf.blit(sub_surf, (cx, row_y + row_h + 6))

        # ── Branding at bottom of audio tab ──
        brand_y = self.rect.h - 60
        brand_txt1 = self.font_small.render("A ", True, (255, 255, 255))
        brand_txt2 = self.font_small.render("BONFIRE BASE", True, (255, 128, 0))
        brand_txt3 = self.font_small.render(" Studios Production", True, (255, 255, 255))
        modal_surf.blit(brand_txt1, (cx, brand_y))
        modal_surf.blit(brand_txt2, (cx + brand_txt1.get_width(), brand_y))
        modal_surf.blit(brand_txt3, (cx + brand_txt1.get_width() + brand_txt2.get_width(), brand_y))

    def _draw_about_tab(self, modal_surf, cx, content_y):
        """Draw About tab: Credits, branding, version."""
        # Credits Title
        credits_title = self.font_body.render("Development Team", True, Colors.TEXT_GOLD)
        modal_surf.blit(credits_title, (cx, content_y + 5))

        # Separator
        pygame.draw.line(modal_surf, (255, 215, 50, 40), (cx, content_y + 35), (cx + 300, content_y + 35), 1)

        credits_data = [
            ("PROJECT MANAGER", "LOUISE JAN CARLO TABALDO"),
            ("LEAD DEVELOPER", "BON JURY PECAOCO"),
            ("GAME DESIGNER", "CHONA MAE GREGORIO"),
            ("GAME DESIGNER", "CRISTINA GERTOS"),
            ("TECHNICAL WRITER", "JAMAICA NAZARENO"),
        ]

        y_off = content_y + 50
        for role, name in credits_data:
            # Role (small gold)
            role_surf = self.font_small.render(role, True, (180, 160, 80))
            modal_surf.blit(role_surf, (cx + 10, y_off))
            # Name (white)
            name_surf = self.font_body.render(name, True, (230, 230, 240))
            modal_surf.blit(name_surf, (cx + 10, y_off + 18))
            y_off += 50

        # Separator
        pygame.draw.line(modal_surf, (255, 255, 255, 15), (cx, y_off + 5), (self.rect.w - cx, y_off + 5), 1)

        # Project Info
        y_off += 20
        proj_label = self.font_small.render("PROJECT", True, (180, 160, 80))
        modal_surf.blit(proj_label, (cx + 10, y_off))
        proj_val = self.font_body.render("CPROG 2 — Computer Programming 2", True, (230, 230, 240))
        modal_surf.blit(proj_val, (cx + 10, y_off + 18))

        # Branding
        brand_y = self.rect.h - 60
        brand_txt1 = self.font_small.render("A ", True, (255, 255, 255))
        brand_txt2 = self.font_small.render("BONFIRE BASE", True, (255, 128, 0))
        brand_txt3 = self.font_small.render(" Studios Production", True, (255, 255, 255))
        modal_surf.blit(brand_txt1, (cx, brand_y))
        modal_surf.blit(brand_txt2, (cx + brand_txt1.get_width(), brand_y))
        modal_surf.blit(brand_txt3, (cx + brand_txt1.get_width() + brand_txt2.get_width(), brand_y))

    def _draw_legal_tab(self, modal_surf, cx, content_y):
        """Draw Legal tab: TOS + Privacy Policy with scrolling."""
        # Combine TOS and Privacy with a separator
        combined_lines = self.TOS_TEXT + ["", "─" * 50, ""] + self.PRIVACY_TEXT

        # Content area dimensions
        content_x = cx
        content_w = self.rect.w - cx * 2
        content_h = self.rect.h - content_y - 70  # Leave room for scroll hint
        line_h = 20

        # Calculate max scroll
        total_content_h = len(combined_lines) * line_h
        self.legal_max_scroll = max(0, total_content_h - content_h)

        # Create clipping surface for scrollable content
        clip_surf = pygame.Surface((content_w, content_h), pygame.SRCALPHA)

        for i, line in enumerate(combined_lines):
            ly = i * line_h - self.legal_scroll
            if ly < -line_h or ly > content_h:
                continue

            # Style based on content
            if line.startswith("TERMS OF SERVICE") or line.startswith("PRIVACY POLICY"):
                color = Colors.TEXT_GOLD
                font = self.font_body
            elif line.startswith(("1.", "2.", "3.", "4.", "5.", "6.")):
                color = (200, 180, 80)
                font = self.font_small
            elif line.startswith("─"):
                # Draw separator line
                pygame.draw.line(clip_surf, (255, 255, 255, 30), (0, ly + line_h // 2), (content_w, ly + line_h // 2), 1)
                continue
            elif line == "":
                continue
            else:
                color = (190, 190, 200)
                font = self.font_small

            line_surf = font.render(line, True, color)
            clip_surf.blit(line_surf, (5, ly))

        modal_surf.blit(clip_surf, (content_x, content_y))

        # Scroll indicators
        if self.legal_max_scroll > 0:
            # Scrollbar track
            track_x = self.rect.w - 30
            track_y = content_y
            track_h = content_h

            pygame.draw.rect(modal_surf, (40, 45, 60), (track_x, track_y, 6, track_h), border_radius=3)

            # Scrollbar thumb
            thumb_h = max(30, int(track_h * (content_h / total_content_h)))
            scroll_ratio = self.legal_scroll / max(1, self.legal_max_scroll)
            thumb_y = track_y + int((track_h - thumb_h) * scroll_ratio)
            pygame.draw.rect(modal_surf, Colors.TEXT_GOLD, (track_x, thumb_y, 6, thumb_h), border_radius=3)

            # Scroll hint at bottom
            if self.legal_scroll < self.legal_max_scroll:
                hint = self.font_small.render("↓ Scroll for more", True, (120, 125, 140))
                modal_surf.blit(hint, (cx, self.rect.h - 55))
