import pygame
import math


def blur_surface(surf, factor=8, tint=(6, 10, 22), tint_alpha=200):
    """Fast frosted-glass blur: downscale → upscale + dark tint.
    Captures the current screen and returns a blurred, dimmed version."""
    w, h = surf.get_size()
    # Downscale then upscale for box blur effect
    small_w = max(1, w // factor)
    small_h = max(1, h // factor)
    small = pygame.transform.smoothscale(surf, (small_w, small_h))
    blurred = pygame.transform.smoothscale(small, (w, h))
    # Apply dark tint overlay
    tint_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    tint_surf.fill((*tint, tint_alpha))
    blurred.blit(tint_surf, (0, 0))
    # Add subtle vignette (darker edges)
    vignette = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(4):
        alpha = 40 - i * 10
        if alpha <= 0: break
        border = i * max(w, h) // 8
        pygame.draw.rect(vignette, (0, 0, 0, alpha), (0, 0, w, h), width=border)
    blurred.blit(vignette, (0, 0))
    return blurred


# ─── Color Palette ───────────────────────────────────────────────────

class Colors:
    # Table / Background
    TABLE_GREEN = (26, 92, 48)
    TABLE_FELT = (34, 110, 58)
    TABLE_DARK = (18, 65, 34)

    # UI Chrome
    PANEL_BG = (20, 20, 30, 200)
    PANEL_BORDER = (60, 60, 80)
    PANEL_HIGHLIGHT = (80, 140, 255)

    # Text
    TEXT_WHITE = (240, 240, 245)
    TEXT_GOLD = (255, 80, 80)  # Rebranded to Cardflow Red
    TEXT_MUTED = (160, 160, 175)
    TEXT_RED = (255, 80, 80)
    TEXT_GREEN = (80, 255, 120)

    # Buttons
    BTN_PRIMARY = (50, 120, 220)
    BTN_PRIMARY_HOVER = (70, 145, 255)
    BTN_DANGER = (200, 50, 50)
    BTN_DANGER_HOVER = (230, 70, 70)
    BTN_SUCCESS = (40, 160, 80)
    BTN_SUCCESS_HOVER = (55, 190, 100)
    BTN_DISABLED = (60, 60, 70)

    # Cards
    CARD_GLOW = (255, 60, 40, 120)  # Red Glow for Cardflow
    CARD_SELECTED = (255, 100, 100, 150)
    CARD_HOVER = (255, 255, 255, 60)

    # Phase indicator
    PHASE_ACTIVE = (80, 200, 120)
    PHASE_INACTIVE = (80, 80, 95)
    PHASE_DONE = (60, 60, 70)

    # Ribbon / Grouping
    RIBBON_RED = (220, 40, 40)
    RIBBON_GOLD = (255, 215, 0)  # Actual Gold color
    RIBBON_SHADOW = (100, 10, 20)

    # Player status
    BURN_RED = (255, 60, 40)
    SAFE_GREEN = (60, 220, 100)

    # Overlay
    OVERLAY_BG = (10, 10, 20, 180)


# ─── Toast / Notification Component ──────────────────────────────────

class ToastNotification:
    """Temporary fading message for hints and feedback."""
    def __init__(self, text, duration=2.5, color=Colors.TEXT_WHITE):
        self.text = text
        self.duration = duration
        self.max_duration = duration
        self.color = color
        self.alpha = 0
        self.target_alpha = 255
        self.y_offset = 20 # Animation start
        
    def update(self, dt):
        self.duration -= dt
        
        # Fade in / out logic
        if self.duration > self.max_duration - 0.5:
            # Fade in
            self.alpha = min(255, self.alpha + int(510 * dt))
            self.y_offset = max(0, self.y_offset - 40 * dt)
        elif self.duration < 0.5:
            # Fade out
            self.alpha = max(0, self.alpha - int(510 * dt))
            self.y_offset -= 10 * dt
        else:
            self.alpha = 255
            self.y_offset = 0
            
        return self.duration > 0

    def draw(self, surface, font, x, y):
        if self.alpha <= 0: return
        
        # Draw background shadow/pill
        lbl = font.render(self.text, True, self.color)
        padding_x, padding_y = 20, 10
        bg_rect = pygame.Rect(0, 0, lbl.get_width() + padding_x*2, lbl.get_height() + padding_y*2)
        bg_rect.center = (x, y + self.y_offset)
        
        # Semi-transparent dark background
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (20, 20, 30, self.alpha // 1.5), (0, 0, *bg_rect.size), border_radius=bg_rect.height//2)
        pygame.draw.rect(bg_surf, (80, 80, 100, self.alpha // 2), (0, 0, *bg_rect.size), width=1, border_radius=bg_rect.height//2)
        surface.blit(bg_surf, bg_rect.topleft)
        
        # Text
        lbl.set_alpha(self.alpha)
        surface.blit(lbl, (bg_rect.centerx - lbl.get_width()//2, bg_rect.centery - lbl.get_height()//2))


# ─── Button Component ────────────────────────────────────────────────

class Button:
    def __init__(self, x, y, w, h, text, font,
                 color=Colors.BTN_PRIMARY,
                 hover_color=Colors.BTN_PRIMARY_HOVER,
                 text_color=Colors.TEXT_WHITE,
                 border_radius=8,
                 enabled=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_radius = border_radius
        self.enabled = enabled
        self.is_hovered = False
        self._pulse_time = 0.0

    def update(self, mouse_pos, dt=0):
        self.is_hovered = self.rect.collidepoint(mouse_pos) and self.enabled
        self._pulse_time += dt

    def is_clicked(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface):
        # Background
        if not self.enabled:
            color = Colors.BTN_DISABLED
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.color

        # Draw rounded rect with alpha support
        btn_surface = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(btn_surface, (*color, 230), (0, 0, self.rect.w, self.rect.h),
                         border_radius=self.border_radius)

        # Border
        border_color = (255, 255, 255, 40) if self.enabled else (255, 255, 255, 15)
        pygame.draw.rect(btn_surface, border_color, (0, 0, self.rect.w, self.rect.h),
                         width=1, border_radius=self.border_radius)

        surface.blit(btn_surface, self.rect.topleft)

        # Text
        txt_color = self.text_color if self.enabled else Colors.TEXT_MUTED
        text_surf = self.font.render(self.text, True, txt_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


# ─── Phase Indicator ─────────────────────────────────────────────────

class PhaseIndicator:
    """Shows the current turn phase as a horizontal breadcrumb bar."""
    PHASES = ['DRAW', 'MELD', 'DISCARD']

    def __init__(self, x, y, font):
        self.x = x
        self.y = y
        self.font = font
        self.active_index = 0
        self._glow_time = 0.0

    def set_phase(self, phase_name):
        phase_map = {'DRAW': 0, 'MELD': 1, 'ACTION': 1, 'DISCARD': 2, 'WAITING': -1}
        self.active_index = phase_map.get(phase_name, -1)

    def draw(self, surface, dt=0):
        self._glow_time += dt
        total_w = 0
        phase_surfs = []

        for i, phase in enumerate(self.PHASES):
            if i == self.active_index:
                color = Colors.PHASE_ACTIVE
                # Pulsating glow
                glow = int(20 * math.sin(self._glow_time * 4))
                color = (min(255, color[0] + glow), min(255, color[1] + glow), min(255, color[2] + glow))
            elif i < self.active_index:
                color = Colors.PHASE_DONE
            else:
                color = Colors.PHASE_INACTIVE

            text_surf = self.font.render(phase, True, color)
            phase_surfs.append(text_surf)
            total_w += text_surf.get_width()

        # Draw with arrows between
        arrow_text = self.font.render(" → ", True, Colors.TEXT_MUTED)
        total_w += arrow_text.get_width() * (len(self.PHASES) - 1)

        cx = self.x - total_w // 2
        for i, surf in enumerate(phase_surfs):
            surface.blit(surf, (cx, self.y))
            cx += surf.get_width()
            if i < len(phase_surfs) - 1:
                surface.blit(arrow_text, (cx, self.y))
                cx += arrow_text.get_width()


# ─── Badge ───────────────────────────────────────────────────────────

class Badge:
    """Small counter badge (e.g., card count, deck count)."""
    def __init__(self, font):
        self.font = font

    def draw(self, surface, x, y, text, bg_color=(40, 40, 55, 220), text_color=Colors.TEXT_WHITE):
        text_surf = self.font.render(str(text), True, text_color)
        tw, th = text_surf.get_size()
        pad = 6
        w = tw + pad * 2
        h = th + pad
        badge_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(badge_surf, bg_color, (0, 0, w, h), border_radius=h // 2)
        badge_surf.blit(text_surf, (pad, pad // 2))
        surface.blit(badge_surf, (x - w // 2, y - h // 2))


# ─── Player Info Panel ───────────────────────────────────────────────

class LevelProgressBar:
    def __init__(self, font_small, width=200, height=14):
        self.font_small = font_small
        self.w = width
        self.h = height

    def draw(self, surface, x, y, level, total_xp):
        # Calculate progress within the current level
        temp_level = 1
        xp_remaining = total_xp
        req = 1000
        
        while True:
            req = 1000 if temp_level <= 10 else temp_level * 150
            if temp_level < level and xp_remaining >= req:
                xp_remaining -= req
                temp_level += 1
            else:
                break
        
        # Cap at level 200
        if level >= 200:
            xp_remaining = req
            progress = 1.0
        else:
            progress = min(1.0, xp_remaining / max(1, req))

        # Background
        pygame.draw.rect(surface, (40, 15, 20), (x, y, self.w, self.h), border_radius=self.h//2)
        # Fill
        fill_w = int(self.w * progress)
        if fill_w > 0:
            fill_rect = pygame.Rect(x, y, fill_w, self.h)
            # Use a vibrant gold gradient or just a solid color for red theme
            pygame.draw.rect(surface, (255, 215, 50), fill_rect, border_radius=self.h//2)
        # Border
        pygame.draw.rect(surface, (180, 60, 60), (x, y, self.w, self.h), width=1, border_radius=self.h//2)
        
        # Text
        if level >= 200:
            text_str = f"Lvl {level}  (MAX LEVEL)"
        else:
            text_str = f"Lvl {level}  ({int(xp_remaining)}/{req})"
            
        text_surf = self.font_small.render(text_str, True, (220, 230, 240))
        surface.blit(text_surf, (x + self.w//2 - text_surf.get_width()//2, y - 18))

class ProfileInspectOverlay:
    def __init__(self, font_title, font_body, font_small):
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = font_small
        self.visible = False
        self.target_player = None
        self.target_avatar = None
        self.pb = LevelProgressBar(font_small, 260, 16)
        
    def show(self, player, avatar_surf):
        self.target_player = player
        self.target_avatar = avatar_surf
        self.visible = True
        
    def hide(self):
        self.visible = False
        
    def draw(self, surface):
        if not self.visible or not self.target_player: return
        
        sw, sh = surface.get_size()
        
        # Dim background
        dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200)) # Darker dim
        surface.blit(dim, (0, 0))
        
        # Panel Dimensions
        pw, ph = 420, 520
        px, py = sw//2 - pw//2, sh//2 - ph//2
        
        # --- 1. Premium Glassmorphism Panel ---
        # Main background with vertical gradient (Crimson theme)
        panel_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        for row in range(ph):
            rt = row / ph
            # Dark crimson to deep black-red gradient
            rc = int(45 - 20 * rt)
            gc = int(12 - 4 * rt)
            bc = int(18 - 6 * rt)
            pygame.draw.line(panel_surf, (rc, gc, bc, 250), (0, row), (pw, row))
            
        # Add a subtle interior highlight line at the top
        pygame.draw.line(panel_surf, (255, 100, 100, 40), (24, 2), (pw-24, 2), width=1)
            
        # Rounded corners mask
        mask = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, pw, ph), border_radius=32)
        panel_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        # Border
        rank_str = getattr(self.target_player, 'rank', "Wood")
        border_color = (255, 215, 100, 120) if rank_str in ("Gold", "Immortal") else (180, 40, 45, 140)
        pygame.draw.rect(panel_surf, border_color, (0, 0, pw, ph), width=2, border_radius=32)
        surface.blit(panel_surf, (px, py))
        
        # --- 2. Title ---
        title_surf = self.font_title.render("PLAYER PROFILE", True, (255, 215, 100))
        # Shadow
        title_shadow = self.font_title.render("PLAYER PROFILE", True, (10, 5, 5))
        tsx = px + pw//2 - title_surf.get_width()//2
        tsy = py + 25
        surface.blit(title_shadow, (tsx + 2, tsy + 2))
        surface.blit(title_surf, (tsx, tsy))
        
        # --- 3. Avatar with Glow ---
        if self.target_avatar:
            av_size = 110
            av = pygame.transform.smoothscale(self.target_avatar, (av_size, av_size))
            
            # Mask to circle
            av_mask = pygame.Surface((av_size, av_size), pygame.SRCALPHA)
            pygame.draw.circle(av_mask, (255, 255, 255), (av_size//2, av_size//2), av_size//2)
            av.blit(av_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            
            # Glow
            glow = pygame.Surface((av_size + 20, av_size + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 215, 100, 40), (av_size//2 + 10, av_size//2 + 10), av_size//2 + 10)
            
            av_x = px + pw//2 - av_size//2
            av_y = py + 80
            surface.blit(glow, (av_x - 10, av_y - 10))
            surface.blit(av, (av_x, av_y))
            
            # Avatar Border
            pygame.draw.circle(surface, (255, 215, 100), (av_x + av_size//2, av_y + av_size//2), av_size//2, width=2)
        
        # --- 4. Name ---
        name_surf = self.font_body.render(self.target_player.name, True, (255, 255, 255))
        surface.blit(name_surf, (px + pw//2 - name_surf.get_width()//2, py + 205))
        
        # --- 5. Rank Badge & Info ---
        from ui.assets_mgr import get_rank_badge
        badge_surf = get_rank_badge(getattr(self.target_player, 'rank', "Wood"), "large")
        # Scale down a bit if it's too large (usually large is 120x120)
        badge_surf = pygame.transform.smoothscale(badge_surf, (100, 100))
        badge_x = px + pw//2 - badge_surf.get_width()//2
        badge_y = py + 235
        surface.blit(badge_surf, (badge_x, badge_y))
        
        # RP Text
        rp = getattr(self.target_player, 'rp', 0)
        rank_str = getattr(self.target_player, 'rank', "Wood")
        rp_surf = self.font_body.render(f"{rank_str} Rank - {rp} RP", True, (220, 220, 230))
        surface.blit(rp_surf, (px + pw//2 - rp_surf.get_width()//2, py + 340))
        
        # --- 6. Stats (Wins/Losses) ---
        wins = getattr(self.target_player, 'wins', 0)
        losses = getattr(self.target_player, 'losses', 0)
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        
        stats_txt = self.font_small.render(f"Wins: {wins}  |  Losses: {losses}  |  Win Rate: {win_rate:.1f}%", True, (170, 180, 200))
        surface.blit(stats_txt, (px + pw//2 - stats_txt.get_width()//2, py + 375))
        
        # --- 7. Level & XP Bar ---
        level = getattr(self.target_player, 'level', 1)
        xp = getattr(self.target_player, 'xp', 0)
        
        # Use our LevelProgressBar
        self.pb.draw(surface, px + pw//2 - self.pb.w//2, py + 415, level, xp)
        
        # --- 8. Close Instruction ---
        close_surf = self.font_small.render("Click anywhere to close", True, (130, 130, 150))
        surface.blit(close_surf, (px + pw//2 - close_surf.get_width()//2, py + 480))


class PlayerPanel:
    """Displays player name, card count, burn status, and points."""
    def __init__(self, font_name, font_stats):
        self.font_name = font_name
        self.font_stats = font_stats

    def draw(self, surface, x, y, player, is_active=False, show_points=False, align='center', avatar_surf=None, show_burned=False, timer_progress=0.0, is_dealer=False, dealer_img=None, show_cards=True):
        # Modern Layout Dimensions
        pw, ph = 260, 84
        if align == 'center': px = x - pw // 2
        elif align == 'left': px = x
        else: px = x - pw
        py = y

        # --- 1. Panel Background (Modern Glassmorphism) ---
        panel_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg_alpha = 250 if is_active else 200
        
        # Draw background with a subtle vertical gradient
        for row in range(ph):
            rt = row / ph
            alpha = bg_alpha - int(20 * rt)
            pygame.draw.line(panel_surf, (20, 24, 38, alpha), (0, row), (pw, row))
            
        # Interior highlight line
        pygame.draw.line(panel_surf, (255, 255, 255, 30), (15, 2), (pw-15, 2), width=1)
        
        # Rounded corners mask
        mask = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, pw, ph), border_radius=22)
        panel_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        # Border
        border_color = (255, 215, 100, 100) if is_active else (255, 255, 255, 25)
        pygame.draw.rect(panel_surf, border_color, (0, 0, pw, ph), width=1, border_radius=22)
        
        # Active turn glow
        if is_active:
            glow_surf = pygame.Surface((pw + 10, ph + 10), pygame.SRCALPHA)
            p = int(30 + 15 * math.sin(pygame.time.get_ticks() * 0.01))
            pygame.draw.rect(glow_surf, (*Colors.PHASE_ACTIVE, p), (0, 0, pw + 10, ph + 10), border_radius=22)
            surface.blit(glow_surf, (px - 5, py - 5))

        surface.blit(panel_surf, (px, py))

        # --- 2. Avatar with Status Ring & Timer ---
        av_x, av_y = px + 12, py + 10
        target_size = 60
        center = (av_x + target_size // 2, av_y + target_size // 2)
        
        if is_active:
            # Pulsating ring around avatar
            ring_p = 2 + 2 * math.sin(pygame.time.get_ticks() * 0.01)
            pygame.draw.circle(surface, (40, 45, 60), center, (target_size // 2) + 6, width=4) # Background track
            
            # --- Turn Timer Progress Bar (Arc) ---
            if timer_progress > 0:
                timer_color = Colors.PHASE_ACTIVE if timer_progress > 0.3 else Colors.BURN_RED
                rect = pygame.Rect(av_x - 6, av_y - 6, target_size + 12, target_size + 12)
                # Draw arc from -90 degrees (top)
                start_angle = -math.pi / 2
                stop_angle = start_angle + (2 * math.pi * timer_progress)
                pygame.draw.arc(surface, timer_color, rect, -stop_angle, -start_angle, 4)

        if avatar_surf:
            try:
                scaled_avatar = pygame.transform.smoothscale(avatar_surf, (target_size, target_size))
                mask_surf = pygame.Surface((target_size, target_size), pygame.SRCALPHA)
                pygame.draw.circle(mask_surf, (255, 255, 255, 255), (target_size // 2, target_size // 2), target_size // 2)
                scaled_avatar.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                surface.blit(scaled_avatar, (av_x, av_y))
            except:
                surface.blit(pygame.transform.smoothscale(avatar_surf, (target_size, target_size)), (av_x, av_y))
        else:
            pygame.draw.circle(surface, (60, 70, 90), center, target_size // 2)
            init_surf = self.font_stats.render(player.name[0].upper(), True, Colors.TEXT_WHITE)
            surface.blit(init_surf, (center[0] - init_surf.get_width() // 2, center[1] - init_surf.get_height() // 2))

        from ui.assets_mgr import get_rank_badge
        
        # --- 3. Text & Stats ---
        text_off_x = av_x + target_size + 16
        
        # Mini Rank Badge
        rank_name = getattr(player, 'rank', "Wood")
        m_badge = get_rank_badge(rank_name, "small")
        if m_badge:
            m_badge = pygame.transform.smoothscale(m_badge, (24, 24))
            surface.blit(m_badge, (text_off_x, py + 14))
            name_x_offset = 30
        else:
            name_x_offset = 0

        name_color = (255, 215, 100) if is_active else Colors.TEXT_WHITE
        name_surf = self.font_name.render(player.name, True, name_color)
        surface.blit(name_surf, (text_off_x + name_x_offset, py + 12))
        
        # Level display removed from in-game panel (visible only in Profile Stalk)


        # Rank badge removed from in-game panel (visible only in Profile Stalk)

        if show_cards:
            card_text = f"{player.card_count()} CARDS"
            card_surf = self.font_stats.render(card_text, True, Colors.TEXT_MUTED)
            surface.blit(card_surf, (text_off_x, py + 42))

        if show_points:
            pts_surf = self.font_stats.render(f"{player.calculate_points()} PTS", True, Colors.TEXT_GOLD)
            surface.blit(pts_surf, (px + pw - pts_surf.get_width() - 15, py + 42))
        elif show_burned:
            status_color = Colors.BURN_RED if player.is_burned else Colors.SAFE_GREEN
            status_label = "BURNED" if player.is_burned else "ACTIVE"
            status_surf = self.font_stats.render(status_label.upper(), True, status_color)
            surface.blit(status_surf, (px + pw - status_surf.get_width() - 15, py + 42))
        else:
             if not player.is_burned:
                 pygame.draw.circle(surface, Colors.SAFE_GREEN, (px + pw - 20, py + 52), 5)


# ─── Overlays ────────────────────────────────────────────────────────

class FightResolutionOverlay:
    """Premium battle overlay with pie-style status indicators for Fight resolution."""

    # Status colors
    COLOR_FIGHT = (220, 50, 50)
    COLOR_FOLD = (120, 130, 145)
    COLOR_BURNED = (255, 140, 30)
    COLOR_CALLER = (180, 80, 255)
    COLOR_WAITING = (50, 55, 70)
    COLOR_RING_BG = (35, 40, 55)

    def __init__(self, width, height, font_title, font_body, font_btn, font_small):
        self.width = width
        self.height = height
        self.font_title = font_title
        self.font_body = font_body
        self.font_btn = font_btn
        self.font_small = font_small

        # Animation state
        self.alpha = 0
        self.target_alpha = 255
        self.fade_speed = 400
        self.entrance_timer = 0.0
        self.entrance_duration = 0.8
        self.time_alive = 0.0

        # Per-player pie fill animation (0.0 → 1.0)
        self.pie_fills = [0.0, 0.0, 0.0]
        self.pie_fill_speed = 2.5
        self.pie_targets = [0.0, 0.0, 0.0]

        # Cached player statuses for animation tracking
        self._last_statuses = [None, None, None]

        # Shake effect
        self.shake_timer = 0.4
        self.shake_intensity = 8

        # Cached blurred background (captured on first draw)
        self._blurred_bg = None

        # Buttons (premium style)
        btn_w, btn_h = 200, 58
        self.btn_fight = Button(
            width // 2 - btn_w - 25, height // 2 + 195, btn_w, btn_h,
            "FIGHT", font_btn,
            color=(180, 40, 40), hover_color=(220, 60, 60),
            border_radius=14
        )
        self.btn_fold = Button(
            width // 2 + 25, height // 2 + 195, btn_w, btn_h,
            "FOLD", font_btn,
            color=(80, 85, 100), hover_color=(110, 115, 135),
            border_radius=14
        )

        self.avatars = [None, None, None]
        
        self._choice_made = False
        self.fight_resolved_timer = None # For resolution progress bar

    def set_avatars(self, avatar_list):
        """Set the player avatar surfaces for rendering inside pie rings."""
        self.avatars = list(avatar_list) if avatar_list else [None, None, None]

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        btn_w, btn_h = 200, 58
        self.btn_fight.rect.x = width // 2 - btn_w - 25
        self.btn_fight.rect.y = height // 2 + 195
        self.btn_fold.rect.x = width // 2 + 25
        self.btn_fold.rect.y = height // 2 + 195

    def update(self, dt, mouse_pos, active_fight=None):
        self.time_alive += dt
        self.entrance_timer = min(self.entrance_timer + dt, self.entrance_duration)
        self.alpha = min(self.alpha + self.fade_speed * dt, self.target_alpha)
        self.shake_timer = max(0, self.shake_timer - dt)
        
        if not active_fight:
            self._choice_made = False

        # Set pie fills instantly to remove confusing "loading" animation
        for i in range(3):
            self.pie_fills[i] = self.pie_targets[i]

        self.btn_fight.update(mouse_pos, dt)
        self.btn_fold.update(mouse_pos, dt)

    def _get_player_status(self, player, active_fight):
        """Returns (status_str, color) for a player."""
        caller = active_fight['caller']
        responses = active_fight.get('responses', {})

        if player == caller:
            return ('CHALLENGER', self.COLOR_CALLER)
        elif player in responses:
            resp = responses[player]
            if resp == 'fight':
                return ('FIGHT!!', self.COLOR_FIGHT)
            else:
                if player.is_burned:
                    return ('BURNED', self.COLOR_BURNED)
                else:
                    return ('FOLD', self.COLOR_FOLD)
        else:
            if player.is_burned:
                return ('BURNED', self.COLOR_BURNED)
            return ('DECIDING...', self.COLOR_WAITING)

    def _draw_pie_ring(self, surface, cx, cy, radius, fill_pct, color, bg_color, thickness=10):
        """Draw a circular arc (pie ring) from the top, filling clockwise."""
        # Background ring (full circle)
        pygame.draw.circle(surface, bg_color, (cx, cy), radius, thickness)

        if fill_pct <= 0:
            return

        # Filled arc
        arc_rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
        start_angle_raw = math.pi / 2  # Top (pygame angles are counter-clockwise from right)
        sweep = 2 * math.pi * min(fill_pct, 1.0)
        end_angle_raw = start_angle_raw - sweep

        # Draw filled arc with anti-aliasing via multiple thin arcs
        for t in range(thickness):
            r = radius - t
            if r <= 0:
                break
            arc_rect2 = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
            pygame.draw.arc(surface, color, arc_rect2, end_angle_raw, start_angle_raw, 2)

    def _draw_avatar_circle(self, surface, cx, cy, radius, avatar_surf):
        """Draw a circular-masked avatar at the given center."""
        size = radius * 2
        if avatar_surf:
            try:
                scaled = pygame.transform.smoothscale(avatar_surf, (size, size))
                mask = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius)
                scaled.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                surface.blit(scaled, (cx - radius, cy - radius))
            except:
                pygame.draw.circle(surface, (50, 55, 75), (cx, cy), radius)
        else:
            pygame.draw.circle(surface, (50, 55, 75), (cx, cy), radius)

    def _draw_crossed_swords(self, surface, cx, cy, size=40):
        """Draw a stylized VS / crossed swords icon."""
        ticks = pygame.time.get_ticks()
        pulse = math.sin(ticks * 0.005) * 0.15 + 1.0
        s = int(size * pulse)
        half = s // 2

        # Glow circle behind
        glow_a = int(40 + 25 * math.sin(ticks * 0.008))
        glow_r = s + 15
        glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (255, 80, 50, glow_a), (glow_r, glow_r), glow_r)
        surface.blit(glow_s, (cx - glow_r, cy - glow_r))

        # VS text
        try:
            vs_font = pygame.font.SysFont("Arial", s, bold=True)
        except:
            vs_font = self.font_title
        vs_surf = vs_font.render("VS", True, (255, 200, 80))
        vs_shadow = vs_font.render("VS", True, (80, 30, 0))
        surface.blit(vs_shadow, (cx - vs_surf.get_width() // 2 + 2, cy - vs_surf.get_height() // 2 + 2))
        surface.blit(vs_surf, (cx - vs_surf.get_width() // 2, cy - vs_surf.get_height() // 2))

    def draw(self, surface, active_fight, points, players, resolution_time_left=None):
        if not active_fight:
            return

        caller = active_fight['caller'] if isinstance(active_fight, dict) else active_fight
        responses = active_fight.get('responses', {}) if isinstance(active_fight, dict) else {}

        # Entrance easing
        ep = min(self.entrance_timer / max(self.entrance_duration, 0.001), 1.0)
        ease = 1.0 - (1.0 - ep) ** 3  # ease-out cubic

        # Screen shake offset
        shake_x, shake_y = 0, 0
        if self.shake_timer > 0:
            import random as _rnd
            shake_x = int(_rnd.uniform(-self.shake_intensity, self.shake_intensity) * (self.shake_timer / 0.4))
            shake_y = int(_rnd.uniform(-self.shake_intensity, self.shake_intensity) * (self.shake_timer / 0.4))

        # Frosted-glass blur backdrop (captured once on first draw)
        if self._blurred_bg is None:
            self._blurred_bg = blur_surface(surface.copy(), factor=8, tint=(8, 5, 15), tint_alpha=190)
        # Draw blurred background with fade-in
        blur_alpha = int(min(self.alpha, 255) * ease)
        if blur_alpha >= 250:
            surface.blit(self._blurred_bg, (0, 0))
        else:
            temp = self._blurred_bg.copy()
            temp.set_alpha(blur_alpha)
            surface.blit(temp, (0, 0))

        if self.alpha < 30:
            return

        # --- Update pie animation targets ---
        for i, p in enumerate(players):
            status_str, status_color = self._get_player_status(p, active_fight)
            if status_str != self._last_statuses[i]:
                self._last_statuses[i] = status_str
                if status_str in ('FIGHT!!', 'FOLD', 'BURNED', 'CHALLENGER'):
                    self.pie_targets[i] = 1.0
                else:
                    self.pie_targets[i] = 0.0

        # ── Layout Calculations ──
        human_player = players[0]
        needs_response = (human_player not in responses and human_player != caller and not human_player.is_burned)
        
        # Animate the scale
        target_scale = 1.0 if not needs_response else 0.0
        if not hasattr(self, '_pie_scale'): self._pie_scale = 0.0
        self._pie_scale += (target_scale - self._pie_scale) * 0.15

        center_x = self.width // 2 + shake_x
        center_y = self.height // 2 + shake_y - 20 + int(self._pie_scale * 30)

        pie_radius = 62 + int(self._pie_scale * 20)
        pie_thickness = 10 + int(self._pie_scale * 2)
        avatar_radius = 46 + int(self._pie_scale * 16)
        
        # 3 pies arranged horizontally with VS between them
        gap = 180 + int(self._pie_scale * 60)
        pie_positions = [
            (center_x - gap, center_y - 10),   # Player 1 (left)
            (center_x, center_y - 50 - int(self._pie_scale * 10)),  # Caller (center, raised)
            (center_x + gap, center_y - 10),    # Player 3 (right)
        ]

        # ── Top Banner with dramatic entrance ──
        banner_h = 80
        banner_y = max(20, center_y - 230)
        banner_alpha = int(min(self.alpha, 240) * ease)

        # Banner background
        banner_surf = pygame.Surface((self.width, banner_h), pygame.SRCALPHA)
        pygame.draw.rect(banner_surf, (30, 15, 15, banner_alpha), (0, 0, self.width, banner_h))
        # Top and bottom accent lines
        line_color = (255, 60, 40, banner_alpha)
        pygame.draw.line(banner_surf, line_color, (0, 0), (self.width, 0), 3)
        pygame.draw.line(banner_surf, line_color, (0, banner_h - 1), (self.width, banner_h - 1), 3)
        # Inner gradient stripe
        stripe = pygame.Surface((self.width, 4), pygame.SRCALPHA)
        stripe.fill((255, 80, 40, banner_alpha // 3))
        banner_surf.blit(stripe, (0, banner_h // 2 - 2))
        surface.blit(banner_surf, (shake_x, banner_y + shake_y))

        # Title text with shadow
        title_text = "FIGHT CHALLENGE!"
        title_surf = self.font_title.render(title_text, True, (255, 75, 55))
        title_shadow = self.font_title.render(title_text, True, (60, 15, 10))
        tx = center_x - title_surf.get_width() // 2
        ty = banner_y + shake_y + banner_h // 2 - title_surf.get_height() // 2
        surface.blit(title_shadow, (tx + 2, ty + 2))
        surface.blit(title_surf, (tx, ty))

        # ── Subtitle: Caller info ──
        sub_text = f"{caller.name.upper()} HAS CHALLENGED THE TABLE!"
        sub_surf = self.font_body.render(sub_text, True, Colors.TEXT_WHITE)
        sub_y = banner_y + shake_y + banner_h + 12
        surface.blit(sub_surf, (center_x - sub_surf.get_width() // 2, sub_y))

        # ── PIE STATUS RINGS ──
        for i, p in enumerate(players):
            px, py = pie_positions[i]
            status_str, status_color = self._get_player_status(p, active_fight)
            fill = self.pie_fills[i]

            # Outer glow when filled
            if fill > 0.5:
                glow_a = int(30 + 20 * math.sin(self.time_alive * 4 + i))
                glow_s = pygame.Surface(((pie_radius + 20) * 2, (pie_radius + 20) * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_s, (*status_color, glow_a), (pie_radius + 20, pie_radius + 20), pie_radius + 20)
                surface.blit(glow_s, (px - pie_radius - 20, py - pie_radius - 20))

            # Background dark circle
            pygame.draw.circle(surface, (20, 22, 32), (px, py), pie_radius + 2)

            # Pie ring (animated fill)
            self._draw_pie_ring(surface, px, py, pie_radius, fill * ease, status_color, self.COLOR_RING_BG, pie_thickness)

            # Avatar inside the ring
            self._draw_avatar_circle(surface, px, py, avatar_radius, self.avatars[i] if i < len(self.avatars) else None)

            # Player name below pie
            name_surf = self.font_body.render(p.name, True, Colors.TEXT_WHITE)
            surface.blit(name_surf, (px - name_surf.get_width() // 2, py + pie_radius + 14))

            # Status label below name with colored badge
            if status_str not in ('DECIDING...',):
                badge_w = max(90, len(status_str) * 11 + 20)
                badge_h = 28
                badge_x = px - badge_w // 2
                badge_y = py + pie_radius + 40

                badge_s = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
                pygame.draw.rect(badge_s, (*status_color, 60), (0, 0, badge_w, badge_h), border_radius=badge_h // 2)
                pygame.draw.rect(badge_s, (*status_color, 140), (0, 0, badge_w, badge_h), width=2, border_radius=badge_h // 2)
                surface.blit(badge_s, (badge_x, badge_y))

                st_surf = self.font_btn.render(status_str, True, status_color)
                surface.blit(st_surf, (px - st_surf.get_width() // 2, badge_y + badge_h // 2 - st_surf.get_height() // 2))
            else:
                # Pulsating "..." waiting indicator
                dots = "." * (int(self.time_alive * 3) % 4)
                wait_text = f"DECIDING{dots}"
                pulse_a = int(150 + 80 * math.sin(self.time_alive * 5 + i * 2))
                wait_surf = self.font_btn.render(wait_text, True, (*self.COLOR_WAITING[:3],))
                wait_surf.set_alpha(pulse_a)
                surface.blit(wait_surf, (px - wait_surf.get_width() // 2, py + pie_radius + 42))

            # Points underneath
            human_player_for_check = players[0]
            
            # Show points if it's the human player
            # Or if everyone including the human has responded (we can check if human responded or is caller/burned)
            human_resolved = (human_player_for_check == caller) or (human_player_for_check in responses) or human_player_for_check.is_burned
            
            if p == human_player_for_check:
                is_visible = True
            elif human_resolved:
                # If human has locked in their choice, they can see others who have also locked in/burned/calling
                is_visible = (p == caller) or (p in responses) or p.is_burned
            else:
                # Human hasn't decided yet, hide opponents' points
                is_visible = False
            
            if is_visible:
                pts_val = f"{p.calculate_points()} PTS"
                pts_color = Colors.TEXT_GOLD if p == caller else Colors.TEXT_MUTED
                pts_surf = self.font_btn.render(pts_val, True, pts_color)
                surface.blit(pts_surf, (px - pts_surf.get_width() // 2, py + pie_radius + 72))

        # ── VS Icons between pies ──
        vs_y = center_y - 30
        self._draw_crossed_swords(surface, center_x - gap // 2, vs_y, 28)
        self._draw_crossed_swords(surface, center_x + gap // 2, vs_y, 28)

        # ── FIGHT / FOLD Buttons ──
        # Only show if the human player hasn't responded yet and hasn't just clicked
        human_player = players[0]
        needs_response = (human_player not in responses and human_player != caller and not human_player.is_burned and not self._choice_made)

        if needs_response:
            # Hint text above buttons
            hint_text = "CHOOSE YOUR RESPONSE"
            hint_pulse = int(200 + 55 * math.sin(self.time_alive * 3))
            hint_surf = self.font_body.render(hint_text, True, (hint_pulse, hint_pulse, hint_pulse))
            hint_y = self.btn_fight.rect.y - 35
            surface.blit(hint_surf, (center_x - hint_surf.get_width() // 2, hint_y))

            # Button glow effects
            ticks = pygame.time.get_ticks()

            # Fight button pulse glow
            fight_glow_a = int(25 + 20 * math.sin(ticks * 0.006))
            fight_glow = pygame.Surface((self.btn_fight.rect.w + 20, self.btn_fight.rect.h + 20), pygame.SRCALPHA)
            pygame.draw.rect(fight_glow, (220, 50, 50, fight_glow_a), (0, 0, fight_glow.get_width(), fight_glow.get_height()), border_radius=18)
            surface.blit(fight_glow, (self.btn_fight.rect.x - 10, self.btn_fight.rect.y - 10))

            # Fold button subtle glow
            fold_glow_a = int(15 + 10 * math.sin(ticks * 0.004))
            fold_glow = pygame.Surface((self.btn_fold.rect.w + 16, self.btn_fold.rect.h + 16), pygame.SRCALPHA)
            pygame.draw.rect(fold_glow, (100, 105, 120, fold_glow_a), (0, 0, fold_glow.get_width(), fold_glow.get_height()), border_radius=18)
            surface.blit(fold_glow, (self.btn_fold.rect.x - 8, self.btn_fold.rect.y - 8))

            self.btn_fight.draw(surface)
            self.btn_fold.draw(surface)
        else:
            # Show a "waiting for others" or the player's own response
            if human_player == caller:
                wait_msg = "WAITING FOR RESPONSES..."
            elif human_player.is_burned:
                wait_msg = "YOU ARE BURNED - AUTO FOLD"
            elif human_player in responses:
                resp = responses[human_player]
                wait_msg = f"YOU CHOSE TO {'FIGHT' if resp == 'fight' else 'FOLD'}!"
            else:
                wait_msg = "WAITING..."

            wait_a = int(180 + 60 * math.sin(self.time_alive * 3))
            wait_surf = self.font_body.render(wait_msg, True, Colors.TEXT_MUTED)
            wait_surf.set_alpha(wait_a)
            wait_y = self.btn_fight.rect.y + 10
            surface.blit(wait_surf, (center_x - wait_surf.get_width() // 2, wait_y))

        # ── Resolution Progress Bar ──
        if resolution_time_left is not None and resolution_time_left > 0:
            total_res_time = 3.5 # Sync with main.py
            prog = max(0.0, min(1.0, resolution_time_left / total_res_time))
            
            bar_w = 400
            bar_h = 8
            bx = center_x - bar_w // 2
            by = self.height - 100
            
            # Label
            lbl = self.font_small.render("FINALIZING MATCH RESULTS...", True, Colors.TEXT_MUTED)
            surface.blit(lbl, (center_x - lbl.get_width()//2, by - 25))
            
            # BG
            pygame.draw.rect(surface, (40, 40, 60), (bx, by, bar_w, bar_h), border_radius=4)
            # Fill
            if prog > 0:
                pygame.draw.rect(surface, (255, 215, 0), (bx, by, int(bar_w * (1.0 - prog)), bar_h), border_radius=4)


class GameOverOverlay:
    """Ultra-premium result screen with podium layout, sparkle particles, and gradient buttons."""

    # Rank medal colors
    MEDAL_GOLD = (255, 215, 0)
    MEDAL_SILVER = (192, 192, 210)
    MEDAL_BRONZE = (205, 127, 50)

    def __init__(self, width, height, font_title, font_body, font_btn, font_small):
        self.width = width
        self.height = height
        self.font_title = font_title
        self.font_body = font_body
        self.font_btn = font_btn
        self.font_small = font_small
        self.alpha = 0
        self.target_alpha = 255
        self.fade_speed = 500
        self.time_alive = 0.0
        self.entrance_timer = 0.0
        self.entrance_duration = 0.7

        self._blurred_bg = None
        self.avatars = [None, None, None]

        # Sparkle particles for winner
        import random as _rnd
        self._sparkles = []
        for _ in range(25):
            self._sparkles.append({
                'x': _rnd.uniform(-1, 1),
                'y': _rnd.uniform(-1, 1),
                'speed': _rnd.uniform(0.3, 1.2),
                'size': _rnd.uniform(1.5, 3.5),
                'phase': _rnd.uniform(0, 6.28),
                'drift': _rnd.uniform(-0.5, 0.5),
            })

        # Custom button rects (not using Button class — we draw premium gradient buttons)
        self._btn_w, self._btn_h = 210, 52
        self._btn_radius = 16
        self.play_again_rect = pygame.Rect(
            width // 2 - self._btn_w - 18, height - 80, self._btn_w, self._btn_h
        )
        self.lobby_rect = pygame.Rect(
            width // 2 + 18, height - 80, self._btn_w, self._btn_h
        )
        self._pa_hover = False
        self._lb_hover = False

    def set_avatars(self, avatar_list):
        self.avatars = list(avatar_list) if avatar_list else [None, None, None]

    def reposition(self, width, height):
        self.width = width
        self.height = height
        self.play_again_rect.x = width // 2 - self._btn_w - 18
        self.play_again_rect.y = height - 80
        self.lobby_rect.x = width // 2 + 18
        self.lobby_rect.y = height - 80

    def update(self, dt, mouse_pos):
        self.time_alive += dt
        self.entrance_timer = min(self.entrance_timer + dt, self.entrance_duration)
        self.alpha = min(self.alpha + self.fade_speed * dt, self.target_alpha)
        self._pa_hover = self.play_again_rect.collidepoint(mouse_pos)
        self._lb_hover = self.lobby_rect.collidepoint(mouse_pos)

    # ── Premium Gradient Button ──
    def _draw_gradient_btn(self, surface, rect, label, color_top, color_bot, is_hovered, icon_char=""):
        bw, bh = rect.w, rect.h
        br = self._btn_radius
        btn = pygame.Surface((bw, bh), pygame.SRCALPHA)

        # Multi-row gradient fill
        for row in range(bh):
            t = row / bh
            r = int(color_top[0] + (color_bot[0] - color_top[0]) * t)
            g = int(color_top[1] + (color_bot[1] - color_top[1]) * t)
            b = int(color_top[2] + (color_bot[2] - color_top[2]) * t)
            pygame.draw.line(btn, (r, g, b, 235), (0, row), (bw, row))

        # Clip to rounded rect
        mask = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, bw, bh), border_radius=br)
        btn.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # Top-edge shine highlight
        shine = pygame.Surface((bw, bh // 3), pygame.SRCALPHA)
        pygame.draw.rect(shine, (255, 255, 255, 35 if not is_hovered else 55), (0, 0, bw, bh // 3), border_radius=br)
        btn.blit(shine, (0, 0))

        # Border (brighter on hover)
        border_a = 80 if not is_hovered else 140
        pygame.draw.rect(btn, (255, 255, 255, border_a), (0, 0, bw, bh), width=2, border_radius=br)

        # Drop shadow
        shadow = pygame.Surface((bw + 8, bh + 8), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 50), (0, 0, bw + 8, bh + 8), border_radius=br + 4)
        surface.blit(shadow, (rect.x - 4, rect.y - 2))

        # Hover scale-up illusion (border glow)
        if is_hovered:
            hglow = pygame.Surface((bw + 12, bh + 12), pygame.SRCALPHA)
            pygame.draw.rect(hglow, (*color_top, 40), (0, 0, bw + 12, bh + 12), border_radius=br + 6)
            surface.blit(hglow, (rect.x - 6, rect.y - 6))

        surface.blit(btn, rect.topleft)

        # Label text
        full_text = f"{icon_char}  {label}" if icon_char else label
        txt = self.font_btn.render(full_text, True, (255, 255, 255))
        txt_rect = txt.get_rect(center=rect.center)
        surface.blit(txt, txt_rect)

    # ── Crown ──
    def _draw_crown(self, surface, cx, cy, size=28):
        ticks = pygame.time.get_ticks()
        fy = int(3 * math.sin(ticks * 0.004))
        pulse = 0.92 + 0.12 * math.sin(ticks * 0.006)
        s = int(size * pulse)
        y = cy + fy

        glow_a = int(50 + 30 * math.sin(ticks * 0.005))
        glow_r = s + 14
        gs = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (255, 215, 0, glow_a), (glow_r, glow_r), glow_r)
        surface.blit(gs, (cx - glow_r, y - glow_r))

        pts = [
            (cx - s, y + s // 2), (cx - s, y - s // 4),
            (cx - s // 2, y + s // 6), (cx - s // 4, y - s // 2),
            (cx, y - s // 3),
            (cx + s // 4, y - s // 2), (cx + s // 2, y + s // 6),
            (cx + s, y - s // 4), (cx + s, y + s // 2),
        ]
        pygame.draw.polygon(surface, (255, 200, 50), pts)
        pygame.draw.polygon(surface, (200, 150, 0), pts, 2)
        for jx, jy, jc in [(cx - s // 4, y - s // 2 + 5, (255, 60, 60)),
                            (cx, y - s // 3 + 3, (80, 255, 120)),
                            (cx + s // 4, y - s // 2 + 5, (100, 150, 255))]:
            pygame.draw.circle(surface, jc, (jx, jy), 3)

    # ── Avatar ──
    def _draw_avatar_circle(self, surface, cx, cy, radius, avatar_surf, border_color=None, border_w=3):
        size = radius * 2
        if avatar_surf:
            try:
                scaled = pygame.transform.smoothscale(avatar_surf, (size, size))
                mask = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(mask, (255, 255, 255, 255), (radius, radius), radius)
                scaled.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                surface.blit(scaled, (cx - radius, cy - radius))
            except:
                pygame.draw.circle(surface, (50, 55, 75), (cx, cy), radius)
        else:
            pygame.draw.circle(surface, (50, 55, 75), (cx, cy), radius)
        if border_color:
            pygame.draw.circle(surface, border_color, (cx, cy), radius + border_w, border_w)

    # ── Rank Medal ──
    def _draw_rank_medal(self, surface, cx, cy, rank, color):
        r = 14
        # Shadow
        pygame.draw.circle(surface, (0, 0, 0, 80), (cx + 1, cy + 1), r + 1)
        # Medal disc
        pygame.draw.circle(surface, color, (cx, cy), r)
        # Highlight arc
        pygame.draw.circle(surface, (255, 255, 255, 60), (cx - 2, cy - 2), r - 3, 2)
        # Border
        darker = tuple(max(0, c - 40) for c in color)
        pygame.draw.circle(surface, darker, (cx, cy), r, 2)
        # Rank number
        rank_surf = self.font_btn.render(f"#{rank}", True, (40, 30, 10) if rank == 1 else (255, 255, 255))
        surface.blit(rank_surf, (cx - rank_surf.get_width() // 2, cy - rank_surf.get_height() // 2))

    # ── Sparkle Particles ──
    def _draw_sparkles(self, surface, cx, cy, w, h):
        ticks = pygame.time.get_ticks()
        for sp in self._sparkles:
            t = self.time_alive * sp['speed'] + sp['phase']
            sx = cx + sp['x'] * w * 0.55 + math.sin(t * 2) * 15
            sy = cy + sp['y'] * h * 0.5 + sp['drift'] * math.cos(t * 1.5) * 20
            a = int(120 + 120 * math.sin(t * 3))
            size = sp['size'] * (0.7 + 0.3 * math.sin(t * 4))
            if 0 < a < 255:
                pygame.draw.circle(surface, (255, 235, 180, min(a, 255)), (int(sx), int(sy)), max(1, int(size)))

    def draw(self, surface, winner, win_method, scores, engine, get_card_image, player_rank="BEGINNER", statuses=None):
        ep = min(self.entrance_timer / max(self.entrance_duration, 0.001), 1.0)
        ease = 1.0 - (1.0 - ep) ** 3

        # Blur backdrop
        if self._blurred_bg is None:
            self._blurred_bg = blur_surface(surface.copy(), factor=8, tint=(6, 10, 22), tint_alpha=200)
        blur_alpha = int(min(self.alpha, 255) * ease)
        if blur_alpha >= 250:
            surface.blit(self._blurred_bg, (0, 0))
        else:
            temp = self._blurred_bg.copy()
            temp.set_alpha(blur_alpha)
            surface.blit(temp, (0, 0))

        if self.alpha < 35:
            return

        center_x = self.width // 2
        ticks = pygame.time.get_ticks()

        # ── Sort players by rank (lowest points = best) ──
        ranked = sorted(enumerate(engine.players), key=lambda x: scores.get(x[1].name, 999))
        rank_map = {}
        for rank_idx, (orig_idx, p) in enumerate(ranked):
            rank_map[orig_idx] = rank_idx + 1  # 1-indexed rank

        # ── Banner ──
        banner_h = 110
        banner_y = 18
        banner_surf = pygame.Surface((self.width, banner_h), pygame.SRCALPHA)

        # Gradient fill
        for row in range(banner_h):
            t = row / banner_h
            r = int(18 + 22 * t)
            g = int(12 + 18 * t)
            b = int(35 + 30 * t)
            a = int(min(self.alpha, 245) * ease)
            pygame.draw.line(banner_surf, (r, g, b, a), (0, row), (self.width, row))
        
        # Animated sweep light across banner
        sweep_x = int((ticks * 0.08) % (self.width + 200)) - 100
        sweep_w = 120
        sweep = pygame.Surface((sweep_w, banner_h), pygame.SRCALPHA)
        for col in range(sweep_w):
            sa = int(18 * math.sin(col / sweep_w * math.pi))
            pygame.draw.line(sweep, (255, 255, 255, sa), (col, 0), (col, banner_h))
        banner_surf.blit(sweep, (sweep_x, 0))

        # Accent lines
        la = int(min(self.alpha, 220) * ease)
        pygame.draw.line(banner_surf, (255, 215, 0, la), (0, 0), (self.width, 0), 3)
        pygame.draw.line(banner_surf, (255, 215, 0, la), (0, banner_h - 1), (self.width, banner_h - 1), 2)
        surface.blit(banner_surf, (0, banner_y))

        # Winner text
        is_player_win = (winner and winner.name == engine.players[0].name)
        main_text = f"{winner.name.upper()} WINS!" if winner else "GAME DRAWN"
        
        # Use Cardflow Red (TEXT_GOLD) or vibrant green
        title_color = (80, 255, 160) if is_player_win else Colors.TEXT_GOLD
        title_surf = self.font_title.render(main_text, True, title_color)
        
        # Subtle glow instead of hard shadow
        glow_surf = self.font_title.render(main_text, True, (*title_color, 50))
        for ox, oy in [(-2,0), (2,0), (0,-2), (0,2)]:
            surface.blit(glow_surf, (center_x - title_surf.get_width() // 2 + ox, banner_y + 18 + oy))
            
        surface.blit(title_surf, (center_x - title_surf.get_width() // 2, banner_y + 18))

        payout = getattr(engine, 'payout', 0)
        method_y_offset = 60
        if payout > 0:
            pay_txt = f"TOTAL COINS COLLECTED: {payout}"
            pay_surf = self.font_body.render(pay_txt, True, (255, 230, 50))
            surface.blit(pay_surf, (center_x - pay_surf.get_width() // 2, banner_y + method_y_offset))
            method_y_offset += 25

        method_labels = {
            'tongits': 'TONG-ITS!', 'fight': 'FIGHT RESOLVED!',
            'fight_won': 'FIGHT RESOLVED!', 'fight_lost': 'FIGHT RESOLVED!',
            'deck_empty': 'DECK DEPLETED!', 'spread': 'SPREAD!'
        }
        method_text = method_labels.get(win_method, win_method.upper() if win_method else '')
        ms = self.font_small.render(method_text, True, (160, 160, 180))
        surface.blit(ms, (center_x - ms.get_width() // 2, banner_y + method_y_offset))

        # ── Player Result Cards (Podium Layout) ──
        player_count = len(engine.players)
        base_card_w = min(280, (self.width - 120) // player_count - 15)
        base_card_h = min(360, self.height - 260)
        gap = 22
        
        card_start_y = banner_y + banner_h + 40

        for i, player_obj in enumerate(engine.players):
            p_name = player_obj.name
            score = scores.get(p_name, 0)
            is_win = (winner and p_name == winner.name)
            rank = rank_map.get(i, 3)

            # Podium sizing: winner gets larger
            if is_win:
                cw = int(base_card_w * 1.15)
                ch = int(base_card_h * 1.05)
                cy = card_start_y - 15
            else:
                cw = base_card_w
                ch = base_card_h
                cy = card_start_y + 10

            # Horizontal positioning (centered group)
            total_w = int(base_card_w * 1.15) + base_card_w * (player_count - 1) + gap * (player_count - 1)
            sx = center_x - total_w // 2
            px = sx
            for j in range(i):
                pw = int(base_card_w * 1.15) if (winner and engine.players[j].name == winner.name) else base_card_w
                px += pw + gap

            # ── Winner sparkle particles ──
            if is_win:
                self._draw_sparkles(surface, px + cw // 2, cy + ch // 2, cw, ch)

            # Winner outer glow (Neon effect)
            if is_win:
                ga = int(40 + 20 * math.sin(self.time_alive * 4))
                gs = pygame.Surface((cw + 30, ch + 30), pygame.SRCALPHA)
                pygame.draw.rect(gs, (*Colors.TEXT_GOLD, ga), (0, 0, cw + 30, ch + 30), border_radius=24)
                surface.blit(gs, (px - 15, cy - 15))

            # Card background (Glassmorphic)
            card = pygame.Surface((cw, ch), pygame.SRCALPHA)
            bg_color = (25, 30, 50, 200) if is_win else (15, 18, 30, 180)
            pygame.draw.rect(card, bg_color, (0, 0, cw, ch), border_radius=20)
            
            # 1px Border (Thicker for winner)
            border_color = (*Colors.TEXT_GOLD, 180) if is_win else (255, 255, 255, 30)
            border_w = 2 if is_win else 1
            pygame.draw.rect(card, border_color, (0, 0, cw, ch), width=border_w, border_radius=20)

            # Top glass highlight
            pygame.draw.rect(card, (255, 255, 255, 20), (0, 0, cw, 40), border_radius=20)

            surface.blit(card, (px, cy))

            # ── Crown for winner ──
            if is_win:
                self._draw_crown(surface, px + cw // 2, cy - 15, 26)

            # ── Avatar ──
            av_r = 34 if is_win else 28
            av_cx = px + cw // 2
            av_cy = cy + 42 if is_win else cy + 36
            medal_colors = {1: (255, 215, 0), 2: (192, 192, 210), 3: (205, 127, 50)}
            av_border = medal_colors.get(rank, (70, 75, 95))
            self._draw_avatar_circle(surface, av_cx, av_cy, av_r,
                                     self.avatars[i] if i < len(self.avatars) else None,
                                     border_color=av_border, border_w=3)

            # ── Rank Medal (top-right of avatar) ──
            medal_x = av_cx + av_r - 4
            medal_y = av_cy - av_r + 4
            self._draw_rank_medal(surface, medal_x, medal_y, rank, medal_colors.get(rank, (100, 100, 100)))

            # ── Player Name & Rank ──
            nc = Colors.TEXT_GOLD if is_win else Colors.TEXT_WHITE
            ns = self.font_body.render(p_name.upper(), True, nc)
            surface.blit(ns, (px + cw // 2 - ns.get_width() // 2, av_cy + av_r + 10))
            
            # Show Rank Title
            rank_title = player_rank if i == 0 else getattr(player_obj, 'rank', "PRO")
            rs = self.font_small.render(rank_title, True, (160, 160, 180))
            surface.blit(rs, (px + cw // 2 - rs.get_width() // 2, av_cy + av_r + 32))

            # ── Points (Modernized) ──
            pts_str = str(score)
            pc = Colors.TEXT_GOLD if is_win else (255, 255, 255)
            ps = self.font_title.render(pts_str, True, pc)
            pl = self.font_btn.render("PTS", True, (160, 160, 180))
            
            pts_y = av_cy + av_r + 48
            
            # Side-by-side layout to prevent overlap and look sleek
            total_w = ps.get_width() + 8 + pl.get_width()
            start_x = px + cw // 2 - total_w // 2
            
            # Subtle glow behind the number
            glow = self.font_title.render(pts_str, True, (*pc[:3], 40))
            surface.blit(glow, (start_x + 2, pts_y + 2))
            surface.blit(ps, (start_x, pts_y))
            
            # Align "PTS" near the baseline of the large number
            pts_label_y = pts_y + ps.get_height() - pl.get_height() - 8
            surface.blit(pl, (start_x + ps.get_width() + 8, pts_label_y))

            # ── Revealed Cards ──
            hand = player_obj.hand
            if hand:
                ca_y = pts_y + 110
                ca_h = 70
                
                # Inset card panel
                inset_w = cw - 30
                pygame.draw.rect(surface, (10, 12, 20, 150), (px + 15, ca_y, inset_w, ca_h), border_radius=12)
                pygame.draw.rect(surface, (255, 255, 255, 15), (px + 15, ca_y, inset_w, ca_h), width=1, border_radius=12)

                ms = 0.24
                si = get_card_image(hand[0], ms)
                cpw = si.get_width() if si else 30
                cph = si.get_height() if si else 44

                olap = min(16, max(5, (inset_w - 20 - cpw) // max(len(hand) - 1, 1))) if len(hand) > 1 else 0
                thw = (len(hand) - 1) * olap + cpw
                hx = px + cw // 2 - thw // 2
                hy = ca_y + (ca_h - cph) // 2

                for j, card in enumerate(hand):
                    im = get_card_image(card, ms)
                    if im:
                        surface.blit(im, (hx + j * olap, hy))

            # ── Status Badge (Pill Style) ──
            status_text = "LOST"
            status_color = (120, 140, 180)

            if is_win:
                status_text = "WINNER"
                status_color = Colors.TEXT_GOLD
            elif player_obj.is_burned:
                status_text = "BURNED"
                status_color = Colors.BURN_RED
            elif statuses and p_name in statuses:
                status_text = statuses[p_name]
                sc_map = {
                    "WINNER": Colors.TEXT_GOLD, "CALLER": (200, 100, 255),
                    "CHALLENGED": (100, 200, 255), "FOUGHT": (100, 200, 255),
                    "FOLDED": (140, 150, 160), "BURNED": Colors.BURN_RED
                }
                status_color = sc_map.get(status_text, status_color)

            bw = max(90, len(status_text) * 10 + 20)
            bh = 26
            bx = px + cw // 2 - bw // 2
            by = cy + ch - 35

            # Semi-transparent fill with full-opacity border
            pygame.draw.rect(surface, (*status_color, 30), (bx, by, bw, bh), border_radius=bh // 2)
            pygame.draw.rect(surface, (*status_color, 180), (bx, by, bw, bh), width=1, border_radius=bh // 2)

            st = self.font_small.render(status_text, True, status_color)
            surface.blit(st, (px + cw // 2 - st.get_width() // 2, by + bh // 2 - st.get_height() // 2))

        # ── Premium Action Buttons ──
        self._draw_gradient_btn(
            surface, self.play_again_rect, "PLAY AGAIN",
            (50, 185, 95), (30, 130, 65), self._pa_hover, "▶"
        )
        self._draw_gradient_btn(
            surface, self.lobby_rect, "LOBBY",
            (60, 110, 200), (40, 75, 150), self._lb_hover, "◀"
        )


# ─── Meld Display ────────────────────────────────────────────────────

class MeldDisplay:
    """Renders a group of melds on the table."""
    @staticmethod
    def draw_meld(surface, cards, x, y, card_w, card_h, get_image_fn, scale=0.6):
        overlap = int(card_w * scale * 0.55)
        for i, card in enumerate(cards):
            img = get_image_fn(card)
            if img:
                scaled = pygame.transform.scale(img, (int(card_w * scale), int(card_h * scale)))
                surface.blit(scaled, (x + i * overlap, y))

    @staticmethod
    def draw_all_melds(surface, table_melds, center_x, start_y, card_w, card_h, get_image_fn, font):
        if not table_melds: return
        meld_spacing_y = int(card_h * 0.6) + 15
        melds_per_row = 4
        overlap = int(card_w * 0.6 * 0.55)

        for idx, tmeld in enumerate(table_melds):
            row = idx // melds_per_row
            col = idx % melds_per_row
            meld_w = overlap * len(tmeld.cards) + int(card_w * 0.6 * 0.45)
            total_row_w = melds_per_row * (meld_w + 20)
            base_x = center_x - total_row_w // 2
            mx = base_x + col * (meld_w + 20)
            my = start_y + row * meld_spacing_y
            label = font.render(tmeld.owner.name[:6], True, Colors.TEXT_MUTED)
            surface.blit(label, (mx, my - 14))
            MeldDisplay.draw_meld(surface, tmeld.cards, mx, my, card_w, card_h, get_image_fn)
