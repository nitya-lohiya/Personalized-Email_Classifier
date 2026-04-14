import torch
import pandas as pd
from transformers import BertTokenizer, BertForSequenceClassification
from sklearn.metrics import classification_report, confusion_matrix

LABEL_MAP = {0: "High", 1: "Medium", 2: "Low"}
MODEL_PATH = "bert_email_classifier"

# ── Load model ──────────────────────────────────────────
print("Loading your trained model...")
tokenizer = BertTokenizer.from_pretrained(MODEL_PATH)
model = BertForSequenceClassification.from_pretrained(MODEL_PATH)
model.eval()
print("✓ Model loaded!\n")

DEVICE = (
    "mps" if torch.backends.mps.is_available()
    else "cuda" if torch.cuda.is_available()
    else "cpu"
)
model.to(DEVICE)


def predict_email(email_text):
    """Predict priority for a single email."""
    inputs = tokenizer(email_text, return_tensors="pt", truncation=True, max_length=128)
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        predicted_class = torch.argmax(probs).item()
        confidence = probs[0][predicted_class].item()

    return LABEL_MAP[predicted_class], confidence


# ── Part 1: Sample email predictions ───────────────────
print("=" * 60)
print("PART 1: SAMPLE EMAIL PREDICTIONS")
print("=" * 60)

test_emails = [
    "Your verification code is 847392. It will expire in 10 minutes.",
    "Security alert: Unusual login detected from new device",
    "You have 5 new likes on your Instagram post",
    "Reply to your thread: Best machine learning resources",
    "SALE! 70% OFF EVERYTHING! Limited time offer!",
    "Congratulations! You won $1,000,000! Click here to claim",
    "Meeting notes from this morning's standup attached",
    "Your weekly newsletter: Top tech stories",
]

for email in test_emails:
    priority, confidence = predict_email(email)

    if priority == "High":
        symbol = "🔴"
    elif priority == "Medium":
        symbol = "🟡"
    else:
        symbol = "🟢"

    print(f"\n{symbol} {priority.upper()} ({confidence * 100:.1f}% confident)")
    print(f"   Email: {email[:70]}")


# ── Part 2: Full test set evaluation ───────────────────
print("\n\n" + "=" * 60)
print("PART 2: FULL TEST SET EVALUATION (2,697 emails)")
print("=" * 60)

PRIORITY_MAP = {"High": 0, "Medium": 1, "Low": 2}
test_df = pd.read_csv("test_3class.csv")

true_labels = []
pred_labels = []

print("\nRunning predictions on all test emails...")
for i, row in test_df.iterrows():
    priority, _ = predict_email(row["text"])
    pred_labels.append(priority)
    true_labels.append(row["priority"])

    if (i + 1) % 500 == 0:
        print(f"  Processed {i + 1}/{len(test_df)} emails...")

print(f"  Processed {len(test_df)}/{len(test_df)} emails... done!")

# Classification report
print("\n" + "-" * 60)
print("CLASSIFICATION REPORT")
print("-" * 60)
print(classification_report(true_labels, pred_labels, target_names=["High", "Medium", "Low"]))

# Confusion matrix
print("-" * 60)
print("CONFUSION MATRIX")
print("-" * 60)
cm = confusion_matrix(true_labels, pred_labels, labels=["High", "Medium", "Low"])
print(f"{'':>10} {'High':>8} {'Medium':>8} {'Low':>8}   ← Predicted")
print(f"{'High':>10} {cm[0][0]:>8} {cm[0][1]:>8} {cm[0][2]:>8}")
print(f"{'Medium':>10} {cm[1][0]:>8} {cm[1][1]:>8} {cm[1][2]:>8}")
print(f"{'Low':>10} {cm[2][0]:>8} {cm[2][1]:>8} {cm[2][2]:>8}")
print(f"{'':>10} ↑ Actual")

# Error analysis
print("\n" + "-" * 60)
print("ERROR ANALYSIS")
print("-" * 60)

errors = [(true, pred, text) for true, pred, text in zip(true_labels, pred_labels, test_df["text"]) if true != pred]
print(f"\nTotal errors: {len(errors)} out of {len(test_df)} ({len(errors)/len(test_df)*100:.2f}%)")

if errors:
    print(f"\nMisclassified emails:")
    for true, pred, text in errors:
        print(f"\n  True: {true} | Predicted: {pred}")
        print(f"  Text: {text[:100]}...")

print("\n" + "=" * 60)
print("EVALUATION COMPLETE")
print("=" * 60)
