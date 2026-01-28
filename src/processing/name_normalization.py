"""
Name normalization for Multi-Technical-Alerts.

Standardizes machine, component, and brand names to reduce cardinality.
"""

import pandas as pd
import unicodedata
from typing import Dict


def name_protocol(series: pd.Series) -> pd.Series:
    """
    Standardize names by normalizing unicode characters and converting to lowercase.
    
    Removes accents and special characters to ensure consistency across data sources.
    
    Args:
        series: Pandas Series with names to normalize
    
    Returns:
        Normalized Series
    """
    # Normalize unicode characters to NFKD, encode to ASCII bytes, decode back to UTF-8 string
    series = series.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    
    # Convert to lowercase
    series = series.str.lower()
    
    # Secure no accents (redundant but safe)
    series = series.str.replace('á', 'a').str.replace('é', 'e').str.replace('í', 'i').str.replace('ó', 'o').str.replace('ú', 'u')
    
    return series


def reduce_cardinality_names(series: pd.Series) -> pd.Series:
    """
    Reduce cardinality of names by mapping similar names to common names.
    
    Uses predefined mapping dictionaries for machineName, componentName, and machineBrand.
    
    Args:
        series: Pandas Series with names to reduce
    
    Returns:
        Series with reduced cardinality
    """
    mapping: Dict[str, Dict[str, str]] = {
        'machineName': {
            'bulldozer': 'bulldozer',
            'pala': 'pala',
        },
        'componentName': {
            'mando final': 'mando final',
            'hidraulico': 'hidraulico',
            'refrig': 'refrigerante',
            'aceite': 'aceite',
            'vibrador': 'vibrador',
            'cojinete ': 'cojinete',
            'winche': 'winche',
            'trasmision': 'transmision',
            'transmision': 'transmision',
            'tandem': 'tandem',
            'cubo': 'cubo',
            'eje': 'eje',
            'engranaje': 'engranaje',
            'freno': 'freno',
            'retardador': 'retardador',
            'rueda': 'rueda',
            'direccion': 'direccion',
            'diferencial': 'diferencial',
        },
        'machineBrand': {
            'cat': 'caterpillar',
        }
    }
    
    # Get the mapping for this series based on its name
    if series.name not in mapping:
        return series
    
    series_mapping = mapping[series.name]
    
    # Create a copy to avoid SettingWithCopyWarning
    result = series.copy()
    
    for original, new in series_mapping.items():
        mask = result.str.contains(original, na=False, regex=False)
        result.loc[mask] = new
    
    return result


def normalize_dataframe_names(df: pd.DataFrame, columns: list[str] = None) -> pd.DataFrame:
    """
    Apply name normalization to specified columns in DataFrame.
    
    Args:
        df: DataFrame to normalize
        columns: List of column names to normalize (default: ['componentName', 'machineName', 'machineBrand'])
    
    Returns:
        DataFrame with normalized names
    """
    if columns is None:
        columns = ['componentName', 'machineName', 'machineBrand']
    
    df = df.copy()
    
    for col in columns:
        if col in df.columns:
            # Apply name protocol
            df[col] = name_protocol(df[col])
            
            # Apply cardinality reduction
            df[col] = reduce_cardinality_names(df[col])
    
    return df
