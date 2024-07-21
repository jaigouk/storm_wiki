import streamlit as st
import os
from dotenv import load_dotenv

import phoenix as px
from phoenix.trace.openai import OpenAIInstrumentor
from openinference.semconv.resource import ResourceAttributes
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

import demo_util
from pages_util import MyArticles, CreateNewArticle
from streamlit_float import *
from streamlit_option_menu import option_menu

load_dotenv()

# Set page config first
st.set_page_config(layout="wide")

# Custom CSS to change the progress bar color
progress_bar_color = """
<style>
    .stProgress > div > div > div > div {
        background-color: #bd93f9;
    }
</style>
"""

# Inject custom CSS
st.markdown(progress_bar_color, unsafe_allow_html=True)

# Custom CSS to hide the progress bar
hide_progress_bar = """
<style>
    /* Hide the progress bar */
    .stProgress {
        display: none !important;
    }
    /* Hide the loading spinner */
    .stSpinner {
        display: none !important;
    }
    /* Hide any other loading indicators */
    .st-emotion-cache-1dp5vir {
        display: none !important;
    }
</style>
"""

# Inject custom CSS
st.markdown(hide_progress_bar, unsafe_allow_html=True)

script_dir = os.path.dirname(os.path.abspath(__file__))
wiki_root_dir = os.path.dirname(os.path.dirname(script_dir))


def main():
    global database

    if "first_run" not in st.session_state:
        st.session_state["first_run"] = True

    # set api keys from secrets
    if st.session_state["first_run"]:
        for key, value in st.secrets.items():
            if type(value) == str:
                os.environ[key] = value

    # initialize session_state
    if "selected_article_index" not in st.session_state:
        st.session_state["selected_article_index"] = 0
    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = 0
    if st.session_state.get("rerun_requested", False):
        st.session_state["rerun_requested"] = False
        st.rerun()

    st.write(
        "<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True
    )
    menu_container = st.container()
    with menu_container:
        pages = ["My Articles", "Create New Article"]
        menu_selection = option_menu(
            None,
            pages,
            icons=["house", "pencil-square"],  # Changed 'search' to 'pencil-square'
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            manual_select=st.session_state.selected_page,
            styles={
                "container": {"padding": "0.2rem 0", "background-color": "#22222200"},
            },
            key="menu_selection",
        )

        if st.session_state.get("manual_selection_override", False):
            menu_selection = pages[st.session_state["selected_page"]]
            st.session_state["manual_selection_override"] = False
            st.session_state["selected_page"] = None

        if menu_selection == "My Articles":
            demo_util.clear_other_page_session_state(page_index=2)
            MyArticles.my_articles_page()
        elif menu_selection == "Create New Article":
            demo_util.clear_other_page_session_state(page_index=3)
            CreateNewArticle.create_new_article_page()


if __name__ == "__main__":
    resource = Resource(attributes={ResourceAttributes.PROJECT_NAME: "storm-wiki"})
    tracer_provider = trace_sdk.TracerProvider(resource=resource)

    phoenix_collector_endpoint = os.getenv(
        "PHOENIX_COLLECTOR_ENDPOINT", "localhost:6006"
    )
    span_exporter = OTLPSpanExporter(
        endpoint=f"http://{phoenix_collector_endpoint}/v1/traces"
    )
    span_processor = SimpleSpanProcessor(span_exporter=span_exporter)
    tracer_provider.add_span_processor(span_processor=span_processor)
    trace_api.set_tracer_provider(tracer_provider=tracer_provider)

    OpenAIInstrumentor().instrument()

    main()
