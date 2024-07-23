import base64
import datetime
import json
import os
import re
from typing import Optional

import markdown
import pytz
import streamlit as st

# If you install the source code instead of the `knowledge-storm` package,
# Uncomment the following lines:
# import sys
# sys.path.append('../../')
from knowledge_storm import (
    STORMWikiRunnerArguments,
    STORMWikiRunner,
    STORMWikiLMConfigs,
)
from knowledge_storm.lm import OpenAIModel, OllamaClient
from knowledge_storm.storm_wiki.modules.callback import BaseCallbackHandler
from stoc import stoc

import logging
from typing import Union, List
from urllib.parse import urlparse
import dspy
import newspaper
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper

from dotenv import load_dotenv

import shutil


load_dotenv()


class WebSearchAPIWrapper(dspy.Retrieve):
    def __init__(self, max_results=3):
        super().__init__()

        self.max_results = max_results

        # The Wikipedia standard for sources.
        self.generally_unreliable = None
        self.deprecated = None
        self.blacklisted = None
        self._generate_domain_restriction()

    def _generate_domain_restriction(self):
        """Generate domain restriction from Wikipedia standard."""

        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(
                script_dir,
                "Wikipedia_Reliable sources_Perennial sources - Wikipedia.html",
            )

            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            # Define the regular expression pattern to find the specified HTML tags
            generally_unreliable = (
                r'<tr class="s-gu" id="[^"]+">|<id="[^"]+" tr class="s-gu" >'
            )
            deprecate = r'<tr class="s-d" id="[^"]+">|<id="[^"]+" tr class="s-d" >'
            blacklist = r'<tr class="s-b" id="[^"]+">|<id="[^"]+" tr class="s-b" >'

            # find instance
            gu = re.findall(generally_unreliable, content)
            d = re.findall(deprecate, content)
            b = re.findall(blacklist, content)

            # extract id
            s_gu = [re.search(r'id="([^"]+)"', match).group(1) for match in gu]
            s_d = [re.search(r'id="([^"]+)"', match).group(1) for match in d]
            s_b = [re.search(r'id="([^"]+)"', match).group(1) for match in b]

            # complete list
            generally_unreliable = [id_str.replace("&#39;", "'") for id_str in s_gu]
            deprecated = [id_str.replace("&#39;", "'") for id_str in s_d]
            blacklisted = [id_str.replace("&#39;", "'") for id_str in s_b]

            # for now, when encountering Fox_News_(politics_and_science), we exclude the entire domain Fox_News and we can later increase the complexity of the rule to distinguish between different cases
            generally_unreliable_f = set(
                id_str.split("_(")[0] for id_str in generally_unreliable
            )
            deprecated_f = set(id_str.split("_(")[0] for id_str in deprecated)
            blacklisted_f = set(id_str.split("_(")[0] for id_str in blacklisted)

            self.generally_unreliable = generally_unreliable_f
            self.deprecated = deprecated_f
            self.blacklisted = blacklisted_f
        except FileNotFoundError:
            print(
                "Warning: Wikipedia sources file not found. Domain restrictions will not be applied."
            )
            self.generally_unreliable = set()
            self.deprecated = set()
            self.blacklisted = set()

    def _is_valid_wikipedia_source(self, url):
        parsed_url = urlparse(url)
        # Check if the URL is from a reliable domain
        combined_set = self.generally_unreliable | self.deprecated | self.blacklisted
        for domain in combined_set:
            if domain in parsed_url.netloc:
                return False

        return True

    def forward(
        self, query_or_queries: Union[str, List[str]], exclude_urls: List[str]
    ) -> List[str]:
        pass


class DuckDuckGoSearchAPI(WebSearchAPIWrapper):
    def __init__(self, max_results=3, use_snippet=False, timeout=120):
        super().__init__(max_results)
        self.retrieve = DuckDuckGoSearchAPIWrapper()
        self.use_snippet = use_snippet
        self.timeout = timeout

    def forward(
        self, query_or_queries: Union[str, List[str]], exclude_urls: List[str]
    ) -> List[str]:
        """Search with https://duckduckgo.com for self.max_results top passages for query or queries

        Args:
            query_or_queries (Union[str, List[str]]): The query or queries to search for.
            exclude_urls (List[str]): A list of urls to exclude from the search results.

        Returns:
            a list of Dicts, each dict has keys of 'description', 'snippets' (list of strings), 'title', 'url'
        """
        queries = (
            [query_or_queries]
            if isinstance(query_or_queries, str)
            else query_or_queries
        )
        collected_results = []
        for query in queries:
            try:
                retrieve_results = self.retrieve.results(
                    query, max_results=5, source="text"
                )
                results = []
                for result in retrieve_results:
                    url = result.get("link", "")
                    if self.use_snippet:
                        reference = result.get("snippet", "")
                    else:
                        # To extract the complete content using newspaper
                        article = newspaper.article(url, timeout=self.timeout)
                        reference = article.text or result.get("snippet", "")

                    target_result = {
                        "description": result.get("snippet", ""),
                        "snippets": [reference],
                        "title": result.get("title", ""),
                        "url": url,
                    }
                    results.append(target_result)

                collected_results += results[: self.max_results]

            except Exception as e:
                logging.error(f"Error occurs when searching query {query}: {e}")

        if exclude_urls:
            collected_results = [
                r for r in collected_results if r["url"] not in exclude_urls
            ]

        return collected_results


class DuckDuckGoAdapter(WebSearchAPIWrapper):
    def __init__(self, k):
        super().__init__(max_results=k)
        self.k = k
        try:
            from langchain_community.utilities.duckduckgo_search import (
                DuckDuckGoSearchAPIWrapper,
            )

            self.ddg_search = DuckDuckGoSearchAPIWrapper()
        except ImportError:
            print(
                "Error: DuckDuckGoSearchAPIWrapper could not be imported. Make sure duckduckgo-search is installed."
            )
            self.ddg_search = None

    def forward(
        self, query_or_queries: Union[str, List[str]], exclude_urls: List[str]
    ) -> List[str]:
        if self.ddg_search is None:
            print(
                "DuckDuckGoSearchAPIWrapper is not available. Returning empty results."
            )
            return []

        queries = (
            [query_or_queries]
            if isinstance(query_or_queries, str)
            else query_or_queries
        )
        results = []
        for query in queries:
            try:
                ddg_results = self.ddg_search.results(query, max_results=self.k)
                for result in ddg_results:
                    if result[
                        "link"
                    ] not in exclude_urls and self._is_valid_wikipedia_source(
                        result["link"]
                    ):
                        results.append(
                            {
                                "description": result.get("snippet", ""),
                                "snippets": [result.get("snippet", "")],
                                "title": result.get("title", ""),
                                "url": result["link"],
                            }
                        )
                    if len(results) >= self.k:
                        break
                if len(results) >= self.k:
                    break
            except Exception as e:
                print(f"Error occurred while searching: {e}")
        return results[: self.k]


class DemoFileIOHelper:
    @staticmethod
    def read_structure_to_dict(articles_root_path):
        """
        Reads the directory structure of articles stored in the given root path and
        returns a nested dictionary. The outer dictionary has article names as keys,
        and each value is another dictionary mapping file names to their absolute paths.

        Args:
            articles_root_path (str): The root directory path containing article subdirectories.

        Returns:
            dict: A dictionary where each key is an article name, and each value is a dictionary
                of file names and their absolute paths within that article's directory.
        """
        articles_dict = {}
        for topic_name in os.listdir(articles_root_path):
            topic_path = os.path.join(articles_root_path, topic_name)
            if os.path.isdir(topic_path):
                # Initialize or update the dictionary for the topic
                articles_dict[topic_name] = {}
                # Iterate over all files within a topic directory
                for file_name in os.listdir(topic_path):
                    file_path = os.path.join(topic_path, file_name)
                    articles_dict[topic_name][file_name] = os.path.abspath(file_path)
        return articles_dict

    @staticmethod
    def read_txt_file(file_path):
        """
        Reads the contents of a text file and returns it as a string.

        Args:
            file_path (str): The path to the text file to be read.

        Returns:
            str: The content of the file as a single string.
        """
        with open(file_path) as f:
            return f.read()

    @staticmethod
    def read_json_file(file_path):
        """
        Reads a JSON file and returns its content as a Python dictionary or list,
        depending on the JSON structure.

        Args:
            file_path (str): The path to the JSON file to be read.

        Returns:
            dict or list: The content of the JSON file. The type depends on the
                        structure of the JSON file (object or array at the root).
        """
        with open(file_path) as f:
            return json.load(f)

    @staticmethod
    def read_image_as_base64(image_path):
        """
        Reads an image file and returns its content encoded as a base64 string,
        suitable for embedding in HTML or transferring over networks where binary
        data cannot be easily sent.

        Args:
            image_path (str): The path to the image file to be encoded.

        Returns:
            str: The base64 encoded string of the image, prefixed with the necessary
                data URI scheme for images.
        """
        with open(image_path, "rb") as f:
            data = f.read()
            encoded = base64.b64encode(data)
        data = "data:image/png;base64," + encoded.decode("utf-8")
        return data

    @staticmethod
    def set_file_modification_time(file_path, modification_time_string):
        """
        Sets the modification time of a file based on a given time string in the California time zone.

        Args:
            file_path (str): The path to the file.
            modification_time_string (str): The desired modification time in 'YYYY-MM-DD HH:MM:SS' format.
        """
        california_tz = pytz.timezone("America/Los_Angeles")
        modification_time = datetime.datetime.strptime(
            modification_time_string, "%Y-%m-%d %H:%M:%S"
        )
        modification_time = california_tz.localize(modification_time)
        modification_time_utc = modification_time.astimezone(datetime.timezone.utc)
        modification_timestamp = modification_time_utc.timestamp()
        os.utime(file_path, (modification_timestamp, modification_timestamp))

    @staticmethod
    def get_latest_modification_time(path):
        """
        Returns the latest modification time of all files in a directory in the California time zone as a string.

        Args:
            directory_path (str): The path to the directory.

        Returns:
            str: The latest file's modification time in 'YYYY-MM-DD HH:MM:SS' format.
        """
        california_tz = pytz.timezone("America/Los_Angeles")
        latest_mod_time = None

        file_paths = []
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_paths.append(os.path.join(root, file))
        else:
            file_paths = [path]

        for file_path in file_paths:
            modification_timestamp = os.path.getmtime(file_path)
            modification_time_utc = datetime.datetime.utcfromtimestamp(
                modification_timestamp
            )
            modification_time_utc = modification_time_utc.replace(
                tzinfo=datetime.timezone.utc
            )
            modification_time_california = modification_time_utc.astimezone(
                california_tz
            )

            if (
                latest_mod_time is None
                or modification_time_california > latest_mod_time
            ):
                latest_mod_time = modification_time_california

        if latest_mod_time is not None:
            return latest_mod_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def assemble_article_data(article_file_path_dict):
        """
        Constructs a dictionary containing the content and metadata of an article
        based on the available files in the article's directory. This includes the
        main article text, citations from a JSON file, and a conversation log if
        available. The function prioritizes a polished version of the article if
        both a raw and polished version exist.

        Args:
            article_file_paths (dict): A dictionary where keys are file names relevant
                                    to the article (e.g., the article text, citations
                                    in JSON format, conversation logs) and values
                                    are their corresponding file paths.

        Returns:
            dict or None: A dictionary containing the parsed content of the article,
                        citations, and conversation log if available. Returns None
                        if neither the raw nor polished article text exists in the
                        provided file paths.
        """
        if (
            "storm_gen_article.md" in article_file_path_dict
            or "storm_gen_article_polished.md" in article_file_path_dict
        ):
            full_article_name = (
                "storm_gen_article_polished.md"
                if "storm_gen_article_polished.md" in article_file_path_dict
                else "storm_gen_article.md"
            )
            # Read the article content
            article_content = DemoFileIOHelper.read_txt_file(
                article_file_path_dict[full_article_name]
            )

            # Add the current date at the beginning of the article
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            article_content = f"{current_date}\n\n{article_content}"

            # Parse the article content
            parsed_article_content = DemoTextProcessingHelper.parse(article_content)

            article_data = {"article": parsed_article_content}
            if "url_to_info.json" in article_file_path_dict:
                article_data["citations"] = _construct_citation_dict_from_search_result(
                    DemoFileIOHelper.read_json_file(
                        article_file_path_dict["url_to_info.json"]
                    )
                )
            if "conversation_log.json" in article_file_path_dict:
                article_data["conversation_log"] = DemoFileIOHelper.read_json_file(
                    article_file_path_dict["conversation_log.json"]
                )
            return article_data
        return None


class DemoTextProcessingHelper:
    @staticmethod
    def remove_citations(sent):
        return (
            re.sub(r"\[\d+", "", re.sub(r" \[\d+", "", sent))
            .replace(" |", "")
            .replace("]", "")
        )

    @staticmethod
    def parse_conversation_history(json_data):
        """
        Given conversation log data, return list of parsed data of following format
        (persona_name, persona_description, list of dialogue turn)
        """
        parsed_data = []
        for persona_conversation_data in json_data:
            if ": " in persona_conversation_data["perspective"]:
                name, description = persona_conversation_data["perspective"].split(
                    ": ", 1
                )
            elif "- " in persona_conversation_data["perspective"]:
                name, description = persona_conversation_data["perspective"].split(
                    "- ", 1
                )
            else:
                name, description = "", persona_conversation_data["perspective"]
            cur_conversation = []
            for dialogue_turn in persona_conversation_data["dlg_turns"]:
                cur_conversation.append(
                    {"role": "user", "content": dialogue_turn["user_utterance"]}
                )
                cur_conversation.append(
                    {
                        "role": "assistant",
                        "content": DemoTextProcessingHelper.remove_citations(
                            dialogue_turn["agent_utterance"]
                        ),
                    }
                )
            parsed_data.append((name, description, cur_conversation))
        return parsed_data

    @staticmethod
    def parse(text):
        regex = re.compile(r']:\s+"(.*?)"\s+http')
        text = regex.sub("]: http", text)
        return text

    @staticmethod
    def add_markdown_indentation(input_string):
        lines = input_string.split("\n")
        processed_lines = [""]
        for line in lines:
            num_hashes = 0
            for char in line:
                if char == "#":
                    num_hashes += 1
                else:
                    break
            num_hashes -= 1
            num_spaces = 4 * num_hashes
            new_line = " " * num_spaces + line
            processed_lines.append(new_line)
        return "\n".join(processed_lines)

    @staticmethod
    def get_current_time_string():
        """
        Returns the current time in the time zone as a string, using the STORM_TIMEZONE environment variable.

        Returns:
            str: The current time in 'YYYY-MM-DD HH:MM:SS' format.
        """
        # Load the time zone from the STORM_TIMEZONE environment variable, default to "America/Los_Angeles" if not set
        time_zone_str = os.getenv("STORM_TIMEZONE", "America/Los_Angeles")
        time_zone = pytz.timezone(time_zone_str)

        # Get the current time in UTC and convert it to the specified time zone
        utc_now = datetime.datetime.now(pytz.utc)
        time_now = utc_now.astimezone(time_zone)

        return time_now.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def compare_time_strings(
        time_string1, time_string2, time_format="%Y-%m-%d %H:%M:%S"
    ):
        """
        Compares two time strings to determine if they represent the same point in time.

        Args:
            time_string1 (str): The first time string to compare.
            time_string2 (str): The second time string to compare.
            time_format (str): The format of the time strings, defaults to '%Y-%m-%d %H:%M:%S'.

        Returns:
            bool: True if the time strings represent the same time, False otherwise.
        """
        # Parse the time strings into datetime objects
        time1 = datetime.datetime.strptime(time_string1, time_format)
        time2 = datetime.datetime.strptime(time_string2, time_format)

        # Compare the datetime objects
        return time1 == time2

    @staticmethod
    def add_inline_citation_link(article_text, citation_dict):
        # Regular expression to find citations like [i]
        pattern = r"\[(\d+)\]"

        # Function to replace each citation with its Markdown link
        def replace_with_link(match):
            i = match.group(1)
            url = citation_dict.get(int(i), {}).get("url", "#")
            return f"[[{i}]]({url})"

        # Replace all citations in the text with Markdown links
        return re.sub(pattern, replace_with_link, article_text)

    @staticmethod
    def generate_html_toc(md_text):
        toc = []
        for line in md_text.splitlines():
            if line.startswith("#"):
                level = line.count("#")
                title = line.strip("# ").strip()
                anchor = title.lower().replace(" ", "-").replace(".", "")
                toc.append(
                    f"<li style='margin-left: {20 * (level - 1)}px;'><a href='#{anchor}'>{title}</a></li>"
                )
        return "<ul>" + "".join(toc) + "</ul>"

    @staticmethod
    def construct_bibliography_from_url_to_info(url_to_info):
        bibliography_list = []
        sorted_url_to_unified_index = dict(
            sorted(
                url_to_info["url_to_unified_index"].items(), key=lambda item: item[1]
            )
        )
        for url, index in sorted_url_to_unified_index.items():
            title = url_to_info["url_to_info"][url]["title"]
            bibliography_list.append(f"[{index}]: [{title}]({url})")
        bibliography_string = "\n\n".join(bibliography_list)
        return f"# References\n\n{bibliography_string}"


class DemoUIHelper:
    def st_markdown_adjust_size(content, font_size=20):
        st.markdown(
            f"""
        <span style='font-size: {font_size}px;'>{content}</span>
        """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def get_article_card_UI_style(boarder_color="#9AD8E1"):
        return {
            "card": {
                "width": "100%",
                "height": "116px",
                "max-width": "640px",
                "background-color": "#FFFFF",
                "border": "1px solid #CCC",
                "padding": "20px",
                "border-radius": "5px",
                "border-left": f"0.5rem solid {boarder_color}",
                "box-shadow": "0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15)",
                "margin": "0px",
            },
            "title": {
                "white-space": "nowrap",
                "overflow": "hidden",
                "text-overflow": "ellipsis",
                "font-size": "17px",
                "color": "rgb(49, 51, 63)",
                "text-align": "left",
                "width": "95%",
                "font-weight": "normal",
            },
            "text": {
                "white-space": "nowrap",
                "overflow": "hidden",
                "text-overflow": "ellipsis",
                "font-size": "25px",
                "color": "rgb(49, 51, 63)",
                "text-align": "left",
                "width": "95%",
            },
            "filter": {"background-color": "rgba(0, 0, 0, 0)"},
        }

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
        persona_tabs = st.tabs([name for (name, _, _) in parsed_conversation_history])
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


def _construct_citation_dict_from_search_result(search_results):
    if search_results is None:
        return None
    citation_dict = {}
    for url, index in search_results["url_to_unified_index"].items():
        citation_dict[index] = {
            "url": url,
            "title": search_results["url_to_info"][url]["title"],
            "snippets": search_results["url_to_info"][url]["snippets"],
        }
    return citation_dict


def _display_main_article_text(article_text, citation_dict, table_content_sidebar):
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
    stoc.from_markdown(article_text, table_content_sidebar)


def _display_references(citation_dict):
    if citation_dict:
        reference_list = [f"reference [{i}]" for i in range(1, len(citation_dict) + 1)]
        selected_key = st.selectbox("Select a reference", reference_list)
        citation_val = citation_dict[reference_list.index(selected_key) + 1]
        citation_val["title"] = citation_val["title"].replace("$", "\\$")
        st.markdown(f"**Title:** {citation_val['title']}")
        st.markdown(f"**Url:** {citation_val['url']}")
        snippets = "\n\n".join(citation_val["snippets"]).replace("$", "\\$")
        st.markdown(f"**Highlights:**\n\n {snippets}")
    else:
        st.markdown("**No references available**")


def _display_main_article(
    selected_article_file_path_dict, show_feedback_form=False, show_qa_panel=False
):
    try:
        article_data = DemoFileIOHelper.assemble_article_data(
            selected_article_file_path_dict
        )

        if article_data is None:
            st.warning("No article data found.")
            return

        with st.container(height=1000, border=True):
            table_content_sidebar = st.sidebar.expander(
                "**Table of contents**", expanded=True
            )
            _display_main_article_text(
                article_text=article_data.get("article", ""),
                citation_dict=article_data.get("citations", {}),
                table_content_sidebar=table_content_sidebar,
            )

        # display reference panel
        if "citations" in article_data:
            with st.sidebar.expander("**References**", expanded=True):
                with st.container(height=800, border=False):
                    _display_references(citation_dict=article_data.get("citations", {}))

        # display conversation history
        if "conversation_log" in article_data:
            with st.expander(
                "**STORM** is powered by a knowledge agent that proactively research a given topic by asking good questions coming from different perspectives.\n\n"
                ":sunglasses: Click here to view the agent's brain**STORM**ing process!"
            ):
                DemoUIHelper.display_persona_conversations(
                    conversation_log=article_data.get("conversation_log", {})
                )

        # Add placeholders for feedback form and QA panel if needed
        if show_feedback_form:
            st.write("Feedback form placeholder")

        if show_qa_panel:
            st.write("QA panel placeholder")

    except Exception as e:
        st.error(f"Error in _display_main_article: {str(e)}")
        st.exception(e)


def get_demo_dir():
    return os.path.dirname(os.path.abspath(__file__))


def get_output_dir():
    output_dir = os.getenv("STREAMLIT_OUTPUT_DIR")
    if not output_dir:
        # Fallback to a default directory if the env var is not set
        output_dir = os.path.join(get_demo_dir(), "DEMO_WORKING_DIR")

    # Ensure the directory exists
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def clear_other_page_session_state(page_index: Optional[int]):
    if page_index is None:
        keys_to_delete = [key for key in st.session_state if key.startswith("page")]
    else:
        keys_to_delete = [
            key
            for key in st.session_state
            if key.startswith("page") and f"page{page_index}" not in key
        ]
    for key in set(keys_to_delete):
        del st.session_state[key]


def convert_txt_to_md(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".txt") and "storm_gen_article" in file:
                txt_path = os.path.join(root, file)
                md_path = txt_path.rsplit(".", 1)[0] + ".md"
                shutil.move(txt_path, md_path)
                print(f"Converted {txt_path} to {md_path}")


import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError


def run_storm_with_fallback(topic, current_working_dir, callback_handler=None):
    def run_with_timeout(func, timeout=300):  # 5 minutes timeout
        with ThreadPoolExecutor() as executor:
            future = executor.submit(func)
            try:
                return future.result(timeout=timeout)
            except TimeoutError:
                st.error(f"Operation timed out after {timeout} seconds")
                return None

    def log_progress(message):
        st.info(message)
        if callback_handler:
            # Use an existing method of StreamlitCallbackHandler
            callback_handler.on_information_gathering_start(message=message)

    llm_configs = STORMWikiLMConfigs()
    ollama_kwargs = {
        "model": "jaigouk/hermes-2-theta-llama-3:latest",
        "url": "http://localhost",
        "port": 11434,
        "stop": ("\n\n---",),
    }

    log_progress("Initializing language models...")

    conv_simulator_lm = OllamaClient(max_tokens=500, **ollama_kwargs)
    question_asker_lm = OllamaClient(max_tokens=500, **ollama_kwargs)
    outline_gen_lm = OllamaClient(max_tokens=400, **ollama_kwargs)
    article_gen_lm = OllamaClient(max_tokens=700, **ollama_kwargs)
    article_polish_lm = OllamaClient(max_tokens=4000, **ollama_kwargs)

    llm_configs.set_conv_simulator_lm(conv_simulator_lm)
    llm_configs.set_question_asker_lm(question_asker_lm)
    llm_configs.set_outline_gen_lm(outline_gen_lm)
    llm_configs.set_article_gen_lm(article_gen_lm)
    llm_configs.set_article_polish_lm(article_polish_lm)

    engine_args = STORMWikiRunnerArguments(
        output_dir=current_working_dir,
        max_conv_turn=3,
        max_perspective=3,
        search_top_k=3,
        retrieve_top_k=5,
    )

    log_progress("Setting up search engine...")
    rm = DuckDuckGoAdapter(k=engine_args.search_top_k)
    runner = STORMWikiRunner(engine_args, llm_configs, rm)

    try:
        log_progress("Starting research phase...")

        def run_research():
            return runner.run(
                topic=topic,
                do_research=True,
                do_generate_outline=False,
                do_generate_article=False,
                do_polish_article=False,
            )

        if run_with_timeout(run_research) is None:
            raise Exception("Research phase timed out")

        log_progress("Research phase completed. Generating outline...")

        def run_outline():
            return runner.run(
                topic=topic,
                do_research=False,
                do_generate_outline=True,
                do_generate_article=False,
                do_polish_article=False,
            )

        if run_with_timeout(run_outline) is None:
            raise Exception("Outline generation timed out")

        log_progress("Outline generated. Writing article...")

        def run_article():
            return runner.run(
                topic=topic,
                do_research=False,
                do_generate_outline=False,
                do_generate_article=True,
                do_polish_article=False,
            )

        if run_with_timeout(run_article) is None:
            raise Exception("Article generation timed out")

        log_progress("Article written. Polishing...")

        def run_polish():
            return runner.run(
                topic=topic,
                do_research=False,
                do_generate_outline=False,
                do_generate_article=False,
                do_polish_article=True,
            )

        if run_with_timeout(run_polish) is None:
            raise Exception("Article polishing timed out")

        log_progress("Article polishing completed.")

    except Exception as e:
        st.error(f"Error during Ollama-based generation: {str(e)}")
        st.warning("Falling back to GPT-4 Mini...")

        # Fallback to GPT-4 Mini
        gpt4_mini_model = OpenAIModel(
            model="gpt-4o-mini-2024-07-18",
            api_key=st.secrets["OPENAI_API_KEY"],
            api_provider="openai",
            max_tokens=1000,
            temperature=0.3,
            top_p=0.9,
        )

        llm_configs.set_conv_simulator_lm(gpt4_mini_model)
        llm_configs.set_question_asker_lm(gpt4_mini_model)
        llm_configs.set_outline_gen_lm(gpt4_mini_model)
        llm_configs.set_article_gen_lm(gpt4_mini_model)
        llm_configs.set_article_polish_lm(gpt4_mini_model)

        # Re-initialize the runner with the updated configs
        runner = STORMWikiRunner(engine_args, llm_configs, rm)

        try:
            log_progress("Starting GPT-4 Mini fallback process...")
            run_with_timeout(
                lambda: runner.run(
                    topic=topic,
                    do_research=True,
                    do_generate_outline=True,
                    do_generate_article=True,
                    do_polish_article=True,
                )
            )
            log_progress("GPT-4 Mini fallback process completed.")
            runner.post_run()
            return runner
        except Exception as e:
            st.error(f"Error during GPT-4 Mini fallback: {str(e)}")
            return None

    runner.post_run()
    return runner


# Update the set_storm_runner function
def set_storm_runner():
    current_working_dir = get_output_dir()
    if not os.path.exists(current_working_dir):
        os.makedirs(current_working_dir)

    # Store the function itself in the session state
    st.session_state["run_storm"] = run_storm_with_fallback

    # Convert existing txt files to md
    convert_txt_to_md(current_working_dir)


def display_article_page(
    selected_article_name,
    selected_article_file_path_dict,
    show_title=True,
    show_main_article=True,
    show_feedback_form=False,
    show_qa_panel=False,
):
    try:
        if show_title:
            st.markdown(
                f"<h2 style='text-align: center;'>{selected_article_name.replace('_', ' ')}</h2>",
                unsafe_allow_html=True,
            )

        if show_main_article:
            _display_main_article(
                selected_article_file_path_dict, show_feedback_form, show_qa_panel
            )
    except Exception as e:
        st.error(f"Error displaying article: {str(e)}")
        st.exception(e)


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
