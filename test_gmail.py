"""
Test Gmail integration for the Email Priority Classifier API.

Prerequisites:
  1. credentials.json in project root (from Google Cloud Console)
  2. Server running: uvicorn main:app --reload
  3. Complete OAuth flow first: visit http://localhost:8000/auth/login

Run: python test_gmail.py
"""

import os
import requests

BASE_URL = "http://127.0.0.1:8000"


def test_auth_login():
    print("=" * 60)
    print("TEST 1: GET /auth/login (OAuth redirect)")
    print("=" * 60)

    if not os.path.exists("credentials.json"):
        print("  SKIPPED — credentials.json not found")
        print("  Download it from Google Cloud Console first.\n")
        return False

    # Don't follow redirects — just check we get a redirect to Google
    r = requests.get(f"{BASE_URL}/auth/login", allow_redirects=False)
    if r.status_code == 307:
        location = r.headers.get("location", "")
        assert "accounts.google.com" in location
        print(f"  Status: {r.status_code} (redirect)")
        print(f"  Redirects to: {location[:80]}...")
        print("  PASSED\n")
        return True
    else:
        print(f"  Status: {r.status_code}")
        print(f"  Response: {r.json()}")
        print("  FAILED\n")
        return False


def test_auth_callback_no_code():
    print("=" * 60)
    print("TEST 2: GET /auth/callback (missing code - should fail)")
    print("=" * 60)
    r = requests.get(f"{BASE_URL}/auth/callback")
    assert r.status_code == 422  # FastAPI validation error
    print(f"  Status: {r.status_code} (expected 422 — missing 'code' param)")
    print("  PASSED\n")


def test_gmail_not_authenticated():
    print("=" * 60)
    print("TEST 3: GET /emails/gmail (not authenticated)")
    print("=" * 60)

    # Remove token to test unauthenticated state
    token_existed = os.path.exists("token.json")
    if token_existed:
        os.rename("token.json", "token.json.bak")

    try:
        r = requests.get(f"{BASE_URL}/emails/gmail")
        assert r.status_code == 401
        print(f"  Status: {r.status_code} (expected 401)")
        print(f"  Detail: {r.json()['detail']}")
        print("  PASSED\n")
    finally:
        if token_existed:
            os.rename("token.json.bak", "token.json")


def test_gmail_fetch_emails():
    print("=" * 60)
    print("TEST 4: GET /emails/gmail (fetch & classify)")
    print("=" * 60)

    if not os.path.exists("token.json"):
        print("  SKIPPED — not authenticated yet")
        print("  Visit http://localhost:8000/auth/login first.\n")
        return

    r = requests.get(f"{BASE_URL}/emails/gmail", params={"max_results": 5})

    if r.status_code == 401:
        print("  SKIPPED — token expired, re-authenticate at /auth/login\n")
        return

    assert r.status_code == 200
    data = r.json()
    print(f"  Fetched: {data['total_emails']} emails\n")

    for email in data["emails"]:
        priority = email["priority"]
        if priority == "High":
            symbol = "🔴"
        elif priority == "Medium":
            symbol = "🟡"
        else:
            symbol = "🟢"

        print(f"  {symbol} {priority:>6} ({email['confidence']*100:.1f}%)")
        print(f"    From: {email['from'][:50]}")
        print(f"    Subject: {email['subject'][:50]}")
        print(f"    Date: {email['date']}")
        print()

    print("  PASSED\n")


def test_gmail_max_results():
    print("=" * 60)
    print("TEST 5: GET /emails/gmail?max_results validation")
    print("=" * 60)

    # Test max_results > 50
    r = requests.get(f"{BASE_URL}/emails/gmail", params={"max_results": 100})
    assert r.status_code == 422
    print(f"  max_results=100 → {r.status_code} (expected 422)")

    # Test max_results < 1
    r = requests.get(f"{BASE_URL}/emails/gmail", params={"max_results": 0})
    assert r.status_code == 422
    print(f"  max_results=0   → {r.status_code} (expected 422)")

    print("  PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GMAIL INTEGRATION - TEST SUITE")
    print("=" * 60 + "\n")

    test_auth_login()
    test_auth_callback_no_code()
    test_gmail_not_authenticated()
    test_gmail_fetch_emails()
    test_gmail_max_results()

    print("=" * 60)
    print("GMAIL TESTS COMPLETE")
    print("=" * 60)
    print("\nIf tests were skipped, follow these steps:")
    print("  1. Add credentials.json (see GMAIL_SETUP_GUIDE.md)")
    print("  2. Visit http://localhost:8000/auth/login")
    print("  3. Complete Google sign-in")
    print("  4. Re-run this script")
