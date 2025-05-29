import logging

from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from apps.lexicon import models

user_log = logging.getLogger("user_log")


class SearchResults(ListView):
    """The actual lexicon entries, filtered by htmx-get."""

    template_name = "lexicon/includes/search-results.html"
    model = models.LexiconEntry
    paginate_by = 250

    def get_queryset(self, **kwargs):
        search = self.request.GET.get("search")
        is_english = self.request.GET.get("eng") == "true"

        # Determine the field to search based on `is_english`
        search_field = "eng__icontains" if is_english else "tok_ples__icontains"
        filter_kwargs = {search_field: search}

        self.project = get_object_or_404(
            models.LexiconProject, language_code=self.kwargs.get("lang_code")
        )
        query = models.LexiconEntry.objects.select_related("project").filter(
            project=self.project
        )
        if search:
            user_log.info(f"{self.request.user} used search.")
            return query.filter(**filter_kwargs)
        else:
            return query
