# PaveX Data Management

ETL pipeline and dashboard system for processing and analyzing autonomous vehicle road segment data.

## Overview

PaveX Data Management ingests JSON files containing road segment information (images, camera data, classifications), transforms them into a relational model, and stores them in Google BigQuery for analysis via a Streamlit web interface.

## Features

- **Automated ETL Pipeline**: Process JSON files and upload to BigQuery
- **Incremental Processing**: Automatically detects and processes only new files
- **Interactive Dashboard**:
  - Embedded Tableau visualization
  - SQL query interface with built-in queries
  - Query cost estimator
  - System metrics and storage overview
- **Query Caching**: 5-minute cache for query results to optimize performance

## Requirements

- Python 3.7+
- Google Cloud account with BigQuery enabled
- Tableau account (for dashboard)
- Packages: `streamlit`, `pandas`, `google-cloud-bigquery`, `python-dotenv`

## Installation

1. Clone repository:
```bash
git clone <repository-url>
cd PaveX-data-management
```

2. Install dependencies:
```bash
pip install streamlit pandas google-cloud-bigquery python-dotenv db-dtypes
```

3. Install Google Cloud CLI:

Download and install from: https://cloud.google.com/sdk/docs/install

4. Configure Google Cloud authentication:

**Step 1: Login to Google Cloud**
```bash
gcloud auth application-default login
```
This will open your browser to authenticate with your Google account.

**Step 2: Set your project ID**
```bash
gcloud config set project YOUR_PROJECT_ID
```
Replace `YOUR_PROJECT_ID` with your Google Cloud project ID (e.g., `vippavexdata`).

**Step 3: Create `.env` file** (for team collaboration)

Each team member should create their own `.env` file in the project root:

```bash
# .env file
GCP_PROJECT_ID=your-project-id
TABLEAU_URL=your-tableau-embed-url
```

**Important**: The `.env` file contains personal project settings and should NOT be committed to git. It's already in `.gitignore`.

## Usage

### First-Time Setup: Upload Initial Data

**IMPORTANT**: Before running the dashboard for the first time, you must upload data to BigQuery.

1. Place your JSON files in the `data/` folder

2. Run the upload script:
```bash
python upload_data.py
```

This will:
- Create the BigQuery dataset (`autonomous_dataset`) if it doesn't exist
- Process all JSON files in the `data/` folder
- Create all necessary tables (segments, drives, cameras, images, categories, etc.)
- Upload data to BigQuery

**Note**: This process may take 5-15 minutes depending on file size and network speed. You'll see progress messages like:
```
Starting ETL pipeline to upload data to BigQuery...
Uploaded 682157 rows to vippavexdata.autonomous_dataset.images
...
✅ Success! All data uploaded to BigQuery.
```

### Run Dashboard

After initial data upload, start the Streamlit dashboard:

```bash
streamlit run home.py
```

Dashboard will open at `http://localhost:8501`

**Important**: Do NOT click the "Run" button in VS Code. Always use the terminal command `streamlit run home.py`.

### Process Additional Data

To add new JSON files after initial setup:

1. Place new JSON files in `data/` folder
2. Run `python upload_data.py` again

The system automatically detects which files have been processed and only uploads new ones (incremental processing).

## Data Structure

### Input Format (JSON)

```json
{
  "segment_name": {
    "drive_name": {
      "dir_day": "...",
      "dir_pass": "...",
      "cam1": {
        "color": ["1710259234.567.png", ...],
        "depth": ["1710259234.567.png", ...],
        "Classification_Swin": {
          "category_name": ["path\\to\\image.png", ...]
        }
      }
    }
  }
}
```

### Database Schema

- **segments**: Road segments (location, date recorded)
- **drives**: Drives within each segment
- **cameras**: Cameras used in drives
- **images**: Image files (color/depth types)
- **camera_images**: Camera-to-image junction table
- **categories**: Classification categories
- **image_categories**: Image-to-category junction table

## Dashboard Tabs

### 1. Dashboard
Displays embedded Tableau visualization

### 2. Query Database
- Pre-built quick queries (View Segments, Count Images, etc.)
- Custom SQL query editor
- Query cost estimator (predicts GB to be processed)
- Automatic dataset prefix added to table names

### 3. System Metrics
- Row counts for each table
- Storage overview (size_gb, row_count)

## Troubleshooting

### Common Issues

#### 1. "DefaultCredentialsError: Your default credentials were not found"

**Solution**: You haven't authenticated with Google Cloud yet.
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

#### 2. "404 Not found: Table was not found"

**Solution**: You need to upload data first.
```bash
python upload_data.py
```

#### 3. "ValueError: Please install the 'db-dtypes' package"

**Solution**: Missing required package.
```bash
pip install db-dtypes
```

#### 4. "Thread 'MainThread': missing ScriptRunContext!"

**Solution**: This is a harmless warning when running `upload_data.py`. You can safely ignore it. The upload will still work correctly.

#### 5. "FutureWarning: Loading pandas DataFrame into BigQuery will require pandas-gbq"

**Solution**: This is a harmless warning. To remove it (optional):
```bash
pip install pandas-gbq
```

#### 6. Running Streamlit produces errors

**Common mistakes**:
- ❌ Clicking "Run" button in VS Code
- ✅ Use terminal: `streamlit run home.py`

#### 7. "Could not determine Google Cloud project ID"

**Solution**: Make sure your `.env` file exists and contains:
```
GCP_PROJECT_ID=your-project-id
```

### Check Logs

All ETL operations are logged to `etl_log.txt`:
- Successful/failed uploads
- Dataset creation
- Errors

Check this file if uploads fail or behave unexpectedly.

## Notes

- Timestamps are extracted from filenames (Unix timestamp format)
- Default location: "Fort Wayne, IN"
- BigQuery dataset: `autonomous_dataset` (auto-created, US region)
- Processed files are tracked via `Source_File` column in segments table
- Each team member uses their own Google Cloud project via `.env` file

## Development

This project was developed to manage autonomous vehicle road segment data, supporting analysis and visualization for the PaveX team.
