import os
import time
import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from transformers import BertTokenizer, BertForSequenceClassification

import gmail_service


# ── Pydantic models ──────────────────────────────────────

class EmailRequest(BaseModel):
    text: str

class BatchEmailRequest(BaseModel):
    emails: list[str]

class PredictionResponse(BaseModel):
    priority: str
    confidence: float
    response_time_ms: float

class BatchPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]
    total_emails: int
    response_time_ms: float


# ── Globals ──────────────────────────────────────────────

LABEL_MAP = {0: "High", 1: "Medium", 2: "Low"}
MODEL_PATH = "bert_email_classifier"

model = None
tokenizer = None
device = None


# ── Model loading ────────────────────────────────────────

def load_model():
    global model, tokenizer, device

    device = (
        "mps" if torch.backends.mps.is_available()
        else "cuda" if torch.cuda.is_available()
        else "cpu"
    )

    tokenizer = BertTokenizer.from_pretrained(MODEL_PATH)
    model = BertForSequenceClassification.from_pretrained(MODEL_PATH)
    model.to(device)
    model.eval()


def predict_email(email_text: str) -> tuple[str, float]:
    inputs = tokenizer(email_text, return_tensors="pt", truncation=True, max_length=128)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        predicted_class = torch.argmax(probs).item()
        confidence = probs[0][predicted_class].item()

    return LABEL_MAP[predicted_class], confidence


# ── App lifecycle ────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield


# ── FastAPI app ──────────────────────────────────────────

app = FastAPI(
    title="Email Priority Classifier API",
    description="Classify emails into High, Medium, or Low priority using a fine-tuned BERT model (99.7% accuracy).",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Endpoints ────────────────────────────────────────────

@app.get("/")
def homepage():
    return {
        "service": "Email Priority Classifier",
        "model": "BERT (fine-tuned)",
        "classes": ["High", "Medium", "Low"],
        "endpoints": {
            "GET /": "This page",
            "GET /health": "Health check",
            "POST /predict": "Classify a single email",
            "POST /classify_batch": "Classify multiple emails",
            "GET /test_data": "Sample emails for testing",
            "GET /auth/login": "Start Gmail OAuth login",
            "GET /auth/callback": "Handle Google OAuth redirect",
            "GET /emails/gmail": "Fetch & classify Gmail emails",
        },
        "docs": "Visit /docs for interactive Swagger UI",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "device": device,
    }


@app.post("/predict", response_model=PredictionResponse)
def predict(request: EmailRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Email text cannot be empty")

    start = time.perf_counter()
    priority, confidence = predict_email(request.text)
    elapsed_ms = (time.perf_counter() - start) * 1000

    return PredictionResponse(
        priority=priority,
        confidence=round(confidence, 4),
        response_time_ms=round(elapsed_ms, 2),
    )


@app.post("/classify_batch", response_model=BatchPredictionResponse)
def classify_batch(request: BatchEmailRequest):
    if not request.emails:
        raise HTTPException(status_code=400, detail="Email list cannot be empty")
    if len(request.emails) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 emails per batch")

    start = time.perf_counter()
    predictions = []
    for email_text in request.emails:
        t0 = time.perf_counter()
        priority, confidence = predict_email(email_text)
        t1 = time.perf_counter()
        predictions.append(PredictionResponse(
            priority=priority,
            confidence=round(confidence, 4),
            response_time_ms=round((t1 - t0) * 1000, 2),
        ))
    elapsed_ms = (time.perf_counter() - start) * 1000

    return BatchPredictionResponse(
        predictions=predictions,
        total_emails=len(request.emails),
        response_time_ms=round(elapsed_ms, 2),
    )


@app.get("/test_data")
def test_data():
    return {
        "sample_emails": [
            {
                "text": "Your verification code is 847392. It will expire in 10 minutes.",
                "expected_priority": "High",
            },
            {
                "text": "Security alert: Unusual login detected from new device",
                "expected_priority": "High",
            },
            {
                "text": "You have 5 new likes on your Instagram post",
                "expected_priority": "Medium",
            },
            {
                "text": "Reply to your thread: Best machine learning resources",
                "expected_priority": "Medium",
            },
            {
                "text": "SALE! 70% OFF EVERYTHING! Limited time offer!",
                "expected_priority": "Low",
            },
            {
                "text": "Congratulations! You won $1,000,000! Click here to claim",
                "expected_priority": "Low",
            },
        ],
        "usage": 'POST /predict with {"text": "<email text>"}',
    }


# ── Gmail Endpoints ─────────────────────────────────────

@app.get("/auth/login")
def gmail_login():
    """Start Gmail OAuth flow — redirects user to Google login."""
    if not os.path.exists(gmail_service.CREDENTIALS_FILE):
        raise HTTPException(
            status_code=500,
            detail="credentials.json not found. Download it from Google Cloud Console. See GMAIL_SETUP_GUIDE.md.",
        )
    auth_url = gmail_service.get_auth_url()
    return RedirectResponse(url=auth_url)


@app.get("/auth/callback")
def gmail_callback(code: str = Query(...), scope: str = Query(default="")):
    """Handle Google OAuth redirect and save token."""
    try:
        creds = gmail_service.authenticate(code)
        return {
            "status": "authenticated",
            "message": "Gmail connected successfully! Token saved to token.json.",
            "next_step": "Visit /emails/gmail to fetch and classify your emails.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {e}")


@app.get("/emails/gmail")
def fetch_and_classify_gmail(max_results: int = Query(default=10, ge=1, le=50)):
    """Fetch emails from Gmail and classify them with BERT."""
    creds = gmail_service.get_credentials()
    if creds is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Visit /auth/login first.",
        )

    try:
        emails = gmail_service.fetch_emails(creds, max_results=max_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {e}")

    results = []
    for email in emails:
        priority, confidence = predict_email(email["text"])
        results.append({
            "id": email["id"],
            "subject": email["subject"],
            "from": email["from"],
            "date": email["date"],
            "snippet": email["snippet"],
            "priority": priority,
            "confidence": round(confidence, 4),
        })

    return {
        "total_emails": len(results),
        "emails": results,
    }
