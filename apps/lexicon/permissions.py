# filepath: apps/lexicon/permissions.py

from django.http import HttpResponseForbidden
import logging

log = logging.getLogger("lexicon")

class ProjectEditPermissionRequiredMixin:
    permission_required = "edit_lexiconproject"

    def has_project_permission(self):
        project = self.get_project()
        return self.request.user.has_perm(self.permission_required, project)

    def dispatch(self, request, *args, **kwargs):
        log.debug("Checking perimssions")
        if not self.has_project_permission():
            return HttpResponseForbidden(
                "You do not have permission to edit this project."
            )
        return super().dispatch(request, *args, **kwargs)
