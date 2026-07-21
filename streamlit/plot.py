import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE_AXES = ["x", "y", "z"]
UNITS = {
    "velocity": "m/s",
    "acceleration": "m/s^2",
}


def plot_axes(result: dict, quantity: str, axes_match: list[tuple[int, int]]):
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        subplot_titles=[f"{axis} {quantity}" for axis in BASE_AXES],
    )
    for i, (axis_idx, factor) in enumerate(axes_match):
        imu_axis = BASE_AXES[i]
        opti_axis = BASE_AXES[axis_idx]
        fig.add_trace(
            go.Scatter(
                x=result["opti"]["time"],
                y=result["opti"][quantity][opti_axis] * factor,
                name=f"Optitrack {imu_axis}",
            ),
            row=i + 1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=result["imu"]["time"],
                y=result["imu"][quantity][imu_axis],
                name=f"AirPods {imu_axis}",
            ),
            row=i + 1,
            col=1,
        )
        fig.update_xaxes(
            title_text="time (s)",
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
