import io
import pytest
import sqlite3
import pandas as pd
from core.ingestion import _check_file_size, _read_file, _clean_columns, load_file_to_sqlite, MAX_FILE_SIZE_BYTES

class MockUploadedFile:
    def __init__(self, name, content):
        self.name = name
        self.content = content
        self.seek_position = 0

    def getvalue(self):
        return self.content

    def read(self):
        return self.content

    def seek(self, pos):
        self.seek_position = pos

def test_check_file_size():
    # Safe size
    safe_file = MockUploadedFile("safe.csv", b"a" * 1024)
    _check_file_size(safe_file) # should not raise

    # Unsafe size
    unsafe_file = MockUploadedFile("large.csv", b"a" * (MAX_FILE_SIZE_BYTES + 1024))
    with pytest.raises(ValueError, match="Maximum allowed size is"):
        _check_file_size(unsafe_file)

def test_read_file_csv():
    csv_content = b"id,name\n1,Alice\n2,Bob"
    file = MockUploadedFile("data.csv", csv_content)
    df = _read_file(file)
    assert len(df) == 2
    assert "name" in df.columns

def test_read_file_unsupported():
    file = MockUploadedFile("data.txt", b"plain text")
    with pytest.raises(ValueError, match="Unsupported file type"):
        _read_file(file)

def test_clean_columns():
    df = pd.DataFrame(columns=["User ID", "Name!", "Age", "User ID"])
    cleaned_df = _clean_columns(df)
    
    assert list(cleaned_df.columns) == ["user_id", "name_", "age", "user_id_1"]

def test_load_file_to_sqlite():
    conn = sqlite3.connect(":memory:")
    csv_content = b"id,name\n1,Alice\n2,Bob"
    file = MockUploadedFile("data.csv", csv_content)
    
    df = load_file_to_sqlite(file, conn, table_name="test_table")
    
    # Check return type
    assert isinstance(df, pd.DataFrame)
    
    # Check that data was written to db
    db_df = pd.read_sql_query("SELECT * FROM test_table", conn)
    assert len(db_df) == 2
    assert "Alice" in db_df["name"].values
