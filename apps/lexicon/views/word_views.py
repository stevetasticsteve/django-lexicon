import datetime
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from apps.lexicon import forms, models
from apps.lexicon.permissions import ProjectEditPermissionRequiredMixin
from apps.lexicon.utils.hunspell import unmunch

user_log = logging.getLogger("user_log")
log = logging.getLogger("lexicon")


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class ProjectList(ListView):
    """The home page that lists the different lexicon projects."""

    model = models.LexiconProject
    template_name = "lexicon/project_list.html"


class ProjectContextMixin:
    """A reusable mixin to provide project context for views."""

    def get_project(self) -> models.LexiconProject:
        """Retrieve the project based on the language code."""
        lang_code = self.kwargs.get("lang_code")
        return get_object_or_404(models.LexiconProject, language_code=lang_code)

    def get_context_data(self, **kwargs) -> dict:
        """Add project and lang_code to the context."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context.update({"lang_code": project.language_code, "project": project})
        return context


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class LexiconView(ProjectContextMixin, TemplateView):
    """The main display for the lexicon, listing all entries.

    Found at lexicon/<lang code>/
    It contains lexicon:search inserted via htmx."""

    template_name = "lexicon/lexicon_list.html"


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class EntryDetail(ProjectContextMixin, DetailView):
    """The view at url lexicon<lang code>/<pk>/detail. Displays all info in .db for a word."""

    model = models.LexiconEntry
    template_name = "lexicon/entry_detail.html"

    def get_object(self, queryset=None):
        queryset = self.get_queryset().prefetch_related("senses", "paradigms")
        return super().get_object(queryset=queryset)

    def get_context_data(self, **kwargs) -> dict:
        """Add the conjugations linked to the entry."""
        context = super().get_context_data(**kwargs)
        conjugations = models.Conjugation.objects.filter(
            word=self.object
        ).select_related("paradigm")
        context["conjugations"] = conjugations
        context["paradigms"] = (
            self.object.paradigms.all()
        )

        # generate hunspell words. util expects a string
        affix_letters = [c.affix_letter for c in self.object.affixes.all()]
        # create a list of conjugation words for hunspell
        hunspell_dic_words = [f"{c.conjugation}/{''.join(affix_letters)}" for c in conjugations]
        # append the main word to the list
        hunspell_dic_words.append(f"{self.object.text}/{''.join(affix_letters)}")
        # convert into a string
        hunspell_dic_words = "\n".join(hunspell_dic_words)
        aff = self.object.project.affix_file
        log.debug(f"Affix file: {aff}")
        log.debug(f"Hunspell dic words: {hunspell_dic_words}")

        if hunspell_dic_words and aff:
            hunspell_words = unmunch(
                hunspell_dic_words, aff
            )
            context["hunspell_words"] = hunspell_words
            context["hunspell_conjugations_number"] = len(hunspell_words)
        return context


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class CreateEntry(
    LoginRequiredMixin,
    ProjectEditPermissionRequiredMixin,
    ProjectContextMixin,
    CreateView,
):
    """The view at url lexicon/<lang code>/create. Creates a new word."""

    model = models.LexiconEntry
    form_class = forms.LexiconEntryForm
    template_name = "lexicon/forms/word_update_form.html"

    def post(self, request, *args, **kwargs):
        log.debug("lexicon:create_entry view POST request.")
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["sense_formset"] = forms.SenseFormSet(self.request.POST)
        else:
            context["sense_formset"] = forms.SenseFormSet()
        return context

    def get_form_kwargs(self):
        # When creating a word project cannot be retrieved from the db.
        # project is required for validation, so it is provided for object creation.
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.model(project=self.get_project())
        return kwargs

    def form_valid(self, form, **kwargs) -> HttpResponse:
        """Add user, project and sense formset to LexiconEntry."""
        log.info(self.request.POST)
        context = self.get_context_data()
        sense_formset = context["sense_formset"]
        if sense_formset.is_valid():
            obj = form.save(commit=False)
            obj.modified_by = self.request.user.username
            obj.project = self.get_project()
            obj.save()
            sense_formset.instance = obj
            sense_formset.save()
            user_log.info(
                f"{self.request.user} created an entry in {obj.project} lexicon."
            )
            return super().form_valid(form, **kwargs)
        else:
            log.info(f"Sense formset is invalid: '{sense_formset.errors}'")
            return self.form_invalid(form)


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class UpdateEntry(
    LoginRequiredMixin,
    ProjectEditPermissionRequiredMixin,
    ProjectContextMixin,
    UpdateView,
):
    """The view at url lexicon/<lang code>/<pk>/update. Updates words."""

    model = models.LexiconEntry
    form_class = forms.LexiconEntryForm
    template_name = "lexicon/forms/word_update_form.html"

    def post(self, request, *args, **kwargs):
        log.debug("lexicon:update_entry view POST request.")
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["sense_formset"] = forms.SenseFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context["sense_formset"] = forms.SenseFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        log.info(self.request.POST)
        context = self.get_context_data()
        sense_formset = context["sense_formset"]

        if sense_formset.is_valid():
            obj = form.save(commit=False)
            obj.modified_by = self.request.user.username
            if "review" in form.changed_data:
                obj.review_user = self.request.user.username
                obj.review_time = datetime.date.today()
            obj.save()
            sense_formset.instance = obj
            sense_formset.save()
            user_log.info(
                f"{self.request.user} edited an entry in {obj.project} lexicon."
            )
            return super().form_valid(form)
        else:
            log.info(f"Sense formset is invalid: '{sense_formset.errors}'")
            return self.form_invalid(form)


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class DeleteEntry(
    LoginRequiredMixin,
    ProjectEditPermissionRequiredMixin,
    ProjectContextMixin,
    DeleteView,
):
    """The view at url lexicon/<lang code>/<pk>/delete. Deletes a word."""

    model = models.LexiconEntry
    template_name = "lexicon/confirm_entry_delete.html"

    def get_success_url(self) -> str:
        return reverse("lexicon:entry_list", args=(self.kwargs.get("lang_code"),))

    def post(self, request, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        log.debug("lexicon:delete_entry view POST request.")
        user_log.info(
            f"{request.user} deleted an entry in {self.object.project} lexicon."
        )
        return super().post(request, *args, **kwargs)


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class ReviewList(ProjectContextMixin, ListView):
    """Shows entries marked for review at url lexicon/<lang code>/review."""

    model = models.LexiconEntry
    template_name = "lexicon/review_list.html"

    def get_queryset(self) -> dict:
        self.project = self.get_project()
        return models.LexiconEntry.objects.filter(project=self.project, review__gt=0)


@require_http_methods(["GET"])
def add_sense_form(request):
    """Return a new empty sense form for the formset."""
    form_count = int(request.GET.get("form_count", 0))
    log.debug(f"form_count: {form_count}")

    # Use the formset's `empty_form` property to get a form with the
    # `__prefix__` placeholder.
    formset = forms.SenseFormSet(prefix="senses")
    empty_form = formset.empty_form

    # Render the form template with the placeholder.
    html = render_to_string(
        "lexicon/forms/sense_form.html",
        {"sense_form": empty_form, "form_id": form_count},
        request=request,
    )

    # Replace the placeholder in the form fields with the actual form index.
    html = html.replace("__prefix__", str(form_count))
    log.debug(html)
    return HttpResponse(html)
