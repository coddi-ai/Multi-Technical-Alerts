"""
Silver to Gold pipeline for Multi-Technical-Alerts.

Applies Stewart Limits, classification, and AI recommendations to Silver layer data.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict
from openai import OpenAI
from config.settings import get_settings
from src.utils.logger import get_logger
from src.utils.file_utils import safe_read_parquet
from src.data.loaders import load_stewart_limits
from src.data.exporters import export_classified_reports, export_machine_status
from src.processing.stewart_limits import calculate_all_limits, save_limits_to_json, save_limits_to_parquet
from src.processing.classification import classify_all_samples
from src.processing.aggregations import get_machine_status
from src.ai.parallel_executor import generate_all_recommendations

logger = get_logger(__name__)


def run_silver_to_gold_pipeline(
    client: str,
    openai_client: OpenAI,
    input_file: Optional[str | Path] = None,
    stewart_limits_file: Optional[str | Path] = None,
    recalculate_limits: bool = False,
    generate_ai: bool = True,
    max_workers: int = 18
) -> Dict[str, pd.DataFrame]:
    """
    Run Silver → Gold transformation pipeline for a client.
    
    Steps:
    1. Load Silver layer data
    2. Calculate or load Stewart Limits
    3. Classify all samples (essay + report level)
    4. Generate AI recommendations (parallel processing)
    5. Aggregate machine statuses
    6. Export to Gold layer
    
    Args:
        client: Client name ('CDA' or 'EMIN')
        openai_client: OpenAI client instance
        input_file: Path to Silver layer file (default: to_consume/{CLIENT}.parquet)
        stewart_limits_file: Path to Stewart Limits JSON (default: processed/stewart_limits.json)
        recalculate_limits: If True, recalculate limits instead of loading
        generate_ai: If True, generate AI recommendations (requires API key)
        max_workers: Number of parallel workers for AI generation
    
    Returns:
        Dictionary with 'classified', 'machines' DataFrames
    """
    settings = get_settings()
    client_upper = client.upper()
    
    logger.info(f"===== Starting Silver → Gold pipeline for {client_upper} =====")
    
    # Step 1: Load Silver layer data
    if input_file is None:
        input_file = settings.get_to_consume_path(client_upper)
    
    logger.info(f"Step 1: Loading Silver layer data from {input_file}")
    df = safe_read_parquet(input_file)
    
    if df.empty:
        logger.error(f"No data loaded from {input_file}")
        return {'classified': df, 'machines': pd.DataFrame()}
    
    logger.info(f"Loaded {len(df)} samples from Silver layer")
    
    # Detect essay columns
    metadata_cols = {
        'client', 'sampleNumber', 'sampleDate', 'unitId', 'machineName', 
        'machineModel', 'machineBrand', 'machineHours', 'machineSerialNumber',
        'componentName', 'componentHours', 'componentSerialNumber',
        'oilMeter', 'oilBrand', 'oilType', 'oilWeight',
        'previousSampleNumber', 'previousSampleDate', 'daysSincePrevious',
        'group_element'
    }
    essays_list = [col for col in df.columns if col not in metadata_cols]
    logger.info(f"Detected {len(essays_list)} essay columns")
    
    # Step 2: Calculate or load Stewart Limits
    if stewart_limits_file is None:
        stewart_limits_file = settings.get_stewart_limits_path()
    
    if recalculate_limits:
        logger.info("Step 2: Calculating Stewart Limits")
        
        # CRITICAL: Filter data to only this client to prevent data leakage
        client_df = df[df['client'] == client_upper].copy()
        logger.info(f"Filtering to client {client_upper}: {len(client_df)} samples (from {len(df)} total)")
        
        # Calculate limits for this client ONLY
        client_limits = calculate_all_limits(
            df=client_df,
            client=client_upper,
            essay_columns=essays_list,
            percentiles=(
                settings.percentile_marginal,
                settings.percentile_condenatorio,
                settings.percentile_critico
            )
        )
        
        # Load existing limits or create new dict
        if stewart_limits_file.exists():
            all_limits = load_stewart_limits(stewart_limits_file)
        else:
            all_limits = {}
        
        # Update with new limits for this client
        all_limits[client_upper] = client_limits
        
        # Save updated limits
        save_limits_to_json(all_limits, stewart_limits_file)
        
        # Also save as Parquet (Phase 1)
        parquet_limits_file = stewart_limits_file.with_suffix('.parquet')
        save_limits_to_parquet(all_limits, parquet_limits_file)
        
        limits = all_limits
    else:
        logger.info(f"Step 2: Loading Stewart Limits from {stewart_limits_file}")
        limits = load_stewart_limits(stewart_limits_file)
        
        if client_upper not in limits:
            logger.warning(f"No limits found for {client_upper}, using empty dict")
            limits[client_upper] = {}
    
    # Step 3: Classify all samples
    logger.info("Step 3: Classifying all samples (essay + report level)")
    df = classify_all_samples(df, limits, essays_list)
    
    # Step 4: Generate AI recommendations (optional)
    if generate_ai:
        logger.info(f"Step 4: Generating AI recommendations with {max_workers} workers")
        df = generate_all_recommendations(
            df=df,
            limits=limits,
            openai_client=openai_client,
            max_workers=max_workers,
            essays_list=essays_list
        )
    else:
        logger.info("Step 4: Skipping AI recommendation generation")
        df['ai_recommendation'] = None
        df['ai_generated_at'] = None
    
    # Step 5: Aggregate machine statuses
    logger.info("Step 5: Aggregating machine statuses")
    machine_df = get_machine_status(df)
    
    # Step 6: Export to Gold layer
    logger.info(f"Step 6: Exporting to Gold layer")
    
    # Export classified reports to Gold layer (to_consume/{client}/classified_reports.parquet)
    classified_reports_path = settings.get_classified_reports_path(client_upper)
    export_classified_reports(df, classified_reports_path, client_upper)
    
    # Export machine status to Gold layer (to_consume/{client}/machine_status_current.parquet)
    machine_status_path = settings.get_machine_status_path(client_upper)
    export_machine_status(machine_df, machine_status_path)
    
    # Also export Stewart Limits to Silver layer (processed/stewart_limits.parquet) for reference
    # This is shared across all clients
    stewart_limits_parquet = settings.get_processed_path() / "stewart_limits.parquet"
    if recalculate_limits:
        from src.data.exporters import export_stewart_limits_parquet
        export_stewart_limits_parquet(limits, stewart_limits_parquet)
    
    logger.info(f"===== Silver → Gold pipeline complete for {client_upper} =====")
    logger.info(f"Final stats: {len(df)} classified samples, {len(machine_df)} machines")
    
    return {
        'classified': df,
        'machines': machine_df
    }
