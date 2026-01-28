"""
Parallel executor for Multi-Technical-Alerts.

Multi-threaded processing of AI recommendations for multiple samples.
"""

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
from tqdm import tqdm
from openai import OpenAI
from src.utils.logger import get_logger
from src.ai.recommendation_service import orchestrate_comment

logger = get_logger(__name__)


def process_single_sample(
    sample_number: str,
    df: pd.DataFrame,
    limits: Dict,
    openai_client: OpenAI,
    essays_list: List[str]
) -> Dict:
    """
    Process a single sample (wrapper for orchestrate_comment).
    
    Args:
        sample_number: Sample identifier
        df: DataFrame with samples
        limits: Stewart Limits
        openai_client: OpenAI client
        essays_list: Essay columns
    
    Returns:
        Result dictionary
    """
    try:
        result = orchestrate_comment(
            df=df,
            sample_number=sample_number,
            limits=limits,
            openai_client=openai_client,
            essays_list=essays_list
        )
        return result
    
    except Exception as e:
        logger.error(f"Error processing sample {sample_number}: {e}")
        return {
            'sampleNumber': sample_number,
            'error': str(e)
        }


def generate_all_recommendations(
    df: pd.DataFrame,
    limits: Dict,
    openai_client: OpenAI,
    max_workers: int = 18,
    essays_list: List[str] = None
) -> pd.DataFrame:
    """
    Generate AI recommendations for all samples using parallel processing.
    
    Uses ThreadPoolExecutor to process multiple samples concurrently.
    
    Args:
        df: DataFrame with oil samples
        limits: Stewart Limits dictionary
        openai_client: OpenAI client instance
        max_workers: Number of parallel workers (default: 18)
        essays_list: List of essay columns (if None, auto-detected)
    
    Returns:
        DataFrame with classification and AI recommendations
    """
    logger.info(f"Starting parallel recommendation generation: {len(df)} samples, {max_workers} workers")
    
    # Auto-detect essay columns if not provided
    if essays_list is None:
        metadata_cols = {
            'client', 'sampleNumber', 'sampleDate', 'unitId', 'machineName', 
            'machineModel', 'machineBrand', 'machineHours', 'machineSerialNumber',
            'componentName', 'componentHours', 'componentSerialNumber',
            'oilMeter', 'oilBrand', 'oilType', 'oilWeight',
            'previousSampleNumber', 'previousSampleDate', 'daysSincePrevious',
            'group_element'
        }
        essays_list = [col for col in df.columns if col not in metadata_cols]
        logger.info(f"Auto-detected {len(essays_list)} essay columns")
    
    # Get list of sample numbers
    sample_numbers = df['sampleNumber'].unique().tolist()
    
    # Process in parallel
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_sample = {
            executor.submit(
                process_single_sample,
                sample_number,
                df,
                limits,
                openai_client,
                essays_list
            ): sample_number
            for sample_number in sample_numbers
        }
        
        # Collect results with progress bar
        with tqdm(total=len(sample_numbers), desc="Generating recommendations") as pbar:
            for future in as_completed(future_to_sample):
                sample_number = future_to_sample[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Unexpected error for sample {sample_number}: {e}")
                    results.append({
                        'sampleNumber': sample_number,
                        'error': str(e)
                    })
                finally:
                    pbar.update(1)
    
    logger.info(f"Parallel processing complete: {len(results)} results")
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    
    # Merge with original DataFrame
    output_df = df.merge(
        results_df,
        on='sampleNumber',
        how='left',
        suffixes=('', '_generated')
    )
    
    # Update classification columns
    classification_cols = [
        'essays_broken', 'severity_score', 'report_status',
        'breached_essays', 'ai_recommendation', 'ai_generated_at'
    ]
    
    for col in classification_cols:
        if f'{col}_generated' in output_df.columns:
            output_df[col] = output_df[f'{col}_generated']
            output_df = output_df.drop(columns=[f'{col}_generated'])
    
    logger.info("Results merged with original DataFrame")
    
    # Log status distribution
    if 'report_status' in output_df.columns:
        status_counts = output_df['report_status'].value_counts().to_dict()
        logger.info(f"Status distribution: {status_counts}")
    
    return output_df
