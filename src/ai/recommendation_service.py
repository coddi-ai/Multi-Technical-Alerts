"""
OpenAI recommendation service for Multi-Technical-Alerts.

Generates AI-powered maintenance recommendations based on oil analysis results.
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Optional
from openai import OpenAI
from src.utils.logger import get_logger
from src.ai.prompts import create_full_messages
from src.processing.classification import classify_essays

logger = get_logger(__name__)


def create_recommendation(
    messages: list[Dict[str, str]],
    client: OpenAI,
    model: str = "gpt-4o-mini",
    temperature: float = 0.9,
    max_tokens: int = 500
) -> str:
    """
    Generate AI recommendation using OpenAI Chat API.
    
    Args:
        messages: List of message dicts (system + few-shot + user)
        client: OpenAI client instance
        model: Model name
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum response length
    
    Returns:
        AI-generated recommendation text
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        recommendation = response.choices[0].message.content
        logger.debug(f"Generated recommendation: {len(recommendation)} characters")
        
        return recommendation
    
    except Exception as e:
        logger.error(f"Error generating recommendation: {e}")
        return f"Error generando recomendación: {str(e)}"


def orchestrate_comment(
    df: pd.DataFrame,
    sample_number: str,
    limits: Dict,
    openai_client: OpenAI,
    essays_list: Optional[list] = None
) -> Dict:
    """
    Orchestrate complete classification and AI recommendation for a single sample.
    
    This is the main entry point for generating AI comments.
    
    Args:
        df: DataFrame with oil samples
        sample_number: Unique sample identifier
        limits: Stewart Limits dictionary
        openai_client: OpenAI client instance
        essays_list: List of essay columns (if None, auto-detected)
    
    Returns:
        Dictionary with complete report metadata
    """
    logger.info(f"Orchestrating comment for sample {sample_number}")
    
    # Get sample data
    sample = df[df['sampleNumber'] == sample_number].iloc[0]
    
    # Auto-detect essay columns if not provided
    if essays_list is None:
        # Exclude metadata columns
        metadata_cols = {
            'client', 'sampleNumber', 'sampleDate', 'unitId', 'machineName', 
            'machineModel', 'machineBrand', 'machineHours', 'machineSerialNumber',
            'componentName', 'componentHours', 'componentSerialNumber',
            'oilMeter', 'oilBrand', 'oilType', 'oilWeight',
            'previousSampleNumber', 'previousSampleDate', 'daysSincePrevious',
            'group_element', 'essays_broken', 'severity_score', 'report_status',
            'breached_essays', 'ai_recommendation', 'ai_generated_at'
        }
        essays_list = [col for col in df.columns if col not in metadata_cols]
    
    # Classify essays
    essays_broken_df, severity_score = classify_essays(sample, limits, essays_list)
    
    # Classify report
    from src.processing.classification import classify_report
    report_status = classify_report(len(essays_broken_df), severity_score)
    
    # Generate AI recommendation only for non-Normal reports
    ai_recommendation = None
    ai_generated_at = None
    
    if report_status != 'Normal' and not essays_broken_df.empty:
        logger.info(f"Generating AI recommendation for {report_status} report")
        
        # Create messages
        messages = create_full_messages(sample, essays_broken_df)
        
        # Generate recommendation
        ai_recommendation = create_recommendation(
            messages=messages,
            client=openai_client
        )
        
        ai_generated_at = datetime.now()
    else:
        logger.info(f"Skipping AI recommendation for {report_status} report")
    
    # Create result dictionary
    result = {
        'sampleNumber': sample_number,
        'unitId': sample.get('unitId'),
        'componentName': sample.get('componentName'),
        'sampleDate': sample.get('sampleDate'),
        'client': sample.get('client'),
        'essays_broken': len(essays_broken_df),
        'severity_score': severity_score,
        'report_status': report_status,
        'breached_essays': essays_broken_df.to_dict('records') if not essays_broken_df.empty else [],
        'ai_recommendation': ai_recommendation,
        'ai_generated_at': ai_generated_at
    }
    
    logger.info(f"Orchestration complete: {report_status} with {len(essays_broken_df)} breached essays")
    
    return result
