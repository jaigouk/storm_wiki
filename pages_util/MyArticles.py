import logging
import streamlit as st
from util.file_io import DemoFileIOHelper
from util.path_utils import get_output_dir
from util.ui_components import UIComponents
from util.theme_manager import load_and_apply_theme, get_my_articles_css

logging.basicConfig(level=logging.DEBUG)


def my_articles_page():
    try:
        current_theme = load_and_apply_theme()
        st.markdown(get_my_articles_css(current_theme), unsafe_allow_html=True)

        if "page2_user_articles_file_path_dict" not in st.session_state:
            local_dir = get_output_dir()
            st.session_state["page2_user_articles_file_path_dict"] = (
                DemoFileIOHelper.read_structure_to_dict(local_dir)
            )

        if "page2_selected_my_article" not in st.session_state:
            display_article_list()
        else:
            display_selected_article()

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.exception(e)


def display_article_list():
    article_names = sorted(
        list(st.session_state["page2_user_articles_file_path_dict"].keys())
    )

    if not article_names:
        if st.button("Start your first research!", use_container_width=True):
            st.session_state.selected_page = 1
            st.session_state["manual_selection_override"] = True
        return

    # Initialize session state variables
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1
    if "page_size" not in st.session_state:
        st.session_state.page_size = 24

    total_pages = max(1, (len(article_names) - 1) // st.session_state.page_size + 1)
    st.session_state.current_page = min(st.session_state.current_page, total_pages)

    # Display pagination controls
    display_pagination(len(article_names), total_pages)

    # Display articles based on current page and page size
    start_idx = (st.session_state.current_page - 1) * st.session_state.page_size
    end_idx = min(start_idx + st.session_state.page_size, len(article_names))

    for i in range(start_idx, end_idx, 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < end_idx:
                article_name = article_names[i + j]
                with cols[j]:
                    if st.button(
                        article_name, key=f"article_{i+j}", use_container_width=True
                    ):
                        st.session_state["page2_selected_my_article"] = article_name
                        st.experimental_rerun()


def display_pagination(total_articles, total_pages):
    st.markdown("<div class='pagination-container'>", unsafe_allow_html=True)
    cols = st.columns(3)

    with cols[0]:
        st.markdown(f"Total: {total_articles} articles")

    with cols[1]:
        new_page = st.number_input(
            f"Page (of {total_pages})",
            min_value=1,
            max_value=total_pages,
            value=st.session_state.current_page,
            step=1,
            key="page_input",
        )
        if new_page != st.session_state.current_page:
            st.session_state.current_page = new_page
            st.experimental_rerun()

    with cols[2]:
        new_page_size = st.selectbox(
            "Page Size",
            options=[24, 48, 72],
            index=[24, 48, 72].index(st.session_state.page_size),
            key="page_size_select",
        )
        if new_page_size != st.session_state.page_size:
            st.session_state.page_size = new_page_size
            st.session_state.current_page = (
                1  # Reset to first page when changing page size
            )
            st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def display_selected_article():
    selected_article_name = st.session_state["page2_selected_my_article"]
    selected_article_file_path_dict = st.session_state[
        "page2_user_articles_file_path_dict"
    ][selected_article_name]

    UIComponents.display_article_page(
        selected_article_name=selected_article_name,
        selected_article_file_path_dict=selected_article_file_path_dict,
        show_title=True,
        show_main_article=True,
        show_feedback_form=False,
        show_qa_panel=False,
    )

    if st.button("Back to Article List"):
        del st.session_state["page2_selected_my_article"]
        st.experimental_rerun()
