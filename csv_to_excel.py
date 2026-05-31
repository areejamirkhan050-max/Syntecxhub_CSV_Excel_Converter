"""
CSV to Excel Converter
Syntecxhub Internship - Task 3, Project 1
"""

import argparse
import logging
import os
import sys
import pandas as pd
from datetime import datetime


def setup_logging(log_file="converter.log"):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)


def parse_date_columns(df):
    for col in df.columns:
        if df[col].dtype == object:
            try:
                converted = pd.to_datetime(df[col], infer_datetime_format=True, errors='raise')
                df[col] = converted
                logger.info(f"  Column '{col}' parsed as datetime.")
            except Exception:
                pass
    return df


def clean_data(df, fill_value="N/A"):
    original_shape = df.shape
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]
    if not missing_cols.empty:
        logger.info("  Missing values found and filled.")
        df.fillna(fill_value, inplace=True)
    else:
        logger.info("  No missing values found.")
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        df.drop_duplicates(inplace=True)
        logger.info(f"  Removed {duplicates} duplicate row(s).")
    logger.info(f"  Shape: {original_shape} -> {df.shape}")
    return df


def apply_renames(df, renames):
    valid_renames = {k: v for k, v in renames.items() if k in df.columns}
    if valid_renames:
        df.rename(columns=valid_renames, inplace=True)
    return df


def convert_csv_to_excel(input_path, output_path, fill_value="N/A", renames=None):
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: '{input_path}'")
        return False
    if not input_path.lower().endswith(".csv"):
        logger.error(f"Input file is not a CSV: '{input_path}'")
        return False
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not output_path.lower().endswith(".xlsx"):
        output_path += ".xlsx"
    try:
        logger.info(f"Reading CSV: '{input_path}'")
        df = pd.read_csv(input_path, encoding="utf-8-sig")
        logger.info(f"Loaded {len(df)} rows x {len(df.columns)} columns.")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(input_path, encoding="latin-1")
        except Exception as e:
            logger.error(f"Could not read CSV file: {e}")
            return False
    except pd.errors.EmptyDataError:
        logger.error("CSV file is empty.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

    logger.info("Cleaning data...")
    df = clean_data(df, fill_value=fill_value)
    logger.info("Detecting date columns...")
    df = parse_date_columns(df)
    if renames:
        df = apply_renames(df, renames)

    try:
        logger.info(f"Exporting to Excel: '{output_path}'")
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Cleaned Data")
            worksheet = writer.sheets["Cleaned Data"]
            for idx, col in enumerate(df.columns, 1):
                max_len = max(
                    df[col].astype(str).map(len).max() if len(df) > 0 else 0,
                    len(str(col))
                ) + 2
                max_len = min(max_len, 50)
                col_letter = worksheet.cell(row=1, column=idx).column_letter
                worksheet.column_dimensions[col_letter].width = max_len
        logger.info(f"Success! Excel saved at: '{output_path}'")
        return True
    except Exception as e:
        logger.error(f"Failed to write Excel file: {e}")
        return False


def parse_args():
    parser = argparse.ArgumentParser(
        description="CSV to Excel Converter | Syntecxhub Internship Task 3"
    )
    parser.add_argument("-i", "--input", required=True, help="Input CSV file path")
    parser.add_argument("-o", "--output", required=True, help="Output Excel file path")
    parser.add_argument("--fill", default="N/A", help="Fill value for missing cells")
    parser.add_argument("--rename", nargs="*", metavar="OLD=NEW", help="Rename columns")
    parser.add_argument("--log", default="converter.log", help="Log file path")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.log)
    logger.info("CSV to Excel Converter | Syntecxhub Task 3")
    renames = {}
    if args.rename:
        for item in args.rename:
            if "=" in item:
                old, new = item.split("=", 1)
                renames[old.strip()] = new.strip()
    success = convert_csv_to_excel(
        input_path=args.input,
        output_path=args.output,
        fill_value=args.fill,
        renames=renames if renames else None
    )
    if success:
        logger.info("Conversion completed successfully!")
        sys.exit(0)
    else:
        logger.error("Conversion failed.")
        sys.exit(1)