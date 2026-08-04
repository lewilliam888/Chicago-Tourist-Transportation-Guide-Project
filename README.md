# Chicago Tourist Transportation Guide

Streamlit app for exploring Chicago attractions through the CTA network. Pick an attraction and it finds the nearest transit stop, estimates how crowded that station will be on the day of your visit, and can group attractions into walkable clusters ranked by popularity.

**Live demo:** <https://chicago-tourist-transportation-guide.streamlit.app/>

## Features

Data comes from six sources: four City of Chicago Open Data endpoints (302 L stations, 10,760+ bus stops, 317 historic landmarks, daily station entries), OpenStreetMap for tourist attractions, and Wikipedia pageviews for popularity.

**Attraction types.** A sidebar filter with five categories: Iconic Attractions, Museums & Galleries, Parks & Outdoors, Zoos & Family (all from OSM), and Architecture (the city's historic landmarks list). With popularity data present you can also restrict to the top N attractions by Wikipedia views.

**Nearest transit.** Computes geodesic distance from the selected attraction to every stop and returns the closest, with walking time, fare, and a folium map connecting the two points.

**Expected crowds.** Predicts how busy the nearest L station will be on your planned visit day using CTA ridership history. Details below.

**Walkable neighborhoods.** DBSCAN clustering over the filtered attractions. Sliders control max walking distance (`eps`) and minimum cluster size. When popularity data exists, clusters are ranked by combined Wikipedia views, so the first result is the highest-value walkable area for the types you picked.

## Busyness prediction

Built on the [CTA daily station entries dataset](https://data.cityofchicago.org/Transportation/CTA-Ridership-L-Station-Entries-Daily-Totals/5neh-572f), filtered to 2022 onward since ridership patterns changed permanently during the pandemic. The ridership data keys on `map_id` (parent station), which joins against the L stops dataset.

By default the app fetches each station's average entries per day of week in one aggregated Socrata query, then labels each day Quiet, Moderate, or Busy by ranking it within that station's own week. Tiers are station-relative on purpose: 3,000 daily entries would be a record day at a small station and a slow one at Lake/State.

For better estimates, `notebooks/ridership_model.ipynb` trains a `HistGradientBoostingRegressor` on station, day of week, month, week of year, and a federal holiday flag. Train is 2022 to 2024, test is 2025 onward, and the model is scored against a per-station day-of-week mean baseline on MAE and MAPE. The notebook exports `data/ridership_lookup.csv` with per-month predictions, and the app uses that file automatically when it exists.

The data is daily totals, so the app predicts which days are busy rather than which hours. A "Busy" Saturday downtown can still be empty at 8am. Bus stops get no estimate because CTA publishes bus ridership per route, not per stop.

## Attraction sources and popularity

The city's landmarks dataset is a historic preservation list. It is excellent for architecture but has no Millennium Park or Navy Pier, so the app pulls actual tourist attractions from OpenStreetMap through the Overpass API (free, no key). Elements are categorized from their OSM tags, and low-signal categories like artwork require a `wikipedia` tag, which doubles as a quality filter.

Popularity comes from Wikipedia. `notebooks/attractions_popularity.ipynb` resolves each attraction to an English Wikipedia article, using the OSM `wikipedia` tag when present and a geosearch with string-similarity matching otherwise, then averages the last 12 months of pageviews from the Wikimedia REST API. The export (`data/attractions.csv`) unlocks the top-N filter and cluster ranking. Pageviews measure reading interest rather than foot traffic, so the score is used for ranking only and never shown as visitor counts.

Without the export the app still works: it queries Overpass live and simply hides the popularity controls.

## Why DBSCAN

The goal is to find natural groupings without deciding in advance how many exist. K-Means forces every landmark into a cluster and needs `k` upfront. DBSCAN finds dense regions and marks isolated landmarks as noise, which is closer to how someone plans a walking tour.

Clustering uses haversine rather than Euclidean distance. At Chicago's latitude a degree of longitude covers about 0.74 times the ground distance of a degree of latitude, so Euclidean distance on raw coordinates would treat east-west neighbors as closer than they are. The `eps` slider takes miles and converts to radians internally (`eps_miles / 3958.8`) because scikit-learn's haversine metric expects radians.

## Stack

Streamlit, pandas, numpy, scikit-learn, folium + streamlit-folium, geopy, matplotlib (notebook only). All data pulled live from the Socrata API.

## Repo layout

```
.
├── app.py                             # Streamlit UI
├── helpers.py                         # loaders, distance calcs, DBSCAN, busyness, OSM
├── notebooks/
│   ├── ridership_model.ipynb          # ridership model, exports the lookup
│   └── attractions_popularity.ipynb   # Wikipedia matching + pageviews, exports attractions
├── data/
│   ├── ridership_lookup.csv           # ridership model predictions
│   └── attractions.csv                # attractions with popularity (created by the notebook)
├── requirements.txt
└── README.md
```

## Running locally

```
git clone https://github.com/lewilliam888/Chicago-Tourist-Transportation-Guide-Project.git
cd Chicago-Tourist-Transportation-Guide-Project
pip install -r requirements.txt
streamlit run app.py
```

First load takes a few seconds while the datasets download and cache. Two optional notebooks regenerate the committed data files: `ridership_model.ipynb` (downloads about 200k rows on first run, cached after) and `attractions_popularity.ipynb` (a few minutes of throttled Wikipedia API calls).

## Limitations

The landmarks dataset is Chicago's official historic preservation list. It has the Manhattan Building and Union Station but not Millennium Park or Navy Pier, so the app suits architecture-focused exploration best.

Walking times assume a 3 mph pace on straight-line distance, ignoring the actual street network.

Busyness estimates reflect daily turnstile entries, not real-time crowding, and cover L stations only.
