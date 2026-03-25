import streamlit as st
import json
import os
import requests
import pandas as pd
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium
from io import BytesIO

# ================================================================
# ✅ GEOCODING — PINCODE ONLY (Reliable for ALL Indian pincodes)
# ================================================================
geolocator = Nominatim(user_agent="transitrack_geocoder")

@st.cache_data
def geocode_pincode(pincode):
    try:
        loc = geolocator.geocode(f"{pincode}, India")
        if loc:
            return (loc.latitude, loc.longitude)
    except:
        return None
    return None

# ================================================================
# ✅ DRIVING DISTANCE — OSRM
# ================================================================
def driving_distance(c1, c2):
    lat1, lon1 = c1
    lat2, lon2 = c2
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}?overview=false"
    )
    try:
        r = requests.get(url).json()
        if "routes" in r:
            return round(r["routes"][0]["distance"] / 1000, 2)
    except:
        return None
    return None

# ================================================================
# ✅ TRANSIT DAYS
# ================================================================
def eway_transit_days(distance_km):
    return round(distance_km / 200, 1)

# ================================================================
# ✅ HISTORY
# ================================================================
HFILE = "history.json"

def load_hist():
    return json.load(open(HFILE)) if os.path.exists(HFILE) else []

def save_hist(h):
    json.dump(h, open(HFILE, "w"), indent=4)

# ================================================================
# ✅ STYLE / HERO SECTION
# ================================================================
st.markdown("""
<style>
.stApp { background-color:#111; color:white; font-family:'Segoe UI'; }
.hero { text-align:center; padding:50px 40px; }
.hero-title { font-size:60px; font-weight:900; color:white; }
.hero-subtitle { color:#ff6a3d; font-size:24px; font-weight:600; }
.hero-desc { color:#bbb; font-size:20px; max-width:700px; margin:auto; }
input { border:2px solid #ff6a3d !important; border-radius:6px !important; }
.footer { text-align:center; padding:20px; margin-top:40px; border-top:1px solid #222; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="hero-title">TransiTrack</div>
    <div class="hero-subtitle">Smarter Routes. Faster Decisions. Powered by Intelligence.</div>
    <div class="hero-desc">
        Unified tools for distance analytics, transit planning, and real‑time logistics intelligence.
    </div>
</div>
""", unsafe_allow_html=True)

# ================================================================
# ✅ TABS
# ================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📍 Driving Distance",
    "📅 Transit Days",
    "🎮 Pacman",
    "📜 History",
    "📁 Excel Distance Upload"
])


# ================================================================
# ✅ TAB 1 — DRIVING DISTANCE
# ================================================================
import polyline
from folium.plugins import AntPath

with tab1:
    st.subheader("Driving Distance (All India Pincodes)")

    p1 = st.text_input("Origin Pincode", placeholder="Enter origin pincode...")
    p2 = st.text_input("Destination Pincode", placeholder="Enter destination pincode...")

    if st.button("Calculate Distance"):

        # Validate format
        if not (p1.isdigit() and len(p1) == 6):
            st.error("Invalid origin pincode format.")
            st.stop()

        if not (p2.isdigit() and len(p2) == 6):
            st.error("Invalid destination pincode format.")
            st.stop()

        # ✅ Geocode using PINCODE ONLY
        c1 = geocode_pincode(p1)
        c2 = geocode_pincode(p2)

        if not c1:
            st.error(f"Unable to geocode origin pincode: {p1}")
            st.stop()
        if not c2:
            st.error(f"Unable to geocode destination pincode: {p2}")
            st.stop()

        lat1, lon1 = c1
        lat2, lon2 = c2

        # ✅ OSRM CALL WITH GEOMETRY FOR ROUTE SHAPE
        osrm_url = (
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=polyline"
        )

        r = requests.get(osrm_url).json()

        if "routes" not in r:
            st.error("OSRM routing failed.")
            st.stop()

        distance_km = round(r["routes"][0]["distance"] / 1000, 2)
        encoded_poly = r["routes"][0]["geometry"]

        # ✅ Decode full driving route (actual road path)
        route_coords = polyline.decode(encoded_poly)

        # ✅ Save to session_state to prevent map disappearing
        st.session_state["p1"] = p1
        st.session_state["p2"] = p2
        st.session_state["distance"] = distance_km
        st.session_state["c1"] = c1
        st.session_state["c2"] = c2
        st.session_state["route"] = route_coords


    # ✅ DISPLAY MAP AFTER COMPUTATION
    if "distance" in st.session_state:

        p1 = st.session_state["p1"]
        p2 = st.session_state["p2"]
        distance_km = st.session_state["distance"]
        c1 = st.session_state["c1"]
        c2 = st.session_state["c2"]
        route_coords = st.session_state["route"]

        st.success(f"✅ Distance from {p1} → {p2}: **{distance_km} km**")

        lat1, lon1 = c1
        lat2, lon2 = c2

        # ✅ Center map
        center_lat = (lat1 + lat2) / 2
        center_lon = (lon1 + lon2) / 2

        # ✅ Build map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

        # ✅ Origin & Destination markers
        folium.Marker([lat1, lon1], popup=f"Origin ({p1})",
                      icon=folium.Icon(color="green", icon="play")).add_to(m)
        folium.Marker([lat2, lon2], popup=f"Destination ({p2})",
                      icon=folium.Icon(color="red", icon="flag")).add_to(m)

        # ✅ Actual route (OSRM polyline)
        folium.PolyLine(
            locations=route_coords,
            color="orange",
            weight=4,
            opacity=0.9
        ).add_to(m)

        # ✅ Animated Truck using AntPath
        AntPath(
            locations=route_coords,
            color="#00FFAA",
            delay=800,
            pulse_color="#00FFFF"
        ).add_to(m)

        st.markdown("### 🛣️ Interactive Route Map (Animated)")
        st_folium(m, width=750, height=550)


# ================================================================
# ✅ TAB 2 — TRANSIT DAYS
# ================================================================
with tab2:
    st.subheader("Transit Days Estimator")

    o = st.text_input("Origin Pincode", key="o1")
    d = st.text_input("Destination Pincode", key="o2")

    if st.button("Calculate Transit Days"):
        if not (o.isdigit() and len(o) == 6):
            st.error("Invalid origin pincode.")
            st.stop()
        if not (d.isdigit() and len(d) == 6):
            st.error("Invalid destination pincode.")
            st.stop()

        c1 = geocode_pincode(o)
        c2 = geocode_pincode(d)

        if not c1 or not c2:
            st.error("Geocoding failed.")
            st.stop()

        dist = driving_distance(c1, c2)
        if dist:
            days = eway_transit_days(dist)
            st.success(f"Transit Estimate: **{days} days** (Distance: {dist} km)")
        else:
            st.error("Unable to compute distance.")


# ================================================================
# ✅ TAB 3 — Pacman
# ================================================================
with tab3:
    st.subheader("🎮 Play Pacman")
    st.components.v1.iframe("https://bobzgames.github.io/GBA/launcher.html#pmc", height=650)


# ================================================================
# ✅ TAB 4 — HISTORY
# ================================================================
with tab4:
    st.subheader("Distance History")

    hist = load_hist()
    if hist:
        for h in hist:
            st.write(f"✅ {h['from']} → {h['to']} = {h['distance']} km")
    else:
        st.info("No history yet.")

    if st.button("Clear History"):
        save_hist([])
        st.success("History cleared!")


# ================================================================
# ✅ TAB 5 — EXCEL UPLOAD FEATURE
# ================================================================
with tab5:
    st.subheader("📁 Upload Excel to Calculate Multiple Distances")

    st.markdown("""
    **Excel Format Required:**
    
    | From | To |
    |------|-----|
    | 400069 | 421301 |
    | 302039 | 400001 |
    
    ✅ A1 = "From"  
    ✅ B1 = "To"  
    ✅ Output will be generated in Column C  
    """)

    file = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])

    if file:
        df = pd.read_excel(file)

        if "From" not in df.columns or "To" not in df.columns:
            st.error("Excel must contain 'From' and 'To' columns.")
            st.stop()

        out_distances = []

        for _, row in df.iterrows():
            a = str(row["From"])
            b = str(row["To"])

            if not (a.isdigit() and len(a) == 6 and b.isdigit() and len(b) == 6):
                out_distances.append("Invalid PIN")
                continue

            c1 = geocode_pincode(a)
            c2 = geocode_pincode(b)

            if not c1 or not c2:
                out_distances.append("Geo Error")
                continue

            dist = driving_distance(c1, c2)
            out_distances.append(dist if dist else "Route Err")

        df["Distance_KM"] = out_distances

        # ✅ Provide downloadable file
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)

        st.success("✅ Distance calculation completed.")

        st.download_button(
            label="⬇️ Download Updated Excel",
            data=output,
            file_name="TransiTrack_Distances.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# FOOTER
st.markdown("""
<div class="footer">Created by <strong>Vishal Ramchandani</strong></div>
""", unsafe_allow_html=True)
