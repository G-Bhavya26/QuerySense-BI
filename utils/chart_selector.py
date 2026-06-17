import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _is_numeric(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series)


def _is_datetime(series: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    # Try converting — if most values parse as dates, treat it as datetime
    try:
        converted = pd.to_datetime(series.dropna().head(10), infer_datetime_format=True)
        return len(converted) > 0
    except Exception:
        return False


def auto_chart(df: pd.DataFrame, question: str = "") -> tuple:
    """
    Automatically selects and renders the most appropriate Plotly chart
    based on the shape and column types of the result DataFrame.

    Args:
        df (pd.DataFrame): The query result.
        question (str): The original user question (used as chart title).

    Returns:
        tuple: (plotly Figure, chart type label string)
    """
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data returned for this query.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16)
        )
        return fig, "empty"

    rows, cols = df.shape
    columns = df.columns.tolist()

    numeric_cols = [c for c in columns if _is_numeric(df[c])]
    datetime_cols = [c for c in columns if _is_datetime(df[c])]
    text_cols = [c for c in columns if c not in numeric_cols and c not in datetime_cols]

    # ── 1 row, 1 col → KPI Card ───────────────────────────────────────────────
    if rows == 1 and cols == 1:
        value = df.iloc[0, 0]
        label = columns[0].replace("_", " ").title()
        if _is_numeric(df.iloc[:, 0]):
            fig = go.Figure(go.Indicator(
                mode="number",
                value=float(value),
                title={"text": label, "font": {"size": 20}},
                number={"font": {"size": 52}},
            ))
        else:
            fig = go.Figure()
            fig.add_annotation(
                text=f"<b>{label}</b><br><span style='font-size:40px'>{value}</span>",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, align="center"
            )
        fig.update_layout(height=220)
        return fig, "kpi"

    # ── Date + numeric → Line chart ───────────────────────────────────────────
    if datetime_cols and numeric_cols:
        x_col = datetime_cols[0]
        y_cols = numeric_cols[:4]
        df_sorted = df.sort_values(x_col)
        fig = px.line(df_sorted, x=x_col, y=y_cols, title=question, markers=True)
        fig.update_layout(height=400)
        return fig, "line"

    # ── Text + numeric → Bar chart ────────────────────────────────────────────
    if text_cols and numeric_cols:
        x_col = text_cols[0]
        y_col = numeric_cols[0]
        df_plot = df.sort_values(y_col, ascending=False).head(30)
        fig = px.bar(df_plot, x=x_col, y=y_col, title=question,
                     color=y_col, color_continuous_scale="Blues")
        fig.update_layout(height=420, coloraxis_showscale=False, xaxis_tickangle=-35)
        return fig, "bar"

    # ── Single numeric column → Histogram ─────────────────────────────────────
    if cols == 1 and numeric_cols:
        fig = px.histogram(df, x=columns[0], nbins=20, title=question)
        fig.update_layout(height=380)
        return fig, "histogram"

    # ── Fallback → Table ──────────────────────────────────────────────────────
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[f"<b>{c}</b>" for c in columns],
            fill_color="#0f3460",
            font=dict(color="white", size=12),
            align="left",
        ),
        cells=dict(
            values=[df[c].tolist() for c in columns],
            align="left",
            font=dict(size=11),
        ),
    )])
    fig.update_layout(height=min(500, 80 + rows * 30), title=question)
    return fig, "table"
