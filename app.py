from helpers import *
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import helpers

st.set_page_config(
    page_title="Chicago Tourist Transport Guide",
    page_icon="🚇",
    layout="wide"
)

st.title('Chicago Tourist Transportation Guide')
st.markdown('Exploring Chicago? Select a landmark from the dropdown menu to find the closest CTA "L" train station and bus stops!')

# URLs for train, bus, and landmark
train_url = "https://data.cityofchicago.org/api/v3/views/8pix-ypme/query.json"
bus_url = "https://data.cityofchicago.org/api/v3/views/qs84-j7wh/query.json"
landmark_url = "https://data.cityofchicago.org/api/v3/views/tdab-kixi/query.json"

# Load data with spinner
with st.spinner("Loading Chicago landmarks and transit data..."):
    train_df = helpers.load_l_stops(train_url)
    bus_df = helpers.load_bus_stops(bus_url)
    landmark_df = helpers.load_landmarks(landmark_url)
    transit_df = helpers.combine_transit_stops(train_df, bus_df)
    ridership_profile, ridership_source = helpers.load_ridership_profile()
    osm_df = helpers.load_osm_attractions()
    pool_df = helpers.build_attraction_pool(landmark_df, osm_df)

transit_df = transit_df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
transit_df = transit_df.reset_index(drop=True)

# Check if data loaded successfully
if landmark_df is None or transit_df is None or len(landmark_df) == 0 or len(transit_df) == 0:
    st.error("Failed to load data. Please check your internet connection and try again.")
    st.stop()

# Sidebar for landmark selection
st.sidebar.header("Mode")
app_mode = st.sidebar.radio(
    "Choose a view:",
    ["Find Nearest Transit", "Explore Walkable Neighborhoods"],
    index=0
)

# Attraction type filter (applies to both modes)
st.sidebar.markdown("---")
st.sidebar.subheader("Attraction Types")
present = set(str(c) for c in pool_df['category'].dropna())
available_categories = [c for c in
                        [helpers.ARCHITECTURE_CATEGORY] + helpers.OSM_CATEGORY_LABELS
                        if c in present]
selected_categories = st.sidebar.multiselect(
    "Show attractions of type:",
    available_categories,
    default=available_categories
)
poi_df = pool_df[pool_df['category'].isin(selected_categories)].copy()

# Popularity filter (needs data/attractions.csv)
popularity_available = poi_df['monthly_views'].notna().any()
if popularity_available:
    top_only = st.sidebar.checkbox("Top attractions only (by Wikipedia views)", value=False)
    if top_only:
        top_n = st.sidebar.slider("How many top attractions:", 10, 200, 75, step=5)
        ranked = poi_df[poi_df['monthly_views'].notna()].nlargest(top_n, 'monthly_views')
        # landmarks have no pageview data
        arch = poi_df[poi_df['category'] == helpers.ARCHITECTURE_CATEGORY]
        poi_df = ranked if len(ranked) else arch

if len(poi_df) == 0:
    st.warning("No attractions match the current filters. Select at least one attraction type.")
    st.stop()
poi_df = poi_df.reset_index(drop=True)

st.sidebar.markdown("---")

if app_mode == "Find Nearest Transit":
    st.sidebar.header("Select an Attraction")
    st.sidebar.markdown("Filtered by the attraction types above:")

    landmark_names = sorted(poi_df['landmark_name'].unique())
    selected_landmark = st.sidebar.selectbox(
        "Choose an attraction:",
        landmark_names,
        index=0
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Transit Type Preference")
    transit_type_filter = st.sidebar.radio(
        "Find nearest:",
        ["Any Transit Stop", "L Train Station Only", "Bus Stop Only"],
        index=0
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Visit Day")
    import datetime
    today_dow = (datetime.date.today().weekday() + 1) % 7  # convert Mon=0 to Sun=0
    visit_day = st.sidebar.selectbox(
        "Planning to visit on:",
        helpers.DAY_NAMES,
        index=today_dow
    )

    landmark_info = poi_df[poi_df['landmark_name'] == selected_landmark].iloc[0]
    landmark_latlon = (landmark_info['latitude'], landmark_info['longitude'])

    if transit_type_filter == "L Train Station Only":
        filtered_transit_df = transit_df[transit_df['stop_type'] == 'L Train Station'].copy()
    elif transit_type_filter == "Bus Stop Only":
        filtered_transit_df = transit_df[transit_df['stop_type'] == 'Bus Stop'].copy()
    else:
        filtered_transit_df = transit_df.copy()
    filtered_transit_df = filtered_transit_df.reset_index(drop=True)

    if len(filtered_transit_df) == 0:
        st.error(f"❌ No {transit_type_filter.lower()} found in the dataset.")
        st.stop()

    closest_stop = helpers.get_closest_stop(landmark_latlon, filtered_transit_df)

    st.subheader("📍 Selected Landmark & Nearest Transit Stop")
    col1, col2, col3, col4 = st.columns([2, 3, 1, 2])
    with col1:
        st.markdown("**Landmark**")
        st.info(selected_landmark)
    with col2:
        st.markdown("**Nearest Stop**")
        st.info(closest_stop[3])
    with col3:
        walking_time = helpers.calculate_walking_time(closest_stop[5])
        st.markdown("**Walking Time**")
        st.info(walking_time)
    with col4:
        st.markdown("**Stop Type**")
        st.info(closest_stop[4])

    # NEW FEATURE: expected crowds
    if closest_stop[4] == 'L Train Station':
        busyness = helpers.get_busyness(
            closest_stop[7], helpers.DAY_NAMES.index(visit_day), ridership_profile
        )
        if busyness is not None:
            st.subheader("👥 Expected Crowds")
            tier_emoji = {"Quiet": "🟢", "Moderate": "🟡", "Busy": "🔴"}
            bcol1, bcol2, bcol3 = st.columns(3)
            with bcol1:
                st.metric(
                    f"{visit_day} at this station",
                    f"{tier_emoji.get(busyness['tier'], '')} {busyness['tier']}"
                )
            with bcol2:
                st.metric("Expected entries", f"{busyness['expected_rides']:,.0f} riders/day")
            with bcol3:
                st.metric("Vs. typical day here", f"{busyness['pct_vs_typical']:+.0f}%")
            st.caption(
                f"Source: CTA daily station entries, 2022-present ({ridership_source}). "
                "Tiers compare this day against the station's own weekly pattern. "
                "Estimates are per day, not per hour."
            )
        elif ridership_profile is not None:
            st.caption("👥 No ridership history available for this station.")
    else:
        st.caption("👥 Crowd estimates are available for L stations only. CTA publishes ridership per bus route, not per stop.")

    st.subheader("🗺️ Location Map")
    map_obj = helpers.create_transit_map(
        landmark_info['latitude'], landmark_info['longitude'],
        landmark_info['landmark_name'],
        closest_stop[1], closest_stop[2], closest_stop[3],
        closest_stop[4], closest_stop[6]
    )
    st_folium(map_obj, width=1400, height=600)

    with st.expander("ℹ️ Detailed Information"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("**Attraction Details:**")
            st.write(f"- **Name:** {landmark_info['landmark_name']}")
            st.write(f"- **Type:** {landmark_info['category']}")
            if 'address' in landmark_info and pd.notna(landmark_info.get('address')):
                st.write(f"- **Address:** {landmark_info['address']}")
            if pd.notna(landmark_info.get('monthly_views')):
                st.write(f"- **Wikipedia views:** {landmark_info['monthly_views']:,.0f}/month")
            st.write(f"- **Coordinates:** {landmark_info['latitude']:.6f}, {landmark_info['longitude']:.6f}")
        with col_b:
            fare = helpers.get_fare_info(closest_stop[4])
            st.write("**Transit Stop Details:**")
            st.write(f"- **Stop Name:** {closest_stop[3]}")
            st.write(f"- **Stop Type:** {closest_stop[4]}")
            st.write(f"- **Routes:** {closest_stop[6]}")
            st.write(f"- **Fare:** {fare}")
            st.write(f"- **Walking Distance:** {closest_stop[5]:.4f} miles")
            st.write(f"- **Estimated Walking Time:** {walking_time}")

else:
    st.sidebar.header("Cluster Settings")
    st.sidebar.markdown("Adjust how landmarks are grouped into walkable neighborhoods.")
    
    eps_miles = st.sidebar.slider(
        "Max walking distance between landmarks (miles)",
        min_value=0.1, max_value=2.0, value=0.5, step=0.1
    )
    min_samples = st.sidebar.slider(
        "Minimum landmarks per cluster",
        min_value=2, max_value=10, value=3, step=1
    )
    
    clustered_df = helpers.cluster_landmarks(poi_df, eps_miles=eps_miles, min_samples=min_samples)
    
    n_clusters = len(set(clustered_df['cluster'])) - (1 if -1 in clustered_df['cluster'].values else 0)
    n_noise = (clustered_df['cluster'] == -1).sum()
    n_clustered = (clustered_df['cluster'] != -1).sum()
    
    st.subheader("🏘️ Walkable Landmark Neighborhoods")
    st.markdown(
        "Landmarks are grouped using **DBSCAN clustering** with haversine distance. "
        "Each color represents a walkable cluster of attractions. Gray markers are isolated landmarks."
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Neighborhoods Found", n_clusters)
    with col2:
        st.metric("Landmarks in Clusters", n_clustered)
    with col3:
        st.metric("Isolated Landmarks", n_noise)
    
    st.subheader("🗺️ Cluster Map")
    cluster_map = helpers.create_cluster_map(clustered_df)
    st_folium(cluster_map, width=1400, height=600)
    
    with st.expander("📋 Browse Clusters"):
        cluster_ids = [c for c in clustered_df['cluster'].unique() if c != -1]
        # most popular clusters first
        if clustered_df['monthly_views'].notna().any():
            cluster_ids = sorted(
                cluster_ids,
                key=lambda c: clustered_df.loc[clustered_df['cluster'] == c, 'monthly_views'].sum(),
                reverse=True
            )
        else:
            cluster_ids = sorted(cluster_ids)
        for cluster_id in cluster_ids:
            cluster_landmarks_df = clustered_df[clustered_df['cluster'] == cluster_id]
            views = cluster_landmarks_df['monthly_views'].sum()
            header = f"**Cluster {cluster_id}** ({len(cluster_landmarks_df)} attractions"
            if views > 0:
                header += f", {views:,.0f} Wikipedia views/month"
            header += ")"
            st.markdown(header)
            names = cluster_landmarks_df.sort_values('monthly_views', ascending=False)
            for _, r in names.iterrows():
                suffix = f" ({r['monthly_views']:,.0f} views/mo)" if pd.notna(r['monthly_views']) else ""
                st.write(f"- {r['landmark_name']}{suffix}")

# Information about transit types
st.sidebar.markdown("---")
st.sidebar.subheader("Transit Types")
st.sidebar.markdown("""
🚇 **L Train Station** - Chicago's elevated rapid transit system  
🚌 **Bus Stop** - CTA bus stops throughout the city
""")

# Statistics
st.sidebar.markdown("---")
st.sidebar.subheader("Data Statistics")
st.sidebar.write(f"Attractions shown: {len(poi_df)}")
st.sidebar.write(f"Historic Landmarks: {len(landmark_df)}")
st.sidebar.write(f"OSM Attractions: {len(osm_df)}")
st.sidebar.write(f"Total L Stations: {len(train_df)}")
st.sidebar.write(f"Total Bus Stops: {len(bus_df)}")

# Footer
st.markdown("---")
st.markdown("*Data sources: City of Chicago Data Portal - CTA L Stops, CTA Bus Stops, CTA Daily Station Entries, and Individual Landmarks*")
st.markdown("*Map powered by Folium and OpenStreetMap*")