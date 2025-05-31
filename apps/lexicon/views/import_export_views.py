import os

from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from apps.lexicon import forms, models, tasks
from apps.lexicon.utils import export
from apps.lexicon.views.word_views import ProjectContextMixin


class ImportPage(ProjectContextMixin, FormView):
    """The view at url lexicon/<lang code>/import. Provides an import form."""

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


class ImportSuccess(ProjectContextMixin, TemplateView):
    """A simple page to inform user of import results lexicon/<lang code>/import-result"""

    template_name = "lexicon/upload_result.html"


class ExportPage(ProjectContextMixin, FormView):
    """Lists the export options at lexicon/<lang code>/export.

    The response is a http file attachment, so no success url is required."""

    template_name = "lexicon/export.html"
    form_class = forms.ExportForm

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


def latest_oxt(request, lang_code) -> FileResponse:
    file = export.export_entries(
        "oxt",
        get_object_or_404(models.LexiconProject, language_code=lang_code),
        True,
        request,
    )
    response = FileResponse(open(file, "rb"), as_attachment=False)
    return response


def oxt_update_service(request, lang_code) -> HttpResponse:
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
