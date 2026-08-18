import numpy as np
import pandas as pd

from pathlib import Path

from .loaders import load_opti, load_imu, load_metadata, write_global_params
from .params import Params
from .processing import process_trial, process_ccf


def calculate_median_lag(trials: pd.DataFrame, participant_path: Path) -> float:
    """
    Given a set of trials of a participant, calculate optimal lag between optitrack
    and IMU data for each trial, and take the median.

    During a recording session, there is often a time offset between the clocks of
    the devices when they receive the signal from OptiTrack or Airpods. We correct for
    this via cross correlation. This offset is not observed to vary much between trials
    of a recording session (1 participant), so the time offset parameter affects
    all trials of a participant.
    """
    metadata = load_metadata(participant_path)
    lags = []

    for trial in trials.reset_index().itertuples():
        df_opti = load_opti(trial.opti_file)
        df_imu = load_imu(trial.imu_file)

        trial_params = Params.from_dict(
            metadata.get(f"{trial.task} {trial.trial_num}", {})
        )

        # calculate result without any time offset
        result = process_trial(df_opti, df_imu, trial_params, {})
        lag = process_ccf(result)
        lags.append(lag)

    median_lag = np.median(lags)
    print(f"Calculating lag for {participant_path.stem}: {median_lag}")
    write_global_params(participant_path, {"offset": median_lag})
    return median_lag
