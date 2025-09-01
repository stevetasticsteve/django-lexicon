# feedback/urls.py
from django.urls import path

from apps.feedback.views import FeedbackSuccess, FeedbackView


urlpatterns = [
    path("", FeedbackView.as_view(), name="feedback"),
    path(
        "sucess",
        FeedbackSuccess.as_view(),
        name="feedback_success",
    ),
]
