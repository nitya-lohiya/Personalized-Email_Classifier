from flask import Flask, jsonify, redirect, request

from gmail_service import authenticate, fetch_emails, get_auth_url

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify(
        {
            "routes": [
                "/auth/login",
                "/auth/callback",
                "/emails/gmail?max=10",
            ]
        }
    )


@app.route("/auth/login")
def auth_login():
    return redirect(get_auth_url())


@app.route("/auth/callback")
def auth_callback():
    result = authenticate(request.url)
    return jsonify(
        {
            "success": True,
            "message": "Authenticated successfully. token.json was saved.",
            "credentials": result,
        }
    )


@app.route("/emails/gmail")
def emails_gmail():
    max_results = request.args.get("max", default=10, type=int)
    emails = fetch_emails(max_results=max_results)
    return jsonify({"success": True, "emails": emails})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
