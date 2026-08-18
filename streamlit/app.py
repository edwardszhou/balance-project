import pandas as pd
import streamlit as st
from pathlib import Path

from data.loaders import (
    get_trials,
    get_participants,
    load_metadata,
)
from data.helpers import calculate_median_lag

DEFAULT_BASE_PATH = ""

aggregate_page = st.Page(
    "views/aggregate_view.py", title="Aggregate View", default=True
)
session_page = st.Page("views/session_view.py", title="Session View")

pg = st.navigation([aggregate_page, session_page])

with st.sidebar:
    st.header("Data source")
    base_path = st.text_input("Base data folder", value="")

    participant_list = get_participants(base_path)
    participants = {}

    all_trials = []
    for pid in participant_list:
        participant_path = Path(base_path) / pid
        trials, unmatched = get_trials(participant_path)
        participants[pid] = {
            "trials": trials,
            "unmatched": unmatched,
            "path": participant_path,
        }
        participant_trials = [
            {
                "participant": pid,
                "task": trial_key[0],
                "trial_num": trial_key[1],
                "opti_file": opti_file,
                "imu_file": imu_file,
            }
            for trial_key, (opti_file, imu_file) in trials.items()
        ]
        all_trials.extend(participant_trials)
        # if no precomputed cc lag, calculate
        metadata = load_metadata(participant_path)
        if not metadata.get("global"):
            participant_trials_df = pd.DataFrame(participant_trials)
            lag = calculate_median_lag(participant_trials_df, participant_path)


all_trials = pd.DataFrame(all_trials)
if not participants or all_trials.empty:
    st.error("No participants found in folder.")
    st.stop()

all_trials.set_index(["participant", "task", "trial_num"], inplace=True)
if not all_trials.index.is_unique:
    st.error("Error: Duplicate trial names found")
    st.dataframe(all_trials[all_trials.index.duplicated(keep=False)], hide_index=True)
    st.stop()

st.session_state.trials = all_trials
st.session_state.participants = participants

pg.run()
