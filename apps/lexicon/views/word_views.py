import datetime
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from apps.lexicon import forms, models

user_log = logging.getLogger("user_log")
log = logging.getLogger("lexicon")


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


class LexiconView(ProjectContextMixin, TemplateView):
    """The main display for the lexicon, listing all entries.

    Found at lexicon/<lang code>/
    It contains lexicon:search inserted via htmx."""

    template_name = "lexicon/lexicon_list.html"


class EntryDetail(ProjectContextMixin, DetailView):
    """The view at url lexicon<lang code>/<pk>/detail. Displays all info in .db for a word."""

    model = models.LexiconEntry
    template_name = "lexicon/entry_detail.html"

    def get_context_data(self, **kwargs) -> dict:
        """Add the conjugations linked to the entry."""
        context = super().get_context_data(**kwargs)
        context["conjugations"] = models.Conjugation.objects.filter(
            word=self.object
        ).select_related("paradigm")
        context["paradigms"] = (
            self.object.paradigms.all()
        )  # Get all paradigms linked to the word
        return context


class CreateEntry(LoginRequiredMixin, ProjectContextMixin, CreateView):
    """The view at url lexicon/<lang code>/create. Creates a new word."""

    model = models.LexiconEntry
    fields = forms.editable_fields
    template_name = "lexicon/simple_form.html"

    def post(self, request, *args, **kwargs):
        log.debug("lexicon:create_entry view POST request.")
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        # When creating a word project cannot be retrieved from the db.
        # project is required for validation, so it is provided for object creation.
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.model(project=self.get_project())
        return kwargs

    def form_valid(self, form, **kwargs) -> HttpResponse:
        """Add the user to modified and the project to the LexiconEntry."""
        obj = form.save(commit=False)
        obj.modified_by = self.request.user.username
        obj.project = self.get_project()
        user_log.info(f"{self.request.user} created an entry in {obj.project} lexicon.")
        return super().form_valid(form, **kwargs)


class UpdateEntry(LoginRequiredMixin, ProjectContextMixin, UpdateView):
    """The view at url lexicon/<lang code>/<pk>/update. Updates words."""

    model = models.LexiconEntry
    fields = forms.editable_fields
    template_name = "lexicon/simple_form.html"

    def post(self, request, *args, **kwargs):
        log.debug("lexicon:update_entry view POST request.")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form, **kwargs) -> HttpResponse:
        """Add the user who submitted the POST"""
        self.object.modified_by = self.request.user.username
        if "review" in form.changed_data:
            self.object.review_user = self.request.user.username
            self.object.review_time = datetime.date.today()
        user_log.info(
            f"{self.request.user} edited an entry in {self.object.project} lexicon."
        )
        return super().form_valid(form, **kwargs)


class DeleteEntry(LoginRequiredMixin, ProjectContextMixin, DeleteView):
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


class ReviewList(ProjectContextMixin, ListView):
    """Shows entries marked for review at url lexicon/<lang code>/review."""

    model = models.LexiconEntry
    template_name = "lexicon/review_list.html"

    def get_queryset(self) -> dict:
        self.project = self.get_project()
        return models.LexiconEntry.objects.filter(project=self.project, review__gt=0)
