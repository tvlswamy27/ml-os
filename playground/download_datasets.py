"""
Downloader utility for ML-OS validation datasets.

Author: Antigravity
License: MIT
"""

import sys
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def validate_dataset(
    file_path: Path, meta: dict[str, Any], is_downsampled: bool = False
) -> None:
    """
    Validate dataset existence, shape, target column, and required columns.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file does not exist at: {file_path}")

    target = meta.get("target")
    # Check if headerless (target is a digit string)
    is_headerless = target is not None and target.isdigit()

    try:
        if is_headerless:
            df = pd.read_csv(file_path, header=None)
            df.columns = [str(i) for i in range(len(df.columns))]
        else:
            df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV dataset at {file_path}: {e}")

    # Validate target column existence
    if target:
        if target not in df.columns:
            raise ValueError(
                f"Target column '{target}' not found in dataset columns: {list(df.columns)}"
            )

    # Validate required columns
    required_cols = meta.get("required_columns", [])
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' missing from dataset.")

    # Validate column count
    expected_cols = meta.get("expected_columns")
    if expected_cols and len(df.columns) != expected_cols:
        raise ValueError(
            f"Column count mismatch. Expected {expected_cols}, but got {len(df.columns)} columns."
        )

    # Validate row count
    expected_rows = meta.get("expected_rows", 0)
    if not is_downsampled and expected_rows:
        # Check with a 5% row count tolerance for dynamic raw uploads
        row_diff = abs(len(df) - expected_rows)
        allowed_tolerance = int(expected_rows * 0.05)
        if row_diff > allowed_tolerance:
            raise ValueError(
                f"Row count mismatch. Expected {expected_rows} (+/- {allowed_tolerance}), but got {len(df)} rows."
            )
    elif is_downsampled:
        # Verify downsample limit was applied
        downsample_limit = meta.get("downsample", 0)
        if len(df) > downsample_limit:
            raise ValueError(
                f"Downsampling failed. Expected maximum {downsample_limit} rows, but got {len(df)} rows."
            )

    print(
        f"✓ Dataset {file_path.name} validated successfully ({len(df)} rows, {len(df.columns)} columns)."
    )


def download_datasets(
    manifest_path: str = "playground/datasets.yaml", data_dir: str = "playground/data"
) -> None:
    """
    Download and validate all datasets configured in datasets.yaml.
    """
    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        print(f"Error: Manifest file not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_file, "r") as f:
        config = yaml.safe_load(f)

    datasets = config.get("datasets", {})
    dest_folder = Path(data_dir)
    dest_folder.mkdir(parents=True, exist_ok=True)

    for name, meta in datasets.items():
        print(f"Processing dataset: {name} ...")
        url = meta.get("url")
        dest_file = dest_folder / f"{name}.csv"
        downsample_limit = meta.get("downsample")
        target = meta.get("target")

        # Check offline presence
        if dest_file.exists():
            print(
                f"  Dataset already exists locally at {dest_file}. Verifying integrity..."
            )
            try:
                validate_dataset(
                    dest_file, meta, is_downsampled=(downsample_limit is not None)
                )
                continue
            except Exception as e:
                print(f"  Existing file integrity check failed: {e}. Re-downloading...")
                dest_file.unlink(missing_ok=True)

        # Download from URL
        if not url:
            print(
                f"  Error: No download URL specified for dataset {name}.",
                file=sys.stderr,
            )
            continue

        try:
            print(f"  Downloading from {url} ...")
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req) as response:
                content = response.read().decode("utf-8")

            # Save full content temporary file to parse
            temp_file = dest_folder / f"{name}_temp.csv"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)

            # Read with pandas to handle headers/downsampling properly
            is_headerless = target is not None and target.isdigit()
            if is_headerless:
                df = pd.read_csv(temp_file, header=None)
            else:
                df = pd.read_csv(temp_file)

            temp_file.unlink(missing_ok=True)

            if downsample_limit and len(df) > downsample_limit:
                print(f"  Downsampling dataset to first {downsample_limit} rows...")
                df = df.iloc[:downsample_limit]

            # Save finalized file
            if is_headerless:
                df.to_csv(dest_file, index=False, header=False)
            else:
                df.to_csv(dest_file, index=False)

            validate_dataset(
                dest_file, meta, is_downsampled=(downsample_limit is not None)
            )
        except Exception as e:
            if dest_file.exists():
                print(
                    f"  Download failed, falling back to local file. Error: {e}",
                    file=sys.stderr,
                )
                try:
                    validate_dataset(
                        dest_file, meta, is_downsampled=(downsample_limit is not None)
                    )
                except Exception as val_err:
                    print(
                        f"  Local fallback file validation failed: {val_err}",
                        file=sys.stderr,
                    )
                    raise val_err
            else:
                print(
                    f"  Failed to download and no local fallback exists for {name}: {e}",
                    file=sys.stderr,
                )
                raise e


if __name__ == "__main__":
    download_datasets()
