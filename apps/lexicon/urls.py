from django.urls import path

import apps.lexicon.views.affix_views as affix_views
import apps.lexicon.views.conjugation_views as conjugation_views
import apps.lexicon.views.ignore_word_views as ignore_word_views
import apps.lexicon.views.import_export_views as import_export_views
import apps.lexicon.views.project_admin_views as project_admin_views
import apps.lexicon.views.search_views as search_views
import apps.lexicon.views.variation_views as variation_views
import apps.lexicon.views.word_views as word_views

app_name = "lexicon"

# Using _ in url names and - in url patterns.
urlpatterns = [
    # project selection.
    path("", word_views.ProjectList.as_view(), name="project_list"),
    # main page for the lexicon. Includes search view via htmx.
    path("<str:lang_code>", word_views.LexiconView.as_view(), name="entry_list"),
    # search box functionality. Html snippets added to entry_list via htmx.
    path(
        "<str:lang_code>/search",
        search_views.LexiconSearchResults.as_view(),
        name="lexicon_search",
    ),
    path(
        "<str:lang_code>/ignore/search",
        search_views.IgnoreSearchResults.as_view(),
        name="ignore_search",
    ),
    # word views for creating, updating and deleting LexiconEntries
    path(
        "<str:lang_code>/word-<int:pk>/detail",
        word_views.EntryDetail.as_view(),
        name="entry_detail",
    ),
    path(
        "<str:lang_code>/word-create",
        word_views.CreateEntry.as_view(),
        name="create_entry",
    ),
    path(
        "<str:lang_code>/word-<int:pk>/update",
        word_views.UpdateEntry.as_view(),
        name="update_entry",
    ),
    path(
        "<str:lang_code>/word-<int:pk>/delete",
        word_views.DeleteEntry.as_view(),
        name="delete_entry",
    ),
    path("add-sense-form/", word_views.add_sense_form, name="add-sense-form"),
    # conjugation views that attach and display conjugation grids to words.
    # these return html snippets attached to the word_detail view via htmx.
    # the views are visible on the entry detail page.
    path(
        "<str:lang_code>/word-<int:pk>/attach-paradigm",
        conjugation_views.paradigm_modal.as_view(),
        name="word_paradigm_modal",
    ),
    path(
        "<str:lang_code>/word-<int:word_pk>/conjugation-grid/<int:paradigm_pk>/<str:edit>",
        conjugation_views.ConjugationGridView.as_view(),
        name="conjugation_grid",
    ),
    # variation views that manage word variations on the word detail page.
    # these return html snippets that attach via htmx.
    path(
        "<str:lang_code>/word-<int:word_pk>/variations",
        variation_views.VariationList.as_view(),
        name="variation_list",
    ),
    path(
        "<str:lang_code>/word-<int:word_pk>/variation-create",
        variation_views.CreateVariation.as_view(),
        name="variation_create",
    ),
    path(
        "<str:lang_code>/variation-<int:pk>/update",
        variation_views.UpdateVariation.as_view(),
        name="variation_update",
    ),
    path(
        "<str:lang_code>/variation-<int:pk>/delete",
        variation_views.DeleteVariation.as_view(),
        name="variation_delete",
    ),
    # views for managing a word's affixes on it's detail page.
    # these return html snippets that attach via htmx.
    path(
        "<str:lang_code>/word-<int:pk>/affix-management",
        affix_views.AffixManagement.as_view(),
        name="word_affix_management",
    ),
    # TODO name class name collision AffixList. Better to rename.
    path(
        "<str:lang_code>/word-<int:pk>/affix-list",
        affix_views.AffixList.as_view(),
        name="word_affix_list",
    ),
    path(
        "<str:lang_code>/word-<int:pk>/update-affixes",
        affix_views.UpdateWordAffixes.as_view(),
        name="word_update_affixes",
    ),
    path(
        "<str:lang_code>/affix-results",
        affix_views.AffixResults.as_view(),
        name="word_affix_results",
    ),
    # review list displaying words marked for review
    path(
        "<str:lang_code>/review-list",
        word_views.ReviewList.as_view(),
        name="review_list",
    ),
    # views for creating, updating and deleting ignore words.
    path(
        "<str:lang_code>/ignore-words",
        ignore_word_views.IgnoreList.as_view(),
        name="ignore_list",
    ),
    path(
        "<str:lang_code>/ignore-words/create",
        ignore_word_views.CreateIgnoreWordView.as_view(),
        name="create_ignore",
    ),
    path(
        "<str:lang_code>/ignore-words/ignore-word-<int:pk>/update",
        ignore_word_views.UpdateIgnoreWordView.as_view(),
        name="update_ignore",
    ),
    path(
        "<str:lang_code>/ignore-words/ignore-word-<int:pk>/delete",
        ignore_word_views.DeleteIgnoreWordView.as_view(),
        name="delete_ignore",
    ),
    # Project admin views
    path(
        "<str:lang_code>/project-admin",
        project_admin_views.ProjectAdmin.as_view(),
        name="project_admin",
    ),
    # Project admin paradigm management
    path(
        "<str:lang_code>/project-admin/paradigm-manage",
        project_admin_views.ManageParadigms.as_view(),
        name="project_admin_paradigm_manage",
    ),
    path(
        "<str:lang_code>/project-admin/paradigm-list",
        project_admin_views.ParadigmList.as_view(),
        name="project_admin_paradigm_list",
    ),
    path(
        "<str:lang_code>/project-admin/paradigm-create",
        project_admin_views.CreateParadigm.as_view(),
        name="project_admin_paradigm_create",
    ),
    path(
        "<str:lang_code>/project-admin/paradigm-<int:pk>/update",
        project_admin_views.UpdateParadigm.as_view(),
        name="project_admin_paradigm_update",
    ),
    path(
        "<str:lang_code>/project-admin/paradigm-<int:pk>/delete",
        project_admin_views.DeleteParadigm.as_view(),
        name="project_admin_paradigm_delete",
    ),
    # Project admin affix management
    path(
        "<str:lang_code>/project-admin/affix-manage",
        project_admin_views.ManageAffixes.as_view(),
        name="project_admin_affix_manage",
    ),
    path(
        "<str:lang_code>/project-admin/affix-list",
        project_admin_views.AffixList.as_view(),
        name="project_admin_affix_list",
    ),
    path(
        "<str:lang_code>/project-admin/affix-create",
        project_admin_views.CreateAffix.as_view(),
        name="project_admin_affix_create",
    ),
    path(
        "<str:lang_code>/project-admin/affix-<int:pk>/update",
        project_admin_views.UpdateAffix.as_view(),
        name="project_admin_affix_update",
    ),
    path(
        "<str:lang_code>/project-admin/affix-<int:pk>/delete",
        project_admin_views.DeleteAffix.as_view(),
        name="project_admin_affix_delete",
    ),
    path(
        "<str:lang_code>/project-admin/affix-file-update",
        affix_views.AffixFileUpdateView.as_view(),
        name="project_admin_affix_file_update",
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
        name="import_success",
    ),
    path(
        "<str:lang_code>/export",
        import_export_views.ExportPage.as_view(),
        name="export_page",
    ),
    path(
        "<str:lang_code>/oxt-deliver.oxt",
        import_export_views.oxt_update_deliver,
        name="oxt_update_deliver",
    ),
    path(
        "<str:lang_code>/oxt-update",
        import_export_views.oxt_update_notify,
        name="oxt_update_notify",
    ),
]
