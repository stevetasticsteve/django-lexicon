"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from apps.lexicon.views.word_views import ProjectList
from config import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", views.LoginView.as_view(), name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", ProjectList.as_view(), name="project_list"),
    path("lexicon/", include("apps.lexicon.urls")),
    path("json-validate", views.JsonValidation.as_view(), name="json_validation"),
]
