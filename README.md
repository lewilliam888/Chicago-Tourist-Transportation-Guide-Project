# 🚇 Chicago Tourist Transportation Guide

A web application that helps tourists find the nearest CTA public transit stops to Chicago's official landmarks.

[Live Demo](https://chicago-tourist-transportation-guide-project-pwxqjuwf8p5rajypt.streamlit.app/)

## 📖 Project Overview

This interactive web app allows users to select from 317 Chicago landmarks and instantly find the closest CTA transit stop - whether it's an L train station or bus stop. The app displays the distance, shows an interactive map, and provides detailed information about both locations.

**Built with:** Python, Streamlit, Pandas, Folium, GeoPy

## Key Features

- 🗺️ **Interactive Maps** - Visualize landmarks and transit stops with custom markers and connecting lines
- 🚇 **302 L Train Stations** - Complete CTA elevated train network
- 🚌 **10,760+ Bus Stops** - Full CTA bus stop coverage
- 📍 **317 Historic Landmarks** - Official Chicago individual landmarks
- 🎯 **Smart Filtering** - Choose to search only L trains, only buses, or both
- 📏 **Accurate Distance Calculations** - Uses geodesic distance for real walking distances
- ⚡ **Optimized Performance** - Vectorized calculations handle 11,000+ data points efficiently

*Select a landmark, choose your preferred transit type, and instantly see the nearest stop with distance and map.*

## 🛠️ Technical Implementation

### Technologies Used
- **Streamlit** - Web framework for rapid application development
- **Pandas** - Data manipulation and analysis
- **Folium** - Interactive map visualizations
- **GeoPy** - Geospatial distance calculations
- **Python 3.11** - Core programming language

### Data Sources
All data sourced from the [City of Chicago Data Portal](https://data.cityofchicago.org/):
- [CTA L Stops](https://data.cityofchicago.org/Transportation/CTA-System-Information-List-of-L-Stops/8pix-ypme) (302 stations)
- [CTA Bus Stops](https://data.cityofchicago.org/Transportation/CTA-Bus-Stops-Shapefile/qs84-j7wh) (10,760+ stops)
- [Individual Landmarks](https://data.cityofchicago.org/Historic-Preservation/Individual-Landmarks/tdab-kixi) (317 landmarks)

### Architecture
- **`app.py`** - Main Streamlit UI with user controls, metrics display, and map rendering
- **`helpers.py`** - Data loading from APIs, distance calculations, and map generation
- Real-time data fetching via Socrata Open Data API
- Streamlit caching for performance optimization
- Vectorized operations for efficient distance calculations across 11,000+ stops

## 🎯 Project Goals & Learning Outcomes

This project demonstrates:
- **API Integration** - Fetching and processing real-time data from public APIs
- **Geospatial Analysis** - Calculating distances and working with coordinate systems
- **Data Optimization** - Handling large datasets (10,000+ records) efficiently
- **UI/UX Design** - Creating an intuitive interface for non-technical users
- **Web Deployment** - Deploying a production-ready app on Streamlit Cloud

## 🔗 Links

- **Live Application**: [Chicago Tourist Transportation Guide](https://chicago-tourist-transportation-guide-project-pwxqjuwf8p5rajypt.streamlit.app/)
- **GitHub Repository**: [View Code](https://github.com/lewilliam888/Chicago-Tourist-Transportation-Guide-Project)

## 👨‍💻 Developer

**William Le**

---
