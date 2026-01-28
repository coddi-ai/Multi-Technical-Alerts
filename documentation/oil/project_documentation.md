# Project Documentation

**Multi-Technical-Alerts - Business Logic and Implementation Details**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Data Treatment Pipeline](#data-treatment-pipeline)
3. [Stewart Limits Methodology](#stewart-limits-methodology)
4. [Classification System](#classification-system)
5. [AI Integration](#ai-integration)
6. [Dashboard Overview](#dashboard-overview)
7. [Business Rules Reference](#business-rules-reference)

---

## 🎯 Overview

This document describes the **business logic** that drives the Multi-Technical-Alerts system. It explains:
- How raw laboratory data is transformed into actionable insights
- The statistical methods used to establish alert thresholds
- The multi-level classification system for equipment health assessment
- How AI generates contextual maintenance recommendations
- The dashboard structure for stakeholder consumption

---

## 🔄 Data Treatment Pipeline

### **High-Level Flow**

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
         ▼ [AI Enhancement]
┌─────────────────┐
│   AI-Enhanced   │  Final Output
│  Recommendations│  - Contextual insights
└────────┬────────┘  - Maintenance actions
         │
         ▼ [Aggregation]
┌─────────────────┐
│   Dashboard     │  Visualization Layer
│   Ready Data    │  - Machine status summaries
└─────────────────┘  - Component health views
```

---

## 📊 Data Treatment Details

### **1. Laboratory-Specific Processing**

#### **CDA (Finning Laboratory) - Wide Format**

**Input Structure**: Each essay has its own column
```
| sampleNumber | Fecha | Hierro | Cobre | Silicio | ... |
```

**Treatment**:
1. ✅ **Direct column mapping** - Essays already in separate columns
2. ✅ **Rename columns** using Spanish standardization (via `essays_elements.xlsx`)
3. ✅ **Add missing metadata** - Infer `machineName` from `machineModel` using mapping dictionary
4. ✅ **Format standardization** - Lowercase component names, replace hyphens in `unitId`

---

#### **EMIN (ALS Laboratory) - Nested Format**

**Input Structure**: Essays stored in testName/testValue pairs
```
| sampleNumber | testName1 | testValue1 | testName2 | testValue2 | ... |
```

**Treatment**:
1. ✅ **Melt operation** - Convert name columns to long format
2. ✅ **Melt operation** - Convert value columns to long format
3. ✅ **Merge & Pivot** - Join on `test_number`, pivot to wide format
4. ✅ **Value cleaning**:
   - Remove hyphens (`'-'` → `NaN`)
   - Replace commas (`'12,5'` → `12.5`)
   - Handle detection limits (`'<0.05'` → `0`, `'>0.05'` → `0.1`)
   - Convert to numeric, coerce errors
5. ✅ **Filter valid data** - Drop rows with unconvertible essay values

**Result**: Both sources arrive at identical schema for unified analysis

---

### **2. Name Standardization**

**Goal**: Reduce cardinality and ensure consistency across data sources

#### **Function: `nameProtocol`**

Normalizes all text fields to lowercase, accent-free format:

```python
Input:  "Transmisión Delantera"
Step 1: Normalize unicode → "Transmision Delantera"
Step 2: Encode to ASCII → "Transmision Delantera"
Step 3: Lowercase → "transmision delantera"
Step 4: Replace accents → "transmision delantera"
Output: "transmision delantera"
```

**Applied to**: `machineName`, `componentName`, `machineBrand`

---

#### **Function: `reduceCardinalityNames`**

Maps similar names to canonical forms:

**machineName Examples**:
```python
"bulldozer D11" → "bulldozer"
"pala hidraulica" → "pala"
"camión tolva 789" → "camion"
```

**componentName Examples**:
```python
"mando final izquierdo" → "mando final"
"mando final derecho" → "mando final"
"transmision principal" → "transmision"
"trasmision" (typo) → "transmision"
"aceite motor diesel" → "aceite"
"refrig sistema" → "refrigerante"
```

**machineBrand Examples**:
```python
"CAT" → "caterpillar"
"Caterpillar Inc." → "caterpillar"
```

**Business Justification**: 
- Lab technicians use inconsistent naming
- Left/right components aggregate to single category
- Typos (transmision vs trasmision) unified
- Enables statistical analysis with sufficient sample sizes

---

### **3. Data Quality Filtering**

**Invalid Sample Removal**:

```python
def filterInvalidSamples(df):
    # Rule 1: Machine must have ≥100 samples
    valid_machines = df['machineName'].value_counts()
    valid_machines = valid_machines[valid_machines >= 100].index
    df = df[df['machineName'].isin(valid_machines)]
    
    # Rule 2: Component must have ≥100 samples
    valid_components = df['componentName'].value_counts()
    valid_components = valid_components[valid_components >= 100].index
    df = df[df['componentName'].isin(valid_components)]
    
    return df
```

**Rationale**:
- Stewart Limits require sufficient historical data for statistical validity
- <100 samples → unstable percentile calculations → unreliable thresholds
- Filters out rare machine types and experimental components

---

## 📈 Stewart Limits Methodology

### **Statistical Foundation**

Stewart Limits is a **percentile-based threshold detection** method used in condition monitoring. It establishes dynamic limits based on historical performance rather than fixed manufacturer specifications.

**Advantages**:
- ✅ **Adaptive**: Accounts for machine-specific operating conditions
- ✅ **Context-aware**: Different limits for different components
- ✅ **Data-driven**: No need for OEM specifications (often unavailable)

---

### **Calculation Process**

**Granularity**: Limits are calculated **independently** for each unique combination:
```
client → machineName → componentName → essayName
```

**Example**: 
- `CDA → camion → motor diesel → Hierro` has **different limits** than
- `EMIN → pala → motor diesel → Hierro`

---

**Algorithm**:

```python
def stewart_limits(serie):
    """
    Calculate statistical thresholds for a data series
    
    Percentiles:
        - Normal < 90th percentile
        - Alert  < 95th percentile
        - Critic < 98th percentile
    """
    # 1. Remove zeros and nulls (lab measurement artifacts)
    serie = serie[serie != 0].dropna()
    
    # 2. Calculate percentiles
    normal = np.ceil(serie.quantile(0.90))   # 90th percentile
    alert = np.ceil(serie.quantile(0.95))    # 95th percentile
    critic = np.ceil(serie.quantile(0.98))   # 98th percentile
    
    # 3. Enforce monotonicity (limits must increase)
    if alert <= normal:
        alert = normal + 1
    if critic <= alert:
        critic = alert + 1
    
    return {
        'threshold_normal': normal,
        'threshold_alert': alert,
        'threshold_critic': critic,
    }
```

---

### **Percentile Selection Rationale**

| Threshold | Percentile | Meaning | Business Rule |
|-----------|-----------|---------|---------------|
| **Normal** | 90th | "Top 10% of historical values" | Monitor but no immediate action |
| **Alert** | 95th | "Top 5% of historical values" | Schedule inspection |
| **Critic** | 98th | "Top 2% of historical values" | Urgent intervention required |

**Why these percentiles?**
- Derived from **tribology engineering standards** for wear monitoring
- Balance between sensitivity (catching real issues) and specificity (avoiding false alarms)
- Industry practice in mining equipment maintenance

---

### **Handling Edge Cases**

**Problem**: For stable systems, percentiles may be identical (e.g., constant essay value)

**Solution**: Enforce minimum separation
```python
# Example: All historical Hierro values are 25 ppm
quantile(0.90) = 25
quantile(0.95) = 25  
quantile(0.98) = 25

# After enforcement:
threshold_normal = 25
threshold_alert = 26   # Force +1
threshold_critic = 27  # Force +1
```

This ensures the classification system always has distinct thresholds.

---

### **Essay Inclusion Criteria**

Not all essays are included in Stewart Limits:

```python
for essay in all_essays:
    if essay in component_data.columns:
        if component_data[essay].nunique() > 3:
            # Calculate limits
        else:
            # Skip - insufficient variance
```

**Rationale**: Essays with ≤3 unique values have insufficient variance for meaningful percentiles (e.g., binary presence/absence tests)

---

## 🏷️ Classification System

### **Multi-Level Hierarchy**

The system implements a **three-tier classification**:

```
Essay Level    →  Report Level    →  Machine Level
(Individual)      (Sample)            (Equipment)

Fe: Critico       Anormal            Anormal
Cu: Normal        (5 points)         (3 components)
Si: Marginal
```

---

### **Level 1: Essay Classification**

**Threshold Comparison**:

```python
def identify_threshold(value, marginal, condenatorio, critico):
    """
    Classify a single essay value against Stewart Limits
    
    Returns: (status_name, threshold_value) or (None, None)
    """
    if pd.isna(value):
        return None, None
    elif value >= critico:
        return 'Critico', critico
    elif value >= condenatorio:
        return 'Condenatorio', condenatorio
    elif value >= marginal:
        return 'Marginal', marginal
    else:
        return None, None  # Within normal range
```

**Example**:
- Hierro value: 55 ppm
- Limits: Normal=30, Alert=45, Critic=60
- Result: `'Condenatorio'` (value 55 is ≥45 but <60)

---

### **Level 2: Report Classification**

**Point Assignment**:

Each essay breach is assigned points based on severity:

| Essay Status | Points | Interpretation |
|--------------|--------|----------------|
| None | 0 | Within normal limits |
| **Marginal** | 1 | Slightly elevated, monitor |
| **Condenatorio** | 3 | Significantly elevated, schedule action |
| **Critico** | 5 | Critically elevated, urgent action |

---

**Report Score Calculation**:

```python
essaySum = Σ(points for each essay in report)

if essaySum < 3:
    reportStatus = 'Normal'
elif essaySum >= 5:
    reportStatus = 'Anormal'
else:
    reportStatus = 'Alerta'
```

**Business Logic**:

| Scenario | Example Essays | Points | Status | Meaning |
|----------|---------------|--------|--------|---------|
| All normal | - | 0 | **Normal** | No action required |
| One marginal | Fe: Marginal | 1 | **Normal** | Single minor issue, monitor |
| Two marginals | Fe: Marginal, Cu: Marginal | 2 | **Normal** | Multiple minor issues, watch closely |
| Three marginals OR one condenatorio | Fe+Cu+Si: Marginal OR Fe: Condenatorio | 3 | **Alerta** | Schedule inspection |
| One condenatorio + marginals | Fe: Condenatorio, Cu: Marginal | 4 | **Alerta** | Multiple issues, prioritize |
| One critico OR multiple condenatorios | Fe: Critico OR Fe+Cu: Condenatorio | 5+ | **Anormal** | Urgent intervention |

**Key Threshold**:
- **<3 points**: Acceptable operating condition
- **≥5 points**: Unacceptable condition requiring immediate action
- **3-4 points**: Intermediate state requiring scheduled maintenance

---

### **Level 3: Machine Classification**

**Goal**: Aggregate component-level reports into overall machine health status

**Process**:

1. **Get Latest Reports**: For each component, select most recent sample
   ```python
   last_reports = df.groupby(['unitId', 'componentName'])['sampleDate'].max()
   ```

2. **Map to Numeric**:
   ```python
   numericReportStatus = {
       'Normal': 0,
       'Alerta': 1,
       'Anormal': 2
   }
   ```

3. **Sum Across Components**:
   ```python
   totalNumericStatus = Σ(numericReportStatus for each component)
   ```

4. **Classify Machine**:
   ```python
   if totalNumericStatus < 2:
       machineStatus = 'Normal'
   elif totalNumericStatus >= 4:
       machineStatus = 'Anormal'
   else:
       machineStatus = 'Alerta'
   ```

---

**Example Calculation**:

**Machine CDA_001** has 4 monitored components:

| Component | Latest Report Status | Points |
|-----------|---------------------|--------|
| Motor Diesel | Anormal | 2 |
| Transmision | Normal | 0 |
| Hidraulico | Alerta | 1 |
| Mando Final | Normal | 0 |
| **Total** | - | **3** |

**Result**: `3 points` → **machineStatus = 'Alerta'**

**Business Interpretation**: 
- Machine has one critical component (Motor Diesel) requiring attention
- Overall machine operational but needs scheduled maintenance
- Not urgent enough to halt operations immediately

---

**Machine Status Thresholds**:

| Points | Status | Operational Meaning |
|--------|--------|-------------------|
| 0-1 | **Normal** | Fleet ready, routine monitoring |
| 2-3 | **Alerta** | Schedule maintenance, monitor closely |
| ≥4 | **Anormal** | Multiple critical issues, prioritize intervention |

**Rationale**:
- One Anormal component (2 points) doesn't fail entire machine → Alerta
- Two Anormal components (4 points) → critical situation → Anormal
- Multiple Alerta components accumulate → triggers machine-level Alerta/Anormal

---

## 🤖 AI Integration

### **Purpose**

AI generates **contextual, actionable maintenance recommendations** that:
- Interpret **why** essays are elevated (root cause analysis)
- Suggest **specific corrective actions** (not generic advice)
- Provide **expert-level insights** (mechanical engineering knowledge)
- Include **urgency indicators** and follow-up schedules

---

### **When AI is Called**

**Optimization Strategy**: AI is **only** invoked for non-Normal reports

```python
if reportStatus == 'Normal':
    aiRecommendation = "No se detectan anomalías en los parámetros analizados."
    # Skip expensive API call
else:
    # Call OpenAI API
    aiRecommendation = create_recommendation(prompt, client)
```

**Cost Justification**:
- Typical fleet: 70-80% Normal reports
- AI cost: ~$0.0001/token × 500 tokens = $0.05 per report
- Savings: 70% × $0.05 = **$0.035 per report** (70% cost reduction)

---

### **AI Model Configuration**

```python
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.9
MAX_WORKERS = 18  # Parallel processing threads
```

**Parameter Choices**:
- **gpt-4o-mini**: Balances cost and quality (vs. gpt-4-turbo)
- **Temperature 0.9**: Higher creativity for varied recommendations (vs. deterministic 0.0)
- **18 workers**: Optimal for I/O-bound API calls without rate limiting

---

### **Prompt Engineering**

#### **System Prompt (Context)**:

```python
context = {
    "role": "system",
    "content": """
    Eres un ingeniero mecánico, especialista en equipos mineros y debes 
    realizar diagnósticos precisos sobre las medidas de un equipo, 
    entregando comentarios breves respecto a los análisis de aceite 
    realizados y recomendaciones concretas de mantención. 
    
    Considera que al haber presencia de Zinc, Bario, Boro, Calcio, 
    Molibdeno, Magnesio o Fósforo en el aceite no se debe sugerir 
    cambio de componentes o de aceite.
    
    Tus respuestas deben ser de 150 palabras o menos.
    """
}
```

**Key Elements**:
1. **Role**: Mechanical engineer specializing in mining equipment
2. **Task**: Diagnose oil analysis results, provide maintenance recommendations
3. **Domain Knowledge**: Zinc/Barium/Boron/Calcium/Molybdenum/Magnesium/Phosphorus are **oil additives**, not wear indicators
4. **Constraint**: ≤150 words (concise, actionable)

---

#### **Few-Shot Examples**:

The system includes **3 calibration examples** to guide response style:

**Example 1: Water Contamination + Viscosity Issue**
```
Input: 
  Componente: Aceite motor Diesel 15W40
  Agua: 8.3% (limit: 0.3%)
  Viscosidad @ 40°C: 144.6 cSt (limit: 138.0)

Response:
  "Se aprecian niveles de desgaste y contaminación externa entre 
  límites permisibles, sin embargo, se detecta contenido de agua 
  8,3% en volumen de muestra. Grado de viscosidad sobre límite 
  superior condenatorio 144,6 por posibles rellenos con lubricante 
  de ISO VG mayor.
  
  Se sugiere cambio de lubricante y mantener seguimiento riguroso 
  cada 125 horas, para evidenciar alzas abruptas de sodio y potasio 
  por eventual traspaso de refrigerante. Monitorear consumos de 
  aceite y gases blancos en salida de escape."
```

**Example 2: Wear Metals + Contamination**
```
Input:
  Componente: Motor Diesel
  Máquina: Camión Tolva
  Hierro: 31.1 ppm (marginal)
  Cobre: 267.7 ppm (condenatorio)
  Silicio: 30.7 ppm (condenatorio)
  PQ Index: 20.0 (marginal)
  Viscosidad @ 100°C: 10.7 cSt (bajo condenatorio)
  Dilución combustible: 0.8% (condenatorio)

Response:
  "Se detecta concentración de metales de desgaste por Fierro 31.1 ppm 
  y Cobre 267.7 ppm, evidenciando posible abrasión excesiva en 
  cojinetes y bujes de turbo. Silicio 30.7 ppm señala ingesta excesiva 
  de polvo ambiental. Análisis fisicoquímico detecta material ferroso 
  en suspensión Índice PQ 20.0. Se evidencia Dilución por combustible 
  de 0.8%, detectando posible anormalidad en bomba de transferencia o 
  sellos de inyectores, provocando una baja ligera en viscosidad en 
  lubricante.
  
  Se recomienda priorizar cambio de lubricante y elementos filtrantes, 
  evaluar presiones en sistema de lubricación y saturación temprana de 
  filtros, mantener seguimiento riguroso cada 50 hrs."
```

**Example 3: Fuel Dilution**
```
Input:
  Componente: Motor Diesel Cummins
  Máquina: Camión Komatsu 730-E
  Dilución combustible: 2.2% (condenatorio)

Response:
  "Niveles de desgaste y contaminaciones determinadas por espectrometría 
  en tamaño y concentraciones admisibles para la operación, sin embargo, 
  análisis físico químico detecta Dilución por combustible 2.2%, altamente 
  perjudicial para la operación, evidenciando posibles anomalías en 
  toberas o sellos de inyectores. Grado de visosidad normal en lubricante.
  
  Se sugiere priorizar intervención mecánica y efectuar cambio de 
  lubricante, junto con envío de contramuestra para realizar seguimiento 
  a deterioro en sellos/toberas de inyectores o bomba de transferencia. 
  Evaluar presiones en sistema de lubricación y saturación temprana 
  de filtros."
```

---

**Example Patterns Teach**:
1. **Structure**: Diagnosis → Root cause → Specific actions → Follow-up
2. **Technical terminology**: "abrasión excesiva", "bujes de turbo", "sellos de inyectores"
3. **Root cause linking**: High Cu → turbo bearing wear, High Si → dust ingestion
4. **Specific actions**: Not just "check oil" but "evaluar presiones en sistema de lubricación"
5. **Follow-up intervals**: "seguimiento cada 50 hrs", "cada 125 horas"

---

#### **User Prompt (Data)**:

```python
def create_final_prompt(sample, breached_essays):
    return f"""
    Analiza una muestra para el siguiente equipo:
    Componente: {sample['componentName']}
    Máquina: {sample['machineName']} - {sample['machineModel']}
    
    Los valores de la muestra son:
    {breached_essays}
    """
```

`breached_essays` DataFrame format:
```
| elemento                      | valor | limite transgredido | valor_limite |
|------------------------------|-------|---------------------|--------------|
| Hierro                       | 55.2  | Condenatorio        | 45.0         |
| Cobre                        | 28.1  | Marginal            | 25.0         |
| Viscosidad cinemática @ 40°C | 152.3 | Critico             | 138.0        |
```

---

### **Parallel Processing**

**Implementation**:

```python
def generate_all_recommendations(df, limits, client, max_workers=18):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_id = {
            executor.submit(process_single_identifier, id, df, limits, client): id
            for id in unique_sample_ids
        }
        
        # Collect results with progress bar
        for future in as_completed(future_to_id):
            result = future.result()
            results.append(result)
    
    return pd.DataFrame(results)
```

**Performance**:
- **Sequential**: 1000 reports × 2s/call = **33 minutes**
- **Parallel (18 workers)**: 1000 reports ÷ 18 × 2s = **~2 minutes**
- **Speedup**: **16x faster**

---

### **Error Handling**

```python
def process_single_identifier(identifier, df, limits, client):
    try:
        result = orchestrate_comment(df, identifier, limits, client)
        return result
    except ValueError as e:
        # Data quality issue (missing identifier, invalid data)
        logger.warning(f"Skipping {identifier}: {e}")
        return None
    except Exception as e:
        # API error, network issue, etc.
        logger.error(f"Error processing {identifier}: {e}")
        return None
```

**Failure Modes**:
- **Missing data**: Skip sample, log warning
- **API timeout**: Retry (OpenAI client has built-in retry logic)
- **Rate limiting**: ThreadPoolExecutor naturally throttles via worker limit
- **Invalid response**: Log error, continue with next sample

---

## 📊 Dashboard Overview

### **Purpose**

Provide **multi-perspective views** of fleet health for different stakeholder needs:

| Stakeholder | Primary Question | Dashboard Tab |
|-------------|-----------------|---------------|
| **Executive** | "What's the overall fleet status?" | 🚜 Machine Status |
| **Maintenance Manager** | "Which machines need attention this week?" | 🚜 Machine Status |
| **Technician** | "What's wrong with this specific sample?" | 📝 Report Detail |
| **Engineer** | "What are the alert thresholds for this component?" | 📊 Limit Visualization |

---

### **Dashboard Structure**

**Framework**: Dash + Plotly  
**Client Isolation**: Pre-filtered data (no cross-client visibility)  
**Update Frequency**: Real-time (reads latest Gold layer files)

---

### **Tab 1: 📊 Limit Visualization**

**Purpose**: Display Stewart Limits for transparency and threshold verification

**Components**:
1. **Machine Dropdown**: Select machine type (e.g., "camion", "pala")
2. **Component Dropdown**: Select component (filtered by machine)
3. **Limits Table**: Shows thresholds for all essays in selected machine-component pair

**Table Schema**:
```
| Essay                        | threshold_normal | threshold_alert | threshold_critic |
|------------------------------|------------------|-----------------|------------------|
| Hierro                       | 30.0             | 45.0            | 60.0             |
| Cobre                        | 15.0             | 25.0            | 35.0             |
| Silicio                      | 17.0             | 30.0            | 45.0             |
| Viscosidad cinemática @ 40°C | 135.0            | 138.0           | 142.0            |
```

**Use Cases**:
- Engineer reviews if thresholds are realistic
- Technician checks why a report was flagged
- Quality assurance audit

---

### **Tab 2: 🚜 Machine Status**

**Purpose**: Fleet-wide health monitoring and prioritization

**Sections**:

1. **📊 Distribución del Estado General por Máquina** (Machine-Level Distribution)
   - **Pie Chart**: % of machines in Normal/Alerta/Anormal status
   - **Priority Table**: Top 10 machines by `totalNumericStatus` (worst first)

2. **🎯 Detalle Estado General por Máquina** (Machine Detail Table)
   - Columns: `unitId`, `machineType`, `machineStatus`, `numberComponents`, `lastSampleDate`, `Summary`
   - `Summary` format: "3 components in Alerta: [motor diesel, transmision, hidraulico]"

3. **📈 Distribución de Estados por Componente** (Report-Level Distribution)
   - **Pie Chart**: % of reports in Normal/Alerta/Anormal status
   - **Histogram**: Reports per component, stacked by status

4. **🎯 Detalle Estado General por Componente** (Component Detail Table)
   - Columns: `unitId`, `componentName`, `lastSampleDate`, `AI Recommendation`

**Key Difference Between Section 1 & 3**:
- **Section 1**: "Of 100 machines, how many are Normal/Alerta/Anormal?"
- **Section 3**: "Of 100 reports, how many are Normal/Alerta/Anormal?"
- Example: One machine with 4 Anormal components → 1 Anormal machine, 4 Anormal reports

---

### **Tab 3: 📝 Report Detail**

**Purpose**: Deep-dive analysis of individual oil samples

**Sections**:

1. **📊 Análisis del Reporte** (Report Analysis)
   - **Radar Charts**: One per `GroupElement` (e.g., "Metales de Desgaste", "Contaminantes")
     - Each radar shows essay values vs. thresholds
     - Multiple limit lines (normal, alert, critic)
   - **Raw Values Table**: `Essay`, `Value`, `Threshold Normal`, `Threshold Alert`, `Threshold Critic`

2. **🤖 Recomendaciones de Mantenimiento** (AI Recommendations)
   - Text display of `aiRecommendation` field
   - Formatted with markdown for readability

3. **📈 Evolución Temporal** (Temporal Evolution)
   - **Time Series Chart**: Essay values over time for selected `unitId`
   - Shows trend (improving/degrading)
   - Overlay threshold lines

4. **🔄 Comparación con Reportes Anteriores** (Historical Comparison)
   - **Comparison Table**: Current vs. previous sample
   - Columns: `Essay`, `Previous Value`, `Current Value`, `Absolute Change`, `% Change`

---

## 📚 Business Rules Reference

### **Quick Reference Table**

| Rule Category | Rule | Value |
|---------------|------|-------|
| **Stewart Limits** | Normal threshold | 90th percentile |
| | Alert threshold | 95th percentile |
| | Critic threshold | 98th percentile |
| | Minimum samples per machine | 100 |
| | Minimum samples per component | 100 |
| | Minimum unique values per essay | >3 |
| **Essay Points** | Marginal | 1 point |
| | Condenatorio | 3 points |
| | Critico | 5 points |
| **Report Classification** | Normal | essaySum < 3 |
| | Alerta | 3 ≤ essaySum < 5 |
| | Anormal | essaySum ≥ 5 |
| **Machine Classification** | Report points - Normal | 0 |
| | Report points - Alerta | 1 |
| | Report points - Anormal | 2 |
| | Machine Normal | totalNumericStatus < 2 |
| | Machine Alerta | 2 ≤ totalNumericStatus < 4 |
| | Machine Anormal | totalNumericStatus ≥ 4 |
| **AI Configuration** | Model | gpt-4o-mini |
| | Temperature | 0.9 |
| | Max words | 150 |
| | Parallel workers | 18 |
| | AI called for | Non-Normal reports only |

---

### **Decision Matrices**

#### **Report Status Decision Matrix**

| Essay Points | Example Scenario | Status |
|--------------|-----------------|--------|
| 0 | All essays normal | Normal |
| 1 | 1 Marginal | Normal |
| 2 | 2 Marginal | Normal |
| 3 | 3 Marginal OR 1 Condenatorio | **Alerta** |
| 4 | 1 Condenatorio + 1 Marginal | **Alerta** |
| 5 | 1 Critico OR 1 Condenatorio + 2 Marginal | **Anormal** |
| 6+ | 2 Condenatorio OR 1 Critico + 1 Marginal | **Anormal** |

---

#### **Machine Status Decision Matrix**

| Component Statuses | Total Points | Machine Status |
|--------------------|--------------|----------------|
| 3 Normal, 1 Normal | 0 | Normal |
| 2 Normal, 1 Alerta, 1 Normal | 1 | Normal |
| 2 Normal, 2 Alerta OR 1 Anormal | 2 | **Alerta** |
| 1 Normal, 2 Alerta, 1 Anormal | 3 | **Alerta** |
| 2 Anormal OR 4 Alerta | 4 | **Anormal** |
| Any combination ≥4 points | ≥4 | **Anormal** |

---

## 🔄 Processing Workflow

**End-to-End Flow**:

```
1. Data Ingestion
   ↓
2. Harmonization (Bronze → Silver)
   ↓
3. Stewart Limits Calculation (every N days or when data changes significantly)
   ↓
4. Essay Classification (compare values vs limits)
   ↓
5. Report Classification (aggregate essay points)
   ↓
6. AI Recommendation (parallel, for non-Normal only)
   ↓
7. Machine Status Aggregation (latest reports per component)
   ↓
8. Gold Layer Export (dashboard-ready files)
   ↓
9. Dashboard Rendering (real-time from Gold layer)
```

**Update Cadence**:
- **Real-time**: Dashboard reads latest Gold layer
- **Daily**: New lab reports ingested, Steps 1-8 executed
- **Weekly**: Stewart Limits recalculated (optional, if data distribution changes)

---

## 📞 Support

For implementation details:
- **[Data Contracts](data_contracts.md)**: Schema and transformation specifications
- **[Dashboard Documentation](dashboard_documentation.md)**: UI wireframes and chart specs
