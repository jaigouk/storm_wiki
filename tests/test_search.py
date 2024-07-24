import pytest
from unittest.mock import patch, MagicMock
from util.search import WebSearchAPIWrapper, DuckDuckGoSearchAPI, DuckDuckGoAdapter
import dspy


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
        tmp_path /
        "Wikipedia_Reliable sources_Perennial sources - Wikipedia.html")
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


def test_web_search_wrapper_forward(web_search_wrapper):
    with pytest.raises(
        ValueError, match="No RM is loaded. Please load a Retrieval Model first."
    ):
        web_search_wrapper.forward("test query", [])


@patch("util.search.DuckDuckGoSearchAPIWrapper")
@patch("newspaper.Article")
def test_duckduckgo_search_api_forward(mock_article, mock_ddg_wrapper):
    mock_ddg_wrapper.return_value.results.return_value = [
        {
            "link": "https://example.com",
            "snippet": "Example snippet",
            "title": "Example Title",
        },
        {"link": "https://test.com", "snippet": "Test snippet", "title": "Test Title"},
    ]
    mock_article.return_value.text = "Mocked article content"

    ddg_api = DuckDuckGoSearchAPI(max_results=2)
    results = ddg_api.forward("test query", [])

    assert len(results) == 2
    assert results[0]["url"] == "https://example.com"
    assert results[0]["snippets"] == ["Mocked article content"]
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


@patch("newspaper.Article")
@patch("util.search.DuckDuckGoSearchAPIWrapper")
def test_duckduckgo_search_api_forward_with_article_parsing(
    mock_ddg_wrapper, mock_article
):
    mock_ddg_wrapper.return_value.results.return_value = [
        {
            "link": "https://example.com",
            "snippet": "Example snippet",
            "title": "Example Title",
        },
    ]
    mock_article.return_value.text = "Parsed article content"

    ddg_api = DuckDuckGoSearchAPI(max_results=1, use_snippet=False)
    results = ddg_api.forward("test query", [])

    assert len(results) == 1
    assert results[0]["snippets"] == ["Parsed article content"]


@patch("newspaper.Article")
@patch("util.search.DuckDuckGoSearchAPIWrapper")
def test_duckduckgo_search_api_forward_article_parsing_exception(
    mock_ddg_wrapper, mock_article
):
    mock_ddg_wrapper.return_value.results.return_value = [
        {
            "link": "https://example.com",
            "snippet": "Example snippet",
            "title": "Example Title",
        },
    ]
    mock_article.return_value.download.side_effect = Exception(
        "Download failed")

    ddg_api = DuckDuckGoSearchAPI(max_results=1, use_snippet=False)
    results = ddg_api.forward("test query", [])

    assert len(results) == 1
    assert results[0]["snippets"] == [
        "Example snippet"]  # Falls back to snippet


def test_web_search_wrapper_file_not_found(tmp_path):
    with patch("os.path.dirname", return_value=str(tmp_path)):
        wrapper = WebSearchAPIWrapper()
        assert not wrapper.generally_unreliable
        assert not wrapper.deprecated
        assert not wrapper.blacklisted
