"""
Quick script to upload all JSON files to BigQuery
Run this ONCE to initialize your database
"""
from home import upload_all_dfs

print("Starting ETL pipeline to upload data to BigQuery...")
print("This may take several minutes for large files...")

try:
    upload_all_dfs("data/", mode="append")
    print("\n✅ Success! All data uploaded to BigQuery.")
    print("You can now run: streamlit run home.py")
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("Check etl_log.txt for details")
