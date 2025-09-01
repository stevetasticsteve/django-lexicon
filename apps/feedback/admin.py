from django.contrib import admin
from apps.feedback import models

class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "user_email",
        "type",
        "date",
        "handled",
    )


admin.site.register(models.Feedback, FeedbackAdmin)