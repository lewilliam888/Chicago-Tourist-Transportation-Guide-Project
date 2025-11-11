import streamlit as st  # Import Streamlit for creating web apps
import urllib.request  # Import module for working with URLs
import json  # Import module for working with JSON data
import pandas as pd  # Import pandas for data manipulation
import folium  # Import folium for creating interactive maps
from geopy.distance import geodesic  # Import geodesic for calculating distances
from geopy.geocoders import Nominatim  # Import Nominatim for geocoding

@st.cache_data  # Cache the function's output to improve performance
# Define the function to load L train stops from a given URL
def load_l_stops(url):
    # Use the correct resource endpoint
    resource_url = "https://data.cityofchicago.org/resource/8pix-ypme.json?$limit=5000"
    
    req = urllib.request.Request(resource_url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    with urllib.request.urlopen(req) as data_url:  # Open the URL
        data = json.loads(data_url.read().decode())  # Read and decode the JSON data

    df = pd.DataFrame(data)  # Convert the data to a DataFrame
    
    # Extract station information from the JSON structure
    df['stop_id'] = df['stop_id']  # Station ID
    df['stop_name'] = df['station_descriptive_name']  # Use descriptive station name
    
    # Extract latitude and longitude from location field
    df['latitude'] = df['location'].apply(lambda x: float(x['latitude']) if isinstance(x, dict) and 'latitude' in x else None)
    df['longitude'] = df['location'].apply(lambda x: float(x['longitude']) if isinstance(x, dict) and 'longitude' in x else None)

    # Extract L line colors (red, blue, green, etc.)
    line_colors = []
    for _, row in df.iterrows():
        colors = []
        if row.get('red') == True:
            colors.append('Red')
        if row.get('blue') == True:
            colors.append('Blue')
        if row.get('g') == True:  # 'g' is Green line
            colors.append('Green')
        if row.get('brn') == True:  # 'brn' is Brown line
            colors.append('Brown')
        if row.get('p') == True:  # 'p' is Purple line
            colors.append('Purple')
        if row.get('pexp') == True:  # 'pexp' is Purple Express
            colors.append('Purple Express')
        if row.get('y') == True:  # 'y' is Yellow line
            colors.append('Yellow')
        if row.get('pnk') == True:  # 'pnk' is Pink line
            colors.append('Pink')
        if row.get('o') == True:  # 'o' is Orange line
            colors.append('Orange')
        line_colors.append(', '.join(colors) if colors else 'Unknown')

    df['routes'] = line_colors

    df = df[['stop_id', 'stop_name', 'latitude', 'longitude', 'routes']]  # Select relevant columns
    df = df.dropna()  # Remove rows with missing data
    df = df.drop_duplicates(['stop_id'])  # Remove duplicate stations
    df['stop_type'] = 'L Train Station'  # Add stop type
    
    return df  # Return the DataFrame

@st.cache_data  # Cache the function's output to improve performance
# Define the function to load bus stops from a given URL
def load_bus_stops(url):
    # Use the CORRECT resource endpoint - qs84-j7wh not hvnx-qtky
    resource_url = "https://data.cityofchicago.org/resource/qs84-j7wh.json?$limit=20000"
    
    req = urllib.request.Request(resource_url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        with urllib.request.urlopen(req) as data_url:  # Open the URL
            raw_response = data_url.read().decode()  # Read and decode
            data = json.loads(raw_response)  # Parse JSON
    except Exception as e:
        st.error(f"Error loading bus stops: {e}")
        return pd.DataFrame(columns=['stop_id', 'stop_name', 'latitude', 'longitude', 'stop_type'])
    
    # Check if data is a dict with nested data
    if isinstance(data, dict):
        # Maybe the actual data is nested under a key?
        if 'data' in data:
            data = data['data']
        elif 'results' in data:
            data = data['results']
    
    # Check if we got any data
    if not data or len(data) == 0:
        st.warning("No bus stop data returned from API")
        return pd.DataFrame(columns=['stop_id', 'stop_name', 'latitude', 'longitude', 'stop_type'])
    
    # Process bus stop records
    processed_data = []
    for record in data:
        try:
            if isinstance(record, dict):
                # Bus stops use 'the_geom' with coordinates array [longitude, latitude]
                if 'the_geom' in record and 'coordinates' in record['the_geom']:
                    coords = record['the_geom']['coordinates']
                    processed_data.append({
                        'stop_id': record.get('systemstop', str(len(processed_data))),
                        'stop_name': record.get('public_nam', 'Bus Stop'),
                        'latitude': float(coords[1]),  # coordinates are [lon, lat]
                        'longitude': float(coords[0]),
                        'routes': record.get('routesstpg', 'Unknown')  # Bus routes
                    })
                # Also check for 'location' format (in case some records use it)
                elif 'location' in record:
                    location = record['location']
                    if isinstance(location, dict) and 'latitude' in location and 'longitude' in location:
                        processed_data.append({
                            'stop_id': record.get('systemstop', record.get('stop_id', str(len(processed_data)))),
                            'stop_name': record.get('public_nam', record.get('public_name', 'Bus Stop')),
                            'latitude': float(location['latitude']),
                            'longitude': float(location['longitude'])
                        })
        except Exception as e:
            continue
    
    if len(processed_data) == 0:
        st.error("Could not process any bus stop records")
        return pd.DataFrame(columns=['stop_id', 'stop_name', 'latitude', 'longitude', 'stop_type'])
    
    df = pd.DataFrame(processed_data)
    df = df.dropna()
    df = df.drop_duplicates(['stop_id'])
    df['stop_type'] = 'Bus Stop'
    
    return df

@st.cache_data  # Cache the function's output to improve performance
# Define the function to load landmarks from a given URL
def load_landmarks(url):
    # Use the correct resource endpoint
    resource_url = "https://data.cityofchicago.org/resource/tdab-kixi.json?$limit=5000"
    
    req = urllib.request.Request(resource_url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    with urllib.request.urlopen(req) as data_url:  # Open the URL
        data = json.loads(data_url.read().decode())  # Read and decode the JSON data

    df = pd.DataFrame(data)  # Convert the data to a DataFrame
    
    # Extract landmark information from the JSON structure
    df['landmark_id'] = df['id']  # Landmark ID
    df['landmark_name'] = df['landmark_name']  # Landmark name
    df['address'] = df['address']  # Address
    df['latitude'] = df['latitude'].apply(lambda x: float(x) if x else None)  # Latitude
    df['longitude'] = df['longitude'].apply(lambda x: float(x) if x else None)  # Longitude
    
    df = df[['landmark_id', 'landmark_name', 'address', 'latitude', 'longitude']]  # Select relevant columns
    df = df.dropna(subset=['latitude', 'longitude', 'landmark_name'])  # Remove rows with missing data
    df = df.drop_duplicates(['landmark_id'])  # Remove duplicates
    
    return df  # Return the DataFrame

# Define the function to combine transit stops
def combine_transit_stops(df1, df2):
    df = pd.concat([df1, df2], ignore_index=True)  # Combine the DataFrames
    return df  # Return the combined DataFrame

# Function to determine marker color based on the type of stop
def get_marker_color(stop_type):
    if stop_type == 'L Train Station':
        return 'blue'
    else:
        return 'green'

# Define the function to geocode an address
def geocode(address):
    geolocator = Nominatim(user_agent="chicago-transport-guide")  # Create a geolocator object
    location = geolocator.geocode(address)  # Geocode the address
    if location is None:
        return ''  # Return an empty string if the address is not found
    else:
        return (location.latitude, location.longitude)  # Return the latitude and longitude

# Define the function to get the closest transit stop to a landmark
def get_closest_stop(landmark_latlon, df):
    """Calculate distance from each stop to the landmark and return a single stop id, lat, lon"""
    # Vectorized distance calculation for better performance
    df = df.copy()
    
    # Calculate all distances at once using vectorized operations
    df['distance'] = df.apply(
        lambda row: geodesic(landmark_latlon, (row['lat'], row['lon'])).miles,
        axis=1
    )
    
    # Find the row with minimum distance
    closest_idx = df['distance'].idxmin()
    closest = df.loc[closest_idx]
    
    chosen_stop = []
    chosen_stop.append(closest['stop_id'])  # Get closest stop ID
    chosen_stop.append(closest['lat'])  # Get latitude
    chosen_stop.append(closest['lon'])  # Get longitude
    chosen_stop.append(closest['stop_name'])  # Get stop name
    chosen_stop.append(closest['stop_type'])  # Get stop type
    chosen_stop.append(closest['distance'])  # Get distance
    chosen_stop.append(closest.get('routes', 'Unknown'))  # Get routes

    return chosen_stop  # Return the chosen stop

# Define the function to create a map showing landmark and transit stop
def create_transit_map(landmark_lat, landmark_lon, landmark_name, stop_lat, stop_lon, stop_name, stop_type, routes):

    """Create a folium map with markers for the landmark and transit stop"""
    # Calculate center point
    center_lat = (landmark_lat + stop_lat) / 2
    center_lon = (landmark_lon + stop_lon) / 2
    
    # Create the map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
    
    # Add marker for the landmark (red star)
    folium.Marker(
        location=[landmark_lat, landmark_lon],
        popup=f"<b>{landmark_name}</b>",
        tooltip=landmark_name,
        icon=folium.Icon(color='red', icon='star', prefix='fa')
    ).add_to(m)
    
    # Add marker for the transit stop (blue/green based on type)
    stop_color = get_marker_color(stop_type)
    stop_icon = 'train' if stop_type == 'L Train Station' else 'bus'
    folium.Marker(
        location=[stop_lat, stop_lon],
        popup=f"<b>{stop_name}</b><br>{stop_type}<br>Routes: {routes}",
        tooltip=stop_name,
        icon=folium.Icon(color=stop_color, icon=stop_icon, prefix='fa')
    ).add_to(m)
    
    # Draw a line between landmark and stop
    folium.PolyLine(
        locations=[[landmark_lat, landmark_lon], [stop_lat, stop_lon]],
        color='purple',
        weight=3,
        opacity=0.7,
        dash_array='10'
    ).add_to(m)
    
    return m  # Return the map