import numpy as np
import pandas as pd

from pathlib import Path

from .loaders import load_opti, load_imu, load_metadata, write_global_params
from .params import Params
from .processing import process_trial, process_ccf


def calculate_median_lag(trials: pd.DataFrame, participant_path: Path) -> float:
    metadata = load_metadata(participant_path)
    lags = []

    for trial in trials.itertuples():
        df_opti = load_opti(trial.opti_file)
        df_imu = load_imu(trial.imu_file)

        trial_params = Params.from_dict(metadata.get(trial.task, {}))
        result = process_trial(df_opti, df_imu, trial_params)
        lag = process_ccf(result)
        lags.append(lag)

    print(f"Calculating lag for {participant_path.stem}: {np.median(lags)}")
    write_global_params(participant_path, {"offset": np.median(lags)})
