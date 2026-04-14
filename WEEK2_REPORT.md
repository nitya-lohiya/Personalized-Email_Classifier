# Week 2: Model Training & Evaluation Report

## What We Did
1. Verified BERT loads correctly with 3-class classification head
2. Fine-tuned BERT on 10,780 training emails (3 epochs)
3. Evaluated on 2,697 test emails
4. Built a testing/inference script with full evaluation metrics

## Training Setup
- **Model:** bert-base-uncased (109M parameters)
- **Device:** Apple Silicon MPS GPU
- **Epochs:** 3
- **Batch Size:** 16
- **Learning Rate:** 2e-5 with linear warmup scheduler
- **Max Token Length:** 128
- **Gradient Clipping:** 1.0

## Training Results

| Epoch | Loss   | Train Accuracy | Time   |
|-------|--------|----------------|--------|
| 1     | 0.0873 | 97.5%          | ~7 min |
| 2     | 0.0078 | 99.8%          | ~8 min |
| 3     | 0.0016 | 100.0%         | ~8 min |

Total training time: ~23 minutes

## Test Set Results
- **Test Accuracy: 99.70%**
- Only ~8 misclassified emails out of 2,697

## Key Observations
- Loss dropped rapidly in Epoch 1 (0.31 → 0.001), indicating BERT learns email patterns quickly
- The dataset has distinct language patterns per category (verification codes, spam language, social notifications), making this a relatively clean classification task
- Near-perfect accuracy suggests the 3-class mapping (High/Medium/Low) creates well-separated categories

## Files Created
- `model training + eval/test_bert.py` — Initial BERT loading test
- `model training + eval/train_bert.py` — Full training script
- `model training + eval/test_predictions.py` — Evaluation + inference script
- `bert_email_classifier/` — Saved model weights and tokenizer

## Next Steps
- Run detailed evaluation (classification report, confusion matrix, error analysis)
- Build a demo/API for live predictions
- Consider if the model generalizes to real-world emails outside this dataset
