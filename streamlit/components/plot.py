import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data.processing import AXES, UNITS


def plot_axes(result: dict, quantity: str):
    time_min = min(result["opti"].index.min(), result["imu"].index.min())
    opti_time = result["opti"].index - time_min
    imu_time = result["imu"].index - time_min

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        subplot_titles=[f"{axis} {quantity}" for axis in AXES]
        + [f"{quantity} magnitude"],
    )
    for i, axis in enumerate(AXES):
        fig.add_trace(
            go.Scatter(
                x=opti_time,
                y=result["opti"][quantity][axis],
                name=f"Optitrack {axis}",
            ),
            row=i + 1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=imu_time,
                y=result["imu"][quantity][axis],
                name=f"Airpods {axis}",
            ),
            row=i + 1,
            col=1,
        )
    fig.add_trace(
        go.Scatter(
            x=opti_time,
            y=result["opti"][quantity]["magnitude"],
            name=f"Optitrack magnitude",
        ),
        row=4,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=imu_time,
            y=result["imu"][quantity]["magnitude"],
            name=f"Airpods magnitude",
        ),
        row=4,
        col=1,
    )

    for i in range(4):
        fig.update_xaxes(
            showticklabels=True,
            ticks="outside",
            showline=True,
            row=i + 1,
            col=1,
        )
        fig.update_yaxes(
            title_text=f"{quantity} ({UNITS[quantity]})",
            row=i + 1,
            col=1,
        )
    fig.update_layout(height=1080, showlegend=True, hovermode="x unified")

    return fig
