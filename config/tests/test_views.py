import pytest
from django.urls import reverse
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_login_view_get(client):
    url = reverse("login")  # Adjust if your url name is different
    response = client.get(url)
    assert response.status_code == 200
    assert "form" in response.context


@pytest.mark.django_db
def test_login_view_post_valid(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="testuser", password="testpass"
    )
    url = reverse("login")
    response = client.post(url, {"username": "testuser", "password": "testpass"})
    # Should redirect to home on success
    assert response.status_code == 302
    assert response.url == reverse("project_list")


@pytest.mark.django_db
def test_login_view_post_invalid(client):
    url = reverse("login")
    response = client.post(url, {"username": "nouser", "password": "badpass"})
    assert response.status_code == 200
    assert "form" in response.context
    assert response.context["form"].errors


@pytest.mark.django_db
@pytest.mark.parametrize(
    "row_labels,column_labels,expected_status,expected_error",
    [
        ('["row1", "row2"]', '["col1", "col2"]', 200, ""),  # valid
        ("not a json", '["col1"]', 200, "row_labels: must be a valid JSON array"),
        ('["row1"]', "not a json", 200, "column_labels: must be a valid JSON array"),
        ("", '["col1"]', 200, "row_labels: cannot be empty."),
        ('["row1"]', "", 200, "column_labels: cannot be empty."),
        ("", "", 200, "row_labels: cannot be empty."),
        ('"just a string"', '["col1"]', 200, "row_labels: must be a valid JSON array"),
    ],
)
def test_json_validation_view(
    client, row_labels, column_labels, expected_status, expected_error
):
    url = reverse("json-validation")
    response = client.post(
        url, {"row_labels": row_labels, "column_labels": column_labels}
    )
    assert response.status_code == expected_status
    if expected_error:
        assert expected_error.split(":")[0] in response.content.decode()
    else:
        assert response.content.decode().strip() == ""
