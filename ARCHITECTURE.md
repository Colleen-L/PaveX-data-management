# ARCHITECTURE.md

This document provides comprehensive system architecture documentation and design decisions for the PaveX Data Management project.

## Project Overview

PaveX Data Management is an ETL pipeline and data dashboard for processing autonomous vehicle road segment data. The system ingests JSON files containing road segment information (images, camera data, classifications), transforms them into a relational model, and stores them in Google BigQuery for analysis via a Streamlit web interface.

## Architecture

### Data Model

The system implements a relational schema with 7 tables:
- **segments**: Road segments with location and recording date
- **drives**: Individual drives within segments (contains dir_day, dir_pass metadata)
- **cameras**: Cameras used in each drive
- **images**: Image files with timestamps (color/depth types)
- **camera_images**: Junction table linking cameras to images
- **categories**: Classification categories (from Classification_Swin model)
- **image_categories**: Junction table linking images to their classifications

### Core Files

- **home.py**: Main Streamlit application with 3 tabs:
  - Dashboard: Embedded Tableau visualization
  - Query Database: SQL interface with built-in queries and cost estimation
  - System Metrics: Storage and row count statistics

- **data-processing.ipynb**: Jupyter notebook containing the original ETL pipeline prototype (now superseded by home.py)

- **data-processing.py**: Empty file (legacy)

### ETL Pipeline Flow

1. **Ingestion**: `process_json_files(json_file)` reads JSON files from data/ folder
2. **Transformation**:
   - Assigns unique IDs to all entities (segments, drives, cameras, images, categories)
   - Extracts timestamps from filenames (Unix timestamp format: `{timestamp}.{ext}`)
   - Builds relational mappings between entities
   - Returns 7 DataFrames representing the relational schema
3. **Loading**: `upload_df(df, table_name, mode)` pushes DataFrames to BigQuery
4. **Incremental Processing**: `get_unprocessed_files()` checks segments table to avoid reprocessing

### Key Design Patterns

**ID Assignment**: Uses in-memory dictionaries to track and assign sequential IDs across all files:
- `segment_id_map`, `drive_id_map`, `camera_id_map`, `image_id_map`, `category_id_map`

**Timestamp Extraction**: The `get_timestamp()` function parses filenames like `1710259234.567.png` to extract Unix timestamps

**Dataset Reference Auto-Prepending**: The `prepend_dataset()` function automatically adds dataset qualifiers to SQL queries:
- Detects CTEs to avoid qualifying them
- Skips already-qualified tables (containing `.` or backticks)
- Prepends `{PROJECT_ID}.autonomous_dataset.` to table names

**Query Caching**: Uses `@st.cache_data(ttl=300)` for 5-minute query result caching

## Running the Application

```bash
# Start Streamlit dashboard
streamlit run home.py
```

The application requires:
- Google Cloud credentials configured (uses Application Default Credentials)
- Environment variable `TABLEAU_URL` for embedded dashboard
- BigQuery project with billing enabled

## Google BigQuery Integration

- **Project**: Determined automatically from default credentials
- **Dataset**: `autonomous_dataset` (created automatically if missing, located in US region)
- **Write Modes**:
  - `replace`: Truncates table before writing
  - `append`: Adds rows to existing table
  - `fail`: Fails if table already exists

## Data Processing

```python
# Process new JSON files and upload to BigQuery
upload_all_dfs("data/", mode="append")
```

This function:
1. Queries BigQuery to find which files have already been processed (via Source_File column)
2. Processes only new files
3. Validates DataFrames before upload
4. Logs success/failure to `etl_log.txt`

## SQL Query Interface

Built-in queries include:
- View Segments/Drives
- Count Images
- Images Per Category
- Most Common Category Per Segment
- Drives with Longest Timespan
- Top Categories by Segment

The "Estimate Query Cost" button uses BigQuery dry-run to calculate bytes processed before execution.

## Data Source Format

JSON files in `data/` folder follow this structure:
```
{
  "segment_name": {
    "drive_name": {
      "dir_day": "...",
      "dir_pass": "...",
      "cam1": {
        "color": ["timestamp1.png", ...],
        "depth": ["timestamp1.png", ...],
        "Classification_Swin": {
          "category_name": ["path\\to\\image.png", ...]
        }
      }
    }
  }
}
```

## Important Notes

- All BigQuery table references in SQL queries are automatically prefixed with the dataset ID
- Image timestamps are extracted from filenames (Unix timestamp format)
- Classification paths may use Windows backslashes (`\\`) which are parsed to extract filenames
- The segments table tracks Source_File to enable incremental processing
- Location is hardcoded to "Fort Wayne, IN" for all segments
- Jupyter notebook (data-processing.ipynb) contains legacy code that previously uploaded to PostgreSQL (Neon Tech) before migrating to BigQuery
