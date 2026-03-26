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
        from_type = st.selectbox("From Type",["Pincode","City"])
        origin = st.text_input("From (Pincode)") if from_type=="Pincode" else st.selectbox("From City",CITIES)

    with col2:
        to_type = st.selectbox("To Type",["Pincode","City"])
        destination = st.text_input("To (Pincode)") if to_type=="Pincode" else st.selectbox("To City",CITIES)

    if st.button("Calculate Route"):
        c1 = geocode_location(origin)
        c2 = geocode_location(destination)

        if not c1 or not c2:
            st.error("Unable to locate origin or destination.")
            st.stop()

        dist, route = osrm_route(c1,c2)
        if not route:
            st.error("Routing failed.")
            st.stop()

        st.session_state["route"] = route
        st.session_state["distance"] = dist
        st.session_state["origin"] = origin
        st.session_state["destination"] = destination
        st.session_state["coords"] = (c1,c2)

        hist = load_history()
        hist.append({"from":origin,"to":destination,"distance":dist})
        save_history(hist)

    if "route" in st.session_state:
        st.success(f"Distance: **{st.session_state['distance']} km**")

        route = st.session_state["route"]
        (lat1,lon1),(lat2,lon2) = st.session_state["coords"]

        m = folium.Map(location=route[len(route)//2], zoom_start=6)

        folium.Marker(route[0],popup=f"From: {st.session_state['origin']}",
                      icon=folium.Icon(color="green")).add_to(m)
        folium.Marker(route[-1],popup=f"To: {st.session_state['destination']}",
                      icon=folium.Icon(color="red")).add_to(m)

        folium.PolyLine(route,color="orange",weight=4).add_to(m)
        AntPath(route,color="#00FFFF",pulse_color="#00FF88").add_to(m)

        st_folium(m,width=800,height=550)

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
    st.subheader("Bulk Distance via Excel")

    st.markdown("""
    **Format:**
    - Column A: From
    - Column B: To  
    (spaces & case ignored)
    """)

    file = st.file_uploader("Upload Excel (.xlsx)",type=["xlsx"])
    if file:
        df = pd.read_excel(file)

        df.columns = (
            df.columns
            .str.replace(r"\s+","",regex=True)
            .str.replace(u"\u00A0","",regex=False)
            .str.lower()
        )

        if "from" not in df.columns or "to" not in df.columns:
            st.error("Headers must include From and To.")
            st.stop()

        out = []
        for _,r in df.iterrows():
            c1 = geocode_location(str(r["from"]))
            c2 = geocode_location(str(r["to"]))
            if not c1 or not c2:
                out.append("Error")
                continue
            d,_ = osrm_route(c1,c2)
            out.append(d)

        df["Distance_KM"] = out

        buff = BytesIO()
        df.to_excel(buff,index=False,engine="openpyxl")
        buff.seek(0)

        st.download_button(
            "⬇️ Download Excel",
            buff,
            "TransiTrack_Output.xlsx"
        )

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
