import flet as ft
import sys
import os


sys.path.append(os.path.join(os.path.dirname(__file__), "..", "python_prototype"))

from ui.database import load_user_profile
from game.engine import TongItsEngine
from flet_ui.lobby import LobbyView
from flet_ui.game_view import GameView

def main(page: ft.Page):
    page.title = "Mama's Go - Cross Platform"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1280
    page.window_height = 720
    page.padding = 0
    page.spacing = 0

    # Load real data
    profile_data = load_user_profile()
    player_name = profile_data.get("name", "Player")
    coins = profile_data.get("coins", 0)
    wins = profile_data.get("wins", 0)
    losses = profile_data.get("losses", 0)

    engine = None

    def handle_start_game(e):
        nonlocal engine
        engine = TongItsEngine([player_name, "Bot 1", "Bot 2"], dealer_idx=0)
        engine.initialize_game()
        page.clean()
        page.add(GameView(engine, on_surrender=lambda _: show_lobby()))
        page.update()

    def show_lobby():
        page.clean()
        page.add(LobbyView(
            page, 
            player_name, 
            coins, 
            wins, 
            losses, 
            on_start_game=handle_start_game
        ))
        page.update()

    show_lobby()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="../assets")
