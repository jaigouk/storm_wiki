import streamlit as st
from streamlit_option_menu import option_menu
from util.theme_manager import (
    dark_themes,
    light_themes,
    get_theme_css,
    get_preview_html,
    load_and_apply_theme,
    save_theme,
)
import sqlite3
import json
import subprocess
from util.file_io import FileIOHelper
import shutil
import os

DB_PATH = os.environ.get("DB_PATH", "./data/settings.db")

SEARCH_ENGINES = {
    "searxng": {
        "env_var": "SEARXNG_BASE_URL",
        "settings": {
            "base_url": {"type": "text", "required": True, "label": "SearXNG Base URL"},
            "api_key": {
                "type": "password",
                "required": False,
                "label": "SearXNG API Key (optional)",
            },
        },
    },
    "bing": {
        "env_var": "BING_SEARCH_API_KEY",
        "settings": {
            "api_key": {"type": "password", "required": True, "label": "Bing API Key"},
        },
    },
    "yourdm": {
        "env_var": "YDC_API_KEY",
        "settings": {
            "api_key": {
                "type": "password",
                "required": True,
                "label": "YourDM API Key",
            },
        },
    },
    "duckduckgo": {"env_var": None, "settings": {}},
    "arxiv": {"env_var": None, "settings": {}},
}

# LLM model options
LLM_MODELS = {
    "ollama": "OLLAMA_PORT",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def load_output_dir():
    return FileIOHelper.load_output_base_dir()


def save_output_dir(output_dir):
    FileIOHelper.save_output_base_dir(output_dir)


def load_categories():
    return FileIOHelper.load_categories()


def save_categories(categories):
    FileIOHelper.save_categories(categories)


def load_general_settings():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='general_settings'")
    result = c.fetchone()
    conn.close()
    if result:
        return json.loads(result[0])
    return {"num_columns": 3}


def save_general_settings(settings):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ("general_settings", json.dumps(settings)),
    )
    conn.commit()
    conn.close()


def load_phoenix_settings():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='phoenix_settings'")
    result = c.fetchone()
    conn.close()
    if result:
        return json.loads(result[0])
    return {
        "project_name": "storm-wiki",
        "enabled": False,
        "collector_endpoint": "localhost:6006",
    }


def save_phoenix_settings(settings):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ("phoenix_settings", json.dumps(settings)),
    )
    conn.commit()
    conn.close()


def get_engine_specific_settings(engine, current_settings={}):
    settings = {}
    if engine in SEARCH_ENGINES and "settings" in SEARCH_ENGINES[engine]:
        for key, config in SEARCH_ENGINES[engine]["settings"].items():
            input_type = config.get("type", "text")
            if input_type == "text":
                settings[key] = st.text_input(
                    config["label"],
                    value=current_settings.get(key, ""),
                    key=f"{engine}_{key}",
                )
            elif input_type == "password":
                settings[key] = st.text_input(
                    config["label"],
                    value=current_settings.get(key, ""),
                    type="password",
                    key=f"{engine}_{key}",
                )
    return settings


def get_available_search_engines():
    available_engines = {}
    search_options = load_search_options()
    engine_settings = search_options.get("engine_settings", {})

    for engine, config in SEARCH_ENGINES.items():
        if config["env_var"] is None:
            available_engines[engine] = None
        elif engine in config.get("settings", {}):
            required_settings = [
                key
                for key, setting in config["settings"].items()
                if setting.get("required", False)
            ]
            if all(
                engine_settings.get(engine, {}).get(key) for key in required_settings
            ):
                available_engines[engine] = config["env_var"]
        elif config["env_var"] in st.secrets:
            available_engines[engine] = config["env_var"]

    if "searxng" in engine_settings and engine_settings["searxng"].get("base_url"):
        available_engines["searxng"] = SEARCH_ENGINES["searxng"]["env_var"]

    return available_engines


def load_search_options():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='search_options'")
    result = c.fetchone()
    conn.close()

    default_options = {
        "primary_engine": "duckduckgo",
        "fallback_engine": None,
        "search_top_k": 3,
        "retrieve_top_k": 3,
        "engine_settings": {
            "searxng": {"base_url": "", "api_key": ""},
            "bing": {"api_key": ""},
            "yourdm": {"api_key": ""},
        },
    }

    if result:
        stored_options = json.loads(result[0])
        default_options.update(stored_options)

    return default_options


def save_search_options(**options):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    existing_options = load_search_options()
    existing_options.update(options)
    c.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ("search_options", json.dumps(existing_options)),
    )
    conn.commit()
    conn.close()


def save_llm_settings(primary_model, fallback_model, model_settings):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (
            "llm_settings",
            json.dumps(
                {
                    "primary_model": primary_model,
                    "fallback_model": fallback_model,
                    "model_settings": model_settings,
                }
            ),
        ),
    )
    conn.commit()
    conn.close()


def load_llm_settings():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='llm_settings'")
    result = c.fetchone()
    conn.close()

    if result:
        return json.loads(result[0])
    return {
        "primary_model": "ollama",
        "fallback_model": None,
        "model_settings": {
            "ollama": {
                "model": "jaigouk/hermes-2-theta-llama-3:latest",
                "max_tokens": 500,
            },
            "openai": {"model": "gpt-4o-mini", "max_tokens": 500},
            "anthropic": {"model": "claude-3-haiku-202403072", "max_tokens": 500},
        },
    }


def list_downloaded_models():
    try:
        output = subprocess.check_output(["ollama", "list"], stderr=subprocess.STDOUT)
        models_list = []
        for line in output.decode("utf-8").splitlines():
            model_name = line.split()[0]
            models_list.append(model_name)
        return models_list
    except Exception as e:
        print(f"Error executing command: {e}")
        return []


def settings_page(selected_setting=None):
    current_theme = load_and_apply_theme()
    st.title("Settings")

    if selected_setting == "General":
        general_settings()
    elif selected_setting == "Theme":
        theme_settings()
    elif selected_setting == "Search":
        search_settings()
    elif selected_setting == "LLM":
        llm_settings()
    elif selected_setting == "Categories":
        category_settings()

    st.markdown(get_theme_css(current_theme), unsafe_allow_html=True)


def general_settings():
    st.subheader("Display Settings")
    general_settings = load_general_settings()
    phoenix_settings = load_phoenix_settings()

    num_columns = st.number_input(
        "Number of columns in article list",
        min_value=1,
        max_value=6,
        value=general_settings.get("num_columns", 3),
        step=1,
        help="Set the number of columns for displaying articles in the My Articles page.",
        key="num_columns_input",
    )

    if st.button("Save Display Settings", key="save_display_settings_button"):
        save_general_settings({"num_columns": num_columns})
        st.success("Display settings saved successfully!")

    st.subheader("Phoenix Settings")
    phoenix_settings = load_phoenix_settings()

    phoenix_enabled = st.toggle(
        "Enable Phoenix Tracing",
        value=phoenix_settings.get("enabled", False),
        help="Toggle Phoenix tracing on/off.",
        key="phoenix_enabled_toggle",
    )

    phoenix_project_name = st.text_input(
        "Phoenix Project Name",
        value=phoenix_settings.get("project_name", "storm-wiki"),
        help="Set the project name for Phoenix tracing.",
        key="phoenix_project_name_input",
    )

    phoenix_collector_endpoint = st.text_input(
        "Phoenix Collector Endpoint",
        value=phoenix_settings.get("collector_endpoint", "localhost:6006"),
        help="Set the endpoint for the Phoenix collector.",
        key="phoenix_collector_endpoint_input",
    )

    if st.button("Save Phoenix Settings", key="save_phoenix_settings_button"):
        save_phoenix_settings(
            {
                "enabled": phoenix_enabled,
                "project_name": phoenix_project_name,
                "collector_endpoint": phoenix_collector_endpoint,
            }
        )
        st.success("Phoenix settings saved successfully!")
        st.session_state.phoenix_settings_updated = True


def theme_settings():
    st.subheader("Theme Settings")
    current_theme = st.session_state.current_theme

    current_theme_mode = "Light" if current_theme in light_themes.values() else "Dark"
    theme_mode = st.radio(
        "Theme Mode",
        ["Light", "Dark"],
        index=["Light", "Dark"].index(current_theme_mode),
        key="theme_mode_radio",
    )

    theme_options = light_themes if theme_mode == "Light" else dark_themes
    current_theme_name = next(
        (k for k, v in theme_options.items() if v == current_theme), None
    )
    if current_theme_name is None:
        current_theme_name = list(theme_options.keys())[0]

    selected_theme_name = st.selectbox(
        "Select a theme",
        list(theme_options.keys()),
        index=list(theme_options.keys()).index(current_theme_name),
        key="theme_select",
    )

    current_theme = theme_options[selected_theme_name]

    st.subheader("Color Customization")
    col1, col2 = st.columns(2)

    with col1:
        custom_theme = {}
        for key, value in current_theme.items():
            if key != "font":
                custom_theme[key] = st.color_picker(
                    f"{key}", value, key=f"color_picker_{key}"
                )
            else:
                custom_theme[key] = st.selectbox(
                    "Font",
                    ["sans serif", "serif", "monospace"],
                    index=["sans serif", "serif", "monospace"].index(value),
                    key="font_select",
                )

    with col2:
        st.markdown(get_preview_html(custom_theme), unsafe_allow_html=True)

    if st.button("Apply Theme", key="apply_theme_button"):
        save_theme(custom_theme)
        st.session_state.current_theme = custom_theme
        st.success("Theme applied successfully!")
        st.session_state.force_rerun = True
        st.rerun()


def search_settings():
    st.subheader("Search Options Settings")

    if "search_options" not in st.session_state:
        st.session_state.search_options = load_search_options()

    search_options = st.session_state.search_options

    primary_engine = st.selectbox(
        "Primary Search Engine",
        options=list(SEARCH_ENGINES.keys()),
        index=list(SEARCH_ENGINES.keys()).index(search_options["primary_engine"]),
        key="primary_engine_select",
    )

    fallback_options = [None] + [
        engine for engine in SEARCH_ENGINES.keys() if engine != primary_engine
    ]
    current_fallback = search_options["fallback_engine"]
    if current_fallback == primary_engine or current_fallback not in fallback_options:
        current_fallback = None

    fallback_engine = st.selectbox(
        "Fallback Search Engine",
        options=fallback_options,
        index=fallback_options.index(current_fallback),
        key="fallback_engine_select",
    )

    search_top_k = st.number_input(
        "Search Top K",
        min_value=1,
        max_value=100,
        value=search_options["search_top_k"],
        key="search_top_k_input",
    )

    retrieve_top_k = st.number_input(
        "Retrieve Top K",
        min_value=1,
        max_value=100,
        value=search_options["retrieve_top_k"],
        key="retrieve_top_k_input",
    )

    st.subheader("Engine-specific Settings")
    engine_settings = search_options.get("engine_settings", {})

    for engine in SEARCH_ENGINES:
        with st.expander(f"{engine.capitalize()} Settings"):
            engine_settings[engine] = get_engine_specific_settings(
                engine, engine_settings.get(engine, {})
            )

    if st.button("Save Search Options", key="save_search_options_button"):
        updated_search_options = {
            "primary_engine": primary_engine,
            "fallback_engine": fallback_engine,
            "search_top_k": search_top_k,
            "retrieve_top_k": retrieve_top_k,
            "engine_settings": engine_settings,
        }
        save_search_options(**updated_search_options)
        st.session_state.search_options = updated_search_options
        st.success("Search options saved successfully!")
        st.experimental_rerun()


def llm_settings():
    st.subheader("LLM Settings")
    llm_settings = load_llm_settings()

    primary_model = st.selectbox(
        "Primary LLM Model",
        options=list(LLM_MODELS.keys()),
        index=list(LLM_MODELS.keys()).index(llm_settings["primary_model"]),
        key="primary_model_select",
    )

    fallback_model = st.selectbox(
        "Fallback LLM Model",
        options=[None]
        + [model for model in LLM_MODELS.keys() if model != primary_model],
        index=0
        if llm_settings["fallback_model"] is None
        else (
            [None] + [model for model in LLM_MODELS.keys() if model != primary_model]
        ).index(llm_settings["fallback_model"]),
        key="fallback_model_select",
    )

    model_settings = llm_settings["model_settings"]

    st.subheader("Model-specific Settings")
    for model, env_var in LLM_MODELS.items():
        st.write(f"{model.capitalize()} Settings")
        model_settings[model] = model_settings.get(model, {})

        if model == "ollama":
            downloaded_models = list_downloaded_models()
            model_settings[model]["model"] = st.selectbox(
                "Ollama Model",
                options=downloaded_models,
                index=downloaded_models.index(
                    model_settings[model].get(
                        "model", "jaigouk/hermes-2-theta-llama-3:latest"
                    )
                ),
                key=f"{model}_model_select",
            )
        elif model == "openai":
            model_settings[model]["model"] = st.selectbox(
                "OpenAI Model",
                options=["gpt-4o-mini", "gpt-4o"],
                index=0 if model_settings[model].get("model") == "gpt-4o-mini" else 1,
                key=f"{model}_model_select",
            )
        elif model == "anthropic":
            model_settings[model]["model"] = st.selectbox(
                "Anthropic Model",
                options=["claude-3-haiku-20240307", "claude-3-5-sonnet-20240620"],
                index=0
                if model_settings[model].get("model") == "claude-3-haiku-20240307"
                else 1,
                key=f"{model}_model_select",
            )

        model_settings[model]["max_tokens"] = st.number_input(
            f"{model.capitalize()} Max Tokens",
            min_value=1,
            max_value=10000,
            value=model_settings[model].get("max_tokens", 500),
            key=f"{model}_max_tokens_input",
        )

    if st.button("Save LLM Settings", key="save_llm_settings_button"):
        save_llm_settings(primary_model, fallback_model, model_settings)
        st.success("LLM settings saved successfully!")


def category_settings():
    st.header("Category Management")

    with st.expander("## Output Directory", expanded=False):
        output_dir = load_output_dir()
        new_output_dir = st.text_input("Set output directory", value=output_dir)
        if st.button("Update Output Directory"):
            save_output_dir(new_output_dir)
            st.success(f"Output directory updated to: {new_output_dir}")
            os.environ["STREAMLIT_OUTPUT_DIR"] = new_output_dir

    with st.expander("## Manage Existing Categories", expanded=False):
        categories = load_categories()
        if categories:
            for category in categories:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"- {category}")
                with col2:
                    if st.button(f"Edit", key=f"edit_{category}"):
                        st.session_state.editing_category = category
                with col3:
                    if st.button(f"Delete", key=f"delete_{category}"):
                        st.session_state.deleting_category = category

            if "editing_category" in st.session_state:
                st.markdown("---")
                st.write(f"Editing category: {st.session_state.editing_category}")
                new_name = st.text_input(
                    "New category name", value=st.session_state.editing_category
                )
                if st.button("Update Category"):
                    update_category(st.session_state.editing_category, new_name)
                    del st.session_state.editing_category
                    st.rerun()

            if "deleting_category" in st.session_state:
                st.markdown("---")
                st.write(f"Deleting category: {st.session_state.deleting_category}")
                remaining_categories = [
                    cat
                    for cat in categories
                    if cat != st.session_state.deleting_category
                ]
                if remaining_categories:
                    target_category = st.selectbox(
                        "Move articles to:", remaining_categories
                    )
                    if st.button("Confirm Delete"):
                        delete_category(
                            st.session_state.deleting_category, target_category
                        )
                        del st.session_state.deleting_category
                        st.rerun()
                else:
                    st.warning("Cannot delete the last remaining category.")
        else:
            st.info("No existing categories.")

    with st.expander("## Add New Category", expanded=False):
        new_category = st.text_input("New category name")
        if st.button("Add Category"):
            if new_category and new_category not in categories:
                categories.append(new_category)
                save_categories(categories)
                create_category_folder(new_category)
                st.success(f"Added new category: {new_category}")
                st.rerun()
            elif new_category in categories:
                st.warning("Category already exists")
            else:
                st.warning("Please enter a category name")


def update_category(old_name, new_name):
    categories = load_categories()
    if old_name in categories:
        categories[categories.index(old_name)] = new_name
        save_categories(categories)
        rename_category_folder(old_name, new_name)
        st.success(f"Category updated from {old_name} to {new_name}")
    else:
        st.error("Category not found")


def delete_category(category, target_category):
    categories = load_categories()
    if category in categories:
        categories.remove(category)
        save_categories(categories)
        move_category_contents(category, target_category)
        st.success(
            f"Category {category} deleted and contents moved to {target_category}"
        )
    else:
        st.error("Category not found")


def create_category_folder(category):
    output_dir = load_output_dir()
    category_path = os.path.join(output_dir, category)
    os.makedirs(category_path, exist_ok=True)


def rename_category_folder(old_name, new_name):
    output_dir = load_output_dir()
    old_path = os.path.join(output_dir, old_name)
    new_path = os.path.join(output_dir, new_name)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)


def move_category_contents(source_category, target_category):
    output_dir = load_output_dir()
    source_path = os.path.join(output_dir, source_category)
    target_path = os.path.join(output_dir, target_category)
    if os.path.exists(source_path):
        for item in os.listdir(source_path):
            s = os.path.join(source_path, item)
            d = os.path.join(target_path, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        shutil.rmtree(source_path)
