import pandas as pd
import os

output_dir = '/app/content-summarization/src/outputs'  # Output directory within the container

print('Creating test CSV...')
df = pd.DataFrame()
df['a'] = [1, 2, 3]

output_file = os.path.join(output_dir, 'file.csv')  # File path within the container
df.to_csv(output_file)
print('\tTest CSV saved to', output_file)
