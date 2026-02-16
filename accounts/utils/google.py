from google.oauth2 import id_token
from django.conf import settings
from google.auth.transport import requests


def verify_google_token(token):
    # Import lazily so project startup and URL loading do not fail
    # when optional Google auth dependencies are missing.

    return id_token.verify_oauth2_token(
        token,
        requests.Request(),
        settings.GOOGLE_CLIENT_ID
    )
