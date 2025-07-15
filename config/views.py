import json
import logging

from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View

user_log = logging.getLogger("user_log")
log = logging.getLogger("lexicon")


class LoginView(View):
    form_class = AuthenticationForm
    template_name = "login.html"

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            user_log.info(f"User '{user.username}' (ID: {user.id}) logged in.")
            return redirect("project_list")
        else:
            username = request.POST.get("username", "unknown")
            user_log.warning(
                f"Failed login attempt for user '{username}' from IP address: {request.META.get('REMOTE_ADDR', 'unknown')}"
            )
            return render(request, self.template_name, {"form": form})


class JsonValidation(View):
    """A view to handle JSON validation requests for both row_labels and column_labels."""

    def post(self, request, *args, **kwargs):
        errors = {}
        user_input = f"{request.POST.get('row_labels', '')},  {request.POST.get('column_labels', '')}"

        for field in ["row_labels", "column_labels"]:
            data = request.POST.get(field, "")
            if not data:
                errors[field] = "cannot be empty."
            else:
                try:
                    parsed_data = json.loads(data)
                    if not isinstance(parsed_data, list):
                        errors[field] = (
                            "must be a valid JSON array. For example: ['label1', 'label2']"
                        )
                except json.JSONDecodeError:
                    errors[field] = (
                        "must be a valid JSON array. For example: ['label1', 'label2']"
                    )

        if errors:
            # Return errors as a simple string
            log.debug(f"JSON validation errors for {user_input}")
            return HttpResponse("\n".join(f"{k}: {v}" for k, v in errors.items()))
        log.debug(f"JSON validation successful for {user_input}")
        return HttpResponse("")
