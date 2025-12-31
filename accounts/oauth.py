from authlib.integrations.django_client import OAuth
from django.conf import settings

oauth = OAuth()
oauth.register(
    name="mediawiki",
    client_id=settings.OAUTH_CLIENT_ID,
    client_secret=settings.OAUTH_CLIENT_SECRET,
    access_token_url=settings.OAUTH_ACCESS_TOKEN_URL,
    authorize_url=settings.OAUTH_AUTHORIZATION_URL,
)
