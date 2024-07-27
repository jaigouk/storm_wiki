import streamlit as st
import os
from dotenv import load_dotenv

from util.phoenix_setup import setup_phoenix
from pages_util import MyArticles, CreateNewArticle, Settings
from streamlit_float import *
from streamlit_option_menu import option_menu
from util.session_state import clear_other_page_session_state
from pages_util.theme_utils import dracula_soft_dark, get_theme_css
from pages_util.style import get_style, default_style

load_dotenv()

# Set page config first
st.set_page_config(layout="wide")


hide_decoration_bar_style = """
    <style>
        header {visibility: hidden;}
    </style>
"""
st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

script_dir = os.path.dirname(os.path.abspath(__file__))
wiki_root_dir = os.path.dirname(os.path.dirname(script_dir))


def main():
    setup_phoenix()

    if "first_run" not in st.session_state:
        st.session_state["first_run"] = True

    # set api keys from secrets
    if st.session_state["first_run"]:
        for key, value in st.secrets.items():
            if isinstance(value, str):
                os.environ[key] = value

    # initialize session_state
    if "selected_article_index" not in st.session_state:
        st.session_state["selected_article_index"] = 0
    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = "My Articles"
    if st.session_state.get("rerun_requested", False):
        st.session_state["rerun_requested"] = False
        st.rerun()

    if "current_theme" not in st.session_state:
        st.session_state.current_theme = dracula_soft_dark

    st.session_state.custom_style = get_theme_css(dracula_soft_dark)
    # Apply custom CSS
    st.markdown(st.session_state.custom_style, unsafe_allow_html=True)

    st.sidebar.title("Storm wiki")

    # Create the navigation
    selected_page = st.sidebar.radio(
        "Navigation",
        ["My Articles", "Create New Article", "Settings"],
        format_func=lambda x: f"{x} {'📚' if x == 'My Articles' else '✏️' if x == 'Create New Article' else '⚙️'}",
    )

    # Run the selected page
    if selected_page == "My Articles":
        clear_other_page_session_state(page_index=2)
        MyArticles.my_articles_page()
    elif selected_page == "Create New Article":
        clear_other_page_session_state(page_index=3)
        CreateNewArticle.create_new_article_page()
    elif selected_page == "Settings":
        Settings.settings_page()

    # Update selected_page in session state
    st.session_state["selected_page"] = selected_page


if __name__ == "__main__":
    main()
