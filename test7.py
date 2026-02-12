import streamlit as st
import pandas as pd
import numpy as np

from meteostat import Point
try:
    from meteostat.hourly import Hourly
except ModuleNotFoundError:
    from meteostat import Hourly

from datetime import datetime, timedelta
import plotly.express as px
from scoring import calculate_wind_chill, cold_impact_score
from streamlit_autorefresh import st_autorefresh


# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(layout="wide")

# Auto refresh every 5 minutes
st_autorefresh(interval=300000, key="refresh")

# --------------------------------------------------
# GLASSMORPHISM + THEME
# --------------------------------------------------
theme = st.sidebar.selectbox("Theme", ["Dark", "Light"])

if theme == "Dark":
    bg = "#0e1117"
    text = "white"
else:
    bg = "#f5f7fa"
    text = "black"

st.markdown(f"""
<style>
body {{
    background-color: {bg};
    color: {text};
}}
.glass {{
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(14px);
    border-radius: 15px;
    padding: 20px;
}}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# CITY SELECTION
# --------------------------------------------------
cities = {
    "New York": (40.7128, -74.0060),
    "Chicago": (41.8781, -87.6298),
    "Toronto": (43.65107, -79.347015),
    "Denver": (39.7392, -104.9903),
    "Oslo": (59.9139, 10.7522),
}

selected = st.sidebar.multiselect("Select Cities", list(cities.keys()), default=["New York"])

# --------------------------------------------------
# DATA FETCH (NO API KEY)
# --------------------------------------------------
@st.cache_data(ttl=300)
def load_city_data(lat, lon):
    location = Point(lat, lon)
    end = datetime.now()
    start = end - timedelta(hours=24)

    data = Hourly(location, start, end)
    df = data.fetch()

    df = df.reset_index()
    df = df[["time", "temp", "wspd", "rhum"]]
    df.columns = ["datetime", "temperature", "wind_speed", "humidity"]

    return df

# --------------------------------------------------
# MAIN DASHBOARD
# --------------------------------------------------
if selected:
    all_data = []

    for city in selected:
        lat, lon = cities[city]
        df = load_city_data(lat, lon)

        df["city"] = city
        df["wind_chill"] = df.apply(
            lambda x: calculate_wind_chill(x.temperature, x.wind_speed),
            axis=1
        )
        df["impact_score"] = df.apply(
            lambda x: cold_impact_score(x.temperature, x.wind_speed, x.humidity),
            axis=1
        )

        all_data.append(df)

    final_df = pd.concat(all_data)

    st.title("🌍 Live Multi-City Cold Intelligence Dashboard")

    # ---------------------------------------
    # HOURLY ANIMATION
    # ---------------------------------------
    fig = px.line(
        final_df,
        x="datetime",
        y="wind_chill",
        color="city",
        render_mode="webgl",
        title="Hourly Wind Chill (Last 24 Hours)"
    )

    fig.update_layout(template="plotly_dark" if theme=="Dark" else "plotly_white")

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------
    # RANKING BOARD
    # ---------------------------------------
    latest = final_df.sort_values("datetime").groupby("city").tail(1)
    ranked = latest.sort_values("wind_chill")

    st.subheader("🏆 Cold Severity Ranking")

    cols = st.columns(len(ranked))

    for i, (_, row) in enumerate(ranked.iterrows()):
        color = "#2563eb"
        if row.wind_chill < -15:
            color = "#b91c1c"
        elif row.wind_chill < -5:
            color = "#f97316"

        cols[i].markdown(f"""
        <div style="background:{color};
                    padding:20px;
                    border-radius:15px;
                    text-align:center;
                    color:white;
                    font-size:20px;">
        #{i+1}<br>
        {row.city}<br>
        {row.wind_chill:.1f}°C
        </div>
        """, unsafe_allow_html=True)

    # ---------------------------------------
    # ALERTS
    # ---------------------------------------
    alerts = ranked[ranked.wind_chill < -15]

    if not alerts.empty:
        st.error("🚨 EXTREME COLD ALERT ACTIVE")

    # ---------------------------------------
    # RAW DATA
    # ---------------------------------------
    st.subheader("Detailed Data")
    st.dataframe(final_df)

else:
    st.warning("Select at least one city.")
