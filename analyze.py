import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('train_3class.csv')

print("="*50)
print("DATA STATISTICS")
print("="*50)

# Email lengths
df['length'] = df['text'].str.len()
print(f"\nAverage length: {df['length'].mean():.0f} characters")
print(f"Shortest: {df['length'].min()}")
print(f"Longest: {df['length'].max()}")

# Priority distribution
print("\nPriority counts:")
print(df['priority'].value_counts())

# Create chart
df['priority'].value_counts().plot(kind='bar', color=['red', 'yellow', 'green'])
plt.title('Email Distribution by Priority')
plt.savefig('distribution.png')
print("\n✓ Chart saved!")
