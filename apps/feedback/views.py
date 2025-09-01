import logging

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView

from apps.feedback.forms import FeedbackForm

log = logging.getLogger("lexicon")
user_log = logging.getLogger("user_log")


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class FeedbackView(LoginRequiredMixin, CreateView):
    form_class = FeedbackForm
    template_name = "feedback/feedback.html"
    success_url = reverse_lazy("feedback_success")

    def form_valid(self, form):
        feedback = form.save()
        feedback.name = self.request.user.username
        feedback.user_email = self.request.user.email
        feedback.save()
        user_log.info(
            f"Feedback submitted by user '{self.request.user.username}' (ID: {self.request.user.id})"
        )

        # Email the admins
        subject = f"New Feedback: {feedback.type} from {feedback.name}"
        message = f"From: {feedback.user_email}\n\nMessage: {feedback.message}"
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [admin[1] for admin in settings.ADMINS],  # Send to all admins
            fail_silently=True,  # Don't raise exceptions if email fails
        )
        return super().form_valid(form)


class FeedbackSuccess(TemplateView):
    """Feedback success page."""

    template_name = "feedback/success.html"
