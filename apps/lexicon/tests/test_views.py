import pytest
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView

from apps.lexicon import models
from apps.lexicon.views import views


@pytest.fixture
def lexicon_projects():
    """Create test lexicon projects"""
    project1 = models.LexiconProject.objects.create(
        language_name="English",
        language_code="eng",
        # Add other required fields based on your model
    )
    project2 = models.LexiconProject.objects.create(
        language_name="Kovol",
        language_code="kgu",
    )
    return [project1, project2]


@pytest.fixture
def english_project():
    """Fixture to create an English project."""
    return models.LexiconProject.objects.create(
        language_code="eng",
        language_name="English",
    )


@pytest.fixture
def english_words(english_project):
    """Fixture to create test words."""
    word1 = models.LexiconEntry.objects.create(
        tok_ples="test_word", eng="test_word_gloss", project=english_project
    )
    word2 = models.LexiconEntry.objects.create(
        tok_ples="extra_word", eng="extra_word_gloss", project=english_project
    )
    return [word1, word2]


@pytest.fixture
def kovol_project():
    """Fixture to create an English project."""
    return models.LexiconProject.objects.create(
        language_code="eng",
        language_name="English",
    )


@pytest.fixture
def kovol_words(kovol_project):
    """Fixture to create test words."""
    word1 = models.LexiconEntry.objects.create(
        tok_ples="hobol", eng="talk", project=kovol_project
    )
    word2 = models.LexiconEntry.objects.create(
        tok_ples="bili", eng="good", project=kovol_project
    )
    return [word1, word2]


@pytest.mark.django_db
class TestProjectList:
    def test_view_uses_correct_template(self, client):
        """Test that the view uses the correct template"""
        response = client.get(reverse("lexicon:project_list"))  # Adjust URL name
        assert response.status_code == 200
        assert response.templates[0].name == "lexicon/project_list.html"

    def test_view_returns_all_projects(self, client, lexicon_projects):
        """Test that all projects are displayed in the context"""
        response = client.get(reverse("lexicon:project_list"))
        assert response.status_code == 200
        assert len(response.context["object_list"]) == 2
        assert (
            len(response.context["lexiconproject_list"]) == 2
        )  # ListView default context name

        # Check that both projects are in the response
        project_names = [p.language_name for p in response.context["object_list"]]
        assert "English" in project_names
        assert "Kovol" in project_names

    def test_empty_project_list(self, client):
        """Test view behavior when no projects exist"""
        response = client.get(reverse("lexicon:project_list"))
        assert response.status_code == 200
        assert len(response.context["object_list"]) == 0

    def test_view_context_contains_expected_data(self, client, lexicon_projects):
        """Test that context contains all expected data"""
        response = client.get(reverse("lexicon:project_list"))

        # Test standard ListView context variables
        assert "object_list" in response.context
        assert "lexiconproject_list" in response.context
        assert "view" in response.context

        content = response.content.decode()
        assert "English" in content
        assert "Kovol" in content


@pytest.mark.django_db
class TestProjectContextMixin:
    """Tests specifically for the ProjectContextMixin."""

    @pytest.fixture
    def mock_view(self):
        """A dummy view inheriting the mixin for isolated testing."""

        class MockView(
            views.ProjectContextMixin, TemplateView
        ):  # we use TemplateView to get the context_data method
            # We need to simulate a request and kwargs for get_project
            def setup(self, request, *args, **kwargs):
                self.request = request
                self.args = args
                self.kwargs = kwargs

        return MockView()

    def test_get_project_success(self, mock_view, english_project, rf):
        """Test get_project method retrieves the correct project.
        Use lexicon:entry_list as the URL to simulate a request."""
        request = rf.get(
            reverse(
                "lexicon:entry_list",
                kwargs={"lang_code": english_project.language_code},
            )
        )
        mock_view.setup(request, lang_code=english_project.language_code)
        project = mock_view.get_project()
        assert project == english_project

    def test_get_project_404_if_not_found(self, mock_view, rf):
        """Test get_project raises Http404 for a non-existent language code.
        Use lexicon:entry_list as the URL to simulate a request."""
        request = rf.get(
            reverse(
                "lexicon:entry_list",
                kwargs={"lang_code": "nonexistent"},
            )
        )
        mock_view.setup(request, lang_code="nonexistent")
        with pytest.raises(Http404):
            mock_view.get_project()

    def test_get_context_data_adds_project_and_lang_code(
        self, mock_view, english_project, rf
    ):
        """Test get_context_data correctly adds project and lang_code to context."""
        request = rf.get(f"/lexicon/{english_project.language_code}/")
        mock_view.setup(request, lang_code=english_project.language_code)

        # When ProjectContextMixin's get_context_data calls super().get_context_data(**kwargs),
        # it will hit the MockView's get_context_data which returns the initial_data.
        context = mock_view.get_context_data(initial_data="test")

        assert "lang_code" in context
        assert context["lang_code"] == english_project.language_code
        assert "project" in context
        assert context["project"] == english_project
        assert context["initial_data"] == "test"  # Ensure existing context is preserved


@pytest.mark.django_db
class TestLexiconView:
    """Tests for the LexiconView."""

    def test_lexicon_view_renders_correctly_with_valid_project(
        self, client, english_project
    ):
        """
        Test that LexiconView renders successfully for a valid project
        and contains all expected context data from both the mixin and the view itself.
        """
        # Construct the URL using reverse to avoid hardcoding
        url = reverse(
            "lexicon:entry_list",
            kwargs={"lang_code": english_project.language_code},
        )
        response = client.get(url)

        # Assert HTTP status code
        assert response.status_code == 200
        # Assert correct template is used
        assert response.templates[0].name == "lexicon/lexicon_list.html"

        # Assert context data from ProjectContextMixin
        context = response.context
        assert "project" in context
        assert context["project"] == english_project
        assert "lang_code" in context
        assert context["lang_code"] == english_project.language_code

        # Assert context data specific to LexiconView
        assert "search_view" in context
        assert context["search_view"] == "lexicon:search"

    def test_lexicon_view_returns_404_for_non_existent_project(self, client):
        """
        Test that LexiconView returns a 404 Not Found error
        when an invalid or non-existent language code is provided.
        This verifies the ProjectContextMixin's get_object_or_404 behavior.
        """
        # Construct a URL with a language code that does not exist
        url = reverse("lexicon:entry_list", kwargs={"lang_code": "nonexistent"})
        response = client.get(url)

        # Assert HTTP status code is 404
        assert response.status_code == 404


@pytest.mark.django_db
class TestSearchResults:
    """Tests for the SearchResults ListView."""

    # URL to access the search results.
    def get_base_url(self, lang_code):
        return reverse("lexicon:search", kwargs={"lang_code": lang_code})

    def test_search_results_renders_correctly_no_search(
        self, client, english_project, english_words
    ):
        """
        Test that the view renders correctly with no search query,
        returning all entries for the specified project.
        """
        url = self.get_base_url(english_project.language_code)
        response = client.get(url)

        assert response.status_code == 200
        assert response.templates[0].name == "lexicon/includes/search-results.html"

        # Should contain both English entries
        assert "object_list" in response.context
        assert len(response.context["object_list"]) == 2
        found_entries_tokples = {e.tok_ples for e in response.context["object_list"]}
        assert "test_word" in found_entries_tokples
        assert "extra_word" in found_entries_tokples

    def test_search_results_filters_by_tok_ples_default(
        self, client, english_project, english_words
    ):
        """
        Test filtering by 'tok_ples' when 'eng' is not true or not provided.
        """
        url = self.get_base_url(english_project.language_code)
        response = client.get(url, data={"search": "test"})  # Search for 'test'

        assert response.status_code == 200
        assert len(response.context["object_list"]) == 1
        assert response.context["object_list"][0].tok_ples == "test_word"

    def test_search_results_filters_by_eng_field(
        self, client, english_project, english_words
    ):
        """
        Test filtering by 'eng' field when 'eng=true' is provided.
        """
        url = self.get_base_url(english_project.language_code)
        response = client.get(
            url, data={"search": "test", "eng": "true"}
        )  # Search for 'sample' in English

        assert response.status_code == 200
        assert len(response.context["object_list"]) == 1
        found_entries_eng = {e.eng for e in response.context["object_list"]}
        assert "test_word_gloss" in found_entries_eng

    def test_search_results_no_matches(self, client, english_project, english_words):
        """
        Test that an empty queryset is returned when no matches are found.
        """
        url = self.get_base_url(english_project.language_code)
        response = client.get(url, data={"search": "nonexistent_word"})

        assert response.status_code == 200
        assert len(response.context["object_list"]) == 0

    def test_search_results_filters_by_project_and_search(
        self, client, kovol_project, kovol_words
    ):
        """
        Test that entries are correctly filtered by both project and search query,
        ensuring entries from other projects are not returned.
        """
        url = self.get_base_url(kovol_project.language_code)  # Target Kovol project
        response = client.get(url, data={"search": "hobol"})  # Search for 'kgu_test'

        assert response.status_code == 200
        assert len(response.context["object_list"]) == 1
        assert response.context["object_list"][0].tok_ples == "hobol"

    def test_search_results_returns_404_for_invalid_lang_code(self, client):
        """
        Test that the view returns 404 for a non-existent language code.
        """
        url = self.get_base_url("invalid_lang")
        response = client.get(url)
        assert response.status_code == 404
