import os
import random
import pygame
import math

class DealerManager:
    """Manages dealer state, rotation, and visual representation."""
    def __init__(self, assets_dir):
        self.dealer_idx = 0
        self.win_streak = 0 # Track consecutive wins for the breathing effect
        self.chip_image = None
        self._load_assets(assets_dir)

    def _load_assets(self, assets_dir):
        path = os.path.join(assets_dir, "Casino", "Chips", "Dealer.png")
        try:
            raw = pygame.image.load(path).convert_alpha()
            # Slightly larger to be visible on the table bumper
            self.chip_image = pygame.transform.smoothscale(raw, (42, 42))
        except Exception as e:
            print(f"Error loading dealer chip: {e}")
            self.chip_image = None

    def randomize(self):
        """Choose a dealer randomly (used when starting from lobby)."""
        self.dealer_idx = random.randint(0, 2)
        self.win_streak = 0 # No streak on fresh start
        return self.dealer_idx

    def rotate(self):
        """Move dealer to the next player (used for Play Again on Draw)."""
        self.dealer_idx = (self.dealer_idx + 1) % 3
        self.win_streak = 0 # Streak lost if they didn't win
        return self.dealer_idx

    def get_idx(self):
        return self.dealer_idx

    def set_idx(self, idx):
        """Update dealer based on winner. Tracks consecutive wins."""
        if self.dealer_idx == idx:
            self.win_streak += 1
        else:
            self.dealer_idx = idx
            self.win_streak = 1 # First win in a row
        return self.dealer_idx

    def draw(self, surface, x, y):
        """Draw the dealer chip. Breathes if on a win streak of 2+."""
        if self.chip_image:
            cw, ch = self.chip_image.get_size()
            
            # Subtle Shadow
            shadow_surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
            pygame.draw.circle(shadow_surf, (0, 0, 0, 90), (cw//2, ch//2), cw//2)
            surface.blit(shadow_surf, (x + 3, y + 3))

            # --- "Hot Streak" Breathing Animation (Only if won 2+ times in a row) ---
            if self.win_streak >= 2:
                ticks = pygame.time.get_ticks()
                # Soft, minimalist breathing (scale ±5%)
                scale = 1.0 + 0.05 * math.sin(ticks * 0.005)
                
                nw = int(cw * scale)
                nh = int(ch * scale)
                
                # Center the scaled image
                off_x = (nw - cw) // 2
                off_y = (nh - ch) // 2
                
                breathing_chip = pygame.transform.smoothscale(self.chip_image, (nw, nh))
                surface.blit(breathing_chip, (x - off_x, y - off_y))
            else:
                # Base Chip
                surface.blit(self.chip_image, (x, y))
    def get_deal_sequence(self):
        """
        Calculates the deal order based on dealer:
        Starts with the player to the left of the dealer (dealer+1),
        then the player to the right (dealer+2), then the dealer last.
        Standard Tong-its deal: 12 cards each, 13th to the dealer.
        """
        others = [(self.dealer_idx + 1) % 3, (self.dealer_idx + 2) % 3]
        round_order = others + [self.dealer_idx]
        
        sequence = []
        for _ in range(12):
            sequence.extend(round_order)
        sequence.append(self.dealer_idx) # 13th card to dealer
        return sequence
