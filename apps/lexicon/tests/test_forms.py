import pytest

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
    word = models.LexiconEntry.objects.create(project=english_project, text="foo")
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
    english_project.text_validator = r"^[a-z]+$"
    english_project.save()
    paradigm = models.Paradigm.objects.create(
        name="TestParadigm",
        project=english_project,
        part_of_speech="n",
        row_labels=["row1"],
        column_labels=["col1"],
    )
    word = models.LexiconEntry.objects.create(project=english_project, text="foo")
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
    word = models.LexiconEntry.objects.create(project=english_project, text="foo")
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
    word = models.LexiconEntry.objects.create(project=english_project, text="foo")
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


@pytest.mark.django_db
def test_paradigm_form_valid(english_project):
    form = forms.ParadigmForm(
        data={
            "name": "Test",
            "part_of_speech": "n",
            "row_labels": '["row1", "row2"]',
            "column_labels": '["col1", "col2"]',
        }
    )
    assert form.is_valid()
    instance = form.save(commit=False)
    assert instance.name == "Test"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field", ["name", "part_of_speech", "row_labels", "column_labels"]
)
def test_paradigm_form_required_fields(english_project, field):
    data = {
        "name": "Test",
        "part_of_speech": "n",
        "row_labels": '["row1"]',
        "column_labels": '["col1"]',
    }
    data[field] = ""
    form = forms.ParadigmForm(data=data)
    assert not form.is_valid()
    assert field in form.errors


@pytest.mark.django_db
def test_paradigm_form_invalid_json_labels(english_project):
    form = forms.ParadigmForm(
        data={
            "name": "Test",
            "part_of_speech": "n",
            "row_labels": "not a json",
            "column_labels": '["col1"]',
        }
    )
    assert not form.is_valid()
    assert "row_labels" in form.errors


@pytest.mark.django_db
def test_paradigm_form_non_list_json(english_project):
    form = forms.ParadigmForm(
        data={
            "name": "Test",
            "part_of_speech": "n",
            "row_labels": '"just a string"',
            "column_labels": '["col1"]',
        }
    )
    assert not form.is_valid()
    assert "Row and column labels must be lists." in form.errors["__all__"]


def test_paradigm_form_widget_attrs():
    form = forms.ParadigmForm()
    row_widget = form.fields["row_labels"].widget
    assert "hx-post" in row_widget.attrs
    assert "hx-target" in row_widget.attrs


@pytest.mark.django_db
def test_word_affix_form_renders_affixes(kovol_project):
    models.Affix.objects.create(
        project=kovol_project, name="Prefix A", applies_to="n", affix_letter="A"
    )
    models.Affix.objects.create(
        project=kovol_project, name="Prefix B", applies_to="n", affix_letter="B"
    )
    entry = models.LexiconEntry.objects.create(project=kovol_project, text="hobol")
    form = forms.WordAffixForm(instance=entry)
    html = form.as_p()
    assert "Prefix A" in html
    assert "Prefix B" in html
