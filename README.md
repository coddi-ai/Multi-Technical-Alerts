# Multi-Technical-Alerts

**AI-Powered Oil Analysis System for Mining Equipment Fleet Management**

---

## 🎯 Purpose

Multi-Technical-Alerts is an automated diagnostic and monitoring system designed to evaluate the health status of mining equipment through oil analysis. The system processes laboratory test results from multiple sources, applies statistical threshold detection, and leverages artificial intelligence to generate actionable maintenance recommendations.

The primary goal is to answer the critical question: **"How is my fleet performing?"** by transforming raw chemical essay data into clear, prioritized maintenance insights for fleet managers and maintenance teams.

---

## 🏗️ What This System Does

### 1. **Unified Data Processing**
The system consolidates oil analysis data from multiple laboratory providers (ALS and Finning) across different clients (EMIN and CDA), creating a standardized data model that enables cross-fleet analysis and comparison.

### 2. **Statistical Threshold Detection (Stewart Limits)**
Establishes dynamic alert thresholds for each chemical essay based on historical performance data, accounting for variations across different machine types and components. These limits define three severity levels:
- **Normal**: Within expected operating parameters
- **Alert**: Marginal values requiring monitoring
- **Anormal**: Critical values requiring immediate action

### 3. **Multi-Level Status Classification**
Implements a hierarchical assessment model that evaluates equipment health at three levels:

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

The AI system is trained with domain-specific examples from mechanical engineering experts specializing in mining equipment, ensuring recommendations are technically accurate and actionable.

### 5. **Fleet Performance Visualization**
Provides multi-perspective dashboards for stakeholders:
- **Executive View**: Fleet-wide health metrics and priority alerts
- **Operational View**: Machine-by-machine status with component breakdowns
- **Technical View**: Detailed essay analysis with temporal trends and historical comparisons

---

## 🔄 How It Works: The Report-Component-Machine Flow

Understanding the data hierarchy is essential:

1. **Each row in the raw data = One Report**
   - A report contains multiple chemical essays (Fe, Cu, Ag, Si, etc.)
   - Each essay measures a specific element or property in the oil sample

2. **Each Report is attached to One Component**
   - Components are specific parts within equipment (e.g., "Motor Diesel", "Transmision", "Hidraulico")
   - One component can have multiple reports over time (different sample dates)

3. **Each Component belongs to One Unit (Machine)**
   - Units are identified by `unitId` (e.g., "CDA_001", "EMIN_120")
   - One machine has multiple components being monitored

4. **The Analysis Flow**:
   ```
   i.   Analyze each essay against its Stewart Limits
   ii.  Compute a grade for the report based on essay breaches
   iii. Group reports by component to assess component health
   iv.  Aggregate component statuses to determine machine health
   v.   Report on fleet performance across all machines
   ```

This hierarchy enables precise diagnostics (identifying which specific component on which machine needs attention) while also providing aggregated insights for fleet management decisions.

---

## 📊 Key Outputs

### For Maintenance Teams:
- **Prioritized Action List**: Machines ranked by urgency requiring intervention
- **Component-Level Diagnostics**: Specific parts needing inspection or replacement
- **AI Recommendations**: Expert-level guidance on root causes and corrective actions

### For Fleet Managers:
- **Fleet Health Metrics**: Percentage of equipment in Normal/Alerta/Anormal status
- **Trend Analysis**: Historical performance tracking to predict failures
- **Resource Planning**: Data-driven scheduling for maintenance activities

### For Executives:
- **Operational Availability**: Fleet readiness metrics
- **Risk Assessment**: Equipment at critical status requiring immediate attention
- **Cost Optimization**: Preventive maintenance insights to avoid catastrophic failures

---

## 🧮 Technical Approach

The system employs:

- **Statistical Analysis**: Percentile-based threshold calculation (Stewart Limits methodology)
- **Natural Language Processing**: GPT-4 for context-aware recommendation generation
- **Parallel Processing**: Multi-threaded AI inference for scalability (18 concurrent workers)
- **Data Validation**: Quality checks to ensure reliable insights
- **Temporal Analysis**: Time-series tracking of component degradation

---

## 🗂️ Project Structure

```
Multi-Technical-Alerts/
├── data/
│   └── oil/
│       ├── raw/              # Bronze layer: Original lab reports
│       ├── processed/         # Silver layer: Standardized data
│       └── to_consume/        # Gold layer: Dashboard-ready data
├── notebooks/
│   └── explore_oil_full.ipynb   # Main analysis pipeline
└── src/                      # (Future) Production code modules
```

---

## 👥 Supported Clients

- **EMIN**: Uses ALS Laboratory for oil analysis
- **CDA**: Uses Finning Laboratory for oil analysis

Each client's data is processed independently to ensure privacy and enable client-specific threshold calibration.

---

## 🚀 Current Status

**Operational Components**:
- ✅ Data ingestion and harmonization
- ✅ Stewart Limits calculation
- ✅ Report classification system
- ✅ AI recommendation generation
- ✅ Machine status aggregation

**In Development**:
- ⏳ Interactive dashboards (Dash/Plotly)
- ⏳ Automated report scheduling
- ⏳ Email alert system
- ⏳ Historical trend analysis

---

## 📖 Documentation

For detailed information, refer to:
- **[Data Contracts](data_contracts.md)**: Data flow, schemas, and transformations
- **[Project Documentation](project_documentation.md)**: Business logic and calculation methods
- **[Dashboard Documentation](dashboard_documentation.md)**: Visualization specifications

---

## 🔒 Data Security

The system implements strict client isolation:
- Raw data is stored in separate client directories
- Processing pipelines maintain client separation
- Dashboards are pre-filtered to prevent cross-client data leakage

---

## 📞 Contact

**Author**: Patricio Ortiz  
**Project Type**: Mining Equipment Predictive Maintenance System
