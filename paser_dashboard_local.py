"""
PASER Road Assessment Dashboard - Using Local Data
Embedded as a tab in the main Streamlit app
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# Cache data loading
@st.cache_data
def load_paser_shapefile():
    """Load PASER data from local shapefile"""
    shapefile_path = "./PASER_Centerline_FW_PaveX_2025/PASER_Centerline_FW_PaveX_2025/PASER_Centerline_FW_PaveX_2025.shp"
    gdf = gpd.read_file(shapefile_path)

    # Convert to WGS84 for mapping
    gdf = gdf.to_crs(epsg=4326)

    # Extract centroid lat/lon
    gdf['Latitude'] = gdf.geometry.centroid.y
    gdf['Longitude'] = gdf.geometry.centroid.x

    return gdf

def show_paser_dashboard():
    """Main dashboard function to be called from home.py"""

    try:
        # Load data
        with st.spinner("Loading PASER road data..."):
            gdf = load_paser_shapefile()
            st.success(f"✅ Loaded {len(gdf)} segments from shapefile!")

        # Convert to regular DataFrame for easier manipulation
        df = pd.DataFrame(gdf.drop(columns=['geometry']))

        # Clean data - remove null PASER ratings
        df = df[df['PASER_Rati'].notna()].copy()

        st.info(f"📊 After filtering: {len(df)} segments with valid PASER ratings")

    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.error(f"Error details: {type(e).__name__}")
        import traceback
        st.code(traceback.format_exc())
        return

    # Header
    st.title("🛣️ Fort Wayne Road Assessment Dashboard")
    st.markdown(f"""
    **Data Source:** PASER Road Condition Survey
    **Coverage:** {len(df):,} road segments in Fort Wayne, Indiana
    **Ratings:** Manual (2024) vs AI Predictions (2025)
    """)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_manual = df['PASER_Rati'].mean()
        st.metric(
            "Avg Manual Rating",
            f"{avg_manual:.2f}",
            help="Average PASER rating from manual inspection (0-10 scale)"
        )

    with col2:
        avg_ai = df['PXpaser25'].mean()
        delta = avg_ai - avg_manual
        st.metric(
            "Avg AI Prediction",
            f"{avg_ai:.2f}",
            delta=f"{delta:.2f}",
            help="Average PASER rating from AI model (2025)"
        )

    with col3:
        poor_count = len(df[df['PASER_Rati'] <= 3])
        poor_pct = (poor_count / len(df)) * 100
        st.metric(
            "Poor Condition",
            f"{poor_count:,}",
            delta=f"{poor_pct:.1f}%",
            delta_color="inverse",
            help="Roads with PASER ≤ 3"
        )

    with col4:
        good_count = len(df[df['PASER_Rati'] >= 7])
        good_pct = (good_count / len(df)) * 100
        st.metric(
            "Good Condition",
            f"{good_count:,}",
            delta=f"{good_pct:.1f}%",
            help="Roads with PASER ≥ 7"
        )

    st.divider()

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📍 Interactive Heatmap",
        "🤖 AI vs Manual",
        "📊 Distribution",
        "🚧 Worst Roads"
    ])

    # ========================================================================
    # TAB 1: HEATMAP
    # ========================================================================
    with tab1:
        st.header("Road Condition Heatmap")

        # Filter controls
        col1, col2 = st.columns([1, 3])

        with col1:
            rating_filter = st.slider(
                "Filter by Rating",
                0, 10, (0, 10),
                help="Show roads in this rating range"
            )

            color_by = st.radio(
                "Color by:",
                ["Manual (2024)", "AI (2025)"]
            )

            use_clustering = st.checkbox(
                "Use marker clustering (faster)",
                value=True,
                help="Groups nearby markers for better performance"
            )

            # Sampling options
            st.subheader("Sample Size")
            sample_option = st.radio(
                "Display:",
                ["500 points (Fast)", "All points (Slow)", "Custom"],
                help="Choose how many points to display on map"
            )

            if sample_option == "Custom":
                custom_points = st.number_input(
                    "Number of points:",
                    min_value=100,
                    max_value=15000,
                    value=500,
                    step=100
                )
            else:
                custom_points = None

        # Filter data
        filtered = df[
            (df['PASER_Rati'] >= rating_filter[0]) &
            (df['PASER_Rati'] <= rating_filter[1])
        ].copy()

        # Determine MAX_POINTS based on user selection
        if sample_option == "All points (Slow)":
            MAX_POINTS = None
            st.warning("⚠️ Showing all points - this may take 30+ seconds to load!")
        elif sample_option == "Custom":
            MAX_POINTS = custom_points
        else:  # "500 points (Fast)"
            MAX_POINTS = 500

        # Apply sampling
        if MAX_POINTS is not None and len(filtered) > MAX_POINTS:
            filtered_display = filtered.sample(n=MAX_POINTS, random_state=42)
            st.info(f"📍 Showing {MAX_POINTS:,} random samples (out of {len(filtered):,} total segments)")
            st.caption("⚡ Map is sampled for performance. Use filters to show specific roads.")
        else:
            filtered_display = filtered
            if len(filtered) > 1000:
                st.warning(f"📍 Showing all {len(filtered):,} segments - this may take a while to render...")
            else:
                st.info(f"📍 Showing all {len(filtered):,} segments")

        if len(filtered_display) > 0:
            # Create map
            center_lat = filtered_display['Latitude'].mean()
            center_lon = filtered_display['Longitude'].mean()

            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=11,
                tiles="CartoDB positron"
            )

            # Choose rating column
            rating_col = 'PASER_Rati' if "Manual" in color_by else 'PXpaser25'

            # Create marker cluster if enabled
            if use_clustering:
                marker_cluster = MarkerCluster().add_to(m)
                target = marker_cluster
            else:
                target = m

            # Add markers
            for _, row in filtered_display.iterrows():
                rating = row[rating_col]

                # Color logic
                if rating <= 3:
                    color = 'red'
                    condition = 'Poor'
                elif rating <= 6:
                    color = 'orange'
                    condition = 'Fair'
                else:
                    color = 'green'
                    condition = 'Good'

                # Popup
                popup_html = f"""
                <b>{row['Street_Nam']}</b><br>
                Seg ID: {row['Seg_ID']}<br>
                Manual: {row['PASER_Rati']}<br>
                AI: {row['PXpaser25']}<br>
                Surface: {row['Surface_Ty']}<br>
                Condition: <b style='color:{color}'>{condition}</b>
                """

                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=4,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.7,
                    popup=folium.Popup(popup_html, max_width=200),
                    tooltip=f"{row['Street_Nam']}: {rating}"
                ).add_to(target)

            # Legend
            legend_html = '''
            <div style="position: fixed; bottom: 50px; right: 50px;
                        width: 150px; background-color: white;
                        border:2px solid grey; z-index:9999; padding: 10px">
            <p style="margin:0; color:black"><b>PASER Rating</b></p>
            <p style="margin:5px 0; color:black"><span style="color:red">●</span> Poor (0-3)</p>
            <p style="margin:5px 0; color:black"><span style="color:orange">●</span> Fair (4-6)</p>
            <p style="margin:5px 0; color:black"><span style="color:green">●</span> Good (7-10)</p>
            </div>
            '''
            m.get_root().html.add_child(folium.Element(legend_html))

            st.write("🗺️ Rendering map with", len(filtered_display), "markers...")
            st_folium(m, width=1400, height=600)
            st.caption(f"✅ Map displayed with {len(filtered_display)} road segments")

    # ========================================================================
    # TAB 2: AI vs MANUAL
    # ========================================================================
    with tab2:
        st.header("AI vs Manual Analysis")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Scatter plot
            fig = px.scatter(
                df,
                x='PASER_Rati',
                y='PXpaser25',
                hover_data=['Street_Nam', 'Seg_ID'],
                title='AI Predictions vs Manual Ratings',
                labels={
                    'PASER_Rati': 'Manual Rating (2024)',
                    'PXpaser25': 'AI Prediction (2025)'
                },
                opacity=0.5
            )

            # Perfect prediction line
            fig.add_trace(
                go.Scatter(
                    x=[0, 10], y=[0, 10],
                    mode='lines',
                    name='Perfect Prediction',
                    line=dict(dash='dash', color='red', width=2)
                )
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Statistics")

            # Correlation
            corr = df[['PASER_Rati', 'PXpaser25']].corr().iloc[0, 1]
            st.metric("Correlation", f"{corr:.3f}")

            # Difference
            diff = df['PXpaser25'] - df['PASER_Rati']
            st.metric("Mean Difference", f"{diff.mean():.2f}")
            st.metric("Std Dev", f"{diff.std():.2f}")

            # Agreement
            st.subheader("Agreement")
            exact = len(df[df['PASER_Rati'] == df['PXpaser25']])
            within_1 = len(df[abs(diff) <= 1])

            st.write(f"**Exact:** {exact} ({exact/len(df)*100:.1f}%)")
            st.write(f"**±1:** {within_1} ({within_1/len(df)*100:.1f}%)")

        # Difference histogram
        st.subheader("Difference Distribution")
        fig2 = px.histogram(
            diff,
            nbins=20,
            title='AI - Manual Rating Difference',
            labels={'value': 'Difference', 'count': 'Count'}
        )
        fig2.add_vline(x=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig2, use_container_width=True)

    # ========================================================================
    # TAB 3: DISTRIBUTION
    # ========================================================================
    with tab3:
        st.header("Rating Distribution")

        # Comparison
        manual_dist = df['PASER_Rati'].value_counts().sort_index().reset_index()
        manual_dist.columns = ['Rating', 'Count']
        manual_dist['Source'] = 'Manual'

        ai_dist = df['PXpaser25'].value_counts().sort_index().reset_index()
        ai_dist.columns = ['Rating', 'Count']
        ai_dist['Source'] = 'AI'

        combined = pd.concat([manual_dist, ai_dist])

        fig = px.bar(
            combined,
            x='Rating',
            y='Count',
            color='Source',
            barmode='group',
            title='PASER Rating Distribution',
            color_discrete_map={'Manual': '#636EFA', 'AI': '#EF553B'}
        )
        st.plotly_chart(fig, use_container_width=True)

        # Pie charts
        col1, col2 = st.columns(2)

        def categorize(rating):
            if rating <= 3:
                return 'Poor (0-3)'
            elif rating <= 6:
                return 'Fair (4-6)'
            else:
                return 'Good (7-10)'

        with col1:
            manual_cat = df['PASER_Rati'].apply(categorize).value_counts()
            fig1 = px.pie(
                values=manual_cat.values,
                names=manual_cat.index,
                title='Manual Categories'
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            ai_cat = df['PXpaser25'].apply(categorize).value_counts()
            fig2 = px.pie(
                values=ai_cat.values,
                names=ai_cat.index,
                title='AI Categories'
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ========================================================================
    # TAB 4: WORST ROADS
    # ========================================================================
    with tab4:
        st.header("🚧 Roads Needing Attention")

        # Filters
        col1, col2 = st.columns(2)

        with col1:
            threshold = st.selectbox("Rating ≤", [3, 4, 5], index=0)

        with col2:
            sort_by = st.selectbox("Sort by", ["PASER_Rati", "Length"])

        # Filter
        worst = df[df['PASER_Rati'] <= threshold].sort_values(sort_by)

        st.info(f"**{len(worst):,}** roads with rating ≤ {threshold}")

        if len(worst) > 0:
            total_length = worst['Length'].sum()
            st.warning(f"**Total length:** {total_length:,.0f} m ({total_length/1609:.1f} miles)")

            # Table
            display = worst[[
                'Seg_ID', 'Street_Nam', 'PASER_Rati', 'PXpaser25',
                'Length', 'Surface_Ty'
            ]].copy()

            display.columns = ['ID', 'Street', 'Manual', 'AI', 'Length(m)', 'Surface']

            st.dataframe(display, use_container_width=True, height=400)

            # Download
            csv = display.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                f"poor_roads_paser_{threshold}.csv",
                "text/csv"
            )

            # Top 10 chart
            st.subheader("Top 10 Longest Poor Roads")
            top10 = worst.nlargest(10, 'Length')

            fig = px.bar(
                top10,
                x='Length',
                y='Street_Nam',
                orientation='h',
                color='PASER_Rati',
                color_continuous_scale='RdYlGn_r'
            )
            st.plotly_chart(fig, use_container_width=True)

# For standalone testing
if __name__ == "__main__":
    show_paser_dashboard()
