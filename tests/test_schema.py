import sqlite3
import pandas as pd
from core.schema import get_schema, schema_to_string, get_sample_rows

def setup_test_db():
    conn = sqlite3.connect(":memory:")
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
    df.to_sql("users", conn, index=False)
    return conn

def test_get_schema():
    conn = setup_test_db()
    schema = get_schema(conn)
    
    assert "users" in schema
    assert "id" in schema["users"]
    assert "name" in schema["users"]
    
    # Check that it identifies types properly (sqlite might say INTEGER/TEXT or BIGINT/TEXT depending on pandas)
    assert schema["users"]["id"].upper() in ("INTEGER", "BIGINT")
    assert schema["users"]["name"].upper() == "TEXT"

def test_schema_to_string():
    schema = {
        "users": {"id": "INTEGER", "name": "TEXT"}
    }
    result = schema_to_string(schema)
    expected = "Table: users\n  - id (INTEGER)\n  - name (TEXT)"
    assert result == expected

def test_get_sample_rows():
    conn = setup_test_db()
    result = get_sample_rows(conn, "users", n=2)
    
    # It returns a markdown table string
    assert "id" in result
    assert "name" in result
    assert "Alice" in result
    assert "Bob" in result
    assert "Charlie" not in result # because n=2

def test_get_sample_rows_invalid_table():
    conn = setup_test_db()
    result = get_sample_rows(conn, "non_existent_table")
    assert result == ""
