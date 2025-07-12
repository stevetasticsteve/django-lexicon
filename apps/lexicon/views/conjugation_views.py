import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse
from django.http.request import HttpRequest as HttpRequest
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView
from django.template.loader import render_to_string


from apps.lexicon import forms, models
from apps.lexicon.permissions import ProjectEditPermissionRequiredMixin
from apps.lexicon.tasks import update_lexicon_entry_search_field
from apps.lexicon.views.word_views import ProjectContextMixin

user_log = logging.getLogger("user_log")
log = logging.getLogger("lexicon")


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class paradigm_modal(
    ProjectContextMixin,
    LoginRequiredMixin,
    ProjectEditPermissionRequiredMixin,
    FormView,
):
    """A view to select a paradigm for a word. Accessed by button in the word detail view.

    Displays a modal dialog with a form to select a paradigm.
    The form is submitted via htmx and the selected paradigm is applied to the word.
    Found at lexicon/<lang code>/<pk>/paradigm-modal.
    The response is a 204 No Content to close the modal dialog."""

    template_name = "lexicon/includes/paradigm_modal.html"
    form_class = forms.ParadigmSelectForm

    def post(self, request, *args, **kwargs):
        log.debug("lexicon:word_paradigm_modal POST request.")
        return super().post(request, *args, **kwargs)

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
        selected_paradigm = models.Paradigm.objects.get(
            pk=form.cleaned_data["paradigm"]
        )
        word = models.LexiconEntry.objects.get(pk=self.kwargs.get("pk"))
        word.paradigms.add(selected_paradigm)
        log.debug(f"'{selected_paradigm}' applied to '{word}'")
        response = HttpResponse(status=204)  # No content
        response["HX-Trigger"] = "paradigmSaved"  # closes the modal dialog
        return response


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class ConjugationGridView(ProjectContextMixin, LoginRequiredMixin, View):
    """A view to render and edit a conjugation grid for a word.

    GET responds with a html snippet to be inserted into the page, in view or edit mode.
    POST updates the conjugations and returns a html snippet to be inserted into the page.
    """

    view_template = "lexicon/includes/conjugation_grid/conjugation_grid_view.html"
    edit_template = "lexicon/includes/conjugation_grid/conjugation_grid_edit.html"


    def get(self, request, lang_code, word_pk, paradigm_pk, edit):
        log.debug(f"lexicon:conjugation_grid view GET request. {lang_code}")
        context = self._context_lookup(word_pk, paradigm_pk)
        template = self.edit_template if edit == "edit" else self.view_template
        return render(request, template, context)

    @transaction.atomic
    def post(self, request, lang_code, word_pk, paradigm_pk, *args, **kwargs):
        """Upon a post request save the conjugation values to the database."""

        word = models.LexiconEntry.objects.get(pk=word_pk)
        paradigm = models.Paradigm.objects.get(pk=paradigm_pk)
        project = word.project

        if not self.request.user.has_perm("edit_lexiconproject", project):
            log.debug(f"User {request.user} does not have permission to edit {project}.")
            html = render_to_string("lexicon/includes/403_permission_error.html", request=request)
            return HttpResponse(html, status=403)

        

        formset = self._get_or_create_formset_context(word, paradigm, request.POST)
        log.debug(
            f"lexicon:conjugation_grid view POST submitted. {lang_code} \nFormset post data = '{formset.data}'"
        )
        if formset.is_valid():
            log.debug("Formset is valid")
            formset.save()
            # Trigger a celery task to update the search field
            update_lexicon_entry_search_field(word_pk)
            # Success: re-render the view template
            context = self._context_lookup(word_pk, paradigm_pk, data=request.POST)
            return render(request, self.view_template, context)
        else:
            # Errors: re-render the edit template with errors
            log.debug(
                f"Paradigm conjugation formset is NOT valid. \nFormset errors = '{formset.errors}'"
            )
            context = self._context_lookup(word_pk, paradigm_pk, data=request.POST)
            context["formset"] = formset
            return render(request, self.edit_template, context)

    def _context_lookup(self, word_pk, paradigm_pk, data=None):
        """Return required context for both view and edit."""

        word = models.LexiconEntry.objects.get(pk=word_pk)
        paradigm = models.Paradigm.objects.get(pk=paradigm_pk)

        # The dict_get template tag can read it
        conjugations = models.Conjugation.objects.filter(word=word, paradigm=paradigm)
        conjugation_grid = {}
        for c in conjugations:
            conjugation_grid.setdefault(c.row, {})[c.column] = c.conjugation

        formset = self._get_or_create_formset_context(word, paradigm, data=data)
        # Create a grid of forms for the template
        forms_grid = []
        forms_iter = iter(formset.forms)
        for _ in range(len(paradigm.row_labels)):
            row = []
            for _ in range(len(paradigm.column_labels)):
                row.append(next(forms_iter))
            forms_grid.append(row)

        return {
            "conjugation_grid": conjugation_grid,
            "word": word,
            "paradigm": paradigm,
            "formset": formset,
            "forms_grid": forms_grid,
            "lang_code": word.project.language_code,
        }

    def _get_or_create_formset_context(self, word, paradigm, data=None):
        """Single method to handle formset creation for both GET and POST."""
        qs = models.Conjugation.objects.filter(word=word, paradigm=paradigm).order_by(
            "row", "column"
        )

        formset = forms.get_conjugation_formset(
            paradigm, queryset=qs, data=data, word=word if data else None
        )

        return formset
