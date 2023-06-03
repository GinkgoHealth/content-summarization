import pandas as pd

print('Creating test CSV...')
df = pd.DataFrame()
df['a'] = [1, 2, 3]

df.to_csv('file')
print('\tTest CSV saved')