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
from data.defaults import AXIS_OPTIONS, DEFAULT_PARAMS

st.set_page_config(page_title="Balance Session Analysis", layout="wide")
st.title("Balance Project — Session View")

participants = st.session_state.participants
trials = st.session_state.trials

with st.sidebar:
    pid = st.selectbox("Participants", participants)
    participant = participants[pid]
    session = st.selectbox("Session", participant["trials"])

if session:
    trial = trials.loc[session]

    df_opti_raw = load_opti(trial["opti_file"])
    df_imu_raw = load_imu(trial["imu_file"])

    with st.sidebar:
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
                st.slider(
                    "Optitrack lowpass cutoff (Hz)",
                    5.0,
                    20.0,
                    DEFAULT_PARAMS.opti.lp_cutoff,
                    0.5,
                ),
                st.slider(
                    "Optitrack lowpass order", 1, DEFAULT_PARAMS.opti.lp_order, 4
                ),
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
                st.slider(
                    "Airpods lowpass cutoff (Hz)",
                    5.0,
                    20.0,
                    DEFAULT_PARAMS.imu.lp_cutoff,
                    0.5,
                ),
                st.slider("Airpods lowpass order", 1, DEFAULT_PARAMS.imu.lp_order, 4),
            )
        if AIRPODS_FILTERS[2] in filters_imu:
            filters_imu[AIRPODS_FILTERS[2]] = (
                st.slider(
                    "Airpods highpass cutoff (Hz)",
                    0.01,
                    0.5,
                    DEFAULT_PARAMS.imu.hp_cutoff,
                    0.01,
                ),
                st.slider("Airpods highpass order", 1, DEFAULT_PARAMS.imu.hp_order, 4),
            )

        st.header("Time")
        time_trim = st.slider("Trimmed seconds", 0.0, 5.0, DEFAULT_PARAMS.trim, 0.1)

        result = process_trial(
            df_opti_raw,
            df_imu_raw,
            filters_opti=filters_opti,
            filters_imu=filters_imu,
            time_trim=time_trim,
        )

        lag = process_ccf(result)

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
    st.error(f"No sessions found for participant {pid}.")

if participant["unmatched"]:
    with st.expander("Unmatched files"):
        st.caption("\n\n".join(participant["unmatched"]))
