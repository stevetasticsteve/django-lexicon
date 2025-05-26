import pytest
from django.urls import reverse

from apps.lexicon import models


@pytest.fixture
def lexicon_projects():
    """Create test lexicon projects"""
    project1 = models.LexiconProject.objects.create(
        language_name="English",
        language_code="eng",
        # Add other required fields based on your model
    )
    project2 = models.LexiconProject.objects.create(
        language_name="Kovol",
        language_code="kgu",
    )
    return [project1, project2]


@pytest.mark.django_db
class TestProjectList:
    def test_view_uses_correct_template(self, client):
        """Test that the view uses the correct template"""
        response = client.get(reverse("lexicon:project_list"))  # Adjust URL name
        assert response.status_code == 200
        assert response.templates[0].name == "lexicon/project_list.html"

    def test_view_returns_all_projects(self, client, lexicon_projects):
        """Test that all projects are displayed in the context"""
        response = client.get(reverse("lexicon:project_list"))
        assert response.status_code == 200
        assert len(response.context["object_list"]) == 2
        assert (
            len(response.context["lexiconproject_list"]) == 2
        )  # ListView default context name

        # Check that both projects are in the response
        project_names = [p.language_name for p in response.context["object_list"]]
        assert "English" in project_names
        assert "Kovol" in project_names

    def test_empty_project_list(self, client):
        """Test view behavior when no projects exist"""
        response = client.get(reverse("lexicon:project_list"))
        assert response.status_code == 200
        assert len(response.context["object_list"]) == 0

    def test_view_accessible_by_name(self, client):
        """Test that the view is accessible by its URL name"""
        response = client.get(reverse("lexicon:project_list"))
        assert response.status_code == 200

    def test_view_context_contains_expected_data(self, client, lexicon_projects):
        """Test that context contains all expected data"""
        response = client.get(reverse("lexicon:project_list"))

        # Test standard ListView context variables
        assert "object_list" in response.context
        assert "lexiconproject_list" in response.context
        assert "view" in response.context

        content = response.content.decode()
        assert "English" in content
        assert "Kovol" in content
