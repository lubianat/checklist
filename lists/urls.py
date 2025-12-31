from django.urls import path

from . import views

urlpatterns = [
    path("", views.list_index, name="list_index"),

    path(
        "<int:list_id>/stamp/<slug:entity_id>/",
        views.stamp_toggle,
        name="stamp_toggle",
    ),
]
