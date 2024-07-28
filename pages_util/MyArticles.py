import logging
import streamlit as st
import math
from util.file_io import DemoFileIOHelper
from util.path_utils import get_output_dir
from util.ui_components import UIComponents
from util.theme_manager import load_and_apply_theme, get_my_articles_css

logging.basicConfig(level=logging.DEBUG)


def my_articles_page():
    try:
        current_theme = load_and_apply_theme()
        st.markdown(get_my_articles_css(current_theme), unsafe_allow_html=True)

        # Load articles
        if "user_articles" not in st.session_state:
            local_dir = get_output_dir()
            st.session_state.user_articles = DemoFileIOHelper.read_structure_to_dict(
                local_dir
            )

        article_names = sorted(list(st.session_state.user_articles.keys()))

        # Pagination controls
        total_articles = len(article_names)
        page_sizes = [12, 24, 48]
        col1, col2 = st.columns(2)
        with col1:
            page_size = st.selectbox(
                "Page Size", options=page_sizes, index=1, key="page_size"
            )
        total_pages = math.ceil(total_articles / page_size)
        with col2:
            current_page = st.number_input(
                "Page", min_value=1, max_value=total_pages, value=1, key="current_page"
            )

        # Calculate start and end indices for the current page
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_articles)

        # Display articles for the current page
        st.write(
            f"Displaying articles {start_idx + 1} to {end_idx} out of {total_articles}"
        )

        for i in range(start_idx, end_idx, 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < end_idx:
                    article_name = article_names[i + j]
                    with cols[j]:
                        if st.button(
                            article_name.replace("_", " "),
                            key=f"article_{i+j}",
                            use_container_width=True,
                        ):
                            st.session_state.page2_selected_my_article = article_name
                            st.experimental_rerun()

        # Display selected article if any
        if "page2_selected_my_article" in st.session_state:
            display_selected_article()

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.exception(e)


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
        st.experimental_rerun()
