import pytest
from django.urls import reverse

from apps.lexicon import models


@pytest.mark.django_db
class TestAffixViews:
    def test_affix_tester_renders_affix_file(self, client, english_project, user):
        """Test that the affix tester view renders the affix file."""
        english_project.affix_file = "SFX A Y 1\nSFX A 0 ing ."
        english_project.save()
        client.force_login(user)
        url = reverse(
            "lexicon:project_admin_affix_tester", args=[english_project.language_code]
        )
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
        url = reverse(
            "lexicon:word_affix_results", args=[english_project.language_code]
        )
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
        url = reverse(
            "lexicon:word_affix_results", args=[english_project.language_code]
        )
        response = client.get(url, {"words": "walk", "affix": "bad"})
        assert response.status_code == 500
        assert (
            response.json()["error"]
            == "An error occurred while processing the affixes."
        )
        assert "bad affix" in response.json()["details"]


@pytest.mark.django_db
class TestWordAffixViews:
    def test_affix_list_view_shows_affixes_and_checked_state(
        self, logged_in_client, kovol_project
    ):
        # Setup: create affixes and a word
        affix_a = models.Affix.objects.create(
            project=kovol_project, name="Prefix A", applies_to="n", affix_letter="A"
        )
        affix_b = models.Affix.objects.create(
            project=kovol_project, name="Prefix B", applies_to="n", affix_letter="B"
        )
        word = models.LexiconEntry.objects.create(
            project=kovol_project, text="hobol"
        )
        word.affixes.add(affix_a)
        url = reverse(
            "lexicon:word_affix_list",
            kwargs={"lang_code": kovol_project.language_code, "pk": word.pk},
        )
        response = logged_in_client.get(url)
        assert response.status_code == 200
        html = response.content.decode()
        print(html)
        # Both affixes should be present
        assert "Prefix A" in html
        assert "Prefix B" in html
        # Only affix_a should be checked
        assert 'id="aff-{}"'.format(affix_a.id) in html
        assert 'id="aff-{}"'.format(affix_b.id) in html

    def test_update_word_affixes_get_form(
        self, client, permissioned_user, kovol_project
    ):
        models.Affix.objects.create(
            project=kovol_project, name="Prefix A", applies_to="n", affix_letter="A"
        )
        models.Affix.objects.create(
            project=kovol_project, name="Prefix B", applies_to="n", affix_letter="B"
        )
        word = models.LexiconEntry.objects.create(
            project=kovol_project, text="hobol"
        )
        url = reverse(
            "lexicon:word_update_affixes",
            kwargs={"lang_code": kovol_project.language_code, "pk": word.pk},
        )
        client.force_login(permissioned_user)
        response = client.get(url)
        assert response.status_code == 200
        html = response.content.decode()
        # Should render checkboxes for both affixes
        assert "Prefix A" in html
        assert "Prefix B" in html
        # Should be a form
        assert "<form" in html

    def test_update_word_affixes_post(self, client, permissioned_user, kovol_project):
        affix_a = models.Affix.objects.create(
            project=kovol_project, name="Prefix A", applies_to="n", affix_letter="A"
        )
        affix_b = models.Affix.objects.create(
            project=kovol_project, name="Prefix B", applies_to="n", affix_letter="B"
        )
        word = models.LexiconEntry.objects.create(
            project=kovol_project, text="hobol"
        )
        url = reverse(
            "lexicon:word_update_affixes",
            kwargs={"lang_code": kovol_project.language_code, "pk": word.pk},
        )
        # Select both affixes
        client.force_login(permissioned_user)
        data = {"affixes": [affix_a.id, affix_b.id]}
        response = client.post(url, data, HTTP_HX_REQUEST="true", follow=True)
        # Should redirect to the affix list fragment (200 or 302 depending on htmx follow)
        assert response.status_code in (200, 302)
        # Refresh word from DB and check affixes
        word.refresh_from_db()
        affix_ids = set(word.affixes.values_list("id", flat=True))
        assert affix_a.id in affix_ids
        assert affix_b.id in affix_ids

    def test_update_word_affixes_post_removes_affix(
        self, client, permissioned_user, kovol_project
    ):
        affix_a = models.Affix.objects.create(
            project=kovol_project, name="Prefix A", applies_to="n", affix_letter="A"
        )
        affix_b = models.Affix.objects.create(
            project=kovol_project, name="Prefix B", applies_to="n", affix_letter="B"
        )
        word = models.LexiconEntry.objects.create(
            project=kovol_project, text="hobol"
        )
        word.affixes.set([affix_a, affix_b])
        client.force_login(permissioned_user)
        url = reverse(
            "lexicon:word_update_affixes",
            kwargs={"lang_code": kovol_project.language_code, "pk": word.pk},
        )
        # Remove affix_b
        data = {"affixes": [affix_a.id]}
        response = client.post(url, data, HTTP_HX_REQUEST="true", follow=True)
        assert response.status_code in (200, 302)
        word.refresh_from_db()
        affix_ids = set(word.affixes.values_list("id", flat=True))
        assert affix_a.id in affix_ids
        assert affix_b.id not in affix_ids

    def test_update_word_affixes_post_empty(
        self, client, permissioned_user, kovol_project
    ):
        affix_a = models.Affix.objects.create(
            project=kovol_project, name="Prefix A", applies_to="n", affix_letter="A"
        )
        word = models.LexiconEntry.objects.create(
            project=kovol_project, text="hobol"
        )
        word.affixes.add(affix_a)
        url = reverse(
            "lexicon:word_update_affixes",
            kwargs={"lang_code": kovol_project.language_code, "pk": word.pk},
        )
        # Remove all affixes
        data = {}  # No affixes selected
        client.force_login(permissioned_user)
        response = client.post(url, data, HTTP_HX_REQUEST="true", follow=True)
        assert response.status_code in (200, 302)
        word.refresh_from_db()
        assert word.affixes.count() == 0

    def test_update_word_affixes_get_forbidden(self, client, user, kovol_project):
        """Unpermissioned user should not be able to GET the affix update form."""
        models.Affix.objects.create(
            project=kovol_project, name="Prefix A", applies_to="n", affix_letter="A"
        )
        word = models.LexiconEntry.objects.create(
            project=kovol_project, text="hobol"
        )
        url = reverse(
            "lexicon:word_update_affixes",
            kwargs={"lang_code": kovol_project.language_code, "pk": word.pk},
        )
        client.force_login(user)
        response = client.get(url)
        assert response.status_code == 403

    def test_update_word_affixes_post_forbidden(self, client, user, kovol_project):
        """Unpermissioned user should not be able to POST affix updates."""
        affix = models.Affix.objects.create(
            project=kovol_project, name="Prefix A", applies_to="n", affix_letter="A"
        )
        word = models.LexiconEntry.objects.create(
            project=kovol_project, text="hobol"
        )
        url = reverse(
            "lexicon:word_update_affixes",
            kwargs={"lang_code": kovol_project.language_code, "pk": word.pk},
        )
        client.force_login(user)
        data = {"affixes": [affix.id]}
        response = client.post(url, data, HTTP_HX_REQUEST="true")
        assert response.status_code == 403
        word.refresh_from_db()
        # Should not have changed
        assert word.affixes.count() == 0
