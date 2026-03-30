import streamlit as st
import json
import os
import requests
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium
import polyline
from folium.plugins import AntPath
import pandas as pd
from io import BytesIO

# ================================================================
# ✅ CITY LIST (SEARCHABLE AUTOCOMPLETE)
# ================================================================
CITIES = [
    "Mumbai","Navi Mumbai","Thane","Delhi","New Delhi","Noida","Gurugram",
    "Faridabad","Ghaziabad","Bangalore","Bengaluru","Chennai","Hyderabad",
    "Pune","Jaipur","Ahmedabad","Surat","Vadodara","Rajkot","Udaipur",
    "Jodhpur","Ajmer","Kolkata","Howrah","Durgapur","Asansol",
    "Kochi","Ernakulam","Thiruvananthapuram","Coimbatore","Madurai",
    "Trichy","Salem","Vijayawada","Visakhapatnam","Guntur",
    "Indore","Bhopal","Raipur","Bilaspur","Nagpur","Nashik",
    "Kolhapur","Aurangabad","Amritsar","Ludhiana","Chandigarh"
]

# ================================================================
# ✅ GEOCODING (CITY OR PINCODE)
# ================================================================
geolocator = Nominatim(user_agent="transitrack_geocoder")

@st.cache_data
def geocode_location(value: str):
    try:
        value = value.strip()
        loc = geolocator.geocode(f"{value}, India")
        if loc:
            return (loc.latitude, loc.longitude)
    except:
        pass
    return None

# ================================================================
# ✅ OSRM ROUTING (REAL ROAD POLYLINE)
# ================================================================
def osrm_route(c1, c2):
    lat1, lon1 = c1
    lat2, lon2 = c2
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=polyline"
    )
    r = requests.get(url).json()
    if "routes" not in r:
        return None, None

    distance_km = round(r["routes"][0]["distance"] / 1000, 2)
    coords = polyline.decode(r["routes"][0]["geometry"])
    return distance_km, coords

# ================================================================
# ✅ TRANSIT DAYS
# ================================================================
def transit_days(km):
    return round(km / 200, 1)

# ================================================================
# ✅ HISTORY
# ================================================================
HFILE = "history.json"

def load_history():
    return json.load(open(HFILE)) if os.path.exists(HFILE) else []

def save_history(h):
    json.dump(h, open(HFILE, "w"), indent=2)

# ================================================================
# ✅ UI STYLING
# ================================================================
st.markdown("""
<style>
.stApp { background:#111; color:white; font-family:'Segoe UI'; }
.hero { text-align:center; padding:40px; }
.hero-title { font-size:52px; font-weight:900; }
.hero-sub { color:#ff6a3d; font-size:22px; }
input { border:2px solid #ff6a3d !important; border-radius:6px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-title">TransiTrack</div>
  <div class="hero-sub">Distance • Routes • Intelligence</div>
</div>
""", unsafe_allow_html=True)

# ================================================================
# ✅ TABS
# ================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📍 Route & Map","📅 Transit Days","📁 Excel Upload","📜 History","🎮 Tetris"]
)

# ================================================================
# ✅ TAB 1 — ROUTE + ANIMATED MAP
# ================================================================
with tab1:
    st.subheader("Route Finder")

    col1, col2 = st.columns(2)

    with col1:
        origin = st.text_input(
            "From (City or Pincode)",
            placeholder="e.g. Mumbai or 400069",
            key="origin_input"
        )

    with col2:
        destination = st.text_input(
            "To (City or Pincode)",
            placeholder="e.g. Jaipur or 302039",
            key="destination_input"
        )

    # --------------------------------------------------
    # 1️⃣ CALCULATION (ONLY ON BUTTON CLICK)
    # --------------------------------------------------
    if st.button("Calculate Route", key="calc_route_btn"):

        if not origin or not destination:
            st.error("Please enter both origin and destination.")
            st.stop()

        c1 = geocode_location(origin)
        c2 = geocode_location(destination)

        if not c1:
            st.error(f"Unable to locate: {origin}")
            st.stop()
        if not c2:
            st.error(f"Unable to locate: {destination}")
            st.stop()

        dist, route = osrm_route(c1, c2)

        if not route:
            st.error("Unable to calculate road route.")
            st.stop()

        # ✅ STORE RESULT (CRITICAL)
        st.session_state["route_result"] = {
            "origin": origin,
            "destination": destination,
            "distance": dist,
            "route": route,
            "c1": c1,
            "c2": c2,
        }

    # --------------------------------------------------
    # 2️⃣ DISPLAY (PERSISTS ACROSS RERUNS)
    # --------------------------------------------------
    if "route_result" in st.session_state:
        result = st.session_state["route_result"]

        st.success(
            f"Distance: **{result['origin']} → {result['destination']} = {result['distance']} km**"
        )

        route = result["route"]
        (lat1, lon1), (lat2, lon2) = result["c1"], result["c2"]

        m = folium.Map(
            location=route[len(route)//2],
            zoom_start=6
        )

        folium.Marker(
            route[0],
            popup=f"From: {result['origin']}",
            icon=folium.Icon(color="green")
        ).add_to(m)

        folium.Marker(
            route[-1],
            popup=f"To: {result['destination']}",
            icon=folium.Icon(color="red")
        ).add_to(m)

        folium.PolyLine(
            route,
            color="orange",
            weight=4
        ).add_to(m)

        AntPath(
            route,
            color="#00FFFF",
            pulse_color="#00FF88"
        ).add_to(m)

        st.markdown("### 🗺️ Interactive Route Map")
        st_folium(m, width=800, height=550)

# ================================================================
# ✅ TAB 2 — TRANSIT DAYS
# ================================================================
with tab2:
    st.subheader("Transit Days Estimator")

    a = st.text_input("From (City or Pincode)")
    b = st.text_input("To (City or Pincode)")

    if st.button("Calculate Transit Days"):
        c1 = geocode_location(a)
        c2 = geocode_location(b)
        if not c1 or not c2:
            st.error("Geocoding failed.")
            st.stop()

        d,_ = osrm_route(c1,c2)
        st.success(f"Estimated Transit: **{transit_days(d)} days**")

# ================================================================
# ✅ TAB 3 — EXCEL UPLOAD (ROBUST NORMALIZATION)
# ================================================================
with tab3:
    st.subheader("📁 Bulk Distance via Excel")

    st.markdown("""
    **Expected Excel format:**

    | From | To |
    |------|----|
    | 400069 | Jaipur |
    | Mumbai | 302039 |

    ✅ Column names are case‑insensitive  
    ✅ Spaces around names are ignored  
    """)

    uploaded_file = st.file_uploader(
        "Upload Excel file (.xlsx)",
        type=["xlsx"],
        key="excel_uploader"
    )

    # ----------------------------------------------------
    # 1️⃣ PROCESS FILE (ON UPLOAD)
    # ----------------------------------------------------
    if uploaded_file is not None:

        df = pd.read_excel(uploaded_file)

        # ✅ Normalize column headers
        df.columns = (
            df.columns
            .astype(str)
            .str.replace(r"\s+", "", regex=True)
            .str.replace("\u00A0", "", regex=False)
            .str.lower()
        )

        if "from" not in df.columns or "to" not in df.columns:
            st.error("Excel must contain 'From' and 'To' columns.")
            st.stop()

        distances = []

        with st.spinner("Calculating distances…"):
            for _, row in df.iterrows():
                src = str(row["from"]).strip()
                dst = str(row["to"]).strip()

                c1 = geocode_location(src)
                c2 = geocode_location(dst)

                if not c1 or not c2:
                    distances.append("Location Error")
                    continue

                dist, _ = osrm_route(c1, c2)
                distances.append(dist if dist else "Route Error")

        df["Distance_KM"] = distances

        # ✅ Create Excel in‑memory and STORE in session_state
        output_buffer = BytesIO()
        df.to_excel(output_buffer, index=False, engine="openpyxl")
        output_buffer.seek(0)

        st.session_state["excel_output"] = output_buffer

        st.success("✅ Distances calculated successfully.")

    # ----------------------------------------------------
    # 2️⃣ DOWNLOAD BUTTON (PERSISTENT)
    # ----------------------------------------------------
    if "excel_output" in st.session_state:
        st.download_button(
            label="⬇️ Download Output Excel",
            data=st.session_state["excel_output"],
            file_name="TransiTrack_Distances.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
``
# ================================================================
# ✅ TAB 4 — HISTORY
# ================================================================
with tab4:
    hist = load_history()
    if hist:
        for h in hist:
            st.write(f"{h['from']} → {h['to']} = {h['distance']} km")
    else:
        st.info("No history yet.")

# ✅ TAB 5 — Pacman
# ================================================================
with tab5:
    st.subheader("🎮 Play Pacman")
    st.components.v1.iframe("https://bobzgames.github.io/GBA/launcher.html#pmc", height=650)

# FOOTER
st.markdown("""
<div class="footer">Created by <strong>Vishal Ramchandani</strong></div>
""", unsafe_allow_html=True)
