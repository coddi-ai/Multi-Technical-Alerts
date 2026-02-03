# Oil Analysis Data Product

**AI-Powered Oil Analysis System for Mining Equipment Fleet Management**

---

## 🎯 Purpose

This data product provides automated oil analysis processing for mining equipment, transforming raw laboratory test results into actionable maintenance insights. The system processes data from bronze (raw) to gold (analysis-ready) layers, applying statistical threshold detection and AI-powered recommendations.

The primary goal is to answer: **"How is my fleet performing based on oil analysis?"** by transforming raw chemical essay data into clear, prioritized maintenance insights.

---

## 🏗️ What This System Does

### 1. **Unified Data Processing**
Consolidates oil analysis data from multiple laboratory providers (ALS and Finning) across different clients (EMIN and CDA), creating a standardized data model that enables cross-fleet analysis and comparison.

### 2. **Statistical Threshold Detection (Stewart Limits)**
Establishes dynamic alert thresholds for each chemical essay based on historical performance data, accounting for variations across different machine types and components. These limits define three severity levels:
- **Normal**: Within expected operating parameters
- **Alert**: Marginal values requiring monitoring
- **Anormal**: Critical values requiring immediate action

### 3. **Multi-Level Status Classification**
Implements a hierarchical assessment model:

```
Essay → Report → Component → Machine/Unit
```

- **Essay Level**: Individual chemical test results (Fe, Cu, Si, etc.) compared against Stewart Limits
- **Report Level**: Aggregate assessment of all essays in a single oil sample
- **Component Level**: Status of individual equipment parts (engine, transmission, hydraulics, etc.)
- **Machine Level**: Overall fleet unit health based on all monitored components

### 4. **AI-Generated Maintenance Recommendations**
Integrates with OpenAI GPT-4 to provide:
- Contextual interpretation of abnormal readings
- Root cause analysis (contamination, wear, degradation, etc.)
- Specific maintenance actions (component inspection, oil change, filter replacement, etc.)
- Urgency classification and follow-up intervals

The AI system is trained with domain-specific examples from mechanical engineering experts specializing in mining equipment.

### 5. **Gold Layer Output**
Produces analysis-ready data files for downstream consumption (dashboards, reporting tools, data warehouses):
- Processed samples with classifications
- Machine status summaries
- Component health assessments
- AI recommendations

---

## 📊 Data Architecture

### Bronze → Silver → Gold Pipeline

```
┌─────────────────┐
│  Raw Lab Data   │  Bronze Layer: Immutable source files
│  (CDA / EMIN)   │  - Excel files (Finning Lab)
└────────┬────────┘  - Parquet files (ALS Lab)
         │
         ▼ [Harmonization]
┌─────────────────┐
│   Unified Oil   │  Silver Layer: Standardized schema
│    Samples      │  - Consistent column names
└────────┬────────┘  - Normalized values
         │           - Validated data types
         │
         ▼ [Statistical Analysis]
┌─────────────────┐
│ Stewart Limits  │  Threshold Calculation
│  (JSON/Parquet) │  - Per client/machine/component/essay
└────────┬────────┘  - 90th, 95th, 98th percentiles
         │
         ▼ [Classification]
┌─────────────────┐
│   Classified    │  Gold Layer: Analysis-ready
│    Reports      │  - Essay → Report → Machine status
└────────┬────────┘  - AI recommendations
         │           - Severity metrics
         ▼
┌─────────────────┐
│  Gold Layer     │  Final Output for Consumption
│  Output Files   │  - CDA summary, EMIN summary
└─────────────────┘  - Stewart Limits reference
```

---

## 🚀 Key Features

- ✅ **Multi-Source Data Integration**: Handles different lab formats and structures
- ✅ **Adaptive Thresholds**: Statistical limits based on historical performance
- ✅ **Context-Aware Analysis**: Machine/component-specific classifications
- ✅ **AI-Powered Insights**: Expert-level maintenance recommendations
- ✅ **Scalable Processing**: Parallel AI generation (18 workers)
- ✅ **Data Quality Controls**: Automated validation and filtering
- ✅ **Gold Layer Export**: Ready for dashboard consumption

---

## 📁 Repository Structure

```
oil-analysis/
├── config/              # Configuration files
│   ├── settings.py      # Environment settings
│   └── logging_config.py
├── data/                # Data layers
│   └── oil/
│       ├── raw/         # Bronze: Source files
│       ├── processed/   # Silver: Standardized data
│       └── to_consume/  # Gold: Analysis-ready
├── src/                 # Source code
│   ├── data/            # Data loading & transformation
│   ├── processing/      # Business logic
│   ├── ai/              # AI recommendations
│   ├── pipeline/        # Orchestration
│   └── utils/           # Common utilities
├── docs/                # Documentation
├── scripts/             # Utility scripts
├── notebooks/           # Exploration notebooks
├── main.py              # Pipeline entry point
└── requirements.txt     # Python dependencies
```

---

## 📚 Documentation

- **[Business Logic & Implementation](BUSINESS_LOGIC.md)**: Detailed explanation of Stewart Limits, classification system, and AI integration
- **[Data Contracts](DATA_CONTRACTS.md)**: Schema specifications and transformation rules
- **[Deployment Guide](DEPLOYMENT.md)**: Setup and deployment instructions

---

## 🔧 Technology Stack

- **Language**: Python 3.11+
- **Data Processing**: Pandas, NumPy
- **AI Integration**: OpenAI GPT-4
- **Containerization**: Docker
- **Data Formats**: Excel, Parquet, JSON

---

## 🎯 Use Cases

### For Fleet Managers
- Identify machines requiring urgent attention
- Prioritize maintenance resources
- Track fleet health trends

### For Maintenance Teams
- Receive specific corrective action recommendations
- Understand root causes of equipment issues
- Schedule preventive maintenance

### For Data Engineers (Downstream Consumers)
- Consume gold layer data for dashboards
- Integrate with business intelligence tools
- Build cross-domain analytics

---

## 🔄 Data Mesh Integration

This oil analysis data product is designed to integrate with a larger data mesh architecture:

```
Oil Analysis (This Repo) → Gold Layer Output
                              ↓
                         Fusion Service
                              ↓
                        Dashboard/BI Tools
```

**Input**: Raw oil analysis files from laboratories  
**Output**: Classified samples, machine statuses, AI recommendations  
**Interface**: JSON/Parquet files in gold layer folder

---

## 📊 Output Data Products

### 1. CDA Summary (`cda_summary.json`)
Complete gold layer data for CDA client including:
- All processed samples with classifications
- Machine-level status aggregations
- Component health assessments
- AI recommendations

### 2. EMIN Summary (`emin_summary.json`)
Complete gold layer data for EMIN client (same structure as CDA)

### 3. Stewart Limits (`stewart_limits.json`)
Reference thresholds for all essays across all machine/component combinations

---

## 🚦 Status Classifications

### Report Level
- **Normal**: essaySum < 3 points
- **Alerta**: 3 ≤ essaySum < 5 points
- **Anormal**: essaySum ≥ 5 points

### Machine Level
- **Normal**: totalStatus < 2 points
- **Alerta**: 2 ≤ totalStatus < 4 points
- **Anormal**: totalStatus ≥ 4 points

---

## 📈 Typical Processing Volumes

- **Raw Samples**: ~50-100 reports/week per client
- **Processing Time**: ~2-5 minutes for full pipeline
- **AI Recommendations**: Generated for ~30% of samples (non-Normal only)
- **Output Size**: ~1-5 MB per client summary file

---

## 🔐 Configuration

Key environment variables:
- `OPENAI_API_KEY`: OpenAI API key for AI recommendations
- `DATA_ROOT`: Root path for data files
- `MAX_WORKERS`: Parallel workers for AI generation (default: 18)

---

## 📞 Quick Start

1. **Run Pipeline**:
   ```bash
   python main.py
   ```

2. **Using Docker**:
   ```bash
   docker-compose up
   ```

3. **Check Output**:
   ```bash
   data/oil/processed/
   ├── cda_summary.json
   ├── emin_summary.json
   └── stewart_limits.json
   ```

For detailed instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).
