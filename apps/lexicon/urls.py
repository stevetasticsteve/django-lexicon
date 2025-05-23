from django.urls import path

from apps.lexicon import views

app_name = "lexicon"

urlpatterns = [
    path("", views.ProjectList.as_view(), name="project_list"),
    path("<str:lang_code>", views.LexiconView.as_view(), name="entry_list"),
    path(
        "<str:lang_code>/<int:pk>/detail",
        views.EntryDetail.as_view(),
        name="entry_detail",
    ),
    path("<str:lang_code>/create", views.CreateEntry.as_view(), name="create_entry"),
    path(
        "<str:lang_code>/<int:pk>/update",
        views.UpdateEntry.as_view(),
        name="update_entry",
    ),
    path(
        "<str:lang_code>/<int:pk>/delete",
        views.DeleteEntry.as_view(),
        name="delete_entry",
    ),
    path("<str:lang_code>/import", views.ImportPage.as_view(), name="import_page"),
    path(
        "<str:lang_code>/import-result",
        views.ImportSuccess.as_view(),
        name="import-success",
    ),
    path("<str:lang_code>/export", views.ExportPage.as_view(), name="export_page"),
    path("<str:lang_code>/latest-oxt", views.latest_oxt, name="latest-oxt"),
    path("<str:lang_code>/oxt-update", views.oxt_update_service, name="update-oxt"),
    path("<str:lang_code>/search", views.SearchResults.as_view(), name="search"),
    path("<str:lang_code>/review", views.ReviewList.as_view(), name="review_list"),
    path("<str:lang_code>/ignore", views.IgnoreList.as_view(), name="ignore_list"),
    path(
        "<str:lang_code>/ignore/search",
        views.IgnoreSearchResults.as_view(),
        name="ignore_search",
    ),
    path(
        "<str:lang_code>/ignore/create",
        views.CreateIgnoreWordView.as_view(),
        name="create_ignore",
    ),
    path(
        "<str:lang_code>/ignore/<int:pk>/update",
        views.UpdateIgnoreWordView.as_view(),
        name="update_ignore",
    ),
    path(
        "<str:lang_code>/ignore/<int:pk>/delete",
        views.DeleteIgnoreWordView.as_view(),
        name="delete_ignore",
    ),
    path(
        "<str:lang_code>/affix-tester", views.AffixTester.as_view(), name="affix_tester"
    ),
    path(
        "<str:lang_code>/affix-results",
        views.AffixResults.as_view(),
        name="affix_results",
    ),
    path(
        "<str:lang_code>/paradigm-modal/<int:pk>",
        views.paradigm_modal.as_view(),
        name="paradigm_modal",
    ),
    path(
        "<int:word_pk>/paradigm/<int:paradigm_pk>/<str:edit>",
        views.ParadigmView.as_view(),
        name="paradigm",
    ),
]
