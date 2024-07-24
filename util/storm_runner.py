import os
import time
import streamlit as st
from typing import Optional
import logging
from dspy import Example

from knowledge_storm import (
    STORMWikiRunnerArguments,
    STORMWikiRunner,
    STORMWikiLMConfigs,
)
from knowledge_storm.lm import OpenAIModel, OllamaClient
from .search import DuckDuckGoAdapter
from .artifact_helpers import convert_txt_to_md


def add_examples_to_runner(runner):
    find_related_topic_example = Example(
        topic="Knowledge Curation",
        related_topics="https://en.wikipedia.org/wiki/Knowledge_management\n"
        "https://en.wikipedia.org/wiki/Information_science\n"
        "https://en.wikipedia.org/wiki/Library_science\n",
    )
    gen_persona_example = Example(
        topic="Knowledge Curation",
        examples="Title: Knowledge management\n"
        "Table of Contents: History\nResearch\n  Dimensions\n  Strategies\n  Motivations\nKM technologies"
        "\nKnowledge barriers\nKnowledge retention\nKnowledge audit\nKnowledge protection\n"
        "  Knowledge protection methods\n    Formal methods\n    Informal methods\n"
        "  Balancing knowledge protection and knowledge sharing\n  Knowledge protection risks",
        personas="1. Historian of Knowledge Systems: This editor will focus on the history and evolution of knowledge curation. They will provide context on how knowledge curation has changed over time and its impact on modern practices.\n"
        "2. Information Science Professional: With insights from 'Information science', this editor will explore the foundational theories, definitions, and philosophy that underpin knowledge curation\n"
        "3. Digital Librarian: This editor will delve into the specifics of how digital libraries operate, including software, metadata, digital preservation.\n"
        "4. Technical expert: This editor will focus on the technical aspects of knowledge curation, such as common features of content management systems.\n"
        "5. Museum Curator: The museum curator will contribute expertise on the curation of physical items and the transition of these practices into the digital realm.",
    )
    write_page_outline_example = Example(
        topic="Example Topic",
        conv="Wikipedia Writer: ...\nExpert: ...\nWikipedia Writer: ...\nExpert: ...",
        old_outline="# Section 1\n## Subsection 1\n## Subsection 2\n"
        "# Section 2\n## Subsection 1\n## Subsection 2\n"
        "# Section 3",
        outline="# New Section 1\n## New Subsection 1\n## New Subsection 2\n"
        "# New Section 2\n"
        "# New Section 3\n## New Subsection 1\n## New Subsection 2\n## New Subsection 3",
    )
    write_section_example = Example(
        info="[1]\nInformation in document 1\n[2]\nInformation in document 2\n[3]\nInformation in document 3",
        topic="Example Topic",
        section="Example Section",
        output="# Example Topic\n## Subsection 1\n"
        "This is an example sentence [1]. This is another example sentence [2][3].\n"
        "## Subsection 2\nThis is one more example sentence [1].",
    )

    runner.storm_knowledge_curation_module.persona_generator.create_writer_with_persona.find_related_topic.demos = [
        find_related_topic_example]
    runner.storm_knowledge_curation_module.persona_generator.create_writer_with_persona.gen_persona.demos = [
        gen_persona_example]
    runner.storm_outline_generation_module.write_outline.write_page_outline.demos = [
        write_page_outline_example]
    runner.storm_article_generation.section_gen.write_section.demos = [
        write_section_example
    ]


def run_storm_with_fallback(topic, current_working_dir, callback_handler=None):
    def log_progress(message):
        st.info(message)
        logging.info(message)
        if callback_handler:
            callback_handler.on_information_gathering_start(message=message)

    log_progress("Initializing language models...")
    llm_configs = STORMWikiLMConfigs()

    engine_args = STORMWikiRunnerArguments(
        output_dir=current_working_dir,
        max_conv_turn=3,
        max_perspective=3,
        search_top_k=3,
        retrieve_top_k=5,
    )

    log_progress("Setting up search engine...")
    rm = DuckDuckGoAdapter(k=engine_args.search_top_k)

    # Try Ollama first
    try:
        log_progress("Starting STORM process with Ollama...")
        ollama_kwargs = {
            "model": "jaigouk/hermes-2-theta-llama-3:latest",
            "url": "http://localhost",
            "port": 11434,
            "stop": ("\n\n---",),
        }

        for lm_type in [
            "conv_simulator",
            "question_asker",
            "outline_gen",
            "article_gen",
            "article_polish",
        ]:
            max_tokens = 4000 if lm_type == "article_polish" else 500
            lm = OllamaClient(max_tokens=max_tokens, **ollama_kwargs)
            getattr(llm_configs, f"set_{lm_type}_lm")(lm)

        runner = STORMWikiRunner(engine_args, llm_configs, rm)
        add_examples_to_runner(runner)

        start_time = time.time()
        result = runner.run(
            topic=topic,
            do_research=True,
            do_generate_outline=True,
            do_generate_article=True,
            do_polish_article=True,
        )
        end_time = time.time()

        log_progress(
            f"Ollama STORM process completed in {end_time - start_time:.2f} seconds."
        )
        runner.post_run()
        return runner

    except Exception as e:
        logging.error(
            f"Error during Ollama-based generation: {str(e)}",
            exc_info=True)
        st.warning("Ollama process failed. Falling back to OpenAI...")

        # Fallback to OpenAI
        try:
            log_progress("Starting OpenAI fallback process...")
            llm_configs = STORMWikiLMConfigs()
            llm_configs.init_openai_model(
                openai_api_key=st.secrets["OPENAI_API_KEY"],
                openai_type="openai",
            )

            openai_model = OpenAIModel(
                model="gpt-4o-mini-2024-07-18",
                api_key=st.secrets["OPENAI_API_KEY"],
                api_provider="openai",
                max_tokens=2000,
                temperature=0.3,
                top_p=0.9,
            )

            for lm_type in [
                "conv_simulator",
                "question_asker",
                "outline_gen",
                "article_gen",
                "article_polish",
            ]:
                getattr(llm_configs, f"set_{lm_type}_lm")(openai_model)

            runner = STORMWikiRunner(engine_args, llm_configs, rm)
            add_examples_to_runner(runner)

            start_time = time.time()
            runner.run(
                topic=topic,
                do_research=True,
                do_generate_outline=True,
                do_generate_article=True,
                do_polish_article=True,
            )
            end_time = time.time()

            log_progress(
                f"OpenAI fallback process completed in {end_time - start_time:.2f} seconds."
            )
            runner.post_run()
            return runner

        except Exception as e:
            st.error(f"Error during OpenAI fallback: {str(e)}")
            logging.error(
                f"Error during OpenAI fallback: {str(e)}",
                exc_info=True)
            return None


def set_storm_runner():
    current_working_dir = os.getenv("STREAMLIT_OUTPUT_DIR")
    if not current_working_dir:
        current_working_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "DEMO_WORKING_DIR",
        )

    if not os.path.exists(current_working_dir):
        os.makedirs(current_working_dir)

    # Store the function itself in the session state
    st.session_state["run_storm"] = run_storm_with_fallback

    # Convert existing txt files to md
    convert_txt_to_md(current_working_dir)


def clear_storm_session():
    """
    Clears the STORM-related session state variables.
    """
    keys_to_clear = ["run_storm", "runner"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def get_storm_runner_status():
    """
    Returns the current status of the STORM runner.
    """
    if "runner" not in st.session_state:
        return "Not initialized"
    elif st.session_state["runner"] is None:
        return "Failed"
    else:
        return "Ready"


def run_storm_step(step: str, topic: str):
    """
    Runs a specific step of the STORM process.

    Args:
    step (str): The step to run ('research', 'outline', 'article', or 'polish')
    topic (str): The topic to process

    Returns:
    bool: True if the step was successful, False otherwise
    """
    if "runner" not in st.session_state or st.session_state["runner"] is None:
        st.error("STORM runner is not initialized. Please set up the runner first.")
        return False

    runner = st.session_state["runner"]
    step_config = {
        "research": {"do_research": True},
        "outline": {"do_generate_outline": True},
        "article": {"do_generate_article": True},
        "polish": {"do_polish_article": True},
    }

    if step not in step_config:
        st.error(f"Invalid step: {step}")
        return False

    try:
        runner.run(topic=topic, **step_config[step])
        return True
    except Exception as e:
        st.error(f"Error during {step} step: {str(e)}")
        return False


def get_storm_output(output_type: str) -> Optional[str]:
    """
    Retrieves a specific type of output from the STORM process.

    Args:
    output_type (str): The type of output to retrieve ('outline', 'article', or 'polished_article')

    Returns:
    Optional[str]: The requested output if available, None otherwise
    """
    if "runner" not in st.session_state or st.session_state["runner"] is None:
        st.error("STORM runner is not initialized. Please set up the runner first.")
        return None

    runner = st.session_state["runner"]
    output_file_map = {
        "outline": "outline.txt",
        "article": "storm_gen_article.md",
        "polished_article": "storm_gen_article_polished.md",
    }

    if output_type not in output_file_map:
        st.error(f"Invalid output type: {output_type}")
        return None

    output_file = output_file_map[output_type]
    output_path = os.path.join(runner.engine_args.output_dir, output_file)

    if not os.path.exists(output_path):
        st.warning(
            f"{output_type.capitalize()} not found. Make sure you've run the corresponding step."
        )
        return None

    with open(output_path, "r", encoding="utf-8") as f:
        return f.read()
