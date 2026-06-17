import io
import re
import sqlite3
import pandas as pd
from typing import Any
import logging

logger = logging.getLogger(__name__)


MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def _check_file_size(uploaded_file: Any) -> None:
    """
    Checks if the uploaded file exceeds the maximum allowed size.

    Args:
        uploaded_file (Any): The file-like object uploaded by the user.

    Raises:
        ValueError: If the file size exceeds MAX_FILE_SIZE_BYTES.
    """
    size = len(uploaded_file.getvalue())
    if size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File is {size / 1024 / 1024:.1f} MB. "
            f"Maximum allowed size is {MAX_FILE_SIZE_MB} MB."
        )


def _read_file(uploaded_file: Any) -> pd.DataFrame:
    """
    Reads an uploaded file (CSV, TSV, Excel, JSON, Parquet) into a Pandas DataFrame.
    Handles multiple text encodings for CSVs to prevent decode errors.

    Args:
        uploaded_file (Any): The file-like object uploaded by the user.

    Returns:
        pd.DataFrame: The loaded data.

    Raises:
        ValueError: If the file format is unsupported or the file cannot be read.
    """
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    uploaded_file.seek(0)

    if name.endswith(".csv") or name.endswith(".tsv"):
        sep = "\t" if name.endswith(".tsv") else ","
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(io.BytesIO(raw), encoding=encoding, sep=sep)
                return df
            except UnicodeDecodeError:
                continue
        raise ValueError("Could not read the file. Please make sure it is a valid CSV.")

    elif name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(io.BytesIO(raw))

    elif name.endswith(".json"):
        return pd.read_json(io.BytesIO(raw))

    elif name.endswith(".parquet"):
        return pd.read_parquet(io.BytesIO(raw))

    else:
        raise ValueError(
            "Unsupported file type. Please upload a CSV, TSV, Excel, JSON, or Parquet file."
        )


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes DataFrame column names by converting to lowercase, replacing non-alphanumeric
    characters with underscores, and ensuring uniqueness.

    Args:
        df (pd.DataFrame): The DataFrame with raw column names.

    Returns:
        pd.DataFrame: The DataFrame with cleaned, unique column names.
    """
    df.columns = [
        re.sub(r"[^a-zA-Z0-9_]", "_", col.strip().lower()) for col in df.columns
    ]

    seen = {}
    new_columns = []
    for col in df.columns:
        if col in seen:
            seen[col] += 1
            new_columns.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_columns.append(col)
    df.columns = new_columns

    return df


def load_file_to_sqlite(
    uploaded_file: Any, conn: sqlite3.Connection, table_name: str = "data"
) -> pd.DataFrame:
    """
    Main orchestration function to validate, load, clean, and write an uploaded file
    into a local SQLite database.

    Args:
        uploaded_file (Any): The file-like object uploaded by the user.
        conn (sqlite3.Connection): The target SQLite database connection.
        table_name (str, optional): The name of the table to create/replace. Defaults to "data".

    Returns:
        pd.DataFrame: The processed DataFrame that was written to the database.
    """
    _check_file_size(uploaded_file)

    df = _read_file(uploaded_file)
    df = _clean_columns(df)

    safe_table_name = re.sub(r"[^a-zA-Z0-9_]", "_", table_name.lower())

    df.to_sql(safe_table_name, conn, if_exists="replace", index=False)

    return df
