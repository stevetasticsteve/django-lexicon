import logging

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
from django.urls import reverse_lazy

from apps.lexicon import models

log = logging.getLogger("lexicon")

# fields that can be edited for the LexiconEntry object
# The view references this var setting up generic edit views
editable_fields = [
    "tok_ples",
    "eng",
    "oth_lang",
    "pos",
    "comments",
    "checked",
    "review",
    "review_comments",
]


class ParadigmSelectForm(forms.Form):
    """The form that appears in the paradigm modal.
    Populates the choices dropdown with suitable paradigms."""

    paradigm = forms.ChoiceField(choices=[])  # empty choices initially

    def __init__(self, *args, paradigms=None, object=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.paradigms = paradigms
        self.object = object

        if self.paradigms:
            # Example: set choices based on available paradigms
            choices = [(p.pk, str(p)) for p in self.paradigms]
        else:
            choices = [("none", "No choices available")]
        self.fields["paradigm"].choices = choices


class ImportForm(forms.Form):
    """The form for choosing import format from a dropdown."""

    file = forms.FileField()
    format = forms.ChoiceField(choices=(("dic", ".dic"), ("csv", ".csv")))


class ExportForm(forms.Form):
    """The form for choosing export formats from a dropdown."""

    checked = forms.BooleanField(
        label="Limit export to only checked entries?", initial=True, required=False
    )
    export_type = forms.ChoiceField(
        label="File format for export",
        required=False,
        choices=(
            (
                "oxt",
                "libre office .oxt",
            ),
            (
                "dic",
                "word .dic",
            ),
            (
                "xml",
                "paratext .xml",
            ),
        ),
    )


class ConjugationForm(forms.ModelForm):
    """A grid layout form that displays and edits Conjugation objects in a paradigm.

    It is combined with the BaseConjugationFormSet to achieve the grid form."""

    def __init__(self, *args, **kwargs):
        self.paradigm = kwargs.pop("paradigm", None)
        self.word = kwargs.pop("word", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        # Set these on the instance before validation
        if self.word:
            self.instance.word = self.word
        if self.paradigm:
            self.instance.paradigm = self.paradigm
        return super().clean()

    class Meta:
        model = models.Conjugation
        fields = ["conjugation"]
        widgets = {
            "conjugation": forms.TextInput(
                attrs={"placeholder": "—", "class": "form-control"}
            ),
        }


class BaseConjugationFormSet(BaseModelFormSet):
    """A custom formset to use to save a grid of conjugations.

    Overides the clean method to delete blank conjugation entries.
    Overides the save method to fill in the required row,column, word and paradigm
    fields."""

    def __init__(self, *args, word=None, paradigm=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.word = word
        self.paradigm = paradigm

    def save(self, commit=True):
        if not self.forms:
            return []

        paradigm = self.paradigm
        num_cols = len(paradigm.column_labels)
        instances = []

        for idx, form in enumerate(self.forms):
            conjugation_value = form.cleaned_data.get("conjugation", "").strip()
            if conjugation_value:  # Only process non-empty conjugations
                row = idx // num_cols
                column = idx % num_cols

                # Get or create the conjugation instance
                instance, created = models.Conjugation.objects.get_or_create(
                    word=self.word,
                    paradigm=paradigm,
                    row=row,
                    column=column,
                    defaults={"conjugation": conjugation_value},
                )

                # If it already exists, update the conjugation value
                if not created:
                    instance.conjugation = conjugation_value
                    if commit:
                        instance.save()

                instances.append(instance)
                log.debug(
                    f"{'Created' if created else 'Updated'} conjugation: '{conjugation_value}' at '({row}, {column})'"
                )

            else:
                # If the conjugation is empty but an instance exists, delete it
                row = idx // num_cols
                column = idx % num_cols
                try:
                    existing = models.Conjugation.objects.get(
                        word=self.word, paradigm=paradigm, row=row, column=column
                    )
                    if commit:
                        existing.delete()
                    log.debug(f"Deleted empty conjugation at '({row}, {column})'")
                except models.Conjugation.DoesNotExist:
                    pass  # Nothing to delete

        return instances


def get_conjugation_formset(paradigm, data=None, queryset=None, word=None):
    """Creates a conjugation formset suitable for GET and POST requests.

    Combines ConjugationForms together with BaseConjugationFormset and provides
    a simple function to call in the view."""
    total_cells = len(paradigm.row_labels) * len(paradigm.column_labels)

    # Create a formset with the right number of forms, but don't pre-populate with empty instances
    ConjugationFormSet = modelformset_factory(
        models.Conjugation,
        form=ConjugationForm,
        formset=BaseConjugationFormSet,
        extra=total_cells,  # Create enough forms for the full grid
        can_delete=False,  # We handle deletion manually
    )

    # Create initial data structure for the grid
    if not data:
        # For GET requests, populate with existing conjugations
        existing_conjugations = {}
        if queryset:
            for conj in queryset:
                grid_index = conj.row * len(paradigm.column_labels) + conj.column
                existing_conjugations[grid_index] = {"conjugation": conj.conjugation}

        # Create initial data for all grid positions
        initial_data = []
        for i in range(total_cells):
            initial_data.append(existing_conjugations.get(i, {"conjugation": ""}))

        return ConjugationFormSet(
            queryset=models.Conjugation.objects.none(),  # Don't pre-populate with instances
            initial=initial_data,
            form_kwargs={"paradigm": paradigm, "word": word},
            word=word,
            paradigm=paradigm,
        )
    else:
        # For POST requests, use the submitted data
        return ConjugationFormSet(
            data,
            queryset=models.Conjugation.objects.none(),
            form_kwargs={"paradigm": paradigm, "word": word},
            word=word,
            paradigm=paradigm,
        )


class VariationForm(forms.ModelForm):
    """A form for editing a Variation object."""

    class Meta:
        model = models.Variation
        fields = ["text", "type", "included_in_spellcheck", "included_in_search"]  #
        widgets = {
            "text": forms.TextInput(attrs={"class": "form-control"}),
            "type": forms.Select(attrs={"class": "form-select"}),
            "included_in_spellcheck": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "included_in_search": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


class ParadigmForm(forms.ModelForm):
    """A form for editing a Paradigm object."""

    class Meta:
        model = models.Paradigm
        fields = ["name", "part_of_speech", "row_labels", "column_labels"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "part_of_speech": forms.Select(attrs={"class": "form-select"}),
            "row_labels": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "hx-post": reverse_lazy("json-validation"),
                    "hx-target": "#form_errors",
                    "hx-swap": "innerHTML",
                    "hx-trigger": "keyup",
                }
            ),
            "column_labels": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "hx-post": reverse_lazy("json-validation"),
                    "hx-target": "#form_errors",
                    "hx-swap": "innerHTML",
                    "hx-trigger": "keyup",
                },
            ),
        }


class AffixForm(forms.ModelForm):
    """A form for editing an Affix object."""

    class Meta:
        model = models.Affix
        fields = ["name", "applies_to", "affix_letter"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "affix_letter": forms.Select(attrs={"class": "form-select"}),
            "applies_to": forms.Select(attrs={"class": "form-select"}),
        }

class WordAffixForm(forms.ModelForm):
    class Meta:
        model = models.LexiconEntry
        fields = ["affixes"]
        widgets = {
            "affixes": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["affixes"].label_from_instance = lambda obj: obj.name