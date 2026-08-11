import pandas as pd
import streamlit as st
from pathlib import Path

from data.loaders import get_sessions, get_participants, load_opti, load_imu

DEFAULT_BASE_PATH = ""

trial_page = st.Page("views/aggregate_view.py", title="Aggregate View", default=True)
session_page = st.Page("views/session_view.py", title="Session View")

pg = st.navigation([trial_page, session_page])

with st.sidebar:
    st.header("Data source")
    base_path = st.text_input("Base data folder", value="")

    participant_list = get_participants(base_path)
    participants = {}

    trials = []
    for id in participant_list:
        participant_path = Path(base_path) / id
        sessions, unmatched = get_sessions(participant_path)

        participants[id] = {
            "trials": sessions,
            "unmatched": unmatched,
            "path": participant_path,
        }

        for session_id, (opti_file, imu_file) in sessions.items():
            df_opti_raw = load_opti(opti_file)
            df_imu_raw = load_imu(imu_file)

            trials.append(
                {
                    "participant": id,
                    "task": session_id.rsplit(" ", 1)[0],
                    "session_id": session_id,
                    "opti_file": opti_file,
                    "imu_file": imu_file,
                }
            )
    trials = pd.DataFrame(trials)


if not participants or trials.empty:
    st.error("No participants found in folder.")
    st.stop()

if not trials["session_id"].is_unique:
    st.error("Error: Duplicate session names found")
    st.dataframe(trials[trials["session_id"].duplicated(keep=False)], hide_index=True)
    st.stop()

trials.set_index("session_id", inplace=True)
st.session_state.trials = trials
st.session_state.participants = participants

pg.run()
