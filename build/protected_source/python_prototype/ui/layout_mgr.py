import pygame
from ui import assets_mgr

def calc_layout(width, height):
    return {
        'width': width, 'height': height,
        'hand_y': height - 170, 'hand_center_x': width // 2,
        'deck_x': width//2-140, 'deck_y': height//2-75,
        'discard_x': width//2+60, 'discard_y': height//2-75,
        'bot1_x': 200, 'bot1_y': 90,
        'bot2_x': width-200, 'bot2_y': 90,
        'player_meld_y': height-315,
        'bot1_meld_x': 40, 'bot1_meld_y': 190,
        'bot2_meld_x': width-300, 'bot2_meld_y': 190,
        'btn_bar_y': height-55, 'btn_bar_x': width//2,
    }

def calc_meld_zones(player_melds, start_x, start_y, max_w=260):
    zones = []
    if not player_melds: return zones
    cs = 0.45  
    cw = int((assets_mgr.BASE_CARD_W or 60)*cs)
    ch = int((assets_mgr.BASE_CARD_H or 84)*cs)
    overlap_x = int(cw*0.35) 
    overlap_y = 6 
    mx, my = start_x, start_y
    for tm in player_melds:
        diag_h = (len(tm.cards)-1)*overlap_y
        meld_w = (len(tm.cards)-1)*overlap_x + cw
        if mx+meld_w > start_x+max_w and mx > start_x:
            mx = start_x; my += ch + 25
        zones.append((tm, pygame.Rect(mx, my, meld_w, ch + diag_h)))
        mx += meld_w + 14 
    return zones

def draw_player_melds(surface, player_melds, start_x, start_y, max_w=260):
    zones = calc_meld_zones(player_melds, start_x, start_y, max_w)
    cs = 0.45
    cw = int((assets_mgr.BASE_CARD_W or 60)*cs)
    ch = int((assets_mgr.BASE_CARD_H or 84)*cs)
    overlap_x = int(cw*0.35)
    overlap_y = 6
    for tm, rect in zones:
        for i, card in enumerate(tm.cards):
            img = assets_mgr.get_card_image(card)
            if img:
                scaled = pygame.transform.scale(img, (cw, ch))
                surface.blit(scaled, (rect.x + i*overlap_x, rect.y + i*overlap_y))
    return zones
