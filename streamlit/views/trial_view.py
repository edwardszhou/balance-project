import copy
import pandas as pd
import streamlit as st
from pprint import pprint

from components.plot import plot_axes
from data.loaders import (
    load_opti,
    load_imu,
    load_metadata,
    write_trial_params,
)
from data.processing import (
    process_trial,
    process_rms,
    TrialProcessingError,
    UNITS,
    SOURCES,
)
from data.params import Params, AXIS_OPTIONS
from data.helpers import auto_align

st.set_page_config(page_title="Balance Analysis", layout="wide")
st.title("Balance Project — Session View")

all_participants = st.session_state.participants
all_trials = st.session_state.trials

with st.sidebar:
    # Identify unique trial via combination of participant, task, and trial #
    col1, col2, col3 = st.columns(3)
    pid = col1.selectbox("Participant", all_participants)
    participant = all_participants[pid]
    path = participant["path"]

    trials = all_trials.loc[pid]
    trial_indexes = trials.index.map(lambda x: f"{x[0]} {x[1]}")
    trial_task = col2.selectbox("Task", trials.index.get_level_values("task").unique())
    trial_num = col3.selectbox(
        "Trial", trials.loc[trial_task].index.get_level_values("trial_num")
    )
    trial_id = f"{trial_task} {trial_num}"


if trial_task and trial_num:
    trial = trials.loc[(trial_task, trial_num)]
    has_opti = pd.notna(trial["opti_file"])
    df_opti_raw = load_opti(trial["opti_file"]) if has_opti else None
    df_imu_raw = load_imu(trial["imu_file"])

    # if exists, get saved filter / processing parameters. otherwise, use default
    metadata = load_metadata(path)
    trial_params = Params.from_dict(metadata.get(f"{trial_task} {trial_num}", {}))

    with st.sidebar:
        st.header("Graph Display")
        displayed_quantities = st.multiselect(
            "Quantities to display", UNITS, "velocity"
        )
        sources = SOURCES if has_opti else {"Airpods": "imu"}
        displayed_graphs = st.multiselect("Graphs to display", sources, sources)
        displayed_graphs = [sources[source] for source in displayed_graphs]

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
            col1, col2 = st.columns(2)
            trial_params.opti.lowpass.cutoff = col1.slider(
                "Optitrack lowpass cutoff (Hz)",
                5.0,
                20.0,
                trial_params.opti.lowpass.cutoff,
                0.5,
            )
            trial_params.opti.lowpass.order = col2.slider(
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
            col1, col2 = st.columns(2)
            trial_params.imu.lowpass.cutoff = col1.slider(
                "Airpods lowpass cutoff (Hz)",
                5.0,
                20.0,
                trial_params.imu.lowpass.cutoff,
                0.5,
            )
            trial_params.imu.lowpass.order = col2.slider(
                "Airpods lowpass order", 1, 4, trial_params.imu.lowpass.order
            )
        if trial_params.imu.highpass.active:
            col1, col2 = st.columns(2)
            trial_params.imu.highpass.cutoff = col1.slider(
                "Airpods highpass cutoff (Hz)",
                0.01,
                0.5,
                trial_params.imu.highpass.cutoff,
                0.01,
            )
            trial_params.imu.highpass.order = col2.slider(
                "Airpods highpass order", 1, 4, trial_params.imu.highpass.order
            )

        st.header("Time")
        col1, col2 = st.columns(2)
        trial_params.trim = col1.slider(
            "Trimmed seconds", 0.0, 5.0, trial_params.trim, 0.1
        )
        # Offset is a per-trial parameter -- device clocks drift between
        # trials, so each trial gets its own time offset.
        trial_params.offset = col2.slider(
            "Offset seconds", -3.0, 3.0, trial_params.offset, 0.01
        )

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

        st.header("Metadata Actions")
        col1, col2 = st.columns(2)
        if col1.button("Save parameters to trial", width="stretch"):
            write_trial_params(path, trial_id, trial_params)

        if col1.button("Save parameters to all trials of participant", width="stretch"):
            # propagate filters / trim / axes to every trial, but keep each
            # trial's own offset (offset is per-trial, not shared)
            for t in trial_indexes:
                params_t = copy.deepcopy(trial_params)
                params_t.offset = Params.from_dict(metadata.get(t, {})).offset
                write_trial_params(path, t, params_t)

        if col2.button("Reset trial parameters", width="stretch"):
            trial_params = Params()
            write_trial_params(path, trial_id, trial_params)
            st.rerun()

        if col2.button("Reset all trials of participant", width="stretch"):
            trial_params = Params()
            for t in trial_indexes:
                write_trial_params(path, t, trial_params)
            st.rerun()

        if has_opti and st.button("Auto align", width="stretch"):
            with st.spinner("Searching axis mappings and offset..."):
                try:
                    axes, offset, score = auto_align(
                        df_opti_raw, df_imu_raw, trial_params
                    )
                except ValueError as e:
                    st.warning(f"Can't auto-align {trial_id}: {e}")
                else:
                    trial_params.axes = list(axes)
                    trial_params.offset = offset
                    write_trial_params(path, trial_id, trial_params)
                    st.session_state["auto_align_result"] = {
                        "trial": trial_id,
                        "axes": list(axes),
                        "offset": offset,
                        "score": score,
                    }
                    st.rerun()

    aligned = st.session_state.pop("auto_align_result", None)
    if aligned and aligned["trial"] == trial_id:
        st.success(
            f"Auto-aligned {trial_id}: axes {aligned['axes']}, "
            f"offset {aligned['offset']:.3f}s "
            f"(velocity diff score {aligned['score']:.4f})"
        )

    try:
        result = process_trial(
            df_opti_raw, df_imu_raw, trial_params
        )
    except TrialProcessingError as e:
        st.warning(
            f"Trial {trial_task} {trial_num} can't be processed: {e}"
        )
        st.stop()
    for unit in displayed_quantities:
        st.subheader(f"{unit} — {trial_task} {trial_num}")
        st.plotly_chart(plot_axes(result, unit, displayed_graphs), width="stretch")

    st.subheader(f"RMS summary — {trial_task} {trial_num}")
    rms_result = process_rms(result)
    for label, source in sources.items():
        st.markdown(f"**{label}**")
        st.dataframe(rms_result[source].to_frame("RMS").T, width="stretch")

    with st.expander("Raw sample counts"):
        if has_opti:
            st.caption(f"Optitrack samples (post-trim): {len(result['opti'])}")
        st.caption(f"Airpods samples (post-trim): {len(result['imu'])}")

else:
    st.error(f"No trials found for participant {pid}.")

if participant["unmatched"]:
    with st.expander("Unmatched files"):
        st.caption("\n\n".join(participant["unmatched"]))

if participant.get("skipped"):
    with st.expander("Skipped trials (too short to process)"):
        st.caption("\n\n".join(participant["skipped"]))
