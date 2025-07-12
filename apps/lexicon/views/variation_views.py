import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from apps.lexicon import forms, models, tasks

log = logging.getLogger("lexicon")
user_log = logging.getLogger("user_log")


class WordContextMixin:
    """Mixin to add the LexiconEntry (word) to the context."""

    word_context_object_name = "word"
    model = models.Variation

    def get_word(self):
        """Get the LexiconEntry instance for this view."""
        # For views with 'word_pk' in kwargs
        word_pk = self.kwargs.get("word_pk")
        if word_pk:
            return get_object_or_404(models.LexiconEntry, pk=word_pk)
        # For views with self.object.word (Update/Delete)
        if hasattr(self, "object") and hasattr(self.object, "word"):
            return self.object.word
        # For views with self.object (Variation) and .word attribute
        obj = getattr(self, "object", None)
        if obj and hasattr(obj, "word"):
            return obj.word
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        word = self.get_word()
        if word:
            context[self.word_context_object_name] = word
        # add the edit context variable so the edit view uses right link
        # the create view overwrites this to get it's correct link
        context["form_type"] = "edit"
        context["lang_code"] = word.project.language_code
        return context

    # success url is same for all views that need it
    def get_success_url(self):
        # Redirect to the variation list for the current word
        return reverse(
            "lexicon:variation_list",
            kwargs={
                "lang_code": self.object.word.project.language_code,
                "word_pk": self.object.word.pk,
            },
        )


class VariationList(WordContextMixin, ListView):
    """A list of all available variations to be shown by htmx.

    This view is included by the in word_views.EntryDetail view."""

    template_name = "lexicon/includes/variations/variation_list.html"

    def get_queryset(self) -> dict:
        self.word = get_object_or_404(
            models.LexiconEntry, pk=self.kwargs.get("word_pk")
        )
        return models.Variation.objects.filter(word=self.word)


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class CreateVariation(WordContextMixin, LoginRequiredMixin, CreateView):
    """Show an in row form and uses that to create new variations."""

    template_name = "lexicon/includes/variations/variation_edit.html"
    form_class = forms.VariationForm

    def form_valid(self, form, *args, **kwargs):
        obj = form.save(commit=False)
        obj.word = self.get_word()
        user_log.info(
            f"{self.request.user} created a Variation for word {self.get_word()}."
        )
        return super().form_valid(form, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_type"] = "create"
        return context


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class UpdateVariation(WordContextMixin, LoginRequiredMixin, UpdateView):
    """Provides a table row edit form for the Variation List."""

    template_name = "lexicon/includes/variations/variation_edit.html"
    form_class = forms.VariationForm

    def post(self, request, *args, **kwargs):
        log.debug("lexicon:variation_update POST request.")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        tasks.update_lexicon_entry_search_field(self.object.word.pk)
        user_log.info(
            f"{self.request.user} created a Variation for word {self.get_word()}."
        )
        return super().form_valid(form)


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class DeleteVariation(WordContextMixin, LoginRequiredMixin, DeleteView):
    """Delete Variations inline from the table."""

    template_name = "lexicon/includes/variations/variation_confirm_delete.html"

    def post(self, request, *args, **kwargs) -> HttpResponse:
        log.debug("lexicon:variation_delete view POST request.")
        user_log.info(f"{request.user} deleted an Variation from {self.get_word()}.")
        return super().post(request, *args, **kwargs)
