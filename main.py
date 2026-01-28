"""
Main test runner for Multi-Technical-Alerts.

Tests the complete pipeline from Bronze to Gold and validates output.
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
    """Test the complete data processing pipeline."""
    print("=" * 80)
    print("MULTI-TECHNICAL-ALERTS - PIPELINE TEST")
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


def test_dashboard():
    """Test dashboard launch (if dashboard is implemented)."""
    print("\n" + "=" * 80)
    print("DASHBOARD TEST")
    print("=" * 80)
    
    # Check if dashboard module exists
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
    
    if not dashboard_path.exists():
        print("⚠️  Dashboard not yet implemented")
        print("   Dashboard files will be created in Phase 6")
        return
    
    print("Dashboard implementation found")
    print("To launch dashboard manually:")
    print("  python dashboard/app.py")
    print("\nDashboard will be available at: http://localhost:8050")


def main():
    """Main test execution."""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║         MULTI-TECHNICAL-ALERTS - MODULAR SYSTEM TEST         ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # Test 1: Pipeline
    results = test_pipeline()
    
    # Test 2: Dashboard (informational)
    test_dashboard()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
    
    if results and all('error' not in r for r in results.values()):
        print("\n✅ All components working correctly!")
        print("\nNext steps:")
        print("1. Review output files in data/oil/processed/")
        print("2. Implement dashboard (Phase 6) if needed")
        print("3. Deploy using Docker (see deployment_guide_for_dummies.md)")
        return 0
    else:
        print("\n⚠️  Some tests failed - check logs/main_test.log for details")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
