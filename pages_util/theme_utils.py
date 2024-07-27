dracula_soft_dark = {
    "primaryColor": "#bd93f9",
    "backgroundColor": "#282a36",
    "secondaryBackgroundColor": "#44475a",
    "textColor": "#f8f8f2",
    "font": "sans serif",
}

tokyo_night = {
    "primaryColor": "#7aa2f7",
    "backgroundColor": "#1a1b26",
    "secondaryBackgroundColor": "#24283b",
    "textColor": "#a9b1d6",
    "font": "sans serif",
}

github_dark = {
    "primaryColor": "#58a6ff",
    "backgroundColor": "#0d1117",
    "secondaryBackgroundColor": "#161b22",
    "textColor": "#c9d1d9",
    "font": "sans serif",
}

github_light = {
    "primaryColor": "#0969da",
    "backgroundColor": "#ffffff",
    "secondaryBackgroundColor": "#f6f8fa",
    "textColor": "#24292f",
    "font": "sans serif",
}

solarized_light = {
    "primaryColor": "#268bd2",
    "backgroundColor": "#fdf6e3",
    "secondaryBackgroundColor": "#eee8d5",
    "textColor": "#657b83",
    "font": "sans serif",
}

nord_light = {
    "primaryColor": "#5e81ac",
    "backgroundColor": "#eceff4",
    "secondaryBackgroundColor": "#e5e9f0",
    "textColor": "#2e3440",
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


def get_theme_css(theme):
    return f"""
    <style>
    .stApp {{
        background-color: {theme['backgroundColor']};
        color: {theme['textColor']};
    }}
    .stSidebar {{
        background-color: {theme['secondaryBackgroundColor']};
    }}
    .stSidebar .stButton > button {{
        background-color: {theme['primaryColor']};
        color: {theme['backgroundColor']};
    }}
    .stSidebar .stButton > button:hover {{
        background-color: {theme['textColor']};
        color: {theme['backgroundColor']};
    }}
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {{
        background-color: {theme['secondaryBackgroundColor']};
        color: {theme['textColor']};
        border: 1px solid {theme['primaryColor']};
    }}
    header {{display: none !important}}
    </style>
    """


def get_preview_html(theme):
    return f"""
    <div style="background-color: {theme['backgroundColor']}; color: {theme['textColor']}; padding: 10px; border-radius: 5px;">
        <h3>Preview</h3>
        <p>This is how your theme will look.</p>
        <button style="background-color: {theme['primaryColor']}; color: {theme['backgroundColor']}; border: none; padding: 5px 10px; border-radius: 3px;">Button</button>
        <input type="text" placeholder="Input field" style="background-color: {theme['secondaryBackgroundColor']}; color: {theme['textColor']}; border: 1px solid {theme['primaryColor']}; padding: 5px; margin-top: 5px; width: 100%;">
    </div>
    """
