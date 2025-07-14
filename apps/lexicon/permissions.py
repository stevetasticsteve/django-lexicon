# filepath: apps/lexicon/permissions.py

import logging

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.loader import render_to_string

log = logging.getLogger("lexicon")


class ProjectEditPermissionRequiredMixin:
    """A mixin to check if the user has permission to edit a lexicon project.

    Should also inherit ProjectContextMixin to provide project context."""

    permission_required = "edit_lexiconproject"

    def has_project_permission(self):
        project = self.get_project()
        return self.request.user.has_perm(self.permission_required, project)

    def dispatch(self, request, *args, **kwargs):
        if not self.has_project_permission():
            log.debug(
                f"User '{request.user}' does not have permission to edit project '{self.get_project()}'"
            )
            if request.headers.get("HX-Request"):
                html = render_to_string(
                    "lexicon/includes/403_permission_error.html", request=request
                )
                return HttpResponse(html, status=403)

            else:
                raise PermissionDenied()

        else:
            log.debug(
                f"User '{request.user}' has permission to edit project '{self.get_project()}'"
            )
        return super().dispatch(request, *args, **kwargs)
