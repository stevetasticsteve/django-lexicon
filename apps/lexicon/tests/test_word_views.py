import pytest
from django.contrib.auth.models import User
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView

from apps.lexicon import models
from apps.lexicon.views import word_views


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
def english_words_with_paradigm(english_project):
    """Fixture to create test words and a paradigm."""
    word1 = models.LexiconEntry.objects.create(
        tok_ples="test_word", eng="test_word_gloss", project=english_project
    )
    word2 = models.LexiconEntry.objects.create(
        tok_ples="extra_word", eng="extra_word_gloss", project=english_project
    )
    paradigm = models.Paradigm.objects.create(
        name="Test Paradigm",
        row_labels=["row1"],
        column_labels=["col1"],
        project=english_project,
    )
    word1.paradigms.add(paradigm)
    conjugation = models.Conjugation.objects.create(
        word=word1, paradigm=paradigm, row=0, column=0, conjugation="test"
    )
    return [word1, word2], paradigm, conjugation


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


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass")


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
            word_views.ProjectContextMixin, TemplateView
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
        assert "test_word" in response.content.decode()

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


@pytest.mark.django_db
class TestEntryDetail:
    def test_entry_detail_view_success(self, client, english_project, english_words):
        """Test that the entry detail view returns 200 and correct context for a valid entry."""
        entry = english_words[0]
        url = reverse(
            "lexicon:entry_detail",
            kwargs={"lang_code": english_project.language_code, "pk": entry.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["object"] == entry
        assert "conjugations" in response.context
        assert "paradigms" in response.context

    def test_entry_detail_view_contents(self, client, english_project, english_words):
        """Test that the entry detail view contains expected content."""
        entry = english_words[0]
        url = reverse(
            "lexicon:entry_detail",
            kwargs={"lang_code": english_project.language_code, "pk": entry.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert entry.tok_ples in content
        assert entry.eng in content

    def test_entry_detail_view_404(self, client, english_project):
        """Test that the entry detail view returns 404 for a non-existent entry."""
        url = reverse(
            "lexicon:entry_detail",
            kwargs={"lang_code": english_project.language_code, "pk": 9999},
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_entry_detail_conjugations_and_paradigms(
        self, client, english_project, english_words_with_paradigm
    ):
        words, paradigm, conjugation = english_words_with_paradigm
        entry = words[0]
        url = reverse(
            "lexicon:entry_detail",
            kwargs={"lang_code": english_project.language_code, "pk": entry.pk},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert conjugation in response.context["conjugations"]
        assert paradigm in response.context["paradigms"]


@pytest.mark.django_db
class TestCreateEntry:
    def get_create_url(self, english_project):
        return reverse(
            "lexicon:create_entry", kwargs={"lang_code": english_project.language_code}
        )

    def test_create_entry_get(self, client, english_project, user):
        """GET request should render the form."""
        client.force_login(user)
        url = self.get_create_url(english_project)
        response = client.get(url)
        assert response.status_code == 200
        assert "form" in response.context
        assert "tok_ples" in response.content.decode()

    def test_create_entry_post_success(self, client, english_project, user):
        """POST valid data should create a new LexiconEntry and redirect."""
        client.force_login(user)
        url = self.get_create_url(english_project)
        data = {
            "tok_ples": "new_word",
            "eng": "new_word_gloss",
            "oth_lang": "",
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
        }
        response = client.post(url, data)
        # Should redirect after successful creation
        assert response.status_code == 302
        # The entry should exist in the database
        assert models.LexiconEntry.objects.filter(
            tok_ples="new_word", project=english_project
        ).exists()

    def test_create_entry_missing_required_field(self, client, english_project, user):
        """POST missing required field should return form with errors."""
        client.force_login(user)
        url = self.get_create_url(english_project)
        data = {
            # "tok_ples" is missing
            "eng": "missing_word",
            "oth_lang": "",
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
        }
        response = client.post(url, data)
        assert response.status_code == 200  # Form re-rendered with errors
        assert "This field is required" in response.content.decode()
        assert not models.LexiconEntry.objects.filter(
            eng="missing_word", project=english_project
        ).exists()

    def test_create_entry_sets_modified_by(self, client, english_project, user):
        """The created entry should have modified_by set to the username."""
        client.force_login(user)
        url = self.get_create_url(english_project)
        data = {
            "tok_ples": "audit_word",
            "eng": "audit_gloss",
            "oth_lang": "",
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
        }
        client.post(url, data)
        entry = models.LexiconEntry.objects.get(
            tok_ples="audit_word", project=english_project
        )
        assert entry.modified_by == user.username


@pytest.mark.django_db
class TestUpdateEntry:
    @pytest.fixture
    def entry(self, english_project):
        return models.LexiconEntry.objects.create(
            tok_ples="update_me",
            eng="update_me_gloss",
            project=english_project,
            checked=False,
            review=0,
        )

    def get_update_url(self, english_project, entry):
        return reverse(
            "lexicon:update_entry",
            kwargs={"lang_code": english_project.language_code, "pk": entry.pk},
        )

    def test_update_entry_get(self, client, english_project, entry, user):
        """GET request should render the update form."""
        client.force_login(user)
        url = self.get_update_url(english_project, entry)
        response = client.get(url)
        assert response.status_code == 200
        assert "form" in response.context
        assert entry.tok_ples in response.content.decode()

    def test_update_entry_post_success(self, client, english_project, entry, user):
        """POST valid data should update the entry and redirect."""
        client.force_login(user)
        url = self.get_update_url(english_project, entry)
        data = {
            "tok_ples": "updated_word",
            "eng": "updated_gloss",
            "oth_lang": "",
            "pos": "",
            "comments": "Updated via test",
            "checked": True,
            "review": 0,
            "review_comments": "",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        entry.refresh_from_db()
        assert entry.tok_ples == "updated_word"
        assert entry.eng == "updated_gloss"
        assert entry.comments == "Updated via test"
        assert entry.modified_by == user.username

    def test_update_entry_missing_required_field(
        self, client, english_project, entry, user
    ):
        """POST missing required field should return form with errors."""
        client.force_login(user)
        url = self.get_update_url(english_project, entry)
        data = {
            # "tok_ples" is missing
            "eng": "should_fail",
            "oth_lang": "",
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
        }
        response = client.post(url, data)
        assert response.status_code == 200  # Form re-rendered with errors
        assert "This field is required" in response.content.decode()
        entry.refresh_from_db()
        assert entry.eng != "should_fail"

    def test_update_entry_sets_review_user(self, client, english_project, entry, user):
        """If review is changed, review_user and review_time should be set."""
        client.force_login(user)
        url = self.get_update_url(english_project, entry)
        data = {
            "tok_ples": entry.tok_ples,
            "eng": entry.eng,
            "oth_lang": "",
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 1,  # Change review value
            "review_comments": "",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        entry.refresh_from_db()
        assert entry.review_user == user.username
        assert entry.review_time is not None
