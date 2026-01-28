"""
CLI script to run data processing pipeline.

Usage:
    python scripts/run_pipeline.py --clients CDA EMIN
    python scripts/run_pipeline.py --clients CDA --recalculate-limits
    python scripts/run_pipeline.py --clients EMIN --no-ai
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.full_pipeline import run_full_pipeline


def main():
    """Parse arguments and run pipeline."""
    parser = argparse.ArgumentParser(
        description="Run Multi-Technical-Alerts data processing pipeline"
    )
    
    parser.add_argument(
        '--clients',
        nargs='+',
        default=None,
        help='Client names to process (default: all from settings)'
    )
    
    parser.add_argument(
        '--recalculate-limits',
        action='store_true',
        help='Recalculate Stewart Limits instead of loading from file'
    )
    
    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Skip AI recommendation generation'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        default=None,
        help='Number of parallel workers for AI generation (default: from settings)'
    )
    
    args = parser.parse_args()
    
    print(f"Running pipeline with arguments: {args}")
    
    # Run pipeline
    results = run_full_pipeline(
        clients=args.clients,
        recalculate_limits=args.recalculate_limits,
        generate_ai=not args.no_ai,
        max_workers=args.max_workers
    )
    
    # Print results
    print("\n" + "=" * 80)
    print("Pipeline Results")
    print("=" * 80)
    
    for client, result in results.items():
        if 'error' in result:
            print(f"\n{client}: ❌ FAILED")
            print(f"  Error: {result['error']}")
        else:
            print(f"\n{client}: ✅ SUCCESS")
            print(f"  Silver samples: {result['silver_samples']}")
            print(f"  Gold samples: {result['gold_samples']}")
            print(f"  Machines: {result['machines']}")
            print(f"  Status: {result['status_distribution']}")
    
    print("\n" + "=" * 80)
    
    # Return exit code
    if all('error' not in r for r in results.values()):
        print("✅ All clients processed successfully")
        return 0
    else:
        print("⚠️  Some clients failed - check logs for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
