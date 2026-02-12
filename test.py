import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import ssl
import certifi
from streamlit_autorefresh import st_autorefresh

# -------------------------------------------------
# 🔐 SSL FIX (IGNORE CERT ERRORS SAFELY)
# -------------------------------------------------
ssl._create_default_https_context = ssl._create_unverified_context

# -------------------------------------------------
# 🔁 AUTO REFRESH (every 10 minutes)
# -------------------------------------------------
st_autorefresh(interval=600_000, key="refresh")

# -------------------------------------------------
# 🌍 APP CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Norway Weather Forecast",
    page_icon="🌦️",
    layout="wide"
)

st.title("🌦️ Norway Weather Forecast")
st.caption("Live hourly forecast ")

# -------------------------------------------------
# 🏙️ TOP 10 CITIES IN NORWAY
# -------------------------------------------------
CITIES = {
    "Oslo": (59.91, 10.75),
    "Bergen": (60.39, 5.32),
    "Trondheim": (63.43, 10.39),
    "Stavanger": (58.97, 5.73),
    "Kristiansand": (58.15, 7.995),
    "Drammen": (59.74, 10.20),
    "Fredrikstad": (59.22, 10.93),
    "Tromsø": (69.65, 18.96),
    "Ålesund": (62.47, 6.15),
    "Bodø": (67.28, 14.37),
    "Narvik": (68.44, 17.43),
    "Alta": (69.97, 23.27),
    "Molde": (62.74, 7.16),
    "Haugesund": (59.41, 5.27),
    "Sandefjord": (59.13, 10.22),
}
# -------------------------------------------------
# 🎛️ USER INPUTS
# -------------------------------------------------
city = st.selectbox("Select a city", list(CITIES.keys()))
hours = st.slider("Hours to display", 6, 48, 24)

lat, lon = CITIES[city]

# -------------------------------------------------
# 🌐 FETCH WEATHER DATA
# -------------------------------------------------
@st.cache_data(ttl=600)
def fetch_forecast(latitude, longitude):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&hourly=temperature_2m,windspeed_10m"
        "&timezone=auto"
    )

    response = requests.get(
        url,
        timeout=10,
        verify=False  # 🚨 SSL IGNORE (fixes your error)
    )

    response.raise_for_status()
    return response.json()

# -------------------------------------------------
# ⬇️ DATA LOAD WITH SAFETY
# -------------------------------------------------
with st.spinner(f"Fetching weather for {city}..."):
    try:
        data = fetch_forecast(lat, lon)
    except Exception as e:
        st.error(f"Failed to fetch weather data:\n{e}")
        st.stop()

# 🚨 HARD STOP IF DATA IS BAD
if not data or "hourly" not in data:
    st.error("Weather data is unavailable or malformed.")
    st.stop()

# -------------------------------------------------
# 📊 DATAFRAME
# -------------------------------------------------
df = pd.DataFrame({
    "Time": data["hourly"]["time"][:hours],
    "Temperature (°C)": data["hourly"]["temperature_2m"][:hours],
    "Wind Speed (km/h)": data["hourly"]["windspeed_10m"][:hours],
})

df["Time"] = pd.to_datetime(df["Time"])

# -------------------------------------------------
# 📈 CHART
# -------------------------------------------------
fig = px.line(
    df,
    x="Time",
    y=["Temperature (°C)", "Wind Speed (km/h)"],
    title=f"Hourly Forecast for {city}"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# 📋 TABLE
# -------------------------------------------------
with st.expander("View raw data"):
    st.dataframe(df, use_container_width=True)

# -------------------------------------------------
# 👣 FOOTER
# -------------------------------------------------
st.caption("• Created by Rinku Bhat ")
