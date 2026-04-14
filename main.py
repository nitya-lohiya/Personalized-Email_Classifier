import os
import time
import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import BertTokenizer, BertForSequenceClassification

import gmail_service

FRONTEND_URL = "http://localhost:5173"


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
MODEL_PATH = "nityalohiya/BERT_Email_Classifier"

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


# ── Heuristic layer (BERT stays primary) ─────────────────
# These rules only fire when:
#   (a) There's a critical-miss-worthy High signal (security/verification)
#   (b) BERT's confidence is below CONFIDENCE_FLOOR and a heuristic matches
# If BERT is confident and no strong override exists, BERT wins.

CONFIDENCE_FLOOR = 0.70

# Rule-breaking: these ALWAYS override BERT regardless of its confidence,
# because mislabeling a verification code is unacceptable.
_HIGH_CRITICAL_KEYWORDS = [
    "verification code", "verify your account", "2-step verification",
    "two-factor", "2fa code", "one-time password", "one time password",
    "otp code", "security alert", "suspicious activity",
    "unusual sign-in", "password reset", "reset your password",
    "confirm your email", "confirm your account",
]

_HIGH_CRITICAL_SENDERS = [
    "accounts.google.com", "no-reply@accounts.google",
    "noreply@accounts.google", "security-noreply@",
    "@github-noreply", "security@", "@paypal.com",
]

# Soft hints: only used when BERT is uncertain.
_HIGH_SOFT_KEYWORDS = [
    "your order", "order confirmation", "has shipped", "out for delivery",
    "payment received", "receipt for", "invoice", "statement available",
]

_MEDIUM_SOFT_KEYWORDS = [
    "accepted your invitation", "invitation to connect", "wants to connect",
    "new follower", "mentioned you", "tagged you", "replied to",
    "commented on", "new message from", "liked your", "newsletter",
    "weekly digest", "daily update", "new jobs", "job alert",
]

_MEDIUM_SOFT_SENDERS = [
    "linkedin.com", "@twitter.com", "@x.com", "@instagram.com",
    "@facebook.com", "@reddit.com", "@discord.com", "@substack.com",
]

_LOW_SOFT_KEYWORDS = [
    "% off", "sale ends", "limited time offer", "flash sale",
    "clearance", "discount code", "free shipping on orders",
    "last chance", "exclusive deal",
]


def apply_heuristics(
    subject: str,
    sender: str,
    bert_priority: str,
    bert_confidence: float,
) -> tuple[str, float, str]:
    """Layer heuristics on top of BERT. Returns (priority, confidence, source).
    source is 'bert', 'heuristic-override', or 'heuristic-tiebreak'."""
    subject_l = (subject or "").lower()
    sender_l = (sender or "").lower()
    combined = f"{subject_l} {sender_l}"

    # 1. Critical High overrides — fire even when BERT is confident
    if any(k in combined for k in _HIGH_CRITICAL_KEYWORDS):
        if bert_priority != "High":
            return "High", max(bert_confidence, 0.95), "heuristic-override"
        return bert_priority, bert_confidence, "bert"

    if any(s in sender_l for s in _HIGH_CRITICAL_SENDERS):
        if bert_priority != "High":
            return "High", max(bert_confidence, 0.92), "heuristic-override"
        return bert_priority, bert_confidence, "bert"

    # 2. If BERT is confident, trust it — don't meddle
    if bert_confidence >= CONFIDENCE_FLOOR:
        return bert_priority, bert_confidence, "bert"

    # 3. BERT is uncertain — let soft heuristics break the tie
    if any(k in combined for k in _HIGH_SOFT_KEYWORDS):
        return "High", 0.80, "heuristic-tiebreak"
    if any(k in combined for k in _MEDIUM_SOFT_KEYWORDS):
        return "Medium", 0.78, "heuristic-tiebreak"
    if any(s in sender_l for s in _MEDIUM_SOFT_SENDERS):
        return "Medium", 0.75, "heuristic-tiebreak"
    if any(k in subject_l for k in _LOW_SOFT_KEYWORDS):
        return "Low", 0.80, "heuristic-tiebreak"

    # 4. Nothing matched — stick with BERT even if uncertain
    return bert_priority, bert_confidence, "bert"


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

# Allow the React frontend (Vite dev server) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    """Handle Google OAuth redirect, save token, and return to the frontend."""
    try:
        gmail_service.authenticate(code)
        return RedirectResponse(url=f"{FRONTEND_URL}/?auth=success")
    except Exception as e:
        return RedirectResponse(url=f"{FRONTEND_URL}/?auth=error&message={e}")


@app.get("/auth/status")
def auth_status():
    """Check if a valid Gmail token is saved."""
    creds = gmail_service.get_credentials()
    return {"authenticated": creds is not None}


@app.get("/emails/gmail")
def fetch_and_classify_gmail(max_results: int = Query(default=10, ge=1, le=100)):
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
        bert_priority, bert_confidence = predict_email(email["text"])
        priority, confidence, source = apply_heuristics(
            email["subject"], email["from"], bert_priority, bert_confidence
        )
        results.append({
            "id": email["id"],
            "subject": email["subject"],
            "from": email["from"],
            "date": email["date"],
            "snippet": email["snippet"],
            "body": email["body"],
            "priority": priority,
            "confidence": round(confidence, 4),
            "classifier": source,
        })

    return {
        "total_emails": len(results),
        "emails": results,
    }
