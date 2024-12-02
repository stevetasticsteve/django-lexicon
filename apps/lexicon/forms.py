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


class ImportDicForm(forms.Form):
    dic_file = forms.FileField()


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
