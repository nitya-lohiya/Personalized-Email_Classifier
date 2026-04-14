from transformers import BertTokenizer, BertForSequenceClassification

print("Loading BERT")
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=3 )

print("✓ BERT loaded successfully!")
print(f"Model has {model.num_parameters()} parameters")

# Test tokenization
sample_email = "Your verification code is 123456"
tokens = tokenizer.tokenize(sample_email)
print(f"\nSample email: {sample_email}")
print(f"BERT sees it as: {tokens}")