import numpy as np
import pandas as pd

from scipy.signal import butter, sosfiltfilt, detrend
from scipy.integrate import cumulative_trapezoid, trapezoid

AXES = ["x", "y", "z"]
UNITS = {
    "velocity": "m/s",
    "acceleration": "m/s^2",
    "jerk": "m/s^3",
}


def lowpass(signal: np.ndarray, time: np.ndarray, cutoff: float, order=4):
    dt = np.median(np.diff(time))
    fs = 1 / dt
    sos = butter(order, cutoff / (0.5 * fs), btype="lowpass", output="sos")
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


def process_opti(
    df: pd.DataFrame,
    t: np.ndarray,
    lp_cutoff: float,
    lp_order: int,
    filter=True,
    flip_axes=None,
):
    px = df["px"].values
    py = df["py"].values
    pz = df["pz"].values

    # Lowpass -> Differentiation
    if filter:
        px = lowpass(px, t, lp_cutoff, lp_order)
        py = lowpass(py, t, lp_cutoff, lp_order)
        pz = lowpass(pz, t, lp_cutoff, lp_order)

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


def process_imu(
    df: pd.DataFrame,
    t: np.ndarray,
    bp_cutoff: tuple[float, float],
    bp_order: int,
    filter=True,
):

    # Bandpass -> Integration -> Detrend
    ax = df["ax"].values
    ay = df["ay"].values
    az = df["az"].values

    if filter:
        ax = bandpass(ax, t, bp_cutoff, bp_order)
        ay = bandpass(ay, t, bp_cutoff, bp_order)
        az = bandpass(az, t, bp_cutoff, bp_order)

    vx = detrend(cumulative_trapezoid(ax, t, initial=0))
    vy = detrend(cumulative_trapezoid(ay, t, initial=0))
    vz = detrend(cumulative_trapezoid(az, t, initial=0))

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
    lp_cutoff: float,
    bp_cutoff: tuple[float, float],
    lp_order: int,
    bp_order: int,
    time_trim: float,
    time_offset: float,
    filter_opti=True,
    filter_imu=True,
):
    t_opti = df_opti["timestamp"].values + time_offset
    t_imu = df_imu["timestampEpoch"].values

    t_start = max(t_opti[0], t_imu[0]) + time_trim
    t_end = min(t_opti[-1], t_imu[-1]) - time_trim

    if t_end <= t_start:
        raise ValueError("Trim buffer too large for this session's overlap window.")

    mask_o = (t_opti >= t_start) & (t_opti <= t_end)
    mask_a = (t_imu >= t_start) & (t_imu <= t_end)

    t_opti = t_opti[mask_o] - t_start
    t_imu = t_imu[mask_a] - t_start

    df_opti = df_opti[mask_o]
    df_imu = df_imu[mask_a]

    return {
        "opti": process_opti(df_opti, t_opti, lp_cutoff, lp_order, filter_opti),
        "imu": process_imu(df_imu, t_imu, bp_cutoff, bp_order, filter_imu),
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
