import plotly.express as px
import dash_mantine_components as dmc
from dash import dcc
from dash import Dash
import pandas as pd

from deadline_api.ConnectionProperty import ConnectionProperty
from deadline_api.Jobs import Jobs
from deadline_api.JobReports import JobReports
from deadline_api.DeadlineConnect import DeadlineCon

# Démarrer les WebService sur une machine avec la commande deadlinewebservice et utiliser la bonne IP
deadline_client = DeadlineCon("127.0.0.1", "8081")

def per_machine_time_fig(client):
    df = pd.DataFrame(client.Jobs.GetJobs())
    df["DateComp"] = pd.to_datetime(df["DateComp"], errors="coerce", format="ISO8601")

    df= df[~df["DateComp"].isna()]

    df["DateStart"] = pd.to_datetime(df["DateStart"], errors="coerce", format="ISO8601")
    df["duration"] = df["DateComp"] - df["DateStart"]
    df["duration"] = df["duration"].dt.total_seconds()
    fig = px.bar(
        df.groupby("Mach").agg({"duration": "mean"}).reset_index(),
        x="Mach",
        y="duration",
        labels={"Mach": "", "duration": "", "title":"Durée moyenne des jobs (secondes) par machine"},
        template="plotly_dark",
    )
    return fig

def timeline_fig(client):
    df = pd.DataFrame(client.Jobs.GetJobs())
    df["DateComp"] = pd.to_datetime(df["DateComp"], errors="coerce", format="ISO8601")

    df= df[~df["DateComp"].isna()]

    df["DateStart"] = pd.to_datetime(df["DateStart"], errors="coerce", format="ISO8601")
    df["duration"] = df["DateComp"] - df["DateStart"]
    df["duration"] = df["duration"].dt.total_seconds()
    fig = px.scatter(
       df,
        x="Date",
        y="duration",
        labels={"DateStart": "ts", "duration": "", "title":""},
        template="plotly_dark",
    )
    return fig

app = Dash()
dmc.add_figure_templates()

app.layout = dmc.MantineProvider(
    dmc.SimpleGrid(
    [
        dcc.Graph(figure=per_machine_time_fig(deadline_client)),
        dcc.Graph(figure=timeline_fig(deadline_client)),
    ],
    cols=2
)
)

if __name__ == "__main__":
    app.run(debug=True)