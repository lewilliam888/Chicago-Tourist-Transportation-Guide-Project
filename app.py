from helpers import *
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import helpers

# Page configuration
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

# Rename columns for consistency with helper functions
transit_df = transit_df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
# Reset index to ensure continuous indexing after combining
transit_df = transit_df.reset_index(drop=True)

# Check if data loaded successfully
if landmark_df is None or transit_df is None or len(landmark_df) == 0 or len(transit_df) == 0:
    st.error("Failed to load data. Please check your internet connection and try again.")
    st.stop()

# Sidebar for landmark selection
st.sidebar.header("Select a Landmark")
st.sidebar.markdown("Choose from Chicago's official landmarks:")

landmark_names = sorted(landmark_df['landmark_name'].unique())

selected_landmark = st.sidebar.selectbox(
    "Choose a landmark:",
    landmark_names,
    index=0
)

# Add transit type filter
st.sidebar.markdown("---")
st.sidebar.subheader("Transit Type Preference")
transit_type_filter = st.sidebar.radio(
    "Find nearest:",
    ["Any Transit Stop", "L Train Station Only", "Bus Stop Only"],
    index=0
)

# Find the landmark information
landmark_info = landmark_df[landmark_df['landmark_name'] == selected_landmark].iloc[0]
landmark_latlon = (landmark_info['latitude'], landmark_info['longitude'])

# Filter transit stops based on user preference
if transit_type_filter == "L Train Station Only":
    filtered_transit_df = transit_df[transit_df['stop_type'] == 'L Train Station'].copy()
    filtered_transit_df = filtered_transit_df.reset_index(drop=True)
elif transit_type_filter == "Bus Stop Only":
    filtered_transit_df = transit_df[transit_df['stop_type'] == 'Bus Stop'].copy()
    filtered_transit_df = filtered_transit_df.reset_index(drop=True)
else:  # "Any Transit Stop"
    filtered_transit_df = transit_df.copy()
    filtered_transit_df = filtered_transit_df.reset_index(drop=True)

# Check if filtered results are empty
if len(filtered_transit_df) == 0:
    st.error(f"❌ No {transit_type_filter.lower()} found in the dataset. Please select a different transit type.")
    st.info(f"Available transit types: {transit_df['stop_type'].unique().tolist()}")
    st.stop()

# Find the closest stop from filtered results
closest_stop = helpers.get_closest_stop(landmark_latlon, filtered_transit_df)

# Display information in columns
st.subheader("📍 Selected Landmark & Nearest Transit Stop")

col1, col2, col3, col4 = st.columns([2, 3, 1, 2])

with col1:
    st.markdown("**Landmark**")
    st.info(selected_landmark)
    
with col2:
    st.markdown("**Nearest Stop**")
    st.info(closest_stop[3])
    
with col3:
    st.markdown("**Distance**")
    st.info(f"{closest_stop[5]:.2f} mi")

with col4:
    st.markdown("**Stop Type**")
    st.info(closest_stop[4])

# Create and display the map
st.subheader("🗺️ Location Map")
map_obj = helpers.create_transit_map(
    landmark_info['latitude'], 
    landmark_info['longitude'],
    landmark_info['landmark_name'],
    closest_stop[1],
    closest_stop[2],
    closest_stop[3],
    closest_stop[4]
)
st_folium(map_obj, width=1400, height=600)

# Additional information in expandable section
with st.expander("ℹ️ Detailed Information"):
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write("**Landmark Details:**")
        st.write(f"- **Name:** {landmark_info['landmark_name']}")
        if 'address' in landmark_info and pd.notna(landmark_info['address']):
            st.write(f"- **Address:** {landmark_info['address']}")
        st.write(f"- **Coordinates:** {landmark_info['latitude']:.6f}, {landmark_info['longitude']:.6f}")
    
    with col_b:
        st.write("**Transit Stop Details:**")
        st.write(f"- **Stop Name:** {closest_stop[3]}")
        st.write(f"- **Stop Type:** {closest_stop[4]}")
        st.write(f"- **Stop ID:** {closest_stop[0]}")
        st.write(f"- **Coordinates:** {closest_stop[1]:.6f}, {closest_stop[2]:.6f}")
        st.write(f"- **Walking Distance:** {closest_stop[5]:.4f} miles ({closest_stop[5] * 1.60934:.4f} km)")

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
st.sidebar.write(f"Total Landmarks: {len(landmark_df)}")
st.sidebar.write(f"Total L Stations: {len(train_df)}")
st.sidebar.write(f"Total Bus Stops: {len(bus_df)}")
st.sidebar.write(f"Total Transit Stops: {len(transit_df)}")

# Debug: Show what stop types exist
if len(bus_df) == 0:
    st.sidebar.warning("⚠️ Bus stops did not load properly")
st.sidebar.caption(f"Stop types in data: {transit_df['stop_type'].unique().tolist()}")

# Footer
st.markdown("---")
st.markdown("*Data sources: City of Chicago Data Portal - CTA L Stops, CTA Bus Stops, and Individual Landmarks*")
st.markdown("*Map powered by Folium and OpenStreetMap*")