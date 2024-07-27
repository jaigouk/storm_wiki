import streamlit as st
from .text_processing import DemoTextProcessingHelper
from knowledge_storm.storm_wiki.modules.callback import BaseCallbackHandler
import markdown
from util.db_utils import load_theme
import streamlit as st
from streamlit_card import card
import os
from .file_io import DemoFileIOHelper


class DemoUIHelper:
    @staticmethod
    def st_markdown_adjust_size(content, font_size=20):
        current_theme = st.session_state.get("current_theme", load_theme())
        st.markdown(
            f"""
        <span style='font-size: {font_size}px; color: {current_theme['textColor']};'>{content}</span>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def get_article_card_style(current_theme):
        return {
            "card": {
                "width": "100%",
                "height": "116px",
                "padding": "10px",
                "border-radius": "5px",
                "box-shadow": "0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15)",
                "margin": "0px",
                "background-color": current_theme["secondaryBackgroundColor"],
            },
            "text": {
                "font-size": "16px",
                "line-height": "1.2",
                "display": "-webkit-box",
                "-webkit-line-clamp": "4",
                "-webkit-box-orient": "vertical",
                "overflow": "hidden",
                "text-overflow": "ellipsis",
                "padding": "5px",
                "color": current_theme["textColor"],
            },
        }

    @staticmethod
    def create_article_card(article_name, current_theme):
        cleaned_article_title = article_name.replace("_", " ")
        return card(
            title="",
            text=cleaned_article_title,
            image=DemoFileIOHelper.read_image_as_base64(
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "assets", "void.jpg"
                )
            ),
            styles=DemoUIHelper.get_article_card_style(current_theme),
        )

    @staticmethod
    def customize_toast_css_style():
        # Note padding is top right bottom left
        st.markdown(
            """
            <style>

                div[data-testid=stToast] {
                    padding: 20px 10px 40px 10px;
                    background-color: #FF0000;   /* red */
                    width: 40%;
                }

                [data-testid=toastContainer] [data-testid=stMarkdownContainer] > p {
                    font-size: 25px;
                    font-style: normal;
                    font-weight: 400;
                    color: #FFFFFF;   /* white */
                    line-height: 1.5; /* Adjust this value as needed */
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def article_markdown_to_html(article_title, article_content):
        return f"""
        <html>
            <head>
                <meta charset="utf-8">
                <title>{article_title}</title>
                <style>
                    .title {{
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="title">
                    <h1>{article_title.replace('_', ' ')}</h1>
                </div>
                <h2>Table of Contents</h2>
                {DemoTextProcessingHelper.generate_html_toc(article_content)}
                {markdown.markdown(article_content)}
            </body>
        </html>
        """

    @staticmethod
    def display_persona_conversations(conversation_log):
        """
        Display persona conversation in dialogue UI
        """
        # get personas list as (persona_name, persona_description, dialogue turns list) tuple
        parsed_conversation_history = (
            DemoTextProcessingHelper.parse_conversation_history(conversation_log)
        )

        # construct tabs for each persona conversation
        persona_tabs = st.tabs(
            [
                name if name else f"Persona {i}"
                for i, (name, _, _) in enumerate(parsed_conversation_history)
            ]
        )
        for idx, persona_tab in enumerate(persona_tabs):
            with persona_tab:
                # show persona description
                st.info(parsed_conversation_history[idx][1])
                # show user / agent utterance in dialogue UI
                for message in parsed_conversation_history[idx][2]:
                    message["content"] = message["content"].replace("$", "\\$")
                    with st.chat_message(message["role"]):
                        if message["role"] == "user":
                            st.markdown(f"**{message['content']}**")
                        else:
                            st.markdown(message["content"])


class StreamlitCallbackHandler(BaseCallbackHandler):
    def __init__(self, status_container):
        self.status_container = status_container

    def on_identify_perspective_start(self, **kwargs):
        self.status_container.info(
            "Start identifying different perspectives for researching the topic."
        )

    def on_identify_perspective_end(self, perspectives: list[str], **kwargs):
        perspective_list = "\n- ".join(perspectives)
        self.status_container.success(
            f"Finish identifying perspectives. Will now start gathering information"
            f" from the following perspectives:\n- {perspective_list}"
        )

    def on_information_gathering_start(self, **kwargs):
        self.status_container.info("Start browsing the Internet.")

    def on_dialogue_turn_end(self, dlg_turn, **kwargs):
        urls = list(set([r.url for r in dlg_turn.search_results]))
        for url in urls:
            self.status_container.markdown(
                f"""
                    <style>
                    .small-font {{
                        font-size: 14px;
                        margin: 0px;
                        padding: 0px;
                    }}
                    </style>
                    <div class="small-font">Finish browsing <a href="{url}" class="small-font" target="_blank">{url}</a>.</div>
                    """,
                unsafe_allow_html=True,
            )

    def on_information_gathering_end(self, **kwargs):
        self.status_container.success("Finish collecting information.")

    def on_information_organization_start(self, **kwargs):
        self.status_container.info(
            "Start organizing information into a hierarchical outline."
        )

    def on_direct_outline_generation_end(self, outline: str, **kwargs):
        self.status_container.success(
            f"Finish leveraging the internal knowledge of the large language model."
        )

    def on_outline_refinement_end(self, outline: str, **kwargs):
        self.status_container.success(f"Finish leveraging the collected information.")
