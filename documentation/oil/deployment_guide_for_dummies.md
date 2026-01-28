# Deployment Guide for Dummies 🚀

**Multi-Technical-Alerts - Step-by-Step Deployment**

This guide will help you deploy the Multi-Technical-Alerts system from scratch, even if you've never deployed anything before!

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### What You Need

✅ **Computer Requirements:**
- Windows 10/11, macOS, or Linux
- At least 4GB RAM
- 10GB free disk space

✅ **Software to Install:**

1. **Python 3.11+**
   - Download: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"
   - Verify: Open terminal and type `python --version`

2. **Git** (optional, for cloning)
   - Download: https://git-scm.com/downloads
   - Verify: `git --version`

3. **Docker** (for containerized deployment)
   - Download: https://www.docker.com/products/docker-desktop
   - Verify: `docker --version`

4. **OpenAI API Key** (for AI recommendations)
   - Sign up: https://platform.openai.com/
   - Create API key: https://platform.openai.com/api-keys
   - Copy your key (starts with `sk-...`)

---

## Local Development Setup

### Step 1: Get the Code

**Option A: Download ZIP**
1. Download project as ZIP file
2. Extract to folder (e.g., `C:\Projects\Multi-Technical-Alerts`)

**Option B: Clone with Git**
```bash
git clone <repository-url>
cd Multi-Technical-Alerts
```

### Step 2: Install Dependencies

Open terminal in project folder:

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

1. **Copy environment template:**
   ```bash
   copy .env.example .env
   # On macOS/Linux: cp .env.example .env
   ```

2. **Edit `.env` file:**
   Open `.env` in text editor and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

   Other settings (optional):
   ```
   MAX_WORKERS=18
   DASHBOARD_PORT=8050
   DEBUG_MODE=False
   ```

### Step 4: Prepare Data

Place your data files in the correct folders:

```
data/oil/
├── essays_elements.xlsx          ← Essays mapping file
├── raw/
│   ├── cda/                       ← CDA Excel files here
│   │   ├── machine1.xlsx
│   │   ├── machine2.xlsx
│   │   └── ...
│   └── emin/                      ← EMIN Parquet files here
│       └── muestrasAlsHistoricos.parquet
```

**Where to get data:**
- **CDA:** Export from Finning platform as Excel files
- **EMIN:** Export from ALS platform as Parquet file
- **Essays mapping:** Request from data team or use existing file

### Step 5: Run the Pipeline

```bash
python main.py
```

**What happens:**
1. Loads raw data from `data/oil/raw/`
2. Transforms and harmonizes data
3. Calculates Stewart Limits
4. Classifies all samples
5. Generates AI recommendations
6. Exports results to `data/oil/processed/`

**Expected output:**
```
===== Starting Bronze → Silver pipeline for CDA =====
Loaded 1234 samples from Silver layer
===== Bronze → Silver pipeline complete for CDA =====

===== Starting Silver → Gold pipeline for CDA =====
Generating AI recommendations with 18 workers
Generating recommendations: 100%|██████████| 1234/1234
===== Silver → Gold pipeline complete for CDA =====

✅ All components working correctly!
```

### Step 6: Check Results

Open output files in `data/oil/processed/`:

- `cda_classified.xlsx` - Classified samples with AI recommendations (Excel)
- `cda_classified.parquet` - Classified samples (Parquet, fast)
- `cda_machine_status.xlsx` - Machine health status (Excel)
- `stewart_limits.json` - Calculated thresholds
- `stewart_limits.xlsx` - Thresholds table (Excel)

---

## Docker Deployment

### Why Docker?

- ✅ No Python installation needed
- ✅ Same environment everywhere (dev, test, prod)
- ✅ Easy to deploy and update
- ✅ Isolated from other applications

### Step 1: Install Docker

1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
2. Install and start Docker Desktop
3. Verify installation:
   ```bash
   docker --version
   docker-compose --version
   ```

### Step 2: Configure Environment

Create `.env` file in project root:

```env
# Required
OPENAI_API_KEY=sk-your-actual-api-key-here

# Optional
MAX_WORKERS=18
SECRET_KEY=change-this-to-random-string-in-production
```

### Step 3: Build Docker Images

```bash
# Build backend image
docker build -t multi-technical-alerts-backend -f Dockerfile.backend .

# Build dashboard image (only if dashboard is implemented)
docker build -t multi-technical-alerts-dashboard -f Dockerfile.dashboard .
```

### Step 4: Run with Docker Compose

**Start all services:**
```bash
docker-compose up -d
```

**Check status:**
```bash
docker-compose ps
```

**View logs:**
```bash
# Backend logs
docker-compose logs -f backend

# Dashboard logs
docker-compose logs -f dashboard
```

**Stop services:**
```bash
docker-compose down
```

### Step 5: Access the System

- **Backend:** Runs once on startup, processes data
- **Dashboard:** http://localhost:8050 (if implemented)

**Login credentials:**
- **Admin:** username=`admin`, password=`admin123` (access to all clients)
- **CDA User:** username=`cda_user`, password=`cda123` (CDA data only)
- **EMIN User:** username=`emin_user`, password=`emin123` (EMIN data only)

⚠️ **IMPORTANT:** Change these passwords in production! Edit `config/users.py`

---

## Production Deployment

### Option 1: Cloud Deployment (Azure/AWS/GCP)

#### Azure Container Instances

1. **Install Azure CLI:**
   ```bash
   # Download from: https://aka.ms/installazurecli
   ```

2. **Login to Azure:**
   ```bash
   az login
   ```

3. **Create Resource Group:**
   ```bash
   az group create --name multi-technical-alerts --location eastus
   ```

4. **Create Container Registry:**
   ```bash
   az acr create --resource-group multi-technical-alerts \
     --name multitechnicalalerts --sku Basic
   ```

5. **Build and push images:**
   ```bash
   # Login to registry
   az acr login --name multitechnicalalerts
   
   # Build and push backend
   docker build -t multitechnicalalerts.azurecr.io/backend:latest -f Dockerfile.backend .
   docker push multitechnicalalerts.azurecr.io/backend:latest
   
   # Build and push dashboard
   docker build -t multitechnicalalerts.azurecr.io/dashboard:latest -f Dockerfile.dashboard .
   docker push multitechnicalalerts.azurecr.io/dashboard:latest
   ```

6. **Create Container Instances:**
   ```bash
   # Backend
   az container create --resource-group multi-technical-alerts \
     --name backend --image multitechnicalalerts.azurecr.io/backend:latest \
     --cpu 2 --memory 4 \
     --environment-variables OPENAI_API_KEY=sk-your-key-here
   
   # Dashboard
   az container create --resource-group multi-technical-alerts \
     --name dashboard --image multitechnicalalerts.azurecr.io/dashboard:latest \
     --cpu 1 --memory 2 --ports 8050 \
     --dns-name-label multi-technical-alerts-dashboard
   ```

7. **Access dashboard:**
   ```
   http://multi-technical-alerts-dashboard.eastus.azurecontainer.io:8050
   ```

#### AWS ECS

1. **Install AWS CLI:**
   ```bash
   # Download from: https://aws.amazon.com/cli/
   ```

2. **Configure AWS:**
   ```bash
   aws configure
   ```

3. **Create ECR repositories:**
   ```bash
   aws ecr create-repository --repository-name multi-technical-alerts/backend
   aws ecr create-repository --repository-name multi-technical-alerts/dashboard
   ```

4. **Build and push:**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   # Build and push
   docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/multi-technical-alerts/backend:latest \
     -f Dockerfile.backend .
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/multi-technical-alerts/backend:latest
   ```

5. **Create ECS task definition and service** (see AWS ECS documentation)

### Option 2: Local Server Deployment

1. **Install Docker on server:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

2. **Copy project files to server:**
   ```bash
   scp -r Multi-Technical-Alerts user@server:/opt/
   ```

3. **Setup systemd service** (Linux):

   Create `/etc/systemd/system/multi-technical-alerts.service`:
   ```ini
   [Unit]
   Description=Multi-Technical-Alerts
   Requires=docker.service
   After=docker.service
   
   [Service]
   Type=oneshot
   RemainAfterExit=yes
   WorkingDirectory=/opt/Multi-Technical-Alerts
   ExecStart=/usr/bin/docker-compose up -d
   ExecStop=/usr/bin/docker-compose down
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Enable and start service:**
   ```bash
   sudo systemctl enable multi-technical-alerts
   sudo systemctl start multi-technical-alerts
   ```

### Option 3: Scheduled Pipeline Execution

#### Windows Task Scheduler

1. Open Task Scheduler
2. Create Task:
   - **Trigger:** Daily at 2:00 AM
   - **Action:** Start a program
     - Program: `C:\Path\To\Python\python.exe`
     - Arguments: `C:\Path\To\Multi-Technical-Alerts\main.py`
     - Start in: `C:\Path\To\Multi-Technical-Alerts`

#### Linux Cron

Add to crontab (`crontab -e`):
```cron
0 2 * * * cd /opt/Multi-Technical-Alerts && /usr/bin/python main.py >> /var/log/multi-technical-alerts.log 2>&1
```

---

## Troubleshooting

### Common Issues

#### ❌ "ModuleNotFoundError: No module named 'pandas'"

**Solution:**
```bash
pip install -r requirements.txt
```

#### ❌ "OpenAI API key not configured"

**Solution:**
1. Check `.env` file exists in project root
2. Verify `OPENAI_API_KEY=sk-...` is set correctly
3. Ensure no spaces around `=`

#### ❌ "No data loaded for CDA"

**Solution:**
1. Check data files exist in `data/oil/raw/cda/`
2. Verify files are Excel format (`.xlsx`)
3. Check logs in `logs/main_test.log` for details

#### ❌ Docker container exits immediately

**Solution:**
```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Missing .env file
# - Invalid OPENAI_API_KEY
# - Missing data files
```

#### ❌ "Permission denied" on Linux/macOS

**Solution:**
```bash
# Give execute permission to scripts
chmod +x scripts/run_pipeline.py

# Fix data directory permissions
chmod -R 755 data/
```

#### ❌ Dashboard not loading

**Solution:**
1. Check if dashboard is implemented (see `IMPLEMENTATION_STATUS.md`)
2. If pending, backend pipeline still works - use Excel files in `data/oil/processed/`
3. If implemented, check dashboard logs: `docker-compose logs dashboard`

### Performance Tuning

#### Slow AI Generation

Reduce parallel workers in `.env`:
```env
MAX_WORKERS=8  # Reduce from 18 to 8
```

#### Out of Memory

Reduce batch size or workers:
```env
MAX_WORKERS=4
MIN_MACHINE_SAMPLES=10  # Increase to filter more aggressively
```

### Getting Help

1. **Check logs:**
   ```bash
   # Local deployment
   cat logs/main_test.log
   
   # Docker deployment
   docker-compose logs -f
   ```

2. **Enable debug mode:**
   In `.env`:
   ```env
   DEBUG_MODE=True
   ```

3. **Review documentation:**
   - `IMPLEMENTATION_STATUS.md` - Current system status
   - `repo_modular.md` - Architecture details
   - `action_plan.md` - Implementation roadmap

4. **Check data quality:**
   ```bash
   python -c "from src.data.validators import get_data_quality_report; import pandas as pd; df = pd.read_parquet('data/oil/to_consume/CDA.parquet'); print(get_data_quality_report(df))"
   ```

---

## Security Checklist

Before deploying to production:

- [ ] Change default passwords in `config/users.py`
- [ ] Set strong `SECRET_KEY` in `.env`
- [ ] Use environment variables for secrets (never commit `.env`)
- [ ] Enable HTTPS for dashboard (use reverse proxy like nginx)
- [ ] Restrict network access (firewall rules)
- [ ] Regularly update dependencies: `pip install --upgrade -r requirements.txt`
- [ ] Monitor logs for suspicious activity
- [ ] Backup processed data regularly

---

## Maintenance

### Regular Tasks

**Daily:**
- Check logs for errors
- Verify pipeline executed successfully

**Weekly:**
- Review classified reports
- Update essays mapping if needed

**Monthly:**
- Recalculate Stewart Limits:
  ```bash
  python scripts/run_pipeline.py --recalculate-limits
  ```
- Update dependencies:
  ```bash
  pip install --upgrade -r requirements.txt
  ```

### Monitoring

Set up monitoring for:
- Pipeline execution time
- AI recommendation success rate
- Disk space in `data/oil/processed/`
- API rate limits (OpenAI)

---

## Success! 🎉

You should now have:
- ✅ Pipeline processing data automatically
- ✅ Classified samples with AI recommendations
- ✅ Machine health status reports
- ✅ Export files (Excel + Parquet)

**Next steps:**
- Review output files in `data/oil/processed/`
- Set up scheduled execution (cron/Task Scheduler)
- Implement dashboard (see `repo_modular.md` for architecture)
- Deploy to production cloud environment

**Need help?** Check `IMPLEMENTATION_STATUS.md` or review logs in `logs/` directory.
