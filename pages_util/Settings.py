import streamlit as st
from pages_util.theme_utils import (
    dark_themes,
    light_themes,
    get_theme_css,
    get_preview_html,
    get_contrasting_text_color,
)
from util.db_utils import save_theme, load_theme


def settings_page():
    st.title("Settings")

    # Sidebar
    with st.sidebar:
        st.title("Settings Section")
        selected_section = st.radio(
            "",
            ["General", "Theme", "Advanced"],
            format_func=lambda x: f"📊 {x}"
            if x == "General"
            else f"🎨 {x}"
            if x == "Theme"
            else f"⚙️ {x}",
            key="settings_section",
        )

    # Main content
    if selected_section == "General":
        st.header("General Settings")
        st.selectbox("Language", ["English", "Spanish", "French"])

    elif selected_section == "Theme":
        st.header("Theme Settings")
        theme_mode = st.radio("Theme Mode", ["Light", "Dark"])

        theme_options = light_themes if theme_mode == "Light" else dark_themes
        current_theme = st.session_state.get("current_theme", load_theme())

        selected_theme_name = st.selectbox(
            "Select a theme",
            list(theme_options.keys()),
            index=list(theme_options.keys()).index(
                next(
                    (k for k, v in theme_options.items() if v == current_theme),
                    list(theme_options.keys())[0],
                )
            ),
        )

        # Update current_theme when a new theme is selected
        current_theme = theme_options[selected_theme_name]

        st.subheader("Color Customization")
        col1, col2 = st.columns(2)

        with col1:
            custom_theme = {}
            for key, value in current_theme.items():
                if key != "font":
                    custom_theme[key] = st.color_picker(f"{key}", value)
                else:
                    custom_theme[key] = st.selectbox(
                        "Font",
                        ["sans serif", "serif", "monospace"],
                        index=["sans serif", "serif", "monospace"].index(value),
                    )

            # Determine text color based on background
            custom_theme["textColor"] = get_contrasting_text_color(
                custom_theme["backgroundColor"]
            )

        with col2:
            st.markdown(get_preview_html(custom_theme), unsafe_allow_html=True)

        if st.button("Apply Theme"):
            save_theme(custom_theme)
            st.session_state.current_theme = custom_theme
            st.session_state.custom_style = get_theme_css(custom_theme)
            st.success("Theme applied successfully!")
            st.experimental_rerun()

    elif selected_section == "Advanced":
        st.header("Advanced Settings")
        st.slider("Font size", min_value=8, max_value=24, value=16)

    # Apply the current theme
    current_theme = st.session_state.get("current_theme", load_theme())
    st.markdown(get_theme_css(current_theme), unsafe_allow_html=True)

    # Apply background and text color
    page_bg_style = f"""
    <style>
    .stApp {{
        background-color: {current_theme['backgroundColor']};
        color: {current_theme['textColor']};
    }}
    [data-testid="stSidebar"] {{
        background-color: {current_theme['sidebarBackgroundColor']};
        color: {get_contrasting_text_color(current_theme['sidebarBackgroundColor'])};
    }}
    .stButton > button {{
        color: {get_contrasting_text_color(current_theme['primaryColor'])};
        background-color: {current_theme['primaryColor']};
    }}
    .stTextInput > div > div > input {{
        color: {current_theme['textColor']};
    }}
    .stSelectbox > div > div > select {{
        background-color: {current_theme['secondaryBackgroundColor']};
        color: {current_theme['textColor']};
    }}
    h1, h2, h3, h4, h5, h6, p, li, a {{
        color: {current_theme['textColor']} !important;
    }}
    .stMarkdown {{
        color: {current_theme['textColor']};
    }}
    </style>
    """

    st.markdown(page_bg_style, unsafe_allow_html=True)
