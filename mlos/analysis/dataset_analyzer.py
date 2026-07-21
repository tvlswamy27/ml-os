"""
Dataset Analyzer.

Analyzes datasets and extracts metadata.

Author: Vikram Tanakala
License: MIT
"""

from pathlib import Path

import pandas as pd

from mlos.domain.models.dataset import Dataset


class DatasetAnalyzer:
    """
    Analyzes machine learning datasets.
    """

    def analyze(
        self,
        dataset_path: str | Path,
    ) -> Dataset:

        dataframe = pd.read_csv(dataset_path)

        return Dataset(
            path=str(dataset_path),
            rows=len(dataframe),
            columns=len(dataframe.columns),
        )