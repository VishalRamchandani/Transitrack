import streamlit as st
import json
import os
import pandas as pd
import requests
import io

# ===============================================================
# ✅ LOAD FULL INDIA PINCODE DATASET (~19,300 pincodes)
# Source reference:
# Minimal India Pincode list with latitude & longitude:
# https://github.com/mrparveensharma/All-India-Pincode-list-with-latitude-and-longitude
#   [1](https://github.com/mrparveensharma/All-India-Pincode-list-with-latitude-and-longitude/blob/master/Minimal-India-Pincode-list-with-latitude-and-longitude.csv)
# Dataset documentation describing ~19,300 PIN codes:
#   [2](https://rdrr.io/github/harshvardhaniimi/IndiaPIN/man/IndiaPIN.html)[3](https://www.harsh17.in/indiapin/)
# ===============================================================

@st.cache_data
def load_pincode_data():
    url = "https://raw.githubusercontent.com/mrparveensharma/All-India-Pincode-list-with-latitude-and-longitude/master/Minimal-India-Pincode-list-with-latitude-and-longitude.csv"
    df = pd.read_csv(url)
    df = df.rename(columns={
        "Pincode": "pincode",
        "Latitude": "latitude",
        "Longitude": "longitude"
    })
    df["pincode"] = df["pincode"].astype(int)
    return df

df = load_pincode_data()


# ===============================================================
# ✅ GET COORDINATES FOR PINCODE
# ===============================================================
def get_coords(pincode):
    try:
        pin = int(pincode)
        row = df[df["pincode"] == pin]
        if not row.empty:
            return (row.iloc[0]["latitude"], row.iloc[0]["longitude"])
    except:
        pass
    return None


# ===============================================================
# ✅ DRIVING DISTANCE (OSRM — free, no key required)
# ===============================================================
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


# ===============================================================
# ✅ TRANSIT DAYS (E-WAY BILL STYLE)
# ===============================================================
def eway_transit_days(dist):
    return round(dist / 200, 1)


# ===============================================================
# ✅ HISTORY FUNCTIONS
# ===============================================================
HFILE = "history.json"

def load_hist():
    return json.load(open(HFILE)) if os.path.exists(HFILE) else []

def save_hist(h):
    json.dump(h, open(HFILE, "w"), indent=4)


# ===============================================================
# ✅ UI STYLE / HERO SECTION
# ===============================================================
st.markdown("""
<style>
.stApp {
    background-color:#111;
    color:white;
    font-family:'Segoe UI';
}
.hero {
    text-align:center;
    padding:50px 40px;
}
.hero-title { font-size:60px; font-weight:900; }
.hero-subtitle { color:#ff6a3d; font-size:24px; font-weight:600; }
.hero-desc { font-size:20px; color:#bbb; max-width:700px; margin:auto; }
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


# ===============================================================
# ✅ TABS
# ===============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📍 Driving Distance",
    "📅 Transit Days",
    "🎮 Pacman",
    "📜 History"
])


# ===============================================================
# ✅ TAB 1 — DRIVING DISTANCE
# ===============================================================
with tab1:
    st.subheader("Driving Distance")

    p1 = st.text_input("Origin Pincode", placeholder="Enter origin pincode...", key="d1")
    p2 = st.text_input("Destination Pincode", placeholder="Enter destination pincode...", key="d2")

    if st.button("Calculate Distance", key="dd_btn"):
        if p1.isdigit() and p2.isdigit():
            c1 = get_coords(p1)
            c2 = get_coords(p2)

            if c1 and c2:
                dist = driving_distance(c1, c2)
                if dist:
                    st.success(f"{p1} → {p2} = {dist} km")

                    hist = load_hist()
                    hist.append({"from": p1, "to": p2, "distance": dist})
                    save_hist(hist)
                else:
                    st.error("Unable to calculate driving route.")
            else:
                st.error("Invalid pincode.")
        else:
            st.error("Enter numeric pincodes only.")


# ===============================================================
# ✅ TAB 2 — TRANSIT DAYS
# ===============================================================
with tab2:
    st.subheader("Transit Days (E-Way Bill Estimate)")

    o = st.text_input("Origin Pincode", placeholder="Enter origin...", key="t1")
    p = st.text_input("Destination Pincode", placeholder="Enter destination...", key="t2")

    if st.button("Calculate Transit Days", key="t3"):
        if o.isdigit() and p.isdigit():
            c1 = get_coords(o)
            c2 = get_coords(p)
            if c1 and c2:
                dist = driving_distance(c1, c2)
                if dist:
                    days = eway_transit_days(dist)
                    st.success(f"Transit Days: {days} days\nDistance: {dist} km")
                else:
                    st.error("Unable to compute distance.")
            else:
                st.error("Invalid pincodes.")
        else:
            st.error("Use numeric pincodes only.")


# ===============================================================
# ✅ TAB 3 — GAME
# ===============================================================
with tab3:
    st.subheader("🎮 Play Pacman")
    st.components.v1.iframe("https://bobzgames.github.io/GBA/launcher.html#pmc", height=650)


# ===============================================================
# ✅ TAB 4 — HISTORY
# ===============================================================
with tab4:
    st.subheader("Distance History")

    hist = load_hist()

    if hist:
        for h in hist:
            st.write(f"🔸 {h['from']} → {h['to']} = {h['distance']} km")
    else:
        st.info("No history yet.")

    if st.button("Clear History", key="clr"):
        save_hist([])
        st.success("History cleared!")


# ===============================================================
# ✅ FOOTER
# ===============================================================
st.markdown("""
<div class="footer">
Created by <strong>Vishal Ramchandani</strong>
</div>
""", unsafe_allow_html=True)
