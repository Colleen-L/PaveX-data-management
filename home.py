import streamlit as st
st.set_page_config(layout="wide")
from streamlit_card import card
import json
import pandas as pd
from datetime import datetime, timezone
import os
from google.cloud import bigquery
from dotenv import load_dotenv
load_dotenv()
import re
import hashlib
import numpy as np

# for log file
import logging
logging.basicConfig(filename="etl_log.txt", level=logging.INFO)

# for heatmap
import geopandas as gpd
import folium
from folium.plugins import HeatMap
from folium import Map, PolyLine
from streamlit_folium import st_folium
from shapely.geometry import LineString, MultiLineString

# initialize BigQuery Client
# Option 1: Set via environment variable (recommended for team projects)
# Option 2: Auto-detect from Application Default Credentials
PROJECT_ID = os.getenv("GCP_PROJECT_ID")

if PROJECT_ID:
    client = bigquery.Client(project=PROJECT_ID)
else:
    # Try to auto-detect from credentials
    try:
        import google.auth
        credentials, project = google.auth.default()
        if project:
            PROJECT_ID = project
            client = bigquery.Client(project=PROJECT_ID, credentials=credentials)
        else:
            raise ValueError("No project ID found in credentials")
    except Exception as e:
        raise Exception(
            "Could not determine Google Cloud project ID. "
            "Please set environment variable: GCP_PROJECT_ID=your-project-id "
            "Or run: gcloud config set project your-project-id && gcloud auth application-default login"
        )

# define dataset name and ID correctly
DATASET_NAME = "autonomous_dataset"
DATASET_ID = f"{PROJECT_ID}.{DATASET_NAME}"


# create dataset if it doesn't exist
dataset = bigquery.Dataset(DATASET_ID)
dataset.location = "US"
try:
    client.create_dataset(dataset, exists_ok=True)
    logging.info(f"Dataset confirmed or created: {DATASET_ID}")
except Exception as e:
    logging.error(f"Dataset creation error: {e}")

##########################################
# function to get the unprocessed files from a folder
# for future processing
##########################################
def get_unprocessed_files(json_folder):
    try:
        # Try to get already processed files from BigQuery
        processed = set(run_query(f"SELECT DISTINCT Source_File FROM `{DATASET_ID}.segments`")['Source_File'])
    except Exception as e:
        # If table doesn't exist yet (first run), return all files
        logging.info(f"Table segments doesn't exist yet or query failed: {e}. Processing all files.")
        processed = set()

    all_files = [f for f in os.listdir(json_folder) if f.endswith(".json")]
    return [f for f in all_files if f not in processed]

##########################################
# helper function that obtains timestamp for the data;
# utilized in process_json_files()
##########################################
def get_timestamp(filename):
    try:
        #takes the part before the dot
        ts_str = filename.split('.')[0]
        # converts to float
        ts_float = float(ts_str)
        # converts to UTC datetime
        return datetime.fromtimestamp(ts_float, tz=timezone.utc)
    except Exception:
        return None

##########################################
# helper function that generates a unique integer ID from a string value
##########################################
def generate_hash_id(value, prefix=""):
    hash_obj = hashlib.sha256(f"{prefix}_{value}".encode())
    # Convert first 8 bytes to integer (positive)
    return int.from_bytes(hash_obj.digest()[:8], byteorder='big', signed=False) % (10**15)

##########################################
# helper function that processes the json files and creates
# DateFrames for the different variables
##########################################
def process_all_json_files(json_folder):
    """
    Process all JSON files in folder while maintaining consistent IDs
    This ensures no ID collisions across files
    """
    # Get all JSON files
    json_files = [f for f in os.listdir(json_folder) if f.endswith(".json")]
    
    if not json_files:
        st.warning("No JSON files found.")
        return None
    
    st.info(f"Processing {len(json_files)} files: {json_files}")
    
    # stores data for later conversion into dataframe
    segments = []
    drives = []
    cameras = []
    images = []
    camera_images = []
    categories = []
    image_categories = []
    missing_classifications = []
    
    # id maps - THESE PERSIST ACROSS ALL FILES
    segment_id_map = {}
    drive_id_map = {}
    camera_id_map = {}
    image_id_map = {}
    category_id_map = {}
    
    # counters for the id - THESE INCREMENT ACROSS ALL FILES
    segment_counter = 1
    drive_counter = 1
    camera_counter = 1
    image_counter = 1
    cam_img_counter = 1
    category_counter = 1
    img_cat_counter = 1

    # Loop through ALL files
    for json_file in json_files:
        file_path = os.path.join(json_folder, json_file)
        st.info(f"Processing: {json_file}")
        
        # loads the JSON
        with open(file_path, 'r') as f:
            data = json.load(f)

        for segment_name, segment_data in data.items():
            # assign unique ID to each segment
            if segment_name not in segment_id_map:
                segment_id_map[segment_name] = segment_counter
                segment_counter += 1
            seg_pk = segment_id_map[segment_name]

            # track timestamps for the segments
            segment_timestamps = []

            for drive_name, drive_data in segment_data.items():
                # obtaining unique drive_id
                drive_key = (segment_name, drive_name)
                if drive_key not in drive_id_map:
                    drive_id_map[drive_key] = drive_counter
                    drive_counter += 1
                drive_pk = drive_id_map[drive_key]

                # saves dir_day and dir_pass
                dir_day = drive_data.get('dir_day')
                dir_pass = drive_data.get('dir_pass')
                # tracks timestamps
                drive_timestamps = []

                # add to Cameras table
                # finds all keys starting with 'cam'
                camera_keys = [k for k in drive_data.keys() if k.startswith('cam')]
                # obtains cam info and assign unique camera id
                for cam_name in camera_keys:
                    cam_key = f"{drive_name}_{cam_name}_{segment_name}"
                    if cam_key not in camera_id_map:
                        camera_id_map[cam_key] = camera_counter
                        camera_counter += 1
                    cam_pk = camera_id_map[cam_key]

                    cameras.append({
                        "Camera_ID": cam_pk,
                        "Drive_ID": drive_pk,
                        "Name": cam_name
                    })

                    cam_data = drive_data[cam_name]

                    # process images by color, depth
                    for img_type in ['color', 'depth']:
                        if img_type in cam_data:
                            for filename in cam_data[img_type]:
                                if filename not in image_id_map:
                                    image_id_map[filename] = image_counter
                                    ts = get_timestamp(filename)
                                    images.append({
                                        "Image_ID": image_counter,
                                        "Filename": filename,
                                        "Type": img_type,
                                        "Timestamp": ts
                                    })
                                    
                                    # track timestamps
                                    if ts:
                                        segment_timestamps.append(ts)
                                        drive_timestamps.append(ts)
                                    
                                    image_counter += 1
                                    
                                image_pk = image_id_map[filename]
                                
                                camera_images.append({
                                    "ID": cam_img_counter,
                                    "Camera_ID": cam_pk,
                                    "Image_ID": image_pk
                                })
                                cam_img_counter += 1

                    # process classifications
                    if "Classification_Swin" in cam_data:
                        for category_name, file_list in cam_data["Classification_Swin"].items():
                            # obtains classification info and assigns unique id
                            if category_name not in category_id_map:
                                category_id_map[category_name] = category_counter
                                categories.append({
                                    "Category_ID": category_counter,
                                    "Name": category_name
                                })
                                category_counter += 1
                            cat_pk = category_id_map[category_name]
                            
                            for filename in file_list:
                                # extracts filename
                                filename_only = filename.split('\\')[-1]
                                
                                if filename_only in image_id_map:
                                    image_pk = image_id_map[filename_only]
                                    image_categories.append({
                                        "ID": img_cat_counter,
                                        "Image_ID": image_pk,
                                        "Category_ID": cat_pk,
                                        "Confidence": None
                                    })
                                    img_cat_counter += 1
                                else:
                                    missing_classifications.append({
                                        "filename": filename_only,
                                        "category": category_name,
                                        "segment": segment_name,
                                        "drive": drive_name,
                                        "camera": cam_name
                                    })

                # adds to Drives table
                drives.append({
                    "Drive_ID": drive_pk,
                    "Name": drive_name,
                    "Segment_ID": seg_pk,
                    "Dir_Day": dir_day,
                    "Dir_Pass": dir_pass,
                    "Time_Driven": min(drive_timestamps) if drive_timestamps else None,
                    "Source_File": json_file
                })

            # adds to Segments
            # using min of the timestamps
            seg_time_recorded = min(segment_timestamps) if segment_timestamps else None
            segments.append({
                "Segment_ID": seg_pk,
                "Name": segment_name,
                "Location": "Fort Wayne, IN",
                "Date_Recorded": seg_time_recorded.date() if seg_time_recorded else None,
                "Source_File": json_file
            })

    # Show processing summary
    st.success(f"Processed {len(json_files)} files")
    st.info(f"Generated: {len(segments)} segments, {len(drives)} drives, {len(images)} images")
    
    # Show missing classifications if any
    if missing_classifications:
        st.warning(f"Found {len(missing_classifications)} missing image classifications")
        if st.checkbox("Show missing classifications details"):
            st.dataframe(pd.DataFrame(missing_classifications))

    # convert to dataframes
    segments_df = pd.DataFrame(segments)
    drives_df = pd.DataFrame(drives)
    cameras_df = pd.DataFrame(cameras)
    images_df = pd.DataFrame(images)
    camera_images_df = pd.DataFrame(camera_images)
    categories_df = pd.DataFrame(categories)
    image_categories_df = pd.DataFrame(image_categories)

    # return as dictionary
    return {
        "segments": segments_df,
        "drives": drives_df,
        "cameras": cameras_df,
        "images": images_df,
        "camera_images": camera_images_df,
        "categories": categories_df,
        "image_categories": image_categories_df,
    }

##########################################
# helper function that checks and adjusts schema dynamically
# before uploading
##########################################
def ensure_table_schema(df, table_name):
    table_id = f"{DATASET_ID}.{table_name}"
    try:
        table = client.get_table(table_id)
        existing_cols = {field.name for field in table.schema}
        new_cols = [col for col in df.columns if col not in existing_cols]
        if new_cols:
            st.warning(f"New columns detected for {table_name}: {new_cols}")
    except Exception:
        st.info(f"Table {table_name} not found, will be created automatically.")

##########################################
# helper function that takes a pandas df and table name then uploads 
# the DataFrame as a table into the dataset in BigQuery
##########################################
def upload_df(df, table_name, mode, client, dataset_id):
    """Upload DataFrame to BigQuery"""
    table_id = f"{dataset_id}.{table_name}"

    if mode == "append":
        write_mode = bigquery.WriteDisposition.WRITE_APPEND
    elif mode == "replace":
        write_mode = bigquery.WriteDisposition.WRITE_TRUNCATE
    elif mode == "fail":
        write_mode = bigquery.WriteDisposition.WRITE_EMPTY
    else:
        raise ValueError("mode must be 'append', 'replace', or 'fail'")

    job_config = bigquery.LoadJobConfig(write_disposition=write_mode)
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    logging.info(f"Uploaded {len(df)} rows to {table_id}")

##########################################
# functiion that fills in known optional fields... removes NaNs
##########################################
def validate_dataframe(df, table_name):
    if df.empty:
        return df

    # fill known optional fields
    if 'Confidence' in df.columns:
        df['Confidence'] = df['Confidence'].fillna(0.0)
    
    if 'Timestamp' in df.columns:
        df['Timestamp'] = df['Timestamp'].fillna(pd.Timestamp('1970-01-01'))
    
    if 'Date_Recorded' in df.columns:
        df['Date_Recorded'] = df['Date_Recorded'].fillna(pd.Timestamp('1970-01-01').date())

    # check critical columns
    critical_cols = {
        "segments": ["Segment_ID", "Name"],
        "drives": ["Drive_ID", "Segment_ID", "Name"],
        "cameras": ["Camera_ID", "Drive_ID", "Name"],
        "images": ["Image_ID", "Filename"],
        "camera_images": ["ID", "Camera_ID", "Image_ID"],
        "categories": ["Category_ID", "Name"],
        "image_categories": ["ID", "Image_ID", "Category_ID"]
    }

    for col in critical_cols.get(table_name, []):
        if col in df.columns and df[col].isnull().any():
            st.warning(f"{table_name} has missing values in critical column: {col}")
            df.dropna(subset=[col], inplace=True)
    
    return df

##########################################
# function that takes the DataFrames and uploads them to BigQuery
##########################################
def upload_all_dfs(json_folder, client, dataset_id, mode="replace"):
    # Process ALL files at once
    dfs = process_all_json_files(json_folder)
    if dfs is None:
        return
    # Upload all tables
    try:
        for table_name, df in dfs.items():
            if not df.empty:
                # Validate and clean
                df = validate_dataframe(df, table_name)
                # Show what we're uploading
                st.info(f"Uploading {len(df)} rows to {table_name}")
                # Upload to BigQuery
                upload_df(df, table_name, mode, client, dataset_id)
                st.success(f"{table_name}: {len(df)} rows uploaded")
            else:
                st.warning(f"{table_name} is empty, skipping")
        logging.info(f"Successfully uploaded all data")
        st.success("All data uploaded successfully!")
    except Exception as e:
        logging.error(f"Failed to upload: {e}")
        st.error(f"Error during upload: {e}")

##########################################
# function that runs a query from frontend UI to BigQuery
##########################################
def run_query(query):
   try:
      query_job = client.query(query)
      df = query_job.to_dataframe()
      return df
   except Exception as e:
      st.error(f"Error running query: {e}")
      return pd.DataFrame()

@st.cache_data(ttl=600)
def load_heatmap_data():
    shapefile_path = "./data/heatmap/PASER_Centerline_FW_PaveX_2025.shp"
    gdf = gpd.read_file(shapefile_path).to_crs(epsg=4326)

    segment_counts = run_query(f"""
        SELECT
            segment_name,
            SUM(classification_count) AS total_classifications
        FROM `{DATASET_ID}.segment_category_counts`
        GROUP BY segment_name
    """)
    return gdf, segment_counts

def build_polyline_map(gdf, segment_counts):
    # Normalize IDs
    gdf["Seg_ID"] = gdf["Seg_ID"].apply(lambda x: str(int(float(x))) if pd.notnull(x) else None)
    gdf["segment_name_key"] = "segment_" + gdf["Seg_ID"]
    segment_counts["segment_name"] = segment_counts["segment_name"].astype(str).str.strip()
    
    # Merge counts
    gdf = gdf.merge(segment_counts, left_on="segment_name_key", right_on="segment_name", how="left")
    
    # Drop missing data
    gdf = gdf.dropna(subset=["geometry", "total_classifications"])
    if gdf.empty:
        st.warning("No valid classification data to plot.")
        return None
    
    # Convert CRS for folium
    gdf_wgs = gdf.to_crs(epsg=4326)
    
    # Map center
    center = [gdf_wgs.geometry.centroid.y.mean(), gdf_wgs.geometry.centroid.x.mean()]
    m = Map(location=center, zoom_start=11, tiles="cartodbpositron", control_scale=True)
    
    # Severity normalization
    max_class = gdf_wgs["total_classifications"].max()
    gdf_wgs["severity_norm"] = gdf_wgs["total_classifications"] / max_class
    
    # Color thresholds
    q1 = gdf_wgs["severity_norm"].quantile(0.33)
    q2 = gdf_wgs["severity_norm"].quantile(0.66)
    
    for _, row in gdf_wgs.iterrows():
        geom = row.geometry
        sev = row["severity_norm"]
        
        # Determine color
        if sev <= q1:
            color = "green"
        elif sev <= q2:
            color = "orange"
        else:
            color = "red"
        
        # Sample coordinates for long lines
        coords = []
        if isinstance(geom, LineString):
            coords = list(geom.coords)[::max(1, len(geom.coords)//20)]  # every ~20th point
        elif isinstance(geom, MultiLineString):
            for line in geom.geoms:
                coords.extend(list(line.coords)[::max(1, len(line.coords)//20)])
        
        # Convert coords to lat/lon
        latlon = [[lat, lon] for lon, lat in coords]
        if latlon:
            PolyLine(latlon, color=color, weight=4, opacity=0.7).add_to(m)
    return m


def load_tableau():
    #####
    #USING TABLEAU
    #####
    tableau_dashboards = {
        "CLASSIFICATIONS PER SEGMENT": os.getenv("CLASSIFICATIONS_PER_SEGMENT_URL"),
        "TOP CLASSIFICATIONS": os.getenv("TOP_CLASSIFICATIONS_URL"),
        "IMAGES PER SEGMENT": os.getenv("IMAGES_PER_SEGMENT_URL"),
        "IMAGES PER DRIVE": os.getenv("IMAGES_PER_DRIVE_URL"),
        "IMAGES PER CAMERA": os.getenv("IMAGES_PER_CAMERA_URL"),
        "IMAGE TYPE DISTRIBUTION": os.getenv("IMAGE_TYPE_DISTRIBUTION_URL"),
    }
    tableau_dashboards = {k:v for k,v in tableau_dashboards.items() if v}
    # --- Sidebar gallery selector ---
    selected = st.sidebar.radio(
        "Select a dashboard to view:",
        list(tableau_dashboards.keys())
    )
    # --- Display selected Tableau visualization ---
    url = tableau_dashboards[selected]
    st.subheader(selected)
    st.components.v1.iframe(url, height=800, width=1200)

    tableau_url = 'https://us-east-1.online.tableau.com/t/li5027-6bf92531c9/views/VIPSmartCities/classifications_per_segment?:origin=card_share_link&:embed=y&:showVizHome=no'
    # Embedding Tableau data visualization using iframe
    st.components.v1.iframe(tableau_url, height=800, width=1200)
  
##########################################
# function for query caching in streamlit
# this prevents unnecessary re-running of the same queries.
##########################################
@st.cache_data(ttl=300)
def cached_run_query(query):
    query_job = client.query(query)
    return query_job.to_dataframe()

# uploaded the DataFrames into BigQuery with the following code (but implement process in future)
# upload_all_dfs("data/", mode="append")

st.title("Data Dashboard & SQL Query")

if st.button("Upload JSON to BigQuery"):
    upload_all_dfs("data/", client, DATASET_ID, mode="replace")

tab1, tab2, tab3 = st.tabs(["Dashboard", "Query Database", "System Metrics"])

# dashboard
with tab1:
    st.header("Dashboard")

    # Support both PowerBI and Tableau
    powerbi_url = os.getenv('POWERBI_URL')
    tableau_url = os.getenv('TABLEAU_URL')

    if powerbi_url:
        st.subheader("PowerBI Dashboard")
        # Embedding PowerBI visualization using iframe
        st.components.v1.iframe(powerbi_url, height=800, scrolling=True)
    elif tableau_url:
        st.subheader("Tableau Dashboard")
        # Embedding Tableau data visualization using iframe
        st.components.v1.iframe(tableau_url, height=800, width=1200)
    else:
        st.info("No dashboard configured. Set POWERBI_URL or TABLEAU_URL in .env file.")
    st.header("Interactive Tableau Dashboard")

    # if "heatmap_obj" not in st.session_state:
    #     st.session_state.heatmap_obj = None

    # # Button logic
    # col1, col2 = st.columns([1, 1])
    # with col1:
    #     if st.button("Load Heatmap"):
    #         gdf, segment_counts = load_heatmap_data()
    #         st.session_state.heatmap_obj = build_circlemap(gdf, segment_counts)
    #         st.success("Heatmap loaded successfully!")

    # with col2:
    #     if st.button("Clear Heatmap"):
    #         st.session_state.heatmap_obj = None
    #         st.warning("Heatmap cleared.")

    # # Display map if exists
    # if st.session_state.heatmap_obj:
    #     st_folium(
    #         st.session_state.heatmap_obj,
    #         width=900,
    #         height=600,
    #         key="persistent_heatmap",
    #         returned_objects=[],  # prevents zoom/pan re-runs
    #     )
    
    if "polyline_map_obj" not in st.session_state:
        st.session_state.polyline_map_obj = None

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Load Map"):
            gdf, segment_counts = load_heatmap_data()
            st.session_state.polyline_map_obj = build_polyline_map(gdf, segment_counts)
            st.success("Polyline map loaded successfully!")

    with col2:
        if st.button("Clear Map"):
            st.session_state.polyline_map_obj = None
            st.warning("Map cleared.")

    if st.session_state.polyline_map_obj:
        st_folium(
            st.session_state.polyline_map_obj,
            width=900,
            height=600,
            key="persistent_polyline_map",
            returned_objects=[],  # prevents re-runs when zooming
        )

with tab2:
    st.header("SQL Query Interface")
    # built-in queries
    queries = {
        "View Segments": "SELECT * FROM segments LIMIT 10;",
        "View Drives": "SELECT * FROM drives LIMIT 10;",
        "Count Images": "SELECT COUNT(*) AS total_images FROM images;",
        "Images Per Category": """SELECT cat.Name AS category_name, 
                                  COUNT(ic.Image_ID) AS total_images
                                  FROM categories cat
                                  JOIN image_categories ic ON cat.Category_ID = ic.Category_ID
                                  GROUP BY cat.Name
                                  ORDER BY total_images DESC""",
        "Most Common Category Per Segment": """SELECT s.Name AS segment_name,
                                                cat.Name AS most_common_cat,
                                                COUNT(*) AS image_count
                                                FROM image_categories ic
                                                JOIN categories cat ON ic.Category_ID = cat.Category_ID
                                                JOIN images i on ic.Image_ID = i.Image_ID
                                                JOIN camera_images ci ON i.Image_ID = ci.Image_ID
                                                JOIN cameras c ON ci.Camera_ID = c.Camera_ID
                                                JOIN drives d ON c.Drive_ID = d.Drive_ID
                                                JOIN segments s ON d.Segment_ID = s.Segment_ID
                                                GROUP BY s.Name, cat.Name
                                                ORDER BY s.Name, image_count DESC;""",
        "Drives with Longest Timespan": """SELECT d.Name AS drive_name,
                                            s.Name as segment_name,
                                            MIN(i.Timestamp) AS start_time,
                                            MAX(i.Timestamp) AS end_time,
                                            TIMESTAMP_DIFF(MAX(i.Timestamp), 
                                            MIN(i.Timestamp), SECOND) AS duration_seconds
                                            FROM drives d
                                            JOIN segments s on d.Segment_ID = s.Segment_ID
                                            JOIN cameras c ON d.Drive_ID = c.Drive_ID
                                            JOIN camera_images ci ON c.Camera_ID = ci.Camera_ID
                                            JOIN images i ON ci.Image_ID = i.Image_ID
                                            GROUP BY d.Name, s.Name
                                            ORDER BY duration_seconds DESC
                                            LIMIT 10;""", 
        "Top Categories by Segment": """SELECT s.Name AS segment_name,
                                        cat.Name AS category_name,
                                        COUNT(*) AS image_count
                                        FROM image_categories ic
                                        JOIN categories cat ON ic.Category_ID = cat.Category_ID
                                        JOIN images i ON ic.Image_ID = i.Image_ID
                                        JOIN camera_images ci ON i.Image_ID = ci.Image_ID
                                        JOIN cameras c ON ci.Camera_ID = c.Camera_ID
                                        JOIN drives d ON c.Drive_ID = d.Drive_ID
                                        JOIN segments s ON d.Segment_ID = s.Segment_ID
                                        GROUP BY segment_name, category_name
                                        ORDER BY segment_name, image_count DESC;""",
    }
    choice = st.selectbox("Quick query:", list(queries.keys()))
    #################
    # function that prepends DATASET_ID to table references or keeps the same
    def prepend_dataset(query):
        
        # find all CTE names
        cte_names = re.findall(r'WITH\s+(\w+)\s+AS', query, flags=re.IGNORECASE)
        
        def replacer(match):
            keyword = match.group(1)
            table = match.group(2)
            if table in cte_names or '.' in table or table.startswith('`'):
                return f"{keyword} {table}"
            return f"{keyword} `{DATASET_ID}.{table}`"
        
        pattern = r"\b(FROM|JOIN|CREATE\s+OR\s+REPLACE\s+TABLE|CREATE\s+TABLE)\s+([`]?[\w]+[`]?)"
        return re.sub(pattern, replacer, query, flags=re.IGNORECASE)



    # text area for user input
    user_query = st.text_area(
        "Or enter your own SQL query:",
        queries[choice],
        height=300,
    )

    # automatically fix dataset references
    full_query = prepend_dataset(user_query)

    # query cost estimator (BigQuery dry-run)
    if st.button("Estimate Query Cost"):
      try:
          job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
          query_job = client.query(full_query, job_config=job_config)
          processed_gb = query_job.total_bytes_processed / 1e9
          st.info(f"Query will process approximately {processed_gb:.2f} GB.")
      except Exception as e:
          st.error(f"Failed to estimate cost: {e}")

    # runs query
    if st.button("Run Query"):
        with st.spinner("Running query..."):
            df = cached_run_query(full_query)
            if not df.empty:
                st.success(f"Returned {len(df)} rows")
                st.dataframe(df)

with tab3:
    st.header("System Metrics")
    st.subheader("Data Summary")

    tables = ["segments", "drives", "cameras", "images"]

    for table in tables:
        try:
            query = f"SELECT COUNT(*) AS total_rows FROM `{DATASET_ID}.{table}`"
            count_df = run_query(query)

            if not count_df.empty:
                total = int(count_df.iloc[0]['total_rows'])
                st.metric(label=f"{table}", value=f"{total:,}")
            else:
                st.warning(f"No data returned for {table}")
        except Exception as e:
            st.error(f"Error fetching {table} metrics: {e}")
    
    st.subheader("Storage Overview")
    try:
        size_query = f"""
        SELECT
          table_id,
          row_count,
          ROUND(size_bytes / POW(1024,3), 4) AS size_gb
        FROM `{DATASET_ID}.__TABLES__`
        ORDER BY size_gb DESC
        """

        size_df = run_query(size_query)
        if not size_df.empty:
            st.dataframe(size_df)
        else:
            st.warning("No storage data found.")
    except Exception as e:
        st.error(f"Error fetching table sizes: {e}")
