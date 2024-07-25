import pytest
from unittest.mock import patch, MagicMock
from util.search import WebSearchAPIWrapper, DuckDuckGoSearchAPI, DuckDuckGoAdapter
import dspy
import requests


@pytest.fixture
def mock_file_content():
    return """
    <tr class="s-gu" id="unreliable_source">
    <tr class="s-d" id="deprecated_source">
    <tr class="s-b" id="blacklisted_source">
    """


@pytest.fixture
def web_search_wrapper(tmp_path, mock_file_content):
    html_file = (
        tmp_path / "Wikipedia_Reliable sources_Perennial sources - Wikipedia.html"
    )
    html_file.write_text(mock_file_content)
    with patch("os.path.dirname", return_value=str(tmp_path)):
        return WebSearchAPIWrapper(max_results=3)


def test_web_search_wrapper_initialization(web_search_wrapper):
    assert web_search_wrapper.max_results == 3
    assert "unreliable_source" in web_search_wrapper.generally_unreliable
    assert "deprecated_source" in web_search_wrapper.deprecated
    assert "blacklisted_source" in web_search_wrapper.blacklisted


def test_is_valid_wikipedia_source(web_search_wrapper):
    assert web_search_wrapper._is_valid_wikipedia_source(
        "https://en.wikipedia.org/wiki/Test"
    )
    assert not web_search_wrapper._is_valid_wikipedia_source(
        "https://unreliable_source.com"
    )
    assert not web_search_wrapper._is_valid_wikipedia_source(
        "https://deprecated_source.org"
    )
    assert not web_search_wrapper._is_valid_wikipedia_source(
        "https://blacklisted_source.net"
    )
    # Edge case: Test with IP address
    assert web_search_wrapper._is_valid_wikipedia_source("http://192.168.1.1/page")
    # Edge case: Test with subdomain
    assert web_search_wrapper._is_valid_wikipedia_source(
        "https://subdomain.example.com"
    )


def test_web_search_wrapper_forward(web_search_wrapper):
    with pytest.raises(
        ValueError, match="No RM is loaded. Please load a Retrieval Model first."
    ):
        web_search_wrapper.forward("test query", [])


@patch("util.search.DuckDuckGoSearchAPIWrapper")
@patch("requests.get")
def test_duckduckgo_search_api_forward(mock_requests_get, mock_ddg_wrapper):
    mock_ddg_wrapper.return_value.results.return_value = [
        {
            "link": "https://example.com",
            "snippet": "Example snippet",
            "title": "Example Title",
        },
        {"link": "https://test.com", "snippet": "Test snippet", "title": "Test Title"},
    ]
    mock_response = MagicMock()
    mock_response.text = "<html><body>Mocked webpage content</body></html>"
    mock_requests_get.return_value = mock_response

    ddg_api = DuckDuckGoSearchAPI(max_results=2)
    results = ddg_api.forward("test query", [])

    assert len(results) == 2
    assert results[0]["url"] == "https://example.com"
    assert results[0]["snippets"] == ["Mocked webpage content"]
    assert results[0]["title"] == "Example Title"


@patch("util.search.DuckDuckGoSearchAPIWrapper")
def test_duckduckgo_adapter_forward(mock_ddg_wrapper):
    mock_ddg_wrapper.return_value.results.return_value = [
        {
            "link": "https://example.com",
            "snippet": "Example snippet",
            "title": "Example Title",
        },
        {"link": "https://test.com", "snippet": "Test snippet", "title": "Test Title"},
    ]

    ddg_adapter = DuckDuckGoAdapter(k=2)
    results = ddg_adapter.forward("test query", [])

    assert len(results) == 2
    assert results[0]["url"] == "https://example.com"
    assert results[0]["snippets"] == ["Example snippet"]
    assert results[0]["title"] == "Example Title"


@patch("util.search.DuckDuckGoSearchAPIWrapper")
def test_duckduckgo_adapter_forward_with_exclude_urls(mock_ddg_wrapper):
    mock_ddg_wrapper.return_value.results.return_value = [
        {
            "link": "https://example.com",
            "snippet": "Example snippet",
            "title": "Example Title",
        },
        {"link": "https://test.com", "snippet": "Test snippet", "title": "Test Title"},
    ]

    ddg_adapter = DuckDuckGoAdapter(k=2)
    results = ddg_adapter.forward("test query", ["https://example.com"])

    assert len(results) == 1
    assert results[0]["url"] == "https://test.com"


def test_duckduckgo_adapter_forward_no_results():
    with patch("util.search.DuckDuckGoSearchAPIWrapper", side_effect=ImportError):
        ddg_adapter = DuckDuckGoAdapter(k=2)
        results = ddg_adapter.forward("test query", [])
        assert results == []


@patch("requests.get")
@patch("util.search.DuckDuckGoSearchAPIWrapper")
def test_duckduckgo_search_api_forward_with_content_parsing(
    mock_ddg_wrapper, mock_requests_get
):
    mock_ddg_wrapper.return_value.results.return_value = [
        {
            "link": "https://example.com",
            "snippet": "Example snippet",
            "title": "Example Title",
        },
    ]
    mock_response = MagicMock()
    mock_response.text = "<html><body>Parsed webpage content</body></html>"
    mock_requests_get.return_value = mock_response

    ddg_api = DuckDuckGoSearchAPI(max_results=1, use_snippet=False)
    results = ddg_api.forward("test query", [])

    assert len(results) == 1
    assert results[0]["snippets"] == ["Parsed webpage content"]


@patch("requests.get")
@patch("util.search.DuckDuckGoSearchAPIWrapper")
def test_duckduckgo_search_api_forward_content_parsing_exception(
    mock_ddg_wrapper, mock_requests_get
):
    mock_ddg_wrapper.return_value.results.return_value = [
        {
            "link": "https://example.com",
            "snippet": "Example snippet",
            "title": "Example Title",
        },
    ]
    mock_requests_get.side_effect = requests.RequestException("Connection failed")

    ddg_api = DuckDuckGoSearchAPI(max_results=1, use_snippet=False)
    results = ddg_api.forward("test query", [])

    assert len(results) == 1
    assert results[0]["snippets"] == ["Example snippet"]  # Falls back to snippet


def test_web_search_wrapper_file_not_found(tmp_path):
    with patch("os.path.dirname", return_value=str(tmp_path)):
        wrapper = WebSearchAPIWrapper()
        assert not wrapper.generally_unreliable
        assert not wrapper.deprecated
        assert not wrapper.blacklisted


@patch("util.search.DuckDuckGoSearchAPIWrapper")
def test_duckduckgo_adapter_forward_empty_results(mock_ddg_wrapper):
    mock_ddg_wrapper.return_value.results.return_value = []

    ddg_adapter = DuckDuckGoAdapter(k=2)
    results = ddg_adapter.forward("test query", [])

    assert len(results) == 0


@patch("util.search.DuckDuckGoSearchAPIWrapper")
def test_duckduckgo_adapter_forward_fewer_results_than_k(mock_ddg_wrapper):
    mock_ddg_wrapper.return_value.results.return_value = [
        {
            "link": "https://example.com",
            "snippet": "Example snippet",
            "title": "Example Title",
        },
    ]

    ddg_adapter = DuckDuckGoAdapter(k=3)
    results = ddg_adapter.forward("test query", [])

    assert len(results) == 1


@patch("util.search.DuckDuckGoSearchAPIWrapper")
@patch("requests.get")
def test_duckduckgo_search_api_forward_with_unicode_content(
    mock_requests_get, mock_ddg_wrapper
):
    mock_ddg_wrapper.return_value.results.return_value = [
        {
            "link": "https://example.com",
            "snippet": "Unicode snippet 你好",
            "title": "Unicode Title こんにちは",
        },
    ]
    mock_response = MagicMock()
    mock_response.text = "<html><body>Unicode content 안녕하세요</body></html>"
    mock_requests_get.return_value = mock_response

    ddg_api = DuckDuckGoSearchAPI(max_results=1, use_snippet=False)
    results = ddg_api.forward("test query", [])

    assert len(results) == 1
    assert results[0]["snippets"] == ["Unicode content 안녕하세요"]
    assert results[0]["title"] == "Unicode Title こんにちは"


@patch("util.search.DuckDuckGoSearchAPIWrapper")
def test_duckduckgo_adapter_forward_multiple_queries(mock_ddg_wrapper):
    mock_ddg_wrapper.return_value.results.side_effect = [
        [{"link": "https://example1.com", "snippet": "Example 1", "title": "Title 1"}],
        [{"link": "https://example2.com", "snippet": "Example 2", "title": "Title 2"}],
    ]

    ddg_adapter = DuckDuckGoAdapter(k=1)
    results = ddg_adapter.forward(["query1", "query2"], [])

    assert len(results) == 2
    assert results[0]["url"] == "https://example1.com"
    assert results[1]["url"] == "https://example2.com"


# Add a new test for single query behavior
@patch("util.search.DuckDuckGoSearchAPIWrapper")
def test_duckduckgo_adapter_forward_single_query(mock_ddg_wrapper):
    mock_ddg_wrapper.return_value.results.return_value = [
        {
            "link": "https://example.com",
            "snippet": "Example snippet",
            "title": "Example Title",
        },
    ]

    ddg_adapter = DuckDuckGoAdapter(k=1)
    results = ddg_adapter.forward("single query", [])

    assert len(results) == 1
    assert results[0]["url"] == "https://example.com"


# Add a test for empty queries
@patch("util.search.DuckDuckGoSearchAPIWrapper")
def test_duckduckgo_adapter_forward_empty_queries(mock_ddg_wrapper):
    ddg_adapter = DuckDuckGoAdapter(k=1)
    results = ddg_adapter.forward([], [])

    assert len(results) == 0
