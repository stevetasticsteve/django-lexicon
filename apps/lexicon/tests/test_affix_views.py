import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAffixViews:
    def test_affix_tester_renders_affix_file(self, client, english_project, user):
        """Test that the affix tester view renders the affix file."""
        english_project.affix_file = "SFX A Y 1\nSFX A 0 ing ."
        english_project.save()
        client.force_login(user)
        url = reverse("lexicon:affix_tester", args=[english_project.language_code])
        response = client.get(url)
        assert response.status_code == 200
        assert "affix_file" in response.context
        assert "SFX A" in response.context["affix_file"]

    def test_affix_results_success(self, client, monkeypatch, english_project, user):
        """Test that the affix results view returns generated words."""
        # Patch hunspell.unmunch to return a predictable result
        monkeypatch.setattr(
            "apps.lexicon.utils.hunspell.unmunch",
            lambda words, affix: ["walked", "walking"]
            if words == "walk" and affix == "SFX"
            else [],
        )
        client.force_login(user)
        url = reverse("lexicon:affix_results", args=[english_project.language_code])
        response = client.get(url, {"words": "walk", "affix": "SFX"})
        assert response.status_code == 200
        assert "generated_words" in response.context
        assert "walked" in response.context["generated_words"]
        assert "walking" in response.context["generated_words"]

    def test_affix_results_error(self, client, monkeypatch, english_project, user):
        """Test that the affix results view handles errors gracefully."""
        # Patch hunspell.unmunch to raise an exception
        def raise_error(words, affix):
            raise ValueError("bad affix")

        monkeypatch.setattr("apps.lexicon.utils.hunspell.unmunch", raise_error)
        client.force_login(user)
        url = reverse("lexicon:affix_results", args=[english_project.language_code])
        response = client.get(url, {"words": "walk", "affix": "bad"})
        assert response.status_code == 500
        assert (
            response.json()["error"]
            == "An error occurred while processing the affixes."
        )
        assert "bad affix" in response.json()["details"]
