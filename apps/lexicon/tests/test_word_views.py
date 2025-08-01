import pytest
from django.db.utils import IntegrityError
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from guardian.shortcuts import assign_perm

from apps.lexicon import models
from apps.lexicon.views import word_views


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
        assert entry.text in content
        eng = models.Sense.objects.filter(entry=entry).first().eng
        assert eng in content

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

    def test_create_entry_get(self, client, english_project, permissioned_user):
        """GET request should render the form."""
        client.force_login(permissioned_user)
        url = self.get_create_url(english_project)
        response = client.get(url)
        assert response.status_code == 200
        assert "form" in response.context
        assert "text" in response.content.decode()
        assert "senses" in response.content.decode()

    def test_create_entry_post_success(
        self, client, english_project, permissioned_user
    ):
        """POST valid data should create a new LexiconEntry and redirect."""
        client.force_login(permissioned_user)
        url = self.get_create_url(english_project)
        data = {
            "text": "new_word",
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
            "senses-TOTAL_FORMS": 1,
            "senses-INITIAL_FORMS": 0,
            "senses-MIN_NUM_FORMS": 1,
            "senses-MAX_NUM_FORMS": 1000,
            "senses-0-eng": "new_word_gloss",
            "senses-0-oth_lang": "",
            "senses-0-order": 1,
            "senses-0-example": "",
        }
        response = client.post(url, data)

        # Should redirect after successful creation
        assert response.status_code == 302
        # The entry should exist in the database
        assert models.LexiconEntry.objects.filter(
            text="new_word", project=english_project
        ).exists()
        assert models.Sense.objects.filter(eng="new_word_gloss").exists()

    def test_create_entry_missing_required_field(
        self, client, english_project, permissioned_user
    ):
        """POST missing required field should return form with errors."""
        client.force_login(permissioned_user)
        url = self.get_create_url(english_project)
        data = {
            # "text" is missing
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
            
        }
        response = client.post(url, data)
        assert response.status_code == 200  # Form re-rendered with errors
        assert "This field is required" in response.content.decode()

    def test_create_entry_fails_without_senseform(self, client, english_project, permissioned_user):
        """POST without any sense form should return form with errors."""
        client.force_login(permissioned_user)
        url = self.get_create_url(english_project)
        data = {
            "text": "no_sense_word",
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
            # No senses data at all
        }
        response = client.post(url, data)
        assert response.status_code == 200
        assert "This field is required" in response.content.decode()

    def test_create_entry_handles_multiple_senses(
        self, client, english_project, permissioned_user
    ):
        """POST with multiple senses should create them correctly."""
        client.force_login(permissioned_user)
        url = self.get_create_url(english_project)
        data = {
            "text": "multi_sense_word",
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
            "senses-TOTAL_FORMS": 2,
            "senses-INITIAL_FORMS": 0,
            "senses-MIN_NUM_FORMS": 1,
            "senses-MAX_NUM_FORMS": 1000,
            "senses-0-eng": "first_gloss",
            "senses-0-oth_lang": "",
            "senses-0-order": 1,
            "senses-0-example": "",
            "senses-1-eng": "second_gloss",
            "senses-1-oth_lang": "",
            "senses-1-order": 2,
            "senses-1-example": "",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        # Check both senses were created
        assert models.Sense.objects.filter(eng="first_gloss").exists()
        assert models.Sense.objects.filter(eng="second_gloss").exists()

    def test_create_entry_sets_modified_by(
        self, client, english_project, permissioned_user
    ):
        """The created entry should have modified_by set to the username."""
        client.force_login(permissioned_user)
        url = self.get_create_url(english_project)
        data = {
            "text": "audit_word",
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
            "senses-TOTAL_FORMS": 1,
            "senses-INITIAL_FORMS": 0,
            "senses-MIN_NUM_FORMS": 1,
            "senses-MAX_NUM_FORMS": 1000,
            "senses-0-eng": "new_word_gloss",
            "senses-0-oth_lang": "",
            "senses-0-order": 1,
            "senses-0-example": "",
        }
        client.post(url, data)
        entry = models.LexiconEntry.objects.get(
            text="audit_word", project=english_project
        )
        assert entry.modified_by == permissioned_user.username

    def test_create_entry_scope_limited(
        self, client, english_words, english_project, kovol_project, permissioned_user
    ):
        """Created entries should be unique within projects only. The unique
        constraint shouldn't affect other projects"""
        client.force_login(permissioned_user)
        url = self.get_create_url(kovol_project)
        data = {
            "text": "test_word",
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
            "senses-TOTAL_FORMS": 1,
            "senses-INITIAL_FORMS": 0,
            "senses-MIN_NUM_FORMS": 1,
            "senses-MAX_NUM_FORMS": 1000,
            "senses-0-eng": "new_word_gloss",
            "senses-0-oth_lang": "",
            "senses-0-order": 1,
            "senses-0-example": "",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert models.LexiconEntry.objects.filter(
            project=kovol_project, text="test_word"
        )
        assert models.LexiconEntry.objects.filter(
            project=english_project, text="test_word"
        )
        assert models.LexiconEntry.objects.filter(text="test_word").count() == 2

    def test_text_unique_within_project(
        self, client, english_words, english_project, permissioned_user
    ):
        """Test the unique constraint for tok_ples within a project holds."""
        client.force_login(permissioned_user)
        url = self.get_create_url(english_project)
        data = {
            "text": "test_word",
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
            "senses-TOTAL_FORMS": 1,
            "senses-INITIAL_FORMS": 0,
            "senses-MIN_NUM_FORMS": 1,
            "senses-MAX_NUM_FORMS": 1000,
            "senses-0-eng": "new_word_gloss",
            "senses-0-oth_lang": "",
            "senses-0-order": 1,
            "senses-0-example": "",
        }
        with pytest.raises(IntegrityError):
            response = client.post(url, data)
            assert response.status_code == 200
            assert (
                "Lexicon entry with this Project and Tok Ples already exists."
                in response.content.decode()
            )
            assert models.LexiconEntry.objects.filter(text="test_word").count() == 1

    def test_create_entry_invalid_text_chars(self, client, permissioned_user):
        """
        POST data with tok_ples violating the project's regex validator
        should re-render the form with validation errors and not save the entry.
        """
        client.force_login(permissioned_user)

        # 1. Create a project with a specific tok_ples_validator
        # Only allows lowercase letters
        project_with_validator = models.LexiconProject.objects.create(
            language_name="Validated Lang",
            language_code="vld",
            text_validator="^[a-z]+$",
        )
        assign_perm("edit_lexiconproject", permissioned_user, project_with_validator)

        url = self.get_create_url(project_with_validator)

        # Data with invalid characters (space, number, uppercase)
        invalid_data = {
            "text": "Invalid Word 123",
            "oth_lang": "",
            "pos": "n",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
        }

        response = client.post(url, invalid_data)

        # 2. Assert status code is 200 (form re-rendered with errors)
        assert response.status_code == 200

        # 3. Assert the validation error message is present
        # Note: HTML encoding might convert ' (apostrophe) to &#x27; or &apos;
        assert (
            "&#x27;invalid word 123&#x27; contains unallowed characters. A project admin set this restriction."
            in response.content.decode()
        )
        # 4. Assert that no LexiconEntry was created for this project
        assert not models.LexiconEntry.objects.filter(
            text="invalid word 123", project=project_with_validator
        ).exists()  # Note: tok_ples is lowercased on save if it ever got there


@pytest.mark.django_db
class TestUpdateEntry:
    @pytest.fixture
    def entry(self, english_project):
        return models.LexiconEntry.objects.create(
            text="update_me",
            project=english_project,
            checked=False,
            review=0,
        )

    def get_update_url(self, english_project, entry):
        return reverse(
            "lexicon:update_entry",
            kwargs={"lang_code": english_project.language_code, "pk": entry.pk},
        )

    def test_update_entry_get(self, client, english_project, entry, permissioned_user):
        """GET request should render the update form."""
        client.force_login(permissioned_user)
        url = self.get_update_url(english_project, entry)
        response = client.get(url)
        assert response.status_code == 200
        assert "form" in response.context
        assert entry.text in response.content.decode()

    def test_update_entry_post_success(
        self, client, english_project, entry, permissioned_user
    ):
        """POST valid data should update the entry and redirect."""
        client.force_login(permissioned_user)
        url = self.get_update_url(english_project, entry)
        data = {
            "text": "updated_word",
            "pos": "",
            "comments": "Updated via test",
            "checked": True,
            "review": 0,
            "review_comments": "",
            "senses-TOTAL_FORMS": 1,
            "senses-INITIAL_FORMS": 0,
            "senses-MIN_NUM_FORMS": 1,
            "senses-MAX_NUM_FORMS": 1000,
            "senses-0-eng": "new_word_gloss",
            "senses-0-oth_lang": "",
            "senses-0-order": 1,
            "senses-0-example": "",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        entry.refresh_from_db()
        assert entry.text == "updated_word"
        assert entry.comments == "Updated via test"
        assert entry.modified_by == permissioned_user.username

    def test_update_entry_missing_required_field(
        self, client, english_project, entry, permissioned_user
    ):
        """POST missing required field should return form with errors."""
        client.force_login(permissioned_user)
        url = self.get_update_url(english_project, entry)
        data = {
            # "text" is missing
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
            "senses-TOTAL_FORMS": 1,
            "senses-INITIAL_FORMS": 0,
            "senses-MIN_NUM_FORMS": 1,
            "senses-MAX_NUM_FORMS": 1000,
            "senses-0-eng": "new_word_gloss",
            "senses-0-oth_lang": "",
            "senses-0-order": 1,
            "senses-0-example": "",
        }
        response = client.post(url, data)
        assert response.status_code == 200  # Form re-rendered with errors
        assert "This field is required" in response.content.decode()
        entry.refresh_from_db()
    
    def test_update_entry_can_delete_sense(
        self, client, english_project, entry, permissioned_user
    ):
        """POST with a sense marked for deletion should remove it."""
        client.force_login(permissioned_user)
        url = self.get_update_url(english_project, entry)
        # Create an initial sense to delete
        sense = models.Sense.objects.create(
            entry=entry, eng="keep_me", oth_lang="", order=1, example=""
        )
        delete_sense = models.Sense.objects.create(
            entry=entry, eng="to_delete", oth_lang="", order=2, example=""
        )
        data = {
            "text": "updated_word",
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
            "senses-TOTAL_FORMS": 2,
            "senses-INITIAL_FORMS": 2,
            "senses-MIN_NUM_FORMS": 1,
            "senses-MAX_NUM_FORMS": 1000,
            # Form 0 (to keep)
            "senses-0-eng": sense.eng,
            "senses-0-oth_lang": sense.oth_lang,
            "senses-0-order": sense.order,
            "senses-0-example": sense.example,
            "senses-0-id": sense.pk,
            # Form 1 (to delete)
            "senses-1-eng": delete_sense.eng,
            "senses-1-oth_lang": delete_sense.oth_lang,
            "senses-1-order": delete_sense.order,
            "senses-1-example": delete_sense.example,
            "senses-1-id": delete_sense.pk,
            "senses-1-entry": entry.pk,
            "senses-1-DELETE": "on",  # Mark for deletion
        }
        response = client.post(url, data)
        print(models.Sense.objects.all())

        assert response.status_code == 302
        assert not models.Sense.objects.filter(pk=delete_sense.pk).exists()

    def test_update_entry_sets_review_user(
        self, client, english_project, entry, permissioned_user
    ):
        """If review is changed, review_user and review_time should be set."""
        client.force_login(permissioned_user)
        url = self.get_update_url(english_project, entry)
        data = {
            "text": entry.text,
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 1,  # Change review value
            "review_comments": "",
            "senses-TOTAL_FORMS": 1,
            "senses-INITIAL_FORMS": 0,
            "senses-MIN_NUM_FORMS": 1,
            "senses-MAX_NUM_FORMS": 1000,
            "senses-0-eng": "new_word_gloss",
            "senses-0-oth_lang": "",
            "senses-0-order": 1,
            "senses-0-example": "",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        entry.refresh_from_db()
        assert entry.review_user == permissioned_user.username
        assert entry.review_time is not None

    def test_update_entry_invalid_text_chars(self, client, permissioned_user):
        """
        POST data to update an entry with tok_ples violating the project's regex validator
        should re-render the form with validation errors and not update the entry.
        """
        client.force_login(permissioned_user)

        # 1. Create a project with a specific txt_validator
        project_with_validator = models.LexiconProject.objects.create(
            language_name="Validated Update Lang",
            language_code="vul",
            text_validator="^[a-z]+$",  # Only allows lowercase letters
        )
        assign_perm("edit_lexiconproject", permissioned_user, project_with_validator)

        # 2. Create an initial, valid entry for this project
        original_text = "validword"
        entry_to_update = models.LexiconEntry.objects.create(
            text=original_text,
            project=project_with_validator,
            checked=False,
            review=0,
        )

        url = self.get_update_url(project_with_validator, entry_to_update)

        # Data with an invalid tok_ples (contains spaces, numbers, uppercase)
        invalid_text_attempt = "Invalid Word 456"
        data = {
            "text": invalid_text_attempt,  # This violates the regex
            "oth_lang": "",
            "pos": "n",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
        }

        response = client.post(url, data)

        # 3. Assert status code is 200 (form re-rendered with errors)
        assert response.status_code == 200
        print(response.content.decode())

        # 4. Assert the validation error message is present
        assert (
            "contains unallowed characters. A project admin set this restriction."
            in response.content.decode()
        )

        # 5. Assert that the entry in the database was NOT updated
        entry_to_update.refresh_from_db()  # Get the latest state from the database
        assert entry_to_update.text == original_text  # Should still be the original



@pytest.mark.django_db
class TestDeleteEntry:
    @pytest.fixture
    def entry(self, english_project):
        return models.LexiconEntry.objects.create(
            text="delete_me",
            project=english_project,
            checked=False,
            review=0,
        )

    def get_delete_url(self, english_project, entry):
        return reverse(
            "lexicon:delete_entry",
            kwargs={"lang_code": english_project.language_code, "pk": entry.pk},
        )

    def test_delete_entry_get_confirmation(
        self, client, english_project, entry, permissioned_user
    ):
        """GET should render the confirmation page for deletion."""
        client.force_login(permissioned_user)
        url = self.get_delete_url(english_project, entry)
        response = client.get(url)
        assert response.status_code == 200
        assert "yes, delete it" in response.content.decode().lower()

    def test_delete_entry_post_success(
        self, client, english_project, entry, permissioned_user
    ):
        """POST should delete the entry and redirect to the entry list."""
        client.force_login(permissioned_user)
        url = self.get_delete_url(english_project, entry)
        response = client.post(url)
        # Should redirect after deletion
        assert response.status_code == 302
        # The entry should no longer exist
        assert not models.LexiconEntry.objects.filter(pk=entry.pk).exists()

    def test_delete_entry_requires_login(self, client, english_project, entry):
        """Anonymous users should be redirected to login."""
        url = self.get_delete_url(english_project, entry)
        response = client.get(url)
        # Should redirect to login page (default 302)
        assert response.status_code == 302
        assert "/login" in response.url or "/accounts/login" in response.url


@pytest.mark.django_db
class TestReviewList:
    def get_review_list_url(self, english_project):
        return reverse(
            "lexicon:review_list", kwargs={"lang_code": english_project.language_code}
        )

    @pytest.fixture
    def reviewed_entries(self, english_project):
        """Create entries with and without review marks."""
        reviewed = models.LexiconEntry.objects.create(
            text="needs_review",
            project=english_project,
            review=1,
        )
        not_reviewed = models.LexiconEntry.objects.create(
            text="no_review",
            project=english_project,
            review=0,
        )
        return reviewed, not_reviewed

    def test_review_list_shows_only_reviewed(
        self, client, english_project, reviewed_entries
    ):
        """Only entries with review > 0 are shown."""
        reviewed, not_reviewed = reviewed_entries
        url = self.get_review_list_url(english_project)
        response = client.get(url)
        assert response.status_code == 200
        # Only the reviewed entry should be in the object_list
        object_list = response.context["object_list"]
        assert reviewed in object_list
        assert not_reviewed not in object_list
        # Content check
        content = response.content.decode()
        assert reviewed.text in content
        assert not_reviewed.text not in content

    def test_review_list_uses_correct_template(
        self, client, english_project, reviewed_entries
    ):
        url = self.get_review_list_url(english_project)
        response = client.get(url)
        assert response.status_code == 200
        assert response.templates[0].name == "lexicon/review_list.html"

    def test_review_list_context_contains_project_and_lang_code(
        self, client, english_project, reviewed_entries
    ):
        url = self.get_review_list_url(english_project)
        response = client.get(url)
        context = response.context
        assert "project" in context
        assert context["project"] == english_project
        assert "lang_code" in context
        assert context["lang_code"] == english_project.language_code

    def test_review_list_returns_404_for_nonexistent_project(self, client):
        url = reverse("lexicon:review_list", kwargs={"lang_code": "nonexistent"})
        response = client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestAddSenseForm:
    def test_add_sense_form_get_request(self, client):
        """Test that a GET request to add_sense_form returns a new form."""
        url = reverse("lexicon:add-sense-form")
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        # Check for some form fields. The prefix should default to senses-0
        assert 'name="senses-0-eng"' in content
        assert 'name="senses-0-oth_lang"' in content
        assert 'name="senses-0-example"' in content
        assert 'name="senses-0-order"' in content

    def test_add_sense_form_with_form_count(self, client):
        """Test that the form_count parameter correctly sets the form prefix."""
        url = reverse("lexicon:add-sense-form")
        response = client.get(url, {"form_count": "3"})
        assert response.status_code == 200
        content = response.content.decode()
        # The prefix should be senses-3
        assert 'name="senses-3-eng"' in content
        assert 'name="senses-3-oth_lang"' in content
        assert 'name="senses-3-example"' in content
        assert 'name="senses-3-order"' in content

    def test_add_sense_form_disallows_post(self, client):
        """Test that POST requests are not allowed."""
        url = reverse("lexicon:add-sense-form")
        response = client.post(url)
        assert response.status_code == 405  # Method Not Allowed


@pytest.mark.django_db
class TestEntryPermissions:
    def get_create_url(self, project):
        return reverse(
            "lexicon:create_entry", kwargs={"lang_code": project.language_code}
        )

    def get_update_url(self, project, entry):
        return reverse(
            "lexicon:update_entry",
            kwargs={"lang_code": project.language_code, "pk": entry.pk},
        )

    def get_delete_url(self, project, entry):
        return reverse(
            "lexicon:delete_entry",
            kwargs={"lang_code": project.language_code, "pk": entry.pk},
        )

    def test_create_entry_forbidden(self, client, english_project, user):
        client.force_login(user)
        url = self.get_create_url(english_project)
        data = {
            "text": "forbidden_word",
            "eng": "forbidden_gloss",
            "oth_lang": "",
            "pos": "",
            "comments": "",
            "checked": False,
            "review": 0,
            "review_comments": "",
        }
        response = client.post(url, data)
        assert response.status_code == 403
        assert not models.LexiconEntry.objects.filter(
            text="forbidden_word", project=english_project
        ).exists()

    def test_update_entry_forbidden(self, client, english_project, user):
        entry = models.LexiconEntry.objects.create(
            text="forbidden_update",
            project=english_project,
            checked=False,
            review=0,
        )
        client.force_login(user)
        url = self.get_update_url(english_project, entry)
        data = {
            "text": "should_not_update",
            "eng": "should_not_update",
            "oth_lang": "",
            "pos": "",
            "comments": "",
            "checked": True,
            "review": 0,
            "review_comments": "",
        }
        response = client.post(url, data)
        assert response.status_code == 403
        entry.refresh_from_db()
        assert entry.text == "forbidden_update"

    def test_delete_entry_forbidden(self, client, english_project, user):
        entry = models.LexiconEntry.objects.create(
            text="forbidden_delete",
            project=english_project,
            checked=False,
            review=0,
        )
        client.force_login(user)
        url = self.get_delete_url(english_project, entry)
        response = client.post(url)
        assert response.status_code == 403
        assert models.LexiconEntry.objects.filter(pk=entry.pk).exists()
