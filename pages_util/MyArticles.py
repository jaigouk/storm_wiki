import os
import logging
import streamlit as st
from streamlit_card import card
from util.file_io import DemoFileIOHelper
from pages_util.style import get_style, default_style

# from util.ui_helpers import DemoUIHelper
from util.path_utils import get_output_dir
from util.display_utils import display_article_page

logging.basicConfig(level=logging.DEBUG)


def article_card_setup(column_to_add, article_name):
    with column_to_add:
        cleaned_article_title = article_name.replace("_", " ")
        hasClicked = card(
            title="",
            text=cleaned_article_title,
            image=DemoFileIOHelper.read_image_as_base64(
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "assets", "void.jpg"
                )
            ),
            styles={
                "card": {
                    "width": "100%",
                    "height": "116px",
                    "background-color": "#44475a",
                    "border": "none",
                    "padding": "10px",
                    "border-radius": "5px",
                    "box-shadow": "0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15)",
                    "margin": "0px",
                    "border-left": "0.5rem solid #bd93f9",
                },
                "text": {
                    "color": "#f8f8f2",
                    "font-size": "16px",
                    "line-height": "1.2",
                    "display": "-webkit-box",
                    "-webkit-line-clamp": "4",
                    "-webkit-box-orient": "vertical",
                    "overflow": "hidden",
                    "text-overflow": "ellipsis",
                    "padding": "5px",
                },
            },
        )
        if hasClicked:
            st.session_state["page2_selected_my_article"] = article_name
            st.rerun()


def my_articles_page():
    try:
        custom_style = st.session_state.get("custom_style", get_style())
        st.markdown(custom_style, unsafe_allow_html=True)

        # sync my articles
        if "page2_user_articles_file_path_dict" not in st.session_state:
            local_dir = get_output_dir()
            st.session_state["page2_user_articles_file_path_dict"] = (
                DemoFileIOHelper.read_structure_to_dict(local_dir)
            )

        if "page2_selected_my_article" not in st.session_state:
            # display article cards
            my_article_columns = st.columns(3)
            if len(st.session_state["page2_user_articles_file_path_dict"]) > 0:
                # get article names
                article_names = sorted(
                    list(st.session_state["page2_user_articles_file_path_dict"].keys())
                )
                # configure pagination
                pagination = st.container()
                bottom_menu = st.columns((1, 4, 1, 1, 1))[1:-1]
                with bottom_menu[2]:
                    batch_size = st.selectbox("Page Size", options=[24, 48, 72])
                with bottom_menu[1]:
                    total_pages = max(1, int(len(article_names) / batch_size))
                    current_page = st.number_input(
                        "Page", min_value=1, max_value=total_pages, step=1
                    )
                with bottom_menu[0]:
                    st.markdown(f"Page **{current_page}** of **{total_pages}** ")
                # show article cards
                with pagination:
                    start_index = (current_page - 1) * batch_size
                    end_index = min(current_page * batch_size, len(article_names))
                    for i, article_name in enumerate(
                        article_names[start_index:end_index]
                    ):
                        column_to_add = my_article_columns[i % 3]
                        article_card_setup(
                            column_to_add=column_to_add,
                            article_name=article_name,
                        )
            else:
                with my_article_columns[0]:
                    hasClicked = card(
                        title="",
                        text="Start your first research!",
                        image=DemoFileIOHelper.read_image_as_base64(
                            os.path.join(
                                os.path.dirname(os.path.dirname(__file__)),
                                "assets",
                                "void.jpg",
                            )
                        ),
                        styles={
                            "card": {
                                "width": "100%",
                                "height": "116px",
                                "background-color": "#44475a",
                                "border": "none",
                                "padding": "10px",
                                "border-radius": "5px",
                                "box-shadow": "0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15)",
                                "margin": "0px",
                                "border-left": "0.5rem solid #bd93f9",
                            },
                            "text": {
                                "color": "#f8f8f2",
                                "font-size": "16px",
                                "line-height": "1.2",
                                "display": "-webkit-box",
                                "-webkit-line-clamp": "4",
                                "-webkit-box-orient": "vertical",
                                "overflow": "hidden",
                                "text-overflow": "ellipsis",
                                "padding": "5px",
                            },
                        },
                    )
                    if hasClicked:
                        st.session_state.selected_page = 1
                        st.session_state["manual_selection_override"] = True
                        st.session_state["rerun_requested"] = True
                        st.rerun()
        else:
            selected_article_name = st.session_state["page2_selected_my_article"]
            selected_article_file_path_dict = st.session_state[
                "page2_user_articles_file_path_dict"
            ][selected_article_name]

            logging.debug(f"Displaying article: {selected_article_name}")
            logging.debug(f"File path dict: {selected_article_file_path_dict}")

            display_article_page(
                selected_article_name=selected_article_name,
                selected_article_file_path_dict=selected_article_file_path_dict,
                show_title=True,
                show_main_article=True,
                show_feedback_form=False,
                show_qa_panel=False,
            )

    except Exception as e:
        logging.error(f"Error in my_articles_page: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        st.exception(e)
