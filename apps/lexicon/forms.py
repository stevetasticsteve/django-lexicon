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
