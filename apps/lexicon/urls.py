from django.urls import path

import apps.lexicon.views.word_views as word_views
import apps.lexicon.views.import_export_views as import_export_views
import apps.lexicon.views.search_views as search_views
import apps.lexicon.views.ignore_word_views as ignore_word_views
import apps.lexicon.views.conjugation_views as conjugation_views
import apps.lexicon.views.affix_views as affix_views

app_name = "lexicon"

urlpatterns = [
    # word_views
    path("", word_views.ProjectList.as_view(), name="project_list"),
    path("<str:lang_code>", word_views.LexiconView.as_view(), name="entry_list"),
    path(
        "<str:lang_code>/<int:pk>/detail",
        word_views.EntryDetail.as_view(),
        name="entry_detail",
    ),
    path(
        "<str:lang_code>/create",
        word_views.CreateEntry.as_view(),
        name="create_entry",
    ),
    path(
        "<str:lang_code>/<int:pk>/update",
        word_views.UpdateEntry.as_view(),
        name="update_entry",
    ),
    path(
        "<str:lang_code>/<int:pk>/delete",
        word_views.DeleteEntry.as_view(),
        name="delete_entry",
    ),
    path(
        "<str:lang_code>/review",
        word_views.ReviewList.as_view(),
        name="review_list",
    ),
    # import_export_views
    path(
        "<str:lang_code>/import",
        import_export_views.ImportPage.as_view(),
        name="import_page",
    ),
    path(
        "<str:lang_code>/import-result",
        import_export_views.ImportSuccess.as_view(),
        name="import-success",
    ),
    path(
        "<str:lang_code>/export",
        import_export_views.ExportPage.as_view(),
        name="export_page",
    ),
    path(
        "<str:lang_code>/latest-oxt",
        import_export_views.latest_oxt,
        name="latest-oxt",
    ),
    path(
        "<str:lang_code>/oxt-update",
        import_export_views.oxt_update_service,
        name="update-oxt",
    ),
    # search_views
    path(
        "<str:lang_code>/search",
        search_views.SearchResults.as_view(),
        name="search",
    ),
    # ignore_word_views
    path(
        "<str:lang_code>/ignore",
        ignore_word_views.IgnoreList.as_view(),
        name="ignore_list",
    ),
    path(
        "<str:lang_code>/ignore/search",
        ignore_word_views.IgnoreSearchResults.as_view(),
        name="ignore_search",
    ),
    path(
        "<str:lang_code>/ignore/create",
        ignore_word_views.CreateIgnoreWordView.as_view(),
        name="create_ignore",
    ),
    path(
        "<str:lang_code>/ignore/<int:pk>/update",
        ignore_word_views.UpdateIgnoreWordView.as_view(),
        name="update_ignore",
    ),
    path(
        "<str:lang_code>/ignore/<int:pk>/delete",
        ignore_word_views.DeleteIgnoreWordView.as_view(),
        name="delete_ignore",
    ),
    # affix_views
    path(
        "<str:lang_code>/affix-tester",
        affix_views.AffixTester.as_view(),
        name="affix_tester",
    ),
    path(
        "<str:lang_code>/affix-results",
        affix_views.AffixResults.as_view(),
        name="affix_results",
    ),
    # conjugation_views
    path(
        "<str:lang_code>/paradigm-modal/<int:pk>",
        conjugation_views.paradigm_modal.as_view(),
        name="paradigm_modal",
    ),
    path(
        "<int:word_pk>/paradigm/<int:paradigm_pk>/<str:edit>",
        conjugation_views.ParadigmView.as_view(),
        name="paradigm",
    ),
]
