"""
Measure ACTUAL Query Performance from Your BigQuery
Run this to get REAL metrics for your presentation!
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import time
from google.cloud import bigquery
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "vippavexdata")
DATASET_ID = f"{PROJECT_ID}.autonomous_dataset"

client = bigquery.Client(project=PROJECT_ID)

print("\n" + "="*70)
print("MEASURING ACTUAL QUERY PERFORMANCE")
print("="*70 + "\n")

# Define test queries with increasing complexity
queries = {
    "Simple SELECT": f"""
        SELECT * FROM `{DATASET_ID}.segments`
        LIMIT 100
    """,

    "Filtered WHERE": f"""
        SELECT * FROM `{DATASET_ID}.images`
        WHERE Type = 'color'
        LIMIT 1000
    """,

    "Single JOIN": f"""
        SELECT s.Name, COUNT(d.Drive_ID) as drive_count
        FROM `{DATASET_ID}.segments` s
        JOIN `{DATASET_ID}.drives` d ON s.Segment_ID = d.Segment_ID
        GROUP BY s.Name
        LIMIT 100
    """,

    "Multi-JOIN (3 tables)": f"""
        SELECT s.Name as segment_name, COUNT(i.Image_ID) as image_count
        FROM `{DATASET_ID}.segments` s
        JOIN `{DATASET_ID}.drives` d ON s.Segment_ID = d.Segment_ID
        JOIN `{DATASET_ID}.cameras` c ON d.Drive_ID = c.Drive_ID
        GROUP BY s.Name
        ORDER BY image_count DESC
        LIMIT 50
    """,

    "Complex (6-way JOIN)": f"""
        SELECT s.Name AS segment_name,
               cat.Name AS category_name,
               COUNT(*) AS classification_count
        FROM `{DATASET_ID}.image_categories` ic
        JOIN `{DATASET_ID}.categories` cat ON ic.Category_ID = cat.Category_ID
        JOIN `{DATASET_ID}.images` i ON ic.Image_ID = i.Image_ID
        JOIN `{DATASET_ID}.camera_images` ci ON i.Image_ID = ci.Image_ID
        JOIN `{DATASET_ID}.cameras` c ON ci.Camera_ID = c.Camera_ID
        JOIN `{DATASET_ID}.drives` d ON c.Drive_ID = d.Drive_ID
        JOIN `{DATASET_ID}.segments` s ON d.Segment_ID = s.Segment_ID
        GROUP BY s.Name, cat.Name
        ORDER BY classification_count DESC
        LIMIT 100
    """,

    "Aggregation GROUP BY": f"""
        SELECT cat.Name, COUNT(*) as total
        FROM `{DATASET_ID}.image_categories` ic
        JOIN `{DATASET_ID}.categories` cat ON ic.Category_ID = cat.Category_ID
        GROUP BY cat.Name
        ORDER BY total DESC
    """
}

results = {}

print("Running queries (this may take a minute)...\n")

for query_name, query_sql in queries.items():
    print(f"Testing: {query_name}...")

    # Run query 3 times and take average
    times = []
    for i in range(3):
        start = time.time()
        try:
            query_job = client.query(query_sql)
            result = query_job.result()  # Wait for completion
            end = time.time()
            elapsed = end - start
            times.append(elapsed)
            print(f"  Run {i+1}: {elapsed:.2f}s")
        except Exception as e:
            print(f"  ERROR: {e}")
            times.append(None)
            break

    if None not in times:
        avg_time = sum(times) / len(times)
        results[query_name] = avg_time
        print(f"  ✓ Average: {avg_time:.2f}s\n")
    else:
        results[query_name] = None
        print(f"  ✗ Query failed\n")

print("\n" + "="*70)
print("RESULTS SUMMARY")
print("="*70 + "\n")

for query_name, avg_time in results.items():
    if avg_time is not None:
        print(f"{query_name:30s}: {avg_time:.2f}s")
    else:
        print(f"{query_name:30s}: FAILED")

print("\n" + "="*70)
print("💡 USE THESE NUMBERS IN YOUR PRESENTATION!")
print("="*70 + "\n")

print("Copy these values into your visualizations:")
print("-" * 70)
for query_name, avg_time in results.items():
    if avg_time is not None:
        print(f"'{query_name}': {avg_time:.1f},")

print("\n" + "="*70)
print("STORAGE METRICS")
print("="*70 + "\n")

# Get storage metrics
try:
    storage_query = f"""
    SELECT
      table_id,
      row_count,
      ROUND(size_bytes / POW(1024,3), 4) AS size_gb
    FROM `{DATASET_ID}.__TABLES__`
    ORDER BY size_gb DESC
    """

    query_job = client.query(storage_query)
    storage_results = query_job.result()

    print(f"{'Table':<25} {'Rows':>15} {'Size (GB)':>15}")
    print("-" * 60)

    total_size = 0
    for row in storage_results:
        print(f"{row['table_id']:<25} {row['row_count']:>15,} {row['size_gb']:>15.4f}")
        total_size += row['size_gb']

    print("-" * 60)
    print(f"{'TOTAL':<25} {'':<15} {total_size:>15.4f}")

    # Calculate estimated monthly cost
    # BigQuery storage: $0.02 per GB/month (active storage)
    monthly_cost = total_size * 0.02
    print(f"\nEstimated Storage Cost: ${monthly_cost:.2f}/month")

except Exception as e:
    print(f"Could not get storage metrics: {e}")

print("\n" + "="*70)
print("Done! Use these REAL numbers in your charts!")
print("="*70 + "\n")
