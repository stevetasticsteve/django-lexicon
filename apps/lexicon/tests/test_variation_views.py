import pytest
from django.urls import reverse

from apps.lexicon import forms, models


@pytest.mark.django_db
def test_variation_list_view(client, english_project):
    word = models.LexiconEntry.objects.create(
        project=english_project, tok_ples="foo", eng="bar"
    )
    var1 = models.Variation.objects.create(word=word, type="spelling", text="foo1")
    var2 = models.Variation.objects.create(word=word, type="dialect", text="foo2")
    url = reverse("lexicon:variation_list", kwargs={"word_pk": word.pk})
    response = client.get(url)
    assert response.status_code == 200
    assert var1.text in response.content.decode()
    assert var2.text in response.content.decode()


@pytest.mark.django_db
def test_variation_edit_get_requires_login(client, english_project):
    word = models.LexiconEntry.objects.create(
        project=english_project, tok_ples="foo", eng="bar"
    )
    var = models.Variation.objects.create(word=word, type="spelling", text="foo1")
    url = reverse("lexicon:variation_edit", kwargs={"pk": var.pk})
    response = client.get(url)
    # Should redirect to login
    assert response.status_code in (302, 403)


@pytest.mark.django_db
def test_variation_edit_get_and_post(logged_in_client, english_project):
    # logged_in_client is a fixture that logs in a user
    word = models.LexiconEntry.objects.create(
        project=english_project, tok_ples="foo", eng="bar"
    )
    var = models.Variation.objects.create(word=word, type="spelling", text="foo1")
    url = reverse("lexicon:variation_edit", kwargs={"pk": var.pk})

    # GET
    response = logged_in_client.get(url)
    assert response.status_code == 200
    assert 'name="text"' in response.content.decode()

    # POST (edit the variation)
    data = {
        "text": "foo1-edited",
        "type": "spelling",
        "included_in_spellcheck": "on",
        "included_in_search": "on",
    }
    response = logged_in_client.post(url, data, follow=True, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    var.refresh_from_db()
    assert var.text == "foo1-edited"
    assert var.included_in_spellcheck is True
    assert var.included_in_search is True


@pytest.mark.django_db
def test_variation_edit_htmx_response(logged_in_client, english_project):
    word = models.LexiconEntry.objects.create(
        project=english_project, tok_ples="foo", eng="bar"
    )
    var = models.Variation.objects.create(word=word, type="spelling", text="foo1")
    url = reverse("lexicon:variation_edit", kwargs={"pk": var.pk})
    data = {
        "text": "foo1-edited",
        "type": "spelling",
        "included_in_spellcheck": "on",
        "included_in_search": "on",
    }
    response = logged_in_client.post(url, data, HTTP_HX_REQUEST="true")
    assert response.status_code == 302
    assert models.Variation.objects.get(pk=var.pk).text == "foo1-edited"


@pytest.mark.django_db
class TestCreateVariation:
    def get_create_url(self, word_pk):
        return reverse("lexicon:variation_create", kwargs={"word_pk": word_pk})

    def test_variation_create_get_requires_login(self, client, english_words):
        word = english_words[0]
        url = self.get_create_url(word.pk)
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_variation_create_get_renders_form(self, logged_in_client, english_words):
        word = english_words[0]
        url = self.get_create_url(word.pk)
        response = logged_in_client.get(url)

        assert response.status_code == 200
        assert (
            response.templates[0].name
            == "lexicon/includes/variations/variation_edit.html"
        )
        assert "form" in response.context
        assert isinstance(response.context["form"], forms.VariationForm)
        assert "word" in response.context
        assert response.context["word"] == word

    def test_variation_create_get_invalid_word_pk_raises_404(self, logged_in_client):
        invalid_word_pk = 99999  # An ID that's unlikely to exist
        url = self.get_create_url(invalid_word_pk)
        response = logged_in_client.get(url)
        assert response.status_code == 404

    def test_variation_create_post_success(self, logged_in_client, english_words):
        word = english_words[0]
        url = self.get_create_url(word.pk)
        initial_variation_count = models.Variation.objects.count()
        data = {
            "text": "newvariant",
            "type": "dialect",
            "included_in_spellcheck": True,
            "included_in_search": True,
        }
        response = logged_in_client.post(url, data, follow=True)

        assert response.status_code == 200  # After redirect
        assert models.Variation.objects.count() == initial_variation_count + 1

        new_variation = models.Variation.objects.latest("id")
        assert new_variation.word == word
        assert new_variation.text == "newvariant"
        assert new_variation.type == "dialect"
        assert new_variation.included_in_spellcheck is True
        assert new_variation.included_in_search is True

        expected_redirect_url = reverse(
            "lexicon:variation_list", kwargs={"word_pk": word.pk}
        )
        assert len(response.redirect_chain) == 1
        actual_redirect_url, status_code = response.redirect_chain[0]
        assert status_code == 302
        from urllib.parse import urlparse

        assert urlparse(actual_redirect_url).path == expected_redirect_url
        assert response.resolver_match.view_name == "lexicon:variation_list"
        assert new_variation.text in response.content.decode()

    def test_variation_create_post_invalid_data(self, logged_in_client, english_words):
        word = english_words[0]
        url = self.get_create_url(word.pk)
        initial_variation_count = models.Variation.objects.count()
        data = {
            "text": "",  # Invalid: text is required by Variation model/form
            "type": "spelling",
        }
        response = logged_in_client.post(url, data)

        assert response.status_code == 200  # Re-renders form with errors
        assert models.Variation.objects.count() == initial_variation_count
        assert "form" in response.context
        assert response.context["form"].errors
        assert "text" in response.context["form"].errors
        assert "word" in response.context
        assert response.context["word"] == word
        assert (
            response.templates[0].name
            == "lexicon/includes/variations/variation_edit.html"
        )

    def test_variation_create_post_invalid_word_pk_raises_404(self, logged_in_client):
        invalid_word_pk = 99999
        url = self.get_create_url(invalid_word_pk)
        data = {
            "text": "newvariant",
            "type": "dialect",
        }
        response = logged_in_client.post(url, data)
        assert response.status_code == 404


@pytest.mark.django_db
class TestDeleteVariation:
    def get_delete_url(self, pk):
        return reverse("lexicon:variation_delete", kwargs={"pk": pk})

    def test_delete_requires_login(self, client, english_words):
        word = english_words[0]
        variation = models.Variation.objects.create(
            word=word, type="spelling", text="todelete"
        )
        url = self.get_delete_url(variation.pk)
        # GET
        response = client.get(url)
        assert response.status_code in (302, 403)
        # POST
        response = client.post(url)
        assert response.status_code in (302, 403)

    def test_delete_get_renders_confirm(self, logged_in_client, english_words):
        word = english_words[0]
        variation = models.Variation.objects.create(
            word=word, type="spelling", text="todelete"
        )
        url = self.get_delete_url(variation.pk)
        response = logged_in_client.get(url)
        assert response.status_code == 200
        assert (
            "form" in response.content.decode()
            or "Are you sure" in response.content.decode()
        )

    def test_delete_post_deletes_and_redirects(self, logged_in_client, english_words):
        word = english_words[0]
        variation = models.Variation.objects.create(
            word=word, type="spelling", text="todelete"
        )
        url = self.get_delete_url(variation.pk)
        initial_count = models.Variation.objects.count()
        response = logged_in_client.post(url, follow=True)
        assert response.status_code == 200
        assert models.Variation.objects.count() == initial_count - 1
        # Should redirect to the variation list for the word
        expected_url = reverse("lexicon:variation_list", kwargs={"word_pk": word.pk})
        assert expected_url in response.request["PATH_INFO"]

    def test_delete_invalid_pk_404(self, logged_in_client):
        url = self.get_delete_url(999999)
        response = logged_in_client.get(url)
        assert response.status_code == 404
        response = logged_in_client.post(url)
        assert response.status_code == 404
