import os
import random
import pygame
from ui.progression_manager import generate_bot_profile


# --- Gendered Identity Pools ---
MALE_NAMES = ["Juan", "Rico", "Dingdong", "Vhong", "Isko", "Vico", "Bong", "Ping", "Manny", "Kap", "Malupiton", "Ador"]
FEMALE_NAMES = ["Maria", "Liza", "Marian", "Anne", "Karylle", "Leni", "Korina", "Darna", "Diwata", "Inday", "Nena"]


def load_avatar_pools(avatars_dir):
    """Load and categorize avatar images by gender from the avatars directory."""
    av_pools = {'male': [], 'female': [], 'any': []}
    
    if os.path.exists(avatars_dir):
        for fn in os.listdir(avatars_dir):
            if fn.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                try:
                    img = pygame.image.load(os.path.join(avatars_dir, fn)).convert_alpha()
                    fn_lower = fn.lower()
                    if any(k in fn_lower for k in ['female', 'women', 'girl', 'lady', 'p_female']): 
                        av_pools['female'].append(img)
                    elif any(k in fn_lower for k in ['male', 'man', 'boy', 'guy', 'men', 'p_male']): 
                        av_pools['male'].append(img)
                    else: 
                        av_pools['any'].append(img)
                except: pass
    
    for g in ['male', 'female']:
        if not av_pools[g]: av_pools[g] = av_pools['any']
    
    return av_pools


def generate_npc(av_pools, exclude_names=None, exclude_avatars=None, bet_limit=300):
    """Generate a random NPC with unique name, avatar, and stats."""
    if exclude_names is None: exclude_names = []
    if exclude_avatars is None: exclude_avatars = []
    
    gender = random.choice(['male', 'female'])
    # Ensure name uniqueness
    pool_names = MALE_NAMES if gender == 'male' else FEMALE_NAMES
    available_names = [n for n in pool_names if n not in exclude_names]
    if not available_names: available_names = pool_names
    name = random.choice(available_names)

    # Ensure avatar uniqueness
    p_avs = av_pools[gender] if av_pools[gender] else av_pools['any']
    available_avatars = [a for a in p_avs if a not in exclude_avatars]
    if not available_avatars: available_avatars = p_avs  # Fallback
    avatar = random.choice(available_avatars) if available_avatars else None
    
    # Generate bot stats based on room bet limit
    bot_stats = generate_bot_profile(bet_limit)
    
    return name, avatar, bot_stats
