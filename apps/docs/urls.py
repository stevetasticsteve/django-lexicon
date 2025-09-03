from django.urls import path
from apps.docs import views

app_name = "docs"

urlpatterns = [
    path("<str:page_name>/", views.DocPageView.as_view(), name="doc_page"),
]
