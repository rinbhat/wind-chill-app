# ❄ Norway Wind Chill Dashboard

A real-time **wind chill analytics dashboard** built with Streamlit, Plotly, and the Open-Meteo API.

The app fetches hourly weather forecasts (temperature and wind speed) and calculates wind chill to visualize cold exposure across major Norwegian cities using interactive charts, heatmaps, gauges, leaderboards, and a live map.

---

## 🌐 Overview

The **Norway Wind Chill Pro Dashboard** provides:

* Real-time forecast insights
* Multi-city comparison
* Advanced visual analytics
* Automatic data refresh
* Interactive exploration controls

Ideal for weather monitoring, data visualization demos, and Streamlit portfolio projects.

---

## ✨ Features

### 📊 Core Analytics

* Real-time wind chill calculation
* Hourly forecast up to 72 hours
* Multi-city comparison (default: Oslo & Stavanger)
* Extreme cold threshold alerts

### 📈 Visual Dashboards

* Animated comparison charts
* Coldest cities leaderboard
* Forecast heatmap animation
* Gauge-style cold meter
* Interactive Norway city map

### ⚙️ Interactivity

* City selection (multi-select)
* Forecast duration slider
* Auto-refresh interval control
* Animation speed control
* Extreme cold alert threshold

### 🧾 Data Tables

* Expandable forecast tables per city
* Conditional formatting for extreme cold values

---

## 🧮 Wind Chill Formula

```
WCI = 13.12 + 0.6215T − 11.37V^0.16 + 0.3965TV^0.16
```

Where:

* **T** = Temperature (°C)
* **V** = Wind speed (km/h)

If temperature > 10°C or wind speed < 4.8 km/h, wind chill equals actual temperature.

---

## 🗺 Supported Cities

Includes major Norwegian cities such as:

Oslo, Bergen, Trondheim, Stavanger, Tromsø, Kristiansand, Drammen, Sandnes, Ålesund, Bodø, Alta, Narvik, Molde, Haugesund, and more.

You can easily extend the list in the `CITIES` dictionary.

---

## 🧰 Tech Stack

* Python
* Streamlit
* Pandas
* Plotly
* Open-Meteo API
* Plotly Mapbox

---

## 📦 Installation

### 1️⃣ Clone the repository

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2️⃣ Create a virtual environment

```bash
python -m venv venv
```

Activate:

**Windows**

```bash
venv\Scripts\activate
```

**macOS / Linux**

```bash
source venv/bin/activate
```

### 3️⃣ Install dependencies

```bash
pip install streamlit pandas plotly requests certifi streamlit-autorefresh
```

---

## ▶️ Run the App

```bash
streamlit run app.py
```

Open in your browser:

```
http://localhost:8501
```

---

## ⚙️ Configuration

Sidebar controls allow you to adjust:

* Dashboard view
* Cities
* Forecast hours
* Auto-refresh interval
* Animation speed
* Extreme cold threshold

---

## 🔄 Data Source

Weather data is provided by the **Open-Meteo Forecast API**

* Free and no API key required
* Hourly forecast data
* Automatic timezone detection

https://open-meteo.com/

---

## 📁 Project Structure

```
project/
│
├── app.py
├── README.md
├── requirements.txt
└── assets/
```

---

## 🚀 Deployment

You can deploy the app on:

* Streamlit Community Cloud
* Docker
* Azure App Service
* AWS / GCP VM
* On-prem server

---

## 🧩 Future Enhancements

* Historical weather trends
* Extreme cold notifications
* Saved user locations
* Export to CSV/PDF
* Dark mode toggle
* Mobile layout optimization

---

## 👨‍💻 Author

Rinku Bhat

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## ⭐ Acknowledgements

* Open-Meteo for the weather API
* Streamlit for the dashboard framework
* Plotly for visualization tools
