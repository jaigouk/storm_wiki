import streamlit as st
import os
from dotenv import load_dotenv

from util.phoenix_setup import setup_phoenix
from pages_util import MyArticles, CreateNewArticle
from streamlit_float import *
from streamlit_option_menu import option_menu
from util.session_state import clear_other_page_session_state

load_dotenv()

# Set page config first
st.set_page_config(layout="wide")


script_dir = os.path.dirname(os.path.abspath(__file__))
wiki_root_dir = os.path.dirname(os.path.dirname(script_dir))


def apply_custom_css():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #282a36;
        }
        .stSidebar {
            background-color: #44475a;
        }
        .stSidebar .stButton > button {
            background-color: #6272a4;
            color: #f8f8f2;
        }
        .stSidebar .stButton > button:hover {
            background-color: #bd93f9;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def settings_page():
    st.title("Settings")
    st.write("This is the settings page. You can add your settings options here.")
    # Add your settings options here


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

    st.sidebar.title("Storm wiki")

    # Create the navigation
    selected_page = st.sidebar.radio(
        "Navigation",
        ["My Articles", "Create New Article", "Settings"],
        format_func=lambda x: f"{x} {'📚' if x == 'My Articles' else '✏️' if x == 'Create New Article' else '⚙️'}",
    )

    # Apply custom CSS
    apply_custom_css()

    # Run the selected page
    if selected_page == "My Articles":
        clear_other_page_session_state(page_index=2)
        MyArticles.my_articles_page()
    elif selected_page == "Create New Article":
        clear_other_page_session_state(page_index=3)
        CreateNewArticle.create_new_article_page()
    elif selected_page == "Settings":
        settings_page()

    # Update selected_page in session state
    st.session_state["selected_page"] = selected_page


if __name__ == "__main__":
    main()
