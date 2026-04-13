import os
import json
import base64
from email.utils import parsedate_to_datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Allow OAuth over plain http:// for local development.
# Google's OAuth library rejects non-HTTPS redirects by default.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

# OAuth config
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
REDIRECT_URI = "http://localhost:8000/auth/callback"


def _get_flow() -> Flow:
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    return flow


def get_auth_url() -> str:
    """Generate the Google OAuth login URL."""
    flow = _get_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def authenticate(auth_code: str) -> Credentials:
    """Exchange the authorization code for credentials and save token."""
    flow = _get_flow()
    flow.fetch_token(code=auth_code)
    creds = flow.credentials

    # Save token for future use
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)

    return creds


def get_credentials() -> Credentials | None:
    """Load saved credentials from token.json, return None if not found."""
    if not os.path.exists(TOKEN_FILE):
        return None

    with open(TOKEN_FILE) as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data["scopes"],
    )

    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        # Update saved token
        token_data["token"] = creds.token
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f, indent=2)

    return creds


def _build_gmail_service(creds: Credentials):
    return build("gmail", "v1", credentials=creds)


def _parse_email_message(msg: dict) -> dict:
    """Parse a Gmail API message into a clean dict."""
    headers = msg.get("payload", {}).get("headers", [])
    header_map = {h["name"].lower(): h["value"] for h in headers}

    # Extract body text
    body = ""
    payload = msg.get("payload", {})

    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    break
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    # Parse date
    date_str = header_map.get("date", "")
    try:
        date_parsed = parsedate_to_datetime(date_str).isoformat()
    except Exception:
        date_parsed = date_str

    subject = header_map.get("subject", "(no subject)")
    sender = header_map.get("from", "unknown")

    return {
        "id": msg["id"],
        "subject": subject,
        "from": sender,
        "date": date_parsed,
        "snippet": msg.get("snippet", ""),
        "body": body[:500],
        "text": f"{subject} {body[:300]}".strip(),
    }


def fetch_emails(creds: Credentials, max_results: int = 10) -> list[dict]:
    """Fetch recent emails from Gmail inbox."""
    service = _build_gmail_service(creds)

    results = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        labelIds=["INBOX"],
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return []

    emails = []
    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me",
            id=msg_ref["id"],
            format="full",
        ).execute()
        emails.append(_parse_email_message(msg))

    return emails
