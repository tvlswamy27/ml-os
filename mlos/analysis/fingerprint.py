"""
Dataset Fingerprinting Engine for ML-OS.

Generates deterministic SHA-256 fingerprints based on dataset schema, features, target,
shapes, and missing statistics.

Author: Antigravity
License: MIT
"""

import hashlib
import json

import pandas as pd


class DatasetFingerprinter:
    """
    Generates deterministic dataset fingerprints for experiment tracking and caching.
    """

    def compute_fingerprint(
        self, dataframe: pd.DataFrame, target_column: str | None = None
    ) -> str:
        """
        Compute a SHA-256 fingerprint hex digest for a dataset.
        """
        schema_info = {
            "columns": list(dataframe.columns),
            "dtypes": [str(dt) for dt in dataframe.dtypes],
            "shape": list(dataframe.shape),
            "target": target_column,
            "null_counts": dataframe.isnull().sum().to_dict(),
        }

        # Calculate sample checksum hash of head & tail rows
        sample_str = dataframe.head(10).to_json(orient="split") + dataframe.tail(
            10
        ).to_json(orient="split")

        payload = {
            "schema": schema_info,
            "sample": sample_str,
        }

        json_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(json_bytes).hexdigest()
