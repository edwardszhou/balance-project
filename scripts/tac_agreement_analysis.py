"""
TAC Agreement Analysis.

Builds the "TAC Agreement analysis" CSV (one row per trial repetition) comparing
OptiTrack and AirPods for a set of participants and a chosen trial group.

For every trial we compute, on each of five planes, three outcome measures for
both devices (OptiTrack "optitrak" and AirPods "earbuds"):

    - DP   : Directional Path          (cm  / deg)
    - VRMS : RMS Velocity              (cm/s  / deg/s)
    - RMSA : RMS Acceleration          (cm/s^2 / deg/s^2)

Planes:
    - AP    (anterior-posterior) : translational, standardized axis Y (forward)
    - ML    (medial-lateral)     : translational, standardized axis X (left)
    - Pitch, Yaw, Roll           : rotational (degrees)
    (Standardized axis Z is vertical/up and is intentionally excluded.)

Axis convention: the Motive CSV export here is Z-up (the "Position Z" column
holds head height, ~1.6 m standing vs ~1.2 m sitting), so Z is vertical and the
two horizontal axes are X (left -> ML) and Y (forward -> AP). The OptiTrack and
AirPods axes correspond one-to-one (verified: per-axis VRMS across 240 static
trials correlates highest on the matching axis, X<->x 0.97, Y<->y 0.94,
Z<->z 0.84), which is why metadata `axes` is left at identity. AP vs ML labelling
of the two horizontal axes follows the capture convention (X=left, Y=forward); if
the lab's facing convention differs, swap AP/ML here.

Formulas (from "TAC agreement analysis plan"):
    DP   = sum(|diff(signal)|)
    vel  = diff(signal) / diff(t)          ; VRMS = sqrt(mean(vel^2))
    acc  = diff(vel) / (t[2:]/2 - t[:-2]/2); RMSA = sqrt(mean(acc^2))

Per-device handling:
    OptiTrack  - translational metrics are computed directly from the cleaned,
                 axis-aligned POSITION signal via the formulas above.
                 Rotational metrics use the exported euler angles (degrees).
    AirPods    - the sensor reports linear ACCELERATION, not position, so the
                 translational pipeline from streamlit/data/processing.py is
                 reused: acceleration -> (integrate) velocity -> (integrate)
                 position. RMSA uses the processed acceleration, VRMS the
                 integrated velocity, DP the twice-integrated position.
                 Rotational metrics use the reported orientation angles
                 (radians, converted to degrees) via the same formulas.

Cleanup constants are read per participant from metadata.json (the same file the
Streamlit app writes during data cleanup): axis convention, trim seconds, and
the low-pass / high-pass / detrend filter settings for each trial. The measured
time offset is read but does not affect per-device metrics (a uniform time shift
leaves every diff(t) unchanged), so it is intentionally not applied here.

Rotation signals are low-pass filtered with each device's configured low-pass
cutoff (when active) to keep differentiation noise from dominating VRMS/RMSA;
no detrend/high-pass is applied to angles. Translational cleanup matches the app.

Usage:
    python scripts/tac_agreement_analysis.py --type static 373 446 459
    python scripts/tac_agreement_analysis.py -t STS -o sts.csv 446
    python scripts/tac_agreement_analysis.py -t TUG --base-path /path/to/data 446
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid

# Reuse the exact data-cleaning pipeline from the Streamlit app. processing.py and
# params.py depend only on numpy/scipy/pandas (no streamlit), so we add the app
# package to the path and import the pure modules. loaders.py pulls in streamlit,
# so the few loader functions we need are reimplemented below without the cache.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "streamlit"))
from data.processing import process_imu, lowpass  # noqa: E402
from data.params import Params, AXIS_OPTIONS  # noqa: E402

M_TO_CM = 100.0

# Trial groups -> the task names (as produced by split_task below) to include.
TASK_SETS = {
    "static": [
        "FT EC",
        "FT EC FO",
        "FT EO",
        "FT EO FO",
        "LT",
        "RT",
        "SIT EC",
        "SIT EO",
    ],
    "STS": [
        "LT SHOE",
        "RT SHOE",
        "STS",
        "STS EC FO",
        "STS FO",
    ],
    "TUG": [
        "TUG",
    ],
}

# Output column order, matching the provided template exactly ("optitrak" spelling).
PLANES = ["AP", "ML", "Pitch", "Yaw", "Roll"]
METRICS = ["VRMS", "DP", "RMSA"]
BASE_COLUMNS = ["filename", "ID", "Condition", "repetition"]


def metric_columns() -> list[str]:
    """Build the 30 metric column names in template order (metric x plane x device)."""
    cols = []
    for metric in METRICS:
        for plane in PLANES:
            cols.append(f"{metric}{plane}_optitrak")
            cols.append(f"{metric}{plane}_earbuds")
    return cols


# --------------------------------------------------------------------------- #
# Loading (mirrors streamlit/data/loaders.py, minus the streamlit cache)
# --------------------------------------------------------------------------- #
def split_task(stem: str) -> tuple[str, str, str]:
    """
    Parse a trial file stem into (task, repetition, participant id).

    Names look like "FT EC 1 446" or "LT-SHOE-2-446". If the second-to-last
    token is a number it is the repetition, otherwise the repetition is "1".
    """
    key = tuple(re.split(r"[-_ ]+", stem))
    pid = key[-1]
    if len(key) >= 2 and key[-2].isdigit():
        task = " ".join(key[:-2])
        rep = key[-2]
    else:
        task = " ".join(key[:-1])
        rep = "1"
    return task, rep, pid


def match_trials(participant_path: Path) -> dict[tuple[str, str], tuple[Path, Path]]:
    """
    Match OptiTrack and AirPods files for a participant by normalized name.

    Returns {(task, repetition): (opti_file, imu_file)}.
    """
    opti_dir = participant_path / "optitrack"
    imu_dir = participant_path / "airpods"
    if not opti_dir.exists() or not imu_dir.exists():
        return {}

    opti_map = {tuple(re.split(r"[-_ ]+", p.stem)): p for p in opti_dir.glob("*.csv")}
    imu_map = {tuple(re.split(r"[-_ ]+", p.stem)): p for p in imu_dir.glob("*.csv")}

    matched = {}
    for key in sorted(opti_map.keys() & imu_map.keys()):
        task, rep, _pid = split_task("_".join(key))
        matched[(task, rep)] = (opti_map[key], imu_map[key])
    return matched


def load_opti(filename: Path) -> pd.DataFrame:
    """
    Load an OptiTrack Motive export: position (mm -> m) and euler rotation (deg).

    Columns kept: timestamp (s), px/py/pz (m), rotation_x/y/z (deg).
    """
    with open(filename, "r") as f:
        meta = next(f).split(",")
        meta_dict = {meta[i]: meta[i + 1] for i in range(0, len(meta) - 1, 2)}
        df = pd.read_csv(f, skiprows=4, header=[0, 1])

    start_time = datetime.strptime(
        meta_dict["Capture Start Time"], "%Y-%m-%d %I.%M.%S.%f %p"
    ).replace(tzinfo=ZoneInfo("America/New_York"))

    # Frame, Time, Rotation Y/X/Z, Position X/Y/Z
    df = df.iloc[:, :8]
    df.columns = [
        "_".join([i.lower() for i in col if "Unnamed" not in i]) for col in df.columns
    ]
    df["timestamp"] = df["time (seconds)"] + start_time.timestamp()
    df["px"] = df["position_x"] / 1000
    df["py"] = df["position_y"] / 1000
    df["pz"] = df["position_z"] / 1000
    return df


def load_imu(filename: Path) -> pd.DataFrame:
    """
    Load AirPods data (csv or json): acceleration (G -> m/s^2) and orientation.

    Columns kept: timestampEpoch (s), ax/ay/az (m/s^2),
    angle_pitch/angle_roll/angle_yaw (radians).
    """
    try:
        df = pd.read_csv(filename)
        df = df.rename(columns={"accel_x": "ax", "accel_y": "ay", "accel_z": "az"})
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
                "anglePitch": "angle_pitch",
                "angleRoll": "angle_roll",
                "angleYaw": "angle_yaw",
            }
        )

    df = df[df["source"] == "airpods"].copy()
    df["ax"] *= -9.81
    df["ay"] *= -9.81
    df["az"] *= -9.81
    df["timestampEpoch"] /= 1000
    return df


def load_metadata(participant_path: Path) -> dict:
    """Load a participant's metadata.json, or {} if missing/invalid."""
    try:
        with open(participant_path / "metadata.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# --------------------------------------------------------------------------- #
# Signal prep
# --------------------------------------------------------------------------- #
def trim(df: pd.DataFrame, time_col: str, seconds: float) -> pd.DataFrame:
    """Drop the first and last `seconds` of a recording (matches process_trial)."""
    t = df[time_col]
    return df.loc[t.between(t.iloc[0] + seconds, t.iloc[-1] - seconds)]


def unwrap_deg(angles_deg: np.ndarray) -> np.ndarray:
    """Unwrap an angle series (in degrees) to remove +/-180 discontinuities."""
    return np.degrees(np.unwrap(np.radians(angles_deg)))


def align_opti_position(df_opti: pd.DataFrame, params: Params) -> dict[str, np.ndarray]:
    """
    Produce cleaned, axis-aligned OptiTrack position per standardized axis (cm).

    Applies the configured low-pass filter to raw px/py/pz, then the metadata
    axis convention (same mapping as processing.process_opti), returning the
    standardized X (left -> ML) and Y (forward -> AP) axes in centimeters.
    Standardized Z is vertical and is not returned.
    """
    t = df_opti["timestamp"].values
    raw = [df_opti["px"].values, df_opti["py"].values, df_opti["pz"].values]

    lp = params.opti.lowpass
    if lp.active:
        raw = [lowpass(axis, t, lp.cutoff, lp.order) for axis in raw]

    # Standardized axis i comes from raw axis `idx` scaled by `fac`.
    aligned = [None, None, None]
    for i, (idx, fac) in enumerate([AXIS_OPTIONS[o] for o in params.axes]):
        aligned[i] = raw[idx] * fac

    return {
        "t": t,
        "ML": aligned[0] * M_TO_CM,  # standardized X (left)
        "AP": aligned[1] * M_TO_CM,  # standardized Y (forward); Z is vertical
    }


def opti_rotation(df_opti: pd.DataFrame, params: Params) -> dict[str, np.ndarray]:
    """
    Cleaned OptiTrack euler rotation per plane (degrees).

    rotation_x -> Pitch, rotation_y -> Roll, rotation_z -> Yaw (matches the
    convention in scripts/plot_velocity.py). Angles are unwrapped and low-pass
    filtered with the OptiTrack cutoff when active.
    """
    t = df_opti["timestamp"].values
    planes = {
        "Pitch": unwrap_deg(df_opti["rotation_x"].values),
        "Roll": unwrap_deg(df_opti["rotation_y"].values),
        "Yaw": unwrap_deg(df_opti["rotation_z"].values),
    }
    lp = params.opti.lowpass
    if lp.active:
        planes = {k: lowpass(v, t, lp.cutoff, lp.order) for k, v in planes.items()}
    planes["t"] = t
    return planes


def imu_translation(df_imu: pd.DataFrame, params: Params) -> dict[str, np.ndarray]:
    """
    AirPods translational signals per standardized axis, via the app pipeline.

    process_imu integrates acceleration -> velocity (with the configured
    detrend/low-pass/high-pass filters). We integrate velocity once more to get
    position for DP. AirPods axes correspond to the OptiTrack axes one-to-one
    (verified by cross-device per-axis correlation): ax -> ML (x), ay -> AP (y);
    az is vertical and excluded. Units: cm, cm/s, cm/s^2.
    """
    t = df_imu["timestampEpoch"].values
    processed = process_imu(df_imu, t, params.imu)

    out = {"t": t}
    for plane, axis in (("ML", "x"), ("AP", "y")):
        vel = processed[("velocity", axis)].values
        acc = processed[("acceleration", axis)].values
        pos = cumulative_trapezoid(vel, t, initial=0)
        out[f"{plane}_vel"] = vel * M_TO_CM
        out[f"{plane}_acc"] = acc * M_TO_CM
        out[f"{plane}_pos"] = pos * M_TO_CM
    return out


def imu_rotation(df_imu: pd.DataFrame, params: Params) -> dict[str, np.ndarray]:
    """
    Cleaned AirPods orientation per plane (degrees).

    Reported angles are radians; converted to degrees, unwrapped, and low-pass
    filtered with the AirPods cutoff when active.
    """
    t = df_imu["timestampEpoch"].values
    planes = {
        "Pitch": unwrap_deg(np.degrees(df_imu["angle_pitch"].values)),
        "Roll": unwrap_deg(np.degrees(df_imu["angle_roll"].values)),
        "Yaw": unwrap_deg(np.degrees(df_imu["angle_yaw"].values)),
    }
    lp = params.imu.lowpass
    if lp.active:
        planes = {k: lowpass(v, t, lp.cutoff, lp.order) for k, v in planes.items()}
    planes["t"] = t
    return planes


# --------------------------------------------------------------------------- #
# Metrics (plan formulas)
# --------------------------------------------------------------------------- #
def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x))))


def directional_path(signal: np.ndarray) -> float:
    """DP = sum(|diff(signal)|)."""
    return float(np.sum(np.abs(np.diff(signal))))


def _velocity(signal: np.ndarray, t: np.ndarray) -> np.ndarray:
    return np.diff(signal) / np.diff(t)


def _acceleration(signal: np.ndarray, t: np.ndarray) -> np.ndarray:
    vel = _velocity(signal, t)
    acc_dt = t[2:] / 2.0 - t[:-2] / 2.0
    return np.diff(vel) / acc_dt


def metrics_from_position(signal: np.ndarray, t: np.ndarray) -> dict[str, float]:
    """DP/VRMS/RMSA derived from a position (or angle) signal by differentiation."""
    return {
        "DP": directional_path(signal),
        "VRMS": _rms(_velocity(signal, t)),
        "RMSA": _rms(_acceleration(signal, t)),
    }


# --------------------------------------------------------------------------- #
# Per-trial row
# --------------------------------------------------------------------------- #
def compute_trial_row(
    opti_file: Path,
    imu_file: Path,
    task: str,
    rep: str,
    pid: str,
    metadata: dict,
) -> dict:
    """Compute the full set of template metrics for a single trial."""
    params = Params.from_dict(metadata.get(f"{task} {rep}", {}))

    df_opti = trim(load_opti(opti_file), "timestamp", params.trim)
    df_imu = trim(load_imu(imu_file), "timestampEpoch", params.trim)

    opti_pos = align_opti_position(df_opti, params)
    opti_rot = opti_rotation(df_opti, params)
    imu_trans = imu_translation(df_imu, params)
    imu_rot = imu_rotation(df_imu, params)

    row = {
        "filename": opti_file.stem,
        "ID": pid,
        "Condition": task,
        "repetition": rep,
    }

    # OptiTrack translational: formulas straight from the position signal.
    for plane in ("AP", "ML"):
        m = metrics_from_position(opti_pos[plane], opti_pos["t"])
        for metric in METRICS:
            row[f"{metric}{plane}_optitrak"] = m[metric]

    # OptiTrack rotational.
    for plane in ("Pitch", "Yaw", "Roll"):
        m = metrics_from_position(opti_rot[plane], opti_rot["t"])
        for metric in METRICS:
            row[f"{metric}{plane}_optitrak"] = m[metric]

    # AirPods translational: integrated pipeline (pos->DP, vel->VRMS, acc->RMSA).
    for plane in ("AP", "ML"):
        row[f"DP{plane}_earbuds"] = directional_path(imu_trans[f"{plane}_pos"])
        row[f"VRMS{plane}_earbuds"] = _rms(imu_trans[f"{plane}_vel"])
        row[f"RMSA{plane}_earbuds"] = _rms(imu_trans[f"{plane}_acc"])

    # AirPods rotational: formulas from the orientation angle signal.
    for plane in ("Pitch", "Yaw", "Roll"):
        m = metrics_from_position(imu_rot[plane], imu_rot["t"])
        for metric in METRICS:
            row[f"{metric}{plane}_earbuds"] = m[metric]

    return row


def build_dataframe(
    participants: list[str], trial_group: str, base_path: Path
) -> pd.DataFrame:
    """Build the full output table for the given participants and trial group."""
    wanted_tasks = set(TASK_SETS[trial_group])
    rows = []

    for pid in participants:
        participant_path = base_path / str(pid)
        if not participant_path.exists():
            print(f"[warn] participant folder not found: {participant_path}")
            continue

        metadata = load_metadata(participant_path)
        skipped = set(metadata.get("global", {}).get("skipped", []))
        trials = match_trials(participant_path)

        selected = sorted(
            (task, rep)
            for (task, rep) in trials
            if task in wanted_tasks and f"{task} {rep}" not in skipped
        )
        if not selected:
            print(f"[warn] no '{trial_group}' trials found for participant {pid}")
            continue

        for task, rep in selected:
            opti_file, imu_file = trials[(task, rep)]
            try:
                rows.append(
                    compute_trial_row(opti_file, imu_file, task, rep, str(pid), metadata)
                )
                print(f"[ok]  {pid}: {task} {rep}")
            except Exception as exc:  # keep going; report the offending trial
                print(f"[error] {pid}: {task} {rep} -> {exc}")

    columns = BASE_COLUMNS + metric_columns()
    return pd.DataFrame(rows, columns=columns)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the TAC agreement-analysis CSV (OptiTrack vs AirPods).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "participants",
        nargs="+",
        help="Participant numbers, e.g. 373 446 459",
    )
    parser.add_argument(
        "-t",
        "--type",
        required=True,
        choices=list(TASK_SETS),
        help="Trial group to include.",
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=REPO_ROOT / "streamlit" / "data",
        help="Folder containing participant subfolders.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output CSV path (default: tac_<type>.csv in the current directory).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output or Path(f"tac_{args.type}.csv")

    df = build_dataframe(args.participants, args.type, args.base_path)
    df.to_csv(output, index=False)
    print(f"\nWrote {len(df)} trial rows to {output}")


if __name__ == "__main__":
    main()
