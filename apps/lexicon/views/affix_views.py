import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView

from apps.lexicon import forms, models
from apps.lexicon.permissions import ProjectEditPermissionRequiredMixin
from apps.lexicon.utils import hunspell
from apps.lexicon.views.word_views import ProjectContextMixin

user_log = logging.getLogger("user_log")
log = logging.getLogger("lexicon")


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class AffixTester(ProjectContextMixin, TemplateView):
    """A view for submitting a basic form to test affixes at lexicon/<lang-code>/affix-tester.

    Includes AffixResults view via htmx to show the results of the affix generation. Hunspell
    combines the words and affixes to generate new words."""

    template_name = "lexicon/affix_tester.html"

    def get_context_data(self, **kwargs):
        """Add affix file information to the template context."""
        context = super().get_context_data(**kwargs)
        project = (
            self.get_project()
        )  # Manually call get_project from ProjectContextMixin
        context["affix_file"] = project.affix_file
        return context


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class AffixResults(TemplateView):
    template_name = "lexicon/includes/affix_results.html"

    def get(self, request, *args, **kwargs):
        try:
            # Try to generate context as normal
            context = self.get_context_data(**kwargs)
        except Exception as e:
            return JsonResponse(
                {
                    "error": "An error occurred while processing the affixes.",
                    "details": str(e),
                },
                status=500,
            )
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        user_log.info(f"{self.request.user} requested affix generation")
        context = super().get_context_data(**kwargs)
        words = self.request.GET.get("words")
        affix = self.request.GET.get("affix")
        # Call the unmunch function (may raise)
        result = hunspell.unmunch(words, affix)
        context.update({"generated_words": result})
        return context


class AffixMixin:
    """Mixin to provide common functionality for affix-related views."""

    context_object_name = "affix"
    model = models.Affix

    def get_project(self) -> models.LexiconProject:
        lang_code = self.kwargs.get("lang_code")
        return get_object_or_404(models.LexiconProject, language_code=lang_code)

    def get_word(self) -> models.LexiconEntry:
        word_pk = self.kwargs.get("pk")
        return get_object_or_404(models.LexiconEntry, pk=word_pk)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["lang_code"] = self.get_project().language_code
        context["word"] = self.get_word()
        return context


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class AffixManagement(AffixMixin, TemplateView):
    """A view for managing affixes at lexicon/<lang-code>/affix-management."""

    template_name = "lexicon/includes/affixes/affix_management.html"

    def get_context_data(self, **kwargs) -> dict:
        """Add affix file information to the template context."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["affix_file"] = project.affix_file
        return context


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class AffixList(AffixMixin, ListView):
    """A view for listing affixes at lexicon/<lang-code>/affix-list/<int:pk>."""

    template_name = "lexicon/includes/affixes/affix_list.html"

    def get_queryset(self):
        project = self.get_project()
        return models.Affix.objects.filter(project=project)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        word = self.get_word()
        context["word_affix_ids"] = set(word.affixes.values_list("id", flat=True))
        return context


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class UpdateWordAffixes(
    AffixMixin, LoginRequiredMixin, ProjectEditPermissionRequiredMixin, UpdateView
):
    """A view for updating word affixes at lexicon/<lang-code>/word-affix/<int:pk>/update/."""

    model = models.LexiconEntry
    form_class = forms.WordAffixForm
    template_name = "lexicon/forms/word_affix_form.html"

    def get_success_url(self) -> str:
        """Return the URL to redirect to after successfully updating word affixes.

        During the htmx request normally used this code is not needed, but it is included
        to ensure that the form submission can be handled correctly in both htmx and non-htmx contexts."""
        # Return to the affix list fragment for this word
        return reverse(
            "lexicon:word_affix_list",
            kwargs={
                "lang_code": self.get_project().language_code,
                "pk": self.get_word().pk,
            },
        )

    def form_valid(self, form) -> HttpResponseRedirect | HttpResponse:
        """Handle valid form submission for updating word affixes.

        A redirect is used to make a GET request to the list view."""
        log.debug(f"Form valid for affix update: {form.cleaned_data}")
        user_log.info(
            f"{self.request.user} updated affixes for word {self.get_word().text}"
        )
        response = super().form_valid(form)
        if self.request.headers.get("HX-Request") == "true":
            url = reverse(
                "lexicon:word_affix_list",
                kwargs={
                    "lang_code": self.get_project().language_code,
                    "pk": self.object.pk,
                },
            )
            return HttpResponseRedirect(url)
        return response
