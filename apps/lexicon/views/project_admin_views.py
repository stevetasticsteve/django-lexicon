import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from apps.lexicon import forms, models
from apps.lexicon.views.word_views import ProjectContextMixin

log = logging.getLogger("lexicon")
user_log = logging.getLogger("user_log")


class ProjectAdmin(ProjectContextMixin, TemplateView):
    template_name = "lexicon/project_admin/project_admin.html"


class ParadigmMixin:
    """A reusable mixin to provide project context for paradigm views."""

    model = models.Paradigm
    context_object_name = "paradigm"

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

    def get_success_url(self):
        return reverse(
            "lexicon:paradigm_list",
            args=(self.get_project().language_code,),
        )


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class ManageParadigms(ParadigmMixin, TemplateView):
    template_name = "lexicon/project_admin/paradigms/paradigm_manage.html"


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class ParadigmList(ParadigmMixin, ListView):
    template_name = "lexicon/project_admin/paradigms/paradigm_list.html"

    def get_queryset(self) -> dict:
        return models.Paradigm.objects.filter(project=self.get_project())


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class CreateParadigm(ParadigmMixin, LoginRequiredMixin, CreateView):
    """Show an in row form and uses that to create new paradigms."""

    template_name = "lexicon/project_admin/paradigms/paradigm_edit.html"
    form_class = forms.ParadigmForm

    def form_valid(self, form, *args, **kwargs):
        obj = form.save(commit=False)
        obj.project = self.get_project()
        user_log.info(
            f"{self.request.user} created a Paradigm for project {self.get_project()}."
        )
        return super().form_valid(form, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_type"] = "create"
        return context


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class UpdateParadigm(ParadigmMixin, LoginRequiredMixin, UpdateView):
    """Provides a table row edit form for the Paradigm List."""

    template_name = "lexicon/project_admin/paradigms/paradigm_edit.html"
    form_class = forms.ParadigmForm

    def post(self, request, *args, **kwargs):
        log.debug("lexicon:paradigm_edit POST request.")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        # tasks.update_lexicon_entry_search_field(self.object.word.pk)
        user_log.info(
            f"{self.request.user} created a Paradigm for project {self.get_project()}."
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_type"] = "edit"
        return context


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class DeleteParadigm(ParadigmMixin, LoginRequiredMixin, DeleteView):
    """Delete Paradigms inline from the table."""

    template_name = "lexicon/project_admin/paradigms/paradigm_confirm_delete.html"

    def post(self, request, *args, **kwargs) -> HttpResponse:
        log.debug("lexicon:paradigm_delete view POST request.")
        user_log.info(f"{request.user} deleted an Paradigm from {self.get_project()}.")
        return super().post(request, *args, **kwargs)


class AffixMixin:
    """A reusable mixin to provide project context for affix views."""

    model = models.Affix
    context_object_name = "affix"

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

    def get_success_url(self):
        return reverse(
            "lexicon:affix_list",
            args=(self.get_project().language_code,),
        )


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class ManageAffixes(AffixMixin, TemplateView):
    template_name = "lexicon/project_admin/affixes/affix_manage.html"


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class AffixList(AffixMixin, ListView):
    """List all affixes for a project."""

    template_name = "lexicon/project_admin/affixes/affix_list.html"

    def get_queryset(self) -> dict:
        return models.Affix.objects.filter(project=self.get_project()).order_by("affix_letter")


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class CreateAffix(AffixMixin, LoginRequiredMixin, CreateView):
    """Show an in row form and uses that to create new affixes."""

    template_name = "lexicon/project_admin/affixes/affix_edit.html"
    form_class = forms.AffixForm

    def form_valid(self, form, *args, **kwargs):
        obj = form.save(commit=False)
        obj.project = self.get_project()

        try:
            valid = super().form_valid(form, **kwargs)
            user_log.info(
                f"{self.request.user} created an affix for project {self.get_project()}."
            )
            return valid
        except IntegrityError:
            log.debug("IntegrityError: Affix letter must be unique for this project.")
            error_msg = "Affix letter must be unique for this project."
            if self.request.headers.get("HX-Request") == "true":
                return HttpResponse(error_msg, status=400)
            form.add_error(None, error_msg)
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_type"] = "create"
        return context


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class UpdateAffix(AffixMixin, LoginRequiredMixin, UpdateView):
    """Provides a table row edit form for the affix List."""

    template_name = "lexicon/project_admin/affixes/affix_edit.html"
    form_class = forms.AffixForm

    def post(self, request, *args, **kwargs):
        log.debug("lexicon:affix_edit POST request.")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        user_log.info(
            f"{self.request.user} created an affix for project {self.get_project()}."
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_type"] = "edit"
        return context


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class DeleteAffix(AffixMixin, LoginRequiredMixin, DeleteView):
    """Delete affixes inline from the table."""

    template_name = "lexicon/project_admin/affixes/affix_confirm_delete.html"

    def post(self, request, *args, **kwargs) -> HttpResponse:
        log.debug("lexicon:affix_delete view POST request.")
        user_log.info(f"{request.user} deleted an affix from {self.get_project()}.")
        return super().post(request, *args, **kwargs)

