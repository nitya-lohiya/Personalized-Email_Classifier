# Gmail API Setup Guide

Step-by-step instructions to connect Gmail to the Email Priority Classifier.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Name it `Email-Classifier`
4. Click **Create**

## Step 2: Enable Gmail API

1. In the left sidebar, go to **APIs & Services** → **Library**
2. Search for **Gmail API**
3. Click **Gmail API** → **Enable**

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** → **Create**
3. Fill in:
   - App name: `Email Classifier`
   - User support email: your email
   - Developer contact: your email
4. Click **Save and Continue**
5. On **Scopes** page, click **Add or Remove Scopes**
   - Add `https://www.googleapis.com/auth/gmail.readonly`
   - Click **Update** → **Save and Continue**
6. On **Test users** page, click **Add Users**
   - Add your Gmail address
   - Click **Save and Continue**

## Step 4: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. Application type: **Web application**
4. Name: `Email Classifier`
5. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:8000/auth/callback
   ```
6. Click **Create**
7. Click **Download JSON**
8. Rename the downloaded file to `credentials.json`
9. Move it to the project root:
   ```
   mv ~/Downloads/client_secret_*.json /path/to/email-classifier/credentials.json
   ```

## Step 5: Test the OAuth Flow

1. Start the server:
   ```bash
   source .venv/bin/activate
   uvicorn main:app --reload
   ```

2. Open your browser and go to:
   ```
   http://localhost:8000/auth/login
   ```

3. You'll be redirected to Google sign-in. Log in with the Gmail account you added as a test user.

4. Click **Continue** on the "Google hasn't verified this app" screen (this is expected for test apps).

5. Grant permission to read your emails.

6. You'll be redirected back to the app with a success message:
   ```json
   {
     "status": "authenticated",
     "message": "Gmail connected successfully! Token saved to token.json."
   }
   ```

7. A `token.json` file is now saved in your project root.

## Step 6: Fetch & Classify Your Emails

Visit in your browser or use curl:

```bash
# Fetch 10 emails (default)
curl http://localhost:8000/emails/gmail

# Fetch 5 emails
curl "http://localhost:8000/emails/gmail?max_results=5"
```

Each email will be classified as **High**, **Medium**, or **Low** priority.

## Step 7: Run Gmail Tests

```bash
python test_gmail.py
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `credentials.json not found` | Download from Google Cloud Console (Step 4) |
| `Not authenticated` | Visit `/auth/login` to complete OAuth flow |
| `Access denied` | Add your email as a test user (Step 3.6) |
| `Token expired` | Visit `/auth/login` again to re-authenticate |
| `redirect_uri_mismatch` | Make sure `http://localhost:8000/auth/callback` is in your authorized redirect URIs (Step 4.5) |

## File Reference

| File | Purpose |
|------|---------|
| `credentials.json` | OAuth client credentials (from Google Cloud) |
| `token.json` | Auto-generated after first login (contains access/refresh tokens) |
| `gmail_service.py` | Gmail API wrapper (OAuth + email fetching) |
| `test_gmail.py` | Gmail integration tests |

## Security Notes

- **Never commit** `credentials.json` or `token.json` to git
- Add both to `.gitignore`:
  ```
  credentials.json
  token.json
  ```
- The app only requests **read-only** access (`gmail.readonly`)
- Tokens are stored locally and never sent to any third party
