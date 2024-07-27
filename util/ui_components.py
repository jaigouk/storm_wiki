import streamlit as st
from .file_io import DemoFileIOHelper
from .text_processing import DemoTextProcessingHelper
from util.theme_manager import load_and_apply_theme, get_contrasting_text_color
from streamlit_card import card
import os
import markdown
from knowledge_storm.storm_wiki.modules.callback import BaseCallbackHandler
import re
import unidecode


class UIComponents:
    @staticmethod
    def display_article_page(
        selected_article_name,
        selected_article_file_path_dict,
        show_title=True,
        show_main_article=True,
        show_feedback_form=False,
        show_qa_panel=False,
    ):
        try:
            current_theme = st.session_state.current_theme
            if show_title:
                st.markdown(
                    f"<h2 style='text-align: center; color: {current_theme['textColor']};'>{selected_article_name.replace('_', ' ')}</h2>",
                    unsafe_allow_html=True,
                )

            if show_main_article:
                article_data = DemoFileIOHelper.assemble_article_data(
                    selected_article_file_path_dict
                )

                if article_data is None:
                    st.warning("No article data found.")
                    return

                UIComponents.display_main_article(
                    article_data, show_feedback_form, show_qa_panel
                )
        except Exception as e:
            st.error(f"Error displaying article: {str(e)}")
            st.exception(e)

    @staticmethod
    def display_main_article(
        article_data, show_feedback_form=False, show_qa_panel=False
    ):
        try:
            current_theme = st.session_state.current_theme
            with st.container(height=1000, border=True):
                table_content_sidebar = st.sidebar.expander(
                    "**Table of contents**", expanded=True
                )
                st.markdown(
                    f"""
                    <style>
                    [data-testid="stExpander"] {{
                        border-color: {current_theme['primaryColor']} !important;
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                UIComponents.display_main_article_text(
                    article_text=article_data.get("article", ""),
                    citation_dict=article_data.get("citations", {}),
                    table_content_sidebar=table_content_sidebar,
                )

            # display reference panel
            if "citations" in article_data:
                with st.sidebar.expander("**References**", expanded=True):
                    with st.container(height=800, border=False):
                        UIComponents._display_references(
                            citation_dict=article_data.get("citations", {})
                        )

            # display conversation history
            if "conversation_log" in article_data:
                with st.expander(
                    "**STORM** is powered by a knowledge agent that proactively research a given topic by asking good questions coming from different perspectives.\n\n"
                    ":sunglasses: Click here to view the agent's brain**STORM**ing process!"
                ):
                    UIComponents.display_persona_conversations(
                        conversation_log=article_data.get("conversation_log", {})
                    )

            # Add placeholders for feedback form and QA panel if needed
            if show_feedback_form:
                st.write("Feedback form placeholder")

            if show_qa_panel:
                st.write("QA panel placeholder")

        except Exception as e:
            st.error(f"Error in display_main_article: {str(e)}")
            st.exception(e)

    @staticmethod
    def _display_references(citation_dict):
        if citation_dict:
            reference_list = [
                f"reference [{i}]" for i in range(1, len(citation_dict) + 1)
            ]
            selected_key = st.selectbox("Select a reference", reference_list)
            citation_val = citation_dict[reference_list.index(selected_key) + 1]
            citation_val["title"] = citation_val["title"].replace("$", "\\$")
            st.markdown(f"**Title:** {citation_val['title']}")
            st.markdown(f"**Url:** {citation_val['url']}")
            snippets = "\n\n".join(citation_val["snippets"]).replace("$", "\\$")
            st.markdown(f"**Highlights:**\n\n {snippets}")
        else:
            st.markdown("**No references available**")

    @staticmethod
    def display_main_article_text(article_text, citation_dict, table_content_sidebar):
        # Post-process the generated article for better display.
        if "Write the lead section:" in article_text:
            article_text = article_text[
                article_text.find("Write the lead section:")
                + len("Write the lead section:") :
            ]
        if article_text[0] == "#":
            article_text = "\n".join(article_text.split("\n")[1:])
        article_text = DemoTextProcessingHelper.add_inline_citation_link(
            article_text, citation_dict
        )
        # '$' needs to be changed to '\$' to avoid being interpreted as LaTeX in st.markdown()
        article_text = article_text.replace("$", "\\$")
        UIComponents.from_markdown(article_text, table_content_sidebar)

    @staticmethod
    def get_article_card_style(current_theme):
        contrast_color = get_contrasting_text_color(
            current_theme["secondaryBackgroundColor"]
        )
        return {
            "card": {
                "width": "100%",
                "height": "116px",
                "padding": "10px",
                "border-radius": "5px",
                "box-shadow": f"0 4px 6px 0 {current_theme['primaryColor']}33",
                "margin": "0px",
                "background-color": current_theme["secondaryBackgroundColor"],
                "border": f"1px solid {current_theme['primaryColor']}",
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
                "color": contrast_color,
            },
        }

    @staticmethod
    def create_article_card(article_name, current_theme):
        cleaned_article_title = article_name.replace("_", " ")
        card_style = UIComponents.get_article_card_style(current_theme)
        card_style["card"]["border"] = (
            f"1px solid {get_contrasting_text_color(current_theme['secondaryBackgroundColor'])}"
        )
        return card(
            title="",
            text=cleaned_article_title,
            image=DemoFileIOHelper.read_image_as_base64(
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "assets", "void.jpg"
                )
            ),
            styles=card_style,
        )

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

    # STOC functionality
    @staticmethod
    def from_markdown(text: str, expander=None):
        toc_items = []
        for line in text.splitlines():
            if line.startswith("###"):
                toc_items.append(("h3", line[3:]))
            elif line.startswith("##"):
                toc_items.append(("h2", line[2:]))
            elif line.startswith("#"):
                toc_items.append(("h1", line[1:]))

        # customize markdown font size
        custom_css = """
        <style>
            /* Adjust the font size for headings */
            h1 { font-size: 28px; }
            h2 { font-size: 24px; }
            h3 { font-size: 22px; }
            h4 { font-size: 20px; }
            h5 { font-size: 18px; }
            /* Adjust the font size for normal text */
            p { font-size: 18px; }
        </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)

        st.write(text)
        UIComponents.toc(toc_items, expander)

    @staticmethod
    def toc(toc_items, expander):
        st.write(UIComponents.DISABLE_LINK_CSS, unsafe_allow_html=True)
        if expander is None:
            expander = st.sidebar.expander("**Table of contents**", expanded=True)
        with expander:
            with st.container(height=600, border=False):
                markdown_toc = ""
                for title_size, title in toc_items:
                    h = int(title_size.replace("h", ""))
                    markdown_toc += (
                        " " * 2 * h
                        + "- "
                        + f'<a href="#{UIComponents.normalize(title)}" class="toc"> {title}</a> \n'
                    )
                st.write(markdown_toc, unsafe_allow_html=True)

    @staticmethod
    def normalize(s):
        s_wo_accents = unidecode.unidecode(s)
        accents = [s for s in s if s not in s_wo_accents]
        for accent in accents:
            s = s.replace(accent, "-")
        s = s.lower()
        normalized = (
            "".join([char if char.isalnum() else "-" for char in s]).strip("-").lower()
        )
        return normalized

    DISABLE_LINK_CSS = """
    <style>
    a.toc {
        color: inherit;
        text-decoration: none; /* no underline */
    }
    </style>"""


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
