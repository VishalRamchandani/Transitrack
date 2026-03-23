import streamlit as st
import json
import os
import requests
from geopy.geocoders import Nominatim


# ---------------------------------------------------------
#                  GLOBAL CSS STYLING
# ---------------------------------------------------------
st.markdown("""
<style>

.stApp {
    background-color: #111111;
    color: white;
    font-family: "Segoe UI", sans-serif;
}

/* HERO */
.hero {
    text-align: center;
    padding: 60px 40px 30px;
}

.hero-title {
    font-size: 60px;
    font-weight: 900;
    color: white;
}

.hero-subtitle {
    color: #ff6a3d;
    font-size: 24px;
    font-weight: 600;
}

.hero-desc {
    color: #bbbbbb;
    font-size: 20px;
    max-width: 700px;
    margin: 20px auto;
}

/* Input fields */
input {
    border: 2px solid #ff6a3d !important;
    border-radius: 6px !important;
}

/* Footer */
.footer {
    text-align: center;
    padding: 20px;
    color: white;
    margin-top: 40px;
    border-top: 1px solid #222;
}

</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
#                HERO SECTION
# ---------------------------------------------------------
st.markdown("""
<div class="hero">
    <div class="hero-title">TransiTrack</div>
    <div class="hero-subtitle">Smarter Routes. Faster Decisions. Powered by Intelligence.</div>
    <div class="hero-desc">
        Unified tools for distance analytics, transit planning, and real‑time logistics intelligence.
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
#                  CORE FUNCTIONS
# ---------------------------------------------------------
geolocator = Nominatim(user_agent="transitrack")

def get_coords(pin):
    try:
        obj = geolocator.geocode(f"{pin}, India")
        return (obj.latitude, obj.longitude) if obj else None
    except:
        return None


def driving_distance(c1, c2):
    lat1, lon1 = c1
    lat2, lon2 = c2
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    try:
        r = requests.get(url).json()
        return round(r["routes"][0]["distance"] / 1000, 2) if "routes" in r else None
    except:
        return None


def eway_transit_days(dist):
    return round(dist / 200, 1)


HFILE = "history.json"

def load_history():
    return json.load(open(HFILE)) if os.path.exists(HFILE) else []

def save_history(h):
    json.dump(h, open(HFILE, "w"), indent=4)


# ---------------------------------------------------------
#                MAIN TABS
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📍 Driving Distance",
    "📅 Transit Days",
    "🎮 Pacman",
    "📜 History"
])


# ---------------------------------------------------------
#  TAB 1 — DRIVING DISTANCE
# ---------------------------------------------------------
with tab1:
    st.subheader("Driving Distance")
    a = st.text_input("Origin Pincode", placeholder="Enter origin pincode...", key="dd1")
    b = st.text_input("Destination Pincode", placeholder="Enter destination pincode...", key="dd2")

    if st.button("Calculate Distance", key="dd_btn"):
        if a.isdigit() and b.isdigit():
            c1 = get_coords(a)
            c2 = get_coords(b)
            if c1 and c2:
                d = driving_distance(c1, c2)
                if d:
                    st.success(f"{a} → {b} = {d} km")

                    hist = load_history()
                    hist.append({"from": a, "to": b, "distance": d})
                    save_history(hist)
                else:
                    st.error("Route not found.")
            else:
                st.error("Invalid pincode.")
        else:
            st.error("Numeric pincodes only.")


# ---------------------------------------------------------
#  TAB 2 — TRANSIT DAYS
# ---------------------------------------------------------
with tab2:
    st.subheader("Transit Days (E-Way Bill Estimate)")
    o = st.text_input("Origin Pincode", placeholder="Enter origin pincode...", key="td1")
    p = st.text_input("Destination Pincode", placeholder="Enter destination pincode...", key="td2")

    if st.button("Calculate Transit", key="td_btn"):
        if o.isdigit() and p.isdigit():
            c1 = get_coords(o)
            c2 = get_coords(p)
            if c1 and c2:
                d = driving_distance(c1, c2)
                if d:
                    days = eway_transit_days(d)
                    st.success(f"Transit Days: {days} days\nDistance: {d} km")
                else:
                    st.error("No distance available.")
            else:
                st.error("Invalid pincodes.")
        else:
            st.error("Enter numeric pincodes only.")


# ---------------------------------------------------------
#  TAB 3 — TETRIS GAME
# ---------------------------------------------------------
with tab3:
    st.subheader("🎮 Play Pacman")
    st.write("Modern HTML5 Pacman, playable directly in your browser.")
    st.components.v1.iframe("https://bobzgames.github.io/GBA/launcher.html#pmc", height=650)


# ---------------------------------------------------------
#  TAB 4 — HISTORY
# ---------------------------------------------------------
with tab4:
    st.subheader("Search History")
    hist = load_history()
    if hist:
        for h in hist:
            st.write(f"🔸 {h['from']} → {h['to']} = {h['distance']} km")
    else:
        st.info("No history yet.")

    if st.button("Clear History"):
        save_history([])
        st.success("History cleared.")


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.markdown("""
<div class="footer">
Created by <strong>Vishal Ramchandani</strong>
</div>
""", unsafe_allow_html=True)
