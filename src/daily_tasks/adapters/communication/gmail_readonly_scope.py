# Responsibility: Name the only Gmail OAuth scope and Google endpoints Daily Tasks uses.
# Public interface:
# +-- GMAIL_READONLY_SCOPE
# +-- GOOGLE_AUTHORIZATION_ENDPOINT
# `-- GOOGLE_TOKEN_ENDPOINT
"""Gmail access is read-only: no other scope is ever requested or accepted."""

from typing import Final

GMAIL_READONLY_SCOPE: Final = "https://www.googleapis.com/auth/gmail.readonly"
GOOGLE_AUTHORIZATION_ENDPOINT: Final = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT: Final = "https://oauth2.googleapis.com/token"
