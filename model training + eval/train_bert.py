import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertForSequenceClassification, get_linear_schedule_with_warmup
from torch.optim import AdamW
import time

# ── Config ──────────────────────────────────────────────
EPOCHS = 3
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
MAX_LENGTH = 128
DEVICE = (
    "mps" if torch.backends.mps.is_available()
    else "cuda" if torch.cuda.is_available()
    else "cpu"
)

LABEL_MAP = {"High": 0, "Medium": 1, "Low": 2}

print(f"Using device: {DEVICE}")

# ── Dataset class ───────────────────────────────────────
class EmailDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokenizer(
            self.texts[idx],
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long),
        }

# ── Load data ───────────────────────────────────────────
print("Loading data...")
train_df = pd.read_csv("train_3class.csv")
test_df = pd.read_csv("test_3class.csv")

train_texts = train_df["text"].tolist()
train_labels = train_df["priority"].map(LABEL_MAP).tolist()

test_texts = test_df["text"].tolist()
test_labels = test_df["priority"].map(LABEL_MAP).tolist()

print(f"Training: {len(train_texts)} emails")
print(f"Testing:  {len(test_texts)} emails")

# ── Tokenizer & model ──────────────────────────────────
print("Loading BERT...")
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=3)
model.to(DEVICE)

# ── DataLoaders ─────────────────────────────────────────
train_dataset = EmailDataset(train_texts, train_labels, tokenizer, MAX_LENGTH)
test_dataset = EmailDataset(test_texts, test_labels, tokenizer, MAX_LENGTH)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)

# ── Optimizer & scheduler ───────────────────────────────
optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)
total_steps = len(train_loader) * EPOCHS
scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=0, num_training_steps=total_steps)

# ── Training loop ───────────────────────────────────────
print(f"\nStarting training for {EPOCHS} epochs...")

for epoch in range(EPOCHS):
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    start = time.time()

    for batch_idx, batch in enumerate(train_loader):
        input_ids = batch["input_ids"].to(DEVICE)
        attention_mask = batch["attention_mask"].to(DEVICE)
        labels = batch["labels"].to(DEVICE)

        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()

        total_loss += loss.item()
        preds = outputs.logits.argmax(dim=-1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

        if (batch_idx + 1) % 50 == 0:
            print(f"  Epoch {epoch+1} | Batch {batch_idx+1}/{len(train_loader)} | Loss: {loss.item():.4f}")

    elapsed = time.time() - start
    avg_loss = total_loss / len(train_loader)
    accuracy = correct / total * 100
    print(f"Epoch {epoch+1}/{EPOCHS} | Loss: {avg_loss:.4f} | Train Acc: {accuracy:.1f}% | Time: {elapsed:.0f}s")

# ── Evaluation ──────────────────────────────────────────
print("\nEvaluating on test set...")
model.eval()
correct = 0
total = 0

with torch.no_grad():
    for batch in test_loader:
        input_ids = batch["input_ids"].to(DEVICE)
        attention_mask = batch["attention_mask"].to(DEVICE)
        labels = batch["labels"].to(DEVICE)

        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        preds = outputs.logits.argmax(dim=-1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

test_accuracy = correct / total * 100
print(f"\n{'='*50}")
print(f"TEST ACCURACY: {test_accuracy:.2f}%")
print(f"{'='*50}")

# ── Save model ──────────────────────────────────────────
save_path = "bert_email_classifier"
model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)
print(f"\n✓ Model saved to {save_path}/")
