from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from estoque.saude import saude

urlpatterns = [
    path("saude/", saude, name="saude"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("estoque.urls")),
]
