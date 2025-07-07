import pytest
from django.contrib.auth.models import User
from guardian.shortcuts import assign_perm

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


@pytest.fixture
def english_project():
    """Fixture to create an English project."""
    return models.LexiconProject.objects.create(
        language_code="eng",
        language_name="English",
    )


@pytest.fixture
def english_words(english_project):
    """Fixture to create test words."""
    word1 = models.LexiconEntry.objects.create(
        tok_ples="test_word", eng="test_word_gloss", project=english_project
    )
    word2 = models.LexiconEntry.objects.create(
        tok_ples="extra_word", eng="extra_word_gloss", project=english_project
    )
    return [word1, word2]


@pytest.fixture
def kovol_project():
    """Fixture to create an 2nd Kovol project."""
    return models.LexiconProject.objects.create(
        language_code="kgu",
        language_name="Kovol",
    )


@pytest.fixture
def english_words_with_paradigm(english_project):
    """Fixture to create test words and a paradigm."""
    word1 = models.LexiconEntry.objects.create(
        tok_ples="test_word", eng="test_word_gloss", project=english_project
    )
    word2 = models.LexiconEntry.objects.create(
        tok_ples="extra_word", eng="extra_word_gloss", project=english_project
    )
    paradigm = models.Paradigm.objects.create(
        name="Test Paradigm",
        row_labels=["row1"],
        column_labels=["col1"],
        project=english_project,
    )
    word1.paradigms.add(paradigm)
    conjugation = models.Conjugation.objects.create(
        word=word1, paradigm=paradigm, row=0, column=0, conjugation="test"
    )
    return [word1, word2], paradigm, conjugation


@pytest.fixture
def kovol_words(kovol_project):
    """Fixture to create test words."""
    word1 = models.LexiconEntry.objects.create(
        tok_ples="hobol", eng="talk", project=kovol_project
    )
    word2 = models.LexiconEntry.objects.create(
        tok_ples="bili", eng="good", project=kovol_project
    )
    return [word1, word2]


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def multirow_paradigm(english_project):
    paradigm = models.Paradigm.objects.create(
        name="Multirow Paradigm",
        project=english_project,
        row_labels=["1", "2", "3"],
        column_labels=["1", "2"],
    )
    word = models.LexiconEntry.objects.create(
        tok_ples="multiword",
        eng="multiword",
        project=english_project,
    )
    # Create conjugations for all cells
    conjugations = []
    for row in range(3):
        for col in range(2):
            conj = models.Conjugation.objects.create(
                word=word,
                paradigm=paradigm,
                row=row,
                column=col,
                conjugation=f"orig_{row}_{col}",
            )
            conjugations.append(conj)
    return word, paradigm, conjugations


# Example fixture for logged-in client
@pytest.fixture
def logged_in_client(client, django_user_model):
    _ = django_user_model.objects.create_user(username="testuser", password="testpass")
    client.login(username="testuser", password="testpass")
    return client


@pytest.fixture
def permissioned_user(user, english_project, kovol_project):
    assign_perm("edit_lexiconproject", user, english_project)
    assign_perm("edit_lexiconproject", user, kovol_project)
    return user
