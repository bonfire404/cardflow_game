import flet as ft

def game_card(title, subtitle, icon_path, color, on_click, active=True, has_bets=False):
    # Card inner content
    items = [
        ft.Container(height=10),
        ft.Image(src=icon_path, width=140, height=140, opacity=1 if active else 0.4),
        ft.Container(height=10),
        ft.Divider(color="white30", height=1, thickness=1),
        ft.Container(height=15),
    ]
    
    if has_bets:
        items.append(
            ft.Row([
                ft.Container(content=ft.Text("100", size=12, weight="bold", color="black"), bgcolor="amber", padding=ft.padding.symmetric(horizontal=12, vertical=6), border_radius=12),
                ft.Container(content=ft.Text("300", size=12, weight="bold", color="white70"), bgcolor="white10", padding=ft.padding.symmetric(horizontal=12, vertical=6), border_radius=12),
                ft.Container(content=ft.Text("600", size=12, weight="bold", color="white70"), bgcolor="white10", padding=ft.padding.symmetric(horizontal=12, vertical=6), border_radius=12),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8)
        )
        items.append(ft.Container(height=15))
    else:
        items.append(ft.Container(height=10))

    items.extend([
        ft.Text(title, size=22, weight="bold", color="white" if active else "white54"),
        ft.Text(subtitle, size=12, color="white70" if active else "white30"),
    ])

    if not active:
        items.append(
            ft.Container(
                content=ft.Text("COMING SOON", size=10, weight="bold", color="white54"),
                bgcolor="black45",
                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                border_radius=12,
                margin=ft.margin.only(top=10)
            )
        )

    card_content = ft.Column(
        controls=items,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0
    )
    
    border_color = color if active else "white24"
    bg_color = "#15" + color.lstrip("#") if active and color.startswith("#") else "#15ffd700" if color == "gold" else "#0dffffff"
    
    card = ft.Container(
        content=card_content,
        width=260, height=380,
        padding=10,
        bgcolor=bg_color,
        blur=ft.Blur(15, 15, ft.BlurTileMode.MIRROR) if hasattr(ft, "Blur") else 15,
        border_radius=32,
        border=ft.border.all(2, border_color),
        on_click=on_click if active else None,
        ink=True if active else False,
    )
    
    def on_hover(e):
        e.control.scale = 1.05 if e.data == "true" else 1.0
        e.control.border = ft.border.all(3 if e.data == "true" else 2, "#ffe664" if e.data == "true" and active else border_color)
        hover_bg = "#26" + color.lstrip("#") if active and color.startswith("#") else "#26ffd700" if color == "gold" else bg_color
        e.control.bgcolor = hover_bg if e.data == "true" and active else bg_color
        e.control.update()
        
    if active:
        card.on_hover = on_hover
        card.scale = 1.0
        card.animate_scale = ft.Animation(200, ft.AnimationCurve.EASE_OUT) if hasattr(ft, "AnimationCurve") else ft.Animation(200, "easeOut")

    return card

def profile_footer(player_name, wins, losses):
    return ft.Container(
        content=ft.Row([
            ft.Stack([
                ft.CircleAvatar(radius=30, bgcolor="transparent", content=ft.Icon("person", size=40, color="white54")),
                ft.Container(width=60, height=60, border=ft.border.all(3, "gold"), border_radius=30)
            ]), # Avatar container fallback
            ft.Column([
                ft.Text(player_name.upper(), size=20, weight="bold", color="white"),
                ft.Row([
                    ft.Text(f"W {wins}", color="greenaccent", size=14, weight="bold"),
                    ft.Text("|", color="white30"),
                    ft.Text(f"L {losses}", color="redaccent", size=14, weight="bold"),
                ], spacing=5)
            ], spacing=0, alignment=ft.MainAxisAlignment.CENTER)
        ], alignment=ft.MainAxisAlignment.START, spacing=15),
        padding=ft.padding.only(left=30, bottom=20, top=20),
        bgcolor="#d0000000",
        border=ft.border.only(top=ft.border.BorderSide(1, "white24")),
    )

def help_button():
    return ft.Container(
        content=ft.Text("?", size=22, weight="bold", color="gold"),
        width=46, height=46,
        alignment=ft.alignment.center if hasattr(ft.alignment, "center") else ft.Alignment(0, 0),
        shape=ft.BoxShape.CIRCLE if hasattr(ft.BoxShape, "CIRCLE") else "circle",
        border=ft.border.all(2, "gold"),
        bgcolor="#22000000"
    )
