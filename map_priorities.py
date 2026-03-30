import pandas as pd

# Our mapping rules
MAPPING = {
    'verify_code': 'High',
    'updates': 'High',
    'social_media': 'Medium',
    'forum': 'Medium',
    'promotions': 'Low',
    'spam': 'Low'
}

print("Loading data...")
train = pd.read_csv('train.csv')
test = pd.read_csv('test.csv')

print("Applying mapping...")
train['priority'] = train['category'].map(MAPPING)
test['priority'] = test['category'].map(MAPPING)

print("\nDistribution:")
print(train['priority'].value_counts())

train.to_csv('train_3class.csv', index=False)
test.to_csv('test_3class.csv', index=False)

print("\n✓ Done! New files created.")
