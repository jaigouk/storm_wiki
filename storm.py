import streamlit as st
import os
from dotenv import load_dotenv

from util.phoenix_setup import setup_phoenix
from pages_util.MyArticles import my_articles_page
from pages_util.CreateNewArticle import create_new_article_page
from pages_util.Settings import settings_page
from streamlit_option_menu import option_menu
from util.session_state import clear_other_page_session_state
from pages_util.theme_utils import get_theme_css, get_contrasting_text_color
from util.db_utils import init_db, load_theme
from streamlit.components.v1 import html

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
    init_db()  # Initialize the database

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

    # Load theme from database
    current_theme = load_theme()
    st.session_state.current_theme = current_theme
    st.session_state.custom_style = get_theme_css(current_theme)

    # Apply custom CSS
    st.markdown(st.session_state.custom_style, unsafe_allow_html=True)

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

    with st.sidebar:
        st.title("Storm wiki")
        sidebar_style = f"""
        <style>
        [data-testid="stSidebar"] {{
            background-color: {current_theme['sidebarBackgroundColor']};
        }}
        </style>
        """
        st.markdown(sidebar_style, unsafe_allow_html=True)
        selected_page = option_menu(
            menu_title=None,
            options=["My Articles", "Create New Article", "Settings"],
            icons=["book", "pencil-square", "gear"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {
                    "padding": "0!important",
                    "background-color": current_theme["sidebarBackgroundColor"],
                },
                "icon": {
                    "color": get_contrasting_text_color(
                        current_theme["sidebarBackgroundColor"]
                    ),
                    "font-size": "25px",
                },
                "nav-link": {
                    "color": get_contrasting_text_color(
                        current_theme["sidebarBackgroundColor"]
                    ),
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": current_theme["primaryColor"],
                    "background-color": "transparent",
                },
                "nav-link-selected": {
                    "background-color": current_theme["primaryColor"],
                    "color": get_contrasting_text_color(current_theme["primaryColor"]),
                },
            },
        )
    # Run the selected page
    if selected_page == "My Articles":
        clear_other_page_session_state(page_index=2)
        my_articles_page()
    elif selected_page == "Create New Article":
        clear_other_page_session_state(page_index=3)
        create_new_article_page()
    elif selected_page == "Settings":
        settings_page()

    # Update selected_page in session state
    st.session_state["selected_page"] = selected_page


if __name__ == "__main__":
    main()
