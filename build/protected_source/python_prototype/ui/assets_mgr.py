import os
import pygame
from ui.paths import get_resource_path

CARD_SCALE = 2
BASE_CARD_W = BASE_CARD_H = 0
card_image_cache = {}
card_back_raw = None
background_raw = None
background = None
avatar1 = None
avatar2 = None
rank_badges_cache = {}

def get_rank_badge(rank_name, size="mini"):
    """
    Returns the rank badge surface based on rank_name ('Wood', 'Iron', 'Bronze', 'Silver', 'Gold', 'Immortal')
    size: 'mini' (48x48) or 'large' (128x128)
    """
    key = (rank_name, size)
    if key not in rank_badges_cache:
        assets_dir = get_resource_path('assets')
        badge_path = os.path.join(assets_dir, "images", "rank", f"{rank_name.lower()}.png")
        
        target_size = (48, 48) if size == "mini" else (128, 128)
        try:
            raw = pygame.image.load(badge_path).convert_alpha()
            rank_badges_cache[key] = pygame.transform.scale(raw, target_size)
        except Exception:
            # Fallback to creating a colorful rank badge with text
            surf = pygame.Surface(target_size, pygame.SRCALPHA)
            color_map = {
                "Wood": (139, 69, 19), "Iron": (169, 169, 169),
                "Bronze": (205, 127, 50), "Silver": (192, 192, 192),
                "Gold": (255, 215, 0), "Immortal": (148, 0, 211)
            }
            bg_color = color_map.get(rank_name, (100, 100, 100))
            
            # Draw ribbon backdrop
            w, h = target_size
            ribbon_pts = [(w*0.1, h*0.2), (w*0.9, h*0.2), (w*0.9, h*0.9), (w*0.5, h*0.7), (w*0.1, h*0.9)]
            pygame.draw.polygon(surf, tuple(max(0, c-40) for c in bg_color), ribbon_pts)
            
            # Draw badge circle
            cx, cy = w//2, h//2 - int(h*0.1)
            r = int(w * 0.35)
            pygame.draw.circle(surf, bg_color, (cx, cy), r)
            pygame.draw.circle(surf, (255, 255, 255, 150), (cx, cy), r, 2)
            pygame.draw.circle(surf, (255, 255, 255, 60), (cx, cy), r-3, 1)
            
            # Draw rank initial letter
            try:
                font = pygame.font.SysFont("Arial", int(r*1.2), bold=True)
                txt = font.render(rank_name[0], True, (255, 255, 255))
                surf.blit(txt, (cx - txt.get_width()//2, cy - txt.get_height()//2))
            except:
                pass
                
            rank_badges_cache[key] = surf
            
    return rank_badges_cache[key]

def init_assets(width, height):
    global background_raw, background, card_back_raw, avatar1, avatar2
    assets_dir = get_resource_path('assets')
    bg_path = os.path.join(assets_dir, "images", "tables", "clean_card_table.png")
    try:
        background_raw = pygame.image.load(bg_path).convert()
        background = pygame.transform.scale(background_raw, (width, height))
    except Exception:
        background_raw = background = None

    card_back_path = os.path.join(assets_dir, "cards", "card-back1.png")
    try: card_back_raw = pygame.image.load(card_back_path).convert_alpha()
    except Exception: card_back_raw = None

    try:
        avatar1 = pygame.image.load(os.path.join(assets_dir, "images", "avatar1.png")).convert_alpha()
        avatar2 = pygame.image.load(os.path.join(assets_dir, "images", "avatar2.png")).convert_alpha()
    except Exception:
        avatar1 = avatar2 = None

def get_card_filename(card):
    suit = card.suit.lower()
    rank = card.rank
    rank_map = {'Ace': '1', 'Jack': '11', 'Queen': '12', 'King': '13'}
    rank_num = rank_map.get(rank, rank)
    return f"card-{suit}-{rank_num}.png"

def get_card_image(card, scale=CARD_SCALE):
    global BASE_CARD_W, BASE_CARD_H
    fname = get_card_filename(card)
    key = (fname, scale)
    if key not in card_image_cache:
        assets_dir = get_resource_path('assets')
        cards_dir = os.path.join(assets_dir, "cards")
        try:
            raw = pygame.image.load(os.path.join(cards_dir, fname)).convert_alpha()
            w, h = int(raw.get_width()*scale), int(raw.get_height()*scale)
            card_image_cache[key] = pygame.transform.scale(raw, (w, h))
            if BASE_CARD_W == 0: BASE_CARD_W, BASE_CARD_H = w, h
        except Exception: card_image_cache[key] = None
    return card_image_cache[key]

def get_card_back(scale=CARD_SCALE):
    if not card_back_raw: return None
    key = ('_back', scale)
    if key not in card_image_cache:
        w, h = int(card_back_raw.get_width()*scale), int(card_back_raw.get_height()*scale)
        card_image_cache[key] = pygame.transform.scale(card_back_raw, (w, h))
    return card_image_cache[key]

def load_font(name_query, size):
    assets_dir = get_resource_path('assets')
    fonts_dir = os.path.join(assets_dir, "fonts")
    for root, dirs, files in os.walk(fonts_dir):
        for fn in files:
            if name_query.lower() in fn.lower() and fn.endswith(('.ttf','.otf')):
                try: return pygame.font.Font(os.path.join(root, fn), size)
                except: pass
    return get_sys_font("Arial", size)

_sys_font_cache = {}
def get_sys_font(name, size, bold=False, italic=False):
    key = (name, size, bold, italic)
    if key not in _sys_font_cache:
        _sys_font_cache[key] = pygame.font.SysFont(name, size, bold=bold, italic=italic)
    return _sys_font_cache[key]

_rotated_cache = {}
def get_rotated_image(image, angle):
    angle = int(round(angle))
    if angle == 0: return image
    key = (id(image), angle)
    if key not in _rotated_cache:
        _rotated_cache[key] = pygame.transform.rotate(image, angle)
    return _rotated_cache[key]

def prewarm_cards():
    _d = __import__('game.models', fromlist=['Deck']).Deck()
    if _d.cards: get_card_image(_d.cards[0])
