import re
import logging

logger = logging.getLogger(__name__)


# Words that are allowed to start a query
ALLOWED_START_WORDS = {"select", "with"}

# Words that are dangerous and never allowed anywhere in the query
BLOCKED_KEYWORDS = {
    "drop",
    "delete",
    "insert",
    "update",
    "alter",
    "truncate",
    "create",
    "replace",
    "pragma",
    "attach",
    "detach",
    "vacuum",
    "reindex",
    "load_extension",
}


def strip_markdown(sql: str) -> str:
    """
    Strips markdown formatting blocks from a SQL string.

    Args:
        sql (str): The raw SQL string potentially containing markdown blocks (e.g. ```sql).

    Returns:
        str: The cleaned SQL string without markdown formatting.
    """
    # Strip markdown block formatting
    sql = re.sub(r"^```(?:sql)?\s*", "", sql.strip(), flags=re.IGNORECASE)
    sql = re.sub(r"\s*```$", "", sql.strip())
    return sql.strip()


def validate_sql(sql: str) -> str:
    """
    Validates a SQL query to ensure it is secure and only performs READ operations.

    It strips any markdown, ensures the query starts with an allowed word
    (e.g., SELECT, WITH), and checks that no destructive keywords (e.g., DROP, DELETE)
    are present in the query.

    Args:
        sql (str): The generated SQL query to validate.

    Returns:
        str: The validated and cleaned SQL query.

    Raises:
        ValueError: If the query is empty, unparseable, starts with an invalid word,
                    or contains a dangerous keyword.
    """
    # 1. Strip the markdown formatting
    sql = strip_markdown(sql)

    if not sql:
        raise ValueError("The generated query was empty.")

    # 2. Check the very first word
    # This regex looks for the first actual word in the text
    match = re.match(r"^\s*(\w+)", sql)
    if not match:
        raise ValueError("Could not understand the SQL command.")

    first_word = match.group(1).lower()

    if first_word not in ALLOWED_START_WORDS:
        raise ValueError(
            f"Only SELECT queries are allowed. Your query started with: '{first_word.upper()}'"
        )

    # 3. Check for dangerous words anywhere in the query
    sql_lower = sql.lower()
    for bad_word in BLOCKED_KEYWORDS:
        # We look for the exact bad word with boundaries (\b) so we don't accidentally
        # block a column named "drop_off_location"
        pattern = rf"\b{bad_word}\b"
        if re.search(pattern, sql_lower):
            raise ValueError(
                f"Dangerous keyword detected: '{bad_word.upper()}'. Not allowed!"
            )

    # If it passes all tests, return the clean, safe SQL
    return sql
