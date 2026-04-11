import os
import random
import pygame

class DealerManager:
    """Manages dealer state, rotation, and visual representation."""
    def __init__(self, assets_dir):
        self.dealer_idx = 0
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
        return self.dealer_idx

    def rotate(self):
        """Move dealer to the next player (used for Play Again)."""
        self.dealer_idx = (self.dealer_idx + 1) % 3
        return self.dealer_idx

    def get_idx(self):
        return self.dealer_idx

    def draw(self, surface, x, y):
        """Draw the dealer chip with a subtle glow for visibility on the table."""
        if self.chip_image:
            cw, ch = self.chip_image.get_size()
            
            # 1. Subtle Outer Glow/Ring
            glow_surf = pygame.Surface((cw + 8, ch + 8), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 255, 255, 40), (cw//2 + 4, ch//2 + 4), cw//2 + 2)
            pygame.draw.circle(glow_surf, (255, 215, 0, 60), (cw//2 + 4, ch//2 + 4), cw//2 + 1, width=2)
            surface.blit(glow_surf, (x - 4, y - 4))

            # 2. Subtle Shadow
            shadow_offset = 2
            shadow_surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
            pygame.draw.circle(shadow_surf, (0, 0, 0, 100), (cw//2, ch//2), cw//2)
            surface.blit(shadow_surf, (x + shadow_offset, y + shadow_offset))
            
            # 3. The Chip
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
