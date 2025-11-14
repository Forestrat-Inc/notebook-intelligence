"""
Utility helpers shared across Forestrat notebooks.

These functions provide quick analytical summaries and common preprocessing
steps so every notebook can focus on the business logic instead of boilerplate.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

__all__ = [
    "ensure_datetime",
    "describe_dataframe",
    "profile_dataframe",
    "detect_outliers_iqr",
    "top_categorical_values",
    "normalize_column",
    "zscore",
]


def ensure_datetime(df: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    """Return a copy of *df* with the requested columns coerced to datetimes."""
    result = df.copy()
    for column in columns:
        if column not in result.columns:
            continue
        result[column] = pd.to_datetime(result[column], errors="coerce")
    return result


def describe_dataframe(df: pd.DataFrame, include_categorical: bool = True) -> pd.DataFrame:
    """Return a combined descriptive summary for numeric (and optional categorical) columns."""
    numeric_summary = df.describe(include=[np.number], datetime_is_numeric=True).transpose()
    if include_categorical:
        categorical_summary = (
            df.describe(include=["object", "category"])
            .transpose()
            .rename(columns={"top": "mode", "freq": "mode_freq"})
        )
        return (
            pd.concat([numeric_summary, categorical_summary], axis=0, sort=False)
            .fillna("")
        )
    return numeric_summary.fillna("")


def profile_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Produce a compact profile containing null counts and cardinality."""
    if df.empty:
        return pd.DataFrame(
            columns=["dtype", "non_null", "nulls", "null_pct", "unique"]
        )
    profile = pd.DataFrame(
        {
            "dtype": df.dtypes,
            "non_null": df.count(),
            "nulls": df.isna().sum(),
            "null_pct": (df.isna().sum() / len(df)).round(4),
            "unique": df.nunique(dropna=True),
        }
    )
    return profile.sort_index()


def detect_outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return the rows where *column* falls outside the IQR fence."""
    if column not in df.columns:
        raise KeyError(f"Column '{column}' is not present in the DataFrame.")
    series = pd.to_numeric(df[column], errors="coerce")
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    mask = (series < lower) | (series > upper)
    return df.loc[mask].copy()


def top_categorical_values(df: pd.DataFrame, column: str, limit: int = 10) -> pd.DataFrame:
    """Return the most frequent values for a categorical column with percentages."""
    if column not in df.columns:
        raise KeyError(f"Column '{column}' is not present in the DataFrame.")
    counts = df[column].value_counts(dropna=False).head(limit)
    percentages = (counts / len(df)).round(4)
    return pd.DataFrame(
        {
            "value": counts.index.to_list(),
            "count": counts.values,
            "pct": percentages.values,
        }
    )


def normalize_column(df: pd.DataFrame, column: str) -> pd.Series:
    """Return a min-max normalized Series for *column*."""
    series = pd.to_numeric(df[column], errors="coerce")
    min_val = series.min()
    max_val = series.max()
    if pd.isna(min_val) or pd.isna(max_val) or min_val == max_val:
        return pd.Series([np.nan] * len(series), index=df.index, name=column)
    normalized = (series - min_val) / (max_val - min_val)
    return normalized.rename(f"{column}_normalized")


def zscore(df: pd.DataFrame, column: str) -> pd.Series:
    """Return z-scores for *column* (population standard deviation)."""
    series = pd.to_numeric(df[column], errors="coerce")
    mean = series.mean()
    std = series.std(ddof=0)
    if pd.isna(std) or std == 0:
        return pd.Series([np.nan] * len(series), index=df.index, name=column)
    scores = (series - mean) / std
    return scores.rename(f"{column}_zscore")
