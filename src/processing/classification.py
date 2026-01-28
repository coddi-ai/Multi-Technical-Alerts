"""
Classification logic for Multi-Technical-Alerts.

Three-tier classification system:
1. Essay-level: Identify which threshold (Marginal, Condenatorio, Critico) is exceeded
2. Report-level: Classify as Normal (<3 points), Alerta (3-4 points), Anormal (≥5 points)
3. Machine-level: Aggregate component statuses to overall machine health
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Classification constants
ESSAY_POINTS = {
    'Critico': 5,
    'Condenatorio': 3,
    'Marginal': 1
}

REPORT_THRESHOLDS = {
    'Normal': 3,    # severity_score < 3 → Normal
    'Anormal': 9     # severity_score >= 9 → Anormal, else Alerta (more restrictive)
}

# Machine-level aggregation (points assigned to each component status)
COMPONENT_POINTS = {
    'Normal': 0,
    'Alerta': 2,
    'Anormal': 5
}

MACHINE_THRESHOLDS = {
    'Normal': 6,     # machine_score < 6 → Normal
    'Anormal': 10    # machine_score >= 10 → Anormal, else Alerta
}


def identify_threshold(
    value: float,
    marginal: float,
    condenatorio: float,
    critico: float
) -> Tuple[str | None, float | None]:
    """
    Identify which threshold has been exceeded by an essay value.
    
    Args:
        value: Measured essay value
        marginal: Marginal threshold (90th percentile)
        condenatorio: Condenatorio threshold (95th percentile)
        critico: Critico threshold (98th percentile)
    
    Returns:
        Tuple of (threshold_name, threshold_value) or (None, None) if no threshold exceeded
    """
    if pd.isna(value):
        return None, None
    
    if value >= critico:
        return 'Critico', critico
    elif value >= condenatorio:
        return 'Condenatorio', condenatorio
    elif value >= marginal:
        return 'Marginal', marginal
    else:
        return None, None


def classify_essays(
    sample: pd.Series,
    limits: Dict,
    essays_list: List[str],
    points_dict: Dict[str, int] = ESSAY_POINTS
) -> Tuple[pd.DataFrame, int]:
    """
    Classify all essays for a single sample.
    
    Args:
        sample: Series with sample data (must include client, machineName, componentName, essay values)
        limits: Stewart Limits dictionary
        essays_list: List of essay column names to check
        points_dict: Points mapping for thresholds
    
    Returns:
        Tuple of (essays_broken DataFrame, total_severity_points)
    """
    client = sample.get('client', '')
    machine = sample.get('machineName', '')
    component = sample.get('componentName', '')
    
    # Get limits for this machine/component
    sel_limits = limits.get(client, {}).get(machine, {}).get(component, {})
    
    essays_broken = []
    
    for essay in essays_list:
        # Get thresholds for this essay
        marginal = sel_limits.get(essay, {}).get('threshold_normal', np.nan)
        condenatorio = sel_limits.get(essay, {}).get('threshold_alert', np.nan)
        critico = sel_limits.get(essay, {}).get('threshold_critic', np.nan)
        
        # Get measured value
        value = sample.get(essay, np.nan)
        
        # Skip if value is invalid or below marginal threshold
        if pd.isna(value) or value < marginal or pd.isna(marginal):
            continue
        
        # Identify threshold
        threshold_reached, value_lim = identify_threshold(value, marginal, condenatorio, critico)
        
        if threshold_reached:
            essays_broken.append({
                'essay': essay,
                'value': value,
                'threshold': threshold_reached,
                'limit': value_lim,
                'points': points_dict.get(threshold_reached, 0)
            })
    
    essays_broken_df = pd.DataFrame(essays_broken)
    
    # Calculate total severity score
    severity_score = essays_broken_df['points'].sum() if not essays_broken_df.empty else 0
    
    return essays_broken_df, int(severity_score)


def classify_report(
    essays_broken: int,
    severity_score: int,
    thresholds: Dict[str, int] = REPORT_THRESHOLDS
) -> str:
    """
    Classify report status based on severity score.
    
    Args:
        essays_broken: Number of essays that exceeded thresholds
        severity_score: Total severity points from broken essays
        thresholds: Classification thresholds
    
    Returns:
        Report status: 'Normal', 'Alerta', or 'Anormal'
    """
    if severity_score < thresholds['Normal']:
        return 'Normal'
    elif severity_score >= thresholds['Anormal']:
        return 'Anormal'
    else:
        return 'Alerta'


def classify_machine(
    df: pd.DataFrame,
    unit_id: str,
    component_points: Dict[str, int] = COMPONENT_POINTS,
    machine_thresholds: Dict[str, int] = MACHINE_THRESHOLDS
) -> Dict:
    """
    Classify overall machine status by aggregating component statuses.
    
    Uses points-based system:
    1. Assign points to each component based on status (Normal=0, Alerta=2, Anormal=5)
    2. Sum points across all components
    3. Apply thresholds to classify machine (similar to report-level logic)
    
    Args:
        df: DataFrame with classified reports for a machine
        unit_id: Machine unit ID
        component_points: Points assigned to each component status
        machine_thresholds: Thresholds for machine classification
    
    Returns:
        Dictionary with machine status details
    """
    # Filter to this machine's latest samples
    machine_df = df[df['unitId'] == unit_id].copy()
    
    if machine_df.empty:
        logger.warning(f"No data found for unit {unit_id}")
        return {}
    
    # Get latest sample date
    latest_date = machine_df['sampleDate'].max()
    
    # Get latest samples for each component
    latest_samples = machine_df.loc[machine_df.groupby('componentName')['sampleDate'].idxmax()]
    
    # Count status distribution
    status_counts = latest_samples['report_status'].value_counts().to_dict()
    
    # Calculate machine score by summing component points
    machine_score = 0
    for status, count in status_counts.items():
        points = component_points.get(status, 0)
        machine_score += points * count
    
    # Classify machine based on total score
    if machine_score < machine_thresholds['Normal']:
        overall_status = 'Normal'
        priority_score = 1
    elif machine_score >= machine_thresholds['Anormal']:
        overall_status = 'Anormal'
        priority_score = 10
    else:
        overall_status = 'Alerta'
        priority_score = 5
    
    # Create component details
    component_details = []
    for _, row in latest_samples.iterrows():
        component_details.append({
            'component': row['componentName'],
            'status': row['report_status'],
            'severity_score': row.get('severity_score', 0),
            'sample_date': row['sampleDate'].isoformat() if pd.notna(row['sampleDate']) else None
        })
    
    return {
        'unit_id': unit_id,
        'client': machine_df['client'].iloc[0],
        'latest_sample_date': latest_date.isoformat() if pd.notna(latest_date) else None,
        'overall_status': overall_status,
        'machine_score': machine_score,
        'total_components': len(latest_samples),
        'components_normal': status_counts.get('Normal', 0),
        'components_alerta': status_counts.get('Alerta', 0),
        'components_anormal': status_counts.get('Anormal', 0),
        'priority_score': priority_score,
        'component_details': component_details
    }


def classify_all_samples(
    df: pd.DataFrame,
    limits: Dict,
    essays_list: List[str]
) -> pd.DataFrame:
    """
    Classify all samples in DataFrame (essay-level and report-level).
    
    Args:
        df: DataFrame with oil samples
        limits: Stewart Limits dictionary
        essays_list: List of essay column names
    
    Returns:
        DataFrame with classification columns added
    """
    logger.info(f"Classifying {len(df)} samples")
    
    df = df.copy()
    
    # Initialize classification columns
    df['essays_broken'] = 0
    df['severity_score'] = 0
    df['report_status'] = 'Normal'
    df['breached_essays'] = [[] for _ in range(len(df))]
    
    # Classify each sample
    for idx, row in df.iterrows():
        essays_broken_df, severity_score = classify_essays(row, limits, essays_list)
        
        df.at[idx, 'essays_broken'] = len(essays_broken_df)
        df.at[idx, 'severity_score'] = severity_score
        df.at[idx, 'report_status'] = classify_report(len(essays_broken_df), severity_score)
        df.at[idx, 'breached_essays'] = essays_broken_df.to_dict('records') if not essays_broken_df.empty else []
    
    logger.info(f"Classification complete: {df['report_status'].value_counts().to_dict()}")
    
    return df
