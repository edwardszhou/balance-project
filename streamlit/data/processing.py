import numpy as np
import pandas as pd

from scipy.signal import butter, sosfiltfilt, detrend, correlate
from scipy.integrate import cumulative_trapezoid, trapezoid

from .params import Params, OptiFilters, IMUFilters, AXIS_OPTIONS

AXES = ["x", "y", "z", "magnitude"]
UNITS = {
    "velocity": "m/s",
    "acceleration": "m/s^2",
    "jerk": "m/s^3",
}
SOURCES = {"Optitrack": "opti", "Airpods": "imu", "Abs. Difference": "diff"}


def lowpass(signal: np.ndarray, time: np.ndarray, cutoff: float, order=4):
    """Apply lowpass butterworth filter to a signal"""
    dt = np.median(np.diff(time))
    fs = 1 / dt
    sos = butter(order, cutoff / (0.5 * fs), btype="lowpass", output="sos")
    return sosfiltfilt(sos, signal)


def highpass(signal: np.ndarray, time: np.ndarray, cutoff: float, order=4):
    """Apply highpass butterworth filter to a signal"""
    dt = np.median(np.diff(time))
    fs = 1 / dt
    sos = butter(order, cutoff / (0.5 * fs), btype="highpass", output="sos")
    return sosfiltfilt(sos, signal)


def bandpass(
    signal: np.ndarray, time: np.ndarray, cutoff: tuple[float, float], order=4
):
    """Apply bandpass butterworth filter to a signal"""
    dt = np.median(np.diff(time))
    fs = 1 / dt
    sos = butter(order, cutoff / (0.5 * fs), btype="bandpass", output="sos")
    return sosfiltfilt(sos, signal)


def rms(df: pd.DataFrame) -> pd.Series:
    """Calculate time-weighted root mean square of dataframe"""
    time = df.index
    integral = trapezoid(df**2, time, axis=0)
    duration = time[-1] - time[0]
    return pd.Series(np.sqrt(integral / duration), index=df.columns)


def process_opti(df: pd.DataFrame, t: np.ndarray, filters: OptiFilters):
    """
    Process raw optitrack data (position)
    Apply filters and differentiate to obtain vel, acc, jerk
    """
    px = df["px"].values
    py = df["py"].values
    pz = df["pz"].values

    # Lowpass -> Differentiation
    if filters.lowpass.active:
        px = lowpass(px, t, filters.lowpass.cutoff, filters.lowpass.order)
        py = lowpass(py, t, filters.lowpass.cutoff, filters.lowpass.order)
        pz = lowpass(pz, t, filters.lowpass.cutoff, filters.lowpass.order)

    vx = np.gradient(px, t)
    vy = np.gradient(py, t)
    vz = np.gradient(pz, t)

    ax = np.gradient(vx, t)
    ay = np.gradient(vy, t)
    az = np.gradient(vz, t)

    jx = np.gradient(ax, t)
    jy = np.gradient(ay, t)
    jz = np.gradient(az, t)

    v_magnitude = np.sqrt(vx**2 + vy**2 + vz**2)
    a_magnitude = np.sqrt(ax**2 + ay**2 + az**2)
    j_magnitude = np.sqrt(jx**2 + jy**2 + jz**2)

    return pd.DataFrame(
        {
            ("velocity", "x"): vx,
            ("velocity", "y"): vy,
            ("velocity", "z"): vz,
            ("velocity", "magnitude"): v_magnitude,
            ("acceleration", "x"): ax,
            ("acceleration", "y"): ay,
            ("acceleration", "z"): az,
            ("acceleration", "magnitude"): a_magnitude,
            ("jerk", "x"): jx,
            ("jerk", "y"): jy,
            ("jerk", "z"): jz,
            ("jerk", "magnitude"): j_magnitude,
        },
        index=t,
    )


def process_imu(df: pd.DataFrame, t: np.ndarray, filters: IMUFilters):
    """
    Process raw IMU data (acceleration)
    Apply filters and integrate/differentiate to obtain pos, acc, jerk
    """

    # Detrend -> Filter -> Integration -> Detrend
    ax = df["ax"].values
    ay = df["ay"].values
    az = df["az"].values

    if filters.detrend_a.active:
        ax = detrend(ax)
        ay = detrend(ay)
        az = detrend(az)

    if filters.lowpass.active:
        ax = lowpass(ax, t, filters.lowpass.cutoff, filters.lowpass.order)
        ay = lowpass(ay, t, filters.lowpass.cutoff, filters.lowpass.order)
        az = lowpass(az, t, filters.lowpass.cutoff, filters.lowpass.order)

    if filters.highpass.active:
        ax = highpass(ax, t, filters.highpass.cutoff, filters.highpass.order)
        ay = highpass(ay, t, filters.highpass.cutoff, filters.highpass.order)
        az = highpass(az, t, filters.highpass.cutoff, filters.highpass.order)

    vx = cumulative_trapezoid(ax, t, initial=0)
    vy = cumulative_trapezoid(ay, t, initial=0)
    vz = cumulative_trapezoid(az, t, initial=0)

    if filters.detrend_v.active:
        vx = detrend(vx)
        vy = detrend(vy)
        vz = detrend(vz)

    jx = np.gradient(ax, t)
    jy = np.gradient(ay, t)
    jz = np.gradient(az, t)

    v_magnitude = np.sqrt(vx**2 + vy**2 + vz**2)
    a_magnitude = np.sqrt(ax**2 + ay**2 + az**2)
    j_magnitude = np.sqrt(jx**2 + jy**2 + jz**2)

    return pd.DataFrame(
        {
            ("velocity", "x"): vx,
            ("velocity", "y"): vy,
            ("velocity", "z"): vz,
            ("velocity", "magnitude"): v_magnitude,
            ("acceleration", "x"): ax,
            ("acceleration", "y"): ay,
            ("acceleration", "z"): az,
            ("acceleration", "magnitude"): a_magnitude,
            ("jerk", "x"): jx,
            ("jerk", "y"): jy,
            ("jerk", "z"): jz,
            ("jerk", "magnitude"): j_magnitude,
        },
        index=t,
    )


def process_diff(df_opti: pd.DataFrame, df_imu: pd.DataFrame):
    """
    Get velocity difference between optitrack and IMU data over common time period
    """
    t_start = max(df_opti.index.min(), df_imu.index.min())
    t_end = min(df_opti.index.max(), df_imu.index.max())

    df_opti = df_opti.loc[t_start:t_end].copy()
    df_imu = df_imu.loc[t_start:t_end].copy()

    t_opti = df_opti.index
    t_imu = df_imu.index

    # IMU data is recorded at 50hz, needs to be resampled to Optitrack timestamps (120hz)
    df_imu_resampled = df_imu.reindex(t_imu.union(t_opti))
    df_imu_resampled.interpolate(method="index", inplace=True)
    df_imu_resampled = df_imu_resampled.loc[t_opti]

    return (df_opti - df_imu_resampled).abs()


def process_trial(
    df_opti: pd.DataFrame,
    df_imu: pd.DataFrame,
    trial_params: Params,
    global_params: dict,
):
    """
    Process raw data from optitrack and IMU into dataframe.
    Data from sensors are both first trimmed at the start and end, then
    processed. Then, axes are aligned between the two sources and
    time offset is applied.
    """

    trim = trial_params.trim
    df_opti = df_opti.loc[
        df_opti["timestamp"].between(
            df_opti["timestamp"].iloc[0] + trim,
            df_opti["timestamp"].iloc[-1] - trim,
        )
    ]
    df_imu = df_imu.loc[
        df_imu["timestampEpoch"].between(
            df_imu["timestampEpoch"].iloc[0] + trim,
            df_imu["timestampEpoch"].iloc[-1] - trim,
        )
    ]
    t_opti = df_opti["timestamp"].values
    t_imu = df_imu["timestampEpoch"].values

    result_opti = process_opti(df_opti, t_opti, trial_params.opti)
    result_imu = process_imu(df_imu, t_imu, trial_params.imu)

    # Swap data for different axes in optitrack
    axes_match = [AXIS_OPTIONS[option] for option in trial_params.axes]
    temp_opti = result_opti.copy()
    for quantity in UNITS:
        for i, (axis_idx, fac) in enumerate(axes_match):
            source = AXES[axis_idx]
            target = AXES[i]
            result_opti[(quantity, target)] = temp_opti[(quantity, source)] * fac

    result_opti.index -= global_params.get("offset", 0)

    result_diff = process_diff(result_opti, result_imu)

    return {"opti": result_opti, "imu": result_imu, "diff": result_diff}


def process_rms(result: dict) -> pd.DataFrame:
    """Process RMS for all signals"""
    return {source: rms(data) for source, data in result.items()}


def process_ccf(result: dict) -> float:
    """
    Calculate optimal time offset between optitrack and IMU velocity signals.
    Find max cross correlation at a specific lag.
    """
    t_opti = result["opti"].index
    t_imu = result["imu"].index
    v_opti = result["opti"]["velocity"]
    v_imu = result["imu"]["velocity"]

    # Resample 50hz IMU signal to 120hz optitrack signal to cross correlate
    imu_vx_resampled = np.interp(t_opti, t_imu, v_imu["x"])
    imu_vy_resampled = np.interp(t_opti, t_imu, v_imu["y"])
    imu_vz_resampled = np.interp(t_opti, t_imu, v_imu["z"])

    corr_x = correlate(v_opti["x"], imu_vx_resampled)
    corr_y = correlate(v_opti["y"], imu_vy_resampled)
    corr_z = correlate(v_opti["z"], imu_vz_resampled)

    lags = np.arange(-len(v_opti["x"]) + 1, len(v_opti["x"]))
    lag = lags[np.argmax(corr_x + corr_y + corr_z)]

    dt = np.median(np.diff(t_opti))

    return lag * dt
