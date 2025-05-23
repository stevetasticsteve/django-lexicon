from django import forms
from apps.lexicon.models import Conjugation

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
