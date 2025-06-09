import pytest
from apps.lexicon import models
from apps.lexicon.tasks import update_lexicon_entry_search_field


@pytest.mark.django_db
def test_update_search_field_basic(english_project):
    entry = models.LexiconEntry.objects.create(
        project=english_project, tok_ples="Word", eng="Meaning"
    )
    # No conjugations or variations yet
    update_lexicon_entry_search_field(entry.pk)
    entry.refresh_from_db()
    assert entry.search == "word"


@pytest.mark.django_db
def test_update_search_field_with_variations_and_conjugations(english_project):
    entry = models.LexiconEntry.objects.create(
        project=english_project, tok_ples="Word", eng="Meaning"
    )
    # Add a variation
    models.Variation.objects.create(word=entry, type="spelling", text="Wurd")
    # Add conjugations
    paradigm = models.Paradigm.objects.create(
        name="TestParadigm",
        project=english_project,
        part_of_speech="n",
        row_labels=["row1"],
        column_labels=["col1"],
    )
    models.Conjugation.objects.create(
        word=entry, paradigm=paradigm, row=0, column=0, conjugation="Words"
    )
    update_lexicon_entry_search_field(entry.pk)
    entry.refresh_from_db()
    # Should include all, lowercased
    assert "word" in entry.search
    assert "wurd" in entry.search
    assert "words" in entry.search
    assert entry.search == "word wurd words"


@pytest.mark.django_db
def test_update_search_field_no_change(english_project):
    entry = models.LexiconEntry.objects.create(
        project=english_project, tok_ples="Word", eng="Meaning", search="word"
    )
    # Should not update or error if search is already correct
    update_lexicon_entry_search_field(entry.pk)
    entry.refresh_from_db()
    assert entry.search == "word"


@pytest.mark.django_db
def test_update_search_field_entry_does_not_exist():
    # Should not raise if entry does not exist
    update_lexicon_entry_search_field(999999)  # Non-existent pk


@pytest.mark.django_db
def test_update_search_field_handles_empty_fields(english_project):
    entry = models.LexiconEntry.objects.create(
        project=english_project, tok_ples="", eng="Meaning"
    )
    update_lexicon_entry_search_field(entry.pk)
    entry.refresh_from_db()
    assert entry.search == ""
