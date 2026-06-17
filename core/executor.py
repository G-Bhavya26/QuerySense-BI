import sqlite3
import logging
import pandas as pd
from typing import Tuple

from core.validator import validate_sql
from core.gemini import heal_sql

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


def execute_with_healing(
    sql: str,
    conn: sqlite3.Connection,
    schema_text: str,
) -> Tuple[pd.DataFrame, str, int]:
    """
    Executes a SQL query on a SQLite connection.
    If the query fails, it asks the AI to fix it and retries up to MAX_RETRIES times.

    Args:
        sql (str): The initial SQL query from the AI.
        conn (sqlite3.Connection): The active SQLite connection.
        schema_text (str): The schema string needed by the AI healer for context.

    Returns:
        Tuple of:
          - pd.DataFrame: The query result.
          - str: The final SQL that successfully ran.
          - int: How many attempts it took.

    Raises:
        RuntimeError: If all retry attempts fail.
    """
    current_sql = sql

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Step 1: Run through the security guard first
            clean_sql = validate_sql(current_sql)

            # Step 2: Run the SQL on the database
            result_df = pd.read_sql_query(clean_sql, conn)

            logger.info(f"Query succeeded on attempt {attempt}.")
            return result_df, clean_sql, attempt

        except Exception as error:
            error_message = str(error)
            logger.warning(f"Attempt {attempt} failed: {error_message}")

            # If this was the last attempt, give up and raise a clear error
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Query failed after {MAX_RETRIES} attempts. "
                    f"Last error: {error_message}\n"
                    f"Last SQL tried:\n{current_sql}"
                )

            # Otherwise, ask the AI to fix the broken SQL and try again
            logger.info("Asking AI to fix the broken SQL...")
            current_sql = heal_sql(
                broken_sql=current_sql,
                error_msg=error_message,
                schema_text=schema_text,
            )
