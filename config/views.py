from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.views import View
import logging

user_log = logging.getLogger("user_log")


def home(request):
    return render(request, template_name="home.html")


def to_do(request):
    return render(request, template_name="to_do.html")


class LoginView(View):
    form_class = AuthenticationForm
    template_name = "registration/login.html"

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            user_log.info(f"User '{user.username}' (ID: {user.id}) logged in.")
            return redirect("home")
        else:
            username = request.POST.get("username", "unknown")
            user_log.warning(
                f"Failed login attempt for user '{username}' from IP address: {request.META.get('REMOTE_ADDR', 'unknown')}"
            )
            return render(request, self.template_name, {"form": form})
