import pandas as pd

df = pd.read_csv('train.csv')

print(f"Total emails: {len(df)}")
print(f"\nColumns: {list(df.columns)}")
print(f"\nCategories:")
print(df['category'].value_counts())

for category in df['category'].unique():
    print(f"\n{'='*50}")
    print(f"CATEGORY: {category}")
    print('='*50)

    samples = df[df['category'] == category].head(3)
    for i, row in samples.iterrows():
        print(f"\n{row['text'][:150]}...")
