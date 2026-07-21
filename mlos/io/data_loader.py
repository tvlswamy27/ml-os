"""
Data Loader.

Responsible for loading datasets into pandas DataFrames.

Author: Vikram Tanakala
License: MIT
"""

from pathlib import Path

import pandas as pd


class DataLoader:
    """
    Loads datasets from disk.
    """

    def load(self, file_path: str | Path) -> pd.DataFrame:
        """
        Load a dataset from a file.

        Parameters
        ----------
        file_path : str | Path
            Path to the dataset.

        Returns
        -------
        pandas.DataFrame
            Loaded dataset.
        """

        file_path = Path(file_path)

        return pd.read_csv(file_path)