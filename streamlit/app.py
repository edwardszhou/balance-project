import streamlit as st
from plot import plot_axes
from pathlib import Path

from data.loaders import get_sessions, get_participants, load_opti, load_imu
from data.processing import process_trial, process_rms

DEFAULT_BASE_PATH = ""
AXES = ["x", "y", "z"]

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

    sessions = get_sessions(participant_path)
    session = st.selectbox("Session", sessions.keys())

    st.header("Filter parameters")
    filter_opti = st.checkbox("Apply filter to Optitrack", value=True)
    filter_imu = st.checkbox("Apply filter to Airpods", value=True)

    lp_cutoff = st.slider("Optitrack lowpass cutoff (Hz)", 5.0, 20.0, 10.0, 0.5)
    lp_order = st.slider("Optitrack lowpass order", 1, 4, 4)
    bp_low = st.slider("Airpods highpass cutoff (Hz)", 0.01, 0.5, 0.1, 0.01)
    bp_high = st.slider("Airpods lowpass cutoff (Hz)", 5.0, 20.0, 10.0, 0.5)
    bp_order = st.slider("Airpods bandpass order", 1, 4, 4)

    st.header("Time")
    time_trim = st.slider("Trimmed seconds", 0.0, 5.0, 3.0, 0.1)
    time_offset = st.slider("Offset seconds", -3.0, 3.0, 0.0, 0.1)

    st.header("Flip axes")
    axes_to_flip = st.multiselect("Negate axes", AXES)

    show_accel = st.checkbox("Also show acceleration comparison", value=False)

df_opti_raw = load_opti(participant_path, sessions[session][0])
df_imu_raw = load_imu(participant_path, sessions[session][1])

try:
    result = process_trial(
        df_opti_raw,
        df_imu_raw,
        lp_cutoff=lp_cutoff,
        bp_cutoff=(bp_low, bp_high),
        lp_order=lp_order,
        bp_order=bp_order,
        time_trim=time_trim,
        time_offset=time_offset,
        filter_opti=filter_opti,
        filter_imu=filter_imu,
        flip_axes=axes_to_flip,
    )
except ValueError as e:
    # st.error(str(e))
    st.stop()


st.subheader(f"Velocity — {session}")
st.plotly_chart(plot_axes(result, "velocity"), width="stretch")

if show_accel:
    st.subheader(f"Acceleration — {session}")
    st.plotly_chart(plot_axes(result, "acceleration"), width="stretch")

st.subheader(f"RMS summary — {session}")
st.dataframe(process_rms(result), width="stretch", hide_index=True)


with st.expander("Raw sample counts"):
    st.write(f"Optitrack samples (post-trim): {len(result['opti']['time'])}")
    st.write(f"Airpods samples (post-trim): {len(result['imu']['time'])}")
