import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestExportView:

    """Test the export page works for get and post."""
    def test_export_view_get(self, client, project_with_affix_file):
        response = client.get(
            reverse(
                "lexicon:export_page",
                kwargs={"lang_code": project_with_affix_file.language_code},
            )
        )
        assert response.status_code == 200

    def test_export_view_post_oxt(self, client, project_with_affix_file):
        """Test that posting to the export view returns an OXT file."""
        response = client.post(
            reverse(
                "lexicon:export_page",
                kwargs={"lang_code": project_with_affix_file.language_code},
            ),
            data={
                "export_type": "oxt",
                "include_hunspell": True,
                "include_ignore": True,
            },
        )
        assert response.status_code == 200
        assert response.has_header("Content-Disposition")
        assert response["Content-Disposition"].startswith("attachment;")
        assert response["Content-Disposition"].endswith('.oxt"')

    def test_export_view_post_dic(self, client, project_with_affix_file):
        """Test that posting to the export view returns a dic file."""
        response = client.post(
            reverse(
                "lexicon:export_page",
                kwargs={"lang_code": project_with_affix_file.language_code},
            ),
            data={
                "export_type": "dic",
                "include_hunspell": True,
                "include_ignore": True,
            },
        )
        assert response.status_code == 200
        assert response.has_header("Content-Disposition")
        assert response["Content-Disposition"].startswith("attachment;")
        assert response["Content-Disposition"].endswith('.dic"')

@pytest.mark.django_db
class TestOxtUpdateViews:
    """Test the oxt update views work correctly."""

    def test_oxt_update_deliver(self, client, project_with_affix_file):
        """Test that the oxt update deliver view returns an OXT file."""
        url = reverse(
            "lexicon:oxt_update_deliver",
            kwargs={"lang_code": project_with_affix_file.language_code},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert response.has_header("Content-Disposition")
        assert response["Content-Disposition"].startswith("attachment;")
        assert response["Content-Disposition"].endswith(".oxt\"")
        assert response["Content-Type"] == "application/vnd.openoffice.extension"

    def test_oxt_update_notify(self, client, project_with_affix_file):
        """Test that the oxt update notify view returns an XML file."""
        url = reverse(
            "lexicon:oxt_update_notify",
            kwargs={"lang_code": project_with_affix_file.language_code},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "text/xml"
