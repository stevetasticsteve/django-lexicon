from django.db import models


class Feedback(models.Model):
    name = models.CharField(max_length=100, blank=True, null=False)
    user_email = models.EmailField(blank=True, null=False)
    message = models.TextField()
    type = models.CharField(
        max_length=10,
        choices=[
            ("bug", "Bug report"),
            ("feature", "Feature request"),
            ("new", "I wish to create a new project"),
            ("permission", "I need permission to edit a project"),
            ("import", "Help importing data"),
            ("other", "Other"),
        ],
    )
    handled = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Feedback"
