import flet as ft

def get_card_image_src(card):
    if not card:
        return "Casino/Cards/back01.png"
    suit = card.suit.lower()
    rank = str(card.rank).lower()
    if rank.isdigit():
        rank = f"{int(rank):02d}" # "02" to "10"
    return f"Casino/Cards/{suit}_{rank}.png"

def GameView(engine, on_surrender):
    player = engine.players[0]
    bot1 = engine.players[1]
    bot2 = engine.players[2]
    
    # Helper to generate a spread of facedown cards
    def bot_hand_view(bot, name, align="left"):
        badge = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(radius=20, content=ft.Icon("person", size=24, color="white54")) if align == "left" else ft.Container(),
                ft.Column([
                    ft.Text(name, color="white", weight="bold", size=14),
                    ft.Text(f"{len(bot.hand)} CARDS", color="white54", size=10),
                ], spacing=1),
                ft.CircleAvatar(radius=20, content=ft.Icon("person", size=24, color="white54")) if align == "right" else ft.Container(),
            ], spacing=10),
            bgcolor="#151720", padding=8, border_radius=16, border=ft.border.all(1, "white10")
        )
        
        cards = ft.Row([
            ft.Image(src="Casino/Cards/back01.png", width=60, height=90)
            for _ in range(len(bot.hand))
        ], spacing=-40)  # Overlapping effect

        return ft.Column([badge, cards] if align == "left" else [badge, cards], spacing=10)

    return ft.Stack([
        # Table Background
        ft.Container(content=ft.Image(src="images/clean_card_table.png", fit="fill"), left=0, right=0, top=0, bottom=0),
        
        # UI Elements
        ft.Column([
            # Top Bar & Bots
            ft.Stack([
                ft.Container(
                    content=bot_hand_view(bot1, bot1.name, align="left"),
                    top=20, left=40
                ),
                ft.Container(
                    content=bot_hand_view(bot2, bot2.name, align="right"),
                    top=20, right=40
                )
            ], height=200),
            
            ft.Container(expand=True),
            
            # Center: Deck and Discard Pile
            ft.Row([
                # Deck
                ft.Stack([
                    ft.Image(src="Casino/Cards/back01.png", width=80, height=120)
                    for i in range(min(5, len(engine.deck.cards))) # Fake stack thickness
                ]),
                ft.Container(width=40),
                # Discard Pile
                ft.Image(
                    src=get_card_image_src(engine.discard_pile[-1]) if engine.discard_pile else "Casino/Cards/back01.png",
                    width=80, height=120,
                    opacity=1.0 if engine.discard_pile else 0.0
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
            
            ft.Container(expand=True),
            
            # Bottom: Player Hand
            ft.Stack([
                # Player Status Badge
                ft.Container(
                    content=ft.Column([
                        ft.CircleAvatar(radius=16, content=ft.Icon("person", size=20, color="white54")),
                        ft.Text(player.name, color="white", weight="bold"),
                        ft.Text(f"{len(player.hand)} CARDS  {player.calculate_points()} PTS", color="yellow600", size=10, weight="bold")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    bgcolor="#20222a",
                    border_radius=12,
                    padding=10,
                    bottom=10,
                    left=0,
                    right=0,
                    alignment=ft.alignment.center if hasattr(ft.alignment, "center") else ft.Alignment(0,0)
                ),
                
                # Cards
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Image(src=get_card_image_src(c), width=100, height=145),
                            border_radius=8,
                            margin=ft.margin.only(top=0), # Can animate hover here later
                            shadow=ft.BoxShadow(blur_radius=10, color="black38", offset=ft.Offset(2, 5)) if hasattr(ft, "BoxShadow") else ft.Shadow(color="black", blur_radius=10) if hasattr(ft, "Shadow") else None,
                        ) for c in player.hand
                    ], alignment=ft.MainAxisAlignment.CENTER if hasattr(ft.MainAxisAlignment, "CENTER") else "center", spacing=-50),
                    bottom=80,
                    left=0,
                    right=0
                ),
                
                # Right action buttons
                ft.Container(
                    content=ft.Row([
                        ft.ElevatedButton("Group", style=ft.ButtonStyle(bgcolor="#2c2d3a", color="white", shape=ft.RoundedRectangleBorder(radius=8) if hasattr(ft, "RoundedRectangleBorder") else None)),
                        ft.ElevatedButton("Auto Sort", style=ft.ButtonStyle(bgcolor="#3e4362", color="white", shape=ft.RoundedRectangleBorder(radius=8) if hasattr(ft, "RoundedRectangleBorder") else None)),
                    ], spacing=10),
                    bottom=40,
                    right=20
                ),
                
                # SURRENDER Button (Bottom Left)
                ft.Container(
                    content=ft.ElevatedButton("SURRENDER", on_click=on_surrender, style=ft.ButtonStyle(bgcolor="red700", color="white")),
                    bottom=40,
                    left=20
                )
            ], expand=True)
        ], expand=True)
    ], expand=True)
