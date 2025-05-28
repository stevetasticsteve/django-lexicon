import datetime
import logging
import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, HttpResponse, JsonResponse
from django.http.request import HttpRequest as HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
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


class EntryDetail(ProjectContextMixin, DetailView):
    """The view at url <lang code>/1/detail. Displays all info in .db for a word."""

    model = models.LexiconEntry
    template_name = "lexicon/entry_detail.html"

    def get_context_data(self, **kwargs) -> dict:
        """Add the conjugations linked to the entry."""
        context = super().get_context_data(**kwargs)
        context["conjugations"] = models.Conjugation.objects.filter(
            word=self.object
        ).select_related("paradigm")
        context["paradigms"] = (
            self.object.paradigms.all()
        )  # Get all paradigms linked to the word

        return context


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
    template_name = "lexicon/simple_form.html"

    def form_valid(self, form, **kwargs):
        """Code that runs when the form has been submitted and is valid."""

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
