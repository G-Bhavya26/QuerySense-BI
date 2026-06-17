import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def detect_anomalies(df: pd.DataFrame, threshold: float = 2.5) -> Dict[str, Any]:
    """
    Detects anomalies in numeric columns using the Z-score method.
    
    Args:
        df (pd.DataFrame): The input dataframe.
        threshold (float): The Z-score threshold for defining an anomaly (default: 2.5).

    Returns:
        Dict[str, Any]: A dictionary detailing the anomalies found.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        return {"status": "success", "message": "No numeric columns to analyze.", "anomalies": {}}

    results = {}
    total_anomalies = 0

    for col in numeric_cols:
        # Drop NaNs to calculate z-scores properly
        col_data = df[col].dropna()
        if len(col_data) < 4:  # Z-score is meaningless below 4 samples
            continue
            
        z_scores = np.abs(stats.zscore(col_data))
        anomaly_indices = np.where(z_scores > threshold)[0]
        
        if len(anomaly_indices) > 0:
            anomalous_values = col_data.iloc[anomaly_indices].tolist()
            results[col] = {
                "count": len(anomaly_indices),
                "values": anomalous_values
            }
            total_anomalies += len(anomaly_indices)

    return {
        "status": "success",
        "total_anomalies": total_anomalies,
        "anomalies": results
    }

def generate_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates standard descriptive statistics for numeric columns.
    
    Args:
        df (pd.DataFrame): The input dataframe.

    Returns:
        pd.DataFrame: A dataframe containing the summary statistics.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return pd.DataFrame()
        
    return numeric_df.describe().T
