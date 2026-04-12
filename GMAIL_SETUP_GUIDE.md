# Gmail Integration Setup Guide

## 1. Enable Gmail API

1. Go to the Google Cloud Console: https://console.cloud.google.com/
2. Create or select a project.
3. Enable the Gmail API for the project.
4. Create OAuth 2.0 Client IDs credentials.
   - Application type: Web application
   - Authorized redirect URI: `http://localhost:8000/auth/callback`
5. Download the JSON credentials file and save it as `credentials.json` in the project root.

## 2. Install required Python packages

Run:

```bash
pip install flask google-auth google-auth-oauthlib google-api-python-client
```

## 3. Run the API server

```bash
python main.py
```

## 4. Authenticate with Google

1. Open in your browser:
   - `http://localhost:8000/auth/login`
2. Grant Gmail read access.
3. After successful login, `token.json` is created automatically.

## 5. Fetch Gmail emails

Open:

```bash
http://localhost:8000/emails/gmail?max=10
```

## 6. Test locally

```bash
python test_gmail.py
```

## Notes

- Keep `credentials.json` and `token.json` private.
- `token.json` is generated after the OAuth flow completes.
- If you need a secure deployment, use HTTPS and do not set `OAUTHLIB_INSECURE_TRANSPORT` in production.
