import argparse
import csv
import sys
import time
import datetime

from NatNetClient import NatNetClient


prev_time = None
curr_time = None
time_offset = None

writer = None
output_file = None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="motive_skeleton.csv",
        help="Output CSV filename",
    )

    return parser.parse_args()


def handle_frame_data(frame):
    global prev_time, curr_time, time_offset

    prev_time = curr_time
    curr_time = frame["timestamp"]

    if time_offset is None:
        time_offset = time.time() - curr_time

    dt = -1
    if prev_time is not None:
        dt = curr_time - prev_time
    if dt < 0 or curr_time is None:
        return

    wall_time = curr_time + time_offset
    timestamp = datetime.datetime.fromtimestamp(wall_time, datetime.UTC)
    timestamp_epoch = int(wall_time * 1000)

    for skeleton in frame["mocap_data"].skeleton_data.skeleton_list:
        skeleton_id = skeleton.id_num
        for bone in skeleton.rigid_body_list:
            position = bone.pos
            rotation = bone.rot
            bone_id = bone.id_num

            writer.writerow(
                [
                    timestamp.isoformat(),
                    timestamp_epoch,
                    dt,
                    skeleton_id,
                    bone_id,
                    *position,
                    *rotation,
                ]
            )


if __name__ == "__main__":
    args = parse_args()
    output_file = args.output

    csv_file = open(output_file, "w", newline="")
    writer = csv.writer(csv_file)
    writer.writerow(
        [
            "timestamp",
            "timestampEpoch",
            "deltaTime",
            "skeletonID",
            "boneID",
            "posX",
            "posY",
            "posZ",
            "quatX",
            "quatY",
            "quatZ",
            "quatW",
        ]
    )

    streaming_client = NatNetClient()
    streaming_client.new_frame_with_data_listener = handle_frame_data
    streaming_client.set_use_multicast(False)

    print(f"Logging skeleton data to {output_file}.")

    is_running = streaming_client.run("d")
    if not is_running:
        print("Error: Could not start streaming client.")
        sys.exit(1)

    is_looping = True
    time.sleep(1)
    if streaming_client.connected() is False:
        print("Error: Could not connect to Motive.")
        sys.exit(2)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        streaming_client.new_frame_with_data_listener = None
        print("Saving file...")
        time.sleep(1)
        csv_file.close()

        print("File saved.")
        sys.exit(0)
