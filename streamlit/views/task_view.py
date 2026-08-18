import pandas as pd
import streamlit as st

from data.loaders import load_metadata, load_opti, load_imu
from data.params import Params
from data.processing import process_trial, process_rms, SOURCES

st.set_page_config(page_title="Balance Analysis", layout="wide")
st.title("Balance Project — Task View")

all_participants = st.session_state.participants
all_trials = st.session_state.trials
all_tasks = all_trials.index.get_level_values("task").unique()
with st.sidebar:
    task = st.selectbox("Task", all_tasks)

trials = all_trials.xs(task, level="task")

trial_names = []
opti_aggregate_df = []
imu_aggregate_df = []
diff_aggregate_df = []

for trial in trials.reset_index().itertuples():
    print(trial)
    participant = all_participants[trial.participant]
    metadata = load_metadata(participant["path"])
    global_params = metadata.get("global", {})

    df_opti = load_opti(trial.opti_file)
    df_imu = load_imu(trial.imu_file)

    trial_params = Params.from_dict(metadata.get(f"{task} {trial.trial_num}", {}))
    result = process_trial(df_opti, df_imu, trial_params, global_params)
    rms_result = process_rms(result)

    trial_names.append(f"{task} {trial.trial_num} - {trial.participant}")
    opti_aggregate_df.append(rms_result["opti"])
    imu_aggregate_df.append(rms_result["imu"])
    diff_aggregate_df.append(rms_result["diff"])


opti_aggregate_df = pd.DataFrame(opti_aggregate_df, index=trial_names)
imu_aggregate_df = pd.DataFrame(imu_aggregate_df, index=trial_names)
diff_aggregate_df = pd.DataFrame(diff_aggregate_df, index=trial_names)

average_df = pd.DataFrame(
    {
        "Optitrack": opti_aggregate_df.mean(),
        "Airpods": imu_aggregate_df.mean(),
        "Absolute Difference": diff_aggregate_df.mean(),
    }
)

st.subheader("Overall mean RMS")
st.dataframe(average_df.T, width="stretch")

st.subheader("Optitrack RMS")
st.dataframe(opti_aggregate_df, width="stretch")
st.subheader("Airpods RMS")
st.dataframe(imu_aggregate_df, width="stretch")
st.subheader("Absolute Difference RMS")
st.dataframe(diff_aggregate_df, width="stretch")
