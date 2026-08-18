import pandas as pd
import streamlit as st

from data.loaders import load_metadata, load_opti, load_imu
from data.params import Params
from data.processing import process_trial, process_rms, SOURCES

st.set_page_config(page_title="Balance Analysis", layout="wide")
st.title("Balance Project — Aggregate View")

all_participants = st.session_state.participants
all_trials = st.session_state.trials

with st.sidebar:
    pid = st.selectbox("Participant", all_participants)

participant = all_participants[pid]
path = participant["path"]
trials = all_trials.loc[pid]

metadata = load_metadata(path)
global_params = metadata.get("global", {})

trial_names = []
opti_aggregate_df = []
imu_aggregate_df = []
error_aggregate_df = []

for trial in trials.reset_index().itertuples():
    df_opti = load_opti(trial.opti_file)
    df_imu = load_imu(trial.imu_file)

    trial_params = Params.from_dict(metadata.get(f"{trial.task} {trial.trial_num}", {}))
    result = process_trial(df_opti, df_imu, trial_params, global_params)
    rms_result = process_rms(result)

    trial_names.append(f"{trial.task} {trial.trial_num}")
    opti_aggregate_df.append(rms_result["opti"])
    imu_aggregate_df.append(rms_result["imu"])
    error_aggregate_df.append(rms_result["error"])


opti_aggregate_df = pd.DataFrame(opti_aggregate_df, index=trial_names)
imu_aggregate_df = pd.DataFrame(imu_aggregate_df, index=trial_names)
error_aggregate_df = pd.DataFrame(error_aggregate_df, index=trial_names)

average_df = pd.DataFrame(
    {
        "Optitrack": opti_aggregate_df.mean(),
        "Airpods": imu_aggregate_df.mean(),
        "Error": error_aggregate_df.mean(),
    }
)

st.subheader("Overall mean RMS")
st.dataframe(average_df.T, width="stretch")

st.subheader("Optitrack RMS")
st.dataframe(opti_aggregate_df, width="stretch")
st.subheader("Airpods RMS")
st.dataframe(imu_aggregate_df, width="stretch")
st.subheader("Absolute Error RMS")
st.dataframe(error_aggregate_df, width="stretch")
