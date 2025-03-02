import re
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# Read the log file
log_file = r'C:\Users\g.grapperon\Desktop\log2.txt'

# Patterns to capture timestamps and messages
timestamp_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}):\s+(.*)'

data = []

# Parse the log file
with open(log_file, 'r') as file:
    for line in file:
        match = re.search(timestamp_pattern, line)
        if match:
            timestamp_str = match.group(1)
            message = match.group(2)
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            data.append((timestamp, message))

# Convert to DataFrame
df = pd.DataFrame(data, columns=['Timestamp', 'Message'])

# Calculate execution durations
df['Duration'] = df['Timestamp'].diff().fillna(pd.Timedelta(seconds=0))

# Identify potential bottlenecks (e.g., steps taking more than a threshold)
threshold = pd.Timedelta(seconds=5)  # Example threshold
bottlenecks = df[df['Duration'] > threshold]

# Summarize execution statistics
summary = {
    'Total Steps': len(df),
    'Total Duration': df['Duration'].sum(),
    'Average Duration': df['Duration'].mean(),
    'Max Duration': df['Duration'].max(),
    'Min Duration': df['Duration'].min(),
    'Potential Bottlenecks': len(bottlenecks)
}

# Generate report
print('--- Execution Time Report ---')
print(df[['Timestamp', 'Message', 'Duration']])
print('\n--- Summary Statistics ---')
for key, value in summary.items():
    print(f'{key}: {value}')

print('\n--- Potential Bottlenecks ---')
print(bottlenecks[['Timestamp', 'Message', 'Duration']])

# Visualizations
plt.figure(figsize=(12, 6))
plt.plot(df['Timestamp'], df['Duration'].dt.total_seconds(), marker='o', label='Step Duration')
plt.axhline(y=threshold.total_seconds(), color='r', linestyle='--', label='Bottleneck Threshold')
plt.xlabel('Timestamp')
plt.ylabel('Duration (seconds)')
plt.title('Execution Time Analysis')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Highlight top 5 slowest steps
top_slowest = df.sort_values(by='Duration', ascending=False).head(5)
print('\n--- Top 5 Slowest Steps ---')
print(top_slowest[['Timestamp', 'Message', 'Duration']])

# Duration distribution analysis
plt.figure(figsize=(10, 6))
plt.hist(df['Duration'].dt.total_seconds(), bins=20, color='skyblue', edgecolor='black')
plt.axvline(df['Duration'].mean().total_seconds(), color='red', linestyle='dashed', linewidth=1, label='Average Duration')
plt.xlabel('Duration (seconds)')
plt.ylabel('Frequency')
plt.title('Distribution of Execution Times')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
