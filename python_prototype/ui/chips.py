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
        dealer_path = os.path.join("assets", "images", "banker.png")
        if os.path.exists(dealer_path):
            self.dealer_img = pygame.transform.smoothscale(pygame.image.load(dealer_path).convert_alpha(), (60, 60))
        else:
            self.dealer_img = None
        
        # Simple font for label
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 12, bold=True)
        
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

    def draw_chip_stack(self, surface, amount_or_chips, base_x, base_y, scale=1.0):
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
            stack_x = base_x + (i * 22 * scale) - (len(stacks) * 11 * scale)
            stack_y = base_y
            
            if not stack: continue
            
            # Draw one unified soft oval shadow for the whole stack
            img = self.chip_images.get(stack[0])
            if img:
                if scale != 1.0:
                    img = pygame.transform.smoothscale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
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
                    if scale != 1.0:
                        img = pygame.transform.smoothscale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                    # Slight imperfection per chip
                    random.seed(amount * 1000 + i * 100 + j)
                    cx = stack_x + base_offset_x + random.uniform(-0.5, 0.5)
                    cy = stack_y + base_offset_y - (j * 3.5 * scale) # stack them upwards
                    surface.blit(img, (cx, cy))
                    
        # Reset random seed
        random.seed()

    def update_layout(self, layout):
        self.banker_pot_display['x'] = layout['deck_x'] + (layout['discard_x'] - layout['deck_x']) // 2 - 20
        self.banker_pot_display['y'] = layout['deck_y'] - 65

    def add_bets(self, bet_amount, layout, banker_total=100, custom_chips=None):
        """Sets the visual state of the chips based on the current pots."""
        self.main_pot = bet_amount * 3
        self.banker_pot = banker_total
        self.update_layout(layout)

        # Place bets near the players so the middle only has the banker pot
        total_per_player = self.main_pot // 3
        player_val = custom_chips if custom_chips else total_per_player
        
        # Helper to generate randomized chip combinations for bots that sum exactly to total
        def generate_random_chips(amount):
            import random
            # Dynamically adjust cap to prevent 'flooding' the table with hundreds of small chips
            chip_cap = 100
            if amount > 5000: chip_cap = 1000
            elif amount > 2000: chip_cap = 500
            
            available_chip_values = [val for val, _ in CHIP_FILE_NAMES if val <= chip_cap]
            available = [val for val in available_chip_values if val <= amount]
            if not available: return amount
            
            chips = []
            remaining = amount
            # Use deterministic largest chips first for bulk
            for v in sorted(available_chip_values, reverse=True):
                if v > 100: # Only use high-value chips for the bulk
                    count = remaining // v
                    if count > 0:
                        chips.extend([v] * count)
                        remaining %= v
            
            while remaining > 0:
                viable = [v for v in available_chip_values if v <= remaining]
                if not viable: break
                c = random.choice(viable)
                chips.append(c)
                remaining -= c
            return chips
        
        bot1_val = generate_random_chips(total_per_player)
        bot2_val = generate_random_chips(total_per_player)
        
        self.main_pot_display = [
            {'val': player_val, 'x': layout['hand_center_x'] + 230, 'y': layout['hand_y'] - 60}, # Player (pushed further right)
            {'val': bot1_val, 'x': layout['bot1_x'] - 160, 'y': layout['bot1_y'] + 110}, # Bot 1 (Right side, push left)
            {'val': bot2_val, 'x': layout['bot2_x'] + 160, 'y': layout['bot2_y'] + 110}  # Bot 2 (Left side, push right)
        ]
        self.banker_pot_display['amount'] = generate_random_chips(self.banker_pot) if self.banker_pot > 0 else 0
        
    def reset_main_pot(self):
        self.main_pot = 0
        self.main_pot_display = []
        
    def reset_banker_pot(self):
        self.banker_pot = 0
        self.banker_pot_display['amount'] = 0

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
