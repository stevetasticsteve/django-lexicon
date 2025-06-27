import pytest
from django.urls import reverse

from apps.lexicon import models


@pytest.mark.django_db
class TestParadigmAdminViews:
    def test_paradigm_list_view(self, logged_in_client, english_project, english_words_with_paradigm):
        """Test the list view returns 200 and contains paradigms."""
        url = reverse(
            "lexicon:paradigm_list", kwargs={"lang_code": english_project.language_code}
        )
        response = logged_in_client.get(url)
        assert response.status_code == 200
        assert "Paradigms" in response.content.decode()
        assert "Test Paradigm" in response.content.decode()

    def test_create_paradigm_get(self, logged_in_client, english_project):
        """Test the create paradigm view returns 200 and contains the form."""
        url = reverse(
            "lexicon:paradigm_create",
            kwargs={
                "lang_code": english_project.language_code,
                "project_pk": english_project.pk,
            },
        )
        response = logged_in_client.get(url)
        assert response.status_code == 200
        assert "form" in response.content.decode().lower()

    def test_create_paradigm_post(self, logged_in_client, english_project):
        """Test creating a paradigm via POST request."""
        url = reverse(
            "lexicon:paradigm_create",
            kwargs={
                "lang_code": english_project.language_code,
                "project_pk": english_project.pk,
            },
        )
        data = {
            "name": "Test Paradigm",
            "part_of_speech": "n",
            "row_labels": '["row1", "row2"]',
            "column_labels": '["col1", "col2"]',
        }
        response = logged_in_client.post(url, data, follow=True)
        assert response.status_code == 200
        assert models.Paradigm.objects.filter(
            name="Test Paradigm", project=english_project
        ).exists()

    def test_update_paradigm_get_and_post(self, logged_in_client, english_project):
        """Test updating a paradigm via GET and POST requests."""
        paradigm = models.Paradigm.objects.create(
            name="Old Paradigm",
            part_of_speech="noun",
            row_labels=["row1"],
            column_labels=["col1"],
            project=english_project,
        )
        url = reverse(
            "lexicon:paradigm_edit",
            kwargs={"lang_code": english_project.language_code, "pk": paradigm.pk},
        )
        # GET
        response = logged_in_client.get(url)
        assert response.status_code == 200
        assert "Old Paradigm" in response.content.decode()
        # POST
        data = {
            "name": "Updated Paradigm",
            "part_of_speech": "v",
            "row_labels": '["row1", "row2"]',
            "column_labels": '["col1", "col2"]',
        }
        response = logged_in_client.post(url, data, follow=True)
        assert response.status_code == 200
        paradigm.refresh_from_db()
        assert paradigm.name == "Updated Paradigm"
        assert paradigm.part_of_speech == "v"

    def test_delete_paradigm(self, logged_in_client, english_project):
        """Test deleting a paradigm via GET and POST requests."""
        paradigm = models.Paradigm.objects.create(
            name="Delete Paradigm",
            part_of_speech="n",
            row_labels=["row1"],
            column_labels=["col1"],
            project=english_project,
        )
        url = reverse(
            "lexicon:paradigm_delete",
            kwargs={"lang_code": english_project.language_code, "pk": paradigm.pk},
        )
        # GET confirmation
        response = logged_in_client.get(url)
        assert response.status_code == 200
        # POST delete
        response = logged_in_client.post(url, follow=True)
        assert response.status_code == 200
        assert not models.Paradigm.objects.filter(pk=paradigm.pk).exists()

    def test_create_paradigm_invalid_data(self, logged_in_client, english_project):
        """Test creating a paradigm with invalid data does not create an object."""
        url = reverse(
            "lexicon:paradigm_create",
            kwargs={
                "lang_code": english_project.language_code,
                "project_pk": english_project.pk,
            },
        )
        data = {
            "name": "",  # Name is required
            "part_of_speech": "",
            "row_labels": "",
            "column_labels": "",
        }
        response = logged_in_client.post(url, data)
        assert response.status_code == 200
        assert (
            models.Paradigm.objects.filter(name="", project=english_project).count()
            == 0
        )
