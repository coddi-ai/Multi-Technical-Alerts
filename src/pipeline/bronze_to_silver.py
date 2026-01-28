"""
Bronze to Silver pipeline for Multi-Technical-Alerts.

Transforms raw data (Bronze layer) into harmonized schema (Silver layer).
"""

import pandas as pd
from pathlib import Path
from typing import Optional
from config.settings import get_settings
from src.utils.logger import get_logger
from src.data.loaders import load_cda_data, load_emin_data, load_essays_mapping
from src.data.transformers import apply_full_transformation
from src.data.validators import filter_invalid_samples, validate_date_range, validate_numeric_essays
from src.data.exporters import export_to_parquet

logger = get_logger(__name__)


def run_bronze_to_silver_pipeline(
    client: str,
    essays_mapping_file: Optional[str | Path] = None,
    output_file: Optional[str | Path] = None
) -> pd.DataFrame:
    """
    Run Bronze → Silver transformation pipeline for a client.
    
    Steps:
    1. Load essays mapping
    2. Load raw data (Bronze layer)
    3. Transform to harmonized schema
    4. Apply validation and filtering
    5. Export to Silver layer
    
    Args:
        client: Client name ('CDA' or 'EMIN')
        essays_mapping_file: Path to essays mapping file (default: data/oil/essays_elements.xlsx)
        output_file: Path to output file (default: to_consume/{CLIENT}.parquet)
    
    Returns:
        Transformed DataFrame (Silver layer)
    """
    settings = get_settings()
    client_upper = client.upper()
    
    logger.info(f"===== Starting Bronze → Silver pipeline for {client_upper} =====")
    
    # Step 1: Load essays mapping
    if essays_mapping_file is None:
        essays_mapping_file = settings.data_root / "essays_elements.xlsx"
    
    logger.info(f"Step 1: Loading essays mapping from {essays_mapping_file}")
    essays_df = load_essays_mapping(essays_mapping_file)
    essays_list = list(essays_df['ElementNameSpanish'])
    logger.info(f"Loaded {len(essays_list)} essay mappings")
    
    # Step 2: Load raw data (Bronze layer)
    logger.info(f"Step 2: Loading raw data for {client_upper}")
    
    if client_upper == 'CDA':
        raw_folder = settings.get_raw_path(client)
        df = load_cda_data(raw_folder)
    elif client_upper == 'EMIN':
        raw_file = settings.get_raw_path(client) / "muestrasAlsHistoricos.parquet"
        df = load_emin_data(raw_file)
    else:
        raise ValueError(f"Unknown client: {client}")
    
    if df.empty:
        logger.error(f"No data loaded for {client_upper}")
        return df
    
    logger.info(f"Loaded {len(df)} raw samples")
    
    # Step 3: Transform to harmonized schema
    logger.info("Step 3: Applying full transformation (harmonization + normalization + Phase 1 enhancements)")
    df = apply_full_transformation(df, client_upper, essays_df)
    logger.info(f"Transformation complete: {len(df)} samples, {len(df.columns)} columns")
    
    # Step 4: Apply validation and filtering
    logger.info("Step 4: Applying validation and filtering")
    
    # Validate date range
    df = validate_date_range(df)
    
    # Validate numeric essays
    df = validate_numeric_essays(df, essays_list)
    
    # Filter invalid samples
    df = filter_invalid_samples(
        df,
        min_machine_samples=settings.min_machine_samples,
        min_component_samples=settings.min_component_samples
    )
    
    logger.info(f"Validation complete: {len(df)} valid samples")
    
    # Step 5: Export to Silver layer
    if output_file is None:
        output_file = settings.get_to_consume_path(client_upper)
    
    logger.info(f"Step 5: Exporting to Silver layer: {output_file}")
    export_to_parquet(df, output_file)
    
    logger.info(f"===== Bronze → Silver pipeline complete for {client_upper} =====")
    logger.info(f"Final stats: {len(df)} samples, {df['unitId'].nunique()} units, {df['componentName'].nunique()} components")
    
    return df
