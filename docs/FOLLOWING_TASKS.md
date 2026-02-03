# Following Tasks - Oil Analysis Data Product

**Document Purpose**: Outline next steps for S3 integration, data management, and pipeline optimization  
**Created**: February 3, 2026  
**Status**: Planning Phase

---

## 📋 Overview

This document outlines the roadmap for evolving the Oil Analysis Data Product from a local file-based system to a cloud-native, event-driven architecture with S3 storage and automated data management.

**Key Objectives**:
1. Enable cross-repository data sharing via S3
2. Implement event-driven pipeline triggers
3. Optimize incremental data processing
4. Minimize computational overhead
5. Ensure data consistency and versioning

---

## 🎯 Task 1: S3 Integration for Data Mesh Communication

### Objective

Connect data inputs and outputs to S3 buckets to enable data sharing between repositories (Oil Analysis, Fusion Service, Dashboard, etc.) in the data mesh architecture.

### Architecture Design

```
┌─────────────────────────────────────────────────────────────┐
│                     S3 Bucket Structure                      │
└─────────────────────────────────────────────────────────────┘

s3://mining-data-mesh/
├── oil-analysis/                    # This data product
│   ├── bronze/                      # Raw laboratory data
│   │   ├── cda/
│   │   │   └── {date}/              # Daily partitions
│   │   │       ├── T-09.xlsx
│   │   │       └── T-10.xlsx
│   │   └── emin/
│   │       └── {date}/
│   │           └── muestrasAlsHistoricos.parquet
│   │
│   ├── silver/                      # Standardized data
│   │   ├── stewart_limits/
│   │   │   └── {version}/           # Versioned limits
│   │   │       ├── stewart_limits.json
│   │   │       └── stewart_limits.parquet
│   │   ├── harmonized/
│   │   │   ├── CDA.parquet          # Full historical data
│   │   │   └── EMIN.parquet
│   │   └── _delta/                  # Incremental changes
│   │       ├── CDA_{date}.parquet
│   │       └── EMIN_{date}.parquet
│   │
│   └── gold/                        # Analysis-ready outputs
│       ├── cda/
│       │   ├── classified_reports.parquet
│       │   ├── machine_status_current.parquet
│       │   └── _history/            # Historical snapshots
│       │       └── {date}/
│       │           ├── classified_reports.parquet
│       │           └── machine_status_current.parquet
│       └── emin/
│           └── ...
│
├── telemetry/                       # Other data products
│   └── gold/
│       ├── cda/
│       └── emin/
│
├── maintenance/
│   └── gold/
│
└── fusion/                          # Combined data product
    └── gold/
        ├── cda/
        └── emin/
```

### Implementation Steps

#### Step 1.1: Setup S3 Infrastructure

**Tools**: AWS CLI, Terraform, or CloudFormation

**Tasks**:
1. Create S3 bucket: `mining-data-mesh`
2. Configure bucket policies:
   - Oil Analysis service: Read/Write to `oil-analysis/*`
   - Fusion Service: Read from `oil-analysis/gold/*`, `telemetry/gold/*`, `maintenance/gold/*`
   - Dashboard Service: Read from `fusion/gold/*`
3. Enable versioning on bucket
4. Configure lifecycle policies:
   - Bronze: Retain indefinitely
   - Silver: Transition to Glacier after 1 year
   - Gold: Retain latest + 30 days, archive rest

**IAM Policy Example**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::mining-data-mesh/oil-analysis/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::mining-data-mesh",
      "Condition": {
        "StringLike": {
          "s3:prefix": "oil-analysis/*"
        }
      }
    }
  ]
}
```

**Terraform Example**:
```hcl
resource "aws_s3_bucket" "data_mesh" {
  bucket = "mining-data-mesh"
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    id      = "bronze-archive"
    enabled = true
    prefix  = "oil-analysis/bronze/"
    
    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }
  
  lifecycle_rule {
    id      = "gold-retention"
    enabled = true
    prefix  = "oil-analysis/gold/"
    
    noncurrent_version_expiration {
      days = 30
    }
  }
}
```

**Estimated Time**: 2-4 hours  
**Cost**: ~$0.023/GB/month (S3 Standard) + transfer costs

---

#### Step 1.2: Update Code for S3 I/O

**Modify `config/settings.py`**:

Add S3 configuration:
```python
class Settings(BaseSettings):
    # ... existing fields ...
    
    # S3 Configuration
    use_s3: bool = Field(default=False, description="Use S3 for data storage")
    s3_bucket: str = Field(default="mining-data-mesh", description="S3 bucket name")
    s3_prefix: str = Field(default="oil-analysis", description="S3 prefix for this data product")
    aws_region: str = Field(default="us-east-1", description="AWS region")
    
    def get_s3_bronze_path(self, client: str) -> str:
        """Get S3 path for Bronze layer."""
        from datetime import date
        today = date.today().isoformat()
        return f"s3://{self.s3_bucket}/{self.s3_prefix}/bronze/{client.lower()}/{today}/"
    
    def get_s3_silver_harmonized_path(self, client: str) -> str:
        """Get S3 path for Silver harmonized data."""
        return f"s3://{self.s3_bucket}/{self.s3_prefix}/silver/harmonized/{client.upper()}.parquet"
    
    def get_s3_gold_path(self, client: str, filename: str) -> str:
        """Get S3 path for Gold layer files."""
        return f"s3://{self.s3_bucket}/{self.s3_prefix}/gold/{client.lower()}/{filename}"
```

**Create `src/utils/s3_utils.py`**:
```python
"""S3 utilities for data I/O."""

import boto3
from pathlib import Path
from typing import Union
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)


class S3Handler:
    """Handle S3 operations for data product."""
    
    def __init__(self, bucket: str, region: str = "us-east-1"):
        self.bucket = bucket
        self.s3_client = boto3.client('s3', region_name=region)
        self.s3_resource = boto3.resource('s3', region_name=region)
    
    def upload_file(self, local_path: Union[str, Path], s3_key: str) -> None:
        """Upload file to S3."""
        logger.info(f"Uploading {local_path} to s3://{self.bucket}/{s3_key}")
        self.s3_client.upload_file(str(local_path), self.bucket, s3_key)
        logger.info(f"Upload complete")
    
    def download_file(self, s3_key: str, local_path: Union[str, Path]) -> None:
        """Download file from S3."""
        logger.info(f"Downloading s3://{self.bucket}/{s3_key} to {local_path}")
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        self.s3_client.download_file(self.bucket, s3_key, str(local_path))
        logger.info(f"Download complete")
    
    def read_parquet(self, s3_key: str) -> pd.DataFrame:
        """Read Parquet file directly from S3."""
        s3_path = f"s3://{self.bucket}/{s3_key}"
        logger.info(f"Reading Parquet from {s3_path}")
        return pd.read_parquet(s3_path)
    
    def write_parquet(self, df: pd.DataFrame, s3_key: str) -> None:
        """Write DataFrame to S3 as Parquet."""
        s3_path = f"s3://{self.bucket}/{s3_key}"
        logger.info(f"Writing {len(df)} rows to {s3_path}")
        df.to_parquet(s3_path, compression='snappy', index=False)
        logger.info(f"Write complete")
    
    def list_files(self, prefix: str) -> list:
        """List files in S3 prefix."""
        logger.info(f"Listing files in s3://{self.bucket}/{prefix}")
        response = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        
        if 'Contents' not in response:
            return []
        
        files = [obj['Key'] for obj in response['Contents']]
        logger.info(f"Found {len(files)} files")
        return files
    
    def file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except:
            return False
```

**Modify `src/data/exporters.py`**:
```python
from src.utils.s3_utils import S3Handler
from config.settings import get_settings

def export_to_parquet(
    df: pd.DataFrame,
    output_path: str | Path,
    compression: str = 'snappy',
    use_s3: bool = None
) -> None:
    """Export DataFrame to Parquet (local or S3)."""
    settings = get_settings()
    use_s3 = use_s3 if use_s3 is not None else settings.use_s3
    
    if use_s3:
        # Extract S3 key from path
        s3_key = str(output_path).replace(f"s3://{settings.s3_bucket}/", "")
        s3_handler = S3Handler(settings.s3_bucket, settings.aws_region)
        s3_handler.write_parquet(df, s3_key)
    else:
        # Local file system (existing logic)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, compression=compression, index=False)
```

**Dependencies to Add**:
```bash
pip install boto3 s3fs
```

Update `requirements.txt`:
```
boto3>=1.28.0
s3fs>=2023.6.0
```

**Estimated Time**: 8-16 hours  
**Testing Required**: Unit tests for S3 operations, integration tests

---

#### Step 1.3: Configure Dual-Mode Operation

Support both local and S3 storage via environment variable:

**`.env` Configuration**:
```bash
# Data Storage Mode
USE_S3=false                    # Set to 'true' for S3 storage
S3_BUCKET=mining-data-mesh
S3_PREFIX=oil-analysis
AWS_REGION=us-east-1

# AWS Credentials (use IAM role in production)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

**Deployment Strategy**:
1. **Phase 1**: Local-only (current state)
2. **Phase 2**: Dual-write (write to both local and S3 for validation)
3. **Phase 3**: S3-primary (read from S3, write to S3, local as cache)
4. **Phase 4**: S3-only (remove local storage)

**Estimated Time**: 4 hours  
**Risk**: Low (backward compatible)

---

## 🔄 Task 2: Event-Driven Pipeline Triggers

### Objective

Replace manual/scheduled pipeline execution with event-driven triggers that respond to new data arrival in real-time.

### Architecture Options

#### Option A: AWS Lambda + S3 Events (Recommended)

**Trigger Flow**:
```
New file uploaded to S3 (bronze/)
    ↓
S3 Event Notification
    ↓
Lambda Function triggered
    ↓
Run Oil Analysis Pipeline
    ↓
Output written to gold/
    ↓
SNS Notification to Fusion Service
```

**Benefits**:
- ✅ Fully serverless (no infrastructure management)
- ✅ Auto-scaling (handles burst loads)
- ✅ Cost-effective (pay per execution)
- ✅ Low latency (seconds to respond)

**Implementation**:

1. **Create Lambda Function**:
```python
# lambda_function.py
import json
import boto3
import os

def lambda_handler(event, context):
    """Triggered when new file uploaded to bronze layer."""
    
    # Parse S3 event
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        # Extract client from path: oil-analysis/bronze/{client}/{date}/file.xlsx
        parts = key.split('/')
        if len(parts) >= 4 and parts[1] == 'bronze':
            client = parts[2].upper()
            
            # Trigger ECS task to run pipeline
            ecs = boto3.client('ecs')
            response = ecs.run_task(
                cluster='oil-analysis-cluster',
                taskDefinition='oil-analysis-pipeline',
                launchType='FARGATE',
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': [os.environ['SUBNET_ID']],
                        'securityGroups': [os.environ['SECURITY_GROUP_ID']],
                        'assignPublicIp': 'ENABLED'
                    }
                },
                overrides={
                    'containerOverrides': [{
                        'name': 'oil-analysis',
                        'environment': [
                            {'name': 'CLIENT', 'value': client},
                            {'name': 'TRIGGER_TYPE', 'value': 'event'},
                            {'name': 'SOURCE_FILE', 'value': key}
                        ]
                    }]
                }
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps(f'Pipeline triggered for {client}')
            }
```

2. **Configure S3 Event Notification**:
```hcl
resource "aws_s3_bucket_notification" "bronze_events" {
  bucket = aws_s3_bucket.data_mesh.id
  
  lambda_function {
    lambda_function_arn = aws_lambda_function.pipeline_trigger.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "oil-analysis/bronze/"
    filter_suffix       = ".xlsx"
  }
  
  lambda_function {
    lambda_function_arn = aws_lambda_function.pipeline_trigger.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "oil-analysis/bronze/"
    filter_suffix       = ".parquet"
  }
}
```

**Estimated Time**: 12-16 hours  
**Cost**: ~$0.20 per 1M requests + ECS Fargate costs

---

#### Option B: Cron Schedule with Change Detection

**For environments without serverless infrastructure**

**Implementation**:
```python
# src/pipeline/incremental_pipeline.py

def detect_new_files(client: str, last_run_timestamp: datetime) -> List[str]:
    """Detect files added since last run."""
    bronze_path = settings.get_raw_path(client)
    new_files = []
    
    for file_path in bronze_path.glob("**/*"):
        if file_path.is_file():
            # Check file modification time
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime > last_run_timestamp:
                new_files.append(file_path)
    
    return new_files


def run_incremental_pipeline(client: str) -> None:
    """Run pipeline only if new data exists."""
    
    # Load last run timestamp
    state_file = settings.logs_dir / f"{client}_last_run.json"
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = json.load(f)
            last_run = datetime.fromisoformat(state['last_run'])
    else:
        last_run = datetime.min
    
    # Check for new files
    new_files = detect_new_files(client, last_run)
    
    if not new_files:
        logger.info(f"No new files for {client}, skipping pipeline")
        return
    
    logger.info(f"Found {len(new_files)} new files for {client}, running pipeline")
    
    # Run full pipeline
    run_full_pipeline(client, recalculate_limits=False, generate_ai=True)
    
    # Update state
    with open(state_file, 'w') as f:
        json.dump({'last_run': datetime.now().isoformat()}, f)
```

**Cron Configuration**:
```bash
# Run every hour
0 * * * * /app/venv/bin/python /app/main_incremental.py >> /app/logs/cron.log 2>&1
```

**Estimated Time**: 4-6 hours  
**Cost**: Minimal (compute only when needed)

---

## ⚡ Task 3: Incremental Data Processing

### Objective

Minimize computational overhead by processing only new/changed data instead of reprocessing entire datasets.

### Strategy

#### 3.1: Delta Processing for Bronze → Silver

**Current State**: Full reprocessing of all raw files  
**Target State**: Process only new files, append to existing Silver layer

**Implementation**:

```python
# src/pipeline/bronze_to_silver_incremental.py

def process_new_files_only(client: str) -> pd.DataFrame:
    """Process only new raw files since last run."""
    
    # Load existing Silver layer data
    silver_path = settings.get_to_consume_path(client)
    if silver_path.exists():
        existing_df = pd.read_parquet(silver_path)
        existing_samples = set(existing_df['sampleNumber'].unique())
    else:
        existing_df = pd.DataFrame()
        existing_samples = set()
    
    # Load all raw files
    raw_df = load_all_raw_files(client)
    
    # Filter to only new samples
    new_df = raw_df[~raw_df['sampleNumber'].isin(existing_samples)]
    
    if new_df.empty:
        logger.info(f"No new samples for {client}")
        return existing_df
    
    logger.info(f"Processing {len(new_df)} new samples for {client}")
    
    # Apply transformations to new data only
    new_df = apply_transformations(new_df, client)
    
    # Append to existing data
    updated_df = pd.concat([existing_df, new_df], ignore_index=True)
    
    # Save updated Silver layer
    export_to_parquet(updated_df, silver_path)
    
    return updated_df
```

**Benefits**:
- ⚡ 10-100x faster for incremental updates
- 💰 Lower compute costs
- 🔄 Supports continuous data ingestion

**Considerations**:
- Must handle late-arriving data (samples with older dates)
- Deduplication logic needed
- Periodic full reprocessing for data quality

**Estimated Time**: 8-12 hours

---

#### 3.2: Stewart Limits - Conditional Recalculation

**Current State**: Recalculate limits every run  
**Target State**: Recalculate only when data distribution changes significantly

**Trigger Conditions**:
1. New machine type appears
2. Sample count increases by >10%
3. Statistical distribution shifts (KS test)
4. Manual trigger (API call or flag)
5. Scheduled (weekly)

**Implementation**:

```python
def should_recalculate_limits(client: str, new_samples_count: int) -> bool:
    """Determine if Stewart Limits need recalculation."""
    
    # Load metadata
    metadata_file = settings.get_processed_path() / f"{client}_limits_metadata.json"
    if not metadata_file.exists():
        return True  # First run
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    old_count = metadata.get('sample_count', 0)
    last_calc = datetime.fromisoformat(metadata.get('last_calculated', '2000-01-01'))
    
    # Trigger conditions
    if new_samples_count - old_count > old_count * 0.1:  # >10% increase
        logger.info("Recalculating limits: >10% new samples")
        return True
    
    if (datetime.now() - last_calc).days > 7:  # Weekly recalc
        logger.info("Recalculating limits: weekly schedule")
        return True
    
    logger.info("Limits are up-to-date")
    return False
```

**Estimated Time**: 4 hours

---

#### 3.3: AI Recommendations - Caching and Deduplication

**Current State**: Generate AI for all non-Normal reports every run  
**Target State**: Cache AI recommendations, regenerate only for new breaches

**Implementation**:

```python
def generate_ai_with_cache(df: pd.DataFrame, ...) -> pd.DataFrame:
    """Generate AI recommendations with caching."""
    
    # Load AI cache
    cache_file = settings.get_processed_path() / "ai_cache.parquet"
    if cache_file.exists():
        cache_df = pd.read_parquet(cache_file)
        cache_dict = dict(zip(cache_df['cache_key'], cache_df['ai_recommendation']))
    else:
        cache_dict = {}
    
    # Create cache keys (based on breached essays + values)
    def create_cache_key(row):
        breaches = row['breached_essays']  # JSON string
        return hashlib.md5(breaches.encode()).hexdigest()
    
    df['cache_key'] = df.apply(create_cache_key, axis=1)
    
    # Check cache
    df['ai_recommendation'] = df['cache_key'].map(cache_dict)
    
    # Identify rows needing AI generation
    needs_ai = df['ai_recommendation'].isna()
    count_cached = (~needs_ai).sum()
    count_needed = needs_ai.sum()
    
    logger.info(f"AI: {count_cached} from cache, {count_needed} to generate")
    
    # Generate only for new patterns
    if count_needed > 0:
        new_recommendations = generate_all_recommendations(
            df[needs_ai], limits, openai_client, max_workers, essays_list
        )
        df.loc[needs_ai, 'ai_recommendation'] = new_recommendations
        
        # Update cache
        new_cache = df[needs_ai][['cache_key', 'ai_recommendation']]
        updated_cache = pd.concat([cache_df, new_cache]) if cache_file.exists() else new_cache
        updated_cache.to_parquet(cache_file, index=False)
    
    return df
```

**Benefits**:
- 💰 50-80% reduction in AI API costs
- ⚡ Faster pipeline execution
- 🎯 Consistent recommendations for similar issues

**Estimated Time**: 6-8 hours

---

## 📊 Task 4: Data Versioning and History Management

### Objective

Maintain historical snapshots for auditing and trend analysis while optimizing storage costs.

### Strategy

#### 4.1: Gold Layer Versioning

**Current State**: Single current snapshot  
**Target State**: Current + versioned history

**Directory Structure**:
```
gold/{client}/
├── classified_reports.parquet              # Latest (symlink)
├── machine_status_current.parquet          # Latest (symlink)
└── _history/
    ├── 2024-02-01/
    │   ├── classified_reports.parquet
    │   └── machine_status_current.parquet
    ├── 2024-02-02/
    └── 2024-02-03/
```

**Implementation**:
```python
def save_with_history(df: pd.DataFrame, output_path: Path, client: str):
    """Save current file and archive to history."""
    from datetime import date
    
    # Save to history
    history_dir = output_path.parent / "_history" / date.today().isoformat()
    history_dir.mkdir(parents=True, exist_ok=True)
    history_path = history_dir / output_path.name
    
    export_to_parquet(df, history_path)
    
    # Save current (or create symlink)
    export_to_parquet(df, output_path)
    
    logger.info(f"Saved current to {output_path} and history to {history_path}")
```

**Lifecycle Policy**:
- Keep daily snapshots for 30 days
- Keep weekly snapshots for 1 year
- Archive to Glacier after 1 year

**Estimated Time**: 4 hours

---

#### 4.2: Change Data Capture (CDC)

**Purpose**: Track what changed in each pipeline run for debugging and auditing

**Implementation**:
```python
# src/utils/change_tracking.py

def track_changes(old_df: pd.DataFrame, new_df: pd.DataFrame, entity: str) -> dict:
    """Track changes between pipeline runs."""
    
    changes = {
        'timestamp': datetime.now().isoformat(),
        'entity': entity,
        'old_count': len(old_df),
        'new_count': len(new_df),
        'added': len(new_df) - len(old_df),
        'status_changes': {},
        'sample': {}
    }
    
    # Track status distribution changes
    if 'report_status' in new_df.columns:
        old_dist = old_df['report_status'].value_counts().to_dict()
        new_dist = new_df['report_status'].value_counts().to_dict()
        changes['status_changes'] = {
            'old': old_dist,
            'new': new_dist
        }
    
    # Sample of new records
    if changes['added'] > 0:
        new_samples = new_df.tail(min(10, changes['added']))
        changes['sample'] = new_samples.to_dict('records')
    
    return changes


# In pipeline
changes_log_file = settings.logs_dir / "changes.jsonl"
with open(changes_log_file, 'a') as f:
    f.write(json.dumps(changes) + '\n')
```

**Estimated Time**: 3 hours

---

## 🎯 Recommended Implementation Priority

### Phase 1: Foundation (Weeks 1-2)
1. ✅ **Task 1.1**: S3 infrastructure setup
2. ✅ **Task 1.2**: Code updates for S3 I/O
3. ✅ **Task 3.1**: Delta processing for Bronze → Silver

**Deliverables**: Working S3 integration with incremental processing

---

### Phase 2: Optimization (Weeks 3-4)
1. ✅ **Task 3.2**: Conditional Stewart Limits recalculation
2. ✅ **Task 3.3**: AI caching
3. ✅ **Task 4.1**: Gold layer versioning

**Deliverables**: 80% reduction in processing time and costs

---

### Phase 3: Automation (Weeks 5-6)
1. ✅ **Task 2**: Event-driven triggers (Lambda or cron-based)
2. ✅ **Task 4.2**: Change data capture

**Deliverables**: Fully automated, event-driven pipeline

---

## 📈 Expected Outcomes

### Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Pipeline Duration** | 5 min | 30 sec | 10x faster |
| **AI API Costs** | $5/run | $1/run | 80% reduction |
| **Compute Costs** | $0.50/run | $0.10/run | 80% reduction |
| **Storage Costs** | $10/month | $15/month | +50% (offset by efficiency gains) |
| **Data Freshness** | Daily batch | Real-time (< 5 min) | Near real-time |

### Operational Benefits

- ✅ Automated pipeline execution (no manual triggers)
- ✅ Real-time data availability for downstream consumers
- ✅ Historical versioning for auditing and debugging
- ✅ Reduced infrastructure management (serverless)
- ✅ Better observability (change tracking, logs)

---

## 🔧 Technical Considerations

### Idempotency

**Requirement**: Pipeline must be idempotent (re-running with same input produces same output)

**Implementation**:
- Use `sampleNumber` as unique key
- Deduplication logic in all layers
- Deterministic AI (set seed or cache)

### Data Consistency

**Requirement**: Ensure consistency between layers

**Implementation**:
- Atomic writes (temp file + rename)
- Schema validation before write
- Checksums for data integrity

### Error Handling

**Requirement**: Graceful degradation, no data loss

**Implementation**:
- Retry logic with exponential backoff
- Dead-letter queue for failed records
- Alerting on critical failures (SNS, PagerDuty)

---

## 📞 Next Steps

1. **Review and Approve**: Get stakeholder sign-off on this roadmap
2. **Provision Infrastructure**: Create AWS resources (S3, Lambda, ECS)
3. **Implement Phase 1**: S3 integration + incremental processing
4. **Testing**: Validate with historical data
5. **Deploy to Production**: Gradual rollout with monitoring
6. **Implement Phase 2 & 3**: Optimization and automation

**Estimated Total Time**: 6-8 weeks (1 developer)  
**Estimated Total Cost**: $50-100/month (AWS services)

---

## 📚 References

- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)
- [Lambda + S3 Tutorial](https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html)
- [Delta Lake (Alternative for advanced CDC)](https://delta.io/)
- [Apache Iceberg (Alternative table format)](https://iceberg.apache.org/)

---

**Document Status**: ✅ Ready for Review  
**Owner**: Oil Analysis Data Product Team  
**Last Updated**: February 3, 2026
