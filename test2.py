import math
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import smtplib
from email.message import EmailMessage

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="❄ Norway Wind Chill Dashboard",
    page_icon="❄",
    layout="wide"
)

# -------------------------------------------------
# Wind chill formula
# -------------------------------------------------
def wind_chill(temp_c, wind_kmh):
    if temp_c > 10 or wind_kmh < 4.8:
        return temp_c
    v = wind_kmh ** 0.16
    return 13.12 + 0.6215 * temp_c - 11.37 * v + 0.3965 * temp_c * v

# -------------------------------------------------
# Norwegian cities
# -------------------------------------------------
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


# -------------------------------------------------
# Sidebar: Settings
# -------------------------------------------------
st.sidebar.header("⚙️ Settings")
st.sidebar.subheader("City selection")
multi_cities = st.sidebar.multiselect("Select cities to compare", sorted(CITIES.keys()), default=["Oslo"])
hours = st.sidebar.slider("Forecast hours", 12, 72, 24)
refresh = st.sidebar.slider("Auto-refresh (seconds)", 30, 600, 120)
alert_threshold = st.sidebar.number_input("Wind chill alert threshold (°C)", value=-20)

st_autorefresh(interval=refresh*1000, key="refresh")

st.title("❄ Norway Wind Chill Dashboard")
st.caption("Multi-city live forecast with wind chill, map, and alerts")

# -------------------------------------------------
# Fetch forecast
# -------------------------------------------------
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

# Store dataframes for all cities
city_dfs = {}
extreme_cities = []

for city in multi_cities:
    lat, lon = CITIES[city]
    lat = float(lat)
    lon = float(lon)
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

# -------------------------------------------------
# Multi-city comparison chart
# -------------------------------------------------
# Multi-city comparison chart (Temperature + Wind Chill)
if city_dfs:
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
    
    fig = px.line(
        compare_df,
        x="Time",
        y=compare_df.columns[1:],  # all temperature + wind chill columns
        labels={"value": "°C", "variable": "Metric"},
        title="Multi-city Temperature & Wind Chill Comparison"
    )
    st.plotly_chart(fig, use_container_width=True)


# -------------------------------------------------
# Map visualization
# -------------------------------------------------
st.subheader("🗺️ City Map")
map_data = pd.DataFrame([
    {"City": city, "lat": CITIES[city][0], "lon": CITIES[city][1]} for city in multi_cities
])
st.map(map_data.rename(columns={"lat": "latitude", "lon": "longitude"}))

# -------------------------------------------------
# Display individual city data + CSV export
# -------------------------------------------------
for city, df in city_dfs.items():
    st.markdown(f"### {city} Forecast")
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"⬇️ Download CSV ({city})",
        data=csv,
        file_name=f"{city.lower().replace(' ','_')}_forecast.csv",
        mime="text/csv"
    )

# -------------------------------------------------
# Email alert
# -------------------------------------------------
if extreme_cities:
    st.error(f"❌ Extreme cold alert in: {', '.join(extreme_cities)}")
    send_email = st.checkbox("Send email alert?")
    if send_email:
        sender = st.text_input("Sender email")
        password = st.text_input("Email password", type="password")
        recipient = st.text_input("Recipient email")
        if sender and password and recipient:
            try:
                msg = EmailMessage()
                msg["Subject"] = "❄ Extreme Cold Alert!"
                msg["From"] = sender
                msg["To"] = recipient
                msg.set_content(f"Extreme cold detected in: {', '.join(extreme_cities)}")

                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                    smtp.login(sender, password)
                    smtp.send_message(msg)
                st.success("✅ Email sent successfully!")
            except Exception as e:
                st.error(f"Failed to send email: {e}")

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.caption("Data: Open-Meteo • Wind chill: Environment Canada • Map: Plotly/Streamlit")
