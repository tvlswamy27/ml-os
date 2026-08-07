"""
Dataset Analyzer.

Analyzes pandas DataFrames and extracts comprehensive dataset metadata & intelligence.

Author: Vikram Tanakala & Antigravity
License: MIT
"""

import pandas as pd

from mlos.domain.models.dataset import Dataset


class DatasetAnalyzer:
    """
    Analyzes datasets and extracts useful metadata and intelligence.
    """

    def analyze(self, dataframe: pd.DataFrame, target: str | None = None) -> Dataset:
        """
        Analyze a dataset and return its metadata and problem type intelligence.
        """
        rows = len(dataframe)
        cols = len(dataframe.columns)
        num_cols = dataframe.select_dtypes(include="number").columns.tolist()
        cat_cols = dataframe.select_dtypes(exclude="number").columns.tolist()

        missing_vals = dataframe.isnull().sum().to_dict()
        missing_pcts = {
            col: float(round(val / max(rows, 1) * 100, 2))
            for col, val in missing_vals.items()
        }
        unique_vals = {
            col: int(dataframe[col].nunique(dropna=True)) for col in dataframe.columns
        }
        duplicate_count = int(dataframe.duplicated().sum())

        # Sub-type column classifications
        datetime_cols = self._detect_datetime_columns(dataframe)
        id_cols = self._detect_id_columns(dataframe, unique_vals, rows)
        text_cols = self._detect_text_columns(dataframe, cat_cols)
        high_card_cols = [
            c
            for c in cat_cols
            if unique_vals.get(c, 0) > 50 and c not in text_cols and c not in id_cols
        ]
        ordinal_cols = self._detect_ordinal_columns(
            dataframe, cat_cols, num_cols, unique_vals
        )
        constant_cols = [c for c, u in unique_vals.items() if u <= 1]
        nzv_cols = self._detect_near_zero_variance(dataframe, num_cols)

        skewed_cols = self._detect_skewness(dataframe, num_cols)
        outlier_counts = self._detect_outliers(dataframe, num_cols)

        # Target and leakage detection
        target_col = target if target and target in dataframe.columns else None
        leakage_cols = (
            self._detect_leakage(dataframe, target_col, num_cols) if target_col else []
        )

        # Problem type inference
        problem_type, imbalance_ratio = self._infer_problem_type(
            dataframe, target_col, datetime_cols, text_cols
        )

        column_types = {}
        for col in dataframe.columns:
            if col in datetime_cols:
                column_types[col] = "datetime"
            elif col in text_cols:
                column_types[col] = "text"
            elif col in id_cols:
                column_types[col] = "id"
            elif col in num_cols:
                column_types[col] = "numerical"
            else:
                column_types[col] = "categorical"

        return Dataset(
            path="",
            rows=rows,
            columns=cols,
            target=target_col,
            problem_type=problem_type,
            numerical_columns=num_cols,
            categorical_columns=cat_cols,
            missing_values={k: int(v) for k, v in missing_vals.items()},
            duplicate_rows=duplicate_count,
            unique_values=unique_vals,
            missing_percentages=missing_pcts,
            column_types=column_types,
            ordinal_columns=ordinal_cols,
            text_columns=text_cols,
            datetime_columns=datetime_cols,
            id_columns=id_cols,
            leakage_columns=leakage_cols,
            high_cardinality_columns=high_card_cols,
            constant_columns=constant_cols,
            near_zero_variance_columns=nzv_cols,
            skewed_columns=skewed_cols,
            imbalance_ratio=imbalance_ratio,
            outliers_count=outlier_counts,
        )

    def _detect_datetime_columns(self, df: pd.DataFrame) -> list[str]:
        datetime_cols = []
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                datetime_cols.append(col)
            elif df[col].dtype == "object":
                # Quick check sample
                sample = df[col].dropna().head(10)
                if len(sample) > 0:
                    try:
                        pd.to_datetime(sample, errors="raise")
                        datetime_cols.append(col)
                    except (ValueError, TypeError):
                        pass
        return datetime_cols

    def _detect_id_columns(
        self, df: pd.DataFrame, unique_vals: dict[str, int], rows: int
    ) -> list[str]:
        id_cols = []
        for col in df.columns:
            name_lower = col.lower()
            u_count = unique_vals.get(col, 0)
            if (
                ("id" in name_lower or "key" in name_lower or "guid" in name_lower)
                and u_count > 0.8 * rows
                or u_count == rows
                and df[col].dtype == "object"
            ):
                id_cols.append(col)
        return id_cols

    def _detect_text_columns(self, df: pd.DataFrame, cat_cols: list[str]) -> list[str]:
        text_cols = []
        for col in cat_cols:
            sample = df[col].dropna().astype(str).head(20)
            if len(sample) > 0 and sample.str.len().mean() > 50:
                text_cols.append(col)
        return text_cols

    def _detect_ordinal_columns(
        self,
        df: pd.DataFrame,
        cat_cols: list[str],
        num_cols: list[str],
        unique_vals: dict[str, int],
    ) -> list[str]:
        ordinal = []
        for col in cat_cols + num_cols:
            name_lower = col.lower()
            if any(
                k in name_lower for k in ["rank", "grade", "level", "tier", "stage"]
            ) or (
                col in num_cols
                and 2 < unique_vals.get(col, 0) <= 10
                and (df[col].dropna() % 1 == 0).all()
            ):
                ordinal.append(col)
        return list(set(ordinal))

    def _detect_near_zero_variance(
        self, df: pd.DataFrame, num_cols: list[str]
    ) -> list[str]:
        nzv = []
        for col in num_cols:
            var = df[col].var()
            if pd.notnull(var) and var < 1e-4:
                nzv.append(col)
        return nzv

    def _detect_skewness(
        self, df: pd.DataFrame, num_cols: list[str]
    ) -> dict[str, float]:
        skewed = {}
        for col in num_cols:
            try:
                sk = float(df[col].skew())
                if pd.notnull(sk) and (sk > 1.5 or sk < -1.5):
                    skewed[col] = round(sk, 2)
            except Exception:
                pass
        return skewed

    def _detect_outliers(self, df: pd.DataFrame, num_cols: list[str]) -> dict[str, int]:
        outliers = {}
        for col in num_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                count = int(((df[col] < lower) | (df[col] > upper)).sum())
                if count > 0:
                    outliers[col] = count
        return outliers

    def _detect_leakage(
        self, df: pd.DataFrame, target: str, num_cols: list[str]
    ) -> list[str]:
        leakage: list[str] = []
        if target not in num_cols:
            return leakage
        target_series = df[target]
        for col in num_cols:
            if col == target:
                continue
            try:
                corr = abs(df[col].corr(target_series))
                if pd.notnull(corr) and corr > 0.98:
                    leakage.append(col)
            except Exception:
                pass
        return leakage

    def _infer_problem_type(
        self,
        df: pd.DataFrame,
        target: str | None,
        datetime_cols: list[str],
        text_cols: list[str],
    ) -> tuple[str, float | None]:
        if target is None:
            # Check for recommendation dataset structure (user_id, item_id, rating)
            cols_lower = [c.lower() for c in df.columns]
            if any("user" in c for c in cols_lower) and any(
                "item" in c or "product" in c for c in cols_lower
            ):
                return "recommendation", None
            return "clustering", None

        target_series = df[target].dropna()
        n_unique = target_series.nunique()
        imbalance_ratio = None

        if (
            datetime_cols
            and len(datetime_cols) > 0
            and pd.api.types.is_numeric_dtype(target_series)
        ):
            return "forecasting", None

        if len(text_cols) > 0 and target in text_cols:
            return "nlp", None

        if pd.api.types.is_numeric_dtype(target_series):
            if n_unique > 20:
                return "regression", None

        if n_unique == 2:
            val_counts = target_series.value_counts()
            if len(val_counts) == 2:
                imbalance_ratio = round(
                    float(val_counts.iloc[0] / max(val_counts.iloc[1], 1)), 2
                )
                if val_counts.iloc[1] / len(target_series) < 0.01:
                    return "anomaly_detection", imbalance_ratio
            return "binary_classification", imbalance_ratio

        if 2 < n_unique <= 20:
            val_counts = target_series.value_counts()
            imbalance_ratio = round(
                float(val_counts.iloc[0] / max(val_counts.iloc[-1], 1)), 2
            )
            return "multiclass_classification", imbalance_ratio

        return "regression", None
