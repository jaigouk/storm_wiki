import streamlit as st
import os
from dotenv import load_dotenv

from util.phoenix_setup import setup_phoenix
from pages_util import MyArticles, CreateNewArticle, Settings
from streamlit_option_menu import option_menu
from util.session_state import clear_other_page_session_state
from util.theme_manager import init_db, load_and_apply_theme, get_option_menu_style

load_dotenv()

# Set page config first
st.set_page_config(layout="wide")

# Custom CSS to hide the progress bar and other loading indicators
hide_streamlit_style = """
<style>
    header {visibility: hidden;}
    .stProgress, .stSpinner, .st-emotion-cache-1dp5vir {
        display: none !important;
    }
    div.block-container{padding-top:1rem;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

script_dir = os.path.dirname(os.path.abspath(__file__))
wiki_root_dir = os.path.dirname(os.path.dirname(script_dir))


def main():
    setup_phoenix()
    init_db()

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
        st.session_state["selected_page"] = 0
    if st.session_state.get("rerun_requested", False):
        st.session_state["rerun_requested"] = False
        st.rerun()

    # Load theme from database
    current_theme = load_and_apply_theme()
    st.session_state.current_theme = current_theme

    # Create the sidebar menu
    with st.sidebar:
        st.title("Storm wiki")
        pages = ["My Articles", "Create New Article", "Settings"]
        menu_selection = option_menu(
            menu_title=None,
            options=pages,
            icons=["house", "pencil-square", "gear"],
            menu_icon="cast",
            default_index=0,
            styles=get_option_menu_style(current_theme),
            key="menu_selection",
        )

        # Add submenu for Settings
        if menu_selection == "Settings":
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("### Settings Section")
            settings_options = ["General", "Theme", "Advanced"]
            selected_setting = option_menu(
                menu_title=None,
                options=settings_options,
                icons=["gear", "palette", "tools"],
                menu_icon=None,
                default_index=0,
                styles=get_option_menu_style(current_theme),
                key="settings_submenu",
            )
            # Store the selected setting in session state
            st.session_state.selected_setting = selected_setting

    # Display the selected page
    if menu_selection == "My Articles":
        clear_other_page_session_state(page_index=2)
        MyArticles.my_articles_page()
    elif menu_selection == "Create New Article":
        clear_other_page_session_state(page_index=3)
        CreateNewArticle.create_new_article_page()
    elif menu_selection == "Settings":
        Settings.settings_page(st.session_state.selected_setting)

    # Update selected_page in session state
    st.session_state["selected_page"] = pages.index(menu_selection)


if __name__ == "__main__":
    main()
