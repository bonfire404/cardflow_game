import flet as ft
from .components import game_card, profile_footer, help_button

def LobbyView(page, player_name, coins, wins, losses, on_start_game):
    
    # 1. Header with Coin Frame, Title, and Help Button
    header = ft.Container(
        content=ft.Row([
            # Left: Coin Frame 
            ft.Stack([
                ft.Image(src="../assets/images/lobby/currency_frame.png", height=50),
                ft.Container(
                    content=ft.Text(f"{coins:,}", size=18, weight="bold", color="#ffd700"),
                    padding=ft.padding.only(left=60, top=13)
                )
            ], width=250, height=50),
            
            # Center: Title
            ft.Container(
                content=ft.Stack([
                    ft.Text("MAMA'S GO", size=28, weight="bold", color="#1a0a00"), # Shadow
                    ft.Container(content=ft.Text("MAMA'S GO", size=28, weight="bold", color="#ffd732"), padding=ft.padding.only(left=2, top=2)),
                ]),
                expand=True,
                alignment=ft.alignment.center if hasattr(ft.alignment, "center") else ft.Alignment(0, 0)
            ),
            
            # Right: Help Button
            ft.Container(content=help_button(), alignment=ft.alignment.center_right if hasattr(ft.alignment, "center_right") else ft.Alignment(1, 0), width=250)
        ]),
        padding=ft.padding.symmetric(horizontal=20, vertical=15),
        bgcolor="#99000000",
        border=ft.border.only(bottom=ft.border.BorderSide(2, "gold"))
    )

    # 2. Main Center Cards
    cards_row = ft.Row([
        game_card("PLAY NOW", "CASINO CLASSIC", "../assets/images/lobby/play_now.png", "gold", on_click=on_start_game, has_bets=True),
        game_card("AI ARENA", "BOT TRAINING", "../assets/images/lobby/ai_arena.png", "#b464ff", on_click=None),
        game_card("FRIENDS", "SOCIAL LOUNGE", "../assets/images/lobby/friends.png", "#00b4ff", on_click=None, active=False),
        game_card("ARENA", "RANKED GLORY", "../assets/images/lobby/arena_ranked.png", "#ff3c3c", on_click=None, active=False),
    ], alignment=ft.MainAxisAlignment.CENTER if hasattr(ft.MainAxisAlignment, "CENTER") else "center", spacing=40)

    # 3. Assemble Full Screen with Background
    bg_stack = ft.Stack([
        # Oversized container to ensure it covers even ultrawide screens
        ft.Container(content=ft.Image(src="../assets/images/casino_lobby_bg.png", fit="cover", width=4000, height=3000), left=-1000, top=-1000, right=-1000, bottom=-1000),
        ft.Container(
            bgcolor="#cc080500", # Cinematic dark tint over the image
            expand=True,
            content=ft.Column([
                header,
                ft.Container(expand=True), # Push cards to center
                cards_row,
                ft.Container(expand=True), # Push footer to bottom
                profile_footer(player_name, wins, losses),
            ], spacing=0)
        )
    ], expand=True)

    return bg_stack
