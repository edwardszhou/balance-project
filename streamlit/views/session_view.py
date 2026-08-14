import streamlit as st
from pprint import pprint

from components.plot import plot_axes
from data.loaders import (
    load_opti,
    load_imu,
    load_metadata,
    write_trial_params,
    write_global_params,
)
from data.processing import (
    process_trial,
    process_rms,
    process_ccf,
    UNITS,
)
from data.params import (
    Params,
    AXIS_OPTIONS,
)

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

    metadata = load_metadata(participant["path"])
    global_params = metadata.get("global", {})
    trial_params = Params.from_dict(metadata.get(trial["task"], {}))

    with st.sidebar:
        st.header("Graph Display")
        displayed_graphs = st.multiselect("Graphs to display", UNITS, "velocity")

        st.header("Filter parameters")

        filters_opti = trial_params.opti.label_fields()
        active_opti = st.pills(
            "Optitrack filters",
            filters_opti,
            selection_mode="multi",
            default=trial_params.opti.active_labels(),
        )
        for label in filters_opti:
            trial_params.opti[label].active = label in active_opti

        if trial_params.opti.lowpass.active:
            trial_params.opti.lowpass.cutoff = st.slider(
                "Optitrack lowpass cutoff (Hz)",
                5.0,
                20.0,
                trial_params.opti.lowpass.cutoff,
                0.5,
            )
            trial_params.opti.lowpass.order = st.slider(
                "Optitrack lowpass order", 1, 4, trial_params.opti.lowpass.order
            )

        filters_imu = trial_params.imu.label_fields()
        active_imu = st.pills(
            "Airpods filters",
            filters_imu,
            selection_mode="multi",
            default=trial_params.imu.active_labels(),
        )
        for label in filters_imu:
            trial_params.imu[label].active = label in active_imu

        if trial_params.imu.lowpass.active:
            trial_params.imu.lowpass.cutoff = st.slider(
                "Airpods lowpass cutoff (Hz)",
                5.0,
                20.0,
                trial_params.imu.lowpass.cutoff,
                0.5,
            )
            trial_params.imu.lowpass.order = st.slider(
                "Airpods lowpass order", 1, 4, trial_params.imu.lowpass.order
            )
        if trial_params.imu.highpass.active:
            trial_params.imu.highpass.cutoff = st.slider(
                "Airpods highpass cutoff (Hz)",
                0.01,
                0.5,
                trial_params.imu.highpass.cutoff,
                0.01,
            )
            trial_params.imu.highpass.order = st.slider(
                "Airpods highpass order", 1, 4, trial_params.imu.highpass.order
            )

        st.header("Time")
        trial_params.trim = st.slider(
            "Trimmed seconds", 0.0, 5.0, trial_params.trim, 0.1
        )

        result = process_trial(df_opti_raw, df_imu_raw, trial_params)

        offset = global_params.get("offset", 0)
        global_params["offset"] = st.slider("Offset seconds", -3.0, 3.0, offset, 0.01)

        st.header("Manipulate axes")
        st.caption("Change optitrack axes to match airpods")
        trial_params.axes = (
            st.pills(
                "Airpods X", AXIS_OPTIONS, default=trial_params.axes[0], required=True
            ),
            st.pills(
                "Airpods Y", AXIS_OPTIONS, default=trial_params.axes[1], required=True
            ),
            st.pills(
                "Airpods Z", AXIS_OPTIONS, default=trial_params.axes[2], required=True
            ),
        )

        st.header("Save metadata")
        if st.button("Save parameters to trial"):
            write_trial_params(participant["path"], trial["task"], trial_params)
            write_global_params(participant["path"], global_params)

        if st.button("Save parameters to all trials of participant"):
            for t in participant["trials"]:
                trial = trials.loc[t]
                write_trial_params(participant["path"], trial["task"], trial_params)
                write_global_params(participant["path"], global_params)

        if st.button("Reset parameters"):
            pprint("Resetting")

    for unit in displayed_graphs:
        st.subheader(f"{unit} — {session}")
        st.plotly_chart(
            plot_axes(result, unit, global_params["offset"], trial_params),
            width="stretch",
        )

    st.subheader(f"RMS summary — {session}")
    st.dataframe(process_rms(result), width="stretch", hide_index=True)

    with st.expander("Raw sample counts"):
        st.caption(f"Optitrack samples (post-trim): {len(result['opti'])}")
        st.caption(f"Airpods samples (post-trim): {len(result['imu'])}")

else:
    st.error(f"No sessions found for participant {pid}.")

if participant["unmatched"]:
    with st.expander("Unmatched files"):
        st.caption("\n\n".join(participant["unmatched"]))
