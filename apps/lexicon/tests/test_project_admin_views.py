import pytest
from django.urls import reverse

from apps.lexicon import models


@pytest.mark.django_db
class TestParadigmAdminViews:
    def test_paradigm_list_view(
        self, client, permissioned_user, english_project, english_words_with_paradigm
    ):
        """Test the list view returns 200 and contains paradigms."""
        url = reverse(
            "lexicon:paradigm_list", kwargs={"lang_code": english_project.language_code}
        )
        client.force_login(permissioned_user)
        response = client.get(url)
        assert response.status_code == 200
        assert "Paradigms" in response.content.decode()
        assert "Test Paradigm" in response.content.decode()

    def test_create_paradigm_get(self, client, permissioned_user, english_project):
        """Test the create paradigm view returns 200 and contains the form."""
        url = reverse(
            "lexicon:paradigm_create",
            kwargs={
                "lang_code": english_project.language_code,
                "project_pk": english_project.pk,
            },
        )
        client.force_login(permissioned_user)
        response = client.get(url)
        assert response.status_code == 200
        assert "form" in response.content.decode().lower()

    def test_create_paradigm_post(self, client, permissioned_user, english_project):
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
        client.force_login(permissioned_user)
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        assert models.Paradigm.objects.filter(
            name="Test Paradigm", project=english_project
        ).exists()

    def test_update_paradigm_get_and_post(
        self, client, permissioned_user, english_project
    ):
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
        client.force_login(permissioned_user)
        response = client.get(url)
        assert response.status_code == 200
        assert "Old Paradigm" in response.content.decode()
        # POST
        data = {
            "name": "Updated Paradigm",
            "part_of_speech": "v",
            "row_labels": '["row1", "row2"]',
            "column_labels": '["col1", "col2"]',
        }
        client.force_login(permissioned_user)
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        paradigm.refresh_from_db()
        assert paradigm.name == "Updated Paradigm"
        assert paradigm.part_of_speech == "v"

    def test_delete_paradigm(self, client, permissioned_user, english_project):
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
        client.force_login(permissioned_user)
        response = client.get(url)
        assert response.status_code == 200
        # POST delete
        client.force_login(permissioned_user)
        response = client.post(url, follow=True)
        assert response.status_code == 200
        assert not models.Paradigm.objects.filter(pk=paradigm.pk).exists()

    def test_create_paradigm_invalid_data(
        self, client, permissioned_user, english_project
    ):
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
        client.force_login(permissioned_user)
        response = client.post(url, data)
        assert response.status_code == 200
        assert (
            models.Paradigm.objects.filter(name="", project=english_project).count()
            == 0
        )


@pytest.mark.django_db
class TestAffixAdminViews:
    def test_affix_list_view(self, client, permissioned_user, english_project):
        """Test the affix list view returns 200 and contains affixes."""
        url = reverse(
            "lexicon:affix_list", kwargs={"lang_code": english_project.language_code}
        )
        client.force_login(permissioned_user)
        response = client.get(url)
        assert response.status_code == 200
        assert "Affix" in response.content.decode()

    def test_create_affix_get(self, client, permissioned_user, english_project):
        """Test the create affix view returns 200 and contains the form."""
        url = reverse(
            "lexicon:affix_create",
            kwargs={
                "lang_code": english_project.language_code,
                "project_pk": english_project.pk,
            },
        )
        client.force_login(permissioned_user)
        response = client.get(url)
        assert response.status_code == 200
        assert "form" in response.content.decode().lower()

    def test_create_affix_post(self, client, permissioned_user, english_project):
        """Test creating an affix via POST request."""
        url = reverse(
            "lexicon:affix_create",
            kwargs={
                "lang_code": english_project.language_code,
                "project_pk": english_project.pk,
            },
        )
        data = {
            "name": "Prefix A",
            "applies_to": "n",
            "affix_letter": "A",
        }
        client.force_login(permissioned_user)
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        assert models.Affix.objects.filter(
            name="Prefix A", project=english_project
        ).exists()

    def test_update_affix_get_and_post(
        self, client, permissioned_user, english_project
    ):
        """Test updating an affix via GET and POST requests."""
        affix = models.Affix.objects.create(
            project=english_project,
            name="Old Affix",
            applies_to="n",
            affix_letter="B",
        )
        url = reverse(
            "lexicon:affix_edit",
            kwargs={"lang_code": english_project.language_code, "pk": affix.pk},
        )
        # GET
        client.force_login(permissioned_user)
        response = client.get(url)
        assert response.status_code == 200
        assert "Old Affix" in response.content.decode()
        # POST
        data = {
            "name": "Updated Affix",
            "applies_to": "v",
            "affix_letter": "C",
        }
        client.force_login(permissioned_user)
        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        affix.refresh_from_db()
        assert affix.name == "Updated Affix"
        assert affix.applies_to == "v"
        assert affix.affix_letter == "C"

    def test_delete_affix(self, client, permissioned_user, english_project):
        """Test deleting an affix via GET and POST requests."""
        affix = models.Affix.objects.create(
            project=english_project,
            name="Delete Affix",
            applies_to="n",
            affix_letter="D",
        )
        url = reverse(
            "lexicon:affix_delete",
            kwargs={"lang_code": english_project.language_code, "pk": affix.pk},
        )
        # GET confirmation
        client.force_login(permissioned_user)
        response = client.get(url)
        assert response.status_code == 200
        # POST delete
        client.force_login(permissioned_user)
        response = client.post(url, follow=True)
        assert response.status_code == 200
        assert not models.Affix.objects.filter(pk=affix.pk).exists()

    def test_create_affix_invalid_data(
        self, client, permissioned_user, english_project
    ):
        """Test creating an affix with invalid data does not create an object."""
        url = reverse(
            "lexicon:affix_create",
            kwargs={
                "lang_code": english_project.language_code,
                "project_pk": english_project.pk,
            },
        )
        data = {
            "name": "",
            "applies_to": "",
            "affix_letter": "",
        }
        client.force_login(permissioned_user)
        response = client.post(url, data)
        assert response.status_code == 200
        assert models.Affix.objects.all().count() == 0

    def test_create_affix_duplicate_letter(
        self, client, permissioned_user, english_project
    ):
        """Test creating an affix with a duplicate letter returns an error."""
        # Create an affix with letter E
        models.Affix.objects.create(
            project=english_project,
            name="Affix E",
            applies_to="n",
            affix_letter="E",
        )
        url = reverse(
            "lexicon:affix_create",
            kwargs={
                "lang_code": english_project.language_code,
                "project_pk": english_project.pk,
            },
        )
        data = {
            "name": "Duplicate Affix",
            "applies_to": "n",
            "affix_letter": "E",
        }
        client.force_login(permissioned_user)
        response = client.post(url, data, HTTP_HX_REQUEST="true")
        # Should return 400 and the error message
        assert response.status_code == 400
        assert (
            "Affix letter must be unique for this project." in response.content.decode()
        )


@pytest.mark.django_db
class TestProjectAdminPermissions:
    def test_unpermissioned_user_access(self, logged_in_client, english_project):
        """Test that an unpermissioned user cannot access any project admin views."""
        urls = [
            reverse(
                "lexicon:project_admin",
                kwargs={"lang_code": english_project.language_code},
            ),
            reverse(
                "lexicon:paradigm_manage",
                kwargs={"lang_code": english_project.language_code},
            ),
            reverse(
                "lexicon:paradigm_list",
                kwargs={"lang_code": english_project.language_code},
            ),
            reverse(
                "lexicon:paradigm_edit",
                kwargs={"lang_code": english_project.language_code, "pk": 1},
            ),
            reverse(
                "lexicon:paradigm_create",
                kwargs={"lang_code": english_project.language_code, "project_pk": 1},
            ),
            reverse(
                "lexicon:paradigm_delete",
                kwargs={"lang_code": english_project.language_code, "pk": 1},
            ),
            reverse(
                "lexicon:affix_manage",
                kwargs={"lang_code": english_project.language_code},
            ),
            reverse(
                "lexicon:affix_list",
                kwargs={"lang_code": english_project.language_code},
            ),
            reverse(
                "lexicon:affix_edit",
                kwargs={"lang_code": english_project.language_code, "pk": 1},
            ),
            reverse(
                "lexicon:affix_create",
                kwargs={"lang_code": english_project.language_code, "project_pk": 1},
            ),
            reverse(
                "lexicon:affix_delete",
                kwargs={"lang_code": english_project.language_code, "pk": 1},
            ),
        ]
        for url in urls:
            response = logged_in_client.get(url)
            assert response.status_code == 403, (
                f"Unpermissioned user should not be able to access {url}"
            )
