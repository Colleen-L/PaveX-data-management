"""
Road Defects Dashboard - Using Local JSON Data
Embedded as a tab in the main Streamlit app
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import json
import glob
import os

# Cache data loading
@st.cache_data
def load_paser_locations():
    """Load PASER shapefile to get GPS coordinates"""
    import geopandas as gpd
    shapefile_path = "./PASER_Centerline_FW_PaveX_2025/PASER_Centerline_FW_PaveX_2025/PASER_Centerline_FW_PaveX_2025.shp"
    gdf = gpd.read_file(shapefile_path)

    # Convert to WGS84 for mapping
    gdf = gdf.to_crs(epsg=4326)

    # Extract centroid lat/lon
    gdf['Latitude'] = gdf.geometry.centroid.y
    gdf['Longitude'] = gdf.geometry.centroid.x

    # Return only needed columns
    return gdf[['Seg_ID', 'Street_Nam', 'Latitude', 'Longitude', 'PASER_Rati', 'PXpaser25']].copy()

@st.cache_data
def load_defects_data():
    """Load defect classification data from local JSON files and join with PASER GPS"""
    all_data = []

    # Load all JSON files in data folder
    json_files = glob.glob("./data/*.json")

    for file_path in json_files:
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Parse each segment
        for segment_id, segment_data in data.items():
            for drive_id, drive_data in segment_data.items():
                # Get metadata
                dir_day = drive_data.get('dir_day', '')
                dir_pass = drive_data.get('dir_pass', '')

                # Process each camera
                for cam_id in ['cam1', 'cam2']:
                    if cam_id not in drive_data:
                        continue

                    cam_data = drive_data[cam_id]

                    # Get classifications
                    if 'Classification_Swin' in cam_data:
                        classifications = cam_data['Classification_Swin']

                        for category, image_paths in classifications.items():
                            # Extract numeric ID from segment_XXXX format
                            try:
                                seg_num = int(segment_id.replace('segment_', ''))
                            except:
                                seg_num = None

                            all_data.append({
                                'Segment_ID': segment_id,
                                'Seg_ID_Numeric': seg_num,
                                'Drive_ID': drive_id,
                                'Camera': cam_id,
                                'Category': category,
                                'Image_Count': len(image_paths),
                                'Dir_Day': dir_day,
                                'Dir_Pass': dir_pass,
                                'Source_File': os.path.basename(file_path)
                            })

    df = pd.DataFrame(all_data)

    # Load PASER GPS data
    paser_gps = load_paser_locations()

    # Join with PASER data to get GPS coordinates
    df = df.merge(
        paser_gps,
        left_on='Seg_ID_Numeric',
        right_on='Seg_ID',
        how='left',
        suffixes=('', '_paser')
    )

    return df

def show_defects_dashboard():
    """Main dashboard function to be called from home.py"""

    try:
        # Load data
        with st.spinner("Loading road defects data and joining with PASER GPS coordinates..."):
            df = load_defects_data()
            matched = df[df['Latitude'].notna()]['Segment_ID'].nunique()
            total = df['Segment_ID'].nunique()
            st.success(f"✅ Loaded {len(df)} classification records from {df['Source_File'].nunique()} files!")
            st.success(f"✅ Matched {matched}/{total} segments with PASER GPS coordinates ({matched/total*100:.1f}%)")

        st.info(f"📊 Total segments: {total:,}, Total images: {df['Image_Count'].sum():,}")

    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.error(f"Error details: {type(e).__name__}")
        import traceback
        st.code(traceback.format_exc())
        return

    # Header
    st.title("🛣️ Road Defects Analysis Dashboard")
    st.markdown(f"""
    **Data Source:** AI Classification Results (Classification_Swin) + PASER GPS Coordinates
    **Coverage:** {df['Segment_ID'].nunique():,} road segments from Fort Wayne field tests
    **Categories:** {', '.join(sorted(df['Category'].unique()))}
    **GPS Integration:** Joined with PASER shapefile for accurate mapping
    """)

    # Aggregate by segment and category
    segment_agg = df.groupby(['Segment_ID', 'Category']).agg({
        'Image_Count': 'sum'
    }).reset_index()

    # Total defects per segment (excluding 'Health')
    defects_only = segment_agg[segment_agg['Category'] != 'Health'].copy()
    segment_totals = defects_only.groupby('Segment_ID').agg({
        'Image_Count': 'sum'
    }).reset_index()
    segment_totals.columns = ['Segment_ID', 'Total_Defects']

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_images = df['Image_Count'].sum()
        st.metric(
            "Total Images",
            f"{total_images:,}",
            help="Total classified images across all segments"
        )

    with col2:
        total_defect_images = defects_only['Image_Count'].sum()
        defect_pct = (total_defect_images / total_images * 100) if total_images > 0 else 0
        st.metric(
            "Defect Images",
            f"{total_defect_images:,}",
            delta=f"{defect_pct:.1f}%",
            delta_color="inverse",
            help="Images with detected defects (non-Health)"
        )

    with col3:
        segments_with_defects = segment_totals[segment_totals['Total_Defects'] > 0]['Segment_ID'].nunique()
        st.metric(
            "Segments with Defects",
            f"{segments_with_defects:,}",
            help="Number of segments containing defects"
        )

    with col4:
        avg_defects = segment_totals['Total_Defects'].mean()
        st.metric(
            "Avg Defects/Segment",
            f"{avg_defects:.1f}",
            help="Average defect images per segment"
        )

    st.divider()

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📍 Defect Heatmap",
        "📊 Category Analysis",
        "📈 Segment Ranking",
        "🔍 Data Explorer"
    ])

    # ========================================================================
    # TAB 1: HEATMAP
    # ========================================================================
    with tab1:
        st.header("Defect Distribution Heatmap")

        # Filter controls
        col1, col2 = st.columns([1, 3])

        with col1:
            # Category filter
            categories = sorted(df['Category'].unique())
            selected_category = st.selectbox(
                "Show category:",
                ["All Defects"] + categories,
                help="Filter by specific defect category",
                key="defects_category_filter"
            )

            # Sampling options
            st.subheader("Sample Size")
            sample_option = st.radio(
                "Display:",
                ["500 points (Fast)", "All points (Slow)", "Custom"],
                help="Choose how many segments to display on map",
                key="defects_sample_option"
            )

            if sample_option == "Custom":
                custom_points = st.number_input(
                    "Number of points:",
                    min_value=50,
                    max_value=5000,
                    value=500,
                    step=50,
                    key="defects_custom_points"
                )
            else:
                custom_points = None

            use_clustering = st.checkbox(
                "Use marker clustering (faster)",
                value=True,
                help="Groups nearby markers for better performance",
                key="defects_use_clustering"
            )

        # Filter data by category and get GPS from joined PASER data
        if selected_category == "All Defects":
            # Get unique segments with their total defects and GPS
            map_data = df.groupby('Segment_ID').agg({
                'Image_Count': 'sum',
                'Latitude': 'first',
                'Longitude': 'first',
                'Street_Nam': 'first'
            }).reset_index()
            # Only keep defects (exclude Health category)
            defects_df = df[df['Category'] != 'Health'].groupby('Segment_ID')['Image_Count'].sum().reset_index()
            defects_df.columns = ['Segment_ID', 'Defect_Count']
            map_data = map_data.merge(defects_df, on='Segment_ID', how='left')
            map_data['Defect_Count'] = map_data['Defect_Count'].fillna(0)
        else:
            # Filter by specific category
            category_df = df[df['Category'] == selected_category].groupby('Segment_ID').agg({
                'Image_Count': 'sum',
                'Latitude': 'first',
                'Longitude': 'first',
                'Street_Nam': 'first'
            }).reset_index()
            category_df.columns = ['Segment_ID', 'Defect_Count', 'Latitude', 'Longitude', 'Street_Nam']
            map_data = category_df

        # Remove segments without GPS coordinates
        map_data = map_data[map_data['Latitude'].notna() & map_data['Longitude'].notna()].copy()

        # Determine MAX_POINTS based on user selection
        if sample_option == "All points (Slow)":
            MAX_POINTS = None
            st.warning("⚠️ Showing all points - this may take 30+ seconds to load!")
        elif sample_option == "Custom":
            MAX_POINTS = custom_points
        else:  # "500 points (Fast)"
            MAX_POINTS = 500

        # Apply sampling
        if MAX_POINTS is not None and len(map_data) > MAX_POINTS:
            map_display = map_data.sample(n=MAX_POINTS, random_state=42)
            st.info(f"📍 Showing {MAX_POINTS:,} random samples (out of {len(map_data):,} total segments)")
            st.caption("⚡ Map is sampled for performance. Use filters to show specific areas.")
        else:
            map_display = map_data
            if len(map_data) > 1000:
                st.warning(f"📍 Showing all {len(map_data):,} segments - this may take a while to render...")
            else:
                st.info(f"📍 Showing all {len(map_data):,} segments")

        if len(map_display) > 0:
            # Create map
            center_lat = map_display['Latitude'].mean()
            center_lon = map_display['Longitude'].mean()

            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=11,
                tiles="CartoDB positron"
            )

            # Create marker cluster if enabled
            if use_clustering:
                marker_cluster = MarkerCluster().add_to(m)
                target = marker_cluster
            else:
                target = m

            # Add markers
            for _, row in map_display.iterrows():
                defect_count = row['Defect_Count']

                # Color logic based on defect severity
                if defect_count == 0:
                    color = 'green'
                    severity = 'None'
                elif defect_count < 10:
                    color = 'lightgreen'
                    severity = 'Low'
                elif defect_count < 50:
                    color = 'orange'
                    severity = 'Medium'
                elif defect_count < 100:
                    color = 'darkorange'
                    severity = 'High'
                else:
                    color = 'red'
                    severity = 'Critical'

                # Popup with street name from PASER
                street_name = row.get('Street_Nam', 'Unknown')
                popup_html = f"""
                <b>{street_name}</b><br>
                Segment: {row['Segment_ID']}<br>
                Category: {selected_category}<br>
                Defect Count: {defect_count}<br>
                Severity: <b style='color:{color}'>{severity}</b>
                """

                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=6,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.7,
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"{street_name}: {defect_count} defects"
                ).add_to(target)

            # Legend
            legend_html = '''
            <div style="position: fixed; bottom: 50px; right: 50px;
                        width: 160px; background-color: white;
                        border:2px solid grey; z-index:9999; padding: 10px">
            <p style="margin:0; color:black"><b>Defect Severity</b></p>
            <p style="margin:5px 0; color:black"><span style="color:green">●</span> None (0)</p>
            <p style="margin:5px 0; color:black"><span style="color:lightgreen">●</span> Low (1-9)</p>
            <p style="margin:5px 0; color:black"><span style="color:orange">●</span> Medium (10-49)</p>
            <p style="margin:5px 0; color:black"><span style="color:darkorange">●</span> High (50-99)</p>
            <p style="margin:5px 0; color:black"><span style="color:red">●</span> Critical (100+)</p>
            </div>
            '''
            m.get_root().html.add_child(folium.Element(legend_html))

            st.write("🗺️ Rendering map with", len(map_display), "markers...")
            st_folium(m, width=1400, height=600)
            st.caption(f"✅ Map displayed with {len(map_display)} segments using real GPS coordinates from PASER data")

            # Show join statistics
            total_segments = df['Segment_ID'].nunique()
            matched_segments = df[df['Latitude'].notna()]['Segment_ID'].nunique()
            st.info(f"📍 GPS Match: {matched_segments}/{total_segments} segments ({matched_segments/total_segments*100:.1f}%) matched with PASER coordinates")

    # ========================================================================
    # TAB 2: CATEGORY ANALYSIS
    # ========================================================================
    with tab2:
        st.header("Defect Category Analysis")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Bar chart: Category distribution
            category_totals = df.groupby('Category')['Image_Count'].sum().reset_index()
            category_totals = category_totals.sort_values('Image_Count', ascending=False)

            fig = px.bar(
                category_totals,
                x='Category',
                y='Image_Count',
                title='Defect Category Distribution',
                labels={'Image_Count': 'Number of Images', 'Category': 'Defect Category'},
                color='Image_Count',
                color_continuous_scale='RdYlGn_r'
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Statistics")

            # Top category
            top_cat = category_totals.iloc[0]
            st.metric("Most Common", top_cat['Category'], f"{top_cat['Image_Count']:,} images")

            # Category count
            st.metric("Total Categories", len(category_totals))

            # Pie chart
            fig2 = px.pie(
                category_totals,
                values='Image_Count',
                names='Category',
                title='Category Proportion'
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Segment-level category heatmap
        st.subheader("Category Distribution by Segment")

        # Pivot table: segments vs categories
        pivot = segment_agg.pivot(index='Segment_ID', columns='Category', values='Image_Count').fillna(0)

        # Take top 20 segments by total defects
        pivot['Total'] = pivot.sum(axis=1)
        top_segments = pivot.nlargest(20, 'Total').drop(columns=['Total'])

        fig3 = px.imshow(
            top_segments.T,
            labels=dict(x="Segment", y="Category", color="Image Count"),
            title="Top 20 Segments - Category Heatmap",
            aspect="auto",
            color_continuous_scale='YlOrRd'
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ========================================================================
    # TAB 3: SEGMENT RANKING
    # ========================================================================
    with tab3:
        st.header("📈 Segment Defect Ranking")

        # Filters
        col1, col2 = st.columns(2)

        with col1:
            min_defects = st.slider(
                "Minimum defects:",
                0, int(segment_totals['Total_Defects'].max()),
                0,
                help="Filter segments with at least this many defects",
                key="defects_min_slider"
            )

        with col2:
            sort_by = st.selectbox("Sort by", ["Total_Defects", "Segment_ID"], key="defects_sort_by")

        # Filter and sort
        filtered_segments = segment_totals[segment_totals['Total_Defects'] >= min_defects].sort_values(
            sort_by, ascending=(sort_by == "Segment_ID")
        )

        st.info(f"**{len(filtered_segments):,}** segments with ≥ {min_defects} defects")

        if len(filtered_segments) > 0:
            # Top 10 chart
            st.subheader("Top 10 Segments by Defect Count")
            top10 = filtered_segments.nlargest(10, 'Total_Defects')

            fig = px.bar(
                top10,
                x='Total_Defects',
                y='Segment_ID',
                orientation='h',
                title='Top 10 Most Defective Segments',
                color='Total_Defects',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Full table
            st.subheader("All Filtered Segments")
            st.dataframe(filtered_segments, use_container_width=True, height=400)

            # Download
            csv = filtered_segments.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                f"segments_min{min_defects}_defects.csv",
                "text/csv"
            )

    # ========================================================================
    # TAB 4: DATA EXPLORER
    # ========================================================================
    with tab4:
        st.header("🔍 Data Explorer")

        st.subheader("Raw Classification Data")

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_category = st.multiselect(
                "Categories:",
                sorted(df['Category'].unique()),
                default=None,
                key="defects_explorer_category"
            )

        with col2:
            filter_camera = st.multiselect(
                "Cameras:",
                sorted(df['Camera'].unique()),
                default=None,
                key="defects_explorer_camera"
            )

        with col3:
            filter_source = st.multiselect(
                "Source Files:",
                sorted(df['Source_File'].unique()),
                default=None,
                key="defects_explorer_source"
            )

        # Apply filters
        filtered_df = df.copy()
        if filter_category:
            filtered_df = filtered_df[filtered_df['Category'].isin(filter_category)]
        if filter_camera:
            filtered_df = filtered_df[filtered_df['Camera'].isin(filter_camera)]
        if filter_source:
            filtered_df = filtered_df[filtered_df['Source_File'].isin(filter_source)]

        st.info(f"Showing {len(filtered_df):,} records (filtered from {len(df):,} total)")

        st.dataframe(filtered_df, use_container_width=True, height=500)

        # Download
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            "📥 Download Filtered Data",
            csv,
            "filtered_classifications.csv",
            "text/csv"
        )

        # Summary stats
        st.subheader("Summary Statistics")
        col1, col2 = st.columns(2)

        with col1:
            st.write("**By Category:**")
            cat_summary = filtered_df.groupby('Category').agg({
                'Image_Count': ['sum', 'mean', 'count']
            }).round(2)
            cat_summary.columns = ['Total Images', 'Avg per Record', 'Record Count']
            st.dataframe(cat_summary)

        with col2:
            st.write("**By Camera:**")
            cam_summary = filtered_df.groupby('Camera').agg({
                'Image_Count': ['sum', 'mean', 'count']
            }).round(2)
            cam_summary.columns = ['Total Images', 'Avg per Record', 'Record Count']
            st.dataframe(cam_summary)

# For standalone testing
if __name__ == "__main__":
    show_defects_dashboard()
