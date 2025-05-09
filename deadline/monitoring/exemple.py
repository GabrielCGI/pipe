import os
import glob
import sys

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def main(log_file: str, threshold: pd.Timedelta):
    """
    Parameters
    ----------
    log_gile: str
        File path
    """
    with open(log_file) as f:
        data = f.readlines()
        df = pd.DataFrame(data, columns=["data"])

    # 2025-04-10 09:04:11 -> 19 caractères
    # 2025-04-10 09:04:11:  0: STDOUT: -> 32 caractères
    df["ts"] = pd.to_datetime(df["data"].str[:19], errors="coerce", format="%Y-%m-%d %H:%M:%S")
    df = df[~df["ts"].isna()]
    df["data"] = df["data"].str[32:]
    df = df.groupby("ts").sum().reset_index()

    df['duration'] = df['ts'].diff().fillna(pd.Timedelta(seconds=0)).dt.total_seconds()

    # Distribution
    fig = px.histogram(df, x="duration", labels={"duration": "Duration (s)"}, title="Distribution of Execution Times")
    fig.add_hline(df["duration"].mean(), line_width=3, line_dash="dot", line_color="red")
    fig.update_layout(
        yaxis=dict(title=dict(text="Total occurences"))
    )
    fig.show()

    # Scatter
    df["legend"] = "blue"
    df.loc[df["data"].str.contains("Saved Image"), "legend"] = "red"
    scatter = px.scatter(
        df, 
        x="ts", 
        y="duration",
        hover_data="data",
        color="legend",
        labels={"duration": "Duration (s)", "title": "Execution Time Analysis"}
        )
    scatter.add_hline(
        threshold.total_seconds(),
        line_width=3,
        line_dash="dot",
        line_color="red",
        annotation_text="'Bottleneck Threshold", 
        annotation_position="bottom right",
        )

    scatter.show()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = r'C:\Users\g.grapperon\Desktop\log2.txt'

    main(log_file)