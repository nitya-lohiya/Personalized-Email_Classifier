from gmail_service import fetch_emails, get_auth_url


def run():
    try:
        emails = fetch_emails(max_results=5)
        print("Fetched emails:")
        for index, email in enumerate(emails, start=1):
            print(f"{index}. {email.get('subject')} from {email.get('from')} ({email.get('date')})")
    except FileNotFoundError as exc:
        print(str(exc))
        print("\nStart authentication by opening this URL in your browser:")
        print(get_auth_url())


if __name__ == "__main__":
    run()
