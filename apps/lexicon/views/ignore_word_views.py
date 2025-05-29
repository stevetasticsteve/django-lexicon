import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.lexicon import models
from apps.lexicon.views.word_views import ProjectContextMixin

user_log = logging.getLogger("user_log")


class IgnoreList(ProjectContextMixin, TemplateView):
    template_name = "lexicon/ignore_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_view"] = "lexicon:ignore_search"
        return context


class IgnoreSearchResults(ListView):
    """The list of ignore words, filtered by htmx-get."""

    template_name = "lexicon/includes/ignore_search_results.html"
    model = models.IgnoreWord
    paginate_by = 250

    def get_queryset(self, **kwargs):
        search = self.request.GET.get("search")
        self.project = get_object_or_404(
            models.LexiconProject, language_code=self.kwargs.get("lang_code")
        )
        query = models.IgnoreWord.objects.select_related("project").filter(
            project=self.project
        )
        print(query)
        if search:
            return query.filter(tok_ples__icontains=search)
        else:
            return query


class IgnoreWordEditView(LoginRequiredMixin):
    """A base class for ignore word forms."""

    template_name = "lexicon/ignore_form.html"
    model = models.IgnoreWord
    fields = ("tok_ples", "type", "eng", "comments")

    def get_success_url(self):
        return reverse(
            "lexicon:ignore_list",
            args=(self.kwargs.get("lang_code"),),
        )


class CreateIgnoreWordView(IgnoreWordEditView, ProjectContextMixin, CreateView):
    """The view at url ignore/1/create. Creates a new ignore view."""

    def form_valid(self, form, **kwargs):
        """When the form saves run this code."""
        obj = form.save(commit=False)
        obj.project = get_object_or_404(
            models.LexiconProject, language_code=self.kwargs.get("lang_code")
        )
        obj.save()
        user_log.info(
            f"{self.request.user} created an ignore word in {obj.project} lexicon."
        )
        return super().form_valid(form, **kwargs)


class UpdateIgnoreWordView(IgnoreWordEditView, ProjectContextMixin, UpdateView):
    """The view at url ignore/1/update. Updates a new ignore view."""

    def form_valid(self, form, **kwargs):
        """When the form saves run this code."""
        obj = form.save(commit=False)
        obj.ignore_word_project = get_object_or_404(
            models.LexiconProject, language_code=self.kwargs.get("lang_code")
        )
        obj.save()
        user_log.info(
            f"{self.request.user} updated an ignore word in {obj.project} lexicon."
        )
        return super().form_valid(form, **kwargs)


class DeleteIgnoreWordView(IgnoreWordEditView, ProjectContextMixin, DeleteView):
    """The view at url ignore/1/delete. Deletes a new ignore view."""

    fields = None
    template_name = "lexicon/confirm_entry_delete.html"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_log.info(
            f"{request.user} deleted an ignore word in {self.object.project} lexicon."
        )
        return super().post(request, *args, **kwargs)
