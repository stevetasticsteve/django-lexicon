from django.contrib import admin
from apps.lexicon import models


class ProjectAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.LexiconProject, ProjectAdmin)
