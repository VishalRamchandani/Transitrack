import streamlit as st
import json
import os
import requests
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium


# ================================================================
# ✅ GEOCODING — USE PINCODE ONLY (Works for ALL Indian pincodes)
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
# ✅ DRIVING DISTANCE — OSRM (free)
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
# ✅ TRANSIT DAYS — simple logic
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
# ✅ UI STYLING
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


# ✅ HERO SECTION
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
    "🎮 pacman",
    "📜 History"
])


# ================================================================
# ✅ TAB 1 — DRIVING DISTANCE + INTERACTIVE MAP
# ================================================================
with tab1:
    st.subheader("Driving Distance (All India Pincodes)")

    p1 = st.text_input("Origin Pincode", placeholder="Enter origin pincode...")
    p2 = st.text_input("Destination Pincode", placeholder="Enter destination pincode...")

    if st.button("Calculate Distance"):

        # ✅ SIMPLE VALIDATION
        if not (p1.isdigit() and len(p1) == 6):
            st.error("Invalid origin pincode format")
            st.stop()
        if not (p2.isdigit() and len(p2) == 6):
            st.error("Invalid destination pincode format")
            st.stop()

        # ✅ GEOCODE (reliable)
        c1 = geocode_pincode(p1)
        c2 = geocode_pincode(p2)

        if not c1:
            st.error(f"Unable to geocode origin pincode {p1}")
            st.stop()
        if not c2:
            st.error(f"Unable to geocode destination pincode {p2}")
            st.stop()

        # ✅ DISTANCE
        dist = driving_distance(c1, c2)
        if not dist:
            st.error("Unable to get OSRM driving distance.")
            st.stop()

        st.success(f"Distance from {p1} → {p2}: **{dist} km**")

        # ✅ RECORD HISTORY
        hist = load_hist()
        hist.append({"from": p1, "to": p2, "distance": dist})
        save_hist(hist)

        # ✅ FOLIUM MAP
        st.markdown("### 🗺️ Interactive Map")

        lat1, lon1 = c1
        lat2, lon2 = c2

        center_lat = (lat1 + lat2) / 2
        center_lon = (lon1 + lon2) / 2

        m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

        folium.Marker([lat1, lon1],
                      popup=f"Origin ({p1})",
                      icon=folium.Icon(color="green", icon="play")).add_to(m)

        folium.Marker([lat2, lon2],
                      popup=f"Destination ({p2})",
                      icon=folium.Icon(color="red", icon="flag")).add_to(m)

        folium.PolyLine([[lat1, lon1], [lat2, lon2]],
                        color="orange", weight=4).add_to(m)

        st_folium(m, width=700, height=500)


# ================================================================
# ✅ TAB 2 — TRANSIT DAYS
# ================================================================
with tab2:
    st.subheader("Transit Days (E‑Way Bill Estimate)")

    o = st.text_input("Origin Pincode", placeholder="Enter origin...")
    d = st.text_input("Destination Pincode", placeholder="Enter destination...")

    if st.button("Calculate Transit Days"):

        if not (o.isdigit() and len(o) == 6):
            st.error("Invalid origin pincode format")
            st.stop()
        if not (d.isdigit() and len(d) == 6):
            st.error("Invalid destination pincode format")
            st.stop()

        c1 = geocode_pincode(o)
        c2 = geocode_pincode(d)

        if not c1 or not c2:
            st.error("Unable to geocode pincode(s).")
            st.stop()

        dist = driving_distance(c1, c2)
        if dist:
            days = eway_transit_days(dist)
            st.success(f"Transit Days: **{days} days**\nDistance: **{dist} km**")
        else:
            st.error("OSRM routing failed.")


# ================================================================
# ✅ TAB 3 —Pacman GAME
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

# ✅ FOOTER
st.markdown("""
<div class="footer">Created by <strong>Vishal Ramchandani</strong></div>
""", unsafe_allow_html=True)
