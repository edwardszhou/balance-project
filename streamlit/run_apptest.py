"""Integration smoke test: runs the real app.py through Streamlit's
AppTest harness (actual script execution, actual widget/component
registration) with data.loaders monkeypatched to return small synthetic
in-memory data instead of parsing real session CSVs, since we don't have a
real data folder here. This exercises the *actual* app.py + live_plot.py +
the declared custom component wiring, not a reimplementation of it.
"""

import sys
import numpy as np
import pandas as pd

sys.path.insert(0, ".")

import data.loaders as loaders  # noqa: E402

# ---- monkeypatch the data-loading layer with synthetic in-memory data ----


def fake_get_participants(base_path):
    return ["P01"]


def fake_get_sessions(participant_path):
    return {"session1": ("opti.csv", "imu.csv")}, []


def fake_load_opti(base_path, session):
    n = 1500
    fs = 120.0
    t = np.arange(n) / fs + 1000.0
    rng = np.random.default_rng(1)
    return pd.DataFrame(
        {
            "timestamp": t,
            "px": 0.05 * np.sin(2 * np.pi * 0.7 * (t - 1000)) + 0.001 * rng.standard_normal(n),
            "py": 0.03 * np.sin(2 * np.pi * 0.5 * (t - 1000)) + 0.001 * rng.standard_normal(n),
            "pz": 0.04 * np.cos(2 * np.pi * 0.6 * (t - 1000)) + 0.001 * rng.standard_normal(n),
        }
    )


def fake_load_imu(base_path, session):
    m = 1200
    fs = 100.0
    t = np.arange(m) / fs + 1000.05
    rng = np.random.default_rng(2)
    return pd.DataFrame(
        {
            "timestampEpoch": t,
            "ax": 0.5 * np.sin(2 * np.pi * 2.0 * (t - 1000)) + 0.05 * rng.standard_normal(m),
            "ay": 0.4 * np.sin(2 * np.pi * 1.5 * (t - 1000)) + 0.05 * rng.standard_normal(m),
            "az": 0.3 * np.cos(2 * np.pi * 1.8 * (t - 1000)) + 0.05 * rng.standard_normal(m),
        }
    )


loaders.get_participants = fake_get_participants
loaders.get_sessions = fake_get_sessions
loaders.load_opti = fake_load_opti
loaders.load_imu = fake_load_imu

from streamlit.testing.v1 import AppTest  # noqa: E402

at = AppTest.from_file("app.py")
at.run(timeout=30)

print("=== exceptions ===")
for e in at.exception:
    print(e)

print("=== sidebar selectbox/slider count ===", len(at.sidebar.selectbox), len(at.sidebar.slider))
print("=== main dataframes ===", len(at.dataframe))
if at.dataframe:
    print(at.dataframe[0].value)

print("=== errors on page ===")
for err in at.error:
    print("ERROR ELEMENT:", err.value)

ok = len(at.exception) == 0 and len(at.dataframe) >= 1
print("\nAPP INTEGRATION TEST", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
