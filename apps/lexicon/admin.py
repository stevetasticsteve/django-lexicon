from django.contrib import admin
from apps.lexicon import models


# Entries
class LexiconEntriesAdmin(admin.ModelAdmin):
    list_filter = ["project"]
    search_fields = ["tok_ples", "eng"]


admin.site.register(models.LexiconEntry, LexiconEntriesAdmin)


# Paradigms
class ParadigmAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Paradigm, ParadigmAdmin)


# Project
class ProjectAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.LexiconProject, ProjectAdmin)

# Conjugations
class ConjugationAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Conjugation,ConjugationAdmin)