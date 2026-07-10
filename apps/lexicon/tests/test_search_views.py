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


@pytest.mark.django_db
class TestLexiconSearchResultsRegex:
    def get_base_url(self, lang_code):
        return reverse("lexicon:lexicon_search", kwargs={"lang_code": lang_code})

    def test_regex_search_matches_pattern(self, client, kovol_project, kovol_words):
        """'^ho' should match 'hobol' but not 'bili'."""
        url = self.get_base_url(kovol_project.language_code)
        response = client.get(url, {"search": "^ho", "regex": "true"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "hobol" in content
        assert "bili" not in content

    def test_regex_search_is_case_insensitive(self, client, kovol_project, kovol_words):
        """iregex is used, so uppercase pattern still matches lowercase text."""
        url = self.get_base_url(kovol_project.language_code)
        response = client.get(url, {"search": "^HO", "regex": "true"})
        assert response.status_code == 200
        assert "hobol" in response.content.decode()

    def test_regex_search_alternation(self, client, kovol_project, kovol_words):
        """Pattern should match either word via alternation."""
        url = self.get_base_url(kovol_project.language_code)
        response = client.get(url, {"search": "^(hobol|bili)$", "regex": "true"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "hobol" in content
        assert "bili" in content

    def test_regex_search_character_class_and_anchor(self, client, kovol_project):
        """The motivating example: [ie]nd$ should match 'ind' and 'end' endings."""
        models.LexiconEntry.objects.create(text="fasind", project=kovol_project)
        models.LexiconEntry.objects.create(text="lokend", project=kovol_project)
        models.LexiconEntry.objects.create(text="wapan", project=kovol_project)

        url = self.get_base_url(kovol_project.language_code)
        response = client.get(url, {"search": "[ie]nd$", "regex": "true"})
        assert response.status_code == 200
        content = response.content.decode()
        assert "fasind" in content
        assert "lokend" in content
        assert "wapan" not in content

    def test_invalid_regex_returns_error_not_500(
        self, client, kovol_project, kovol_words
    ):
        """An unclosed bracket is invalid Python regex and should be caught
        before hitting the DB."""
        url = self.get_base_url(kovol_project.language_code)
        response = client.get(url, {"search": "[invalid", "regex": "true"})
        assert response.status_code == 200
        assert response.context["search_error"] is not None
        assert "Invalid regex" in response.context["search_error"]
        assert len(response.context["object_list"]) == 0

    def test_regex_search_too_long_returns_error(
        self, client, kovol_project, kovol_words
    ):
        url = self.get_base_url(kovol_project.language_code)
        long_search = "a" * 200
        response = client.get(url, {"search": long_search, "regex": "true"})
        assert response.status_code == 200
        assert response.context["search_error"] is not None
        assert "too long" in response.context["search_error"]
        assert len(response.context["object_list"]) == 0

    def test_regex_search_on_english_field(
        self, client, english_project, english_words
    ):
        """regex=true combined with eng=true should search senses.eng."""
        url = self.get_base_url(english_project.language_code)
        response = client.get(url, {"search": "^test", "eng": "true", "regex": "true"})
        assert response.status_code == 200
        assert len(response.context["object_list"]) == 1
        assert response.context["object_list"][0].text == "test_word"

    def test_non_regex_search_treats_special_chars_literally(
        self, client, kovol_project
    ):
        """When regex is off, icontains should not interpret regex metacharacters —
        guards against regex=false accidentally taking the regex path."""
        models.LexiconEntry.objects.create(text="a.b", project=kovol_project)
        models.LexiconEntry.objects.create(text="axb", project=kovol_project)

        url = self.get_base_url(kovol_project.language_code)
        response = client.get(url, {"search": "a.b"})  # no regex param
        assert response.status_code == 200
        content = response.content.decode()
        assert "a.b" in content
        assert "axb" not in content  # would match if '.' were treated as regex wildcard
