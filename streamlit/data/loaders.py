import json
import pandas as pd
import re

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from streamlit import cache_data


@cache_data
def get_sessions(base_path: str):
    opti_dir = Path(base_path) / "optitrack"
    imu_dir = Path(base_path) / "airpods"

    if not opti_dir.exists() or not imu_dir.exists():
        return []

    opti_files = list(opti_dir.glob("*.csv"))
    imu_files = list(imu_dir.glob("*.csv"))

    opti_map = {tuple(re.split(r"[-_ ]+", p.stem)): p for p in opti_files}
    imu_map = {tuple(re.split(r"[-_ ]+", p.stem)): p for p in imu_files}

    matched_keys = opti_map.keys() & imu_map.keys()
    matched_sessions = {
        " ".join(key): (opti_map[key], imu_map[key])
        for key in sorted(opti_map.keys() & imu_map.keys())
    }
    unmatched_sessions = sorted(
        f"{p.parent.name}/{p.name}"
        for key, p in opti_map.items() | imu_map.items()
        if key not in matched_keys
    )

    return matched_sessions, unmatched_sessions


@cache_data
def get_participants(base_path: str):
    base_path = Path(base_path)
    if not base_path.exists():
        return []

    participants = []
    for p in sorted(base_path.iterdir()):
        if not p.is_dir():
            continue
        if (p / "optitrack").exists() or (p / "airpods").exists():
            participants.append(p.name)
    return participants


@cache_data
def load_opti(base_path: Path, session: Path) -> pd.DataFrame:
    filename = base_path / "optitrack" / session

    with open(filename, "r") as f:
        metadata = next(f)
        meta = metadata.split(",")
        meta_dict = {meta[i]: meta[i + 1] for i in range(0, len(meta), 2)}
        df = pd.read_csv(f, skiprows=4, header=[0, 1])

    start_time = datetime.strptime(
        meta_dict["Capture Start Time"], "%Y-%m-%d %I.%M.%S.%f %p"
    )
    start_time = start_time.replace(tzinfo=ZoneInfo("America/New_York"))

    df = df.iloc[:, :8]
    df.columns = [
        "_".join([i.lower() for i in col if "Unnamed" not in i]) for col in df.columns
    ]
    df["timestamp"] = df["time (seconds)"] + start_time.timestamp()

    # Convert mm to meters
    df["position_x"] /= 1000
    df["position_y"] /= 1000
    df["position_z"] /= 1000

    return df.rename(
        columns={
            "position_x": "px",
            "position_y": "py",
            "position_z": "pz",
        }
    )


@cache_data
def load_imu(base_path: Path, session: Path) -> pd.DataFrame:

    filename = base_path / "optitrack" / session
    try:
        df = pd.read_csv(filename)
        df = df.rename(
            columns={
                "accel_x": "ax",
                "accel_y": "ay",
                "accel_z": "az",
            }
        )
    except Exception:
        with open(filename, "r") as f:
            data = json.load(f)

        df = pd.json_normalize(data["airpodsDatapoints"])
        df = df.rename(
            columns={
                "timing.timestampEpoch": "timestampEpoch",
                "accelerationX": "ax",
                "accelerationY": "ay",
                "accelerationZ": "az",
            }
        )

    df = df[df["source"] == "airpods"]
    # Convert Gs to m/s^2, ms to seconds
    df["ax"] *= 9.81
    df["ay"] *= 9.81
    df["az"] *= 9.81
    df["timestampEpoch"] /= 1000
    return df
