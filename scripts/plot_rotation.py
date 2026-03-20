import argparse
import sys

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R, Slerp

OPTI_TIME_OFFSET = -100


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


# Interpolate each component of rotation matrix
def interpolate_rotations(rot_src, time_src, time_target):
    rot_matrices = rot_src.as_matrix()  # shape (N,3,3)
    interp_matrices = np.empty((len(time_target), 3, 3))

    for i in range(3):
        for j in range(3):
            interp_matrices[:, i, j] = np.interp(
                time_target, time_src, rot_matrices[:, i, j]
            )

    # Re-orthogonalize via SVD to ensure proper rotation matrices
    rot_reconstructed = []
    for mat in interp_matrices:
        U, _, Vt = np.linalg.svd(mat)
        R_mat = U @ Vt
        if np.linalg.det(R_mat) < 0:
            U[:, -1] *= -1
            R_mat = U @ Vt
        rot_reconstructed.append(R_mat)

    return R.from_matrix(np.array(rot_reconstructed))


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

    # frame transform
    T = np.array([[0, 0, -1], [-1, 0, 0], [0, 1, 0]])
    R_opti = rot_opti.as_matrix()
    R_transformed = T @ R_opti @ T.T

    rot_opti = R.from_matrix(R_transformed)

    euler_opti = unwrap_euler(rot_opti.as_euler("xyz", degrees=True))
    euler_app = unwrap_euler(rot_app.as_euler("xyz", degrees=True))

    pitch_a, roll_a, yaw_a = euler_app.T
    pitch_o, roll_o, yaw_o = euler_opti.T

    # pitch_o += np.mean(np.interp(time_opti, time_app, pitch_a) - pitch_o)
    # roll_o += np.mean(np.interp(time_opti, time_app, roll_a) - roll_o)
    # yaw_o += np.mean(np.interp(time_opti, time_app, yaw_a) - yaw_o)
    # rot_opti = R.from_euler("xyz", np.array([pitch_o, roll_o, yaw_o]).T, degrees=True)

    # Interpolate app rotations to opti time
    rot_app_interp = interpolate_rotations(rot_app, time_app, time_opti)
    relative_rot = rot_app_interp * rot_opti.inv()
    R_correction = relative_rot.mean()

    rot_opti_corrected = R_correction * rot_opti

    euler_oc = unwrap_euler(rot_opti_corrected.as_euler("xyz", degrees=True))
    pitch_oc, roll_oc, yaw_oc = euler_oc.T

    fig, axes = plt.subplots(3, 1, sharex=True)

    axes[0].plot(time_opti, pitch_o, label="Pitch (optitrack)")
    axes[0].plot(time_opti, pitch_oc, label="Pitch (optitrackC)")
    axes[0].plot(time_app, pitch_a, linestyle="--", label="Pitch (airpods)")
    axes[0].set_ylabel("Pitch")
    axes[0].legend()
    axes[0].grid(True)

    axes[1].plot(time_opti, roll_o, label="Roll (optitrack)")
    axes[1].plot(time_opti, roll_oc, label="Roll (optitrackC)")
    axes[1].plot(time_app, roll_a, linestyle="--", label="Roll (airpods)")
    axes[1].set_ylabel("Roll")
    axes[1].legend()
    axes[1].grid(True)

    axes[2].plot(time_opti, yaw_o, label="Yaw (optitrack)")
    axes[2].plot(time_opti, yaw_oc, label="Yaw (optitrackC)")
    axes[2].plot(time_app, yaw_a, linestyle="--", label="Yaw (airpods)")
    axes[2].set_ylabel("Yaw")
    axes[2].set_xlabel("Timestamp")
    axes[2].legend()
    axes[2].grid(True)

    plt.suptitle("Rotation vs Time")
    plt.show()
