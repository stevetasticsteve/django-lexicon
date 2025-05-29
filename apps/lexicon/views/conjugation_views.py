import logging

from django.db import transaction
from django.http import HttpResponse
from django.http.request import HttpRequest as HttpRequest
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView

from apps.lexicon import forms, models
from apps.lexicon.views.word_views import ProjectContextMixin

user_log = logging.getLogger("user_log")
log = logging.getLogger("lexicon")


class paradigm_modal(ProjectContextMixin, FormView):
    template_name = "lexicon/includes/paradigm_modal.html"
    form_class = forms.ParadigmSelectForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Add extra data you want to pass
        project = models.LexiconEntry.objects.get(pk=self.kwargs.get("pk")).project
        kwargs["paradigms"] = models.Paradigm.objects.filter(project=project)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        word = models.LexiconEntry.objects.get(pk=self.kwargs.get("pk"))
        context["object"] = word
        return context

    def form_valid(self, form):
        # Do your processing here (e.g., save data)
        selected_paradigm = models.Paradigm.objects.get(
            pk=form.cleaned_data["paradigm"]
        )
        word = models.LexiconEntry.objects.get(pk=self.kwargs.get("pk"))
        word.paradigms.add(selected_paradigm)
        log.debug(f"{selected_paradigm} applied to {word}")
        response = HttpResponse(status=204)  # No content
        response["HX-Trigger"] = "paradigmSaved"  # closes the modal dialog
        return response


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class ParadigmView(View):
    """A view to render and edit conjugations for a word.

    GET responds with a html snippet to be inserted into the page.
    POST updates the conjugations and returns a html snippet to be inserted into the page.
    """

    view_template = "lexicon/includes/paradigm_view.html"
    edit_template = "lexicon/includes/paradigm_edit.html"

    def get(self, request, word_pk, paradigm_pk, edit):
        context = self._context_lookup(word_pk, paradigm_pk)
        template = self.edit_template if edit == "edit" else self.view_template
        return render(request, template, context)

    @transaction.atomic
    def post(self, request, word_pk, paradigm_pk, *args, **kwargs):
        """Upon a post request save the conjugation values to the database."""

        word = models.LexiconEntry.objects.get(pk=word_pk)
        paradigm = models.Paradigm.objects.get(pk=paradigm_pk)

        formset = self._get_or_create_formset_context(word, paradigm, request.POST)
        if formset.is_valid():
            log.debug("Formset is valid")
            formset.save()
            # Success: re-render the view template
            context = self._context_lookup(word_pk, paradigm_pk)
            return render(request, self.view_template, context)
        else:
            # Errors: re-render the edit template with errors
            log.debug("Formset is NOT valid")
            log.debug(formset.errors)
            context = self._context_lookup(word_pk, paradigm_pk)
            return render(request, self.edit_template, context)

    def _context_lookup(self, word_pk, paradigm_pk):
        """Return required context for both view and edit."""

        word = models.LexiconEntry.objects.get(pk=word_pk)
        paradigm = models.Paradigm.objects.get(pk=paradigm_pk)

        # Build a nested dict: {row_idx: {col_idx: conjugation_obj}}
        # The dict_get template tag can read it
        conjugations = models.Conjugation.objects.filter(word=word, paradigm=paradigm)
        conjugation_grid = {}
        for c in conjugations:
            conjugation_grid.setdefault(c.row, {})[c.column] = c.conjugation

        formset = self._get_or_create_formset_context(word, paradigm)
        # Create a grid of forms for the template
        # self._ensure_conjugations_exist(word, paradigm)
        forms_grid = []
        forms_iter = iter(formset.forms)
        for _ in range(len(paradigm.row_labels)):
            row = []
            for _ in range(len(paradigm.column_labels)):
                row.append(next(forms_iter))
            forms_grid.append(row)
        log.debug(f"forms_grid= {forms_grid}")

        return {
            "conjugation_grid": conjugation_grid,
            "word": word,
            "paradigm": paradigm,
            "formset": formset,
            "forms_grid": forms_grid,
        }

    # def _ensure_conjugations_exist(self, word, paradigm):
    #     """Ensure all grid positions have conjugation objects in the database."""
    #     for row_idx in range(len(paradigm.row_labels)):
    #         for col_idx in range(len(paradigm.column_labels)):
    #             models.Conjugation.objects.get_or_create(
    #                 word=word,
    #                 paradigm=paradigm,
    #                 row=row_idx,
    #                 column=col_idx,
    #                 defaults={"conjugation": ""},
    #             )

    def _get_or_create_formset_context(self, word, paradigm, data=None):
        """Single method to handle formset creation for both GET and POST."""
        # self._ensure_conjugations_exist(word, paradigm)
        qs = models.Conjugation.objects.filter(word=word, paradigm=paradigm).order_by(
            "row", "column"
        )

        formset = forms.get_conjugation_formset(
            paradigm, queryset=qs, data=data, word=word if data else None
        )

        return formset
