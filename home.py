import streamlit as st
import json
import pandas as pd
from datetime import datetime, timezone
import os
from google.cloud import bigquery
from dotenv import load_dotenv
load_dotenv()
import re

# initialize BigQuery Client
client = bigquery.Client()
# client obtains project id
PROJECT_ID = client.project
# client obtains dataset id
DATASET_ID = f"{PROJECT_ID}.autonomous_dataset"
# reassign client to project ID
client = bigquery.Client(project=PROJECT_ID)
# creates dataset
dataset = bigquery.Dataset(DATASET_ID)
dataset.location = "US"
client.create_dataset(dataset, exists_ok = True)

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
# helper function that processes the json files and creates
# DateFrames for the different variables
##########################################
def process_json_files(json_file):
    # stores data for later conversion into dataframe
    segments = []
    drives = []
    cameras = []
    images = []
    camera_images = []
    categories = []
    image_categories = []
    # id maps
    segment_id_map = {}
    drive_id_map = {}
    camera_id_map = {}
    image_id_map = {}
    category_id_map = {}
    # counters for the id (beneficial for conversion to psql)
    segment_counter = 1
    drive_counter = 1
    camera_counter = 1
    image_counter = 1
    cam_img_counter = 1
    category_counter = 1
    img_cat_counter = 1

    # loads the JSON
    with open(json_file, 'r') as f:
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
        # tracks timestampes
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
              # obtains classifcation info and assigns unique id
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
# helper function that takes a pandas df and table name then uploads 
# the DataFrame as a table into the dataset in BigQuery
##########################################
def upload_df(df, table_name, mode):
    table_id = f"{DATASET_ID}.{table_name}"

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
    print(f"Uploaded {len(df)} rows to {table_id}")

##########################################
# function that takes the DataFrames and uploads them to BigQuery
##########################################
def upload_all_dfs(json_folder, mode="replace"):
    json_files = [f for f in os.listdir(json_folder) if f.endswith(".json")]

    for json_file in json_files:
        full_path = os.path.join(json_folder, json_file)
        dfs = process_json_files(full_path)

        for table_name, df in dfs.items():
            upload_df(df, table_name, mode)

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

# uploaded the DataFrames into BigQuery with the following code (but implement process in future)
#upload_all_dfs("data/", mode="replace")

st.title("Data Dashboard & SQL Query App")

view = st.radio("Choose a view:", ["Dashboard", "Query Database"])

# dashboard
if view == "Dashboard":
    st.header("Dashboard")

else:
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
    #################
    def prepend_dataset(query):
        #################
        # helper function that determines if the query needs prepend or not
        #################
        def replacer(match):
            keyword = match.group(1)  # FROM or JOIN
            table = match.group(2)    # the actual table name
            # skip if already qualified or backticked
            if '.' in table or table.startswith('`'):
                return f"{keyword} {table}"
            return f"{keyword} `{DATASET_ID}.{table}`"
      
        # Match FROM or JOIN followed by whitespace and a word
        pattern = r"\b(FROM|JOIN)\s+([`]?[\w]+[`]?)"
        return re.sub(pattern, replacer, query, flags=re.IGNORECASE)

    # text area for user input
    user_query = st.text_area(
        "Or enter your own SQL query:",
        queries[choice],
        height=300,
    )

    # automatically fix dataset references
    full_query = prepend_dataset(user_query)

    # runs query
    if st.button("Run Query"):
        with st.spinner("Running query..."):
            df = run_query(full_query)
            if not df.empty:
                st.success(f"Returned {len(df)} rows")
                st.dataframe(df)