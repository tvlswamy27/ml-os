"""
Dataset Analyzer.

Analyzes pandas DataFrames and extracts dataset metadata.

Author: Vikram Tanakala
License: MIT
"""

import pandas as pd

from mlos.domain.models.dataset import Dataset


class DatasetAnalyzer:
    """
    Analyzes datasets and extracts useful metadata.
    """

    def analyze(self, dataframe: pd.DataFrame) -> Dataset:
        """
        Analyze a dataset and return its metadata.

        Parameters
        ----------
        dataframe : pandas.DataFrame
            Dataset to analyze.

        Returns
        -------
        Dataset
            Extracted dataset metadata.
        """

        return Dataset(
            path="",
            rows=self._get_row_count(dataframe),
            columns=self._get_column_count(dataframe),
            numerical_columns=self._get_numerical_columns(dataframe),
            categorical_columns=self._get_categorical_columns(dataframe),
            missing_values=self._get_missing_values(dataframe),
        )

    def _get_row_count(self, dataframe: pd.DataFrame) -> int:
        """
        Count the total number of rows in the dataset.

        Parameters
        ----------
        dataframe : pandas.DataFrame
            Dataset to inspect.

        Returns
        -------
        int
            Total number of rows.
        """

        return len(dataframe)

    def _get_column_count(self, dataframe: pd.DataFrame) -> int:
        """
        Count the total number of columns in the dataset.

        Parameters
        ----------
        dataframe : pandas.DataFrame
            Dataset to inspect.

        Returns
        -------
        int
            Total number of columns.
        """

        return len(dataframe.columns)

    def _get_numerical_columns(
        self,
        dataframe: pd.DataFrame,
    ) -> list[str]:
        """
        Identify all numerical columns.

        Parameters
        ----------
        dataframe : pandas.DataFrame
            Dataset to inspect.

        Returns
        -------
        list[str]
            List of numerical column names.
        """

        return dataframe.select_dtypes(
            include="number"
        ).columns.tolist()

    def _get_categorical_columns(
        self,
        dataframe: pd.DataFrame,
    ) -> list[str]:
        """
        Identify all categorical columns.

        Parameters
        ----------
        dataframe : pandas.DataFrame
            Dataset to inspect.

        Returns
        -------
        list[str]
            List of categorical column names.
        """

        return dataframe.select_dtypes(
            exclude="number"
        ).columns.tolist()

    def _get_missing_values(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, int]:
        """
        Count missing values for every column.

        Parameters
        ----------
        dataframe : pandas.DataFrame
            Dataset to inspect.

        Returns
        -------
        dict[str, int]
            Dictionary mapping each column name to its
            number of missing values.
        """

        return dataframe.isnull().sum().to_dict()