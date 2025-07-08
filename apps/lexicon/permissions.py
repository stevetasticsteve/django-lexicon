# filepath: apps/lexicon/permissions.py

import logging

from django.http import HttpResponseForbidden

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
                f"User {request.user} does not have permission to edit project {self.get_project()}"
            )
            return HttpResponseForbidden(
                "You do not have permission to edit this project."
            )
        else:
            log.debug(
                f"User {request.user} has permission to edit project {self.get_project()}"
            )
        return super().dispatch(request, *args, **kwargs)
