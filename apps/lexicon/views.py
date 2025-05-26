import datetime
import logging
import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import FileResponse, HttpResponse, JsonResponse
from django.http.request import HttpRequest as HttpRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, FormView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from apps.lexicon import forms, models, tasks
from apps.lexicon.utils import export, hunspell

user_log = logging.getLogger("user_log")
log = logging.getLogger("lexicon")


class ProjectList(ListView):
    """The home page that lists the different lexicon projects."""

    model = models.LexiconProject
    template_name = "lexicon/project_list.html"


class ProjectContextMixin:
    """A reusable mixin to provide project context for views."""

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


# class ProjectTemplateMixin(TemplateView):
#     """A base class to handle common context passing to templates.

#     All project pages need access to the lang_code context variable."""

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         self.lang_code = self.kwargs.get("lang_code")
#         context["lang_code"] = self.lang_code
#         self.project = get_object_or_404(
#             models.LexiconProject, language_code=self.kwargs.get("lang_code")
#         )
#         context["project"] = self.project
#         return context


class LexiconView(ProjectContextMixin, TemplateView):
    """The main display for the lexicon, listing all entries."""

    template_name = "lexicon/lexicon_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_view"] = "lexicon:search"
        return context


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


# class ProjectSingleMixin(SingleObjectMixin):
#     """A base class to handle common context passing to templates with Single Mixin.

#     All project pages need access to the lang_code context variable."""

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         self.lang_code = self.kwargs.get("lang_code")
#         context["lang_code"] = self.lang_code
#         self.project = get_object_or_404(
#             models.LexiconProject, language_code=self.kwargs.get("lang_code")
#         )
#         context["project"] = self.project
#         return context


class EntryDetail(ProjectContextMixin, DetailView):
    """The view at url <lang code>/1/detail. Displays all info in .db for a word."""

    model = models.LexiconEntry
    template_name = "lexicon/entry_detail.html"

    def get_context_data(self, **kwargs):
        """Add the conjugations linked to the entry."""
        context = super().get_context_data(**kwargs)
        context["conjugations"] = models.Conjugation.objects.filter(word=self.object)
        # context["paradigms"] = set(conj.paradigm for conj in context["conjugations"])
        context["paradigms"] = self.object.paradigms.all()  # Get all paradigms linked to the word

        return context

    # def get_context_data(self, **kwargs):
    #     """Add senses and variations for the template to use."""
    #     context = super().get_context_data(**kwargs)
    #     context["word_senses"] = models.KovolWordSense.objects.filter(word=self.object)
    #     context["spelling_variations"] = (
    #         models.KovolWordSpellingVariation.objects.filter(word=self.object)
    #     )
    #     context["phrases"] = models.PhraseEntry.objects.filter(linked_word=self.object)

    # return context


class CreateEntry(LoginRequiredMixin, ProjectContextMixin, CreateView):
    """The view at url <lang code>/create. Creates a new word."""

    model = models.LexiconEntry
    fields = forms.editable_fields
    template_name = "lexicon/simple_form.html"

    def form_valid(self, form, **kwargs):
        """When the form saves run this code."""
        obj = form.save(commit=False)
        obj.modified_by = self.request.user.username
        obj.project = get_object_or_404(
            models.LexiconProject, language_code=self.kwargs.get("lang_code")
        )
        obj.save()
        user_log.info(f"{self.request.user} created an entry in {obj.project} lexicon.")
        return super().form_valid(form, **kwargs)


class UpdateEntry(LoginRequiredMixin, ProjectContextMixin, UpdateView):
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
        user_log.info(
            f"{self.request.user} edited an entry in {self.object.project} lexicon."
        )

        return super().form_valid(form, **kwargs)


class DeleteEntry(LoginRequiredMixin, ProjectContextMixin, DeleteView):
    """The view at url <lang code>/<pk>/delete. Deletes a word."""

    model = models.LexiconEntry
    fields = None
    template_name = "lexicon/confirm_entry_delete.html"

    def get_success_url(self):
        return reverse("lexicon:entry_list", args=(self.kwargs.get("lang_code"),))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_log.info(
            f"{request.user} deleted an entry in {self.object.project} lexicon."
        )
        return super().post(request, *args, **kwargs)


class ImportPage(ProjectContextMixin, FormView):
    """The view ate url <lang code>/import. Provides an import form."""

    template_name = "lexicon/import_page.html"
    form_class = forms.ImportForm

    def form_valid(self, form, **kwargs):
        file = form.cleaned_data["file"]
        format = form.cleaned_data["format"]
        match format:
            case "dic":
                tasks.import_dic.delay(file.read(), self.kwargs.get("lang_code"))
            case "csv":
                tasks.import_csv.delay(file.read(), self.kwargs.get("lang_code"))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "lexicon:import-success",
            args=(self.kwargs.get("lang_code"),),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lang_code"] = self.kwargs.get("lang_code")
        return context


class ImportSuccess(ProjectContextMixin, TemplateView):
    """A simple page to inform user of import results <lang code>/import-result"""

    template_name = "lexicon/upload_result.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lang_code"] = self.kwargs.get("lang_code")
        return context


class ExportPage(FormView, ProjectContextMixin):
    """Lists the export options at <lang code>/export.

    The response is a http file attachment, so no success url is required."""

    template_name = "lexicon/export.html"
    form_class = forms.ExportForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lang_code"] = self.kwargs.get("lang_code")
        context["project"] = get_object_or_404(
            models.LexiconProject, language_code=self.kwargs.get("lang_code")
        )
        return context

    def form_valid(self, form, **kwargs):
        file = export.export_entries(
            form.cleaned_data["export_type"],
            get_object_or_404(
                models.LexiconProject, language_code=self.kwargs.get("lang_code")
            ),
            form.cleaned_data["checked"],
            self.request,
        )
        response = FileResponse(
            open(file, "rb"), as_attachment=True, filename=os.path.basename(file)
        )
        return response


def latest_oxt(request, lang_code):
    file = export.export_entries(
        "oxt",
        get_object_or_404(models.LexiconProject, language_code=lang_code),
        True,
        request,
    )
    response = FileResponse(open(file, "rb"), as_attachment=False)
    return response


def oxt_update_service(request, lang_code):
    """Respond to requests for an oxt update with xml update info."""
    # load the xml template
    with open(
        os.path.join("apps", "lexicon", "templates", "oxt", "update.xml")
    ) as xml_file:
        xml = xml_file.read()

    project = get_object_or_404(models.LexiconProject, language_code=lang_code)

    xml = xml.replace("$VERSION", str(project.version))
    xml = xml.replace("$IDENTIFIER", f"NTMPNG {lang_code} extension")
    xml = xml.replace(
        "$DOWNLOAD_URL",
        request.build_absolute_uri(reverse("lexicon:latest-oxt", args=[lang_code])),
    )
    return HttpResponse(xml, content_type="text/xml")


class ReviewList(ListView):
    """Shows entries marked for review <lang code>/review."""

    model = models.LexiconEntry
    template_name = "lexicon/review_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lang_code"] = self.lang_code
        context["project"] = self.project
        return context

    def get_queryset(self):
        self.lang_code = self.kwargs.get("lang_code")
        self.project = get_object_or_404(
            models.LexiconProject, language_code=self.lang_code
        )
        return models.LexiconEntry.objects.filter(project=self.project, review__gt=0)


class IgnoreList(ProjectContextMixin, TemplateView):
    template_name = "lexicon/ignore_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_view"] = "lexicon:ignore_search"
        return context


class IgnoreSearchResults(ListView):
    """The list of ignore words, filtered by htmx-get."""

    template_name = "lexicon/includes/ignore_search_results.html"
    model = models.IgnoreWord
    paginate_by = 250

    def get_queryset(self, **kwargs):
        search = self.request.GET.get("search")
        self.project = get_object_or_404(
            models.LexiconProject, language_code=self.kwargs.get("lang_code")
        )
        query = models.IgnoreWord.objects.select_related("project").filter(
            project=self.project
        )
        print(query)
        if search:
            return query.filter(tok_ples__icontains=search)
        else:
            return query


class IgnoreWordEditView(LoginRequiredMixin):
    """A base class for ignore word forms."""

    template_name = "lexicon/ignore_form.html"
    model = models.IgnoreWord
    fields = ("tok_ples", "type", "eng", "comments")

    def get_success_url(self):
        return reverse(
            "lexicon:ignore_list",
            args=(self.kwargs.get("lang_code"),),
        )


class CreateIgnoreWordView(IgnoreWordEditView, ProjectContextMixin, CreateView):
    """The view at url ignore/1/create. Creates a new ignore view."""

    def form_valid(self, form, **kwargs):
        """When the form saves run this code."""
        obj = form.save(commit=False)
        obj.project = get_object_or_404(
            models.LexiconProject, language_code=self.kwargs.get("lang_code")
        )
        obj.save()
        user_log.info(
            f"{self.request.user} created an ignore word in {obj.project} lexicon."
        )
        return super().form_valid(form, **kwargs)


class UpdateIgnoreWordView(IgnoreWordEditView, ProjectContextMixin, UpdateView):
    """The view at url ignore/1/update. Updates a new ignore view."""

    def form_valid(self, form, **kwargs):
        """When the form saves run this code."""
        obj = form.save(commit=False)
        obj.ignore_word_project = get_object_or_404(
            models.LexiconProject, language_code=self.kwargs.get("lang_code")
        )
        obj.save()
        user_log.info(
            f"{self.request.user} updated an ignore word in {obj.project} lexicon."
        )
        return super().form_valid(form, **kwargs)


class DeleteIgnoreWordView(IgnoreWordEditView, ProjectContextMixin, DeleteView):
    """The view at url ignore/1/delete. Deletes a new ignore view."""

    fields = None
    template_name = "lexicon/confirm_entry_delete.html"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_log.info(
            f"{request.user} deleted an ignore word in {self.object.project} lexicon."
        )
        return super().post(request, *args, **kwargs)


class AffixTester(ProjectContextMixin, TemplateView):
    """A view for submitting a basic form to test affixes."""

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
    """Handle requests for testing affixes."""

    template_name = "lexicon/includes/affix_results.html"

    def get_context_data(self, **kwargs):
        user_log.info(f"{self.request.user} requested affix generation")
        context = super().get_context_data(**kwargs)

        words = self.request.GET.get("words")
        affix = self.request.GET.get("affix")

        try:
            # Call the unmunch function
            result = hunspell.unmunch(words, affix)
        except Exception as e:
            return JsonResponse(
                {
                    "error": "An error occurred while processing the affixes.",
                    "details": str(e),
                },
                status=500,
            )
        context.update({"generated_words": result})
        return context


class paradigm_modal(ProjectContextMixin, FormView):
    template_name = "lexicon/includes/paradigm_modal.html"
    form_class = forms.ParadigmSelectForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Add extra data you want to pass
        project = models.LexiconEntry.objects.get(pk=self.kwargs.get("pk")).project
        kwargs["paradigms"] = models.Paradigm.objects.filter(project=project)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        word = models.LexiconEntry.objects.get(pk=self.kwargs.get("pk"))
        context["object"] = word
        return context

    def form_valid(self, form):
        # Do your processing here (e.g., save data)
        selected_paradigm = models.Paradigm.objects.get(
            pk=form.cleaned_data["paradigm"]
        )
        word = models.LexiconEntry.objects.get(pk=self.kwargs.get("pk"))
        word.paradigms.add(selected_paradigm)
        log.debug(f"{selected_paradigm} applied to {word}")
        response = HttpResponse(status=204)  # No content
        response["HX-Trigger"] = "paradigmSaved"  # closes the modal dialog
        return response


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class ParadigmView(View):
    """A view to render and edit conjugations for a word.

    GET responds with a html snippet to be inserted into the page.
    POST updates the conjugations and returns a html snippet to be inserted into the page.
    """

    view_template = "lexicon/includes/paradigm_view.html"
    edit_template = "lexicon/includes/paradigm_edit.html"

    def _context_lookup(self, word_pk, paradigm_pk):
        """Return required context for both view and edit."""

        word = models.LexiconEntry.objects.get(pk=word_pk)
        paradigm = models.Paradigm.objects.get(pk=paradigm_pk)

        # Build a nested dict: {row_idx: {col_idx: conjugation_obj}}
        # The dict_get template tag can read it
        conjugations = models.Conjugation.objects.filter(word=word, paradigm=paradigm)
        conjugation_grid = {}
        for c in conjugations:
            conjugation_grid.setdefault(c.row, {})[c.column] = c.conjugation

        qs = models.Conjugation.objects.filter(word=word, paradigm=paradigm).order_by(
            "row", "column"
        )
        formset = forms.get_conjugation_formset(
            paradigm, queryset=qs,
        )
        # Create a grid of forms for the template
        forms_grid = []
        forms_iter = iter(formset.forms)
        for _ in range(len(paradigm.row_labels)):
            row = []
            for _ in range(len(paradigm.column_labels)):
                row.append(next(forms_iter))
            forms_grid.append(row)

        return {
            "conjugation_grid": conjugation_grid,
            "word": word,
            "paradigm": paradigm,
            "formset": formset,
            "forms_grid": forms_grid,
        }

    def get(self, request, word_pk, paradigm_pk, edit):
        context = self._context_lookup(word_pk, paradigm_pk)
        template = self.edit_template if edit == "edit" else self.view_template
        return render(request, template, context)

    @transaction.atomic
    def post(self, request, word_pk, paradigm_pk, *args, **kwargs):
        """Upon a post request save the conjugation values to the database."""

        word = models.LexiconEntry.objects.get(pk=word_pk)
        paradigm = models.Paradigm.objects.get(pk=paradigm_pk)
        qs = models.Conjugation.objects.filter(word=word, paradigm=paradigm).order_by("row", "column")
        formset = forms.get_conjugation_formset(paradigm, queryset=qs, data=request.POST, word=word)
        log.debug(f"formset: {formset.data}")
        if formset.is_valid():
            log.debug("Formset is valid")
            formset.save()
            # Success: re-render the view template
            context = self._context_lookup(word_pk, paradigm_pk)
            return render(request, self.view_template, context)
        else:
            # Errors: re-render the edit template with errors
            log.debug("Formset is NOT valid")
            log.debug(formset.errors)
            context = self._context_lookup(word_pk, paradigm_pk)
            return render(request, self.edit_template, context)
