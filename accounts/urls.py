from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("login/dev/", views.login_dev, name="login_dev"),
    path("logout/", views.logout_view, name="logout"),
    path("redirect/", views.oauth_redirect, name="oauth_redirect"),
    path("callback/", views.oauth_callback, name="oauth_callback"),
]
