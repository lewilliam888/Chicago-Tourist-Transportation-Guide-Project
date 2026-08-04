import streamlit as st
import urllib.request
import urllib.parse
import json
import pandas as pd 
import folium 
from geopy.distance import geodesic 
from geopy.geocoders import Nominatim 

@st.cache_data 
# Define the function to load L train stops from a given URL
def load_l_stops(url):
    resource_url = "https://data.cityofchicago.org/resource/8pix-ypme.json?$limit=5000"
    
    req = urllib.request.Request(resource_url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    with urllib.request.urlopen(req) as data_url:
        data = json.loads(data_url.read().decode()) 

    df = pd.DataFrame(data)
    
    # Extract station information from the JSON structure
    df['stop_id'] = df['stop_id'] 
    df['stop_name'] = df['station_descriptive_name']
    
    # Extract latitude and longitude from location field
    df['latitude'] = df['location'].apply(lambda x: float(x['latitude']) if isinstance(x, dict) and 'latitude' in x else None)
    df['longitude'] = df['location'].apply(lambda x: float(x['longitude']) if isinstance(x, dict) and 'longitude' in x else None)

    # Extract L line colors
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

    # map_id joins to the ridership dataset
    df = df[['stop_id', 'map_id', 'stop_name', 'latitude', 'longitude', 'routes']]
    df = df.dropna(subset=['stop_id', 'stop_name', 'latitude', 'longitude'])
    df = df.drop_duplicates(['stop_id'])
    df['stop_type'] = 'L Train Station'

    return df

@st.cache_data
# Define the function to load bus stops from a given URL
def load_bus_stops(url):
    resource_url = "https://data.cityofchicago.org/resource/qs84-j7wh.json?$limit=20000"
    
    req = urllib.request.Request(resource_url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        with urllib.request.urlopen(req) as data_url:
            raw_response = data_url.read().decode()
            data = json.loads(raw_response)
    except Exception as e:
        st.error(f"Error loading bus stops: {e}")
        return pd.DataFrame(columns=['stop_id', 'stop_name', 'latitude', 'longitude', 'stop_type'])
    
    # Check if data is a dict with nested data
    if isinstance(data, dict):
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
                if 'the_geom' in record and 'coordinates' in record['the_geom']:
                    coords = record['the_geom']['coordinates']
                    processed_data.append({
                        'stop_id': record.get('systemstop', str(len(processed_data))),
                        'stop_name': record.get('public_nam', 'Bus Stop'),
                        'latitude': float(coords[1]),
                        'longitude': float(coords[0]),
                        'routes': record.get('routesstpg', 'Unknown')
                    })
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
    resource_url = "https://data.cityofchicago.org/resource/tdab-kixi.json?$limit=5000"
    
    req = urllib.request.Request(resource_url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    with urllib.request.urlopen(req) as data_url:
        data = json.loads(data_url.read().decode())

    df = pd.DataFrame(data)
    
    # Extract landmark information from the JSON structure
    df['landmark_id'] = df['id']
    df['landmark_name'] = df['landmark_name']
    df['address'] = df['address']
    df['latitude'] = df['latitude'].apply(lambda x: float(x) if x else None)
    df['longitude'] = df['longitude'].apply(lambda x: float(x) if x else None)
    
    df = df[['landmark_id', 'landmark_name', 'address', 'latitude', 'longitude']]
    df = df.dropna(subset=['latitude', 'longitude', 'landmark_name']) 
    df = df.drop_duplicates(['landmark_id']) 
    
    return df

# Define the function to combine transit stops
def combine_transit_stops(df1, df2):
    df = pd.concat([df1, df2], ignore_index=True)
    return df

# Function to determine marker color based on the type of stop
def get_marker_color(stop_type):
    if stop_type == 'L Train Station':
        return 'blue'
    else:
        return 'green'

# Define the function to geocode an address
def geocode(address):
    geolocator = Nominatim(user_agent="chicago-transport-guide")
    location = geolocator.geocode(address)
    if location is None:
        return '' 
    else:
        return (location.latitude, location.longitude)

# Define the function to get the closest transit stop to a landmark
def get_closest_stop(landmark_latlon, df):
    """Calculate distance from each stop to the landmark and return a single stop id, lat, lon"""
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
    chosen_stop.append(closest['stop_id'])
    chosen_stop.append(closest['lat'])
    chosen_stop.append(closest['lon'])
    chosen_stop.append(closest['stop_name'])
    chosen_stop.append(closest['stop_type'])
    chosen_stop.append(closest['distance'])
    chosen_stop.append(closest.get('routes', 'Unknown'))
    chosen_stop.append(closest.get('map_id'))  # NaN for bus stops

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

    return m

# NEW FEATURE: Average walking times
def calculate_walking_time(distance_miles):
    minutes = distance_miles * 20
    if minutes < 1:
        return "Less than 1 minute walk"
    elif minutes < 60:
        return f"~{int(minutes)} minute walk"
    else:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"~{hours}h {mins}min walk"
    
# NEW FEATURE: Fare prices
def get_fare_info(stop_type):
    """Return fare information based on transit type"""
    fares = {
        "L Train Station": "$2.50",
        "Bus Stop": "$2.25"
    }
    return fares.get(stop_type, "$2.50")

from sklearn.cluster import DBSCAN
import numpy as np

@st.cache_data
def cluster_landmarks(landmark_df, eps_miles=0.5, min_samples=3):
    coords = landmark_df[['latitude', 'longitude']].to_numpy()
    coords_rad = np.radians(coords)
    eps_rad = eps_miles / 3958.8
    
    db = DBSCAN(eps=eps_rad, min_samples=min_samples, metric='haversine')
    labels = db.fit_predict(coords_rad)
    
    result = landmark_df.copy()
    result['cluster'] = labels
    return result


def get_cluster_color(cluster_id):
    if cluster_id == -1:
        return 'gray'
    colors = [
        'red', 'blue', 'green', 'purple', 'orange',
        'darkred', 'darkblue', 'darkgreen', 'cadetblue',
        'darkpurple', 'pink', 'lightred', 'beige',
        'lightblue', 'lightgreen', 'black'
    ]
    return colors[cluster_id % len(colors)]


def create_cluster_map(clustered_df):
    center_lat = clustered_df['latitude'].mean()
    center_lon = clustered_df['longitude'].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    for _, row in clustered_df.iterrows():
        color = get_cluster_color(row['cluster'])
        cluster_label = f"Cluster {row['cluster']}" if row['cluster'] != -1 else "Isolated"

        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=6,
            popup=f"<b>{row['landmark_name']}</b><br>{cluster_label}",
            tooltip=row['landmark_name'],
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7
        ).add_to(m)

    return m


# NEW FEATURE: Expected crowds at L stations
import os
import io
import datetime

RIDERSHIP_AGG_URL = (
    "https://data.cityofchicago.org/resource/5neh-572f.csv"
    "?$select=station_id,date_extract_dow(date),avg(rides)"
    "&$where=date>'2022-01-01'"
    "&$group=station_id,date_extract_dow(date)"
    "&$limit=1200"
)

DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday",
             "Thursday", "Friday", "Saturday"]  # index = Socrata dow


def _add_tiers(df):
    """Label each station-day Quiet/Moderate/Busy relative to that station's own week."""
    pct = df.groupby('station_id')['expected_rides'].rank(pct=True)
    df['tier'] = pd.cut(
        pct, bins=[0, 1/3, 2/3, 1],
        labels=['Quiet', 'Moderate', 'Busy'],
        include_lowest=True
    ).astype(str)
    return df


@st.cache_data
def load_ridership_profile():
    """Return (profile_df, source_label), or (None, None) if unavailable."""
    lookup_path = os.path.join(os.path.dirname(__file__), 'data', 'ridership_lookup.csv')
    if os.path.exists(lookup_path):
        df = pd.read_csv(lookup_path, dtype={'station_id': str})
        df = df.rename(columns={'pred_rides': 'expected_rides'})
        if 'month' in df.columns:
            df = df[df['month'] == datetime.date.today().month].drop(columns='month')
        source = 'model prediction'
    else:
        try:
            req = urllib.request.Request(RIDERSHIP_AGG_URL)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            with urllib.request.urlopen(req) as resp:
                text = resp.read().decode()
            df = pd.read_csv(io.StringIO(text), dtype={'station_id': str})
        except Exception:
            return None, None
        df = df.rename(columns={'date_extract_dow_date': 'dow', 'avg_rides': 'expected_rides'})
        source = 'historical average since 2022'

    df['dow'] = df['dow'].astype(int)
    df['expected_rides'] = df['expected_rides'].astype(float)
    if 'tier' not in df.columns:
        df = _add_tiers(df)

    return df, source


# NEW FEATURE: Tourist attractions from OpenStreetMap

CHICAGO_BBOX = "41.64,-87.95,42.03,-87.50"

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
OVERPASS_URL = OVERPASS_ENDPOINTS[0]

OVERPASS_QUERY = f"""
[out:json][timeout:90];
(
  nwr["tourism"~"^(museum|gallery|zoo|aquarium|theme_park)$"]["name"]({CHICAGO_BBOX});
  nwr["tourism"~"^(attraction|viewpoint|artwork)$"]["name"]["wikipedia"]({CHICAGO_BBOX});
  nwr["leisure"="park"]["name"]["wikipedia"]({CHICAGO_BBOX});
  nwr["amenity"="planetarium"]["name"]({CHICAGO_BBOX});
  nwr["leisure"="stadium"]["name"]["wikipedia"]({CHICAGO_BBOX});
  nwr["man_made"="tower"]["name"]["wikipedia"]({CHICAGO_BBOX});
  nwr["building"]["height"]["name"]["wikipedia"]({CHICAGO_BBOX});
);
out center tags;
"""

ARCHITECTURE_CATEGORY = "Architecture (Historic Landmarks)"

OSM_CATEGORY_LABELS = [
    "Iconic Attractions",
    "Museums & Galleries",
    "Parks & Outdoors",
    "Zoos & Family",
]


def _osm_category(tags):
    tourism = tags.get("tourism", "")
    if tourism in ("museum", "gallery") or tags.get("amenity") == "planetarium":
        return "Museums & Galleries"
    if tourism in ("zoo", "aquarium", "theme_park"):
        return "Zoos & Family"
    if tourism in ("attraction", "viewpoint", "artwork"):
        return "Iconic Attractions"
    if tags.get("leisure") == "stadium" or tags.get("man_made") == "tower":
        return "Iconic Attractions"
    if tags.get("building") and tags.get("height") and tags.get("wikipedia"):
        return "Iconic Attractions"
    if tags.get("leisure") == "park":
        return "Parks & Outdoors"
    return None


def _wiki_title(tags):
    wiki = tags.get("wikipedia", "")
    if wiki.startswith("en:"):
        return wiki[3:]
    return None


def _display_name(tags):
    """Official name, with the local nickname if one exists (Cloud Gate (The Bean))."""
    name = tags.get("name")
    nickname = tags.get("loc_name") or tags.get("alt_name") or tags.get("short_name")
    if nickname and nickname.lower() != name.lower():
        return f"{name} ({nickname})"
    return name


@st.cache_data
def load_osm_attractions():
    """Chicago tourist attractions from data/attractions.csv, or Overpass if absent."""
    cols = ['landmark_name', 'category', 'latitude', 'longitude', 'wiki_title', 'monthly_views']
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'attractions.csv')
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df = df.rename(columns={'name': 'landmark_name'})
        for c in cols:
            if c not in df.columns:
                df[c] = np.nan
        return df[cols]

    payload = None
    data = urllib.parse.urlencode({'data': OVERPASS_QUERY}).encode()
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            req = urllib.request.Request(endpoint, data=data)
            req.add_header('User-Agent', 'chicago-tourist-transport-guide (github.com/lewilliam888)')
            with urllib.request.urlopen(req, timeout=90) as resp:
                payload = json.loads(resp.read().decode())
            break
        except Exception:
            continue
    if payload is None:
        st.warning("Could not load OSM attractions (all Overpass servers busy). Showing historic landmarks only.")
        return pd.DataFrame(columns=cols)

    rows = []
    for el in payload.get('elements', []):
        tags = el.get('tags', {})
        name = tags.get('name')
        category = _osm_category(tags)
        if not name or category is None:
            continue
        lat = el.get('lat') or el.get('center', {}).get('lat')
        lon = el.get('lon') or el.get('center', {}).get('lon')
        if lat is None or lon is None:
            continue
        rows.append({
            'landmark_name': _display_name(tags),
            'category': category,
            'latitude': float(lat),
            'longitude': float(lon),
            'wiki_title': _wiki_title(tags),
            'monthly_views': np.nan,
            '_wikidata': tags.get('wikidata'),
        })

    df = pd.DataFrame(rows)
    if len(df) == 0:
        return pd.DataFrame(columns=cols)

    # same place can appear as both a node and a way
    has_wd = df['_wikidata'].notna()
    df = pd.concat([
        df[has_wd].drop_duplicates('_wikidata'),
        df[~has_wd],
    ])
    df = df.drop_duplicates(['landmark_name', 'category'])
    return df[cols].reset_index(drop=True)


def build_attraction_pool(landmark_df, osm_df):
    """Combine historic landmarks (as the Architecture category) with OSM attractions."""
    arch = landmark_df.copy()
    arch['category'] = ARCHITECTURE_CATEGORY
    arch['wiki_title'] = None
    arch['monthly_views'] = np.nan
    keep = ['landmark_name', 'category', 'latitude', 'longitude', 'wiki_title', 'monthly_views']
    if osm_df is None or len(osm_df) == 0:
        return arch[keep].reset_index(drop=True)
    return pd.concat([arch[keep], osm_df[keep]], ignore_index=True)


def get_busyness(map_id, dow, profile_df):
    """Busyness for one station on one day of week, or None if no data."""
    if profile_df is None or map_id is None or pd.isna(map_id):
        return None
    station = profile_df[profile_df['station_id'] == str(map_id)]
    if len(station) == 0:
        return None
    day_rows = station[station['dow'] == dow]
    if len(day_rows) == 0:
        return None
    row = day_rows.iloc[0]
    typical = station['expected_rides'].mean()
    return {
        'tier': row['tier'],
        'expected_rides': row['expected_rides'],
        'pct_vs_typical': (row['expected_rides'] - typical) / typical * 100,
    }
