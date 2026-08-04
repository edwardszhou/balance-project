import numpy as np
import pandas as pd

from scipy.signal import butter, sosfiltfilt, detrend, correlate
from scipy.integrate import cumulative_trapezoid, trapezoid

AXES = ["x", "y", "z"]
UNITS = {
    "velocity": "m/s",
    "acceleration": "m/s^2",
    "jerk": "m/s^3",
}
OPTI_FILTERS = ["Low-pass"]
AIRPODS_FILTERS = ["Detrend (a)", "Low-pass", "High-pass", "Detrend (v)"]


def lowpass(signal: np.ndarray, time: np.ndarray, cutoff: float, order=4):
    dt = np.median(np.diff(time))
    fs = 1 / dt
    sos = butter(order, cutoff / (0.5 * fs), btype="lowpass", output="sos")
    return sosfiltfilt(sos, signal)


def highpass(signal: np.ndarray, time: np.ndarray, cutoff: float, order=4):
    dt = np.median(np.diff(time))
    fs = 1 / dt
    sos = butter(order, cutoff / (0.5 * fs), btype="highpass", output="sos")
    return sosfiltfilt(sos, signal)


def bandpass(
    signal: np.ndarray, time: np.ndarray, cutoff: tuple[float, float], order=4
):
    dt = np.median(np.diff(time))
    fs = 1 / dt
    sos = butter(order, cutoff / (0.5 * fs), btype="bandpass", output="sos")
    return sosfiltfilt(sos, signal)


def rms(signal: np.ndarray, time: np.ndarray) -> float:
    if len(time) < 2:
        return float("nan")
    integral = trapezoid(signal**2, time)
    duration = time[-1] - time[0]
    return float(np.sqrt(integral / duration))


def process_opti(df: pd.DataFrame, t: np.ndarray, filters: dict):
    px = df["px"].values
    py = df["py"].values
    pz = df["pz"].values

    # Lowpass -> Differentiation
    if OPTI_FILTERS[0] in filters:
        px = lowpass(px, t, *filters[OPTI_FILTERS[0]])
        py = lowpass(py, t, *filters[OPTI_FILTERS[0]])
        pz = lowpass(pz, t, *filters[OPTI_FILTERS[0]])

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

    return {
        "time": t,
        "velocity": {"x": vx, "y": vy, "z": vz, "magnitude": v_magnitude},
        "acceleration": {"x": ax, "y": ay, "z": az, "magnitude": a_magnitude},
        "jerk": {"x": jx, "y": jy, "z": jz, "magnitude": j_magnitude},
    }


def process_imu(df: pd.DataFrame, t: np.ndarray, filters: dict):

    # Bandpass -> Integration -> Detrend
    ax = df["ax"].values
    ay = df["ay"].values
    az = df["az"].values

    if AIRPODS_FILTERS[0] in filters:
        ax = detrend(ax)
        ay = detrend(ay)
        az = detrend(az)

    if AIRPODS_FILTERS[1] in filters:
        ax = lowpass(ax, t, *filters[AIRPODS_FILTERS[1]])
        ay = lowpass(ay, t, *filters[AIRPODS_FILTERS[1]])
        az = lowpass(az, t, *filters[AIRPODS_FILTERS[1]])

    if AIRPODS_FILTERS[2] in filters:
        ax = highpass(ax, t, *filters[AIRPODS_FILTERS[2]])
        ay = highpass(ay, t, *filters[AIRPODS_FILTERS[2]])
        az = highpass(az, t, *filters[AIRPODS_FILTERS[2]])

    vx = cumulative_trapezoid(ax, t, initial=0)
    vy = cumulative_trapezoid(ay, t, initial=0)
    vz = cumulative_trapezoid(az, t, initial=0)

    if AIRPODS_FILTERS[3] in filters:
        vx = detrend(vx)
        vy = detrend(vy)
        vz = detrend(vz)

    jx = np.gradient(ax, t)
    jy = np.gradient(ay, t)
    jz = np.gradient(az, t)

    v_magnitude = np.sqrt(vx**2 + vy**2 + vz**2)
    a_magnitude = np.sqrt(ax**2 + ay**2 + az**2)
    j_magnitude = np.sqrt(jx**2 + jy**2 + jz**2)

    return {
        "time": t,
        "velocity": {"x": vx, "y": vy, "z": vz, "magnitude": v_magnitude},
        "acceleration": {"x": ax, "y": ay, "z": az, "magnitude": a_magnitude},
        "jerk": {"x": jx, "y": jy, "z": jz, "magnitude": j_magnitude},
    }


def process_trial(
    df_opti: pd.DataFrame,
    df_imu: pd.DataFrame,
    filters_opti: dict,
    filters_imu: dict,
    time_trim: float,
):
    t_opti = df_opti["timestamp"].values
    t_imu = df_imu["timestampEpoch"].values

    mask_opti = (t_opti >= t_opti[0] + time_trim) & (t_opti <= t_opti[-1] - time_trim)
    t_opti = t_opti[mask_opti]
    df_opti = df_opti[mask_opti]

    mask_imu = (t_imu >= t_imu[0] + time_trim) & (t_imu <= t_imu[-1] - time_trim)
    t_imu = t_imu[mask_imu]
    df_imu = df_imu[mask_imu]

    return {
        "opti": process_opti(df_opti, t_opti, filters_opti),
        "imu": process_imu(df_imu, t_imu, filters_imu),
    }


def process_rms(result: dict) -> pd.DataFrame:
    rows = []
    for source, data in result.items():
        for quantity in UNITS:
            rows.append(
                {
                    "Source": "Optitrack" if source == "opti" else "Airpods",
                    "Quantity": quantity,
                    "RMS y": rms(data[quantity]["y"], data["time"]),
                    "RMS x": rms(data[quantity]["x"], data["time"]),
                    "RMS z": rms(data[quantity]["z"], data["time"]),
                    "RMS magnitude": rms(data[quantity]["magnitude"], data["time"]),
                }
            )
    return pd.DataFrame(rows)


def process_ccf(result: dict) -> float:
    t_opti = result["opti"]["time"]
    t_imu = result["imu"]["time"]
    v_opti = result["opti"]["velocity"]
    v_imu = result["imu"]["velocity"]

    # interpolate airpods velocity onto optitrack timestamps
    imu_vx_resampled = np.interp(t_opti, t_imu, v_imu["x"])
    imu_vy_resampled = np.interp(t_opti, t_imu, v_imu["y"])
    imu_vz_resampled = np.interp(t_opti, t_imu, v_imu["z"])

    corr_x = correlate(v_opti["x"], imu_vx_resampled)
    corr_y = correlate(v_opti["y"], imu_vy_resampled)
    corr_z = correlate(v_opti["z"], imu_vz_resampled)
    corr = corr_x + corr_y + corr_z

    lags = np.arange(-len(v_opti["x"]) + 1, len(v_opti["x"]))

    # Keep only lags within 1 second
    mask = (lags >= -120) & (lags <= 120)
    lag = lags[mask][np.argmax(corr[mask])]

    dt = np.median(np.diff(t_opti))

    return lag * dt
