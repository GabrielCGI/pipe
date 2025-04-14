import sys
import re
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

def interactive_plot(df, threshold):
    fig, ax = plt.subplots(figsize=(12, 6))

    # Scatter plot of durations
    sc = ax.scatter(df['Timestamp'], df['Duration'].dt.total_seconds(), c='blue', label='Step Duration')
    ax.axhline(y=threshold.total_seconds(), linestyle='--', color='red', label='Bottleneck Threshold')

    # Add task separators where "Saved Image:" appears
    for idx, row in df.iterrows():
        if 'Saved Image:' in row['Message']:
            ax.axvline(x=row['Timestamp'], color='gray', linestyle=':', linewidth=1)
            ax.text(row['Timestamp'], ax.get_ylim()[1]*0.95, 'Saved Image', rotation=90,
                    verticalalignment='top', horizontalalignment='right', fontsize=8, color='gray')

    # Set labels and title
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Duration (seconds)')
    ax.set_title('Execution Time Analysis')
    ax.legend()
    ax.grid(True)

    # Annotation for hover
    annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                        bbox=dict(boxstyle="round", fc="w"),
                        arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)

    # Prepare data
    durations = df['Duration'].dt.total_seconds()
    messages = df['Message']
    timestamps = df['Timestamp']

    def update_annot(ind):
        idx = ind["ind"][0]
        annot.xy = (timestamps.iloc[idx], durations.iloc[idx])
        text = f"{timestamps.iloc[idx]}\n{messages.iloc[idx]}\n{durations.iloc[idx]:.2f}s"
        annot.set_text(text)
        annot.get_bbox_patch().set_alpha(0.9)

    def hover(event):
        vis = annot.get_visible()
        if event.inaxes == ax:
            cont, ind = sc.contains(event)
            if cont:
                update_annot(ind)
                annot.set_visible(True)
                fig.canvas.draw_idle()
            else:
                if vis:
                    annot.set_visible(False)
                    fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", hover)
    plt.tight_layout()
    plt.show()

def main(log_file):
    timestamp_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}):\s+(.*)'

    data = []

    with open(log_file, 'r') as file:
        for line in file:
            match = re.search(timestamp_pattern, line)
            if match:
                timestamp_str = match.group(1)
                message = match.group(2)
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                data.append((timestamp, message))

    if not data:
        print(f'No valid data found in log: {log_file}')
        return

    df = pd.DataFrame(data, columns=['Timestamp', 'Message'])
    df['Duration'] = df['Timestamp'].diff().fillna(pd.Timedelta(seconds=0))

    threshold = pd.Timedelta(seconds=5)
    bottlenecks = df[df['Duration'] > threshold]

    sum_duration = df['Duration'].sum()
    mean_duration = df['Duration'].mean()
    max_duration = df['Duration'].max()
    min_duration = df['Duration'].min()

    summary = {
        'Total Steps': len(df),
        'Total Duration': sum_duration,
        'Average Duration': mean_duration,
        'Max Duration': max_duration,
        'Min Duration': min_duration,
        'Potential Bottlenecks': len(bottlenecks)
    }

    print('--- Execution Time Report ---')
    print(df[['Timestamp', 'Message', 'Duration']])
    print('\n--- Summary Statistics ---')
    for key, value in summary.items():
        print(f'{key}: {value}')
    
    print('\n--- Potential Bottlenecks ---')
    print(bottlenecks[['Timestamp', 'Message', 'Duration']])

    interactive_plot(df, threshold)

    top_slowest = df.sort_values(by='Duration', ascending=False).head(5)
    print('\n--- Top 5 Slowest Steps ---')
    print(top_slowest[['Timestamp', 'Message', 'Duration']])

    # Histogram of durations
    plt.figure(figsize=(10, 6))
    plt.hist(df['Duration'].dt.total_seconds(), bins=20, edgecolor='black')
    plt.axvline(df['Duration'].mean().total_seconds(), color='red', linestyle='dashed', linewidth=1, label='Average Duration')
    plt.xlabel('Duration (seconds)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Execution Times')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = r'C:\Users\g.grapperon\Desktop\log2.txt'

    main(log_file)
