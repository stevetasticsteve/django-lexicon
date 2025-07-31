import logging

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from apps.lexicon import models

user_log = logging.getLogger("user_log")
log = logging.getLogger("lexicon")


class ProjectSearchView(ListView):
    """Generic search view for project-scoped models.

    Subclasses should define 'model' and a 'search_field'. Search will alternate
    between the provided search_field and English toggle if applicable."""

    template_name = "lexicon/includes/search/results_list.html"
    paginate_by = 250
    english_search_field = "eng__icontains"

    def get_queryset(self) -> QuerySet:
        search = self.request.GET.get("search")
        self.project = get_object_or_404(
            models.LexiconProject, language_code=self.kwargs.get("lang_code")
        )
        query = self.model.objects.select_related("project").filter(
            project=self.project
        )
        if search:
            user_log.info(f"{self.request.user} used search.")
            # A search on related senses can return duplicate LexiconEntry objects.
            # We use distinct() to avoid this.
            return query.filter(**self.get_filter_kwargs()).distinct()
        else:
            return query

    def get_filter_kwargs(self) -> dict:
        """Return the query parameters for filtering."""
        search = self.request.GET.get("search")
        is_english = self.request.GET.get("eng") == "true"

        search_field = self.english_search_field if is_english else self.search_field
        return {search_field: search}

class LexiconSearchResults(ProjectSearchView):
    """Search results for lexicon entries."""

    model = models.LexiconEntry
    search_field = "search__icontains"
    english_search_field = "senses__eng__icontains"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related("senses")


class IgnoreSearchResults(ProjectSearchView):
    """Search results for ignore words."""

    template_name = "lexicon/includes/search/ignore_results.html"
    model = models.IgnoreWord
    search_field = "text__icontains"
