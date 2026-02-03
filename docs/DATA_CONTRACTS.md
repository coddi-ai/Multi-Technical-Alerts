# Data Contracts - Oil Analysis Data Product

**Version**: 1.0  
**Last Updated**: February 3, 2026  
**Owner**: Oil Analysis Data Product Team

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Data Layer Architecture](#data-layer-architecture)
3. [Bronze Layer](#bronze-layer)
4. [Silver Layer](#silver-layer)
5. [Gold Layer](#gold-layer)
6. [Schema Definitions](#schema-definitions)
7. [Data Quality Rules](#data-quality-rules)
8. [Versioning and Compatibility](#versioning-and-compatibility)

---

## 🎯 Overview

This document defines the data contracts for the Oil Analysis Data Product, specifying the schema, format, and location of data at each processing layer (Bronze, Silver, Gold). These contracts ensure consistent data structure for downstream consumers and enable reliable data mesh integration.

**Data Product Purpose**: Process raw oil analysis laboratory results into actionable maintenance insights with AI-powered recommendations.

**Primary Consumers**:
- Fusion Service (aggregates multiple data products)
- Dashboard applications
- Business Intelligence tools
- Data analysts

---

## 🏗️ Data Layer Architecture

```
data/oil/
├── raw/                          # Bronze Layer (Immutable source data)
│   ├── cda/                      # CDA client raw files
│   │   ├── T-09.xlsx
│   │   ├── T-10.xlsx
│   │   └── ...
│   └── emin/                     # EMIN client raw files
│       ├── muestrasAlsHistoricos.parquet
│       └── Equipamiento.parquet
│
├── processed/                    # Silver Layer (Standardized, validated)
│   ├── stewart_limits.json       # Statistical thresholds (all clients)
│   ├── stewart_limits.parquet    # Flattened thresholds for querying
│   ├── cda_classified.parquet    # Legacy: CDA classified data
│   └── emin_classified.parquet   # Legacy: EMIN classified data
│
├── to_consume/                   # Gold Layer (Analysis-ready)
│   ├── CDA.parquet               # Silver layer output (harmonized)
│   ├── EMIN.parquet              # Silver layer output (harmonized)
│   ├── cda/                      # CDA Gold layer outputs
│   │   ├── classified_reports.parquet
│   │   └── machine_status_current.parquet
│   └── emin/                     # EMIN Gold layer outputs
│       ├── classified_reports.parquet
│       └── machine_status_current.parquet
│
└── essays_elements.xlsx          # Auxiliary: Essay metadata and mappings
```

---

## 📥 Bronze Layer

**Purpose**: Immutable storage of raw laboratory data  
**Update Frequency**: Weekly (new files added)  
**Retention**: Indefinite (source of truth)

### Location

```
data/oil/raw/{client}/
```

### Formats

#### CDA Client (Finning Laboratory)
- **Format**: Excel (.xlsx)
- **Structure**: Wide format (one column per essay)
- **Naming**: `T-{week_number}.xlsx`
- **Columns**: Variable (lab-specific column names in Spanish)

#### EMIN Client (ALS Laboratory)
- **Format**: Parquet (.parquet)
- **Structure**: Nested format (testName/testValue pairs)
- **Naming**: `muestrasAlsHistoricos.parquet`
- **Columns**: Variable (includes testName1, testValue1, testName2, testValue2, etc.)

### Contract Guarantees

✅ **Immutability**: Files are never modified after ingestion  
✅ **Completeness**: All source columns preserved  
✅ **Traceability**: Original file names and formats maintained  

### Quality Expectations

- No schema validation at this layer
- Files accepted as-is from laboratories
- Any format acceptable (Excel, Parquet, CSV)

---

## 🔄 Silver Layer

**Purpose**: Standardized, validated, harmonized data  
**Update Frequency**: Daily (after Bronze ingestion)  
**Retention**: 1 year

### Location

```
data/oil/processed/
```

### Files

#### 1. Stewart Limits (JSON)

**File**: `stewart_limits.json`  
**Format**: JSON  
**Purpose**: Statistical thresholds for classification

**Schema**:
```json
{
  "CDA": {
    "camion": {
      "motor diesel": {
        "Hierro": {
          "threshold_normal": 30.0,
          "threshold_alert": 45.0,
          "threshold_critic": 60.0,
          "count": 1250
        },
        "Cobre": { ... }
      }
    }
  },
  "EMIN": { ... }
}
```

**Nested Structure**: `{client} → {machineName} → {componentName} → {essayName} → thresholds`

**Update Trigger**: When `recalculate_limits=True` or new data significantly changes distribution

---

#### 2. Stewart Limits (Parquet)

**File**: `stewart_limits.parquet`  
**Format**: Parquet  
**Purpose**: Flattened thresholds for SQL-like querying

**Schema**:
```python
{
    'client': str,              # 'CDA' or 'EMIN'
    'machine': str,             # 'camion', 'pala', 'excavadora'
    'component': str,           # 'motor diesel', 'transmision', 'hidraulico'
    'essay': str,               # 'Hierro', 'Cobre', 'Silicio', etc.
    'threshold_normal': float,  # 90th percentile
    'threshold_alert': float,   # 95th percentile
    'threshold_critic': float   # 98th percentile
}
```

**Indexes**: Recommended index on `(client, machine, component, essay)`

---

#### 3. Harmonized Client Data (to_consume/)

**Files**: `CDA.parquet`, `EMIN.parquet`  
**Format**: Parquet  
**Purpose**: Standardized input for Gold layer processing

**Schema**: See [Silver Layer Schema](#silver-layer-schema) below

**Contract Guarantees**:
- ✅ All clients have identical schema
- ✅ Column names standardized (lowercase, no accents)
- ✅ Data types validated
- ✅ Minimum sample counts enforced

---

## 🥇 Gold Layer

**Purpose**: Analysis-ready data products for consumption  
**Update Frequency**: Daily (after pipeline completion)  
**Retention**: Latest + 30 days history  
**SLA**: 99% availability, <1 hour freshness

### Location

```
data/oil/to_consume/{client}/
```

### Files

#### 1. Classified Reports

**File**: `classified_reports.parquet`  
**Format**: Parquet (Snappy compression)  
**Purpose**: Complete oil sample analysis with classifications and AI recommendations

**Schema**: See [Classified Reports Schema](#classified-reports-schema) below

**Key Features**:
- Essay-level classifications (Normal, Marginal, Condenatorio, Crítico)
- Report-level status (Normal, Alerta, Anormal)
- AI-generated maintenance recommendations
- Historical essay values
- Stewart Limits breaches

**Typical Size**: 1-5 MB per client

---

#### 2. Machine Status Current

**File**: `machine_status_current.parquet`  
**Format**: Parquet (Snappy compression)  
**Purpose**: Current fleet health status aggregation

**Schema**: See [Machine Status Schema](#machine-status-schema) below

**Key Features**:
- One row per machine (unitId)
- Latest component statuses
- Machine-level health classification
- Summary of alerts

**Typical Size**: 10-100 KB per client

---

## 📊 Schema Definitions

### Bronze Layer Schema

No standardized schema (raw laboratory formats vary)

---

### Silver Layer Schema

**File**: `to_consume/{CLIENT}.parquet`

**Metadata Columns**:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `client` | string | Client identifier | "CDA", "EMIN" |
| `sampleNumber` | string | Unique sample ID | "24-012345" |
| `sampleDate` | datetime | Sample collection date | "2024-01-15" |
| `unitId` | string | Machine identifier | "CDA_001" |
| `machineName` | string | Machine type | "camion", "pala" |
| `machineModel` | string | Model designation | "789D", "PC5500" |
| `machineBrand` | string | Manufacturer | "caterpillar", "komatsu" |
| `machineHours` | float | Operating hours | 12500.0 |
| `machineSerialNumber` | string | Serial number | "CAT0XYZ123" |
| `componentName` | string | Component being sampled | "motor diesel", "transmision" |
| `componentHours` | float | Component hours | 8200.0 |
| `componentSerialNumber` | string | Component serial | "ENG456" |
| `oilMeter` | float | Oil volume (liters) | 45.5 |
| `oilBrand` | string | Oil manufacturer | "mobil", "shell" |
| `oilType` | string | Oil specification | "15W40", "10W30" |
| `oilWeight` | string | Viscosity grade | "15W40" |
| `previousSampleNumber` | string | Previous sample ID | "24-012340" |
| `previousSampleDate` | datetime | Previous sample date | "2023-12-15" |
| `daysSincePrevious` | int | Days since last sample | 31 |
| `group_element` | string | Essay grouping | "Metales de Desgaste" |

**Essay Columns** (variable, typically 30-50 columns):

| Column | Type | Description | Unit |
|--------|------|-------------|------|
| `Hierro` | float | Iron concentration | ppm |
| `Cobre` | float | Copper concentration | ppm |
| `Plomo` | float | Lead concentration | ppm |
| `Silicio` | float | Silicon concentration | ppm |
| `Aluminio` | float | Aluminum concentration | ppm |
| `Cromo` | float | Chromium concentration | ppm |
| `Viscosidad cinemática @ 40°C` | float | Kinematic viscosity | cSt |
| `TBN` | float | Total Base Number | mgKOH/g |
| `Agua` | float | Water content | % |
| ... | float | Additional essays | varies |

**Data Types**:
- All essay values: `float` (nullable for missing/invalid measurements)
- Dates: `datetime64[ns]`
- IDs and names: `string`

**Null Handling**:
- Missing essay values: `NaN`
- Missing metadata: `None` or empty string

---

### Classified Reports Schema

**File**: `to_consume/{client}/classified_reports.parquet`

**Inherits all columns from Silver Layer, plus:**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `essay_sum` | int | Sum of essay points | 6 |
| `report_status` | string | Report classification | "Normal", "Alerta", "Anormal" |
| `breached_essays` | string | JSON list of breached essays | "[{\"essay\":\"Hierro\",\"value\":55.2,\"status\":\"Condenatorio\"}]" |
| `ai_recommendation` | string | AI-generated maintenance advice | "Se detecta concentración elevada..." |
| `ai_generated_at` | datetime | AI generation timestamp | "2024-02-03T10:30:00Z" |
| `machine_status` | string | Machine-level status | "Normal", "Alerta", "Anormal" |
| `total_numeric_status` | int | Machine status points | 3 |

**Essay Classification Columns** (one per essay):

For each essay (e.g., `Hierro`), the following columns are added:

| Column | Type | Description |
|--------|------|-------------|
| `{essay}_status` | string | Classification ("Normal", "Marginal", "Condenatorio", "Crítico") |
| `{essay}_points` | int | Points assigned (0, 1, 3, 5) |
| `{essay}_threshold` | float | Breached threshold value |

**Example Essay Classification**:
- `Hierro_status`: "Condenatorio"
- `Hierro_points`: 3
- `Hierro_threshold`: 45.0

**Contract Guarantees**:
- ✅ All rows have `report_status`
- ✅ `ai_recommendation` is non-null for non-Normal reports
- ✅ `essay_sum` = sum of all essay points
- ✅ `breached_essays` is valid JSON or null

**Partitioning Recommendation**: Partition by `sampleDate` (YYYY-MM-DD) for time-based queries

---

### Machine Status Schema

**File**: `to_consume/{client}/machine_status_current.parquet`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `client` | string | Client identifier | "CDA" |
| `unitId` | string | Machine identifier | "CDA_001" |
| `machineName` | string | Machine type | "camion" |
| `machineModel` | string | Model designation | "789D" |
| `machine_status` | string | Overall machine health | "Normal", "Alerta", "Anormal" |
| `total_numeric_status` | int | Sum of component status points | 3 |
| `number_components` | int | Components monitored | 4 |
| `last_sample_date` | datetime | Most recent sample date | "2024-02-01" |
| `components_normal` | int | Count of Normal components | 2 |
| `components_alerta` | int | Count of Alerta components | 1 |
| `components_anormal` | int | Count of Anormal components | 1 |
| `component_summary` | string | JSON array of component statuses | "[{\"component\":\"motor diesel\",\"status\":\"Anormal\"}]" |
| `priority_score` | int | Urgency ranking (higher = more urgent) | 10 |
| `last_ai_recommendation` | string | Most recent AI recommendation | "..." |

**Sorting Recommendation**: Order by `priority_score DESC, last_sample_date DESC`

**Contract Guarantees**:
- ✅ One row per unique `unitId`
- ✅ `last_sample_date` reflects most recent sample across all components
- ✅ `number_components` = sum of (normal + alerta + anormal)
- ✅ `component_summary` is valid JSON array

---

## ✅ Data Quality Rules

### Bronze Layer

No validation (accept as-is from laboratories)

### Silver Layer

| Rule | Enforcement | Action if Failed |
|------|-------------|------------------|
| `machineName` has ≥100 samples | Filter | Drop machine |
| `componentName` has ≥100 samples | Filter | Drop component |
| Essay values are numeric | Validation | Convert or set to NaN |
| `sampleDate` is valid datetime | Validation | Drop row |
| No duplicate `sampleNumber` | Uniqueness | Keep most recent |
| Client field matches file location | Consistency | Override with correct client |

### Gold Layer

| Rule | Enforcement | Action if Failed |
|------|-------------|------------------|
| `report_status` is in {Normal, Alerta, Anormal} | Enum | Log error, set to "Unknown" |
| `essay_sum` matches sum of essay points | Calculation | Recalculate |
| `ai_recommendation` exists for non-Normal | Completeness | Generate or set placeholder |
| All essay columns have `_status`, `_points`, `_threshold` | Schema | Add missing columns with nulls |

---

## 🔄 Versioning and Compatibility

### Schema Version

**Current Version**: `1.0`  
**Version Field**: Not yet included in data (future enhancement)

### Backward Compatibility Promise

**Gold Layer Guarantees**:
1. ✅ Existing columns will never be removed
2. ✅ New columns will be added at the end
3. ✅ Data types will not change (exception: widening only, e.g., int32 → int64)
4. ✅ Enum values will not be removed (new values may be added)

**Breaking Changes**:
- Will be announced 30 days in advance
- Major version increment (1.0 → 2.0)
- Migration guide provided

### Evolution Guidelines

**Safe Changes** (no version increment):
- Adding new essay columns
- Adding new metadata columns
- Adding new enum values to `report_status`

**Minor Changes** (patch version increment, e.g., 1.0 → 1.1):
- Changing column descriptions
- Adding indexes
- Performance optimizations

**Major Changes** (major version increment, e.g., 1.0 → 2.0):
- Removing columns
- Changing data types (narrowing)
- Changing enum values
- Changing file locations

---

## 📦 File Format Specifications

### Parquet Configuration

**Compression**: Snappy (balance between speed and size)  
**Row Group Size**: 128 MB  
**Page Size**: 1 MB  
**Index**: Automatically created on write

**Reason for Snappy**: Fast compression/decompression, widely supported, good compression ratio (~2:1)

### JSON Configuration

**Encoding**: UTF-8  
**Indentation**: 2 spaces  
**Date Format**: ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`)  
**Ensure ASCII**: False (allow Spanish characters)

---

## 🔗 Integration Points

### S3 Bucket Structure

```
s3://oil-analysis-data-product/
├── bronze/{client}/{date}/          # Raw files
├── silver/                          # Harmonized data
│   ├── stewart_limits.parquet
│   ├── CDA.parquet
│   └── EMIN.parquet
└── gold/{client}/                   # Analysis-ready
    ├── classified_reports.parquet
    └── machine_status_current.parquet
```

### API Interface 

**Endpoint**: `GET /api/v1/{client}/classified-reports`  
**Response Format**: JSON (paginated)  
**Authentication**: API key

---

## 📞 Support

**Data Contract Owner**: Data Team
**Contact**: patricio@coddi.ai 
**Documentation**: This file + inline code docstrings  

---

## 📝 Changelog

### Version 1.0 (2024-02-03)
- Initial data contract definition
- Bronze-Silver-Gold layer structure
- Schema definitions for all layers
- Data quality rules
- Versioning policy
