from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse


from apps.lexicon import models
from apps.lexicon import forms

import datetime


class ProjectList(ListView):
    """The home page that lists the different lexicon projects."""

    model = models.LexiconProject
    template_name = "lexicon/project_list.html"


class LexiconView(ListView):
    """The main display for the lexicon, listing all entries."""

    model = models.LexiconEntry
    template_name = "lexicon/lexicon_list.html"

    def get_context_data(self, **kwargs):
        """Data added to the context used in the template."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.kwargs.get("slug")
        context["object_list"] = models.LexiconEntry.objects.filter(
            project=models.LexiconProject.objects.get(
                language_code=self.kwargs.get("slug")
            )
        )
        return context


class EntryDetail(DetailView):
    """The view at url <lang code>/1/detail. Displays all info in .db for a word."""

    model = models.LexiconEntry
    template_name = "lexicon/entry_detail.html"

    # def get_context_data(self, **kwargs):
    #     """Add senses and variations for the template to use."""
    #     context = super().get_context_data(**kwargs)
    #     context["word_senses"] = models.KovolWordSense.objects.filter(word=self.object)
    #     context["spelling_variations"] = (
    #         models.KovolWordSpellingVariation.objects.filter(word=self.object)
    #     )
    #     context["phrases"] = models.PhraseEntry.objects.filter(linked_word=self.object)

    # return context


class CreateEntry(LoginRequiredMixin, CreateView):
    """The view at url <lang code>/create. Creates a new word."""

    model = models.LexiconEntry
    fields = forms.editable_fields
    template_name = "lexicon/simple_form.html"

    def form_valid(self, form, **kwargs):
        """When the form saves run this code."""
        obj = form.save(commit=False)
        obj.modified_by = self.request.user.username
        obj.project = models.LexiconProject.objects.get(
            language_code=self.kwargs.get("slug")
        )
        obj.save()
        return super().form_valid(form, **kwargs)


class UpdateEntry(LoginRequiredMixin, UpdateView):
    """The view at url <lang code>/<pk>/update. Updates words.

    get_context_data and form_valid are extended to add in inline formsets representing
    the one to many relationships of spelling variations and senses.
    The inline formsets allow deleting sense and spelling variations so a delete view
    isn't required.
    """

    model = models.LexiconEntry
    fields = forms.editable_fields
    template_name = "lexicon/simple_form.html"  # need a different form to insert senses

    # def get_context_data(self, **kwargs):
    #     """Add formsets to the context data for the template to use."""
    #     context = super().get_context_data(**kwargs)
    #     if self.request.POST:
    #         context["senses_form"] = sense_inline_form(
    #             self.request.POST, prefix="sense", instance=self.object
    #         )
    #         context["variation_form"] = variation_inline_form(
    #             self.request.POST, prefix="spelling_variation", instance=self.object
    #         )
    #     else:
    #         context["sense_form"] = sense_inline_form(
    #             prefix="sense", instance=self.object
    #         )
    #         context["variation_form"] = variation_inline_form(
    #             prefix="spelling_variation", instance=self.object
    #         )
    #     return context

    def form_valid(self, form, **kwargs):
        """Code that runs when the form has been submitted and is valid."""
        # context = self.get_context_data()
        # sense_form = context["senses_form"]
        # variation_form = context["variation_form"]
        # if sense_form.is_valid():
        #     sense_form.save()
        # if variation_form.is_valid():
        #     variation_form.save()

        # Add user the user who made modifications or requested a review
        self.object.modified_by = self.request.user.username
        if "review" in form.changed_data:
            self.object.review_user = self.request.user.username
            self.object.review_time = datetime.date.today()
        return super().form_valid(form, **kwargs)


class DeleteEntry(LoginRequiredMixin, DeleteView):
    """The view at url <lang code>/<pk>/delete. Deletes a word."""

    model = models.LexiconEntry
    fields = None
    template_name = "lexicon/confirm_entry_delete.html"

    def get_success_url(self):
        return reverse("lexicon:entry_list", args=(self.kwargs.get("slug"),))
