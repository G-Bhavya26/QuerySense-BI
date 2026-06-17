import pytest
from unittest.mock import MagicMock
from core.gemini import _ask_gemini, generate_sql, generate_insight, heal_sql, _sql_cache

@pytest.fixture(autouse=True)
def clear_cache():
    # Clear the global cache before each test
    _sql_cache.clear()

def test_ask_gemini(mocker):
    # Mock genai.GenerativeModel
    mock_model_class = mocker.patch("core.gemini.genai.GenerativeModel")
    mock_model_instance = MagicMock()
    mock_model_class.return_value = mock_model_instance
    
    mock_response = MagicMock()
    mock_response.text = "Mocked LLM Response"
    mock_model_instance.generate_content.return_value = mock_response

    result = _ask_gemini("System Instruction", "User Prompt")
    
    assert result == "Mocked LLM Response"
    mock_model_class.assert_called_once()
    mock_model_instance.generate_content.assert_called_once_with("User Prompt")

def test_generate_sql_caching(mocker):
    # First call should hit the mock
    mock_ask = mocker.patch("core.gemini._ask_gemini", return_value="SELECT * FROM mock")
    
    schema = "Table: test"
    question = "Get all"
    
    # Run first time
    result1 = generate_sql(schema, question)
    assert result1 == "SELECT * FROM mock"
    assert mock_ask.call_count == 1
    
    # Run second time, should hit cache and NOT increment call_count
    result2 = generate_sql(schema, question)
    assert result2 == "SELECT * FROM mock"
    assert mock_ask.call_count == 1

def test_generate_insight(mocker):
    mock_json_response = '```json\n{"insight": "Test insight", "follow_ups": ["Q1"]}\n```'
    mocker.patch("core.gemini._ask_gemini", return_value=mock_json_response)
    
    result = generate_insight("question", "SELECT 1", "data")
    
    assert result["insight"] == "Test insight"
    assert "Q1" in result["follow_ups"]

def test_generate_insight_fallback(mocker):
    # Test when LLM returns invalid JSON
    mocker.patch("core.gemini._ask_gemini", return_value="This is not valid json")
    
    result = generate_insight("question", "SELECT 1", "data")
    
    assert result["insight"] == "This is not valid json"
    assert result["follow_ups"] == []

def test_heal_sql(mocker):
    mocker.patch("core.gemini._ask_gemini", return_value="SELECT FIXED SQL")
    
    result = heal_sql("SELECT BAD", "syntax error", "schema")
    assert result == "SELECT FIXED SQL"
