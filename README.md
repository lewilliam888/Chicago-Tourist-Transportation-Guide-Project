# Chicago Tourist Transportation Guide

An interactive Streamlit app for exploring Chicago's 317 historic landmarks alongside the CTA transit network. Two modes: find the nearest transit stop to any landmark, or use DBSCAN clustering to identify walkable neighborhoods of nearby attractions.

**Live demo:** https://chicago-tourist-transportation-guide.streamlit.app/

## What it does

The app pulls real-time data from three City of Chicago Open Data endpoints — 302 L train stations, 10,760+ bus stops, and 317 designated landmarks — and lets users interact with it in two ways.

The **nearest transit** mode takes a selected landmark, calculates geodesic distance to every transit stop, and returns the closest one along with walking time, fare, and a folium map showing both points connected by a line.

The **walkable neighborhoods** mode runs DBSCAN clustering on landmark coordinates to surface natural groupings of attractions within walking distance of each other. Users can tune the maximum walking distance (`eps`) and minimum cluster size (`min_samples`) with sliders to see how the cluster structure changes.

## Why DBSCAN

DBSCAN was chosen over K-Means because the goal is to find *natural* clusters of nearby landmarks without specifying how many should exist. K-Means would force every landmark into a cluster and require choosing `k` upfront; DBSCAN identifies dense regions and treats isolated landmarks as noise (label `-1`), which is closer to how someone would actually plan a walking tour.

The clustering uses **haversine distance** rather than Euclidean. Euclidean distance on raw lat/lon coordinates distorts at any latitude away from the equator — at Chicago's latitude (~41.9°N), one degree of longitude is roughly 0.74× the distance of one degree of latitude, so a Euclidean clusterer would treat east-west neighbors as artificially closer than north-south ones. Haversine handles this correctly by treating coordinates as points on a sphere.

The `eps` parameter is exposed in miles for usability and converted to radians internally (`eps_miles / 3958.8`, where 3958.8 is Earth's radius in miles) since scikit-learn's haversine implementation expects radians.

## Stack

- Streamlit for the UI and deployment
- scikit-learn for DBSCAN
- pandas + numpy for data handling
- folium + streamlit-folium for the maps
- geopy for geodesic distance calculations
- Data from the [City of Chicago Open Data Portal](https://data.cityofchicago.org/) via the Socrata API

## Repo layout

```
.
├── app.py            # Streamlit UI, mode toggle, layout
├── helpers.py        # API loaders, distance calcs, DBSCAN, map builders
├── requirements.txt
└── README.md
```

## Running locally

```bash
git clone https://github.com/lewilliam888/Chicago-Tourist-Transportation-Guide-Project.git
cd Chicago-Tourist-Transportation-Guide-Project
pip install -r requirements.txt
streamlit run app.py
```

The first load takes a few seconds while the three datasets are fetched and cached.

## Notes & limitations

The "Individual Landmarks" dataset is Chicago's official historic preservation list — it includes architecturally significant buildings like the Manhattan Building and Union Station, but not modern tourist attractions like Millennium Park or Navy Pier. The app is most useful for architecture-focused exploration.

Walking time estimates assume a 3 mph pace and don't account for elevation, intersections, or the actual pedestrian network.
