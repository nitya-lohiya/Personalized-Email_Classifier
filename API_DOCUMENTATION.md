# Email Priority Classifier API

A FastAPI server that classifies emails into **High**, **Medium**, or **Low** priority using a fine-tuned BERT model with 99.7% accuracy.

## Quick Start

```bash
# Install dependencies
pip install fastapi uvicorn torch transformers

# Start the server
uvicorn main:app --reload

# Server runs at http://127.0.0.1:8000
# Interactive docs at http://127.0.0.1:8000/docs
```

## Endpoints

### GET `/`
Returns API info and available endpoints.

**Response:**
```json
{
  "service": "Email Priority Classifier",
  "model": "BERT (fine-tuned)",
  "classes": ["High", "Medium", "Low"],
  "endpoints": { ... },
  "docs": "Visit /docs for interactive Swagger UI"
}
```

---

### GET `/health`
Health check — confirms model is loaded and ready.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "mps"
}
```

---

### POST `/predict`
Classify a single email.

**Request:**
```json
{
  "text": "Your verification code is 847392. It will expire in 10 minutes."
}
```

**Response:**
```json
{
  "priority": "High",
  "confidence": 0.9999,
  "response_time_ms": 11.2
}
```

**Errors:**
- `400` — empty text

---

### POST `/classify_batch`
Classify multiple emails in one request (max 100).

**Request:**
```json
{
  "emails": [
    "Your OTP is 123456",
    "50% off everything today!",
    "New comment on your forum post"
  ]
}
```

**Response:**
```json
{
  "predictions": [
    { "priority": "High",   "confidence": 0.9995, "response_time_ms": 12.1 },
    { "priority": "Low",    "confidence": 0.9997, "response_time_ms": 10.3 },
    { "priority": "Medium", "confidence": 0.9998, "response_time_ms": 11.5 }
  ],
  "total_emails": 3,
  "response_time_ms": 34.2
}
```

**Errors:**
- `400` — empty list or more than 100 emails

---

### GET `/test_data`
Returns sample emails you can use to test the `/predict` endpoint.

**Response:**
```json
{
  "sample_emails": [
    { "text": "Your verification code is 847392...", "expected_priority": "High" },
    { "text": "SALE! 70% OFF EVERYTHING!...", "expected_priority": "Low" }
  ],
  "usage": "POST /predict with {\"text\": \"<email text>\"}"
}
```

## Priority Classes

| Priority | Description | Examples |
|----------|-------------|----------|
| **High** | Time-sensitive, requires action | Verification codes, security alerts, account updates |
| **Medium** | Important but can wait | Social media notifications, forum discussions |
| **Low** | Can ignore or delete | Promotions, spam, phishing attempts |

## Model Details

- **Base model:** `bert-base-uncased` (109M parameters)
- **Fine-tuned on:** 10,780 emails from HuggingFace dataset
- **Test accuracy:** 99.70% on 2,697 test emails
- **Max input length:** 128 tokens
- **Avg response time:** ~11ms (after warmup, Apple Silicon MPS)

## Testing

```bash
# Start server first
uvicorn main:app --reload

# Run test suite (in another terminal)
python test_api_client.py
```

The test suite covers all endpoints, prediction accuracy, error handling, and response time benchmarks.

## Interactive Docs

FastAPI auto-generates interactive API docs:
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
