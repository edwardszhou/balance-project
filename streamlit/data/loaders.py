import json
import pandas as pd
import re

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from streamlit import cache_data

from .params import Params


def split_trial_key(key: tuple[str, ...]):
    """
    Split arbitrary name tuple into task, trial #, and participant
    """
    pid = key[-1]
    if len(key) >= 2 and key[-2].isdigit():
        task = " ".join(key[:-2])
        number = key[-2]
    else:
        task = " ".join(key[:-1])
        number = "1"

    return task, number, pid


@cache_data
def get_trials(base_path: str):
    """
    Get all valid trial names for a given path (participant folder). Match files
    between optitrack and imu based on filename, and process trial data
    from file name.
    """
    opti_dir = Path(base_path) / "optitrack"
    imu_dir = Path(base_path) / "airpods"

    if not opti_dir.exists() or not imu_dir.exists():
        return []

    opti_files = list(opti_dir.glob("*.csv"))
    imu_files = list(imu_dir.glob("*.csv"))

    opti_map = {tuple(re.split(r"[-_ ]+", p.stem)): p for p in opti_files}
    imu_map = {tuple(re.split(r"[-_ ]+", p.stem)): p for p in imu_files}

    matched_keys = opti_map.keys() & imu_map.keys()

    # Form (task, trial#, pid) tuples from trials with both sources
    matched_trials = {
        split_trial_key(key): (opti_map[key], imu_map[key])
        for key in sorted(matched_keys)
    }

    # Get list of all unmatched files + parent directory (opti/airpods)
    unmatched_trials = sorted(
        f"{p.parent.name}/{p.name}"
        for key, p in opti_map.items() | imu_map.items()
        if key not in matched_keys
    )

    return matched_trials, unmatched_trials


@cache_data
def get_participants(base_path: str):
    """
    Find all valid participant folders in the given directory.
    Participant folder is valid if it contains optitrack and airpods
    subdirectories.
    """
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
def load_opti(filename: Path) -> pd.DataFrame:
    """
    Load optitrack file into dataframe and standardize units.
    Optitrack files are assumed to have been exported from Motive as csvs.
    """
    with open(filename, "r") as f:
        metadata = next(f)
        meta = metadata.split(",")
        meta_dict = {meta[i]: meta[i + 1] for i in range(0, len(meta), 2)}
        df = pd.read_csv(f, skiprows=4, header=[0, 1])

    start_time = datetime.strptime(
        meta_dict["Capture Start Time"], "%Y-%m-%d %I.%M.%S.%f %p"
    )
    start_time = start_time.replace(tzinfo=ZoneInfo("America/New_York"))

    # Trim unnecessary metadata from csv header, flatten columns
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
def load_imu(filename: Path) -> pd.DataFrame:
    """
    Load airpods IMU data file into dataframe and standardize units.
    Airpods files are assuemd to have been either exported from the
    Balance Project app as csv, exported as json, or downloaded from the
    database as json.
    """
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

    # Exclude IMU data from iPhone
    df = df[df["source"] == "airpods"]

    # Convert Gs to m/s^2, ms to seconds
    df["ax"] *= -9.81
    df["ay"] *= -9.81
    df["az"] *= -9.81
    df["timestampEpoch"] /= 1000
    return df


def load_metadata(participant_path: Path) -> dict:
    """Load metadata json for partcipant."""
    filename = participant_path / "metadata.json"
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_trial_params(participant_path: Path, trial: str, params: Params):
    """Write trial parameters to metadata.json for participant"""
    write_metadata(participant_path, {trial: params.to_dict()})


def write_global_params(participant_path: Path, updates: dict):
    """Write globa parameters to metadata.json for participant"""
    write_metadata(participant_path, {"global": updates})


def write_metadata(participant_path: Path, updates: dict):
    """Update metadata.json for participant"""

    filename = participant_path / "metadata.json"
    metadata = load_metadata(participant_path)
    metadata.update(updates)

    with open(filename, "w") as f:
        json.dump(metadata, f, indent=4)
