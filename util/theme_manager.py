import streamlit as st
import sqlite3
import json

dracula_soft_dark = {
    "primaryColor": "#bf96f9",
    "backgroundColor": "#282a36",
    "secondaryBackgroundColor": "#44475a",
    "textColor": "#f8f8f2",
    "sidebarBackgroundColor": "#444759",
    "sidebarTextColor": "#6272a4",
    "font": "sans serif",
}

tokyo_night = {
    "primaryColor": "#7aa2f7",
    "backgroundColor": "#1a1b26",
    "secondaryBackgroundColor": "#24283b",
    "textColor": "#a9b1d6",
    "sidebarBackgroundColor": "#16161e",
    "sidebarTextColor": "#565f89",
    "font": "sans serif",
}

github_dark = {
    "primaryColor": "#58a6ff",
    "backgroundColor": "#0d1117",
    "secondaryBackgroundColor": "#161b22",
    "textColor": "#c9d1d9",
    "sidebarBackgroundColor": "#090c10",
    "sidebarTextColor": "#8b949e",
    "font": "sans serif",
}

github_light = {
    "primaryColor": "#0969da",
    "backgroundColor": "#ffffff",
    "secondaryBackgroundColor": "#f6f8fa",
    "textColor": "#24292f",
    "sidebarBackgroundColor": "#f0f2f4",
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
    "GitHub Light": github_light,
    "Solarized Light": solarized_light,
    "Nord Light": nord_light,
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
        return {**dracula_soft_dark, **stored_theme}
    return dracula_soft_dark


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
            "color": theme["sidebarTextColor"],
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
    contrasting_text_color = get_contrasting_text_color(theme["primaryColor"])
    return f"""
    <style>
    :root {{
        --primary-color: {theme['primaryColor']};
        --background-color: {theme['backgroundColor']};
        --secondary-background-color: {theme['secondaryBackgroundColor']};
        --text-color: {theme['textColor']};
        --sidebar-background-color: {theme['sidebarBackgroundColor']};
        --sidebar-text-color: {theme['sidebarTextColor']};
        --font: {theme['font']};
    }}

    /* Base styles */
    body {{
        background-color: var(--background-color);
        color: var(--text-color);
        font-family: var(--font);
    }}
    .stApp {{
        background-color: var(--background-color);
    }}

    /* Text elements */
    p, h1, h2, h3, h4, h5, h6, li, span, label {{
        color: var(--text-color) !important;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: var(--sidebar-background-color);
        color: var(--sidebar-text-color);
    }}
    [data-testid="stSidebar"] .stMarkdown p {{
        color: var(--sidebar-text-color) !important;
    }}

    /* Buttons */
    .stButton > button {{
        background-color: var(--primary-color);
        color: {contrasting_text_color};
        border-color: var(--primary-color);
    }}
    .stButton > button:hover {{
        background-color: {adjust_color_brightness(theme['primaryColor'], -20)};
        color: {contrasting_text_color};
        border-color: {adjust_color_brightness(theme['primaryColor'], -20)};
    }}

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stNumberInput > div > div > input {{
        background-color: var(--secondary-background-color);
        color: var(--text-color);
        border-color: var(--primary-color);
    }}

    /* Dropdowns */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {{
        background-color: var(--secondary-background-color);
        color: var(--text-color);
    }}
    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div {{
        background-color: var(--secondary-background-color);
        color: var(--text-color);
    }}
    .stSelectbox > div > div > ul,
    .stMultiSelect > div > div > ul {{
        background-color: var(--secondary-background-color);
        color: var(--text-color);
    }}
    .stSelectbox [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="select"] > div {{
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color);
    }}

    /* Checkbox and Radio */
    .stCheckbox > label,
    .stRadio > label {{
        color: var(--text-color) !important;
    }}

    /* Slider */
    .stSlider > div > div > div > div {{
        background-color: var(--primary-color);
    }}

    /* Date and Time inputs */
    .stDateInput > div > div > input,
    .stTimeInput > div > div > input {{
        background-color: var(--secondary-background-color);
        color: var(--text-color);
    }}

    /* File uploader */
    .stFileUploader > div > div {{
        background-color: var(--secondary-background-color);
        color: var(--text-color);
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        background-color: var(--secondary-background-color);
        color: var(--text-color) !important;
    }}

    /* Dataframes and Tables */
    .stDataFrame, .stTable {{
        background-color: var(--secondary-background-color);
        color: var(--text-color);
    }}

    /* Metric */
    [data-testid="stMetricValue"] {{
        color: var(--text-color) !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: var(--secondary-background-color);
    }}
    .stTabs [data-baseweb="tab"] {{
        color: var(--text-color);
    }}
    .stTabs [data-baseweb="tab-border"] {{
        background-color: var(--primary-color);
    }}

    /* Plotly charts */
    .js-plotly-plot .plotly {{
        background-color: var(--secondary-background-color) !important;
    }}

    /* Pagination */
    .stPagination > div > div > div > div {{
        background-color: var(--secondary-background-color);
        color: var(--text-color);
    }}

    /* Code blocks */
    .stCodeBlock {{
        background-color: var(--secondary-background-color);
    }}

    /* Tooltips */
    .stTooltipIcon {{
        color: var(--text-color) !important;
    }}

    /* Option menu (if you're using streamlit-option-menu) */
    .stOptionMenu {{
        background-color: var(--sidebar-background-color);
    }}
    .stOptionMenu .nav-link {{
        color: var(--sidebar-text-color) !important;
    }}
    .stOptionMenu .nav-link.active {{
        background-color: var(--primary-color);
        color: {contrasting_text_color} !important;
    }}
    </style>
    """


def adjust_color_brightness(hex_color, brightness_offset):
    # Convert hex to RGB
    rgb = tuple(int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    # Adjust brightness
    new_rgb = tuple(max(0, min(255, c + brightness_offset)) for c in rgb)
    # Convert back to hex
    return "#{:02x}{:02x}{:02x}".format(*new_rgb)


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
