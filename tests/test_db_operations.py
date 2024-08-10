import pytest
import os
from db.db_operations import (
    DB_PATH,
    init_db,
    save_setting,
    load_setting,
    load_search_options,
    save_search_options,
    update_search_option,
    load_llm_settings,
    save_llm_settings,
)


@pytest.fixture(scope="function")
def test_db():
    # Use a temporary database for testing
    test_db_path = "test_settings.db"
    original_db_path = DB_PATH

    # Temporarily change the DB_PATH
    globals()["DB_PATH"] = test_db_path

    init_db()

    yield

    # Clean up: remove the test database and restore the original DB_PATH
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    globals()["DB_PATH"] = original_db_path


def test_save_and_load_setting(test_db):
    key = "test_key"
    value = {"test": "value"}
    save_setting(key, value)
    loaded_value = load_setting(key)
    assert loaded_value == value


def test_load_setting_default(test_db):
    key = "non_existent_key"
    default_value = "default"
    loaded_value = load_setting(key, default_value)
    assert loaded_value == default_value


def test_save_and_load_search_options(test_db):
    options = {
        "primary_engine": "test_engine",
        "fallback_engine": "fallback_engine",
        "search_top_k": 5,
        "retrieve_top_k": 3,
        "engine_settings": {"test_engine": {"api_key": "test_key"}},
    }
    save_search_options(options)
    loaded_options = load_search_options()
    assert loaded_options == options


def test_update_search_option_top_level(test_db):
    # Set initial search options
    initial_options = load_search_options()

    # Update a top-level option
    update_search_option("primary_engine", "bing")

    # Load and check the updated options
    updated_options = load_search_options()
    assert updated_options["primary_engine"] == "bing"
    assert updated_options != initial_options


def test_update_search_option_nested(test_db):
    # Set initial search options
    initial_options = load_search_options()

    # Update a nested option
    update_search_option("engine_settings.searxng.base_url", "https://example.com")

    # Load and check the updated options
    updated_options = load_search_options()
    assert (
        updated_options["engine_settings"]["searxng"]["base_url"]
        == "https://example.com"
    )
    assert updated_options != initial_options


def test_update_search_option_new_nested(test_db):
    # Set initial search options
    initial_options = load_search_options()

    # Update a new nested option
    update_search_option("engine_settings.new_engine.api_key", "new_key")

    # Load and check the updated options
    updated_options = load_search_options()
    assert updated_options["engine_settings"]["new_engine"]["api_key"] == "new_key"
    assert updated_options != initial_options


def test_update_search_option_invalid_key(test_db):
    with pytest.raises(ValueError):
        update_search_option("invalid.key.format.too.many.levels", "value")


def test_update_search_option_numeric(test_db):
    update_search_option("search_top_k", 10)
    updated_options = load_search_options()
    assert updated_options["search_top_k"] == 10


def test_update_search_option_boolean(test_db):
    # Assuming we have a boolean option, if not, we can add one
    update_search_option("use_cache", True)
    updated_options = load_search_options()
    assert updated_options["use_cache"] == True


def test_update_search_option_missing_engine_settings(test_db):
    # First, remove the engine_settings key
    options = load_search_options()
    del options["engine_settings"]
    save_search_options(options)

    # Now update a nested option
    update_search_option("engine_settings.new_engine.api_key", "new_key")

    # Load and check the updated options
    updated_options = load_search_options()
    assert updated_options["engine_settings"]["new_engine"]["api_key"] == "new_key"


def test_load_search_options_default(test_db):
    # First, ensure no search options are saved
    save_setting("search_options", None)

    default_options = load_search_options()
    assert default_options["primary_engine"] == "duckduckgo"
    assert default_options["fallback_engine"] is None
    assert default_options["search_top_k"] == 3
    assert default_options["retrieve_top_k"] == 3
    assert "searxng" in default_options["engine_settings"]
    assert "bing" in default_options["engine_settings"]
    assert "yourdm" in default_options["engine_settings"]


def test_save_and_load_llm_settings(test_db):
    settings = {
        "primary_model": "test_model",
        "fallback_model": "fallback_model",
        "model_settings": {
            "test_model": {"model": "test_model_name", "max_tokens": 1000}
        },
    }
    save_llm_settings(settings)
    loaded_settings = load_llm_settings()

    # Check that all saved settings are present in loaded settings
    assert loaded_settings["primary_model"] == settings["primary_model"]
    assert loaded_settings["fallback_model"] == settings["fallback_model"]
    assert (
        loaded_settings["model_settings"]["test_model"]
        == settings["model_settings"]["test_model"]
    )

    # Check that default settings are also present
    assert "ollama" in loaded_settings["model_settings"]
    assert "openai" in loaded_settings["model_settings"]
    assert "anthropic" in loaded_settings["model_settings"]

    # Optional: Check specific default values
    assert (
        loaded_settings["model_settings"]["ollama"]["model"]
        == "jaigouk/hermes-2-theta-llama-3:latest"
    )
    assert loaded_settings["model_settings"]["openai"]["max_tokens"] == 500
    assert (
        loaded_settings["model_settings"]["anthropic"]["model"]
        == "claude-3-haiku-20240307"
    )


def test_load_llm_settings_default(test_db):
    # First, ensure no LLM settings are saved
    save_setting("llm_settings", None)

    default_settings = load_llm_settings()
    assert default_settings["primary_model"] == "ollama"
    assert default_settings["fallback_model"] is None
    assert "ollama" in default_settings["model_settings"]
    assert "openai" in default_settings["model_settings"]
    assert "anthropic" in default_settings["model_settings"]


def test_overwrite_setting(test_db):
    key = "overwrite_test"
    value1 = {"test": "value1"}
    value2 = {"test": "value2"}

    save_setting(key, value1)
    loaded_value1 = load_setting(key)
    assert loaded_value1 == value1

    save_setting(key, value2)
    loaded_value2 = load_setting(key)
    assert loaded_value2 == value2
