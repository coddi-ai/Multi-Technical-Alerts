"""
Full pipeline orchestration for Multi-Technical-Alerts.

Runs complete Bronze → Silver → Gold flow for all clients.
"""

import os
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
from config.settings import get_settings
from config.logging_config import setup_logging
from src.utils.logger import get_logger
from src.pipeline.bronze_to_silver import run_bronze_to_silver_pipeline
from src.pipeline.silver_to_gold import run_silver_to_gold_pipeline

# Load environment variables
load_dotenv()


def run_full_pipeline(
    clients: List[str] = None,
    recalculate_limits: bool = False,
    generate_ai: bool = True,
    max_workers: int = None
) -> Dict:
    """
    Run complete data processing pipeline for all clients.
    
    Bronze → Silver → Gold for each client:
    1. Load raw data
    2. Transform and harmonize
    3. Calculate Stewart Limits
    4. Classify samples
    5. Generate AI recommendations
    6. Export results
    
    Args:
        clients: List of client names (default: from settings)
        recalculate_limits: If True, recalculate Stewart Limits
        generate_ai: If True, generate AI recommendations
        max_workers: Number of parallel workers (default: from settings)
    
    Returns:
        Dictionary with results for each client
    """
    # Setup logging
    logger = setup_logging(log_file="full_pipeline.log", level="INFO")
    logger.info("=" * 80)
    logger.info("STARTING FULL PIPELINE EXECUTION")
    logger.info("=" * 80)
    
    # Load settings
    settings = get_settings()
    
    if clients is None:
        clients = settings.clients
    
    if max_workers is None:
        max_workers = settings.max_workers
    
    logger.info(f"Clients: {clients}")
    logger.info(f"Recalculate limits: {recalculate_limits}")
    logger.info(f"Generate AI: {generate_ai}")
    logger.info(f"Max workers: {max_workers}")
    
    # Initialize OpenAI client
    openai_client = None
    if generate_ai:
        api_key = os.getenv('OPENAI_API_KEY') or settings.openai_api_key
        if not api_key or api_key == 'your_openai_api_key_here':
            logger.warning("OpenAI API key not configured, AI generation disabled")
            generate_ai = False
        else:
            logger.info("Initializing OpenAI client")
            openai_client = OpenAI(api_key=api_key)
    
    # Process each client
    results = {}
    
    for client in clients:
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"PROCESSING CLIENT: {client}")
        logger.info("=" * 80)
        
        try:
            # Bronze → Silver
            logger.info(f"[{client}] Phase 1/2: Bronze → Silver")
            silver_df = run_bronze_to_silver_pipeline(client=client)
            
            if silver_df.empty:
                logger.error(f"[{client}] No data after Bronze → Silver, skipping")
                results[client] = {'error': 'No data in Silver layer'}
                continue
            
            # Silver → Gold
            logger.info(f"[{client}] Phase 2/2: Silver → Gold")
            gold_results = run_silver_to_gold_pipeline(
                client=client,
                openai_client=openai_client,
                recalculate_limits=recalculate_limits,
                generate_ai=generate_ai,
                max_workers=max_workers
            )
            
            # Store results
            results[client] = {
                'silver_samples': len(silver_df),
                'gold_samples': len(gold_results['classified']),
                'machines': len(gold_results['machines']),
                'status_distribution': gold_results['classified']['report_status'].value_counts().to_dict()
            }
            
            logger.info(f"[{client}] Pipeline complete: {results[client]}")
        
        except Exception as e:
            logger.error(f"[{client}] Pipeline failed: {e}", exc_info=True)
            results[client] = {'error': str(e)}
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("PIPELINE EXECUTION SUMMARY")
    logger.info("=" * 80)
    
    for client, result in results.items():
        if 'error' in result:
            logger.error(f"{client}: FAILED - {result['error']}")
        else:
            logger.info(f"{client}: SUCCESS - {result['gold_samples']} samples, {result['machines']} machines")
            logger.info(f"  Status: {result['status_distribution']}")
    
    logger.info("=" * 80)
    logger.info("PIPELINE EXECUTION COMPLETE")
    logger.info("=" * 80)
    
    return results


if __name__ == "__main__":
    # Run full pipeline when executed directly
    results = run_full_pipeline()
    print("\n=== Pipeline Results ===")
    for client, result in results.items():
        print(f"{client}: {result}")
