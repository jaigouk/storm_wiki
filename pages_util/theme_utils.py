# Define default themes
light_theme = {
    "primaryColor": "#FF4B4B",
    "backgroundColor": "#FFFFFF",
    "secondaryBackgroundColor": "#F0F2F6",
    "textColor": "#31333F",
    "font": "sans serif",
}

dark_theme = {
    "primaryColor": "#FF4B4B",
    "backgroundColor": "#0E1117",
    "secondaryBackgroundColor": "#262730",
    "textColor": "#FAFAFA",
    "font": "sans serif",
}

dracula_soft_dark = {
    "primaryColor": "#bd93f9",
    "backgroundColor": "#282a36",
    "secondaryBackgroundColor": "#44475a",
    "textColor": "#f8f8f2",
    "sidebarBackgroundColor": "#1e1f29",
    "font": "sans serif",
}

tokyo_night = {
    "primaryColor": "#7aa2f7",
    "backgroundColor": "#1a1b26",
    "secondaryBackgroundColor": "#24283b",
    "textColor": "#a9b1d6",
    "sidebarBackgroundColor": "#16161e",
    "font": "sans serif",
}

github_dark = {
    "primaryColor": "#58a6ff",
    "backgroundColor": "#0d1117",
    "secondaryBackgroundColor": "#161b22",
    "textColor": "#c9d1d9",
    "sidebarBackgroundColor": "#090c10",
    "font": "sans serif",
}

github_light = {
    "primaryColor": "#0969da",
    "backgroundColor": "#ffffff",
    "secondaryBackgroundColor": "#f6f8fa",
    "textColor": "#24292f",
    "sidebarBackgroundColor": "#f6f8fa",
    "font": "sans serif",
}

solarized_light = {
    "primaryColor": "#268bd2",
    "backgroundColor": "#fdf6e3",
    "secondaryBackgroundColor": "#eee8d5",
    "textColor": "#657b83",
    "sidebarBackgroundColor": "#eee8d5",
    "font": "sans serif",
}

nord_light = {
    "primaryColor": "#5e81ac",
    "backgroundColor": "#eceff4",
    "secondaryBackgroundColor": "#e5e9f0",
    "textColor": "#2e3440",
    "sidebarBackgroundColor": "#d8dee9",
    "font": "sans serif",
}

dark_themes = {
    "Dracula Soft Dark": dracula_soft_dark,
    "Tokyo Night": tokyo_night,
    "GitHub Dark": github_dark,
}

light_themes = {
    "GitHub Light": github_light,
    "Solarized Light": solarized_light,
    "Nord Light": nord_light,
}


def get_style():
    return get_theme_css(dracula_soft_dark)


def adjust_color_brightness(hex_color, amount):
    rgb = tuple(int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    new_rgb = [max(0, min(255, x + amount)) for x in rgb]
    return f"#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}"


def get_contrasting_text_color(hex_color):
    # Convert hex to RGB
    rgb = tuple(int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))

    # Calculate luminance
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255

    # Return black for light backgrounds, white for dark
    return "#000000" if luminance > 0.5 else "#ffffff"


def get_theme_css(theme):
    return f"""
    <style>
    :root {{
        --primary-color: {theme['primaryColor']};
        --background-color: {theme['backgroundColor']};
        --secondary-background-color: {theme['secondaryBackgroundColor']};
        --text-color: {theme['textColor']};
        --font: {theme['font']};
    }}
    body {{
        color: {theme['textColor']};
    }}
    h1, h2, h3, h4, h5, h6, p, li, a {{
        color: {theme['textColor']} !important;
    }}
    .stTextInput > div > div > input {{
        color: {theme['textColor']};
    }}
    .stSelectbox > div > div > select {{
        color: {theme['textColor']};
    }}
    .stMarkdown {{
        color: {theme['textColor']};
    }}
    </style>
    """


def get_preview_html(theme):
    return f"""
    <div style="display: flex; gap: 10px;">
        <div style="background-color: {theme['secondaryBackgroundColor']}; color: {theme['textColor']}; padding: 10px; border-radius: 5px; width: 150px;">
            <h4 style="margin: 0;">Sidebar</h4>
            <p>📊 General</p>
            <p style="color: {theme['primaryColor']};">🎨 Theme</p>
            <p>⚙️ Advanced</p>
        </div>
        <div style="background-color: {theme['backgroundColor']}; color: {theme['textColor']}; padding: 10px; border-radius: 5px; flex-grow: 1;">
            <h3>Preview</h3>
            <p>This is how your theme will look.</p>
            <button style="background-color: {theme['primaryColor']}; color: #FFFFFF; border: none; padding: 5px 10px; border-radius: 3px;">Button</button>
            <input type="text" placeholder="Input field" style="background-color: {theme['secondaryBackgroundColor']}; color: {theme['textColor']}; border: 1px solid {theme['primaryColor']}; padding: 5px; margin-top: 5px; width: 100%;">
        </div>
    </div>
    """
