import json
import os
from pathlib import Path
from typing import Any, Dict, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

CLIENT_SECRETS_FILE = Path("credentials.json")
TOKEN_FILE = Path("token.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
REDIRECT_URI = "http://localhost:8000/auth/callback"


def _ensure_local_transport() -> None:
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


def get_auth_url() -> str:
    _ensure_local_transport()
    if not CLIENT_SECRETS_FILE.exists():
        raise FileNotFoundError(
            "credentials.json not found. Create it from Google Cloud Console and place it in the project root."
        )

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def authenticate(authorization_response: str) -> Dict[str, Any]:
    _ensure_local_transport()
    if not CLIENT_SECRETS_FILE.exists():
        raise FileNotFoundError(
            "credentials.json not found. Create it from Google Cloud Console and place it in the project root."
        )

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    flow.fetch_token(authorization_response=authorization_response)
    creds = flow.credentials
    _save_credentials(creds)
    return _credentials_to_dict(creds)


def _save_credentials(creds: Credentials) -> None:
    data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or []),
    }
    TOKEN_FILE.write_text(json.dumps(data, indent=2))


def _load_credentials() -> Credentials:
    if not TOKEN_FILE.exists():
        raise FileNotFoundError("token.json not found. Authenticate first via /auth/login.")

    data = json.loads(TOKEN_FILE.read_text())
    creds = Credentials.from_authorized_user_info(data, SCOPES)

    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_credentials(creds)

    return creds


def _build_service() -> Any:
    creds = _load_credentials()
    return build("gmail", "v1", credentials=creds)


def fetch_emails(max_results: int = 10) -> List[Dict[str, Any]]:
    service = _build_service()
    results = service.users().messages().list(userId="me", maxResults=max_results).execute()
    messages = results.get("messages", [])
    return [_parse_message(service, msg["id"]) for msg in messages]


def _parse_message(service: Any, message_id: str) -> Dict[str, Any]:
    raw = service.users().messages().get(
        userId="me",
        id=message_id,
        format="metadata",
        metadataHeaders=["From", "Subject", "Date"],
    ).execute()
    headers = {header["name"]: header["value"] for header in raw.get("payload", {}).get("headers", [])}

    return {
        "id": raw.get("id"),
        "threadId": raw.get("threadId"),
        "from": headers.get("From"),
        "subject": headers.get("Subject"),
        "date": headers.get("Date"),
        "snippet": raw.get("snippet"),
    }


def _credentials_to_dict(creds: Credentials) -> Dict[str, Any]:
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or []),
    }
