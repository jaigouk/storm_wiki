import logging
import re
import streamlit as st
import math
from util.file_io import DemoFileIOHelper
from util.path_utils import get_output_dir
from util.ui_components import UIComponents
from util.theme_manager import load_and_apply_theme, get_my_articles_css

logging.basicConfig(level=logging.DEBUG)


def initialize_session_state():
    if "page_size" not in st.session_state:
        st.session_state.page_size = 24
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1


def update_page_size():
    st.session_state.page_size = st.session_state.page_size_select
    st.session_state.current_page = 1
    st.session_state.need_rerun = True


def display_selected_article():
    selected_article_name = st.session_state.page2_selected_my_article
    selected_article_file_path_dict = st.session_state.user_articles[
        selected_article_name
    ]

    UIComponents.display_article_page(
        selected_article_name=selected_article_name.replace("_", " "),
        selected_article_file_path_dict=selected_article_file_path_dict,
        show_title=True,
        show_main_article=True,
        show_feedback_form=False,
        show_qa_panel=False,
    )

    if st.button("Back to Article List"):
        del st.session_state.page2_selected_my_article
        st.rerun()


def display_article_list(page_size):
    current_theme = load_and_apply_theme()
    articles = st.session_state.user_articles
    article_keys = list(articles.keys())
    total_articles = len(article_keys)

    num_pages = (total_articles + page_size - 1) // page_size
    current_page = st.selectbox("Page", range(1, num_pages + 1)) - 1
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, total_articles)

    # Create a 2-column layout
    cols = st.columns(2)

    for i in range(start_idx, end_idx):
        article_key = article_keys[i]
        article_file_path_dict = articles[article_key]

        with cols[i % 2]:
            with st.container():
                # Article card
                article_name = article_key.replace("_", " ")
                st.subheader(article_name)

                # Display a preview of the article content
                article_data = DemoFileIOHelper.assemble_article_data(
                    article_file_path_dict
                )
                if article_data:
                    # st.write(article_data.keys())
                    content_preview = article_data.get("short_text", "")

                    st.write(content_preview + "...")

                if st.button(
                    "Read More",
                    type="secondary",
                    key=f"view_{article_key}",
                    use_container_width=False,
                ):
                    st.session_state.page2_selected_my_article = article_key
                    st.rerun()


# In your my_articles_page function:
def my_articles_page():
    initialize_session_state()
    current_theme = load_and_apply_theme()
    st.markdown(get_my_articles_css(current_theme), unsafe_allow_html=True)

    if "user_articles" not in st.session_state:
        local_dir = get_output_dir()
        st.session_state.user_articles = DemoFileIOHelper.read_structure_to_dict(
            local_dir
        )

    if "page_size" not in st.session_state:
        st.session_state.page_size = 12  # Default page size

    page_size_options = [12, 24, 48, 96]
    selected_page_size = st.selectbox(
        "Items per page",
        page_size_options,
        index=page_size_options.index(st.session_state.page_size),
    )

    if selected_page_size != st.session_state.page_size:
        st.session_state.page_size = selected_page_size

    if "page2_selected_my_article" in st.session_state:
        selected_article_name = st.session_state.page2_selected_my_article
        selected_article_file_path_dict = st.session_state.user_articles[
            selected_article_name
        ]
        UIComponents.display_article_page(
            selected_article_name,
            selected_article_file_path_dict,
            show_title=True,
            show_main_article=True,
            show_feedback_form=False,
            show_qa_panel=False,
        )
    else:
        display_article_list(page_size=st.session_state.page_size)
