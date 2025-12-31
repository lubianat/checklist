import logging

from authlib.integrations.base_client.errors import MismatchingStateError
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.shortcuts import redirect, render
from requests.exceptions import RequestException

from .models import Token
from .oauth import oauth
from .services import (
    WikimediaAuthError,
    create_user_from_access_token,
    create_user_from_full_token,
)

logger = logging.getLogger(__name__)

def _oauth_enabled():
    return bool(settings.OAUTH_CLIENT_ID and settings.OAUTH_CLIENT_SECRET)


def login_view(request):
    if request.user.is_authenticated:
        return redirect("list_index")
    return render(
        request,
        "accounts/login.html",
        {
            "error": None,
            "oauth_enabled": _oauth_enabled(),
        },
    )


def logout_view(request):
    if request.user.is_authenticated:
        Token.objects.filter(user=request.user).delete()
    django_logout(request)
    return redirect("list_index")


def oauth_redirect(request):
    if not _oauth_enabled():
        messages.error(request, "OAuth is not configured.")
        return redirect("login")
    return oauth.mediawiki.authorize_redirect(request)


def oauth_callback(request):
    if not _oauth_enabled():
        messages.error(request, "OAuth is not configured.")
        return redirect("login")
    try:
        full_token = oauth.mediawiki.authorize_access_token(request)
        user = create_user_from_full_token(full_token)
        django_login(request, user)
        return redirect("list_index")
    except (MismatchingStateError, KeyError, WikimediaAuthError, RequestException):
        logger.exception("OAuth callback failed")
        return render(
            request,
            "accounts/login.html",
            {
                "error": "oauth_failed",
                "oauth_enabled": _oauth_enabled(),
            },
            status=401,
        )


def login_dev(request):
    if request.user.is_authenticated:
        return redirect("list_index")
    if request.method == "POST":
        access_token = request.POST.get("access_token", "").strip()
        try:
            user = create_user_from_access_token(access_token)
            django_login(request, user)
            return redirect("list_index")
        except (WikimediaAuthError, RequestException) as error:
            logger.exception("Developer login failed")
            return render(
                request,
                "accounts/login_dev.html",
                {"error": error},
                status=400,
            )
    return render(request, "accounts/login_dev.html", {"error": None})
