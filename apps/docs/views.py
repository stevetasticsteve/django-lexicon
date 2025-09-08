import logging
import os

import markdown

from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

log = logging.getLogger("lexicon")


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class DocPageView(TemplateView):
    """Reads the markdown file and renders it as HTML."""

    template_name = "docs/doc_page.html"

    def create_toc_data(self):
        """Creates a list of available documentation pages."""
        docs_path = os.path.join("apps", "docs", "markdown")
        # List all markdown files in the docs_path
        doc_files = [
            f.replace(".md", "") for f in os.listdir(docs_path) if f.endswith(".md")
        ]
        # Extract the part after the first underscore for display names
        doc_files = [{"file": f, "name": f.split("_")[1]} for f in doc_files]
        # Sort the list by the file name
        doc_files.sort(key=lambda x: x["file"])
        return doc_files

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_name = self.kwargs.get("page_name")
        log.debug(f"Rendering documentation page: {page_name}")
        file_path = f"apps/docs/markdown/{page_name}.md"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                html_content = markdown.markdown(content)
        except FileNotFoundError:
            html_content = "<h2>Documentation not found</h2>"
        context["content"] = html_content
        context["toc"] = self.create_toc_data()
        return context

