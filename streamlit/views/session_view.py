import streamlit as st
from components.plot import plot_axes
from pathlib import Path

from data.loaders import get_sessions, get_participants, load_opti, load_imu
from data.processing import (
    process_trial,
    process_rms,
    process_ccf,
    UNITS,
    OPTI_FILTERS,
    AIRPODS_FILTERS,
)

DEFAULT_BASE_PATH = ""
AXIS_OPTIONS = {
    "+X": (0, 1),
    "+Y": (1, 1),
    "+Z": (2, 1),
    "-X": (0, -1),
    "-Y": (1, -1),
    "-Z": (2, -1),
}

st.set_page_config(page_title="Balance Session Analysis", layout="wide")
st.title("Balance Project — Session View")

with st.sidebar:
    st.header("Data source")
    base_path = st.text_input("Base data folder", value=DEFAULT_BASE_PATH)
    participants = get_participants(base_path)

if not participants:
    st.error("No participants found in folder.")
    st.stop()

with st.sidebar:
    participant = st.selectbox("Participants", participants)
    participant_path = Path(base_path) / participant

    sessions, unmatched = get_sessions(participant_path)
    session = st.selectbox("Session", sessions.keys())

    st.header("Graph Display")
    displayed_graphs = st.multiselect("Graphs to display", UNITS, "velocity")

    st.header("Filter parameters")
    filters_opti = st.pills(
        "Optitrack filters",
        OPTI_FILTERS,
        selection_mode="multi",
        default=OPTI_FILTERS,
    )
    filters_opti = {f: None for f in filters_opti}
    if OPTI_FILTERS[0] in filters_opti:
        filters_opti[OPTI_FILTERS[0]] = (
            st.slider("Optitrack lowpass cutoff (Hz)", 5.0, 20.0, 10.0, 0.5),
            st.slider("Optitrack lowpass order", 1, 4, 4),
        )

    filters_imu = st.pills(
        "Airpods filters",
        AIRPODS_FILTERS,
        selection_mode="multi",
        default=AIRPODS_FILTERS,
    )
    filters_imu = {f: None for f in filters_imu}
    if AIRPODS_FILTERS[1] in filters_imu:
        filters_imu[AIRPODS_FILTERS[1]] = (
            st.slider("Airpods lowpass cutoff (Hz)", 5.0, 20.0, 10.0, 0.5),
            st.slider("Airpods lowpass order", 1, 4, 4),
        )
    if AIRPODS_FILTERS[2] in filters_imu:
        filters_imu[AIRPODS_FILTERS[2]] = (
            st.slider("Airpods highpass cutoff (Hz)", 0.01, 0.5, 0.1, 0.01),
            st.slider("Airpods highpass order", 1, 4, 4),
        )

    st.header("Time")
    time_trim = st.slider("Trimmed seconds", 0.0, 5.0, 1.5, 0.1)

if session:
    df_opti_raw = load_opti(participant_path, sessions[session][0])
    df_imu_raw = load_imu(participant_path, sessions[session][1])

    result = process_trial(
        df_opti_raw,
        df_imu_raw,
        filters_opti=filters_opti,
        filters_imu=filters_imu,
        time_trim=time_trim,
    )

    lag = process_ccf(result)

    with st.sidebar:
        time_offset = st.slider("Offset seconds", -3.0, 3.0, lag, 0.05)

        st.header("Manipulate axes")
        st.caption("Change optitrack axes to match airpods")
        axes_match = (
            st.pills("Airpods X", AXIS_OPTIONS, default="+X", required=True),
            st.pills("Airpods Y", AXIS_OPTIONS, default="+Y", required=True),
            st.pills("Airpods Z", AXIS_OPTIONS, default="+Z", required=True),
        )
        axes_match = [AXIS_OPTIONS[option] for option in axes_match]

    for unit in displayed_graphs:
        st.subheader(f"{unit} — {session}")
        st.plotly_chart(
            plot_axes(result, unit, time_offset, axes_match), width="stretch"
        )

    st.subheader(f"RMS summary — {session}")
    st.dataframe(process_rms(result), width="stretch", hide_index=True)

    with st.expander("Raw sample counts"):
        st.caption(f"Optitrack samples (post-trim): {len(result['opti']['time'])}")
        st.caption(f"Airpods samples (post-trim): {len(result['imu']['time'])}")

else:
    st.error(f"No sessions found for participant {participant}.")

if unmatched:
    with st.expander("Unmatched files"):
        st.caption("\n\n".join(unmatched))
