from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from apps.lexicon import models
from apps.lexicon.tasks import update_lexicon_entry_search_field


# Inline elements for LexiconEntry
class SenseInline(admin.TabularInline):
    model = models.Sense
    extra = 0


class VariationInline(admin.TabularInline):
    model = models.Variation
    extra = 0


class ConjugationInline(admin.TabularInline):
    model = models.Conjugation
    fk_name = "word"
    readonly_fields = ("paradigm", "row", "column")
    extra = 0

    def has_add_permission(self, request, obj=None):
        # Adding conjugations should be done via the grid interface
        # to ensure row/column integrity with the paradigm.
        return False


# Entries
class LexiconEntriesAdmin(admin.ModelAdmin):
    list_display = ("text", "project", "pos", "checked", "review")
    list_filter = ("project", "pos", "checked", "review")
    search_fields = ("text", "search", "senses__eng")
    inlines = [SenseInline, ConjugationInline, VariationInline]

    def save_formset(self, request, form, formset, change):
        # When an inline formset is saved (e.g., conjugations or variations),
        # we need to trigger an update of the parent's search field.
        super().save_formset(request, form, formset, change)
        if formset.model in [models.Conjugation, models.Variation]:
            update_lexicon_entry_search_field.delay(formset.instance.pk)


admin.site.register(models.LexiconEntry, LexiconEntriesAdmin)


# # Paradigms
# class ParadigmAdmin(admin.ModelAdmin):
#     pass


# admin.site.register(models.Paradigm, ParadigmAdmin)


# Project
class ProjectAdmin(GuardedModelAdmin):
    pass


admin.site.register(models.LexiconProject, ProjectAdmin)
