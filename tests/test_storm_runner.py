import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
import os
from util.storm_runner import (
    run_storm_with_fallback,
    add_examples_to_runner,
    set_storm_runner,
    clear_storm_session,
    get_storm_runner_status,
    run_storm_step,
    get_storm_output,
)


# Mock Streamlit's secrets
class MockSecrets(dict):
    def __getattr__(self, key):
        return self[key]


@pytest.fixture
def mock_secrets():
    return MockSecrets({"OPENAI_API_KEY": "test_key"})


@pytest.fixture
def mock_storm_runner():
    mock = MagicMock()
    mock.storm_knowledge_curation_module.persona_generator.create_writer_with_persona.find_related_topic = MagicMock()
    mock.storm_knowledge_curation_module.persona_generator.create_writer_with_persona.gen_persona = MagicMock()
    mock.storm_outline_generation_module.write_outline.write_page_outline = MagicMock()
    mock.storm_article_generation.section_gen.write_section = MagicMock()
    return mock


@pytest.fixture(autouse=True)
def mock_streamlit(monkeypatch, mock_secrets):
    monkeypatch.setattr(st, "secrets", mock_secrets)
    monkeypatch.setattr(st, "info", MagicMock())
    monkeypatch.setattr(st, "error", MagicMock())
    monkeypatch.setattr(st, "warning", MagicMock())


@patch("util.storm_runner.STORMWikiRunnerArguments")
@patch("util.storm_runner.STORMWikiLMConfigs")
@patch("util.storm_runner.DuckDuckGoAdapter")
@patch("util.storm_runner.OllamaClient")
@patch("util.storm_runner.OpenAIModel")
@patch("util.storm_runner.STORMWikiRunner")
def test_successful_run_with_ollama(
    mock_storm_runner_class,
    mock_openai,
    mock_ollama,
    mock_ddg,
    mock_llm_configs,
    mock_args,
    mock_storm_runner,
):
    mock_storm_runner_class.return_value = mock_storm_runner
    mock_ollama.return_value = MagicMock()
    mock_ddg.return_value = MagicMock()
    mock_llm_configs.return_value = MagicMock()

    result = run_storm_with_fallback("test topic", "/tmp/test_dir")

    assert result == mock_storm_runner
    mock_storm_runner.run.assert_called_once()
    mock_storm_runner.post_run.assert_called_once()
    mock_openai.assert_not_called()


@patch("util.storm_runner.STORMWikiRunnerArguments")
@patch("util.storm_runner.STORMWikiLMConfigs")
@patch("util.storm_runner.DuckDuckGoAdapter")
@patch("util.storm_runner.OllamaClient")
@patch("util.storm_runner.OpenAIModel")
@patch("util.storm_runner.STORMWikiRunner")
def test_ollama_failure_openai_success(
    mock_storm_runner_class,
    mock_openai,
    mock_ollama,
    mock_ddg,
    mock_llm_configs,
    mock_args,
    mock_storm_runner,
):
    mock_storm_runner_class.return_value = mock_storm_runner
    mock_ollama.side_effect = Exception("Ollama failed")
    mock_openai.return_value = MagicMock()
    mock_ddg.return_value = MagicMock()
    mock_llm_configs.return_value = MagicMock()

    # Set up the run method to succeed for OpenAI
    mock_storm_runner.run.return_value = None

    result = run_storm_with_fallback("test topic", "/tmp/test_dir")

    assert result == mock_storm_runner
    assert mock_storm_runner.run.call_count == 1  # Only called for OpenAI
    mock_storm_runner.post_run.assert_called_once()


@patch("util.storm_runner.STORMWikiRunnerArguments")
@patch("util.storm_runner.STORMWikiLMConfigs")
@patch("util.storm_runner.DuckDuckGoAdapter")
@patch("util.storm_runner.OllamaClient")
@patch("util.storm_runner.OpenAIModel")
@patch("util.storm_runner.STORMWikiRunner")
def test_both_models_fail(
    mock_storm_runner_class,
    mock_openai,
    mock_ollama,
    mock_ddg,
    mock_llm_configs,
    mock_args,
    mock_storm_runner,
):
    mock_storm_runner_class.return_value = mock_storm_runner
    mock_ollama.side_effect = Exception("Ollama failed")
    mock_openai.return_value = MagicMock()
    mock_ddg.return_value = MagicMock()
    mock_llm_configs.return_value = MagicMock()

    # Set up the run method to fail for both Ollama and OpenAI
    mock_storm_runner.run.side_effect = Exception("Model failed")

    result = run_storm_with_fallback("test topic", "/tmp/test_dir")

    assert result is None
    # Only called once (for OpenAI)
    assert mock_storm_runner.run.call_count == 1
    mock_storm_runner.post_run.assert_not_called()


def test_set_storm_runner(monkeypatch, tmp_path):
    mock_makedirs = MagicMock()
    mock_convert_txt_to_md = MagicMock()
    mock_getenv = MagicMock(return_value=str(tmp_path))

    monkeypatch.setattr(os, "makedirs", mock_makedirs)
    monkeypatch.setattr(
        "util.storm_runner.convert_txt_to_md",
        mock_convert_txt_to_md)
    monkeypatch.setattr(os, "getenv", mock_getenv)
    monkeypatch.setattr(
        os.path, "exists", lambda x: False
    )  # Simulate directory not existing

    set_storm_runner()

    assert "run_storm" in st.session_state
    assert callable(st.session_state["run_storm"])
    mock_makedirs.assert_called_once_with(str(tmp_path))
    mock_convert_txt_to_md.assert_called_once_with(str(tmp_path))
    mock_getenv.assert_called_once_with("STREAMLIT_OUTPUT_DIR")


def test_clear_storm_session():
    st.session_state["run_storm"] = MagicMock()
    st.session_state["runner"] = MagicMock()

    clear_storm_session()

    assert "run_storm" not in st.session_state
    assert "runner" not in st.session_state


@pytest.mark.parametrize(
    "runner_status, expected_status",
    [
        (None, "Not initialized"),
        (MagicMock(), "Ready"),
    ],
)
def test_get_storm_runner_status(runner_status, expected_status):
    if runner_status is None:
        st.session_state.pop("runner", None)
    else:
        st.session_state["runner"] = runner_status

    assert get_storm_runner_status() == expected_status


def test_run_storm_step_success():
    mock_runner = MagicMock()
    st.session_state["runner"] = mock_runner

    result = run_storm_step("research", "test topic")

    assert result is True
    mock_runner.run.assert_called_once_with(
        topic="test topic", do_research=True)


def test_run_storm_step_failure():
    mock_runner = MagicMock()
    mock_runner.run.side_effect = Exception("Test error")
    st.session_state["runner"] = mock_runner

    result = run_storm_step("research", "test topic")

    assert result is False


def test_run_storm_step_invalid_step():
    st.session_state["runner"] = MagicMock()

    result = run_storm_step("invalid_step", "test topic")

    assert result is False


def test_get_storm_output_success(tmp_path):
    mock_runner = MagicMock()
    mock_runner.engine_args.output_dir = tmp_path
    st.session_state["runner"] = mock_runner

    output_file = tmp_path / "outline.txt"
    output_file.write_text("Test outline")

    result = get_storm_output("outline")

    assert result == "Test outline"


def test_get_storm_output_file_not_found():
    mock_runner = MagicMock()
    mock_runner.engine_args.output_dir = "/nonexistent/path"
    st.session_state["runner"] = mock_runner

    result = get_storm_output("outline")

    assert result is None


def test_get_storm_output_invalid_type():
    st.session_state["runner"] = MagicMock()

    result = get_storm_output("invalid_type")

    assert result is None
