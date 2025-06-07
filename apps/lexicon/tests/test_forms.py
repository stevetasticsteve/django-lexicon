import pytest
from django.core.exceptions import ValidationError

from apps.lexicon import forms, models


@pytest.mark.django_db
def test_conjugation_form_validates_and_sets_instance_fields(english_project):
    paradigm = models.Paradigm.objects.create(
        name="TestParadigm",
        project=english_project,
        part_of_speech="n",
        row_labels=["row1"],
        column_labels=["col1"],
    )
    word = models.LexiconEntry.objects.create(
        project=english_project, tok_ples="foo", eng="bar"
    )
    form = forms.ConjugationForm(
        data={"conjugation": "valid"},
        paradigm=paradigm,
        word=word,
    )
    assert form.is_valid()
    instance = form.save(commit=False)
    assert instance.word == word
    assert instance.paradigm == paradigm


@pytest.mark.django_db
def test_conjugation_form_invalid_regex(english_project):
    # Set a regex that only allows lowercase letters
    english_project.tok_ples_validator = r"^[a-z]+$"
    english_project.save()
    paradigm = models.Paradigm.objects.create(
        name="TestParadigm",
        project=english_project,
        part_of_speech="n",
        row_labels=["row1"],
        column_labels=["col1"],
    )
    word = models.LexiconEntry.objects.create(
        project=english_project, tok_ples="foo", eng="bar"
    )
    form = forms.ConjugationForm(
        data={"conjugation": "INVALID123"},
        paradigm=paradigm,
        word=word,
    )
    assert not form.is_valid()
    assert "contains unallowed characters" in str(form.errors)


@pytest.mark.django_db
def test_conjugation_formset_save_creates_and_deletes(english_project):
    paradigm = models.Paradigm.objects.create(
        name="TestParadigm",
        project=english_project,
        part_of_speech="n",
        row_labels=["row1", "row2"],
        column_labels=["col1", "col2"],
    )
    word = models.LexiconEntry.objects.create(
        project=english_project, tok_ples="foo", eng="bar"
    )
    # Simulate a POST with two filled cells and two empty
    data = {
        "form-TOTAL_FORMS": "4",
        "form-INITIAL_FORMS": "0",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
        "form-0-conjugation": "a",
        "form-1-conjugation": "",
        "form-2-conjugation": "b",
        "form-3-conjugation": "",
    }
    formset = forms.get_conjugation_formset(paradigm, data=data, word=word)
    assert formset.is_valid()
    instances = formset.save()
    assert len(instances) == 2
    assert models.Conjugation.objects.filter(word=word, paradigm=paradigm).count() == 2

    # Now simulate a POST that deletes one
    data["form-0-conjugation"] = ""
    formset = forms.get_conjugation_formset(paradigm, data=data, word=word)
    assert formset.is_valid()
    instances = formset.save()
    assert models.Conjugation.objects.filter(word=word, paradigm=paradigm).count() == 1


@pytest.mark.django_db
def test_get_conjugation_formset_initial_data(english_project):
    paradigm = models.Paradigm.objects.create(
        name="TestParadigm",
        project=english_project,
        part_of_speech="n",
        row_labels=["row1"],
        column_labels=["col1", "col2"],
    )
    word = models.LexiconEntry.objects.create(
        project=english_project, tok_ples="foo", eng="bar"
    )
    # Create one existing conjugation
    models.Conjugation.objects.create(
        word=word, paradigm=paradigm, row=0, column=1, conjugation="existing"
    )
    formset = forms.get_conjugation_formset(
        paradigm,
        word=word,
        queryset=models.Conjugation.objects.filter(word=word, paradigm=paradigm),
    )
    assert (
        formset.forms[1].fields["conjugation"].initial is None
    )  # because initial is set on the form, not the field
    assert formset.forms[1].initial["conjugation"] == "existing"
