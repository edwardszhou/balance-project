import pandas as pd
import streamlit as st
from pathlib import Path

from data.loaders import (
    get_trials,
    get_participants,
    load_metadata,
)
from data.helpers import detect_skipped_trials

DEFAULT_BASE_PATH = ""

participant_page = st.Page(
    "views/participant_view.py", title="Participant View", default=True
)
task_page = st.Page("views/task_view.py", title="Task View")
session_page = st.Page("views/trial_view.py", title="Trial View")

pg = st.navigation([task_page, participant_page, session_page])

with st.sidebar:
    st.header("Data source")
    base_path = st.text_input("Base data folder", value="")

    participant_list = get_participants(base_path)
    participants = {}

    # Build overall dataframes for participants and trials
    #
    # Task: type of task recorded (i.e. STS)
    # Participant: participant ID
    # Trial Number: iteration of the task (1-3)
    # Trial: Combination of task, participant, and trial number
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

        # detect trials that can't be processed (short / non-overlapping)
        # so the UI can flag them; cached under "global" after first load
        metadata = load_metadata(participant_path)
        if not metadata.get("global"):
            participant_trials_df = pd.DataFrame(
                [t for t in participant_trials if t["opti_file"] is not None]
            )
            skipped = detect_skipped_trials(
                participant_trials_df, participant_path
            )
        else:
            skipped = metadata["global"].get("skipped", [])
        participants[pid]["skipped"] = skipped


all_trials = pd.DataFrame(all_trials)
if not participants or all_trials.empty:
    st.error("No participants found in folder.")
    st.stop()

all_trials.set_index(["participant", "task", "trial_num"], inplace=True)
# if not all_trials.index.is_unique:
#     st.error("Error: Duplicate trial names found")
#     st.dataframe(all_trials[all_trials.index.duplicated(keep=False)], hide_index=True)
#     st.stop()

st.session_state.trials = all_trials
st.session_state.participants = participants

pg.run()
