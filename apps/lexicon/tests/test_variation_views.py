import pytest
from django.urls import reverse
from apps.lexicon import models


@pytest.mark.django_db
def test_variation_list_view(client, english_project):
    word = models.LexiconEntry.objects.create(
        project=english_project, tok_ples="foo", eng="bar"
    )
    var1 = models.Variation.objects.create(word=word, type="spelling", text="foo1")
    var2 = models.Variation.objects.create(word=word, type="dialect", text="foo2")
    url = reverse("lexicon:variation_list", kwargs={"pk": word.pk})
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


