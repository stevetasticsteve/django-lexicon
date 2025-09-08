import logging
import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from apps.lexicon import forms, models, tasks
from apps.lexicon.permissions import ProjectEditPermissionRequiredMixin
from apps.lexicon.utils import export
from apps.lexicon.views.word_views import ProjectContextMixin

log = logging.getLogger("lexicon")


# v0.3 import was hidden from public use.
# import views are untested
class ImportPage(
    LoginRequiredMixin,
    ProjectEditPermissionRequiredMixin,
    ProjectContextMixin,
    FormView,
):
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
            "lexicon:import_success",
            args=(self.kwargs.get("lang_code"),),
        )


class ImportSuccess(ProjectContextMixin, TemplateView):
    """A simple page to inform user of import results lexicon/<lang code>/import-result"""

    template_name = "lexicon/upload_result.html"

# export views below are in use

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
            self.request,
            checked=form.cleaned_data["checked"],
            hunspell=form.cleaned_data["include_hunspell"],
            ignore_word_flag=form.cleaned_data["include_ignore"],
        )
        response = FileResponse(
            open(file, "rb"), as_attachment=True, filename=os.path.basename(file)
        )
        return response


def oxt_update_deliver(request, lang_code) -> FileResponse:
    """Respond to requests for the latest oxt file."""
    log.debug(f"oxt download request for language code {lang_code}")
    file = export.export_entries(
        "oxt",
        get_object_or_404(models.LexiconProject, language_code=lang_code),
        request,
    )
    log.debug(f"oxt file located at {file}")

    # Open the file and serve with proper headers
    response = FileResponse(
        open(file, "rb"),
        content_type="application/vnd.openoffice.extension",
    )
    # Suggest filename for LibreOffice to save/install
    filename = f"{lang_code}.oxt"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


def oxt_update_notify(request, lang_code) -> HttpResponse:
    """Respond to requests for an oxt update with xml update info."""
    # load the xml template
    log.debug(f"oxt update request for language code {lang_code}")
    with open(
        os.path.join("apps", "lexicon", "templates", "oxt", "update.xml")
    ) as xml_file:
        xml = xml_file.read()

    project = get_object_or_404(models.LexiconProject, language_code=lang_code)

    xml = xml.replace("$VERSION", str(project.version))
    xml = xml.replace("$IDENTIFIER", f"NTMPNG {lang_code} extension")
    download_url = request.build_absolute_uri(
        reverse("lexicon:oxt_update_deliver", args=[lang_code])
    )
    xml = xml.replace("$DOWNLOAD_URL", download_url)
    log.debug(f"oxt download xml: {xml}")
    return HttpResponse(xml, content_type="text/xml")
