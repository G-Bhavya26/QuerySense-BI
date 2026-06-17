import sqlite3
import streamlit as st
from typing import Optional


def init_session() -> None:
    """
    Initialises all session state keys with default values.
    Call this once at the top of app.py.
    Every key is only set if it doesn't already exist,
    so reruns don't wipe existing state.
    """
    defaults = {
        # The single shared in-memory SQLite connection
        "conn": None,
        # List of dicts: {"name": filename, "df": DataFrame}
        "datasets": [],
        # Conversation history: list of {"question": str, "sql": str, "result_summary": str}
        "chat_history": [],
        # Charts pinned to the dashboard: list of {"question": str, "fig": Figure}
        "dashboard": [],
        # Last query result — used by the Pin to Dashboard button
        "last_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Create the shared SQLite connection once and reuse it
    if st.session_state["conn"] is None:
        st.session_state["conn"] = sqlite3.connect(
            ":memory:", check_same_thread=False
        )


def get_conn() -> Optional[sqlite3.Connection]:
    """Returns the shared SQLite connection."""
    return st.session_state.get("conn")


def add_dataset(name: str, df) -> None:
    """Registers a newly loaded dataset. Replaces if same name exists."""
    datasets = st.session_state["datasets"]
    # Remove old entry with same name if it exists
    st.session_state["datasets"] = [d for d in datasets if d["name"] != name]
    st.session_state["datasets"].append({"name": name, "df": df})


def get_datasets() -> list:
    """Returns all loaded datasets."""
    return st.session_state.get("datasets", [])


def add_to_history(question: str, sql: str, result_summary: str) -> None:
    """Adds a completed Q&A turn to the conversation history."""
    st.session_state["chat_history"].append({
        "question": question,
        "sql": sql,
        "result_summary": result_summary,
    })


def get_history() -> list:
    """Returns full conversation history."""
    return st.session_state.get("chat_history", [])


def pin_chart(question: str, fig) -> None:
    """Pins a chart to the dashboard."""
    st.session_state["dashboard"].append({
        "question": question,
        "fig": fig,
    })


def get_dashboard() -> list:
    """Returns all pinned dashboard charts."""
    return st.session_state.get("dashboard", [])


def clear_session() -> None:
    """Wipes the entire session and starts fresh."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session()
