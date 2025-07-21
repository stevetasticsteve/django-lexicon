import re

import pytest
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse


# password reset tests
@pytest.mark.django_db
def test_password_reset_email_sent(client):
    """Test that a password reset email is sent to the user."""
    user = User.objects.create_user(
        username="resetuser", email="reset@example.com", password="oldpassword"
    )
    response = client.post(reverse("password_reset"), {"email": user.email})
    assert response.status_code == 302  # Should redirect after form submit
    assert len(mail.outbox) == 1
    assert user.email in mail.outbox[0].to


@pytest.mark.django_db
def test_password_reset_email_invalid_user(client):
    """Test that no email is sent if the user does not exist."""
    response = client.post(reverse("password_reset"), {"email": "notfound@example.com"})
    assert response.status_code == 302
    assert len(mail.outbox) == 0  # No email sent for unknown user


@pytest.mark.django_db
def test_password_reset_confirm_and_login(client):
    """Test the password reset confirm flow and login with new password."""
    user = User.objects.create_user(
        username="resetuser2", email="reset2@example.com", password="oldpassword"
    )
    client.post(reverse("password_reset"), {"email": user.email})
    email = mail.outbox[0]
    # Extract the reset link from the email
    match = re.search(r"http[s]?://[^/]+(/[^ \n]+)", email.body)
    assert match
    reset_path = match.group(1)
    client.logout()  # Ensure not logged in

    # Visit the password reset confirm page
    response = client.get(reset_path)
    assert response.status_code == 302
    # Follow the redirect to set-password page
    set_password_url = response.url
    response = client.get(set_password_url)
    assert response.status_code == 200

    # Submit new password
    response = client.post(
        set_password_url,
        {
            "new_password1": "newsecurepassword123",
            "new_password2": "newsecurepassword123",
        },
    )
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.check_password("newsecurepassword123")
    # Try logging in with new password
    login = client.login(username="resetuser2", password="newsecurepassword123")
    assert login


@pytest.mark.django_db
def test_password_reset_templates_used(client, settings):
    """Test that the correct templates are used for password reset views."""
    # This assumes you have custom templates named as below
    response = client.get(reverse("password_reset"))
    assert "registration/password_reset_form.html" in [
        t.name for t in response.templates
    ]
    response = client.get(reverse("password_reset_done"))
    assert "registration/password_reset_done.html" in [
        t.name for t in response.templates
    ]
    response = client.get(reverse("password_reset_complete"))
    assert "registration/password_reset_complete.html" in [
        t.name for t in response.templates
    ]


@pytest.mark.django_db
def test_password_reset_complete(client):
    """Test that the password reset complete page renders correctly after resetting the password."""
    user = User.objects.create_user(
        username="resetuser3", email="reset3@example.com", password="oldpassword"
    )
    client.post(reverse("password_reset"), {"email": user.email})
    email = mail.outbox[0]
    match = re.search(r"http[s]?://[^/]+(/[^ \n]+)", email.body)
    reset_path = match.group(1)
    client.post(
        reset_path,
        {
            "new_password1": "anothernewpassword",
            "new_password2": "anothernewpassword",
        },
    )
    response = client.get(reverse("password_reset_complete"))
    assert response.status_code == 200
    assert "registration/password_reset_complete.html" in [
        t.name for t in response.templates
    ]


# django-registration tests
@pytest.mark.django_db
def test_registration_two_step_activation(client):
    # Step 1: Register
    response = client.post(
        reverse("django_registration_register"),
        {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "strongpassword123",
            "password2": "strongpassword123",
        },
    )
    assert response.status_code == 302
    assert len(mail.outbox) == 1

    # Step 2: Activate
    email = mail.outbox[0]
    match = re.search(r"http[s]?://[^\s]+", email.body)
    assert match
    activation_path = match.group(0)
    key = activation_path.split("key=")[-1]  # .strip()
    response = client.get(activation_path)
    assert response.status_code == 200
    response = client.post(activation_path, {"activation_key": key})
    # Step 3: Complete profile (example)
    user = User.objects.get(username="newuser")
    assert user.is_active


@pytest.mark.django_db
def test_django_registration_templates_used(client, settings):
    # Registration form
    response = client.get(reverse("django_registration_register"))
    assert "django_registration/registration_form.html" in [
        t.name for t in response.templates
    ]

    # Submit registration
    response = client.post(
        reverse("django_registration_register"),
        {
            "username": "templateuser",
            "email": "templateuser@example.com",
            "password1": "strongpassword123",
            "password2": "strongpassword123",
        },
        follow=True,
    )
    assert "django_registration/registration_complete.html" in [
        t.name for t in response.templates
    ]
    assert len(mail.outbox) == 1

    # Activation email templates
    email = mail.outbox[0]
    # Check that the body contains expected text from your template
    assert "To activate your account" in email.body
    # Check that the subject contains expected text from your template
    assert "Activate your Lexicon account" in email.subject

    # Activation complete
    response = client.get(reverse("django_registration_activation_complete"))
    assert "django_registration/activation_complete.html" in [
        t.name for t in response.templates
    ]

    # Registration closed
    response = client.get(reverse("django_registration_disallowed"))
    assert "django_registration/registration_closed.html" in [
        t.name for t in response.templates
    ]
