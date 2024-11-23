from django.shortcuts import render
from django.views.generic.list import ListView
from apps.lexicon import models


class ProjectList(ListView):
    """The home page that lists the different lexicon projects."""

    model = models.LexiconProject
    template_name = "lexicon/project_list.html"
