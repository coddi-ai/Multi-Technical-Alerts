# Oil Analysis Data Product

**AI-Powered Oil Analysis Pipeline for Mining Equipment**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)](https://openai.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

---

## 🎯 Overview

This repository contains the **Oil Analysis Data Product** that processes mining equipment oil analysis data from raw laboratory results (Bronze layer) to analysis-ready insights (Gold layer). The system applies statistical threshold detection (Stewart Limits) and AI-powered maintenance recommendations to support fleet management decisions.

**Core Question Answered**: *"How is my fleet performing based on oil analysis?"*

---

## 🏗️ System Capabilities

### Data Processing Pipeline

```
Raw Lab Data → Harmonization → Statistical Analysis → Classification → AI Recommendations → Gold Layer
  (Bronze)        (Silver)         (Limits)          (Status)        (Insights)         (Output)
```

### Key Features

- ✅ **Multi-Lab Integration**: Processes data from ALS and Finning laboratories
- ✅ **Multi-Client Support**: Handles CDA and EMIN client data independently
- ✅ **Stewart Limits**: Dynamic statistical thresholds (90th, 95th, 98th percentiles)
- ✅ **Multi-Level Classification**: Essay → Report → Component → Machine status hierarchy
- ✅ **AI Recommendations**: GPT-4 powered maintenance insights for abnormal conditions
- ✅ **Parallel Processing**: 18-worker AI generation for fast execution
- ✅ **Docker Ready**: Containerized deployment with docker-compose

---

## 📊 Data Flow

### Input (Bronze Layer)
- **Location**: `data/oil/raw/`
- **Formats**: Excel (Finning), Parquet (ALS)
- **Content**: Raw laboratory oil analysis results

### Processing (Silver Layer)
- **Location**: `data/oil/processed/`
- **Transformations**:
  - Name normalization and standardization
  - Missing value handling
  - Data quality filtering (minimum 100 samples)
  - Stewart Limits calculation

### Output (Gold Layer)
- **Location**: `data/oil/processed/`
- **Files**:
  - `cda_summary.json`: Complete CDA client analysis
  - `emin_summary.json`: Complete EMIN client analysis
  - `stewart_limits.json`: Reference thresholds

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key (for AI recommendations)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd oil-analysis

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Running the Pipeline

```bash
# Run complete pipeline
python main.py
```

### Using Docker

```bash
# Build and run with docker-compose
docker-compose up

# Or build manually
docker build -f Dockerfile.backend -t oil-analysis .
docker run -e OPENAI_API_KEY=your_key oil-analysis
```

---

## 📁 Repository Structure

```
oil-analysis/
├── config/                 # Configuration
│   ├── settings.py         # Environment settings
│   ├── logging_config.py   # Logging setup
│   └── users.py            # User credentials (for future auth)
│
├── data/oil/               # Data layers
│   ├── raw/                # Bronze: Source files
│   │   ├── cda/            # CDA lab results
│   │   └── emin/           # EMIN lab results
│   ├── processed/          # Silver & Gold: Processed data
│   └── to_consume/         # Future: External consumption
│
├── src/                    # Source code
│   ├── data/               # Data handling
│   │   ├── loaders.py      # Read lab files
│   │   ├── transformers.py # Bronze → Silver
│   │   ├── exporters.py    # Gold layer export
│   │   ├── schemas.py      # Data models
│   │   └── validators.py   # Data quality checks
│   │
│   ├── processing/         # Business logic
│   │   ├── stewart_limits.py       # Threshold calculation
│   │   ├── classification.py       # Status classification
│   │   ├── aggregations.py         # Machine-level rollup
│   │   └── name_normalization.py   # Standardization
│   │
│   ├── ai/                 # AI integration
│   │   ├── recommendation_service.py
│   │   ├── prompts.py      # AI prompts
│   │   └── parallel_executor.py
│   │
│   ├── pipeline/           # Orchestration
│   │   ├── full_pipeline.py        # Main pipeline
│   │   ├── bronze_to_silver.py     # Layer 1 → 2
│   │   └── silver_to_gold.py       # Layer 2 → 3
│   │
│   └── utils/              # Common utilities
│       ├── logger.py
│       ├── date_utils.py
│       └── file_utils.py
│
├── docs/                   # Documentation
│   └── PROJECT_OVERVIEW.md # Detailed guide
│
├── scripts/                # Utility scripts
│   └── run_pipeline.py
│
├── notebooks/              # Jupyter exploration
│   └── explore_oil_full.ipynb
│
├── logs/                   # Application logs
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── Dockerfile.backend      # Docker image
├── docker-compose.yml      # Container orchestration
└── README.md               # This file
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Data Configuration
DATA_ROOT=./data/oil

# Processing Configuration
MAX_WORKERS=18  # Parallel AI generation threads

# Logging
LOGS_DIR=./logs
```

### Settings

Edit `config/settings.py` to configure:
- Client list (default: `["cda", "emin"]`)
- Data paths
- Processing parameters

---

## 📊 Classification System

### Essay-Level Classification

Individual chemical tests are compared against Stewart Limits:

- **Normal**: Below 90th percentile
- **Marginal**: 90th-95th percentile (1 point)
- **Condenatorio**: 95th-98th percentile (3 points)
- **Crítico**: Above 98th percentile (5 points)

### Report-Level Classification

Aggregate essay points for each oil sample:

- **Normal**: Total < 3 points
- **Alerta**: 3-4 points
- **Anormal**: ≥ 5 points

### Machine-Level Classification

Rollup component statuses for fleet units:

- **Normal**: Component scores < 2
- **Alerta**: Component scores 2-3
- **Anormal**: Component scores ≥ 4

---

## 🤖 AI Integration

### Model Configuration

- **Model**: GPT-4o-mini
- **Temperature**: 0.9
- **Max Tokens**: ~500 (150 words)
- **Parallel Workers**: 18

### AI Recommendation Strategy

AI is called **only for non-Normal reports** to optimize costs:
- Normal reports: Generic "no anomalies" message
- Alert/Abnormal reports: Full AI analysis with:
  - Root cause identification
  - Specific corrective actions
  - Follow-up recommendations
  - Urgency indicators

### Cost Optimization

- **Without optimization**: 100% of reports → ~$0.05 × 100 = $5.00
- **With optimization**: 30% of reports → ~$0.05 × 30 = $1.50
- **Savings**: 70% cost reduction

---

## 📈 Output Schema

### Gold Layer Structure (JSON)

```json
{
  "sampleId": "CDA_001_2024-01-15",
  "client": "cda",
  "unitId": "CDA_001",
  "machineName": "camion",
  "machineModel": "789D",
  "componentName": "motor diesel",
  "sampleDate": "2024-01-15",
  "reportStatus": "Anormal",
  "essaySum": 6,
  "machineStatus": "Alerta",
  "totalNumericStatus": 3,
  "aiRecommendation": "Se detecta concentración elevada de Hierro...",
  "essays": {
    "Hierro": {
      "value": 55.2,
      "status": "Condenatorio",
      "threshold": 45.0,
      "points": 3
    },
    "Cobre": {
      "value": 28.1,
      "status": "Marginal",
      "threshold": 25.0,
      "points": 1
    }
  }
}
```

---

## 🔧 Development

### Running Tests

```bash
# Run full pipeline test
python main.py
```

### Exploring Data

```bash
# Launch Jupyter notebook
jupyter notebook notebooks/explore_oil_full.ipynb
```

### Adding New Clients

1. Add raw data files to `data/oil/raw/<client_name>/`
2. Update `config/settings.py`:
   ```python
   clients = ["cda", "emin", "new_client"]
   ```
3. Run pipeline: `python main.py`

---

## 📚 Documentation

- **[Project Overview](docs/PROJECT_OVERVIEW.md)**: High-level system description and data architecture
- **Business Logic**: Detailed Stewart Limits methodology (coming soon)
- **Data Contracts**: Schema specifications (coming soon)
- **Deployment Guide**: Production deployment (coming soon)

---

## 🐳 Docker Deployment

### Development

```bash
docker-compose up
```

### Production

```bash
# Build image
docker build -f Dockerfile.backend -t oil-analysis:latest .

# Run container
docker run -d \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --name oil-analysis \
  oil-analysis:latest
```

### Scheduled Execution

Use cron or Kubernetes CronJob for periodic execution:

```bash
# Run daily at 2 AM
0 2 * * * docker start oil-analysis
```

---

## 📊 Typical Processing Metrics

- **Input**: 50-100 raw lab reports per week
- **Processing Time**: 2-5 minutes (full pipeline)
- **AI Generation**: ~30 seconds for 100 reports (parallel)
- **Output Size**: 1-5 MB per client summary

---

## 🔐 Security

- **API Keys**: Store in `.env` file (never commit)
- **Data Access**: Gold layer files contain processed data only
- **Client Isolation**: Separate output files per client

---

## 🤝 Data Mesh Integration

This oil analysis data product is designed to integrate with broader data mesh architecture:

```
┌─────────────────────┐
│ Oil Analysis        │ ← This Repository
│ (Bronze → Gold)     │
└──────────┬──────────┘
           │
           ├─ Output: cda_summary.json
           ├─ Output: emin_summary.json
           └─ Output: stewart_limits.json
                      ↓
           ┌──────────────────────┐
           │ Fusion Service       │ (Separate Repo)
           │ (Cross-domain)       │
           └──────────┬───────────┘
                      ↓
           ┌──────────────────────┐
           │ Dashboard/BI Tools   │ (Separate Repo)
           └──────────────────────┘
```

**Interface**: JSON files in gold layer folder serve as data product output

---

## 📞 Support

For questions or issues:
- Review documentation in `docs/`
- Check logs in `logs/` folder
- Examine sample data in `notebooks/`

---

## 🔄 Version

**v1.0.0** - Oil Analysis Data Product (Data Mesh Architecture)

- Multi-client support (CDA, EMIN)
- Stewart Limits implementation
- AI-powered recommendations
- Docker deployment ready
- Gold layer output for data mesh integration
