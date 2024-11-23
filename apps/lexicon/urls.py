from django.urls import path
from apps.lexicon import views

app_name = "lexicon"

urlpatterns = [
    path("", views.ProjectList.as_view(), name="project_list"),
]
