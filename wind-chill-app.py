import math
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

def wind_chill(temp_c, wind_kmh):
    if temp_c > 10 or wind_kmh < 4.8:
        return temp_c
    v = wind_kmh ** 0.16
    return 13.12 + 0.6215*temp_c - 11.37*v + 0.3965*temp_c*v

st.set_page_config(
    page_title="❄ Wind Chill Forecast",
    layout="wide"
)

st.title("Dr. FixIT's Formula to Create Live Wind Chill Forecast")

cities = {
    "Oslo": {"lat": 59.91, "lon": 10.75},
    "Bergen": {"lat": 60.39, "lon": 5.32},
    "Stavanger": {"lat": 58.97, "lon": 5.73},
    "Trondheim": {"lat": 63.43, "lon": 10.39},
    "Drammen": {"lat": 59.74, "lon": 10.20},
    "Fredrikstad": {"lat": 59.22, "lon": 10.95},
    "Kristiansand": {"lat": 58.15, "lon": 8.00},
    "Sandnes": {"lat": 58.85, "lon": 5.74},
    "Tromsø": {"lat": 69.65, "lon": 18.96},
    "Ålesund": {"lat": 62.47, "lon": 6.15},
}

st.sidebar.header("Settings")

city = st.sidebar.selectbox("Choose a city", list(cities.keys()))
lat = cities[city]["lat"]
lon = cities[city]["lon"]

hours = st.sidebar.slider("Forecast hours", 12, 72, 24)
refresh = st.sidebar.slider("Auto-refresh (seconds)", 10, 300, 60)

st_autorefresh(interval=refresh*1000, key="refresh")

url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m,windspeed_10m"
    "&timezone=auto"
)

with st.spinner(f"Fetching forecast for {city}…"):
    try:
        data = requests.get(url, timeout=10, verify=False).json()  # verify=False for local SSL issues
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        st.stop()

df = pd.DataFrame({
    "time": data["hourly"]["time"][:hours],
    "temp_c": data["hourly"]["temperature_2m"][:hours],
    "wind_kmh": data["hourly"]["windspeed_10m"][:hours],
})

df["wind_chill_c"] = df.apply(
    lambda r: wind_chill(r.temp_c, r.wind_kmh),
    axis=1
)

fig = px.line(
    df,
    x="time",
    y=["temp_c", "wind_chill_c"],
    labels={"value": "°C", "variable": "Metric"},
    title=f"Temperature vs Wind Chill in {city}"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader(f"Forecast data for {city}")
st.dataframe(df, use_container_width=True)
