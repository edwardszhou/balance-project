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
rigid_body_id = None

def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--output",
    "-o",
    type=str,
    default="optitrack_rigidbody.csv",
    help="Output CSV filename"
  )
  parser.add_argument(
    "--id",
    "-i",
    type=int,
    required=True,
    help="Rigid body ID"
  )

  return parser.parse_args()


def handle_new_frame(frame):
  global prev_time, curr_time, time_offset

  prev_time = curr_time
  curr_time = frame['timestamp']

  if time_offset is None:
    time_offset = time.time() - curr_time

def handle_rigid_body_frame(id, position, rotation):
  if id != rigid_body_id:
    return
  print("Received frame for rigid body", id, position, rotation)
  
  dt = -1
  if prev_time is not None:
    dt = curr_time - prev_time
  if dt < 0 or curr_time is None or time_offset is None:
    return
  
  wall_time = curr_time + time_offset
  timestamp = datetime.datetime.fromtimestamp(wall_time, datetime.UTC)
  timestamp_epoch = int(wall_time * 1000)

  writer.writerow([
    timestamp.isoformat(),
    timestamp_epoch,
    dt,
    *position,
    *rotation,
  ])
  


if __name__ == "__main__":
  args = parse_args()
  output_file = args.output
  rigid_body_id = args.id

  csv_file = open(output_file, "w", newline="")
  writer = csv.writer(csv_file)
  writer.writerow([
    "timestamp",
    "timestampEpoch",
    "deltaTime",
    "posX", "posY", "posZ",
    "quatX", "quatY", "quatZ", "quatW"
  ])

  streaming_client = NatNetClient()
  streaming_client.new_frame_listener = handle_new_frame
  streaming_client.rigid_body_listener = handle_rigid_body_frame
  streaming_client.set_use_multicast(False)

  print(f"Logging rigid body {rigid_body_id} to {output_file}.")

  is_running = streaming_client.run('d')
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
      streaming_client.rigid_body_listener = None
      print("Saving file...")
      time.sleep(1)
      csv_file.close()

      print("File saved.")
      sys.exit(0)
