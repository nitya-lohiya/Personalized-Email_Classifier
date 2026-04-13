
#Test client for the Email Priority Classifier API.
#Run the server first: uvicorn main:app --reload
#Then run this script: python test_api_client.py


import time
import requests

BASE_URL = "http://127.0.0.1:8000"


def test_homepage():
    print("=" * 60)
    print("TEST 1: GET / (Homepage)")
    print("=" * 60)
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200
    data = r.json()
    assert "service" in data
    assert len(data["endpoints"]) == 5
    print(f"  Status: {r.status_code}")
    print(f"  Service: {data['service']}")
    print(f"  Endpoints: {len(data['endpoints'])}")
    print("  PASSED\n")


def test_health():
    print("=" * 60)
    print("TEST 2: GET /health")
    print("=" * 60)
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    print(f"  Status: {data['status']}")
    print(f"  Model loaded: {data['model_loaded']}")
    print(f"  Device: {data['device']}")
    print("  PASSED\n")


def test_predict():
    print("=" * 60)
    print("TEST 3: POST /predict (Single email)")
    print("=" * 60)

    test_cases = [
        ("Your verification code is 847392. Expires in 10 min.", "High"),
        ("Security alert: Unusual login from new device", "High"),
        ("You have 5 new likes on your Instagram post", "Medium"),
        ("Reply to your thread: Best ML resources", "Medium"),
        ("SALE! 70% OFF EVERYTHING! Limited time!", "Low"),
        ("Congratulations! You won $1,000,000! Click here", "Low"),
    ]

    all_passed = True
    times = []

    for email_text, expected in test_cases:
        r = requests.post(f"{BASE_URL}/predict", json={"text": email_text})
        assert r.status_code == 200
        data = r.json()
        times.append(data["response_time_ms"])

        match = data["priority"] == expected
        symbol = "PASS" if match else "FAIL"
        if not match:
            all_passed = False

        print(f"  [{symbol}] Expected={expected}, Got={data['priority']} "
              f"({data['confidence']*100:.1f}%) [{data['response_time_ms']:.1f}ms]")
        print(f"         {email_text[:60]}")

    avg_time = sum(times) / len(times)
    print(f"\n  Average response time: {avg_time:.1f}ms")
    print(f"  Max response time: {max(times):.1f}ms")
    if all_passed:
        print("  ALL PREDICTIONS CORRECT\n")
    else:
        print("  SOME PREDICTIONS INCORRECT\n")


def test_predict_empty():
    print("=" * 60)
    print("TEST 4: POST /predict (Empty input - should fail)")
    print("=" * 60)
    r = requests.post(f"{BASE_URL}/predict", json={"text": "  "})
    assert r.status_code == 400
    print(f"  Status: {r.status_code} (expected 400)")
    print(f"  Detail: {r.json()['detail']}")
    print("  PASSED\n")


def test_classify_batch():
    print("=" * 60)
    print("TEST 5: POST /classify_batch")
    print("=" * 60)
    emails = [
        "Your OTP is 123456",
        "You have a new follower on Twitter",
        "50% off everything today only!",
        "Account password changed successfully",
        "New comment on your forum post",
    ]
    r = requests.post(f"{BASE_URL}/classify_batch", json={"emails": emails})
    assert r.status_code == 200
    data = r.json()
    assert data["total_emails"] == 5
    assert len(data["predictions"]) == 5

    print(f"  Total emails: {data['total_emails']}")
    print(f"  Total time: {data['response_time_ms']:.1f}ms")
    for i, (email, pred) in enumerate(zip(emails, data["predictions"])):
        print(f"  [{i+1}] {pred['priority']:>6} ({pred['confidence']*100:.1f}%) - {email[:50]}")
    print("  PASSED\n")


def test_batch_empty():
    print("=" * 60)
    print("TEST 6: POST /classify_batch (Empty list - should fail)")
    print("=" * 60)
    r = requests.post(f"{BASE_URL}/classify_batch", json={"emails": []})
    assert r.status_code == 400
    print(f"  Status: {r.status_code} (expected 400)")
    print(f"  Detail: {r.json()['detail']}")
    print("  PASSED\n")


def test_test_data():
    print("=" * 60)
    print("TEST 7: GET /test_data")
    print("=" * 60)
    r = requests.get(f"{BASE_URL}/test_data")
    assert r.status_code == 200
    data = r.json()
    samples = data["sample_emails"]
    assert len(samples) == 6
    print(f"  Sample emails returned: {len(samples)}")
    for s in samples:
        print(f"    [{s['expected_priority']:>6}] {s['text'][:55]}")
    print("  PASSED\n")


def test_response_time():
    print("=" * 60)
    print("TEST 8: Response time benchmark (<200ms target)")
    print("=" * 60)
    email = "Your verification code is 999999"
    times = []
    for i in range(10):
        r = requests.post(f"{BASE_URL}/predict", json={"text": email})
        times.append(r.json()["response_time_ms"])

    avg = sum(times) / len(times)
    p95 = sorted(times)[8]
    print(f"  10 requests completed")
    print(f"  Average: {avg:.1f}ms")
    print(f"  P95:     {p95:.1f}ms")
    print(f"  Min:     {min(times):.1f}ms")
    print(f"  Max:     {max(times):.1f}ms")
    if avg < 200:
        print(f"  TARGET MET (avg < 200ms)")
    else:
        print(f"  TARGET MISSED (avg >= 200ms)")
    print("  PASSED\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("EMAIL CLASSIFIER API - TEST SUITE")
    print("=" * 60 + "\n")

    start = time.time()

    test_homepage()
    test_health()
    test_predict()
    test_predict_empty()
    test_classify_batch()
    test_batch_empty()
    test_test_data()
    test_response_time()

    elapsed = time.time() - start

    print("=" * 60)
    print(f"ALL 8 TESTS PASSED ({elapsed:.1f}s)")
    print("=" * 60)
