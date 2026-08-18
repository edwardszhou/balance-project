import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data.processing import AXES, UNITS

COLORS = {
    "opti": "#2391FF",
    "imu": "#FF6A00",
    "diff": "#ADADAD",
}


def plot_axes(result: dict, quantity: str, sources: list):
    time_min = min([result[s].index.min() for s in sources])
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        subplot_titles=[f"{axis} {quantity}" for axis in AXES],
    )
    for i, axis in enumerate(AXES):
        for source in sources:
            fig.add_trace(
                go.Scatter(
                    x=result[source].index - time_min,
                    y=result[source][quantity][axis],
                    name=f"{source} {axis}",
                    line=dict(color=COLORS[source], width=2),
                ),
                row=i + 1,
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
