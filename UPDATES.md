# Recent Updates

## October 22, 2025 - Google Cloud Integration & Setup Improvements

### Major Changes

#### 1. Google Cloud BigQuery Setup
- **Added dynamic project ID detection** - System now automatically detects your Google Cloud project from environment variables or gcloud config
- **Team collaboration support** - Each team member can use their own GCP project via `.env` file
- **Improved authentication flow** - Added comprehensive setup instructions for Google Cloud CLI and authentication

#### 2. ETL Pipeline Improvements
- **Fixed first-time upload error** - Added error handling for when BigQuery tables don't exist yet
- **Created `upload_data.py` script** - Standalone script for initial data upload (run this before starting the dashboard)
- **Better error messages** - More informative errors when things go wrong

#### 3. Dashboard Integration
- **Added PowerBI support** - Dashboard now supports both PowerBI and Tableau embedding
- **Flexible configuration** - Set `POWERBI_URL` or `TABLEAU_URL` in `.env` file
- **Graceful fallback** - Shows helpful message if no dashboard URL is configured

**Note**: PowerBI dashboard is embedded but visualization work is still in progress.

#### 4. Documentation Updates
- **Comprehensive README** - Added detailed setup instructions, troubleshooting guide, and first-time usage workflow
- **ARCHITECTURE.md** - Added system architecture documentation covering data model, ETL flow, and design decisions
- **Troubleshooting section** - Common errors and solutions documented

#### 5. Dependencies
- **Added `db-dtypes`** - Required for BigQuery data type conversion to pandas
- **Updated .gitignore** - Now excludes logs, cache files, and personal config

### Breaking Changes

⚠️ **Important**: You must create a `.env` file before running the application.

**Required `.env` file:**
```bash
GCP_PROJECT_ID=your-project-id
POWERBI_URL=your-powerbi-embed-url  # Optional, for dashboard
```

### Migration Guide for Team Members

If you're pulling these changes for the first time:

1. **Install new dependencies:**
   ```bash
   pip install db-dtypes
   ```

2. **Setup Google Cloud authentication:**
   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Create `.env` file** in project root:
   ```bash
   GCP_PROJECT_ID=your-project-id
   POWERBI_URL=your-powerbi-embed-url
   ```

4. **Upload initial data** (if not done yet):
   ```bash
   python upload_data.py
   ```

5. **Run the dashboard:**
   ```bash
   streamlit run home.py
   ```

### Files Changed
- `home.py` - Dynamic project ID detection, PowerBI support, error handling
- `README.md` - Comprehensive setup and troubleshooting guide
- `upload_data.py` - New script for data upload
- `ARCHITECTURE.md` - New architecture documentation
- `.gitignore` - Updated to exclude logs and cache
- `.env` - Required configuration file (not in git)

### Known Issues
- PowerBI dashboard is embedded but visualizations are work in progress
- `google-cloud-bigquery-storage` warning appears (harmless, can ignore or install package to remove)
- `ScriptRunContext` warning when running `upload_data.py` (harmless, ignore it)

### Next Steps
- Complete PowerBI dashboard visualizations
- Potentially migrate to Purdue cloud infrastructure (TBD based on mentor feedback)

---

For detailed setup instructions, see [README.md](README.md).
For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md).
