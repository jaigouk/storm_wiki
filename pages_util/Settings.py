import streamlit as st
from util.theme_manager import (
    dark_themes,
    light_themes,
    get_theme_css,
    get_preview_html,
    get_contrasting_text_color,
    load_and_apply_theme,
    update_theme_and_rerun,
    load_theme_from_db as load_theme,
)


def settings_page(selected_setting):
    current_theme = load_and_apply_theme()
    st.title("Settings")

    if selected_setting == "General":
        st.header("General Settings")
        st.selectbox("Language", ["English", "Spanish", "French"])

    elif selected_setting == "Theme":
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

        with col2:
            st.markdown(get_preview_html(custom_theme), unsafe_allow_html=True)

        if st.button("Apply Theme"):
            update_theme_and_rerun(custom_theme)

    elif selected_setting == "Advanced":
        st.header("Advanced Settings")
        st.slider("Font size", min_value=8, max_value=24, value=16)

    # Apply the current theme
    st.markdown(get_theme_css(current_theme), unsafe_allow_html=True)
