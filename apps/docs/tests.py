
import pytest
from unittest import mock
from .views import DocPageView


@pytest.fixture
def view_instance():
    return DocPageView()


def test_create_toc_data(view_instance):
    """Tests the creation of the table of contents data."""
    files = ["doc_intro.md", "doc_usage.md", "doc_api.md", "not_markdown.txt"]
    with mock.patch("os.listdir", return_value=files):
        toc = view_instance.create_toc_data()
        expected = [
            {"file": "doc_api", "name": "api"},
            {"file": "doc_intro", "name": "intro"},
            {"file": "doc_usage", "name": "usage"},
        ]
        assert toc == expected


def test_get_context_data_renders_markdown(view_instance):
    """Tests that markdown content is correctly rendered to HTML."""
    dummy_md = "# Title\nSome text"
    expected_html = "<h1>Title</h1>\n<p>Some text</p>"
    view_instance.kwargs = {"page_name": "doc_intro"}
    with (
        mock.patch("builtins.open", mock.mock_open(read_data=dummy_md)),
        mock.patch.object(
            DocPageView,
            "create_toc_data",
            return_value=[{"file": "doc_intro", "name": "intro"}],
        ),
    ):
        context = view_instance.get_context_data()
        assert "content" in context
        assert expected_html in context["content"]
        assert context["toc"] == [{"file": "doc_intro", "name": "intro"}]


def test_get_context_data_file_not_found(view_instance):
    """Tests handling of a missing markdown file."""
    view_instance.kwargs = {"page_name": "missing_doc"}
    with (
        mock.patch("builtins.open", side_effect=FileNotFoundError),
        mock.patch.object(DocPageView, "create_toc_data", return_value=[]),
    ):
        context = view_instance.get_context_data()
        assert context["content"] == "<h2>Documentation not found</h2>"
        assert context["toc"] == []