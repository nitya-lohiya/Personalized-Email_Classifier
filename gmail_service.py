import os
import re
import html
import json
import base64
from concurrent.futures import ThreadPoolExecutor
from email.utils import parsedate_to_datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


_URL_RE = re.compile(r"https?://\S+")
_FOOTER_MARKERS = [
    "unsubscribe",
    "manage your preferences",
    "manage preferences",
    "update your preferences",
    "© 20",
    "copyright ©",
    "all rights reserved",
    "linkedin corporation",
]

_HEADER_JUNK_PATTERNS = [
    re.compile(r"^this email was (intended|sent) (for|to)\b.*$", re.IGNORECASE),
    re.compile(r"^learn why we included this\b.*$", re.IGNORECASE),
    re.compile(r"^view (this email )?in (your )?browser\b.*$", re.IGNORECASE),
    re.compile(r"^you are receiving this\b.*$", re.IGNORECASE),
    re.compile(r"^you received this\b.*$", re.IGNORECASE),
]


def _clean_text(raw: str) -> str:
    """Strip URLs, drop boilerplate lines, and cut off marketing-email footers."""
    # Remove all http(s) URLs
    raw = _URL_RE.sub("", raw)

    lines = raw.splitlines()
    keep = []
    for line in lines:
        stripped = line.strip()
        lowered = stripped.lower()

        # Cut off the rest of the email at the first footer marker
        if any(marker in lowered for marker in _FOOTER_MARKERS):
            break

        # Skip individual header junk lines (but keep scanning)
        if any(p.match(stripped) for p in _HEADER_JUNK_PATTERNS):
            continue

        keep.append(line)

    raw = "\n".join(keep)

    # Collapse whitespace
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n\s*\n\s*\n+", "\n\n", raw)
    return raw.strip()


def _strip_html(raw: str) -> str:
    """Turn HTML into readable plain text."""
    # Drop <script> and <style> blocks entirely
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
    # <br>, <p>, </p>, </div> → newline
    raw = re.sub(r"<\s*br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    raw = re.sub(r"</\s*(p|div|tr|li|h[1-6])\s*>", "\n", raw, flags=re.IGNORECASE)
    # Strip all other tags
    raw = re.sub(r"<[^>]+>", "", raw)
    # Decode HTML entities (&amp;, &#39;, &nbsp;, etc.)
    raw = html.unescape(raw)
    return _clean_text(raw)


def _extract_raw_body(payload: dict) -> str:
    """Recursively find raw body text — prefer text/plain, fall back to HTML-stripped.
    No URL removal or footer cutting — that's only for display."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if body_data and mime_type == "text/plain":
        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

    if body_data and mime_type == "text/html":
        html_text = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
        # Strip tags but don't remove URLs — BERT was trained on text that had them
        stripped = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
        stripped = re.sub(r"<\s*br\s*/?>", "\n", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"</\s*(p|div|tr|li|h[1-6])\s*>", "\n", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"<[^>]+>", "", stripped)
        stripped = html.unescape(stripped)
        stripped = re.sub(r"[ \t]+", " ", stripped)
        return stripped.strip()

    # Walk multipart
    parts = payload.get("parts", [])
    plain = ""
    htmlish = ""
    for part in parts:
        found = _extract_raw_body(part)
        if not found:
            continue
        if part.get("mimeType") == "text/plain" and not plain:
            plain = found
        elif part.get("mimeType") == "text/html" and not htmlish:
            htmlish = found
        elif not plain and not htmlish:
            plain = found

    return plain or htmlish

# Allow OAuth over plain http:// for local development.
# Google's OAuth library rejects non-HTTPS redirects by default.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

# OAuth config
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
REDIRECT_URI = "http://localhost:8000/auth/callback"


_flow_state: dict = {"code_verifier": None}


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
    # Persist the PKCE verifier so /auth/callback can reuse it.
    _flow_state["code_verifier"] = flow.code_verifier
    return auth_url


def authenticate(auth_code: str) -> Credentials:
    """Exchange the authorization code for credentials and save token."""
    flow = _get_flow()
    # Restore the PKCE verifier from the login step.
    flow.code_verifier = _flow_state.get("code_verifier")
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

    # Extract raw body (for BERT) and cleaned body (for display)
    raw_body = _extract_raw_body(msg.get("payload", {}))
    display_body = _clean_text(raw_body)

    # Parse date
    date_str = header_map.get("date", "")
    try:
        date_parsed = parsedate_to_datetime(date_str).isoformat()
    except Exception:
        date_parsed = date_str

    subject = header_map.get("subject", "(no subject)")
    sender = header_map.get("from", "unknown")
    snippet = msg.get("snippet", "")

    return {
        "id": msg["id"],
        "subject": subject,
        "from": sender,
        "date": date_parsed,
        "snippet": snippet,
        "body": display_body[:5000],
        # Classifier input: subject + raw body (matches what the model saw
        # in its first working version). Display uses the cleaned body.
        "text": f"{subject} {raw_body[:300]}".strip(),
    }


def fetch_emails(creds: Credentials, max_results: int = 10) -> list[dict]:
    """Fetch recent emails from Gmail inbox in parallel."""
    service = _build_gmail_service(creds)

    results = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        labelIds=["INBOX"],
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return []

    def fetch_one(msg_ref):
        # Each thread gets its own service instance — googleapiclient's
        # httplib2 is not thread-safe on shared instances.
        thread_service = _build_gmail_service(creds)
        msg = thread_service.users().messages().get(
            userId="me",
            id=msg_ref["id"],
            format="full",
        ).execute()
        return _parse_email_message(msg)

    # Fetch in parallel — preserves order of the input list.
    with ThreadPoolExecutor(max_workers=10) as executor:
        emails = list(executor.map(fetch_one, messages))

    return emails
