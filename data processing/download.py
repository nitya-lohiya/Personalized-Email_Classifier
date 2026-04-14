from datasets import load_dataset
import pandas as pd

print("Downloading emails...")
dataset = load_dataset("jason23322/high-accuracy-email-classifier")

train = pd.DataFrame(dataset['train'])
test = pd.DataFrame(dataset['test'])

train.to_csv('train.csv', index=False)
test.to_csv('test.csv', index=False)

print(f"Got {len(train)} training emails!")
print(f"Got {len(test)} test emails!")
