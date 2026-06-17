import pytest
from core.validator import strip_markdown, validate_sql

def test_strip_markdown():
    assert strip_markdown("```sql\nSELECT * FROM data;\n```") == "SELECT * FROM data;"
    assert strip_markdown("```\nSELECT * FROM data;\n```") == "SELECT * FROM data;"
    assert strip_markdown("SELECT * FROM data;") == "SELECT * FROM data;"
    assert strip_markdown("  ```sql\nSELECT * FROM data;``` ") == "SELECT * FROM data;"

def test_validate_sql_success():
    assert validate_sql("SELECT * FROM data") == "SELECT * FROM data"
    assert validate_sql("WITH cte AS (SELECT 1) SELECT * FROM cte") == "WITH cte AS (SELECT 1) SELECT * FROM cte"
    assert validate_sql("select id, name from users") == "select id, name from users"

def test_validate_sql_empty():
    with pytest.raises(ValueError, match="empty query"):
        validate_sql("")
    with pytest.raises(ValueError, match="empty query"):
        validate_sql("   ")

def test_validate_sql_invalid_start():
    with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
        validate_sql("UPDATE users SET name = 'test'")
    with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
        validate_sql("DELETE FROM users")

def test_validate_sql_dangerous_keywords():
    with pytest.raises(ValueError, match="Dangerous keyword detected: 'DROP'"):
        validate_sql("SELECT * FROM data; DROP TABLE data;")
    
    with pytest.raises(ValueError, match="Dangerous keyword detected: 'DELETE'"):
        validate_sql("SELECT * FROM data WHERE id = 1; DELETE FROM users")

def test_validate_sql_allows_safe_words_containing_dangerous_substrings():
    # 'drop_off' contains 'drop' but is safe because of word boundaries
    assert validate_sql("SELECT drop_off_location FROM trips") == "SELECT drop_off_location FROM trips"
