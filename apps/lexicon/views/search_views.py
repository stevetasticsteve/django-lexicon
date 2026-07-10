import logging
import re

from django.db import connection
from django.db.models import QuerySet
from django.db.utils import OperationalError
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from apps.lexicon import models

user_log = logging.getLogger("user_log")
log = logging.getLogger("lexicon")

MAX_SEARCH_LENGTH = 30
REGEX_STATEMENT_TIMEOUT_MS = 2000


class ProjectSearchView(ListView):
    """Generic search view for project-scoped models.
    Subclasses should define 'model' and a 'search_field'. Search will alternate
    between the provided search_field and English toggle if applicable."""

    template_name = "lexicon/includes/search/results_list.html"
    paginate_by = 250
    english_search_field = "eng__icontains"

    def get_queryset(self) -> QuerySet:
        search = self.request.GET.get("search")
        self.search_error = None
        self.project = get_object_or_404(
            models.LexiconProject, language_code=self.kwargs.get("lang_code")
        )
        query = self.model.objects.select_related("project").filter(
            project=self.project
        )

        if not search:
            return query

        if len(search) > MAX_SEARCH_LENGTH:
            self.search_error = (
                f"Search text too long (max {MAX_SEARCH_LENGTH} characters)."
            )
            return query.none()

        is_regex = self.request.GET.get("regex") == "true"

        if is_regex:
            try:
                re.compile(search)
            except re.error as e:
                self.search_error = f"Invalid regex: {e}"
                return query.none()

        user_log.info(f"'{self.request.user}' searched '{search}' in '{self.project}'.")

        try:
            if is_regex:
                # Scoped to this transaction only; won't affect other requests
                # sharing the connection.
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"SET LOCAL statement_timeout = {REGEX_STATEMENT_TIMEOUT_MS}"
                    )
                result = query.filter(**self.get_filter_kwargs()).distinct()
                # Force evaluation now so a timeout raises here, not at template
                # render time.
                result.exists()
            else:
                result = query.filter(**self.get_filter_kwargs()).distinct()

            return result

        except OperationalError as e:
            log.warning(f"Search error for '{search}' in '{self.project}': {e}")
            self.search_error = "Search timed out — try a simpler pattern."
            return query.none()

    def get_filter_kwargs(self) -> dict:
        """Return the query parameters for filtering."""
        search = self.request.GET.get("search")
        is_english = self.request.GET.get("eng") == "true"
        is_regex = self.request.GET.get("regex") == "true"
        base_field = self.english_search_field if is_english else self.search_field
        field_name, _, lookup = base_field.rpartition("__")
        if is_regex:
            lookup = (
                "iregex"  # case-insensitive; use "regex" if you want case-sensitive
            )
        return {f"{field_name}__{lookup}": search}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_error"] = getattr(self, "search_error", None)
        return context


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
