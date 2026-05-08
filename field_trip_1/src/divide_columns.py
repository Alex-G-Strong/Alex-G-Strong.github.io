"""
Divide one CSV column by another and write the result.

Usage:
    python divide_columns.py <csv_file> <numerator_col> <denominator_col> [options]

Examples:
    python divide_columns.py data.csv soil_thickness_cm elevation_m
    python divide_columns.py data.csv A B --output-col A_over_B --output result.csv
"""

import argparse
import pandas as pd
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Divide two columns in a CSV file.")
    parser.add_argument("csv",         help="Path to the input CSV file")
    parser.add_argument("numerator",   help="Column name for the numerator")
    parser.add_argument("denominator", help="Column name for the denominator")
    parser.add_argument("--output-col", default="result",
                        help="Name for the result column (default: 'result')")
    parser.add_argument("--output", default=None,
                        help="Path for output CSV (default: overwrites input file)")
    parser.add_argument("--abs-denominator", action="store_true",
                        help="Use the absolute value of the denominator column before dividing")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)

    if args.numerator not in df.columns:
        raise ValueError(f"Column '{args.numerator}' not found. Available: {list(df.columns)}")
    if args.denominator not in df.columns:
        raise ValueError(f"Column '{args.denominator}' not found. Available: {list(df.columns)}")

    denom = df[args.denominator].abs() if args.abs_denominator else df[args.denominator]
    df[args.output_col] = df[args.numerator] / denom

    out_path = args.output or args.csv
    df.to_csv(out_path, index=False)

    print(f"Result column '{args.output_col}' written to {out_path}")
    print(df[[args.numerator, args.denominator, args.output_col]].to_string(index=False))


if __name__ == "__main__":
    main()
