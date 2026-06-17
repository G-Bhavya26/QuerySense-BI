# QuerySense BI Engine

QuerySense is a natural language-driven Business Intelligence (BI) engine that allows users to query their datasets using plain English. It leverages Google Gemini to generate SQL queries, self-heal broken queries, and provide AI-powered business insights.

## Core Architecture

The project is structured with a modular architecture:

- **Ingestion Module (`core/ingestion.py`)**: Handles secure file uploads with robust error handling. Supports CSV, TSV, Excel, JSON, and Parquet. Normalizes column names and loads data into a local SQLite database.
- **Schema Module (`core/schema.py`)**: Extracts table structure (column names and types) from SQLite and formats it for the AI prompt.
- **NLP Interface (`core/gemini.py`)**: Manages text-to-SQL translation. Features query generation, insight summarization, self-healing retry logic, and in-memory caching.
- **Query Validator (`core/validator.py`)**: Strict security layer. Blocks 15+ dangerous keywords (`DROP`, `DELETE`, `ATTACH`, etc.) and enforces SELECT-only queries.
- **Query Executor (`core/executor.py`)**: Runs SQL with a 3-attempt self-healing loop. On failure, sends the error back to Gemini for automatic correction.
- **Anomaly Detector (`eda/analyzer.py`)**: Z-score based statistical anomaly detection with configurable threshold (default 2.5).

## Technologies Used

- **Web Interface**: Streamlit
- **Data Handling**: Pandas, NumPy, PyArrow, OpenPyXL, SQLite
- **AI Engine**: Google Gemini 2.5 Flash
- **Statistics**: SciPy (Z-score)
- **Visualisation**: Plotly
- **PDF Export**: ReportLab
- **Environment Management**: Python-dotenv

## Getting Started

1. Clone the repository
2. Install requirements: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your `GEMINI_API_KEY`
4. Run the app: `streamlit run dashboard/app.py`

## Features

- Multi-format data ingestion (CSV, TSV, Excel, JSON, Parquet)
- Schema extraction and column normalization
- Natural language to SQL translation using Google Gemini
- Self-healing SQL with 3-attempt retry loop
- Query result caching (SHA-256 fingerprint)
- Z-score anomaly detection with interactive scatter plot
- Smart auto-chart selection (KPI card, bar, line, histogram, table)
- Pinned charts dashboard
- Automated PDF report generation via ReportLab
- Multi-turn conversation history (follow-up questions)
