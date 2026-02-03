# Oil Analysis Data Product

**AI-Powered Oil Analysis Pipeline for Mining Equipment with S3 Integration**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)](https://openai.com/)
[![AWS](https://img.shields.io/badge/AWS-S3-orange.svg)](https://aws.amazon.com/s3/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

---

## 🎯 Overview

This repository contains the **Oil Analysis Data Product** that processes mining equipment oil analysis data through a three-layer architecture: **Bronze → Silver → Golden**. The system applies statistical threshold detection (Stewart Limits) and AI-powered maintenance recommendations to support fleet management decisions.

**Core Question Answered**: *"How is my fleet performing based on oil analysis?"*

### Key Highlights

- 🔄 **Two Processing Modes**: Historical (bulk + limits calculation) and Incremental (daily updates)
- 🤖 **AI-Powered**: GPT-4o-mini recommendations for abnormal conditions
- ☁️ **S3 Integration**: Automatic upload of Silver and Golden layers
- 📊 **Multi-Client**: Independent processing for CDA and EMIN
- 🏭 **Multi-Lab**: Supports ALS and Finning laboratory formats

---

## 🏗️ System Architecture

### Data Processing Pipeline

```
Bronze Layer → Silver Layer → Golden Layer → S3 Upload
 (Raw Data)    (Harmonized)    (Analyzed)     (Cloud)
```

### Three-Layer Architecture

```
data/
├── bronze/{client}/              # Raw laboratory data (immutable)
├── silver/{CLIENT}.parquet       # Harmonized, validated data
└── golden/{client}/              # Analysis-ready outputs
    ├── classified.parquet        # Classified reports with AI
    ├── machine_status.parquet    # Aggregated machine health
    └── stewart_limits.parquet    # Statistical thresholds
```

### S3 Mirror (Auto-synced)

```
s3://{BUCKET}/MultiTechnique Alerts/oil/
├── silver/{CLIENT}.parquet
└── golden/{client}/*.parquet
```

---

## 🌟 Key Features

### Data Processing

- ✅ **Multi-Lab Integration**: ALS (Parquet) and Finning (Excel) formats
- ✅ **Independent Clients**: CDA and EMIN processed separately
- ✅ **Stewart Limits**: Dynamic percentile-based thresholds (90/95/98)
- ✅ **Multi-Level Classification**: Essay → Report → Machine hierarchy
- ✅ **Data Quality**: Validation, normalization, and filtering

### AI & Automation

- ✅ **GPT-4o-mini**: AI-powered maintenance recommendations
- ✅ **Parallel Processing**: 18-worker concurrent AI generation
- ✅ **Contextual Analysis**: Considers breached essays and machine history
- ✅ **Auto-Upload**: S3 sync after each client completes

### Deployment

- ✅ **Docker Ready**: Containerized with docker-compose
- ✅ **Environment-based**: Configuration via .env file
- ✅ **Flexible Modes**: Historical or incremental processing

---

## 📊 Data Flow

### Input (Bronze Layer)
- **Location**: `data/bronze/{client}/`
- **Formats**: 
  - CDA: Excel files from Finning Lab
  - EMIN: Parquet files from ALS Lab
- **Content**: Raw laboratory oil analysis results
- **Storage**: Local only (not uploaded to S3)

### Processing (Silver Layer)
- **Location**: `data/silver/{CLIENT}.parquet`
- **Transformations**:
  - Schema harmonization across clients
  - Name normalization (machines, components)
  - Data validation and quality checks
  - Essay column standardization
- **Storage**: Local + S3

### Output (Golden Layer)
- **Location**: `data/golden/{client}/`
- **Files per Client**:
  - `classified.parquet`: Classified reports with AI recommendations
  - `machine_status.parquet`: Aggregated equipment health status
  - `stewart_limits.parquet`: Statistical thresholds for classification
- **Storage**: Local + S3

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key (for AI recommendations)
- AWS credentials (optional, for S3 upload)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd Multi-Technical-Alerts

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your credentials:
#   - OPENAI_API_KEY (required)
#   - ACCESS_KEY, SECRET_KEY, BUCKET_NAME (optional for S3)
```

### Running the Pipeline

#### Historical Processing (with Stewart Limits calculation)

```bash
python main.py
```

This will:
1. Load all historical data from Bronze layer
2. Calculate Stewart Limits based on historical distribution
3. Classify all samples
4. Generate AI recommendations
5. Upload to S3 (if configured)

#### Incremental Processing (daily updates)

```python
from src.pipeline.full_pipeline import run_full_pipeline

# Daily mode: reuse existing Stewart Limits
results = run_full_pipeline(
    recalculate_limits=False,  # Use existing limits
    generate_ai=True,
    upload_to_s3=True
)
```

### Using Docker

```bash
# Build and run with docker-compose
docker-compose up

# Or build manually
docker build -f Dockerfile.backend -t oil-analysis .
docker run -p 8050:8050 oil-analysis
```
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
