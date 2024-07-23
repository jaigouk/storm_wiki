import os
import time
import streamlit as st
from demo_util import (
    DemoFileIOHelper,
    DemoTextProcessingHelper,
    DemoUIHelper,
    get_demo_dir,
    get_output_dir,
    set_storm_runner,
    StreamlitCallbackHandler,
    display_article_page,
    convert_txt_to_md,
)


def apply_custom_css():
    st.markdown(
        """
    <style>
    /* Remove top line */
    header {
        background: none !important;
    }

    /* Adjust card styling */
    .stTileButton {
        background-color: #44475a !important;
        color: #f8f8f2 !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Remove green line on cards */
    .stTileButton::before {
        display: none !important;
    }

    /* Adjust other elements */
    .stApp {
        background-color: #282a36;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #44475a;
        color: #f8f8f2;
        border: 1px solid #6272a4;
    }
    .stButton > button {
        background-color: #6272a4;
        color: #f8f8f2;
    }
    .stButton > button:hover {
        background-color: #bd93f9;
    }
    /* Adjust dropdown menu */
    .stSelectbox > div > div {
        background-color: #44475a;
        color: #f8f8f2;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def create_new_article_page():
    apply_custom_css()

    st.markdown(
        "<h1 style='text-align: center; color: white;'>Create a New Article</h1>",
        unsafe_allow_html=True,
    )

    if "page3_write_article_state" not in st.session_state:
        st.session_state["page3_write_article_state"] = "not started"

    if st.session_state["page3_write_article_state"] == "not started":
        _, search_form_column, _ = st.columns([1, 3, 1])
        with search_form_column:
            with st.form(key="search_form"):
                st.text_input(
                    "Enter the topic",
                    key="page3_topic",
                    placeholder="Enter the topic",
                    help="Enter the main topic or question for your article",
                )

                st.text_area(
                    "Elaborate on the purpose",
                    key="page3_purpose",
                    placeholder="Please type here to elaborate on the purpose of writing this article",
                    help="Provide more context or specific areas you want to explore",
                    height=100,
                )

                submit_button = st.form_submit_button(
                    label="Research",
                    help="Start researching the topic",
                    use_container_width=True,
                )

                if submit_button:
                    if not st.session_state["page3_topic"].strip():
                        st.warning("Topic could not be empty", icon="⚠️")
                    else:
                        st.session_state["page3_topic_name_cleaned"] = (
                            st.session_state["page3_topic"]
                            .replace(" ", "_")
                            .replace("/", "_")
                        )
                        st.session_state["page3_write_article_state"] = "initiated"
                        st.rerun()

    if st.session_state["page3_write_article_state"] == "initiated":
        current_working_dir = get_output_dir()
        if not os.path.exists(current_working_dir):
            os.makedirs(current_working_dir)

        if "run_storm" not in st.session_state:
            set_storm_runner()
        st.session_state["page3_current_working_dir"] = current_working_dir
        st.session_state["page3_write_article_state"] = "pre_writing"

    if st.session_state["page3_write_article_state"] == "pre_writing":
        status = st.status(
            "I am brain**STORM**ing now to research the topic. (This may take several minutes.)"
        )
        progress_bar = st.progress(0)
        progress_text = st.empty()

        class ProgressCallback(StreamlitCallbackHandler):
            def __init__(self, progress_bar, progress_text):
                self.progress_bar = progress_bar
                self.progress_text = progress_text
                self.steps = ["research", "outline", "article", "polish"]
                self.current_step = 0

            def on_information_gathering_start(self, **kwargs):
                self.progress_text.text(
                    kwargs.get(
                        "message",
                        f"Step {self.current_step + 1}/{len(self.steps)}: {self.steps[self.current_step]}",
                    )
                )
                self.progress_bar.progress((self.current_step + 1) / len(self.steps))
                self.current_step = min(self.current_step + 1, len(self.steps) - 1)

        callback = ProgressCallback(progress_bar, progress_text)

        with status:
            # Run STORM with fallback
            runner = st.session_state["run_storm"](
                st.session_state["page3_topic"],
                st.session_state["page3_current_working_dir"],
                callback_handler=callback,
            )
            if runner:
                conversation_log_path = os.path.join(
                    st.session_state["page3_current_working_dir"],
                    st.session_state["page3_topic_name_cleaned"],
                    "conversation_log.json",
                )
                if os.path.exists(conversation_log_path):
                    DemoUIHelper.display_persona_conversations(
                        DemoFileIOHelper.read_json_file(conversation_log_path)
                    )
                st.session_state["page3_write_article_state"] = "final_writing"
                status.update(label="brain**STORM**ing complete!", state="complete")
                progress_bar.progress(100)

                # Store the runner in the session state
                st.session_state["runner"] = runner
            else:
                st.error("Failed to generate the article.")
                st.session_state["page3_write_article_state"] = "not started"
                return  # Exit the function early if runner is None

    if st.session_state["page3_write_article_state"] == "final_writing":
        # Check if runner exists in the session state
        if "runner" not in st.session_state or st.session_state["runner"] is None:
            st.error("Article generation failed. Please try again.")
            st.session_state["page3_write_article_state"] = "not started"
            return

        with st.status(
            "Now I will connect the information I found for your reference. (This may take 4-5 minutes.)"
        ) as status:
            st.info(
                "Now I will connect the information I found for your reference. (This may take 4-5 minutes.)"
            )
            try:
                st.session_state["runner"].run(
                    topic=st.session_state["page3_topic"],
                    do_research=False,
                    do_generate_outline=False,
                    do_generate_article=True,
                    do_polish_article=True,
                    remove_duplicate=False,
                )
                # finish the session
                st.session_state["runner"].post_run()

                # Convert txt files to md after article generation
                convert_txt_to_md(st.session_state["page3_current_working_dir"])

                # update status bar
                st.session_state["page3_write_article_state"] = "prepare_to_show_result"
                status.update(label="information synthesis complete!", state="complete")
            except Exception as e:
                st.error(f"Error during final article generation: {str(e)}")
                st.session_state["page3_write_article_state"] = "not started"

    if st.session_state["page3_write_article_state"] == "final_writing":
        # polish final article
        with st.status(
            "Now I will connect the information I found for your reference. (This may take 4-5 minutes.)"
        ) as status:
            st.info(
                "Now I will connect the information I found for your reference. (This may take 4-5 minutes.)"
            )
            st.session_state["runner"].run(
                topic=st.session_state["page3_topic"],
                do_research=False,
                do_generate_outline=False,
                do_generate_article=True,
                do_polish_article=True,
                remove_duplicate=False,
            )
            # finish the session
            st.session_state["runner"].post_run()

            # Convert txt files to md after article generation
            convert_txt_to_md(st.session_state["page3_current_working_dir"])

            # update status bar
            st.session_state["page3_write_article_state"] = "prepare_to_show_result"
            status.update(label="information synthesis complete!", state="complete")

    if st.session_state["page3_write_article_state"] == "prepare_to_show_result":
        _, show_result_col, _ = st.columns([4, 3, 4])
        with show_result_col:
            if st.button("Show final article"):
                st.session_state["page3_write_article_state"] = "completed"
                st.rerun()

    if st.session_state["page3_write_article_state"] == "completed":
        # display polished article
        current_working_dir_paths = DemoFileIOHelper.read_structure_to_dict(
            st.session_state["page3_current_working_dir"]
        )
        current_article_file_path_dict = current_working_dir_paths[
            st.session_state["page3_topic_name_cleaned"]
        ]
        display_article_page(
            selected_article_name=st.session_state["page3_topic_name_cleaned"],
            selected_article_file_path_dict=current_article_file_path_dict,
            show_title=True,
            show_main_article=True,
        )
