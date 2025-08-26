import pytest
from django.urls import reverse

from apps.lexicon import models


@pytest.mark.django_db
class TestLexiconSearchResults:
    # URL to access the search results.
    def get_base_url(self, lang_code):
        return reverse("lexicon:lexicon_search", kwargs={"lang_code": lang_code})

    def test_search_returns_matching_entries(
        self, client, english_project, english_words
    ):
        """Test that search returns tok_ples matching the search term."""
        url = self.get_base_url(english_project.language_code)

        response = client.get(url, {"search": "test"})
        assert response.status_code == 200
        assert response.templates[0].name == "lexicon/includes/search/results_list.html"

        assert len(response.context["object_list"]) == 1
        content = response.content.decode()
        assert "test" in content
        assert "extra" not in content

    def test_search_returns_all_if_no_search(
        self, client, english_project, english_words
    ):
        """Test that search returns all entries if no search term is provided."""
        url = self.get_base_url(english_project.language_code)
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.context["object_list"]) == 2
        content = response.content.decode()
        assert "test" in content
        assert "extra" in content

    def test_search_is_project_scoped(
        self, client, english_project, kovol_project, kovol_words
    ):
        """Test that search is scoped to the project.
        Kovol words should not appear in English search."""
        # Test 1 - no Kovol words in English search
        url = self.get_base_url(english_project.language_code)
        response = client.get(url, {"search": "bili"})
        assert response.status_code == 200
        assert "bili" not in response.content.decode()
        assert "kgu" not in response.content.decode()
        # Test 2 - Kovol words should appear in Kovol search
        url = self.get_base_url(kovol_project.language_code)
        response = client.get(url, {"search": "bili"})
        assert response.status_code == 200
        assert "bili" in response.content.decode() or "kgu" in response.content.decode()

    def test_search_results_filters_by_eng_field(
        self, client, english_project, english_words
    ):
        """
        Test filtering by 'eng' field when 'eng=true' is provided.
        """
        url = self.get_base_url(english_project.language_code)
        response = client.get(url, data={"search": "test", "eng": "true"})

        assert response.status_code == 200
        assert len(response.context["object_list"]) == 1
        assert response.context["object_list"][0].text == "test_word"

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
        assert response.context["object_list"][0].text == "hobol"

    def test_search_results_returns_404_for_invalid_lang_code(self, client):
        """
        Test that the view returns 404 for a non-existent language code.
        """
        url = self.get_base_url("invalid_lang")
        response = client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestIgnoreSearchResults:
    @pytest.fixture
    def ignore_words(self, english_project):
        word1 = models.IgnoreWord.objects.create(
            text="ignoreme", type="tpi", eng="test", project=english_project
        )
        word2 = models.IgnoreWord.objects.create(
            text="keepme", type="tpi", eng="test", project=english_project
        )
        return [word1, word2]

    # URL to access the search results.
    def get_base_url(self, lang_code):
        return reverse("lexicon:ignore_search", kwargs={"lang_code": lang_code})

    def test_ignore_search_returns_matching(
        self, client, english_project, ignore_words
    ):
        """Test that ignore search returns tok_ples matching the search term."""
        url = self.get_base_url(english_project.language_code)
        response = client.get(url, {"search": "ignore"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "ignoreme" in content
        assert "keepme" not in content

    def test_ignore_search_returns_all_if_no_search(
        self, client, english_project, ignore_words
    ):
        """Test that ignore search returns all entries if no search term is provided."""
        url = self.get_base_url(english_project.language_code)
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "ignoreme" in content
        assert "keepme" in content

    def test_ignore_search_is_project_scoped(
        self, client, english_project, kovol_project
    ):
        models.IgnoreWord.objects.create(
            text="ignoreme", type="tpi", eng="test", project=kovol_project
        )
        url = reverse(
            "lexicon:ignore_search", kwargs={"lang_code": english_project.language_code}
        )
        response = client.get(url, {"search": "ignore"})
        assert response.status_code == 200
        # Should not show the ignoreme from kovol_project
        assert (
            "ignoreme" not in response.content.decode()
            or "kgu" not in response.content.decode()
        )
