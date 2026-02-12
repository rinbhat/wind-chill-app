import math
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
# Sidebar & Navigation
# -----------------------------
st.sidebar.header("⚙️ Settings")
page = st.sidebar.radio(
    "Navigate",
    ["Home", "Wind Chill Heatmap", "Cold Meter Dashboard", "City Map", "Forecast Tables"]
)
multi_cities = st.sidebar.multiselect(
    "Select cities",
    sorted(CITIES.keys()),
    default=["Oslo","Bergen"]
)
hours = st.sidebar.slider("Forecast hours", 12, 72, 24)
refresh = st.sidebar.slider("Auto-refresh (seconds)", 30, 600, 120)
alert_threshold = st.sidebar.number_input("Wind chill alert threshold (°C)", value=-20)

# Auto-refresh
st_autorefresh(interval=refresh*1000, key="refresh")

# -----------------------------
# Fetch forecast data
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
# Color function for tables
# -----------------------------
def color_wind_chill(val):
    if val <= alert_threshold:
        color = '#0d3b66'
        text_color = 'white'
    elif val <= 0:
        color = '#3f88c5'
        text_color = 'white'
    else:
        color = '#f4d35e'
        text_color = 'black'
    return f'background-color: {color}; color:{text_color}'

# -----------------------------
# Home Page
# -----------------------------
if page == "Home":
    st.title("🌡️ Norway Wind Chill Dashboard")
    st.subheader("Multi-city Temperature & Wind Chill Comparison")

    if not multi_cities:
        st.info("⚠️ Please select at least one city to see the comparison chart")
    else:
        compare_df = pd.DataFrame()
        for city in multi_cities:
            df = city_dfs[city]
            temp = df[["Time","Temperature (°C)","Wind Chill (°C)"]].copy()
            temp = temp.rename(columns={
                "Temperature (°C)": f"{city} Temp",
                "Wind Chill (°C)": f"{city} Wind Chill"
            })
            if compare_df.empty:
                compare_df = temp
            else:
                compare_df = compare_df.merge(temp, on="Time", how="outer")

        fig = px.line(
            compare_df,
            x="Time",
            y=compare_df.columns[1:],
            labels={"value":"°C","variable":"Metric"},
            title="Temperature & Wind Chill Comparison (all selected cities)"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Quick Access Dashboards")
    st.markdown("""
    - [Wind Chill Heatmap](#)
    - [Cold Meter Dashboard](#)
    - [City Map](#)
    - [Forecast Tables](#)
    """)

# -----------------------------
# Wind Chill Heatmap Dashboard with hourly animation
# -----------------------------
if page == "Wind Chill Heatmap":
    st.title("❄ Animated Wind Chill Heatmap")
    if not multi_cities:
        st.info("⚠️ Please select at least one city to generate heatmap")
    else:
        # prepare heatmap data for all hours
        z_data = []
        hover_text = []
        for hour_idx in range(hours):
            row_vals = []
            hover_row = []
            for city in multi_cities:
                row_vals.append(city_dfs[city]["Wind Chill (°C)"].iloc[hour_idx])
                hover_row.append(f"{city}<br>Wind Chill: {city_dfs[city]['Wind Chill (°C)'].iloc[hour_idx]:.1f}°C")
            z_data.append(row_vals)
            hover_text.append(hover_row)

        fig = go.Figure(
            data=go.Heatmap(
                z=z_data,
                x=multi_cities,
                y=[f"Hour {i+1}" for i in range(hours)],
                text=hover_text,
                hoverinfo="text",
                colorscale="RdBu_r",
                colorbar=dict(title="°C")
            )
        )
        fig.update_layout(height=500, title="Hourly Wind Chill Heatmap")
        st.plotly_chart(fig, use_container_width=True)
    st.button("⬅️ Back to Home", on_click=lambda: st.experimental_rerun())

# -----------------------------
# Cold Meter Dashboard with hourly animation
# -----------------------------
if page == "Cold Meter Dashboard":
    st.title("🌡️ Cold Meter Dashboard (Hourly)")

    if not multi_cities:
        st.info("⚠️ Please select at least one city to generate Cold Meter Dashboard")
    else:
        # for simplicity, show latest hour wind chill for each city in a clean grid
        n = len(multi_cities)
        cols = 2
        rows = (n + 1)//cols
        fig_gauge = make_subplots(
            rows=rows, cols=cols,
            specs=[[{"type":"indicator"}]*cols for _ in range(rows)],
            subplot_titles=multi_cities
        )
        for idx, city in enumerate(multi_cities):
            row = idx//cols + 1
            col = idx%cols + 1
            wind = city_dfs[city]["Wind Chill (°C)"].iloc[-1]  # last hour
            color = '#0d3b66' if wind <= -20 else '#3f88c5' if wind <= 0 else '#f4d35e'
            fig_gauge.add_trace(go.Indicator(
                mode="gauge+number+delta",
                value=wind,
                number={'suffix':'°C','font':{'size':20}},
                delta={'reference':0,'position':'top'},
                gauge={'axis':{'range':[-40,10]}, 'bar':{'color':color}},
                domain={'row':row-1,'column':col-1}
            ), row=row, col=col)
        fig_gauge.update_layout(height=250*rows, showlegend=False)
        st.plotly_chart(fig_gauge, use_container_width=True)
    st.button("⬅️ Back to Home", on_click=lambda: st.experimental_rerun())

# -----------------------------
# City Map
# -----------------------------
if page == "City Map":
    st.title("🗺️ City Map")
    if not multi_cities:
        st.info("⚠️ Please select at least one city to generate map")
    else:
        map_data = pd.DataFrame([
            {"City": city, "lat": CITIES[city][0], "lon": CITIES[city][1]} for city in multi_cities
        ])
        st.map(map_data.rename(columns={"lat":"latitude","lon":"longitude"}))
    st.button("⬅️ Back to Home", on_click=lambda: st.experimental_rerun())

# -----------------------------
# Forecast Tables
# -----------------------------
if page == "Forecast Tables":
    st.title("📊 Forecast Tables")
    if not multi_cities:
        st.info("⚠️ Please select cities to view forecast tables")
    else:
        for city, df in city_dfs.items():
            with st.expander(f"{city} Forecast"):
                st.dataframe(df.style.applymap(color_wind_chill, subset=["Wind Chill (°C)"]), use_container_width=True)
                st.download_button(f"Download CSV ({city})", df.to_csv(index=False).encode("utf-8"), file_name=f"{city}.csv")
    st.button("⬅️ Back to Home", on_click=lambda: st.experimental_rerun())

# -----------------------------
# Extreme Cold Alerts
# -----------------------------
if extreme_cities:
    st.error(f"❌ Extreme cold alert in: {', '.join(extreme_cities)}")

st.caption("Data: Open-Meteo • Wind chill: Environment Canada • Map: Plotly/Streamlit")
