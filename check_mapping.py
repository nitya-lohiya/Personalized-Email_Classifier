import pandas as pd

df = pd.read_csv('train_3class.csv')

for priority in ['High', 'Medium', 'Low']:
    print(f"\n{'='*50}")
    print(f"{priority} PRIORITY EXAMPLES")
    print('='*50)

    samples = df[df['priority'] == priority].head(3)
    for i, row in samples.iterrows():
        print(f"\nOriginal category: {row['category']}")
        print(f"Text: {row['text'][:100]}...")
