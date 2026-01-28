"""
Aggregation functions for Multi-Technical-Alerts.

Create machine-level and component-level summaries from classified reports.
"""

import pandas as pd
from typing import List
from src.utils.logger import get_logger
from src.processing.classification import classify_machine

logger = get_logger(__name__)


def get_machine_status(
    df: pd.DataFrame,
    date_col: str = 'sampleDate',
    unit_col: str = 'unitId',
    component_col: str = 'componentName',
    status_col: str = 'report_status'
) -> pd.DataFrame:
    """
    Aggregate component statuses to machine-level health status.
    
    For each machine, takes the latest sample from each component and determines
    overall machine status (worst status across components).
    
    Args:
        df: DataFrame with classified reports
        date_col: Date column name
        unit_col: Machine unit ID column
        component_col: Component name column
        status_col: Report status column
    
    Returns:
        DataFrame with machine-level statuses
    """
    logger.info(f"Aggregating machine statuses from {len(df)} reports")
    
    # Get unique units
    units = df[unit_col].unique()
    
    machine_statuses = []
    
    for unit in units:
        machine_dict = classify_machine(df, unit)
        if machine_dict:
            machine_statuses.append(machine_dict)
    
    machine_df = pd.DataFrame(machine_statuses)
    
    logger.info(f"Generated machine status for {len(machine_df)} units")
    
    return machine_df


def create_component_summary(
    df: pd.DataFrame,
    group_cols: List[str] = ['client', 'unitId', 'componentName']
) -> pd.DataFrame:
    """
    Create component-level summary statistics.
    
    Args:
        df: DataFrame with classified reports
        group_cols: Columns to group by
    
    Returns:
        DataFrame with component summary
    """
    logger.info("Creating component summary")
    
    summary = df.groupby(group_cols).agg({
        'sampleNumber': 'count',
        'sampleDate': ['min', 'max'],
        'report_status': lambda x: x.value_counts().to_dict(),
        'severity_score': ['mean', 'max'],
        'essays_broken': ['mean', 'max']
    }).reset_index()
    
    # Flatten multi-level columns
    summary.columns = ['_'.join(col).strip('_') for col in summary.columns.values]
    
    # Rename for clarity
    summary = summary.rename(columns={
        'sampleNumber_count': 'total_samples',
        'sampleDate_min': 'first_sample_date',
        'sampleDate_max': 'latest_sample_date',
        'report_status_<lambda>': 'status_distribution',
        'severity_score_mean': 'avg_severity_score',
        'severity_score_max': 'max_severity_score',
        'essays_broken_mean': 'avg_essays_broken',
        'essays_broken_max': 'max_essays_broken'
    })
    
    logger.info(f"Component summary created: {len(summary)} components")
    
    return summary


def create_priority_table(
    machine_df: pd.DataFrame,
    top_n: int = 10
) -> pd.DataFrame:
    """
    Create priority table of machines requiring attention.
    
    Args:
        machine_df: DataFrame with machine statuses
        top_n: Number of top priority machines to return
    
    Returns:
        DataFrame sorted by priority score
    """
    logger.info(f"Creating priority table (top {top_n})")
    
    # Filter to machines with issues
    priority_df = machine_df[machine_df['overall_status'] != 'Normal'].copy()
    
    # Sort by priority score (descending) and latest date (descending)
    priority_df = priority_df.sort_values(
        by=['priority_score', 'latest_sample_date'],
        ascending=[False, False]
    )
    
    # Select top N
    priority_df = priority_df.head(top_n)
    
    logger.info(f"Priority table created: {len(priority_df)} machines")
    
    return priority_df


def create_time_series_data(
    df: pd.DataFrame,
    unit_id: str,
    component: str,
    essay: str,
    date_col: str = 'sampleDate'
) -> pd.DataFrame:
    """
    Create time series data for a specific essay in a component.
    
    Args:
        df: DataFrame with samples
        unit_id: Machine unit ID
        component: Component name
        essay: Essay name
        date_col: Date column
    
    Returns:
        DataFrame with time series (date, value)
    """
    # Filter to unit and component
    filtered = df[
        (df['unitId'] == unit_id) &
        (df['componentName'] == component)
    ].copy()
    
    # Check if essay exists
    if essay not in filtered.columns:
        logger.warning(f"Essay '{essay}' not found in data")
        return pd.DataFrame()
    
    # Select relevant columns
    time_series = filtered[[date_col, essay]].copy()
    time_series = time_series.dropna(subset=[essay])
    time_series = time_series.sort_values(date_col)
    
    logger.info(f"Created time series for {unit_id}/{component}/{essay}: {len(time_series)} points")
    
    return time_series
