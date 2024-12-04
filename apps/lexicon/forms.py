from django import forms

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
