"""
Stewart Limits calculation for Multi-Technical-Alerts.

Computes statistical thresholds (90th, 95th, 98th percentiles) for essay classification.
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Tuple
from src.utils.logger import get_logger
from src.processing.name_normalization import name_protocol

logger = get_logger(__name__)


def calculate_stewart_limits(
    serie: pd.Series,
    percentiles: Tuple[int, int, int] = (90, 95, 98)
) -> Dict[str, float]:
    """
    Calculate Stewart Limits for a single essay.
    
    Uses percentiles to define thresholds:
    - Marginal (threshold_normal): 90th percentile
    - Condenatorio (threshold_alert): 95th percentile
    - Critico (threshold_critic): 98th percentile
    
    Args:
        serie: Series with essay values
        percentiles: Tuple of (marginal, condenatorio, critico) percentiles
    
    Returns:
        Dictionary with threshold_normal, threshold_alert, threshold_critic
    """
    # Remove zeros and NaNs for better statistical distribution
    serie = serie[serie != 0].dropna()
    
    if len(serie) < 3:
        logger.warning(f"Insufficient data ({len(serie)} samples) for Stewart Limits")
        return {
            'threshold_normal': np.nan,
            'threshold_alert': np.nan,
            'threshold_critic': np.nan
        }
    
    # Calculate percentiles
    normal = np.ceil(serie.quantile(percentiles[0] / 100))
    alert = np.ceil(serie.quantile(percentiles[1] / 100))
    critic = np.ceil(serie.quantile(percentiles[2] / 100))
    
    # Ensure thresholds are monotonically increasing
    if alert <= normal:
        alert = normal + 1
    if critic <= alert:
        critic = alert + 1
    
    return {
        'threshold_normal': float(normal),
        'threshold_alert': float(alert),
        'threshold_critic': float(critic)
    }


def calculate_all_limits(
    df: pd.DataFrame,
    client: str,
    essay_columns: List[str],
    percentiles: Tuple[int, int, int] = (90, 95, 98),
    min_unique_values: int = 3
) -> Dict:
    """
    Calculate Stewart Limits for all machines, components, and essays.
    
    Args:
        df: DataFrame with oil analysis data
        client: Client name
        essay_columns: List of essay column names
        percentiles: Percentile thresholds
        min_unique_values: Minimum unique values required to calculate limits
    
    Returns:
        Nested dictionary: {machine: {component: {essay: {threshold_normal, threshold_alert, threshold_critic}}}}
    """
    logger.info(f"Calculating Stewart Limits for client {client}")
    
    # Normalize machine and component names to avoid duplicates (CAMIÓN vs CAMION)
    df = df.copy()
    df['machineName_normalized'] = name_protocol(df['machineName'])
    df['componentName_normalized'] = name_protocol(df['componentName'])
    
    limits = {}
    
    # Get unique normalized machines
    machines = df['machineName_normalized'].unique()
    logger.info(f"Processing {len(machines)} normalized machines")
    
    for machine in machines:
        limits[machine] = {}
        
        # Get components for this machine (using normalized names)
        machine_df = df[df['machineName_normalized'] == machine]
        components = machine_df['componentName_normalized'].unique()
        
        for component in components:
            limits[machine][component] = {}
            
            # Filter data for this machine/component combination (using normalized names)
            component_df = machine_df[machine_df['componentName_normalized'] == component].copy()
            
            # Drop columns with all NaNs
            component_df = component_df.dropna(axis=1, how='all')
            
            # Calculate limits for each essay
            for essay in essay_columns:
                if essay not in component_df.columns:
                    continue
                
                # Check if essay has enough unique values
                if component_df[essay].nunique() <= min_unique_values:
                    logger.debug(f"Skipping {essay} for {machine}/{component}: only {component_df[essay].nunique()} unique values")
                    continue
                
                # Calculate limits
                essay_limits = calculate_stewart_limits(component_df[essay], percentiles)
                
                # Only store if valid (not all NaN)
                if not pd.isna(essay_limits['threshold_normal']):
                    limits[machine][component][essay] = essay_limits
    
    logger.info(f"Stewart Limits calculation complete for {client}")
    return limits


def save_limits_to_json(limits: Dict, output_path: str | Path) -> None:
    """
    Save Stewart Limits to JSON file.
    
    Args:
        limits: Limits dictionary
        output_path: Path to output JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving Stewart Limits to {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(limits, f, indent=4, ensure_ascii=False)
    
    logger.info("Stewart Limits saved successfully")


def save_limits_to_parquet(limits: Dict, output_path: str | Path) -> pd.DataFrame:
    """
    Save Stewart Limits to Parquet format (Phase 1 enhancement).
    
    Flattens nested dictionary to DataFrame for easier querying.
    
    Args:
        limits: Limits dictionary (can be nested with client → machine → component → essay)
        output_path: Path to output Parquet file
    
    Returns:
        Flattened DataFrame
    """
    from src.data.exporters import export_stewart_limits_parquet
    return export_stewart_limits_parquet(limits, output_path)


def load_limits_from_json(file_path: str | Path) -> Dict:
    """
    Load Stewart Limits from JSON file.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        Limits dictionary
    """
    from src.data.loaders import load_stewart_limits
    return load_stewart_limits(file_path)
