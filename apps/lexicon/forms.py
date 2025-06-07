import logging

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory

from apps.lexicon.models import Conjugation

log = logging.getLogger("lexicon")

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


class ParadigmGridForm(forms.Form):
    def __init__(self, *args, paradigm, word, **kwargs):
        super().__init__(*args, **kwargs)
        self.paradigm = paradigm
        self.word = word
        self.row_labels = paradigm.row_labels
        self.column_labels = paradigm.column_labels

        for i, row in enumerate(self.row_labels):
            for j, col in enumerate(self.column_labels):
                field_name = f"cell_{i}_{j}"
                existing = Conjugation.objects.filter(
                    paradigm=paradigm, word=word, row=i, column=j
                ).first()
                self.fields[field_name] = forms.CharField(
                    required=False,
                    initial=existing.form if existing else "",
                    label=f"{row} / {col}",
                )


class ImportForm(forms.Form):
    file = forms.FileField()
    format = forms.ChoiceField(choices=(("dic", ".dic"), ("csv", ".csv")))


class ExportForm(forms.Form):
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
        model = Conjugation
        fields = ["conjugation"]
        widgets = {
            "conjugation": forms.TextInput(
                attrs={"placeholder": "—", "class": "form-control"}
            ),
        }


class BaseConjugationFormSet(BaseModelFormSet):
    """A custom formset to use to save a grid of conjugations.

    Overides the clean method to delete blank conjugation entries"""

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
            # Only process valid forms!
            if not form.is_valid():
                continue

            conjugation_value = form.cleaned_data.get("conjugation", "").strip()
            if conjugation_value:  # Only process non-empty conjugations
                row = idx // num_cols
                column = idx % num_cols

                # Get or create the conjugation instance
                instance, created = Conjugation.objects.get_or_create(
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
                    f"{'Created' if created else 'Updated'} conjugation: {conjugation_value} at ({row}, {column})"
                )

            else:
                # If the conjugation is empty but an instance exists, delete it
                row = idx // num_cols
                column = idx % num_cols
                try:
                    existing = Conjugation.objects.get(
                        word=self.word, paradigm=paradigm, row=row, column=column
                    )
                    if commit:
                        existing.delete()
                    log.debug(f"Deleted empty conjugation at ('{row}, {column}')")
                except Conjugation.DoesNotExist:
                    pass  # Nothing to delete

        return instances


def get_conjugation_formset(paradigm, data=None, queryset=None, word=None, extra=None):
    total_cells = len(paradigm.row_labels) * len(paradigm.column_labels)

    # Create a formset with the right number of forms, but don't pre-populate with empty instances
    ConjugationFormSet = modelformset_factory(
        Conjugation,
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
            queryset=Conjugation.objects.none(),  # Don't pre-populate with instances
            initial=initial_data,
            form_kwargs={"paradigm": paradigm, "word": word},
            word=word,
            paradigm=paradigm,
        )
    else:
        # For POST requests, use the submitted data
        return ConjugationFormSet(
            data,
            queryset=Conjugation.objects.none(),
            form_kwargs={"paradigm": paradigm, "word": word},
            word=word,
            paradigm=paradigm,
        )
