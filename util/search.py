import os
import re
import logging
from urllib.parse import urlparse
from typing import Union, List, Dict, Any

import dspy
import requests
from bs4 import BeautifulSoup
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper


class WebSearchAPIWrapper(dspy.Retrieve):
    def __init__(self, max_results=3):
        super().__init__()
        self.max_results = max_results
        self.generally_unreliable = set()
        self.deprecated = set()
        self.blacklisted = set()
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

            patterns = {
                "generally_unreliable": r'<tr class="s-gu"[^>]*id="([^"]+)"',
                "deprecated": r'<tr class="s-d"[^>]*id="([^"]+)"',
                "blacklisted": r'<tr class="s-b"[^>]*id="([^"]+)"',
            }

            for category, pattern in patterns.items():
                matches = re.findall(pattern, content)
                processed_ids = [id_str.replace("&#39;", "'") for id_str in matches]
                setattr(
                    self,
                    category,
                    set(id_str.split("_(")[0] for id_str in processed_ids),
                )

        except FileNotFoundError:
            logging.warning(
                "Wikipedia sources file not found. Domain restrictions will not be applied."
            )
        except IOError as e:
            logging.error(f"Error reading Wikipedia sources file: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in _generate_domain_restriction: {e}")

    def _is_valid_wikipedia_source(self, url):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.split(".")[-2]  # Get the domain name
        combined_set = self.generally_unreliable | self.deprecated | self.blacklisted
        return domain not in combined_set

    def forward(
        self, query_or_queries: Union[str, List[str]], exclude_urls: List[str] = []
    ) -> List[Dict[str, Any]]:
        if not dspy.settings.rm:
            raise ValueError("No RM is loaded. Please load a Retrieval Model first.")
        return super().forward(query_or_queries, exclude_urls=exclude_urls)


class DuckDuckGoSearchAPI(WebSearchAPIWrapper):
    def __init__(self, max_results=3, use_snippet=False, timeout=120):
        super().__init__(max_results)
        self.retrieve = DuckDuckGoSearchAPIWrapper()
        self.use_snippet = use_snippet
        self.timeout = timeout

    def forward(
        self, query_or_queries: Union[str, List[str]], exclude_urls: List[str] = []
    ) -> List[Dict[str, Any]]:
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
                        try:
                            response = requests.get(url, timeout=self.timeout)
                            soup = BeautifulSoup(response.text, "html.parser")
                            reference = soup.get_text() or result.get("snippet", "")
                        except Exception as e:
                            logging.error(f"Error extracting content from {url}: {e}")
                            reference = result.get("snippet", "")

                    target_result = {
                        "description": result.get("snippet", ""),
                        "snippets": [reference],
                        "title": result.get("title", ""),
                        "url": url,
                    }
                    results.append(target_result)

                collected_results.extend(results[: self.max_results])

            except Exception as e:
                logging.error(f"Error occurs when searching query {query}: {e}")

        collected_results = [
            r
            for r in collected_results
            if r["url"] not in exclude_urls
            and self._is_valid_wikipedia_source(r["url"])
        ]
        return collected_results[: self.max_results]


class DuckDuckGoAdapter(WebSearchAPIWrapper):
    def __init__(self, k):
        super().__init__(max_results=k)
        self.k = k
        try:
            self.ddg_search = DuckDuckGoSearchAPIWrapper()
        except ImportError:
            logging.error(
                "Error: DuckDuckGoSearchAPIWrapper could not be imported. Make sure duckduckgo-search is installed."
            )
            self.ddg_search = None

    def forward(
        self, query_or_queries: Union[str, List[str]], exclude_urls: List[str] = []
    ) -> List[Dict[str, Any]]:
        if self.ddg_search is None:
            logging.warning(
                "DuckDuckGoSearchAPIWrapper is not available. Returning empty results."
            )
            return []

        queries = (
            [query_or_queries]
            if isinstance(query_or_queries, str)
            else query_or_queries
        )
        all_results = []

        for query in queries:
            query_results = []
            try:
                ddg_results = self.ddg_search.results(query, max_results=self.k)
                for result in ddg_results:
                    if result[
                        "link"
                    ] not in exclude_urls and self._is_valid_wikipedia_source(
                        result["link"]
                    ):
                        query_results.append(
                            {
                                "description": result.get("snippet", ""),
                                "snippets": [result.get("snippet", "")],
                                "title": result.get("title", ""),
                                "url": result["link"],
                            }
                        )
                    if len(query_results) >= self.k:
                        break
            except Exception as e:
                logging.error(
                    f"Error occurred while searching query '{query}': {e}",
                    exc_info=True,
                )

            all_results.extend(query_results)

        if not all_results:
            logging.warning(f"No results found for queries: {query_or_queries}")

        return all_results
