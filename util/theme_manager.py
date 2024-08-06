import streamlit as st
import sqlite3
import json

dracula_soft_dark = {
    "primaryColor": "#bf96f9",
    "backgroundColor": "#282a36",
    "secondaryBackgroundColor": "#44475a",
    "textColor": "#C0C0D0",
    "sidebarBackgroundColor": "#44475a",
    "sidebarTextColor": "#C0C0D0",
    "font": "sans serif",
}

tokyo_night = {
    "primaryColor": "#7aa2f7",
    "backgroundColor": "#1a1b26",
    "secondaryBackgroundColor": "#24283b",
    "textColor": "#a9b1d6",
    "sidebarBackgroundColor": "#24283b",
    "sidebarTextColor": "#565f89",
    "font": "sans serif",
}

github_dark = {
    "primaryColor": "#58a6ff",
    "backgroundColor": "#0d1117",
    "secondaryBackgroundColor": "#161b22",
    "textColor": "#c9d1d9",
    "sidebarBackgroundColor": "#161b22",
    "sidebarTextColor": "#8b949e",
    "font": "sans serif",
}

github_light = {
    "primaryColor": "#0969da",
    "backgroundColor": "#ffffff",
    "secondaryBackgroundColor": "#f6f8fa",
    "textColor": "#24292f",
    "sidebarBackgroundColor": "#f6f8fa",
    "sidebarTextColor": "#57606a",
    "font": "sans serif",
}

solarized_light = {
    "primaryColor": "#268bd2",
    "backgroundColor": "#fdf6e3",
    "secondaryBackgroundColor": "#eee8d5",
    "textColor": "#657b83",
    "sidebarBackgroundColor": "#eee8d5",
    "sidebarTextColor": "#657b83",
    "font": "sans serif",
}

nord_light = {
    "primaryColor": "#5e81ac",
    "backgroundColor": "#eceff4",
    "secondaryBackgroundColor": "#e5e9f0",
    "textColor": "#2e3440",
    "sidebarBackgroundColor": "#e5e9f0",
    "sidebarTextColor": "#4c566a",
    "font": "sans serif",
}

dark_themes = {
    "Dracula Soft Dark": dracula_soft_dark,
    "Tokyo Night": tokyo_night,
    "GitHub Dark": github_dark,
}

light_themes = {
    "Solarized Light": solarized_light,
    "Nord Light": nord_light,
    "GitHub Light": github_light,
}


def init_db():
    conn = sqlite3.connect("settings.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)""")
    conn.commit()
    conn.close()


def save_theme(theme):
    conn = sqlite3.connect("settings.db")
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ("theme", json.dumps(theme)),
    )
    conn.commit()
    conn.close()


def load_theme_from_db():
    conn = sqlite3.connect("settings.db")
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='theme'")
    result = c.fetchone()
    conn.close()

    if result:
        stored_theme = json.loads(result[0])
        # Use the stored theme as is, without merging with default
        return stored_theme

    # If no theme is stored, use the default Dracula Soft Dark theme
    return dracula_soft_dark.copy()


def adjust_color_brightness(hex_color, brightness_factor):
    # Convert hex to RGB
    rgb = tuple(int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    # Adjust brightness
    new_rgb = tuple(
        min(255, max(0, int(c * (1 + brightness_factor / 100)))) for c in rgb
    )
    # Convert back to hex
    return "#{:02x}{:02x}{:02x}".format(*new_rgb)


def get_contrasting_text_color(hex_color):
    # Convert hex to RGB
    rgb = tuple(int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    # Calculate luminance
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    # Return black for light backgrounds, white for dark
    return "#000000" if luminance > 0.5 else "#ffffff"


def get_option_menu_style(theme):
    return {
        "container": {
            "padding": "0.5rem",
            "background-color": theme["sidebarBackgroundColor"],
            "border-radius": "0px",
        },
        "icon": {"color": theme["sidebarTextColor"], "font-size": "16px"},
        "nav-link": {
            "color": adjust_color_brightness(theme["sidebarTextColor"], 50),
            "font-size": "16px",
            "text-align": "left",
            "margin": "0px",
            "--hover-color": theme["primaryColor"],
            "background-color": "transparent",
        },
        "nav-link-selected": {
            "background-color": theme["primaryColor"],
            "color": get_contrasting_text_color(theme["primaryColor"]),
        },
    }


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

    /* Base styles */
    .stApp {{
        background-color: var(--background-color);
        color: var(--text-color);
        font-family: var(--font);
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: var(--secondary-background-color);
        color: var(--text-color);
    }}

    /* Text and headers */
    .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, li {{
        color: var(--text-color) !important;
    }}

    /* Buttons */
    .stButton > button {{
        font-size: 14px;
        padding: 2px 10px;
        height: auto;
        width: auto;
        background-color: var(--primary-color) !important;
        color: var(--background-color) !important;
        border-color: var(--primary-color) !important;
        border-radius: 4px;
        transition: all 0.3s ease;
    }}
    .stButton > button:hover {{
        background-color: {adjust_color_brightness(theme['primaryColor'], -20)} !important;
        color: var(--background-color) !important;
    }}
    .stButton > button > div > p {{
        color: inherit !important;
    }}

    /* Form submit button styles */
    .stButton > button[kind="secondaryFormSubmit"],
    .stButton > button[data-testid="baseButton-secondaryFormSubmit"] {{
        background-color: var(--primary-color) !important;
        color: {get_contrasting_text_color(theme['primaryColor'])} !important;
        border: none !important;
    }}
    .stButton > button[kind="secondaryFormSubmit"]:hover,
    .stButton > button[data-testid="baseButton-secondaryFormSubmit"]:hover {{
        opacity: 0.8;
    }}

    /* Sidebar button styles */
    [data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        text-align: left;
        background-color: transparent !important;
        color: var(--text-color) !important;
        border: 1px solid var(--text-color) !important;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        background-color: var(--primary-color) !important;
        color: var(--background-color) !important;
        border-color: var(--primary-color) !important;
    }}

    /* Settings page button styles */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] .stButton > button {{
        width: 100%;
        text-align: left;
        background-color: transparent !important;
        color: var(--text-color) !important;
        border: none !important;
        border-radius: 0;
    }}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] .stButton > button:hover {{
        background-color: var(--primary-color) !important;
        color: var(--background-color) !important;
    }}

    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea textarea {{
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border-color: var(--primary-color) !important;
    }}
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea textarea:focus {{
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 1px var(--primary-color) !important;
    }}

    /* Placeholder text color */
    .stTextInput > div > div > input::placeholder,
    .stNumberInput > div > div > input::placeholder,
    .stTextArea textarea::placeholder {{
        color: var(--text-color) !important;
        opacity: 0.6;
    }}

    /* Specific styling for number input */
    [data-testid="stNumberInput"] input {{
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border-color: var(--primary-color) !important;
    }}

    /* Dropdowns */
    .stSelectbox > div > div {{
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
    }}
    .stSelectbox > div > div > div {{
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
    }}
    .stSelectbox [data-baseweb="select"] > div,
    .stSelectbox [data-baseweb="select"] ul,
    .stSelectbox [data-baseweb="select"] [role="option"] {{
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
    }}
    .stSelectbox [data-baseweb="select"] [role="option"]:hover {{
        background-color: var(--primary-color) !important;
        color: var(--background-color) !important;
    }}

    /* Dropdown menu items */
    .st-emotion-cache-1ppb27g,
    .st-emotion-cache-crpzz5 {{
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
    }}
    .st-emotion-cache-1ppb27g:hover,
    .st-emotion-cache-crpzz5:hover,
    .stSelectbox [data-baseweb="select"] [role="option"]:hover {{
        background-color: var(--primary-color) !important;
        color: var(--background-color) !important;
    }}
    .st-emotion-cache-sy3zga {{
        color: var(--text-color) !important;
    }}

    /* Ensure text color changes on hover for better contrast */
    .st-emotion-cache-1ppb27g:hover .st-emotion-cache-sy3zga,
    .st-emotion-cache-crpzz5:hover .st-emotion-cache-sy3zga,
    .stSelectbox [data-baseweb="select"] [role="option"]:hover .st-emotion-cache-sy3zga {{
        color: var(--background-color) !important;
    }}

    /* Number input step buttons */
    .stNumberInput [data-testid="stNumberInput-StepDown"],
    .stNumberInput [data-testid="stNumberInput-StepUp"] {{
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border-color: var(--primary-color) !important;
    }}
    .stNumberInput [data-testid="stNumberInput-StepDown"]:hover,
    .stNumberInput [data-testid="stNumberInput-StepUp"]:hover {{
        background-color: var(--primary-color) !important;
        color: var(--background-color) !important;
    }}

    /* Checkboxes and radio buttons */
    .stCheckbox, .stRadio {{
        color: var(--text-color);
    }}

    /* Sliders */
    .stSlider > div > div > div > div {{
        background-color: var(--primary-color);
    }}
    </style>
    """


def get_read_more_button_css(theme):
    is_light_theme = is_light_color(theme["backgroundColor"])
    button_bg_color = (
        theme["secondaryBackgroundColor"]
        if is_light_theme
        else theme["backgroundColor"]
    )
    button_text_color = theme["textColor"]
    button_border_color = theme["primaryColor"]
    button_hover_bg_color = theme["primaryColor"]
    button_hover_text_color = get_contrasting_text_color(button_hover_bg_color)

    return f"""
    .stButton.read-more-button > button {{
        width: auto;
        height: auto;
        white-space: normal;
        word-wrap: break-word;
        background-color: {button_bg_color} !important;
        color: {button_text_color} !important;
        border: 1px solid {button_border_color} !important;
        padding: 5px 10px;
        font-size: 14px;
        border-radius: 4px;
        transition: all 0.3s ease;
        float: right;
        margin-top: 10px;
    }}
    .stButton.read-more-button > button:hover {{
        background-color: {button_hover_bg_color} !important;
        color: {button_hover_text_color} !important;
    }}
    """


def is_light_color(hex_color):
    # Convert hex to RGB
    rgb = tuple(int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    # Calculate luminance
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    return luminance > 0.5


def get_my_articles_css(theme):
    is_light_theme = is_light_color(theme["backgroundColor"])
    primary_button_bg_color = theme["primaryColor"]
    primary_button_text_color = get_contrasting_text_color(primary_button_bg_color)
    secondary_button_bg_color = (
        theme["secondaryBackgroundColor"]
        if is_light_theme
        else theme["backgroundColor"]
    )
    secondary_button_text_color = theme["textColor"]
    secondary_button_border_color = theme["primaryColor"]

    return f"""
    <style>
    .article-card {{
        background-color: {theme['secondaryBackgroundColor']};
        color: {theme['textColor']};
        border: 1px solid {theme['primaryColor']};
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        height: auto;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    .article-card:hover {{
        background-color: {theme['primaryColor']};
        color: {get_contrasting_text_color(theme['primaryColor'])};
    }}

    /* Primary button styles */
    .stButton > button,
    .stButton > button:hover,
    .stButton > button:focus,
    .stButton > button:active {{
        background-color: {primary_button_bg_color} !important;
        color: {primary_button_text_color} !important;
        border: none !important;
        padding: 5px 10px;
        font-size: 14px;
        border-radius: 4px;
        transition: all 0.3s ease;
    }}
    .stButton > button:hover {{
        opacity: 0.8;
    }}

    /* Secondary button styles */
    button[kind="secondary"],
    button[kind="secondaryFormSubmit"],
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-secondaryFormSubmit"] {{
        background-color: {secondary_button_bg_color} !important;
        color: {secondary_button_text_color} !important;
        border: 1px solid {secondary_button_border_color} !important;
        padding: 5px 10px;
        font-size: 14px;
        border-radius: 4px;
        transition: all 0.3s ease;
    }}
    button[kind="secondary"]:hover,
    button[kind="secondaryFormSubmit"]:hover,
    button[data-testid="baseButton-secondary"]:hover,
    button[data-testid="baseButton-secondaryFormSubmit"]:hover {{
        background-color: {theme['primaryColor']} !important;
        color: {get_contrasting_text_color(theme['primaryColor'])} !important;
    }}

    /* Form submit button styles */
    .stButton > button[kind="secondaryFormSubmit"],
    .stButton > button[data-testid="baseButton-secondaryFormSubmit"] {{
        background-color: {primary_button_bg_color} !important;
        color: {primary_button_text_color} !important;
        border: none !important;
    }}
    .stButton > button[kind="secondaryFormSubmit"]:hover,
    .stButton > button[data-testid="baseButton-secondaryFormSubmit"]:hover {{
        opacity: 0.8;
    }}

    /* Tooltip styles */
    .stTooltipIcon {{
        color: {theme['textColor']} !important;
    }}
    .stTooltipContent {{
        background-color: {theme['secondaryBackgroundColor']} !important;
        color: {theme['textColor']} !important;
        border: 1px solid {theme['primaryColor']} !important;
    }}

    .pagination-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
    }}
    .pagination-container > div {{
        margin: 0 10px;
    }}

    /* Ensure button text is always visible */
    .stButton > button > div > p {{
        color: inherit !important;
    }}
    </style>
    """


def get_form_submit_button_css(theme):
    primary_color = theme["primaryColor"]
    bg_color = theme["backgroundColor"]
    is_light_theme = is_light_color(bg_color)

    text_color = get_contrasting_text_color(primary_color)
    hover_bg_color = adjust_color_brightness(
        primary_color, -30 if is_light_theme else 30
    )
    hover_text_color = get_contrasting_text_color(hover_bg_color)

    return f"""
    <style>
    div[data-testid="stForm"] .stButton > button {{
        background-color: {primary_color} !important;
        color: {text_color} !important;
        border-color: {primary_color} !important;
        border-style: solid !important;
        border-width: 1px !important;
        border-radius: 4px !important;
        padding: 0.25rem 0.75rem !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        transition: all 0.3s ease !important;
    }}
    div[data-testid="stForm"] .stButton > button:hover {{
        background-color: {hover_bg_color} !important;
        color: {hover_text_color} !important;
        border-color: {hover_bg_color} !important;
    }}
    div[data-testid="stForm"] .stButton > button:active {{
        background-color: {adjust_color_brightness(hover_bg_color, -20)} !important;
        transform: translateY(2px);
    }}
    </style>
    """


def get_global_css(theme):
    return f"""
    <style>
    /* Base styles */
    .stApp {{
        background-color: {theme['backgroundColor']};
        color: {theme['textColor']};
        font-family: {theme['font']};
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {theme['secondaryBackgroundColor']};
        color: {theme['textColor']};
    }}

    /* Buttons */
    .stButton > button {{
        background-color: {theme['primaryColor']};
        color: {theme['backgroundColor']};
        border: none;
        padding: 5px 10px;
        font-size: 14px;
        border-radius: 4px;
        transition: all 0.3s ease;
    }}
    .stButton > button:hover {{
        background-color: {adjust_color_brightness(theme['primaryColor'], -20)};
    }}

    /* Sidebar button styles */
    [data-testid="stSidebar"] .stButton > button {{
        background-color: transparent;
        color: {theme['textColor']};
        border: 1px solid {theme['textColor']};
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        background-color: {theme['primaryColor']};
        color: {theme['backgroundColor']};
        border-color: {theme['primaryColor']};
    }}

    /* ... (rest of the global CSS) ... */
    </style>
    """


def load_and_apply_theme():
    if "current_theme" not in st.session_state:
        st.session_state.current_theme = load_theme_from_db()

    current_theme = st.session_state.current_theme

    # Apply custom CSS
    st.markdown(get_theme_css(current_theme), unsafe_allow_html=True)

    # Apply option menu styles
    option_menu_style = get_option_menu_style(current_theme)
    st.session_state.option_menu_style = option_menu_style

    return current_theme


def update_theme_and_rerun(new_theme):
    save_theme(new_theme)
    st.session_state.current_theme = new_theme
    st.rerun()


def get_preview_html(theme):
    return f"""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <div style="display: flex; gap: 10px;">
        <div style="background-color: {theme['secondaryBackgroundColor']}; color: {theme['textColor']}; padding: 10px; border-radius: 5px; width: 150px;">
            <h4 style="margin: 0;">Sidebar</h4>
            <p><i class="fas fa-home"></i> General</p>
            <p style="color: {theme['primaryColor']};"><i class="fas fa-pencil-alt"></i> Theme</p>
            <p><i class="fas fa-cog"></i> Advanced</p>
        </div>
        <div style="background-color: {theme['backgroundColor']}; color: {theme['textColor']}; padding: 10px; border-radius: 5px; flex-grow: 1;">
            <h3>Preview</h3>
            <p>This is how your theme will look.</p>
            <button style="background-color: {theme['primaryColor']}; color: #FFFFFF; border: none; padding: 5px 10px; border-radius: 3px;">Button</button>
            <input type="text" placeholder="Input field" style="background-color: {theme['secondaryBackgroundColor']}; color: {theme['textColor']}; border: 1px solid {theme['primaryColor']}; padding: 5px; margin-top: 5px; width: 100%;">
        </div>
    </div>
    """


def get_all_custom_css(theme):
    return f"""
    <style>
    /* Read More button styles */
    .stButton>button {{
        width: auto;
        height: auto;
        white-space: normal;
        word-wrap: break-word;
        background-color: {theme['sidebarBackgroundColor']};
        color: {theme['primaryColor']};
        border: 1px solid {theme['primaryColor']};
        padding: 5px 10px;
        font-size: 14px;
        border-radius: 4px;
        transition: all 0.3s ease;
        float: right;
        margin-top: 10px;
    }}
    .stButton>button:hover {{
        background-color: {theme['primaryColor']};
        color: {theme['backgroundColor']};
    }}

    /* Additional custom CSS */
    .st-primary-button > button {{
        width: 100%;
        font-size: 14px;
        padding: 5px 10px;
    }}
    .article-container {{
        display: flex;
        flex-direction: column;
        height: 100%;
    }}
    .article-content {{
        flex-grow: 1;
    }}
    .button-container {{
        display: flex;
        justify-content: flex-end;
    }}
    .small-font {{
        font-size: 14px;
        margin: 0px;
        padding: 0px;
    }}

    /* New style for secondary buttons */
    button[kind="secondary"],
    button[data-testid="baseButton-secondary"] {{
        background-color: {theme['sidebarBackgroundColor']} !important;
        color: {theme['primaryColor']} !important;
        border: 0px;
    }}

    /* Ensure button text is always visible */
    .stButton > button > div > p {{
        color: inherit !important;
    }}
    </style>
    """
