# Email Priority Classifier

A BERT-based machine learning model that classifies emails into three priority levels: **High**, **Medium**, and **Low**.

## Priority Levels

| Priority | Categories | Description |
|----------|-----------|-------------|
| High | Verification codes, account updates | Time-sensitive, requires immediate action |
| Medium | Social media, forum notifications | Important but can wait |
| Low | Promotions, spam | Can ignore or delete |

## Results

- **Test Accuracy: 99.70%** on 2,697 emails
- Trained on 10,780 emails from the [HuggingFace email dataset](https://huggingface.co/datasets/jason23322/high-accuracy-email-classifier)

## Project Structure

```
email-classifier/
├── download.py              # Download dataset from HuggingFace
├── explore.py               # Explore raw data categories
├── map_priorities.py        # Map 6 categories → 3 priorities
├── check_mapping.py         # Verify mapping with examples
├── analyze.py               # Data statistics and distribution chart
├── train.csv                # Raw training data (10,780 emails)
├── test.csv                 # Raw test data (2,697 emails)
├── train_3class.csv         # Training data with priority labels
├── test_3class.csv          # Test data with priority labels
├── distribution.png         # Priority distribution chart
├── WEEK1_REPORT.md          # Week 1: Data preparation report
├── WEEK2_REPORT.md          # Week 2: Training & evaluation report
├── model training + eval/
│   ├── test_bert.py         # BERT loading test
│   ├── train_bert.py        # Model training script
│   └── test_predictions.py  # Evaluation & inference script
└── bert_email_classifier/   # Saved fine-tuned model
    ├── config.json
    ├── model.safetensors
    ├── tokenizer.json
    └── tokenizer_config.json
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install pandas torch transformers scikit-learn matplotlib
```

## Usage

### 1. Prepare Data
```bash
python download.py
python map_priorities.py
```

### 2. Train Model
```bash
python "model training + eval/train_bert.py"
```

### 3. Test Model
```bash
python "model training + eval/test_predictions.py"
```

## Tech Stack
- Python 3.13
- PyTorch (MPS/CUDA/CPU)
- HuggingFace Transformers (BERT)
- Pandas, scikit-learn, Matplotlib
