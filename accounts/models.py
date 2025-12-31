from datetime import UTC, datetime, timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .oauth import oauth


def unix_timestamp_to_datetime(expires_at_oauth):
    if expires_at_oauth is None:
        return None
    return datetime.fromtimestamp(expires_at_oauth, UTC)


class TokenManager(models.Manager):
    def build_fields(self, full_token):
        access_token = full_token["access_token"]
        refresh_token = full_token.get("refresh_token")
        expires_at = unix_timestamp_to_datetime(full_token.get("expires_at"))
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }

    def upsert_from_full_token(self, user, full_token):
        fields = self.build_fields(full_token)
        return self.update_or_create(user=user, defaults=fields)


class Token(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="passport_token")
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    objects = TokenManager()

    def __str__(self):
        return f"Token for {self.user}: [redacted]"

    def is_expired(self, buffer_minutes=5):
        if not self.expires_at:
            return False
        soon = timezone.now() + timedelta(minutes=buffer_minutes)
        return self.expires_at <= soon

    def refresh_if_needed(self):
        if self.is_expired() and self.refresh_token:
            self.refresh()

    def refresh(self):
        new_token = oauth.mediawiki.fetch_access_token(
            grant_type="refresh_token",
            refresh_token=self.refresh_token,
        )

        self.access_token = new_token["access_token"]
        self.refresh_token = new_token.get("refresh_token")
        self.expires_at = unix_timestamp_to_datetime(new_token.get("expires_at"))
        self.save()
