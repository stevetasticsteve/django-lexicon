from django.urls import path
from apps.lexicon import views

app_name = "lexicon"

urlpatterns = [
    path("", views.ProjectList.as_view(), name="project_list"),
    path("<slug:slug>", views.LexiconView.as_view(), name="entry_list"),
    path(
        "<slug:slug>/<int:pk>/detail", views.EntryDetail.as_view(), name="entry_detail"
    ),
    path("<slug:slug>/create", views.CreateEntry.as_view(), name="create_entry"),
    path(
        "<slug:slug>/<int:pk>/update", views.UpdateEntry.as_view(), name="update_entry"
    ),
    path(
        "<slug:slug>/<int:pk>/delete", views.DeleteEntry.as_view(), name="delete_entry"
    ),
]
