import streamlit as st
from pages_util.style import get_style, default_style
from pages_util.theme_utils import (
    dark_themes,
    light_themes,
    get_theme_css,
    get_preview_html,
)


def settings_sidebar():
    st.sidebar.title("Settings")
    return st.sidebar.radio("Settings Section", ["General", "Theme", "Advanced"])


def settings_page():
    selected_section = settings_sidebar()

    st.title("Settings")

    if selected_section == "General":
        st.header("General Settings")
        st.selectbox("Language", ["English", "Spanish", "French"])

    elif selected_section == "Theme":
        st.header("Theme Settings")
        theme_mode = st.radio("Theme Mode", ["Dark", "Light"])

        if theme_mode == "Dark":
            theme_options = dark_themes
        else:
            theme_options = light_themes

        selected_theme_name = st.selectbox("Select a theme", list(theme_options.keys()))
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

        with col2:
            st.markdown(get_preview_html(custom_theme), unsafe_allow_html=True)

        if st.button("Apply Theme"):
            st.session_state.current_theme = custom_theme
            st.session_state.custom_style = get_theme_css(custom_theme)
            st.experimental_rerun()

    elif selected_section == "Advanced":
        st.header("Advanced Settings")
        st.slider("Font size", min_value=8, max_value=24, value=16)

    # Apply the current theme
    custom_style = st.session_state.get("custom_style", get_style())
    st.markdown(custom_style, unsafe_allow_html=True)
