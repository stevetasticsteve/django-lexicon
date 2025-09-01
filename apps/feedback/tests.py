import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from apps.feedback.models import Feedback


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="testuser", password="testpassword", email="test@example.com"
    )


@pytest.mark.django_db
def test_feedback_view_authenticated(client, test_user):
    """Test that an authenticated user can access the feedback view and submit feedback."""
    client.force_login(test_user)
    url = reverse("feedback")
    response = client.get(url)
    assert response.status_code == 200

    feedback_data = {
        "type": "bug",
        "message": "This is a test feedback message.",
    }
    response = client.post(url, feedback_data)
    assert response.status_code == 302  # Redirect to success page
    assert Feedback.objects.count() == 1
    feedback = Feedback.objects.first()
    assert feedback.name == "testuser"
    assert feedback.user_email == "test@example.com"
    assert feedback.message == "This is a test feedback message."
    assert feedback.type == "bug"


@pytest.mark.django_db
def test_feedback_model():
    """Test the Feedback model."""
    feedback = Feedback.objects.create(
        name="test", user_email="test@test.com", message="message", type="bug"
    )

    assert feedback.name == "test"
    assert feedback.user_email == "test@test.com"
    assert feedback.message == "message"
    assert feedback.type == "bug"


@pytest.mark.django_db
def test_feedback_success_page(client, test_user):
    """Test that the feedback success page is accessible."""
    client.force_login(test_user)
    url = reverse("feedback_success")
    response = client.get(url)
    assert response.status_code == 200
