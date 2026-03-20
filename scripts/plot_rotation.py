import argparse
import sys

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R, Slerp

OPTI_TIME_OFFSET = -140


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


def normalize_time(t):
    t = np.array(t)
    return t - t[0]


def unwrap_euler(euler_deg):
    return np.degrees(np.unwrap(np.radians(euler_deg), axis=0))


if __name__ == "__main__":
    args = parse_args()
    try:
        if args.opti and args.app:
            df_opti = pd.read_csv(args.opti)
            df_app = pd.read_csv(args.app)
        elif args.filename:
            df_opti = pd.read_csv(f"../data/opti_{args.filename}.csv")
            df_app = pd.read_csv(f"../data/app_{args.filename}.csv")
        else:
            print("Files not specified.")
            sys.exit(1)
    except Exception as e:
        print("Error reading file path:", e)
        sys.exit(1)

    df_app = df_app.loc[df_app["source"] == "airpods"]

    time_opti = df_opti["timestampEpoch"].values - OPTI_TIME_OFFSET
    time_app = df_app["timestampEpoch"].values

    rot_opti = R.from_quat(df_opti[["quatX", "quatY", "quatZ", "quatW"]].values)
    rot_app = R.from_euler(
        "xyz", df_app[["angle_pitch", "angle_roll", "angle_yaw"]].values
    )

    # Mask to get overlapping time only
    time_start = max(time_opti[0], time_app[0])
    time_end = min(time_opti[-1], time_app[-1])
    mask_opti = (time_opti >= time_start) & (time_opti <= time_end)
    mask_app = (time_app >= time_start) & (time_app <= time_end)

    time_opti = time_opti[mask_opti]
    rot_opti = rot_opti[mask_opti]
    time_app = time_app[mask_app]
    rot_app = rot_app[mask_app]

    # Align rotation

    # alignments = rot_app[0] * rot_opti[0].inv()
    # align_quat = alignments.as_quat()
    # rot_align = R.from_quat(align_quat)
    # rot_opti_new = rot_align * rot_opti

    euler_opti = unwrap_euler(rot_opti.as_euler("zxy", degrees=True))
    euler_app = unwrap_euler(rot_app.as_euler("xyz", degrees=True))

    pitch_a, roll_a, yaw_a = euler_app.T
    pitch_o, roll_o, yaw_o = euler_opti.T
    # pitch_on, roll_on, yaw_on = euler_opti_new.T
    roll_o *= -1
    pitch_o *= -1

    pitch_o += np.mean(np.interp(time_opti, time_app, pitch_a) - pitch_o)
    roll_o += np.mean(np.interp(time_opti, time_app, roll_a) - roll_o)
    yaw_o += np.mean(np.interp(time_opti, time_app, yaw_a) - yaw_o)

    fig, axes = plt.subplots(3, 1, sharex=True)

    axes[0].plot(time_opti, pitch_o, label="Pitch (optitrack)")
    # axes[0].plot(time_opti, pitch_on, label="Pitch (optitrackN)")
    axes[0].plot(time_app, pitch_a, linestyle="--", label="Pitch (airpods)")
    axes[0].set_ylabel("Pitch")
    axes[0].legend()
    axes[0].grid(True)

    axes[1].plot(time_opti, roll_o, label="Roll (optitrack)")
    # axes[1].plot(time_opti, roll_on, label="Roll (optitrackN)")
    axes[1].plot(time_app, roll_a, linestyle="--", label="Roll (airpods)")
    axes[1].set_ylabel("Roll")
    axes[1].legend()
    axes[1].grid(True)

    axes[2].plot(time_opti, yaw_o, label="Yaw (optitrack)")
    # axes[2].plot(time_opti, yaw_on, label="Yaw (optitrackN)")
    axes[2].plot(time_app, yaw_a, linestyle="--", label="Yaw (airpods)")
    axes[2].set_ylabel("Yaw")
    axes[2].set_xlabel("Timestamp")
    axes[2].legend()
    axes[2].grid(True)

    plt.suptitle("Rotation vs Time")
    plt.show()
