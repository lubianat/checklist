from django.contrib import admin
from django.urls import include, path

from lists.views import catalog_create, catalog_detail, catalog_refresh, list_index

urlpatterns = [
    path("", list_index, name="list_index"),
    path("catalogs/create/", catalog_create, name="catalog_create"),
    path("catalogs/<slug:slug>/", catalog_detail, name="catalog_detail"),
    path("catalogs/<slug:slug>/refresh/", catalog_refresh, name="catalog_refresh"),
    path("lists/", include("lists.urls")),
    path("auth/", include("accounts.urls")),
    path("admin/", admin.site.urls),
]
