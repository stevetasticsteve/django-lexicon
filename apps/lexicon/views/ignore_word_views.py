import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from apps.lexicon import models
from apps.lexicon.permissions import ProjectEditPermissionRequiredMixin
from apps.lexicon.views.word_views import ProjectContextMixin

user_log = logging.getLogger("user_log")
log = logging.getLogger("lexicon")


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class IgnoreList(ProjectContextMixin, TemplateView):
    """The list of ignore words.

    Found at lexicon/<lang code>/ignore
    It contains lexicon:ignore-search via htmx."""

    template_name = "lexicon/ignore_list.html"


class IgnoreWordMixin(
    ProjectContextMixin, LoginRequiredMixin, ProjectEditPermissionRequiredMixin
):
    """A base class for ignore word forms."""

    template_name = "lexicon/ignore_form.html"
    model = models.IgnoreWord
    fields = ("tok_ples", "type", "eng", "comments")

    def get_success_url(self):
        return reverse(
            "lexicon:ignore_list",
            args=(self.get_project().language_code,),
        )


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class CreateIgnoreWordView(IgnoreWordMixin, CreateView):
    """The view at url lexicon/ignore/1/create. Creates a new ignore view."""

    def form_valid(self, form, **kwargs) -> HttpResponse:
        """Handle the integrity error for unique ignore words."""
        try:
            obj = form.save(commit=False)
            obj.project = self.get_project()
            obj.save()
            user_log.info(
                f"{self.request.user} created an ignore word in {self.get_project()} lexicon."
            )
            return super().form_valid(form, **kwargs)
        except IntegrityError as e:
            log.debug(f"IntegrityError: {e}")
            error_msg = "Ignore word must be unique for this project."
            if self.request.headers.get("HX-Request") == "true":
                return HttpResponse(error_msg, status=400)
            form.add_error(None, error_msg)
            return self.form_invalid(form)


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class UpdateIgnoreWordView(IgnoreWordMixin, UpdateView):
    """The view at url lexicon/ignore/1/update. Updates a new ignore view."""

    def form_valid(self, form, **kwargs) -> HttpResponse:
        """Handle the integrity error for unique ignore words."""
        try:
            obj = form.save(commit=False)
            obj.project = self.get_project()
            obj.save()
            user_log.info(
                f"{self.request.user} updated an ignore word in {self.get_project()} lexicon."
            )
            return super().form_valid(form, **kwargs)
        except IntegrityError:
            log.debug("IntegrityError: Ignore word must be unique for this project.")
            error_msg = "Ignore word must be unique for this project."
            if self.request.headers.get("HX-Request") == "true":
                return HttpResponse(error_msg, status=400)
            form.add_error(None, error_msg)
            return self.form_invalid(form)


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class DeleteIgnoreWordView(IgnoreWordMixin, DeleteView):
    """The view at url lexicon/ignore/1/delete. Deletes a new ignore view."""

    template_name = "lexicon/confirm_entry_delete.html"

    def post(self, request, *args, **kwargs) -> HttpResponse:
        user_log.info(
            f"{request.user} deleted an ignore word in {self.get_project()} lexicon."
        )
        return super().post(request, *args, **kwargs)
