import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView

from apps.lexicon import forms, models, tasks

log = logging.getLogger("lexicon")


class VariationList(ListView):
    """A list of all available variations to be shown by htmx.

    This view is included by the in word_views.EntryDetail view."""

    model = models.Variation
    template_name = "lexicon/includes/variations/variation_list.html"

    def get_queryset(self) -> dict:
        self.word = get_object_or_404(models.LexiconEntry, pk=self.kwargs.get("pk"))
        return models.Variation.objects.filter(word=self.word)


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class VariationEdit(LoginRequiredMixin, UpdateView):
    """Provides a table row edit form for the Variation List."""

    model = models.Variation
    template_name = "lexicon/includes/variations/variation_edit.html"
    form_class = forms.VariationForm
    context_object_name = "variation"

    def get_context_data(self, **kwargs):
        # add the word to context so the cancel link can redirect to the word's variation list
        context = super().get_context_data(**kwargs)
        context["word"] = self.object.word
        return context  # Redirect to the variation list for the current word

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        log.debug("lexicon:variation_edit POST request.")
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        # Redirect to the variation list for the current word
        return reverse("lexicon:variation_list", kwargs={"pk": self.object.word.pk})

    def form_valid(self, form):
        tasks.update_lexicon_entry_search_field(self.object.word.pk)
        return super().form_valid(form)
