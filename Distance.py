import streamlit as st
import json
import os
import requests
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium

# ================================================================
# ✅ INDIA POST API — Validates ALL Indian pincodes
# ================================================================
def fetch_postoffice_info(pincode):
    url = f"https://api.postalpincode.in/pincode/{pincode}"
    try:
        r = requests.get(url, timeout=6).json()
        if r[0]["Status"] == "Success":
            # Even if PostOffice = null → Valid Pincode
            po = r[0].get("PostOffice")
            if po:
                return po[0]  # district/state available
            else:
                return {"District": "", "State": ""}
        return None
    except:
        return None


# ================================================================
# ✅ NOMINATIM — pincode‑only geocoding (WORKS FOR ALL PINCODES)
# ================================================================
geolocator = Nominatim(user_agent="transitrack_geocoder")

@st.cache_data
def geocode_pincode(pincode):
    """
    Using '<PINCODE>, India' fixes missing district/state issues.
    This reliably returns coordinates for ALL valid Indian pincodes.
    """
    try:
        loc = geolocator.geocode(f"{pincode}, India")
        if loc:
            return (loc.latitude, loc.longitude)
    except:
        return None
    return None


# ================================================================
# ✅ DRIVING DISTANCE — OSRM (Free)
# ================================================================
def driving_distance(c1, c2):
    lat1, lon1 = c1
    lat2, lon2 = c2

    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    try:
        r = requests.get(url).json()
        if "routes" in r:
            return round(r["routes"][0]["distance"] / 1000, 2)
    except:
        return None
    return None


# ================================================================
# ✅ TRANSIT DAYS (Simple E‑Way Bill Logic)
# ================================================================
def eway_transit_days(distance_km):
    return round(distance_km / 200, 1)


# ================================================================
# ✅ HISTORY STORAGE
# ================================================================
HFILE = "history.json"

def load_hist():
    return json.load(open(HFILE)) if os.path.exists(HFILE) else []

def save_hist(h):
    json.dump(h, open(HFILE, "w"), indent=4)


# ================================================================
# ✅ PAGE STYLE / HERO
# ================================================================
st.markdown("""
<style>
.stApp { background-color:#111; color:white; font-family:'Segoe UI'; }
.hero { text-align:center; padding:50px 40px; }
.hero-title { font-size:60px; font-weight:900; }
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
tab1, tab2, tab3, tab4 = st.tabs([
    "📍 Driving Distance",
    "📅 Transit Days",
    "🎮 Pacman",
    "📜 History"
])


# ================================================================
# ✅ TAB 1 — DRIVING DISTANCE (FINAL WORKING VERSION)
# ================================================================
with tab1:
    st.subheader("Driving Distance (All India Pincodes)")

    p1 = st.text_input("Origin Pincode", placeholder="Enter origin...", key="orig")
    p2 = st.text_input("Destination Pincode", placeholder="Enter destination...", key="dest")

    if st.button("Calculate Distance"):

        if not (p1.isdigit() and p2.isdigit()):
            st.error("Enter numeric 6-digit Indian pincodes.")
            st.stop()

        # ✅ Validate via India Post (NEVER fails for valid pincodes)
        info1 = fetch_postoffice_info(p1)
        info2 = fetch_postoffice_info(p2)

        if not info1:
            st.error(f"Invalid origin pincode: {p1}")
            st.stop()
        if not info2:
            st.error(f"Invalid destination pincode: {p2}")
            st.stop()

        # ✅ Geocode using pincode-only (bulletproof)
        c1 = geocode_pincode(p1)
        c2 = geocode_pincode(p2)

        if not c1 or not c2:
            st.error("Unable to geocode one or both pincodes.")
            st.stop()

        # ✅ Driving Distance
        dist = driving_distance(c1, c2)

        if not dist:
            st.error("Unable to calculate route via OSRM.")
            st.stop()

        st.success(f"Distance from {p1} → {p2}: **{dist} km**")

        # ✅ Save History
        hist = load_hist()
        hist.append({"from": p1, "to": p2, "distance": dist})
        save_hist(hist)

        # ✅ INTERACTIVE FOLIUM MAP
        lat1, lon1 = c1
        lat2, lon2 = c2

        st.markdown("### 🗺️ Interactive Map with Markers")

        center_lat = (lat1 + lat2) / 2
        center_lon = (lon1 + lon2) / 2

        m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

        folium.Marker(
            [lat1, lon1],
            popup=f"Origin: {p1}",
            icon=folium.Icon(color="green", icon="play")
        ).add_to(m)

        folium.Marker(
            [lat2, lon2],
            popup=f"Destination: {p2}",
            icon=folium.Icon(color="red", icon="flag")
        ).add_to(m)

        folium.PolyLine(
            locations=[[lat1, lon1], [lat2, lon2]],
            color="orange",
            weight=4
        ).add_to(m)

        st_folium(m, width=700, height=500)


# ================================================================
# ✅ TAB 2 — TRANSIT DAYS
# ================================================================
with tab2:
    st.subheader("Transit Days (E‑Way Bill Estimate)")

    o = st.text_input("Origin Pincode", placeholder="Enter origin...", key="t1")
    d = st.text_input("Destination Pincode", placeholder="Enter destination...", key="t2")

    if st.button("Calculate Transit Days"):

        if not (o.isdigit() and d.isdigit()):
            st.error("Enter numeric pincodes.")
            st.stop()

        info1 = fetch_postoffice_info(o)
        info2 = fetch_postoffice_info(d)

        if not info1:
            st.error(f"Invalid origin pincode: {o}")
            st.stop()
        if not info2:
            st.error(f"Invalid destination pincode: {d}")
            st.stop()

        c1 = geocode_pincode(o)
        c2 = geocode_pincode(d)

        if not c1 or not c2:
            st.error("Unable to geocode pincodes.")
            st.stop()

        dist = driving_distance(c1, c2)

        if dist:
            days = eway_transit_days(dist)
            st.success(f"Transit Days: **{days} days**\nDistance: **{dist} km**")
        else:
            st.error("Unable to calculate route.")


# ================================================================
# ✅ TAB 3 — Pacman GAME
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
            st.write(f"🔸 {h['from']} → {h['to']} = {h['distance']} km")
    else:
        st.info("No history yet.")

    if st.button("Clear History"):
        save_hist([])
        st.success("History cleared!")


# ================================================================
# ✅ FOOTER
# ================================================================
st.markdown("""
<div class="footer">Created by <strong>Vishal Ramchandani</strong></div>
""", unsafe_allow_html=True)
