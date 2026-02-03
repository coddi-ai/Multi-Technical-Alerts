"""
Oil Analysis Data Pipeline

Processes oil analysis data from Bronze to Gold layer, applying Stewart Limits
and generating AI-powered maintenance recommendations.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_settings
from config.logging_config import setup_logging
from src.pipeline.full_pipeline import run_full_pipeline

# Load environment variables
load_dotenv()


def test_pipeline():
    """Execute the complete oil analysis data processing pipeline."""
    print("=" * 80)
    print("OIL ANALYSIS DATA PIPELINE")
    print("=" * 80)
    
    # Setup logging
    logger = setup_logging(log_file="main_test.log", level="INFO")
    logger.info("Starting pipeline test")
    
    # Load settings
    settings = get_settings()
    logger.info(f"Data root: {settings.data_root}")
    logger.info(f"Clients: {settings.clients}")
    
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    generate_ai = bool(api_key and api_key != 'your_openai_api_key_here')
    
    if not generate_ai:
        logger.warning("OpenAI API key not configured - AI recommendations will be skipped")
        logger.warning("Set OPENAI_API_KEY in .env file to enable AI generation")
    
    # Run pipeline
    print("\nStarting pipeline execution...")
    print(f"- Recalculate limits: True")
    print(f"- Generate AI: {generate_ai}")
    print(f"- Max workers: {settings.max_workers}")
    print()
    
    try:
        results = run_full_pipeline(
            clients=settings.clients,
            recalculate_limits=True,
            generate_ai=generate_ai,
            max_workers=settings.max_workers
        )
        
        print("\n" + "=" * 80)
        print("PIPELINE TEST RESULTS")
        print("=" * 80)
        
        for client, result in results.items():
            print(f"\nClient: {client}")
            if 'error' in result:
                print(f"  ❌ FAILED: {result['error']}")
            else:
                print(f"  ✅ SUCCESS")
                print(f"     Silver samples: {result['silver_samples']}")
                print(f"     Gold samples: {result['gold_samples']}")
                print(f"     Machines: {result['machines']}")
                print(f"     Status distribution: {result['status_distribution']}")
        
        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        
        return results
    
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}", exc_info=True)
        print(f"\n❌ PIPELINE TEST FAILED: {e}")
        return None





def main():
    """Main pipeline execution."""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║              OIL ANALYSIS DATA PIPELINE                      ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # Run pipeline
    results = test_pipeline()
    
    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION COMPLETE")
    print("=" * 80)
    
    if results and all('error' not in r for r in results.values()):
        print("\n✅ Pipeline executed successfully!")
        print("\nNext steps:")
        print("1. Review output files in data/golden/")
        print("2. Gold layer data available for downstream consumption")
        print("3. Deploy using Docker (see docs/)")
        return 0
    else:
        print("\n⚠️  Pipeline failed - check logs/main_test.log for details")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
