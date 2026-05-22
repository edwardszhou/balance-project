import argparse
import pandas as pd
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str, help="Input CSV")
    parser.add_argument(
        "--output", "-o", type=str, default=None, help="Output CSV filename "
    )
    return parser.parse_args()


def flatten_csv(input_file, output_file=None):
    df = pd.read_csv(input_file, skiprows=2, header=[0, 1, 2, 3, 4])
    df.columns = [
        "_".join([str(i) for i in col if str(i) != "nan"]).strip("_")
        for col in df.columns.values
    ]

    if output_file is None:
        path = Path(input_file)
        output_file = path.with_name(f"{path.stem}_flattened.csv")

    df.to_csv(output_file, index=False)
    print(f"Flattened CSV saved to: {output_file}")


if __name__ == "__main__":
    args = parse_args()
    flatten_csv(args.input_file, args.output)
