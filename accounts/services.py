import requests
from django.conf import settings
from django.contrib.auth.models import User

from .models import Token


class WikimediaAuthError(Exception):
    pass


class WikimediaClient:
    def __init__(self, access_token):
        self.access_token = access_token

    def get_profile(self):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": settings.WIKIMEDIA_USER_AGENT,
        }
        response = requests.get(
            settings.OAUTH_PROFILE_URL,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise WikimediaAuthError("Profile response was not valid JSON.") from exc
        if not isinstance(payload, dict):
            raise WikimediaAuthError("Profile response was not a JSON object.")
        return payload

    def get_username(self):
        profile = self.get_profile()
        username = profile.get("username")
        if not username:
            raise WikimediaAuthError("Missing username in profile response")
        return username


def create_user_from_full_token(full_token):
    access_token = full_token["access_token"]
    client = WikimediaClient(access_token)
    username = client.get_username()

    user, _ = User.objects.get_or_create(username=username)
    Token.objects.upsert_from_full_token(user=user, full_token=full_token)
    return user


def create_user_from_access_token(access_token):
    if not access_token:
        raise WikimediaAuthError("Missing access token")
    client = WikimediaClient(access_token)
    username = client.get_username()

    user, _ = User.objects.get_or_create(username=username)
    Token.objects.update_or_create(
        user=user,
        defaults={
            "access_token": access_token,
            "refresh_token": None,
            "expires_at": None,
        },
    )
    return user
