import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
from scipy.spatial.transform import Rotation as R
from datetime import datetime

FILENAME = "tug2"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", "-a", help="App data CSV path")
    parser.add_argument("--opti", "-o", help="OptiTrack data CSV path")
    parser.add_argument(
        "--filename",
        "-f",
        help="File name for app and optitrack CSV (data/[app/opti]_[name].csv)",
    )

    return parser.parse_args()


def unwrap_euler(euler, degrees=False):
    if degrees:
        return np.degrees(np.unwrap(np.radians(euler), axis=0))
    return np.degrees(np.unwrap(euler, axis=0))


if __name__ == "__main__":
    opti_filename = f"../data/4-7/47{FILENAME}opti.csv"

    with open(opti_filename, "r") as f:
        metadata = next(f)
        metadata_list = metadata.split(",")
        metadata_dict = {
            metadata_list[i]: metadata_list[i + 1]
            for i in range(0, len(metadata_list), 2)
        }

        df_opti = pd.read_csv(f, skiprows=4, header=[0, 1])

    start_time = datetime.strptime(
        metadata_dict["Capture Start Time"], "%Y-%m-%d %I.%M.%S.%f %p"
    )

    df_opti = df_opti.iloc[:, :8]
    df_opti.columns = [
        "_".join([i.lower() for i in col if "Unnamed" not in i])
        for col in df_opti.columns.values
    ]
    df_opti["timestampEpoch"] = df_opti["time (seconds)"] + start_time.timestamp()
    df_opti["timestampEpoch"] *= 1000

    app_filename = f"../data/4-7/47{FILENAME}.csv"
    df_app = pd.read_csv(app_filename)
    df_app = df_app.loc[df_app["source"] == "airpods"]

    time_opti = df_opti["timestampEpoch"].values
    time_app = df_app["timestampEpoch"].values

    # Mask to get overlapping time only
    time_start = max(time_opti[0], time_app[0])
    time_end = min(time_opti[-1], time_app[-1])
    mask_opti = (time_opti >= time_start) & (time_opti <= time_end)
    mask_app = (time_app >= time_start) & (time_app <= time_end)

    time_opti = time_opti[mask_opti]
    df_opti = df_opti[mask_opti]
    time_app = time_app[mask_app]
    df_app = df_app[mask_app]

    euler_app = unwrap_euler(df_app[["angle_pitch", "angle_roll", "angle_yaw"]].values)
    euler_opti = unwrap_euler(
        df_opti[["rotation_x", "rotation_y", "rotation_z"]].values, degrees=True
    )

    pitch_a, roll_a, yaw_a = euler_app.T
    pitch_o, roll_o, yaw_o = euler_opti.T

    fig, axes = plt.subplots(3, 1, figsize=(12, 30), sharex=True)

    axes[0].plot(time_opti, pitch_o, label="Pitch (optitrack)")
    axes[0].plot(time_app, pitch_a, linestyle="--", label="Pitch (airpods)")
    axes[0].set_ylabel("Pitch")
    axes[0].set_ylim(bottom=-90, top=90)
    axes[0].legend()
    axes[0].grid(True)

    axes[1].plot(time_opti, roll_o, label="Roll (optitrack)")
    axes[1].plot(time_app, roll_a, linestyle="--", label="Roll (airpods)")
    axes[1].set_ylabel("Roll")
    axes[1].set_ylim(bottom=-90, top=90)
    axes[1].legend()
    axes[1].grid(True)

    axes[2].plot(time_opti, yaw_o, label="Yaw (optitrack)")
    axes[2].plot(time_app, yaw_a, linestyle="--", label="Yaw (airpods)")
    axes[2].set_ylabel("Yaw")
    axes[2].set_xlabel("Timestamp")
    # axes[2].set_ylim(bottom=-90, top=90)
    axes[2].legend()
    axes[2].grid(True)

    plt.suptitle("Rotation vs Time")
    plt.savefig(f"output/{FILENAME}_rotation.png")
    plt.show()
