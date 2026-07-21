import plotly.graph_objects as go
from plotly.subplots import make_subplots

AXES = ["x", "y", "z"]
UNITS = {
    "velocity": "m/s",
    "acceleration": "m/s^2",
}


def plot_axes(result, quantity):
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        subplot_titles=[f"{axis} {quantity}" for axis in AXES],
    )
    for i, axis in enumerate(AXES, start=1):
        fig.add_trace(
            go.Scatter(
                x=result["opti"]["time"],
                y=result["opti"][quantity][axis],
                name=f"Optitrack {axis}",
            ),
            row=i,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=result["imu"]["time"],
                y=result["imu"][quantity][axis],
                name=f"AirPods {axis}",
            ),
            row=i,
            col=1,
        )
        fig.update_xaxes(
            title_text="time (s)",
            showticklabels=True,
            ticks="outside",
            showline=True,
            row=i,
            col=1,
        )
        fig.update_yaxes(
            title_text=f"{quantity} ({UNITS[quantity]})",
            row=i,
            col=1,
        )
    fig.update_layout(height=1080, showlegend=True, hovermode="x unified")

    return fig
