"""
Pipeline package for Multi-Technical-Alerts.

Orchestrates end-to-end data processing:
- bronze_to_silver.py: Raw data → Harmonized schema
- silver_to_gold.py: Harmonized data → Classified with AI
- full_pipeline.py: Complete Bronze → Silver → Gold flow
"""
