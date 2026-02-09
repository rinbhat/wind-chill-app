# ❄ Live Wind Chill Forecast

Dr. FixIT's formula to create a **live wind chill forecast** using Python, Streamlit, and Plotly. The app fetches hourly temperature and wind speed data from [Open-Meteo API](https://open-meteo.com/) and calculates the wind chill.  

---

## 🌐 Features

- Live wind chill calculation based on temperature and wind speed.
- Interactive **chart** of temperature vs. wind chill.
- **Forecast table** for detailed hourly data.
- **Auto-refresh** option to update the forecast automatically.
- Adjustable **latitude, longitude, forecast hours, and refresh interval** via sidebar.
- Default location set to **Stavanger, Norway** (can be changed in the sidebar).

---

## 📍 Default Location

- **Latitude:** 58.97  
- **Longitude:** 5.73  

You can update the location in the sidebar to your preferred coordinates.

---

## 🛠 Installation

1. Clone or download this repository:

```bash
git clone <your-repo-url>
cd <your-repo-folder>
__________________________________________________________________________________________________________________________

Python Standard Library

math → built-in, no installation required.

Third-party packages (install via pip)
Package	Purpose
requests	Fetches data from the Open-Meteo API.
pandas	Handles tabular data (DataFrame for forecast data).
streamlit	Main framework to build the interactive web app.
plotly	Creates the line chart (plotly.express).
streamlit-autorefresh	Handles automatic refreshing of the app.