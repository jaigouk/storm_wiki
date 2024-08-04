import streamlit as st
from util.file_io import FileIOHelper
from util.ui_components import UIComponents
from util.theme_manager import load_and_apply_theme
from pages_util.Settings import load_general_settings, save_general_settings
import logging

logging.basicConfig(level=logging.DEBUG)


def initialize_session_state():
    if "page_size" not in st.session_state:
        st.session_state.page_size = 24
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1
    if "num_columns" not in st.session_state:
        general_settings = load_general_settings()
        try:
            if isinstance(general_settings, dict):
                num_columns = general_settings.get("num_columns", 3)
                if isinstance(num_columns, dict):
                    num_columns = num_columns.get("num_columns", 3)
            else:
                num_columns = general_settings
            st.session_state.num_columns = int(num_columns)
        except (ValueError, TypeError):
            st.session_state.num_columns = 3  # Default to 3 if conversion fails
    if "trigger_rerun" not in st.session_state:
        st.session_state.trigger_rerun = False


def display_selected_article():
    logging.debug(
        f"Displaying selected article: {st.session_state.page2_selected_my_article}"
    )
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
        show_references_in_sidebar=True,
    )

    if st.button("Back to Article List"):
        logging.debug("Back to Article List button clicked")
        del st.session_state.page2_selected_my_article
        st.rerun()


def read_more_callback(article_key):
    logging.debug(f"Read More callback triggered for article: {article_key}")
    st.session_state.page2_selected_my_article = article_key


def read_more_callback(article_key):
    logging.debug(f"Read More callback triggered for article: {article_key}")
    st.session_state.page2_selected_my_article = article_key
    st.session_state.trigger_rerun = True


def display_article_list(page_size, num_columns):
    articles = st.session_state.user_articles
    article_keys = list(articles.keys())
    total_articles = len(article_keys)

    # Use the new values for display
    current_page = st.session_state.current_page - 1  # Convert to 0-indexed
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, total_articles)

    # Display articles
    cols = st.columns(num_columns)

    for i in range(start_idx, end_idx):
        article_key = article_keys[i]
        article_file_path_dict = articles[article_key]

        with cols[i % num_columns]:
            article_data = FileIOHelper.assemble_article_data(article_file_path_dict)
            short_text = article_data.get("short_text", "") + "..."

            st.markdown(f"### {article_key.replace('_', ' ')}")
            st.markdown(short_text)
            if st.button("Read More", key=f"read_more_{article_key}"):
                read_more_callback(article_key)
                st.rerun()

    # Pagination controls
    st.sidebar.write("### Navigation")
    col1, col2 = st.sidebar.columns(2)

    num_pages = max(1, (total_articles + page_size - 1) // page_size)

    with col1:
        if st.button("← Previous", disabled=(st.session_state.current_page == 1)):
            st.session_state.current_page = max(1, st.session_state.current_page - 1)
            st.session_state.trigger_rerun = True

    with col2:
        if st.button("Next →", disabled=(st.session_state.current_page == num_pages)):
            st.session_state.current_page = min(
                num_pages, st.session_state.current_page + 1
            )
            st.session_state.trigger_rerun = True

    new_page = st.sidebar.number_input(
        "Page",
        min_value=1,
        max_value=num_pages,
        value=st.session_state.current_page,
        key="page_number_input",
    )
    if new_page != st.session_state.current_page:
        st.session_state.current_page = new_page
        st.session_state.trigger_rerun = True

    st.sidebar.write(f"of {num_pages} pages")


def my_articles_page():
    logging.debug("Entering my_articles_page function")
    initialize_session_state()
    UIComponents.apply_custom_css()

    if "user_articles" not in st.session_state:
        local_dir = FileIOHelper.get_output_dir()
        st.session_state.user_articles = FileIOHelper.read_structure_to_dict(local_dir)

    if "page2_selected_my_article" in st.session_state:
        logging.debug(
            f"Displaying selected article: {st.session_state.page2_selected_my_article}"
        )
        display_selected_article()
    else:
        logging.debug("Displaying article list")
        display_article_list(st.session_state.page_size, st.session_state.num_columns)

    logging.debug(f"Session state at end of my_articles_page: {st.session_state}")
