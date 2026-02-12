import time
import math
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="❄ Norway Wind Chill Pro Dashboard",
    layout="wide",
    page_icon="❄"
)

# -----------------------------
# Dr. FixIT Wind Chill Formula
# -----------------------------
def wind_chill(temp_c, wind_kmh):
    if temp_c > 10 or wind_kmh < 4.8:
        return temp_c
    v = wind_kmh ** 0.16
    return 13.12 + 0.6215*temp_c - 11.37*v + 0.3965*temp_c*v

# -----------------------------
# Cities (UPDATED FULL LIST)
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
    "Select cities",
    sorted(CITIES.keys()),
    default=["Oslo","Bergen","Trondheim","Stavanger","Kristiansand",
             "Drammen","Sandnes","Fredrikstad","Tromsø","Lillestrøm",
             "Sarpsborg","Skien","Sandefjord","Haugesund","Moss",
             "Porsgrunn","Bodø","Arendal","Hamar","Ålesund",
             "Mo i Rana","Narvik","Alta","Molde","Notodden",
             "Levanger","Namsos","Voss"]
)

hours = st.sidebar.slider("Forecast hours", 12, 72, 24)
refresh = st.sidebar.slider("Auto-refresh interval (sec)", 30, 600, 60)
speed = st.sidebar.slider("Animation speed (seconds per hour)", 0.2, 2.0, 0.5)
alert_threshold = st.sidebar.number_input("Extreme cold threshold (°C)", value=-20)

st_autorefresh(interval=refresh*1000, key="refresh")

# -----------------------------
# Session State for Pages
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

def go_to_page(page_name):
    st.session_state.page = page_name

# -----------------------------
# Hide Streamlit Branding + Add Custom Footer
# -----------------------------
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden;}

/* Custom Footer Bottom Right */
.custom-footer {
    position: fixed;
    bottom: 10px;
    right: 20px;
    font-size: 14px;
    color: #888;
    z-index: 100;
}
</style>
"""

# -----------------------------
# Fetch Forecast
# -----------------------------
@st.cache_data(ttl=900)
def fetch_forecast(lat, lon):
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           "&hourly=temperature_2m,windspeed_10m&timezone=auto")
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()

city_dfs = {}
for city in multi_cities:
    lat, lon = CITIES[city]
    try:
        data = fetch_forecast(lat, lon)
        df = pd.DataFrame({
            "Time": data["hourly"]["time"][:hours],
            "Temperature (°C)": data["hourly"]["temperature_2m"][:hours],
            "Wind Speed (km/h)": data["hourly"]["windspeed_10m"][:hours]
        })
        df["Wind Chill (°C)"] = df.apply(
            lambda r: wind_chill(r["Temperature (°C)"], r["Wind Speed (km/h)"]),
            axis=1
        )
        city_dfs[city] = df
    except Exception as e:
        st.error(f"Failed to fetch {city}: {e}")

# -----------------------------
# Home Page
# -----------------------------
if st.session_state.page == "Home":
    st.title("❄ Norway Wind Chill Dashboard – Home")
    
    if not multi_cities:
        st.info("Select cities in the sidebar to generate dashboard and leaderboard.")
    else:
        latest_hour = hours-1
        leaderboard_df = pd.DataFrame({
            "City": multi_cities,
            "Temperature (°C)": [city_dfs[c]["Temperature (°C)"].iloc[latest_hour] for c in multi_cities],
            "Wind Chill (°C)": [city_dfs[c]["Wind Chill (°C)"].iloc[latest_hour] for c in multi_cities]
        })
        leaderboard_df = leaderboard_df.sort_values(by="Wind Chill (°C)")

        st.subheader("🏆 Coldest Cities Leaderboard")
        st.dataframe(
            leaderboard_df.style
                .background_gradient(subset=["Wind Chill (°C)"], cmap="Blues_r")
                .format({"Temperature (°C)": "{:.1f}", "Wind Chill (°C)": "{:.1f}"}),
            use_container_width=True
        )

        st.markdown("**Quick Access Dashboards:**")
        col1, col2, col3, col4 = st.columns(4)
        col1.button("🌡️ Multi-city Comparison", on_click=go_to_page, args=("Multi-city",))
        col2.button("🗺️ City Map", on_click=go_to_page, args=("City Map",))
        col3.button("📊 Wind Chill Heatmap", on_click=go_to_page, args=("Heatmap",))
        col4.button("🌡️ Cold Meter", on_click=go_to_page, args=("Cold Meter",))
        st.markdown("---")

# -----------------------------
# Multi-page Dashboards
# -----------------------------
elif multi_cities and st.session_state.page in ["Multi-city","Heatmap","Cold Meter","City Map"]:
    placeholder_graph = st.empty()
    placeholder_heatmap = st.empty()
    placeholder_gauge = st.empty()
    placeholder_map = st.empty()
    placeholder_tables = st.empty()

    for hour_idx in range(hours):

        if st.session_state.page == "Multi-city":
            compare_df = pd.DataFrame()
            for city in multi_cities:
                df = city_dfs[city][["Time","Temperature (°C)","Wind Chill (°C)"]].iloc[:hour_idx+1]
                df = df.rename(columns={
                    "Temperature (°C)": f"{city} Temp",
                    "Wind Chill (°C)": f"{city} Wind Chill"
                })
                compare_df = df if compare_df.empty else compare_df.merge(df,on="Time")
            if not compare_df.empty:
                fig_graph = px.line(
                    compare_df,
                    x="Time",
                    y=compare_df.columns[1:],
                    labels={"value":"°C","variable":"Metric"},
                    title=f"Temperature & Wind Chill – Hour {hour_idx+1}"
                )
                placeholder_graph.plotly_chart(fig_graph, use_container_width=True)

        if st.session_state.page == "Heatmap":
            z = pd.DataFrame({
                city: city_dfs[city]["Wind Chill (°C)"].iloc[:hour_idx+1]
                for city in multi_cities
            })
            fig_heatmap = px.imshow(
                z.T,
                labels=dict(x="Hour",y="City",color="Wind Chill (°C)"),
                x=[f"H{h+1}" for h in range(hour_idx+1)],
                y=multi_cities,
                color_continuous_scale="RdBu_r",
                aspect="auto"
            )
            placeholder_heatmap.plotly_chart(fig_heatmap, use_container_width=True)

        if st.session_state.page == "Cold Meter":
            n = len(multi_cities)
            cols = 3
            rows = (n+cols-1)//cols
            fig_gauge = make_subplots(
                rows=rows,
                cols=cols,
                specs=[[{"type":"indicator"}]*cols]*rows,
                subplot_titles=multi_cities
            )

            for idx, city in enumerate(multi_cities):
                row = idx//cols + 1
                col = idx%cols + 1
                val = city_dfs[city]["Wind Chill (°C)"].iloc[hour_idx]
                color = '#0d3b66' if val<=-20 else '#3f88c5' if val<=0 else '#f4d35e'

                fig_gauge.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=val,
                    number={'suffix':'°C','font':{'size':18}},
                    gauge={
                        'axis': {'range':[-40,10]},
                        'bar': {'color':color},
                        'steps':[
                            {'range':[-40,-20],'color':'#0d3b66'},
                            {'range':[-20,0],'color':'#3f88c5'},
                            {'range':[0,10],'color':'#f4d35e'}
                        ],
                        'threshold': {
                            'line':{'color':"red",'width':4},
                            'value':alert_threshold
                        }
                    }
                ), row=row, col=col)

            fig_gauge.update_layout(height=250*rows, title_text=f"Cold Meter – Hour {hour_idx+1}")
            placeholder_gauge.plotly_chart(fig_gauge, use_container_width=True)

        if st.session_state.page == "City Map":
            frame_df = pd.DataFrame({
                "City": multi_cities,
                "Lat": [CITIES[c][0] for c in multi_cities],
                "Lon": [CITIES[c][1] for c in multi_cities],
                "Wind Chill": [city_dfs[c]["Wind Chill (°C)"].iloc[hour_idx] for c in multi_cities]
            })

            fig_map = go.Figure(go.Scattermapbox(
                lat=frame_df["Lat"],
                lon=frame_df["Lon"],
                mode="markers+text",
                marker=dict(
                    size=16,
                    color=frame_df["Wind Chill"],
                    colorscale="RdBu_r",
                    cmin=-40,
                    cmax=10,
                    colorbar=dict(title="Wind Chill °C")
                ),
                text=frame_df["City"],
                textposition="top center"
            ))

            fig_map.update_layout(
                mapbox_style="carto-positron",
                mapbox_zoom=4.5,
                mapbox_center={"lat":60,"lon":10},
                height=400
            )

            placeholder_map.plotly_chart(fig_map, use_container_width=True)

        with placeholder_tables.container():
            st.subheader(f"📊 Forecast Tables – Hour {hour_idx+1}")
            for city in multi_cities:
                df = city_dfs[city].iloc[:hour_idx+1].copy()
                with st.expander(f"{city} Forecast (First {hour_idx+1} hours)"):
                    df_style = df.style.applymap(
                        lambda x: "background-color:red;color:white;"
                        if isinstance(x,float) and x<=alert_threshold else "",
                        subset=["Wind Chill (°C)"]
                    )
                    st.dataframe(df_style, use_container_width=True)

        time.sleep(speed)

    st.button("⬅️ Back to Home", on_click=lambda: go_to_page("Home"))

else:
    st.info("Select at least one city to generate the dashboards.")
