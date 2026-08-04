# Chicago Tourist Transportation Guide

Streamlit app for exploring Chicago's 317 historic landmarks through the CTA network. Pick a landmark and it finds the nearest transit stop, estimates how crowded that station will be on the day of your visit, and can group landmarks into walkable clusters.

**Live demo:** <https://chicago-tourist-transportation-guide.streamlit.app/>

## Features

Data comes from four City of Chicago Open Data endpoints: 302 L stations, 10,760+ bus stops, 317 designated landmarks, and daily station entry counts.

**Nearest transit.** Computes geodesic distance from the selected landmark to every stop and returns the closest, with walking time, fare, and a folium map connecting the two points.

**Expected crowds.** Predicts how busy the nearest L station will be on your planned visit day using CTA ridership history. Details below.

**Walkable neighborhoods.** DBSCAN clustering over landmark coordinates. Sliders control max walking distance (`eps`) and minimum cluster size.

## Busyness prediction

Built on the [CTA daily station entries dataset](https://data.cityofchicago.org/Transportation/CTA-Ridership-L-Station-Entries-Daily-Totals/5neh-572f), filtered to 2022 onward since ridership patterns changed permanently during the pandemic. The ridership data keys on `map_id` (parent station), which joins against the L stops dataset.

By default the app fetches each station's average entries per day of week in one aggregated Socrata query, then labels each day Quiet, Moderate, or Busy by ranking it within that station's own week. Tiers are station-relative on purpose: 3,000 daily entries would be a record day at a small station and a slow one at Lake/State.

For better estimates, `notebooks/ridership_model.ipynb` trains a `HistGradientBoostingRegressor` on station, day of week, month, week of year, and a federal holiday flag. Train is 2022 to 2024, test is 2025 onward, and the model is scored against a per-station day-of-week mean baseline on MAE and MAPE. The notebook exports `data/ridership_lookup.csv` with per-month predictions, and the app uses that file automatically when it exists.

The data is daily totals, so the app predicts which days are busy rather than which hours. A "Busy" Saturday downtown can still be empty at 8am. Bus stops get no estimate because CTA publishes bus ridership per route, not per stop.

## Why DBSCAN

The goal is to find natural groupings without deciding in advance how many exist. K-Means forces every landmark into a cluster and needs `k` upfront. DBSCAN finds dense regions and marks isolated landmarks as noise, which is closer to how someone plans a walking tour.

Clustering uses haversine rather than Euclidean distance. At Chicago's latitude a degree of longitude covers about 0.74 times the ground distance of a degree of latitude, so Euclidean distance on raw coordinates would treat east-west neighbors as closer than they are. The `eps` slider takes miles and converts to radians internally (`eps_miles / 3958.8`) because scikit-learn's haversine metric expects radians.

## Stack

Streamlit, pandas, numpy, scikit-learn, folium + streamlit-folium, geopy, matplotlib (notebook only). All data pulled live from the Socrata API.

## Repo layout

```
.
├── app.py                          # Streamlit UI
├── helpers.py                      # loaders, distance calcs, DBSCAN, busyness
├── notebooks/
│   └── ridership_model.ipynb       # ridership model, exports the lookup
├── data/
│   └── ridership_lookup.csv        # model predictions (created by the notebook)
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

First load takes a few seconds while the datasets download and cache. To regenerate the model lookup, run the notebook top to bottom. The first run downloads about 200k rows, cached locally after that.

## Limitations

The landmarks dataset is Chicago's official historic preservation list. It has the Manhattan Building and Union Station but not Millennium Park or Navy Pier, so the app suits architecture-focused exploration best.

Walking times assume a 3 mph pace on straight-line distance, ignoring the actual street network.

Busyness estimates reflect daily turnstile entries, not real-time crowding, and cover L stations only.
