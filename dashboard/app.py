import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from scipy import stats
from dotenv import load_dotenv

load_dotenv()

from core.ingestion import load_file_to_sqlite
from core.schema import get_schema, schema_to_string, get_sample_rows
from core.validator import validate_sql
from core.gemini import generate_sql, generate_insight
from core.executor import execute_with_healing
from eda.analyzer import detect_anomalies
from export.report_generator import create_pdf_report
from utils.session import (
    init_session, get_conn, add_dataset, get_history, add_to_history,
    pin_chart, get_dashboard, clear_session
)
from utils.chart_selector import auto_chart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuerySense BI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Premium CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp {
        background: radial-gradient(circle at top left, #1E1E2E, #12121A);
        color: #E2E2E2;
    }

    h1, h2, h3 {
        color: #A9A9FF !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }

    [data-testid="stSidebar"] {
        background: rgba(30, 30, 46, 0.4);
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease-in-out;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: rgba(169, 169, 255, 0.3);
    }

    .stButton>button {
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(118, 75, 162, 0.4);
        color: white;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.05);
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(169, 169, 255, 0.15);
        border-bottom: 2px solid #A9A9FF;
    }
</style>
""", unsafe_allow_html=True)

# ── Session init ──────────────────────────────────────────────────────────────
init_session()
conn = get_conn()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 QuerySense BI")
    st.markdown("---")

    st.header("1. Upload Data")
    uploaded_file = st.file_uploader(
        "CSV, Excel, JSON, or Parquet",
        type=["csv", "xlsx", "xls", "json", "parquet", "tsv"]
    )

    if uploaded_file is not None:
        file_key = f"loaded_{uploaded_file.name}"
        if file_key not in st.session_state:
            try:
                with st.spinner("Loading and cleaning data..."):
                    table_name = os.path.splitext(uploaded_file.name)[0]
                    df = load_file_to_sqlite(uploaded_file, conn, table_name=table_name)
                    add_dataset(uploaded_file.name, df)
                    schema_dict = get_schema(conn)
                    st.session_state["schema_text"] = schema_to_string(schema_dict)
                    st.session_state[file_key] = True
                st.success(f"Loaded: **{uploaded_file.name}**")
            except Exception as e:
                st.error(f"Upload failed: {e}")

    datasets = get_history()
    if st.button("Reset Session", type="secondary"):
        clear_session()
        st.rerun()

    st.markdown("---")
    st.caption("QuerySense BI Engine v1.0")

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("📊 QuerySense BI Engine")
st.markdown("Upload your data and talk to it using natural language.")

schema_text = st.session_state.get("schema_text", "")
current_df = None

# Use the most recently loaded dataset
from utils.session import get_datasets
datasets_list = get_datasets()
if datasets_list:
    current_df = datasets_list[-1]["df"]

if current_df is not None:

    # ── Dataset KPI cards ─────────────────────────────────────────────────────
    st.markdown("### Dataset Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Rows", f"{len(current_df):,}")
    c2.metric("Total Columns", len(current_df.columns))
    c3.metric("Numeric Columns", len(current_df.select_dtypes(include=["number"]).columns))
    c4.metric("Text Columns", len(current_df.select_dtypes(include=["object", "category"]).columns))

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "💬 Query Engine",
        "📈 Anomaly Detection",
        "📊 Dashboard",
        "📄 Export",
    ])

    # ── TAB 1: Query Engine ───────────────────────────────────────────────────
    with tab1:
        st.subheader("Ask a Question")

        question = st.text_input(
            "Type your question in plain English",
            placeholder="e.g. What is the total revenue by product?"
        )

        run_clicked = st.button("▶ Run Query", key="run_query", type="primary")

        if run_clicked and question.strip():
            with st.spinner("Generating SQL and running query..."):
                try:
                    history = get_history()
                    raw_sql = generate_sql(schema_text, question, history=history)

                    result_df, final_sql, attempts = execute_with_healing(
                        sql=raw_sql,
                        conn=conn,
                        schema_text=schema_text,
                    )

                    fig, chart_type = auto_chart(result_df, question=question)

                    insights = {}
                    if not result_df.empty:
                        data_str = result_df.head(10).to_markdown(index=False)
                        insights = generate_insight(question, final_sql, data_str)
                        add_to_history(
                            question=question,
                            sql=final_sql,
                            result_summary=result_df.head(3).to_markdown(index=False)
                        )

                    # Persist full result in session so it survives reruns
                    st.session_state["last_result"] = {
                        "question": question,
                        "sql": final_sql,
                        "attempts": attempts,
                        "df": result_df,
                        "fig": fig,
                        "insights": insights,
                    }

                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state["last_result"] = None

        elif run_clicked:
            st.warning("Please type a question first.")

        # Always re-render last result from session state
        last = st.session_state.get("last_result")
        if last:
            if last["attempts"] > 1:
                st.warning(f"SQL was auto-healed after {last['attempts']} attempt(s).")

            st.code(last["sql"], language="sql")
            st.dataframe(last["df"], use_container_width=True)
            st.plotly_chart(last["fig"], use_container_width=True, key="query_chart")

            insights = last["insights"]
            if insights.get("insight"):
                st.info(f"**AI Insight:** {insights['insight']}")

            follow_ups = insights.get("follow_ups", [])
            if follow_ups:
                st.markdown("**Suggested follow-up questions:**")
                for fq in follow_ups:
                    st.markdown(f"- {fq}")

            st.divider()
            if st.button("📌 Pin this chart to Dashboard", key="pin_btn"):
                pin_chart(last["question"], last["fig"])
                st.success("✅ Chart pinned! Go to the 📊 Dashboard tab to see it.")


    # ── TAB 2: Anomaly Detection ──────────────────────────────────────────────
    with tab2:
        st.subheader("Automated Anomaly Detection")
        st.markdown("Uses Z-scores to find statistical outliers in your numeric columns.")

        sensitivity = st.slider(
            "Anomaly Sensitivity (Z-Score Threshold)",
            min_value=1.0, max_value=5.0,
            value=2.5, step=0.1,
            help="Lower = more sensitive (catches more). Higher = only extreme outliers."
        )

        if st.button("Run Z-Score Analysis"):
            with st.spinner("Scanning for anomalies..."):
                results = detect_anomalies(current_df, threshold=sensitivity)

            if results["status"] == "success":
                total = results["total_anomalies"]
                st.metric("Total Anomalies Found", total)

                if total > 0:
                    st.json(results["anomalies"])

                    col_with_anomaly = list(results["anomalies"].keys())[0]
                    plot_df = current_df.copy().reset_index(drop=True)
                    col_data = plot_df[col_with_anomaly].dropna()
                    z_scores = np.abs(stats.zscore(col_data))
                    plot_df["Is Anomaly"] = False
                    plot_df.loc[col_data.index, "Is Anomaly"] = z_scores > sensitivity

                    fig = px.scatter(
                        plot_df, y=col_with_anomaly, color="Is Anomaly",
                        color_discrete_map={True: "#FF4B4B", False: "#A9A9FF"},
                        title=f"Anomaly Scan: {col_with_anomaly}",
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig, use_container_width=True, key="anomaly_chart")
                else:
                    st.success(f"No anomalies found at threshold {sensitivity}. Try lowering the slider.")
            else:
                st.warning(results.get("message", "Could not analyze."))

    # ── TAB 3: Dashboard ──────────────────────────────────────────────────────
    with tab3:
        st.subheader("Pinned Charts Dashboard")
        pinned = get_dashboard()

        if not pinned:
            st.info("No charts pinned yet. Run a query and click 'Pin to Dashboard'.")
        else:
            for i, item in enumerate(pinned):
                st.markdown(f"**{item['question']}**")
                st.plotly_chart(item["fig"], use_container_width=True, key=f"dashboard_chart_{i}")
                st.divider()

    # ── TAB 4: Export ─────────────────────────────────────────────────────────
    with tab4:
        st.subheader("Export PDF Report")
        st.markdown("Generates a full statistical overview of your dataset as a downloadable PDF.")

        if st.button("Generate PDF Report"):
            with st.spinner("Building PDF..."):
                try:
                    path = create_pdf_report(
                        current_df,
                        "Automated data overview generated by QuerySense BI."
                    )
                    with open(path, "rb") as pdf_file:
                        st.download_button(
                            label="Download Report",
                            data=pdf_file,
                            file_name="querysense_report.pdf",
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.error(f"PDF generation failed: {e}")

else:
    st.info("Upload a data file in the sidebar to get started.")
