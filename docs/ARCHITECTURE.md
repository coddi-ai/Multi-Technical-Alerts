# Oil Analysis Data Product - Architecture

## 🎯 Product Definition

**Data Product**: Oil Analysis Processing Pipeline  
**Domain**: Mining Equipment Maintenance  
**Owner**: Predictive Maintenance Team  
**Consumers**: Fusion Service, Dashboard Applications, BI Tools

---

## 🏗️ Architecture Pattern

### Bronze-Silver-Gold Data Lake

```
┌─────────────────────────────────────────────────────────────┐
│                    Oil Analysis Data Product                 │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   BRONZE     │ ───▶ │   SILVER     │ ───▶ │    GOLD      │
│  Raw Layer   │      │ Curated Layer│      │ Product Layer│
└──────────────┘      └──────────────┘      └──────────────┘
     │                      │                      │
     │                      │                      │
  [Input]              [Processing]           [Output]
     │                      │                      │
     ▼                      ▼                      ▼
 Excel/Parquet      Standardization      cda_summary.json
 Lab Reports        + Classification     emin_summary.json
                    + AI Enrichment      stewart_limits.json
```

---

## 📦 Components

### 1. Data Ingestion (Bronze Layer)

**Purpose**: Immutable storage of raw laboratory data

**Sources**:
- **CDA Client**: Finning Laboratory (Excel format)
- **EMIN Client**: ALS Laboratory (Parquet format)

**Location**: `data/oil/raw/{client}/`

**Characteristics**:
- Read-only after ingestion
- Preserves original format
- Audit trail for compliance

---

### 2. Data Transformation (Silver Layer)

**Purpose**: Standardized, validated, clean data

**Processes**:
1. **Harmonization**
   - Column mapping
   - Data type conversion
   - Name normalization

2. **Quality Checks**
   - Minimum sample size validation
   - Missing value handling
   - Outlier detection

3. **Enrichment**
   - Stewart Limits calculation
   - Essay classification
   - Report status determination

**Location**: `data/oil/processed/`

**Characteristics**:
- Unified schema across all clients
- Quality-assured data
- Ready for analysis

---

### 3. AI Enhancement Layer

**Purpose**: Generate expert-level maintenance insights

**Technology**:
- **Model**: OpenAI GPT-4o-mini
- **Approach**: Few-shot learning with domain examples
- **Parallelization**: 18 concurrent workers

**Optimization**:
- AI only called for non-Normal reports (~30% of data)
- Caching mechanism for repeated patterns
- Error handling with fallback messages

**Output**: `aiRecommendation` field in gold layer

---

### 4. Gold Layer (Product Output)

**Purpose**: Analysis-ready data product for consumers

**Files**:
1. **`cda_summary.json`**
   - All CDA client samples with classifications
   - Machine-level aggregations
   - AI recommendations

2. **`emin_summary.json`**
   - All EMIN client samples with classifications
   - Machine-level aggregations
   - AI recommendations

3. **`stewart_limits.json`**
   - Reference thresholds for all essays
   - Client/machine/component granularity
   - Metadata (calculation date, sample count)

**Location**: `data/oil/processed/`

**SLA**: Updated daily at 2 AM (configurable)

---

## 🔄 Data Flow

### Processing Pipeline

```python
# Simplified pipeline flow
def oil_analysis_pipeline(client):
    # Step 1: Load raw data
    raw_data = load_bronze_layer(client)
    
    # Step 2: Transform to silver
    silver_data = harmonize_data(raw_data)
    silver_data = validate_quality(silver_data)
    
    # Step 3: Calculate limits
    limits = calculate_stewart_limits(silver_data)
    
    # Step 4: Classify samples
    classified_data = classify_essays(silver_data, limits)
    classified_data = classify_reports(classified_data)
    
    # Step 5: AI enrichment
    enriched_data = generate_ai_recommendations(classified_data)
    
    # Step 6: Aggregate to machine level
    machine_data = aggregate_to_machines(enriched_data)
    
    # Step 7: Export gold layer
    export_gold_layer(client, enriched_data, machine_data, limits)
```

---

## 📊 Data Schema

### Gold Layer Schema (Simplified)

```json
{
  "client": "cda",
  "generatedAt": "2024-02-03T10:30:00Z",
  "samples": [
    {
      "sampleId": "unique_identifier",
      "unitId": "CDA_001",
      "machineName": "camion",
      "componentName": "motor diesel",
      "sampleDate": "2024-01-15",
      "reportStatus": "Anormal",
      "essaySum": 6,
      "aiRecommendation": "...",
      "essays": {
        "Hierro": {
          "value": 55.2,
          "status": "Condenatorio",
          "threshold": 45.0
        }
      }
    }
  ],
  "machines": [
    {
      "unitId": "CDA_001",
      "machineStatus": "Alerta",
      "components": [...]
    }
  ]
}
```

---

## 🔐 Data Governance

### Data Quality Rules

| Rule | Threshold | Action |
|------|-----------|--------|
| Minimum samples per machine | 100 | Filter out |
| Minimum samples per component | 100 | Filter out |
| Minimum unique values per essay | 3 | Skip from limits |
| Missing value rate | >50% | Flag column |

### Client Isolation

- Separate folders for each client in bronze layer
- Independent processing pipelines
- Separate gold layer output files
- No cross-client data sharing

### Data Retention

- **Bronze**: Indefinite (source of truth)
- **Silver**: 1 year (for reprocessing)
- **Gold**: Latest version + 30 days history

---

## 🚀 Deployment Architecture

### Containerized Service

```
┌─────────────────────────────────────┐
│         Docker Container            │
│  ┌───────────────────────────────┐ │
│  │   Oil Analysis Pipeline       │ │
│  │                               │ │
│  │  - Data Loaders               │ │
│  │  - Transformers               │ │
│  │  - Stewart Limits Calculator  │ │
│  │  - AI Service Client          │ │
│  │  - Gold Layer Exporter        │ │
│  └───────────────────────────────┘ │
│           ▲              │          │
│           │              ▼          │
│     ┌─────────┐    ┌─────────┐     │
│     │  Data   │    │  Logs   │     │
│     │ Volume  │    │ Volume  │     │
│     └─────────┘    └─────────┘     │
└─────────────────────────────────────┘
         │                    │
         │                    └─ OpenAI API
         │
    Cron/Scheduler
```

### Execution Model

**Trigger**: Scheduled (Cron)  
**Frequency**: Daily at 2 AM  
**Duration**: 2-5 minutes  
**Resource Requirements**:
- CPU: 2 cores
- Memory: 4 GB
- Disk: 10 GB

---

## 🔌 Integration Points

### Inputs

1. **Laboratory Data Files**
   - **Protocol**: File upload to `data/oil/raw/{client}/`
   - **Format**: Excel (.xlsx) or Parquet (.parquet)
   - **Frequency**: Weekly batches

### Outputs

1. **Gold Layer Files** (Primary Interface)
   - **Protocol**: JSON files in shared volume
   - **Location**: `data/oil/processed/`
   - **Consumers**: Fusion Service, Dashboards

2. **Logs**
   - **Protocol**: File-based logs
   - **Location**: `logs/`
   - **Consumers**: Monitoring systems

---

## 📈 Scalability Considerations

### Current Capacity

- **Clients**: 2 (CDA, EMIN)
- **Samples per week**: ~100
- **Processing time**: 2-5 minutes

### Scale Limits

- **Vertical Scaling**: Up to 10 clients with current architecture
- **Horizontal Scaling**: Not currently supported (single-instance processing)

### Future Enhancements

1. **Streaming Processing**: Real-time sample ingestion
2. **Distributed Execution**: Apache Spark for larger volumes
3. **API Interface**: REST API for on-demand processing
4. **Event-Driven**: Kafka/EventGrid triggers

---

## 🎯 Data Mesh Principles

### Domain Ownership
- **Owner**: Predictive Maintenance Team
- **Responsibility**: Data quality, schema evolution, SLA compliance

### Data as a Product
- **Product**: Gold layer JSON files
- **Contract**: Versioned schema with backward compatibility
- **SLA**: 99% availability, <1 hour freshness

### Self-Serve Infrastructure
- **Deployment**: Docker Compose (one command)
- **Configuration**: Environment variables
- **Monitoring**: File-based logs with error tracking

### Federated Governance
- **Schema**: Documented in data contracts
- **Quality**: Automated validation rules
- **Access**: File-based (future: API gateway)

---

## 🔧 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.11+ | Core processing |
| **Data Processing** | Pandas, NumPy | Transformations |
| **AI** | OpenAI API (GPT-4o-mini) | Recommendations |
| **Orchestration** | Python scripts | Pipeline execution |
| **Containerization** | Docker | Deployment |
| **Storage** | File system (JSON, Parquet) | Data persistence |
| **Logging** | Python logging | Observability |

---

## 📊 Monitoring & Observability

### Key Metrics

1. **Processing Metrics**
   - Pipeline execution time
   - Samples processed per client
   - AI API call duration
   - Error rate

2. **Data Quality Metrics**
   - Samples filtered (quality issues)
   - Missing value percentage
   - Outlier detection rate

3. **Business Metrics**
   - % Normal/Alert/Abnormal reports
   - Machines requiring attention
   - AI recommendation coverage

### Logging Strategy

```
logs/
├── main_pipeline.log       # Execution logs
├── ai_service.log          # AI API interactions
├── data_quality.log        # Validation issues
└── errors.log              # Critical failures
```

---

## 🚦 Status & Roadmap

### ✅ Completed (v1.0)

- Bronze-Silver-Gold pipeline
- Multi-client support (CDA, EMIN)
- Stewart Limits calculation
- AI recommendation generation
- Docker deployment

### 🔄 In Progress

- API interface for on-demand queries
- Real-time data streaming
- Enhanced monitoring dashboard

### 📅 Planned

- Integration with other data products (telemetry, maintenance)
- Historical trend analysis
- Predictive failure models

---

## 📞 Support & Contact

**Data Product Owner**: Predictive Maintenance Team  
**Technical Lead**: [Name]  
**Documentation**: `docs/` folder in repository  
**Issue Tracking**: GitHub Issues
