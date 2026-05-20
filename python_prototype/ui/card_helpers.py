import pygame
from PIL import Image, ImageSequence
from ui.ui_components import Colors


def get_card_filename(card):
    suit = card.suit.lower()
    rank = card.rank
    rank_map = {
        'Ace': 'ace', 
        'Jack': 'jack', 
        'Queen': 'queen', 
        'King': 'king'
    }
    rank_str = rank_map.get(rank, rank)
    if rank_str.isdigit() and len(rank_str) == 1:
        rank_str = f"0{rank_str}"
    elif rank_str == '10':
        rank_str = '10'
    return f"{suit}_{rank_str}.png"


def draw_hand_ribbon(surface, rects, text="", is_front=True):
    """Draws a premium ribbon wrap around a set of card rects."""
    if not rects: return
    
    # Calculate bounding box
    min_x = min(r.x for r in rects)
    max_x = max(r.x + r.w for r in rects)
    min_y = min(r.y for r in rects)
    max_y = max(r.y + r.h for r in rects)
    
    rw = (max_x - min_x)
    rh = 30
    rx = min_x
    screen_h = surface.get_height()
    ry = (screen_h - 170) + 85 - rh // 2
    
    ribbon_color = Colors.RIBBON_RED
    shadow_color = Colors.RIBBON_SHADOW
    gold_trim = Colors.RIBBON_GOLD
    
    if not is_front:
      
        back_surf = pygame.Surface((rw + 12, rh + 4), pygame.SRCALPHA)
        pygame.draw.rect(back_surf, shadow_color, (0, 2, rw + 12, rh), border_radius=4)
       
        pygame.draw.polygon(back_surf, shadow_color, [(0, 0), (15, rh//2), (0, rh)])
        pygame.draw.polygon(back_surf, shadow_color, [(rw+12, 0), (rw+12-15, rh//2), (rw+12, rh)])
        surface.blit(back_surf, (rx - 6, ry - 2))
    else:
        
        front_surf = pygame.Surface((rw, rh), pygame.SRCALPHA)
        
        pygame.draw.rect(front_surf, ribbon_color, (0, 0, rw, rh), border_radius=2)
        pygame.draw.rect(front_surf, (255, 255, 255, 40), (0, 0, rw, 2))
        pygame.draw.rect(front_surf, (0, 0, 0, 40), (0, rh-2, rw, 2))      
        
        pygame.draw.line(front_surf, gold_trim, (0, 4), (rw, 4), 1)
        pygame.draw.line(front_surf, gold_trim, (0, rh-5), (rw, rh-5), 1)
        
        # Shine effect
        shine = pygame.Surface((rw, rh), pygame.SRCALPHA)
        pygame.draw.rect(shine, (255, 255, 255, 30), (rw//4, 0, rw//2, rh))
        front_surf.blit(shine, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

        surface.blit(front_surf, (rx, ry))
        
        # Label
        if text:
            try:
                f = pygame.font.SysFont("Arial", 14, bold=True)
            except:
                f = pygame.font.Font(None, 14)
            
            txt_surf = f.render(text.upper(), True, gold_trim)
            surface.blit(txt_surf, (rx + rw//2 - txt_surf.get_width()//2, ry + rh//2 - txt_surf.get_height()//2))


def load_gif(filename):
    pil_image = Image.open(filename)
    frames = []
    for frame in ImageSequence.Iterator(pil_image):
        frame = frame.convert("RGBA")
        pygame_image = pygame.image.fromstring(
            frame.tobytes(), frame.size, frame.mode
        ).convert_alpha()
        frames.append(pygame_image)
    return frames
