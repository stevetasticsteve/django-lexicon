import pytest
from django.urls import reverse
from apps.lexicon import models


@pytest.fixture
def ignore_word(english_project):
    return models.IgnoreWord.objects.create(
        tok_ples="ignoreme",
        type="tpi",
        eng="test",
        project=english_project,
        comments="test comment",
    )


@pytest.mark.django_db
class TestIgnoreWordViews:
    def get_list_url(self, project):
        return reverse("lexicon:ignore_list", args=[project.language_code])

    def get_create_url(self, project):
        return reverse("lexicon:create_ignore", args=[project.language_code])

    def get_update_url(self, project, obj):
        return reverse("lexicon:update_ignore", args=[project.language_code, obj.pk])

    def get_delete_url(self, project, obj):
        return reverse("lexicon:delete_ignore", args=[project.language_code, obj.pk])

    def test_ignore_list_view(self, client, english_project, user):
        """Test that the ignore list view returns a 200 status code."""
        client.force_login(user)
        url = self.get_list_url(english_project)
        response = client.get(url)
        assert response.status_code == 200
        assert "ignore" in response.content.decode().lower()

    def test_create_ignore_word(self, client, english_project, user):
        """Test that a new ignore word can be created."""
        client.force_login(user)
        url = self.get_create_url(english_project)
        data = {
            "tok_ples": "newignore",
            "type": "tpi",
            "eng": "english",
            "comments": "some comment",
        }
        response = client.post(url, data)
        assert response.status_code == 302  # Redirect after success
        assert models.IgnoreWord.objects.filter(
            tok_ples="newignore", project=english_project
        ).exists()

    def test_update_ignore_word(self, client, english_project, ignore_word, user):
        """Test that an existing ignore word can be updated."""
        client.force_login(user)
        url = self.get_update_url(english_project, ignore_word)
        data = {
            "tok_ples": "ignoreme",
            "type": "tpi",
            "eng": "updated",
            "comments": "updated comment",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        ignore_word.refresh_from_db()
        assert ignore_word.eng == "updated"
        assert ignore_word.comments == "updated comment"

    def test_delete_ignore_word(self, client, english_project, ignore_word, user):
        """Test that an existing ignore word can be deleted."""
        client.force_login(user)
        url = self.get_delete_url(english_project, ignore_word)
        response = client.post(url)
        assert response.status_code == 302
        assert not models.IgnoreWord.objects.filter(pk=ignore_word.pk).exists()

    def test_login_required(self, client, english_project, ignore_word):
        """Test that login is required for ignore word views."""
        # List
        url = self.get_list_url(english_project)
        response = client.get(url)
        assert response.status_code in (200, 302)  # List may be public or require login

        # Create
        url = self.get_create_url(english_project)
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login

        # Update
        url = self.get_update_url(english_project, ignore_word)
        response = client.get(url)
        assert response.status_code == 302

        # Delete
        url = self.get_delete_url(english_project, ignore_word)
        response = client.get(url)
        assert response.status_code == 302
