import pygame
import math


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
    TEXT_GOLD = (255, 215, 0)
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
    CARD_GLOW = (255, 215, 0, 100)
    CARD_SELECTED = (100, 200, 255, 150)
    CARD_HOVER = (255, 255, 255, 60)

    # Phase indicator
    PHASE_ACTIVE = (80, 200, 120)
    PHASE_INACTIVE = (80, 80, 95)
    PHASE_DONE = (60, 60, 70)

    # Ribbon / Grouping
    RIBBON_RED = (200, 30, 45)
    RIBBON_GOLD = (218, 165, 32)
    RIBBON_SHADOW = (120, 15, 25)

    # Player status
    BURN_RED = (255, 60, 40)
    SAFE_GREEN = (60, 220, 100)

    # Overlay
    OVERLAY_BG = (10, 10, 20, 180)


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

    def is_clicked(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


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

class PlayerPanel:
    """Displays player name, card count, burn status, and points."""
    def __init__(self, font_name, font_stats):
        self.font_name = font_name
        self.font_stats = font_stats

    def draw(self, surface, x, y, player, is_active=False, show_points=False, align='center', avatar_surf=None, show_burned=False, timer_progress=0.0, is_dealer=False, dealer_img=None):
        # Modern Layout Dimensions
        pw, ph = 240, 80
        if align == 'center': px = x - pw // 2
        elif align == 'left': px = x
        else: px = x - pw
        py = y

        # --- 1. Panel Background (Modern Glassmorphism) ---
        panel_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg_alpha = 240 if is_active else 180
        pygame.draw.rect(panel_surf, (18, 22, 36, bg_alpha), (0, 0, pw, ph), border_radius=18)
        pygame.draw.rect(panel_surf, (255, 255, 255, 30), (0, 0, pw, ph), width=1, border_radius=18)
        
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

        # --- 3. Text & Stats ---
        text_off_x = av_x + target_size + 14
        
        name_color = Colors.TEXT_GOLD if is_active else Colors.TEXT_WHITE
        name_surf = self.font_name.render(player.name, True, name_color)
        surface.blit(name_surf, (text_off_x, py + 12))

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
    """Overlay showing when a fight is called, asking the user to Fight or Fold."""
    def __init__(self, width, height, font_title, font_body, font_btn):
        self.width = width
        self.height = height
        self.font_title = font_title
        self.font_body = font_body
        self.font_btn = font_btn
        self.alpha = 0
        self.target_alpha = 255
        self.fade_speed = 600

        btn_w, btn_h = 240, 55
        self.btn_fight = Button(
            width // 2 - btn_w - 20, height // 2 + 100, btn_w, btn_h,
            "FIGHT", font_btn,
            color=Colors.BTN_SUCCESS, hover_color=Colors.BTN_SUCCESS_HOVER
        )
        self.btn_fold = Button(
            width // 2 + 20, height // 2 + 100, btn_w, btn_h,
            "FOLD", font_btn,
            color=Colors.BTN_DANGER, hover_color=Colors.BTN_DANGER_HOVER
        )

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        btn_w, btn_h = 240, 55
        self.btn_fight.rect.x = width // 2 - btn_w - 20
        self.btn_fight.rect.y = height // 2 + 100
        self.btn_fold.rect.x = width // 2 + 20
        self.btn_fold.rect.y = height // 2 + 100

    def update(self, dt, mouse_pos):
        self.alpha = min(self.alpha + self.fade_speed * dt, self.target_alpha)
        self.btn_fight.update(mouse_pos, dt)
        self.btn_fold.update(mouse_pos, dt)

    def draw(self, surface, active_fight, points, players):
        caller = active_fight['caller'] if isinstance(active_fight, dict) else active_fight

        # Full Screen Cinematic Backdrop
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((5, 10, 20, int(self.alpha * 0.9)))
        surface.blit(overlay, (0, 0))

        if self.alpha < 50: return

        # Large Header Banners
        header_y = self.height // 2 - 200
        pygame.draw.rect(surface, (40, 20, 20, self.alpha), (0, header_y, self.width, 140))
        pygame.draw.line(surface, Colors.TEXT_RED, (0, header_y), (self.width, header_y), 2)
        pygame.draw.line(surface, Colors.TEXT_RED, (0, header_y + 140), (self.width, header_y + 140), 2)

        title = "⚔️ FIGHT CHALLENGE! ⚔️"
        t_surf = self.font_title.render(title, True, Colors.TEXT_RED)
        surface.blit(t_surf, (self.width // 2 - t_surf.get_width() // 2, header_y + 35))

        subtitle = f"{caller.name} has challenged the table!"
        sub_surf = self.font_body.render(subtitle.upper(), True, Colors.TEXT_WHITE)
        surface.blit(sub_surf, (self.width // 2 - sub_surf.get_width() // 2, header_y + 90))

        # Status Info
        pts_text = f"YOUR POINTS: {points}"
        pts_surf = self.font_title.render(pts_text, True, Colors.TEXT_GOLD)
        surface.blit(pts_surf, (self.width // 2 - pts_surf.get_width() // 2, header_y + 180))

        hint = "CONCEDE (FOLD) AND PAY MINIMUM, OR CHALLENGE (FIGHT) TO WIN IT ALL!"
        hint_surf = self.font_body.render(hint, True, Colors.TEXT_MUTED)
        surface.blit(hint_surf, (self.width // 2 - hint_surf.get_width() // 2, header_y + 240))

        self.btn_fight.draw(surface)
        self.btn_fold.draw(surface)


class GameOverOverlay:
    """Full-screen result board with cinematic backdrop and player status cards."""
    def __init__(self, width, height, font_title, font_body, font_btn):
        self.width = width
        self.height = height
        self.font_title = font_title
        self.font_body = font_body
        self.font_btn = font_btn
        self.alpha = 0
        self.target_alpha = 255
        self.fade_speed = 600

        self.play_again_btn = Button(
            width // 2 - 250, height - 100, 240, 55,
            "PLAY AGAIN", font_btn,
            color=Colors.BTN_SUCCESS,
            hover_color=Colors.BTN_SUCCESS_HOVER,
        )
        self.lobby_btn = Button(
            width // 2 + 10, height - 100, 240, 55,
            "LOBBY", font_btn,
            color=Colors.BTN_PRIMARY,
            hover_color=Colors.BTN_PRIMARY_HOVER,
        )

    def reposition(self, width, height):
        self.width = width
        self.height = height
        self.play_again_btn.rect.x = width // 2 - 250
        self.play_again_btn.rect.y = height - 100
        self.lobby_btn.rect.x = width // 2 + 10
        self.lobby_btn.rect.y = height - 100

    def update(self, dt, mouse_pos):
        self.alpha = min(self.alpha + self.fade_speed * dt, self.target_alpha)
        self.play_again_btn.update(mouse_pos, dt)
        self.lobby_btn.update(mouse_pos, dt)

    def draw(self, surface, winner, win_method, scores, engine, get_card_image, statuses=None):
        # 1. High-end Backdrop (Translucent for transparency)
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((8, 12, 24, int(self.alpha * 0.75)))
        surface.blit(overlay, (0, 0))

        if self.alpha < 40: return

        # 2. Hero Header
        banner_y = 60
        pygame.draw.rect(surface, (25, 30, 50, self.alpha), (0, banner_y, self.width, 140))
        pygame.draw.line(surface, Colors.TEXT_GOLD, (0, banner_y), (self.width, banner_y), 2)
        pygame.draw.line(surface, Colors.TEXT_GOLD, (0, banner_y + 140), (self.width, banner_y + 140), 2)
        
        main_text = f"{winner.name.upper()} WINS!" if winner else "GAME DRAWN"
        title_surf = self.font_title.render(main_text, True, Colors.TEXT_GOLD)
        surface.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, banner_y + 25))
        
        method_labels = {
            'tongits': '🏆 TONG-ITS! 🏆',
            'fight': '⚔️ FIGHT CHALLENGE! ⚔️',
            'fight_won': '⚔️ FIGHT RESOLVED! ⚔️',
            'fight_lost': '⚔️ FIGHT RESOLVED! ⚔️',
            'deck_empty': '🎴 DECK DEPLETED! 🎴'
        }
        method_text = method_labels.get(win_method, win_method.upper())
        method_surf = self.font_body.render(method_text, True, Colors.TEXT_WHITE)
        surface.blit(method_surf, (self.width // 2 - method_surf.get_width() // 2, banner_y + 85))

        # 3. Result Board (Backdrop style cards)
        card_w, card_h = 320, 260
        gap = 40
        player_count = len(scores)
        total_w = (card_w * player_count) + (gap * (player_count - 1))
        start_x = self.width // 2 - total_w // 2
        card_y = banner_y + 140 + 60

        for i, player in enumerate(engine.players):
            px = start_x + i * (card_w + gap)
            p_name = player.name
            score = scores.get(p_name, 0)
            is_win = (winner and p_name == winner.name)
            
            # Card Base
            card_bg = (32, 38, 58, self.alpha) if not is_win else (45, 55, 95, self.alpha)
            pygame.draw.rect(surface, card_bg, (px, card_y, card_w, card_h), border_radius=18)
            if is_win:
                pygame.draw.rect(surface, Colors.TEXT_GOLD, (px, card_y, card_w, card_h), width=3, border_radius=18)

            # Name
            name_surf = self.font_body.render(p_name.upper(), True, Colors.TEXT_WHITE)
            surface.blit(name_surf, (px + card_w // 2 - name_surf.get_width() // 2, card_y + 20))
            
            # Points Display
            pts_surf = self.font_title.render(str(score), True, Colors.TEXT_GOLD)
            surface.blit(pts_surf, (px + card_w // 2 - pts_surf.get_width() // 2, card_y + 55))
            
            # --- Revealed Cards ---
            mini_scale = 0.35
            overlap = 18
            hand = player.hand
            hx = px + card_w // 2 - (len(hand) * overlap + 20) // 2
            hy = card_y + 105
            for j, card in enumerate(hand):
                im = get_card_image(card, mini_scale)
                if im:
                    surface.blit(im, (hx + j * overlap, hy))

            # Dynamic Status Badge
            status_text = "LOST"
            status_color = (120, 180, 255)
            
            if is_win:
                status_text = "WINNER"
                status_color = Colors.TEXT_GOLD
            elif player.is_burned or score > 50:
                status_text = "BURNED"
                status_color = Colors.BURN_RED
            elif statuses and p_name in statuses:
                status_text = statuses[p_name]
                # High-end color mapping for fight statuses
                sc_map = {
                    "CALLER": (200, 100, 255),
                    "FOUGHT": (100, 200, 255),
                    "FOLDED": (140, 150, 160)
                }
                status_color = sc_map.get(status_text, status_color)
            elif engine.active_fight:
                caller = engine.active_fight.get('caller')
                responses = engine.active_fight.get('responses', {})
                if player == caller:
                    status_text = "CHALLENGER"
                    status_color = (200, 100, 255)
                elif player in responses:
                    resp = responses[player]
                    status_text = "FOUGHT" if resp == 'fight' else "FOLDED"
                    status_color = (100, 200, 255) if resp == 'fight' else (140, 150, 160)
            
            pygame.draw.rect(surface, (*status_color, 40), (px + 40, card_y + card_h - 45, card_w - 80, 30), border_radius=8)
            st_surf = self.font_body.render(status_text, True, status_color)
            surface.blit(st_surf, (px + card_w // 2 - st_surf.get_width() // 2, card_y + card_h - 40))

        # 4. Action
        self.play_again_btn.draw(surface)
        self.lobby_btn.draw(surface)


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
