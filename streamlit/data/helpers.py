import copy
import numpy as np
import pandas as pd

from itertools import permutations, product
from pathlib import Path
from scipy.signal import correlate

from .loaders import load_opti, load_imu, load_metadata, write_global_params
from .params import Params
from .processing import (
    process_trial,
    process_diff,
    rms,
    TrialProcessingError,
)


def detect_skipped_trials(
    trials: pd.DataFrame, participant_path: Path
) -> list[str]:
    """
    Process each of a participant's trials and return those that cannot be
    processed at all -- a recording too short to survive trimming, or
    optitrack/airpods files that do not overlap in time. The result is cached
    in the participant's metadata under "global" so the UI can flag them
    without reprocessing on every load.
    """
    metadata = load_metadata(participant_path)
    skipped = []

    for trial in trials.reset_index().itertuples():
        df_opti = load_opti(trial.opti_file)
        df_imu = load_imu(trial.imu_file)

        trial_params = Params.from_dict(
            metadata.get(f"{trial.task} {trial.trial_num}", {})
        )

        try:
            process_trial(df_opti, df_imu, trial_params)
        except TrialProcessingError as e:
            label = f"{trial.task} {trial.trial_num}"
            print(f"Skipping trial {label} for {participant_path.stem}: {e}")
            skipped.append(label)

    write_global_params(participant_path, {"skipped": skipped})
    return skipped

def _best_offset(result: dict, max_offset: float = 3.0) -> float:
    """
    Optimal time offset (seconds) between the optitrack and airpods velocity
    signals, found by cross correlation but restricted to |offset| <=
    max_offset. The bound matches the range of the UI offset slider and keeps
    a wrong axis mapping from returning an absurd multi-second lag that would
    leave the two signals with no overlapping time window.
    """
    t_opti = result["opti"].index
    t_imu = result["imu"].index
    v_opti = result["opti"]["velocity"]
    v_imu = result["imu"]["velocity"]

    imu_x = np.interp(t_opti, t_imu, v_imu["x"])
    imu_y = np.interp(t_opti, t_imu, v_imu["y"])
    imu_z = np.interp(t_opti, t_imu, v_imu["z"])

    corr = (
        correlate(v_opti["x"], imu_x)
        + correlate(v_opti["y"], imu_y)
        + correlate(v_opti["z"], imu_z)
    )
    n = len(v_opti["x"])
    lags = np.arange(-n + 1, n)
    dt = np.median(np.diff(t_opti))

    max_lag = int(max_offset / dt)
    window = np.abs(lags) <= max_lag
    best_lag = lags[window][np.argmax(corr[window])]
    return best_lag * dt


def _velocity_diff_score(result: dict) -> float:
    """
    Scalar 'how aligned' score: the sum of the time-weighted RMS of the
    absolute velocity difference (optitrack vs airpods) across x, y, z.
    Lower is better -- 0 would mean the velocity graphs sit on top of each
    other. Magnitude is excluded because it is sign-invariant and so would
    not reward correct axis-sign alignment.
    """
    # a nonzero offset can leave a few un-interpolatable boundary rows as NaN;
    # drop them so the score stays finite and comparable across candidates
    diff = result["diff"].dropna()
    if len(diff) == 0:
        return float("inf")
    diff_rms = rms(diff)
    return float(sum(diff_rms[("velocity", axis)] for axis in ("x", "y", "z")))


def auto_align(
    df_opti: pd.DataFrame, df_imu: pd.DataFrame, base_params: Params
) -> tuple[list[str], float, float]:
    """
    Search for the trial parameters that best align the optitrack and
    airpods velocity graphs.

    Two things determine velocity alignment: how each airpods axis maps to
    an optitrack axis (and its sign), and the time offset between the two
    device clocks. This brute-forces every bijective axis mapping (6
    permutations x 8 sign combinations = 48), derives the optimal time
    offset for each via cross correlation, and keeps whichever minimizes
    the velocity difference score. Filters and trim are taken from
    base_params and left unchanged.

    Returns (axes, offset, score) for the best candidate. Raises ValueError
    if no candidate can be aligned at all (e.g. the optitrack and airpods
    recordings never overlap in time within the offset bound).
    """
    best = None
    for perm in permutations(["X", "Y", "Z"]):
        for signs in product(("+", "-"), repeat=3):
            axes = [f"{sign}{axis}" for sign, axis in zip(signs, perm)]
            params = copy.deepcopy(base_params)
            params.axes = axes
            params.offset = 0.0

            # process once with no offset, find the optimal offset via
            # cross correlation, then re-score with that offset applied
            try:
                result = process_trial(df_opti, df_imu, params)
            except TrialProcessingError:
                continue
            offset = _best_offset(result)
            result["opti"].index = result["opti"].index - offset
            result["diff"] = process_diff(result["opti"], result["imu"])

            # a wrong mapping can push the offset so far that the two signals
            # no longer overlap in time; such candidates are meaningless, skip
            if len(result["diff"]) == 0:
                continue
            score = _velocity_diff_score(result)

            if best is None or score < best[2]:
                best = (axes, offset, score)

    if best is None:
        raise ValueError("Auto-align could not find any valid alignment.")

    return best
