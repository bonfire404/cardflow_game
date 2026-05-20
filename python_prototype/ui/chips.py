import os
import pygame
import math
import random

# Mapping of file names to their assumed denominations
CHIP_FILE_NAMES = [
    (5000, "front_5000.png"),
    (1000, "front_1000.png"),
    (500, "front_500.png"),
    (100, "front_100.png"),
    (25, "front_25.png"),
    (10, "front_10.png"),
    (5, "front_5.png"),
    (1, "front_1.png"),
]

class ChipSystem:
    def __init__(self, assets_dir):
        self.chips_dir = os.path.join(assets_dir, "Casino", "Chips")
        self.chip_images = {}
        for val, fname in CHIP_FILE_NAMES:
            path = os.path.join(self.chips_dir, fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    # Scale down the chips to fit well on the table without overlapping
                    self.chip_images[val] = pygame.transform.smoothscale(img, (36, 36))
                except Exception as e:
                    print(f"Error loading {fname}: {e}")
        
        self.main_pot = 0
        self.banker_pot = 0
        
        # Physical positions on the table
        self.main_pot_display = []
        self.banker_pot_display = {'amount': 0, 'x': 0, 'y': 0}
        
        # Load Dealer Image
        dealer_path = os.path.join(assets_dir, "images", "banker.png")
        if os.path.exists(dealer_path):
            self.dealer_img = pygame.transform.smoothscale(pygame.image.load(dealer_path).convert_alpha(), (60, 60))
        else:
            self.dealer_img = None
        
        # Simple font for label
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 12, bold=True)
        self.tooltip_font = pygame.font.SysFont("Arial", 14, bold=True)
        
        # Hover state
        self.hover_timer = 0.0
        self.hovered_bet = None # {amount, x, y}
        self.last_mouse_pos = (0, 0)
        
    def breakdown_amount(self, amount):
        breakdown = []
        rem = amount
        for val, fname in sorted(CHIP_FILE_NAMES, key=lambda x: -x[0]):
            if val not in self.chip_images:
                continue
            count = rem // val
            for _ in range(count):
                breakdown.append(val)
            rem %= val
            
        if rem > 0 and self.chip_images:
            min_val = min(self.chip_images.keys())
            breakdown.append(min_val)
            
        return breakdown

    def draw_chip_stack(self, surface, amount_or_chips, base_x, base_y):
        if isinstance(amount_or_chips, list):
            if not amount_or_chips: return
            chips = amount_or_chips[:]
            amount = sum(chips)
        else:
            if amount_or_chips <= 0: return
            chips = self.breakdown_amount(amount_or_chips)
            amount = amount_or_chips
            
        chips.sort(reverse=True)
        
        MAX_PER_STACK = 8
        stacks = [chips[i:i + MAX_PER_STACK] for i in range(0, len(chips), MAX_PER_STACK)]
        
        import random
        for i, stack in enumerate(stacks):
            stack_x = base_x + (i * 22) - (len(stacks) * 11)
            stack_y = base_y
            
            if not stack: continue
            
            # Draw one unified soft oval shadow for the whole stack
            img = self.chip_images.get(stack[0])
            if img:
                w, h = img.get_size()
                shadow = pygame.Surface((w+10, int(h*0.6)), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow, (0, 0, 0, 100), (0, 0, w+10, int(h*0.6)))
                surface.blit(shadow, (stack_x - 5, stack_y + h//2 - 5))
            
            # Use deterministic seed based on stack properties so they don't jitter
            random.seed(amount * 100 + i)
            base_offset_x = random.uniform(-1, 1)
            base_offset_y = random.uniform(-1, 1)
            
            for j, val in enumerate(stack):
                img = self.chip_images.get(val)
                if img:
                    # Slight imperfection per chip
                    random.seed(amount * 1000 + i * 100 + j)
                    cx = stack_x + base_offset_x + random.uniform(-0.5, 0.5)
                    cy = stack_y + base_offset_y - (j * 3.5) # stack them upwards
                    surface.blit(img, (cx, cy))
                    
        # Reset random seed
        random.seed()

    def update_layout(self, layout):
        self.banker_pot_display['x'] = layout['deck_x'] + (layout['discard_x'] - layout['deck_x']) // 2 - 20
        self.banker_pot_display['y'] = layout['deck_y'] - 65
        
        if len(self.main_pot_display) == 3:
            self.main_pot_display[0]['x'] = layout['hand_center_x'] + 220
            self.main_pot_display[0]['y'] = layout['hand_y'] - 130
            self.main_pot_display[1]['x'] = layout['bot1_x'] - 180
            self.main_pot_display[1]['y'] = layout['bot1_y'] + 140
            self.main_pot_display[2]['x'] = layout['bot2_x'] + 180
            self.main_pot_display[2]['y'] = layout['bot2_y'] + 140

    def _generate_realistic_chips(self, amount, custom_source=None):
        """Generates a variety of chips to make a stack look 'natural'."""
        if amount <= 0: return []
        
        # If we have a custom source (like user's bet), try to 'double' it for variety
        if custom_source and isinstance(custom_source, list) and sum(custom_source) * 2 == amount:
            return custom_source * 2
            
        available_vals = sorted(self.chip_images.keys(), reverse=True)
        available = [val for val in available_vals if val <= amount]
        if not available: return [amount] if amount > 0 else []
        
        chips = []
        remaining = amount
       
        # 1. Pick a substantial starting chip
        if available:
            if len(available) > 1 and random.random() > 0.3:
                # 70% chance to start with the second largest chip to force a stack
                first = available[1]
            else:
                first = available[0]
            chips.append(first)
            remaining -= first
        
        # 2. Fill randomly for variety but keep a reasonable count (max ~2 stacks)
        while remaining > 0 and len(chips) < 12:
            valid_picks = [v for v in available if v <= remaining]
            if not valid_picks: break
            pick = random.choice(valid_picks)
            chips.append(pick)
            remaining -= pick
        
        # 3. Final greedy fill to ensure sum is EXACT
        for val in available_vals:
            while remaining >= val:
                chips.append(val)
                remaining -= val
        
        return chips

    def _generate_minimalist_chips(self, amount):
        """Greedily uses highest possible chips to keep the table clean."""
        # Only use higher denominations (>=100) if possible
        banker_denoms = sorted([val for val in self.chip_images.keys() if val >= 100], reverse=True)
        if not banker_denoms:
            banker_denoms = sorted(self.chip_images.keys(), reverse=True)
        
        chips = []
        remaining = amount
        
        for val in banker_denoms:
            while remaining >= val:
                chips.append(val)
                remaining -= val
        
        # Any remaining change
        if remaining > 0:
            all_denoms = sorted(self.chip_images.keys(), reverse=True)
            for v in all_denoms:
                while remaining >= v:
                    chips.append(v)
                    remaining -= v
        
        return chips

    def add_bets(self, bet_amount, layout, banker_bet_amount=100, custom_chips=None, dealer_idx=0):
        self.main_pot += bet_amount * 3
        banker_contribution = banker_bet_amount * 2
        self.banker_pot += banker_contribution
        self.update_layout(layout)

        # 1. Player/Bot bets always use 'realistic' variety
        total_per_player = self.main_pot // 3
        player_val = custom_chips if custom_chips else self._generate_realistic_chips(total_per_player)
        bot1_val = self._generate_realistic_chips(total_per_player)
        bot2_val = self._generate_realistic_chips(total_per_player)
        
        self.main_pot_display = [
            {'val': player_val, 'x': layout['hand_center_x'] + 220, 'y': layout['hand_y'] - 130}, 
            {'val': bot1_val, 'x': layout['bot1_x'] - 180, 'y': layout['bot1_y'] + 140}, 
            {'val': bot2_val, 'x': layout['bot2_x'] + 180, 'y': layout['bot2_y'] + 140}
        ]

        # 2. Banker Pot logic: Realistic early on, compressed later
        if not isinstance(self.banker_pot_display.get('amount'), list):
            self.banker_pot_display['amount'] = []

        # Generate new contribution
        # Use custom_chips ONLY if the player is the dealer (idx 0)
        source = custom_chips if dealer_idx == 0 else None
        new_banker_chips = self._generate_realistic_chips(banker_contribution, custom_source=source)
        self.banker_pot_display['amount'].extend(new_banker_chips)

        
    def reset_main_pot(self):
        self.main_pot = 0
        self.main_pot_display = []
        
    def reset_banker_pot(self):
        self.banker_pot = 0
        self.banker_pot_display['amount'] = 0

    def update(self, dt, mouse_pos):
        # Update hover timer
        if mouse_pos == self.last_mouse_pos:
            self.hover_timer += dt
        else:
            self.hover_timer = 0
            self.hovered_bet = None
        self.last_mouse_pos = mouse_pos

        if self.hover_timer >= 1.0 and not self.hovered_bet:
            # Check all bets
            mx, my = mouse_pos
            
            # Check main pot display
            for bet in self.main_pot_display:
                if not bet.get('val'): continue
                bx, by = bet['x'], bet['y']
                # Rough hit box for the stack cluster
                val = bet['val']
                chips = val if isinstance(val, list) else self.breakdown_amount(val)
                n_stacks = (len(chips) + 7) // 8
                width = 22 * n_stacks + 14
                rect = pygame.Rect(bx - 11 * n_stacks, by - 20, width, 56)
                if rect.collidepoint(mx, my):
                    self.hovered_bet = {'amount': sum(chips) if isinstance(val, list) else val, 'x': bx, 'y': by}
                    return

            # Check banker pot
            amt = self.banker_pot_display['amount']
            if (isinstance(amt, list) and amt) or (isinstance(amt, int) and amt > 0):
                bx, by = self.banker_pot_display['x'], self.banker_pot_display['y']
                chips = amt if isinstance(amt, list) else self.breakdown_amount(amt)
                n_stacks = (len(chips) + 7) // 8
                width = 22 * n_stacks + 14
                rect = pygame.Rect(bx - 11 * n_stacks, by - 10, width, 56)
                if rect.collidepoint(mx, my):
                    self.hovered_bet = {'amount': sum(chips) if isinstance(amt, list) else amt, 'x': bx, 'y': by}
                    return

    def _draw_tooltip(self, surface, amount, x, y):
        txt = f"{amount:,}"
        text_surf = self.tooltip_font.render(txt, True, (255, 255, 255))
        
        padding_x, padding_y = 12, 8
        w = text_surf.get_width() + padding_x * 2
        h = text_surf.get_height() + padding_y * 2
        
        # Position above the chips
        tx = x - w // 2
        ty = y - h - 30
        
        # Draw background with rounded corners and border
        # Shadow
        shadow_rect = pygame.Rect(tx + 3, ty + 3, w, h)
        pygame.draw.rect(surface, (0, 0, 0, 100), shadow_rect, border_radius=8)
        
        # Main Box (Glassmorphism look)
        bg_rect = pygame.Rect(tx, ty, w, h)
        pygame.draw.rect(surface, (30, 30, 40, 230), bg_rect, border_radius=8)
        pygame.draw.rect(surface, (200, 180, 50), bg_rect, width=2, border_radius=8) # Gold border
        
        # Text
        surface.blit(text_surf, (tx + padding_x, ty + padding_y))

    def draw(self, surface):
        for bet in self.main_pot_display:
            if bet.get('val'):
                val = bet['val']
                if isinstance(val, list) or val > 0:
                    self.draw_chip_stack(surface, val, bet['x'], bet['y'])

        amt = self.banker_pot_display['amount']
        if (isinstance(amt, list) and amt) or (isinstance(amt, int) and amt > 0):
            bx, by = self.banker_pot_display['x'], self.banker_pot_display['y']
            self.draw_chip_stack(surface, amt, bx, by + 10)
            # Draw actual Dealer chip image
            if hasattr(self, 'dealer_img') and self.dealer_img:
                surface.blit(self.dealer_img, (bx + 18 - 20, by + 50))

        # Finally draw hovered tooltip if any
        if self.hovered_bet and self.hover_timer >= 1.0:
            self._draw_tooltip(surface, self.hovered_bet['amount'], self.hovered_bet['x'], self.hovered_bet['y'])
            self._draw_tooltip(surface, self.hovered_bet['amount'], self.hovered_bet['x'], self.hovered_bet['y'])
