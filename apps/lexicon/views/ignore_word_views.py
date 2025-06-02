import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from apps.lexicon import models
from apps.lexicon.views.word_views import ProjectContextMixin

user_log = logging.getLogger("user_log")


class IgnoreList(ProjectContextMixin, TemplateView):
    """The list of ignore words.

    Found at lexicon/<lang code>/ignore
    It contains lexicon:ignore-search via htmx."""

    template_name = "lexicon/ignore_list.html"


class IgnoreWordEditView(ProjectContextMixin, LoginRequiredMixin):
    """A base class for ignore word forms."""

    template_name = "lexicon/ignore_form.html"
    model = models.IgnoreWord
    fields = ("tok_ples", "type", "eng", "comments")

    def get_success_url(self):
        return reverse(
            "lexicon:ignore_list",
            args=(self.get_project().language_code,),
        )


class CreateIgnoreWordView(IgnoreWordEditView, CreateView):
    """The view at url lexicon/ignore/1/create. Creates a new ignore view."""

    def form_valid(self, form, **kwargs) -> HttpResponse:
        """When the form saves run this code."""
        obj = form.save(commit=False)
        obj.project = self.get_project()
        obj.save()
        user_log.info(
            f"{self.request.user} created an ignore word in {obj.project} lexicon."
        )
        return super().form_valid(form, **kwargs)


class UpdateIgnoreWordView(IgnoreWordEditView, UpdateView):
    """The view at url lexicon/ignore/1/update. Updates a new ignore view."""

    def form_valid(self, form, **kwargs) -> HttpResponse:
        """When the form saves run this code."""
        obj = form.save(commit=False)
        obj.project = self.get_project()
        obj.save()
        user_log.info(
            f"{self.request.user} updated an ignore word in {obj.project} lexicon."
        )
        return super().form_valid(form, **kwargs)


class DeleteIgnoreWordView(IgnoreWordEditView, DeleteView):
    """The view at url lexicon/ignore/1/delete. Deletes a new ignore view."""

    template_name = "lexicon/confirm_entry_delete.html"

    def post(self, request, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        user_log.info(
            f"{request.user} deleted an ignore word in {self.object.project} lexicon."
        )
        return super().post(request, *args, **kwargs)
