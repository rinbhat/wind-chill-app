import math
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="❄ Norway Wind Chill Dashboard",
    page_icon="❄",
    layout="wide"
)

# -----------------------------
# Wind chill formula
# -----------------------------
def wind_chill(temp_c, wind_kmh):
    if temp_c > 10 or wind_kmh < 4.8:
        return temp_c
    v = wind_kmh ** 0.16
    return 13.12 + 0.6215*temp_c - 11.37*v + 0.3965*temp_c*v

# -----------------------------
# Cities dictionary
# -----------------------------
CITIES = {
    "Oslo": (59.91, 10.75),
    "Bergen": (60.39, 5.32),
    "Trondheim": (63.43, 10.39),
    "Stavanger": (58.97, 5.73),
    "Kristiansand": (58.15, 7.995),
    "Drammen": (59.74, 10.20),
    "Sandnes": (58.85, 5.735),
    "Fredrikstad": (59.22, 10.93),
    "Tromsø": (69.65, 18.96),
    "Lillestrøm": (59.956, 11.049),
    "Sarpsborg": (59.284, 11.11),
    "Skien": (59.21, 9.61),
    "Sandefjord": (59.131, 10.216),
    "Haugesund": (59.414, 5.268),
    "Moss": (59.464, 10.659),
    "Porsgrunn": (59.139, 9.655),
    "Bodø": (67.282, 14.375),
    "Arendal": (58.462, 8.772),
    "Hamar": (60.795, 11.068),
    "Ålesund": (62.47, 6.15),
    "Mo i Rana": (66.312, 14.128),
    "Narvik": (68.438, 17.427),
    "Alta": (69.968, 23.271),
    "Molde": (62.737, 7.160),
    "Notodden": (59.558, 9.249),
    "Levanger": (63.744, 11.297),
    "Namsos": (64.472, 11.494),
    "Voss": (60.623, 6.419),
}

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("⚙️ Settings")
multi_cities = st.sidebar.multiselect(
    "Select cities to compare",
    sorted(CITIES.keys())
)
hours = st.sidebar.slider("Forecast hours", 12, 72, 24)
refresh = st.sidebar.slider("Auto-refresh (seconds)", 30, 600, 120)
alert_threshold = st.sidebar.number_input("Wind chill alert threshold (°C)", value=-20)

st_autorefresh(interval=refresh*1000, key="refresh")

st.title("❄ Norway Wind Chill Dashboard")
st.caption("Live multi-city forecast with wind chill, map, and cold-to-warm ranking")

# -----------------------------
# Check if cities are selected
# -----------------------------
if not multi_cities:
    st.warning("⚠️ Please select multiple cities to generate the dashboard")
    st.stop()

# -----------------------------
# Fetch forecast
# -----------------------------
@st.cache_data(ttl=900)
def fetch_forecast(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=temperature_2m,windspeed_10m"
        "&timezone=auto"
    )
    r = requests.get(url, timeout=15, verify=False)
    r.raise_for_status()
    return r.json()

city_dfs = {}
extreme_cities = []

for city in multi_cities:
    lat, lon = CITIES[city]
    try:
        data = fetch_forecast(lat, lon)
    except Exception as e:
        st.error(f"Failed to fetch data for {city}: {e}")
        continue

    df = pd.DataFrame({
        "Time": data["hourly"]["time"][:hours],
        "Temperature (°C)": data["hourly"]["temperature_2m"][:hours],
        "Wind Speed (km/h)": data["hourly"]["windspeed_10m"][:hours],
    })
    df["Wind Chill (°C)"] = df.apply(
        lambda r: wind_chill(r["Temperature (°C)"], r["Wind Speed (km/h)"]),
        axis=1
    )
    city_dfs[city] = df
    if df["Wind Chill (°C)"].min() <= alert_threshold:
        extreme_cities.append(city)

# -----------------------------
# Cold-to-Warm Dashboard
# -----------------------------
st.subheader("❄ Cities Ordered by Wind Chill")
summary = []
for city, df in city_dfs.items():
    summary.append({
        "City": city,
        "Temperature (°C)": df["Temperature (°C)"].iloc[0],
        "Wind Chill (°C)": df["Wind Chill (°C)"].iloc[0]
    })
summary_df = pd.DataFrame(summary)
# Sort by Wind Chill descending (warmest at top, coldest bottom)
summary_df = summary_df.sort_values("Wind Chill (°C)", ascending=False)

fig_summary = px.bar(
    summary_df,
    x="Wind Chill (°C)",
    y="City",
    orientation="h",
    color="Temperature (°C)",
    color_continuous_scale="RdBu_r",
    title="Cities from Warmest to Coldest (Wind Chill)",
    text="Wind Chill (°C)"
)
fig_summary.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig_summary, use_container_width=True)

# -----------------------------
# Multi-city comparison chart
# -----------------------------
st.subheader("📊 Multi-city Temperature & Wind Chill Comparison")
compare_df = pd.DataFrame()
for city, df in city_dfs.items():
    temp = df[["Time", "Temperature (°C)", "Wind Chill (°C)"]].copy()
    temp = temp.rename(columns={
        "Temperature (°C)": f"{city} Temp",
        "Wind Chill (°C)": f"{city} Wind Chill"
    })
    if compare_df.empty:
        compare_df = temp
    else:
        compare_df = compare_df.merge(temp, on="Time", how="outer")

# Highlight coldest cities in red
coldest_wind_chill = summary_df["Wind Chill (°C)"].min()
line_colors = []
for col in compare_df.columns[1:]:
    if "Wind Chill" in col:
        city_name = col.split(" ")[0]
        if city_name in summary_df[summary_df["Wind Chill (°C)"] == coldest_wind_chill]["City"].values:
            line_colors.append("red")
        else:
            line_colors.append(None)
    else:
        line_colors.append(None)

fig = px.line(
    compare_df,
    x="Time",
    y=compare_df.columns[1:],
    labels={"value": "°C", "variable": "Metric"},
    title="Multi-city Temperature & Wind Chill Comparison"
)
for i, color in enumerate(line_colors):
    if color:
        fig.data[i].line.color = color
st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Map visualization
# -----------------------------
st.subheader("🗺️ City Map")
map_data = pd.DataFrame([
    {"City": city, "lat": CITIES[city][0], "lon": CITIES[city][1]} for city in multi_cities
])
st.map(map_data.rename(columns={"lat":"latitude", "lon":"longitude"}))

# -----------------------------
# Collapsible forecast tables with color-coded wind chill
# -----------------------------
def color_wind_chill(val):
    if val <= alert_threshold:
        color = '#0d3b66'  # very cold - dark blue
    elif val <= 0:
        color = '#3f88c5'  # cold - medium blue
    else:
        color = '#f0f0f0'  # normal
    return f'background-color: {color}'

for city, df in city_dfs.items():
    with st.expander(f"📊 {city} Forecast (click to expand)"):
        st.dataframe(df.style.applymap(color_wind_chill, subset=["Wind Chill (°C)"]), use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"⬇️ Download CSV ({city})",
            data=csv,
            file_name=f"{city.lower().replace(' ','_')}_forecast.csv",
            mime="text/csv"
        )

# -----------------------------
# Alerts
# -----------------------------
if extreme_cities:
    st.error(f"❌ Extreme cold alert in: {', '.join(extreme_cities)}")

st.caption("Data: Open-Meteo • Wind chill: Environment Canada • Map: Plotly/Streamlit")
