import logging

from django.http import JsonResponse
from django.views.generic import TemplateView

from apps.lexicon.utils import hunspell
from apps.lexicon.views.word_views import ProjectContextMixin

user_log = logging.getLogger("user_log")


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
