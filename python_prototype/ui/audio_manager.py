import os
import json
import random
import pygame


def _load_sfx(sfx_dir, filename, default_volume):
    """Helper to safely load a single sound effect."""
    path = os.path.join(sfx_dir, filename)
    if os.path.exists(path):
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(default_volume)
            return sound
        except:
            pass
    return None


class AudioManager:
    """Manages all game audio: SFX loading, music playback, volume persistence."""
    
    # Default volumes for each SFX (used when applying volume factor)
    SFX_BASE_VOLUMES = {
        'shuffle': 0.6, 'chips': 0.7, 'deal': 0.6, 'draw': 0.6,
        'sapaw': 0.7, 'fight': 0.8, 'win': 0.8, 'lose': 0.7,
        'burned': 0.8, 'tick': 0.6, 'turn_end': 0.6, 'all_in': 0.8, 'click': 0.6,
    }
    
    def __init__(self, assets_dir):
        music_dir = os.path.join(assets_dir, "music")
        sfx_dir = os.path.join(assets_dir, "sfx")
        
        # --- Music Tracks ---
        self.MUSIC_LOBBY = os.path.join(music_dir, "Casino.mp3")
        self.INGAME_TRACKS = [
            os.path.join(music_dir, "Moavii - Downtown (ingame).mp3"),
            os.path.join(music_dir, "Avanti - Chance Of Sunshine (ingame).mp3"),
        ]
        self.INGAME_TRACKS = [t for t in self.INGAME_TRACKS if os.path.exists(t)]
        self.MUSIC_INGAME = self.INGAME_TRACKS[0] if self.INGAME_TRACKS else os.path.join(music_dir, "Moavii - Downtown (ingame).mp3")
        
        # Lobby music as Sound object (for pause/resume across scenes)
        self.sound_lobby = None
        if os.path.exists(self.MUSIC_LOBBY):
            try:
                self.sound_lobby = pygame.mixer.Sound(self.MUSIC_LOBBY)
                self.sound_lobby.set_volume(0.3)
            except: pass
        
        # --- Sound Effects ---
        self.sfx_shuffle = _load_sfx(sfx_dir, "shuffling-card.mp3", 0.6)
        self.sfx_chips   = _load_sfx(sfx_dir, "chips_betting.mp3", 0.7)
        self.sfx_deal    = _load_sfx(sfx_dir, "card_distribution.mp3", 0.6)
        self.sfx_draw    = _load_sfx(sfx_dir, "getting_card.wav", 0.6)
        self.sfx_sapaw   = _load_sfx(sfx_dir, "sapaw.wav", 0.7)
        self.sfx_fight   = _load_sfx(sfx_dir, "fight_iniate.wav", 0.8)
        self.sfx_win     = _load_sfx(sfx_dir, "player_win.wav", 0.8)
        self.sfx_lose    = _load_sfx(sfx_dir, "player_lose.wav", 0.7)
        self.sfx_burned  = _load_sfx(sfx_dir, "player_burned.wav", 0.8)
        self.sfx_tick    = _load_sfx(sfx_dir, "time_ticking.mp3", 0.6)
        self.sfx_turn_end = _load_sfx(sfx_dir, "time_ends.wav", 0.6)
        self.sfx_all_in  = _load_sfx(sfx_dir, "all_betsIN.wav", 0.8)
        self.sfx_click   = _load_sfx(sfx_dir, "button_selection.wav", 0.6)
        
        # --- Music Playback State ---
        self.current_music = None
        self.lobby_music_started = False
        self.lobby_music_paused = False
        
        # --- Music End Event ---
        self.MUSIC_END_EVENT = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.MUSIC_END_EVENT)
        
        # --- Audio Settings Persistence ---
        self.SETTINGS_FILE = os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db")),
            "settings.json"
        )
        self.bgm_volume = 1.0
        self.sfx_volume = 1.0
        self._load_audio_settings()
    
    def _load_audio_settings(self):
        """Load saved volume settings from disk."""
        try:
            os.makedirs(os.path.dirname(self.SETTINGS_FILE), exist_ok=True)
            if os.path.exists(self.SETTINGS_FILE):
                with open(self.SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    self.bgm_volume = data.get("bgm_volume", 1.0)
                    self.sfx_volume = data.get("sfx_volume", 1.0)
        except: pass
    
    def _save_audio_settings(self):
        """Persist current volume settings to disk."""
        try:
            os.makedirs(os.path.dirname(self.SETTINGS_FILE), exist_ok=True)
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump({"bgm_volume": self.bgm_volume, "sfx_volume": self.sfx_volume}, f)
        except: pass
    
    def set_sfx_volume(self, volume_factor):
        """Apply volume factor to all SFX and persist."""
        self.sfx_volume = volume_factor
        sfx_map = {
            'shuffle': self.sfx_shuffle, 'chips': self.sfx_chips, 'deal': self.sfx_deal,
            'draw': self.sfx_draw, 'sapaw': self.sfx_sapaw, 'fight': self.sfx_fight,
            'win': self.sfx_win, 'lose': self.sfx_lose, 'burned': self.sfx_burned,
            'tick': self.sfx_tick, 'turn_end': self.sfx_turn_end, 'all_in': self.sfx_all_in,
            'click': self.sfx_click,
        }
        for key, sfx in sfx_map.items():
            if sfx:
                sfx.set_volume(self.SFX_BASE_VOLUMES[key] * volume_factor)
        self._save_audio_settings()
    
    def set_bgm_volume(self, volume_factor):
        """Apply volume factor to BGM and persist."""
        self.bgm_volume = volume_factor
        pygame.mixer.music.set_volume(0.3 * volume_factor)
        pygame.mixer.Channel(7).set_volume(0.3 * volume_factor)
        self._save_audio_settings()
    
    def play_music(self, track_path):
        """Play a music track. Pass 'NEXT' to rotate ingame tracks."""
        if track_path == "NEXT":
            pool = [t for t in self.INGAME_TRACKS if t != self.current_music]
            if not pool: pool = self.INGAME_TRACKS
            if not pool: return
            track_path = random.choice(pool)
            self.MUSIC_INGAME = track_path
        elif track_path != self.MUSIC_LOBBY and self.INGAME_TRACKS:
            track_path = random.choice(self.INGAME_TRACKS)
            self.MUSIC_INGAME = track_path
            
        if not os.path.exists(track_path):
            return
            
        if self.current_music == track_path and pygame.mixer.music.get_busy():
            return
        self.current_music = track_path
        try:
            if track_path == self.MUSIC_LOBBY:
                pygame.mixer.music.stop()
                if self.sound_lobby:
                    if not self.lobby_music_started:
                        pygame.mixer.Channel(7).play(self.sound_lobby, loops=-1)
                        self.lobby_music_started = True
                        self.lobby_music_paused = False
                    elif self.lobby_music_paused:
                        pygame.mixer.Channel(7).unpause()
                        self.lobby_music_paused = False
                    
            else:  # Ingame music
                if self.sound_lobby and self.lobby_music_started and not self.lobby_music_paused:
                    pygame.mixer.Channel(7).pause()
                    self.lobby_music_paused = True
                pygame.mixer.music.load(track_path)
                pygame.mixer.music.set_volume(0.3 * self.bgm_volume)
                pygame.mixer.music.play(1)
        except Exception as e:
            print(f"Music error: {e}")
