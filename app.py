import streamlit as st
import pandas as pd
import joblib
import requests
import os
import sys
import time

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Krishi Konnect",
    page_icon="🌿",
    layout="wide"
)

# -----------------------------
# CUSTOM CSS
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #f4fff6 0%, #ffffff 40%, #f4fff6 100%);
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.hero {
    background: linear-gradient(90deg, #0f3d2e 0%, #1f7a4a 60%, #4cc26b 100%);
    padding: 28px;
    border-radius: 22px;
    color: white;
    box-shadow: 0px 8px 28px rgba(0,0,0,0.15);
}

.big-title {
    font-size: 52px;
    font-weight: 900;
    margin-bottom: -10px;
}

.sub-title {
    font-size: 18px;
    opacity: 0.92;
}

.card {
    background: white;
    padding: 18px;
    border-radius: 18px;
    border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0px 8px 22px rgba(0,0,0,0.06);
}

.result-card {
    background: linear-gradient(180deg, #ffffff 0%, #f0fff4 100%);
    padding: 18px;
    border-radius: 18px;
    border: 1px solid rgba(16, 185, 129, 0.25);
    box-shadow: 0px 8px 22px rgba(0,0,0,0.06);
    margin-bottom: 14px;
}

.crop-name {
    font-size: 26px;
    font-weight: 900;
    color: #0f3d2e;
}

.stButton button {
    background: linear-gradient(90deg, #0f3d2e 0%, #1f7a4a 60%, #4cc26b 100%);
    color: white;
    border-radius: 14px;
    border: none;
    padding: 12px 18px;
    font-weight: 800;
    font-size: 16px;
}
.stButton button:hover {
    opacity: 0.95;
    transform: scale(1.01);
}

section[data-testid="stSidebar"] {
    background: #f2fff5;
    border-right: 1px solid rgba(0,0,0,0.06);
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
st.markdown('<div class="hero">', unsafe_allow_html=True)
st.markdown('<div class="big-title">🌿 Krishi Konnect</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI crop advisory using Soil Health Card + NASA POWER climate signals</div>', unsafe_allow_html=True)
st.markdown("""
<p style="margin-top:14px; font-size:16px; opacity:0.95;">
Enter soil values from your Soil Health Card and select your state.  
We automatically fetch climate data and recommend the most suitable crops.
</p>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.write("")

# -----------------------------
# DEBUG (hidden in expander)
# -----------------------------
with st.expander("🔧 Debug info (for deployment)", expanded=False):
    st.write("Python:", sys.version)
    st.write("Files:", os.listdir())

# -----------------------------
# LOAD MODEL SAFELY
# -----------------------------
def load_artifacts():
    if not os.path.exists("crop_model.pkl"):
        st.error("❌ crop_model.pkl not found. Upload it to the Space files.")
        st.stop()

    if not os.path.exists("model_columns.pkl"):
        st.error("❌ model_columns.pkl not found. Upload it to the Space files.")
        st.stop()

    try:
        m = joblib.load("crop_model.pkl")
        c = joblib.load("model_columns.pkl")
        return m, c
    except Exception as e:
        st.error("❌ Model failed to load. This is usually a version mismatch.")
        st.write("Error:", str(e))
        st.stop()

model, cols = load_artifacts()

# -----------------------------
# STATE COORDS
# -----------------------------
state_coords = {
    "Punjab": (31.1471, 75.3412),
    "Haryana": (29.0588, 76.0856),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Maharashtra": (19.7515, 75.7139),
    "Bihar": (25.0961, 85.3131),
    "Rajasthan": (27.0238, 74.2179),
    "Gujarat": (22.2587, 71.1924),
    "Madhya Pradesh": (22.9734, 78.6569),
    "West Bengal": (22.9868, 87.8550),
    "Tamil Nadu": (11.1271, 78.6569),
    "Karnataka": (15.3173, 75.7139),
    "Telangana": (18.1124, 79.0193),
    "Andhra Pradesh": (15.9129, 79.7400),
    "Kerala": (10.8505, 76.2711),
    "Odisha": (20.9517, 85.0985),
    "Assam": (26.2006, 92.9376),
    "Chhattisgarh": (21.2787, 81.8661),
    "Jharkhand": (23.6102, 85.2799),
    "Uttarakhand": (30.0668, 79.0193),
    "Himachal Pradesh": (31.1048, 77.1734),
    "Jammu & Kashmir": (33.7782, 76.5762),
}

# -----------------------------
# NASA FETCH (ERROR SAFE)
# -----------------------------
def fetch_nasa_power(lat, lon):
    url = "https://power.larc.nasa.gov/api/temporal/climatology/point"
    params = {
        "parameters": "T2M_MAX,T2M_MIN,PRECTOTCORR,QV2M,WD10M,CLOUD_AMT,PS",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "format": "JSON"
    }

    try:
        r = requests.get(url, params=params, timeout=20)
        data = r.json()
        p = data["properties"]["parameter"]

        def avg_monthly(d):
            vals = list(d.values())
            return float(sum(vals) / len(vals))

        def sum_monthly(d):
            vals = list(d.values())
            return float(sum(vals))

        out = {}
        out["T2M_MAX"] = avg_monthly(p["T2M_MAX"])
        out["T2M_MIN"] = avg_monthly(p["T2M_MIN"])
        out["PRECTOTCORR"] = sum_monthly(p["PRECTOTCORR"])
        out["QV2M"] = avg_monthly(p["QV2M"])
        out["WD10M"] = avg_monthly(p["WD10M"])
        out["CLOUD_AMT"] = avg_monthly(p["CLOUD_AMT"])
        out["PS"] = avg_monthly(p["PS"])
        out["ok"] = True
        return out

    except Exception:
        # fallback (won’t crash app)
        return {
            "T2M_MAX": 30.0,
            "T2M_MIN": 18.0,
            "PRECTOTCORR": 900.0,
            "QV2M": 0.012,
            "WD10M": 2.0,
            "CLOUD_AMT": 0.35,
            "PS": 99.0,
            "ok": False
        }

# -----------------------------
# SIDEBAR INPUTS
# -----------------------------
st.sidebar.title("🧪 Soil Health Card Inputs")

soilcolor = st.sidebar.selectbox(
    "Soil Color",
    ["red", "brown", "black", "yellow", "yellowish brown"]
)

ph = st.sidebar.number_input("pH", 3.0, 10.0, 6.5, step=0.1)
n = st.sidebar.number_input("Nitrogen (N)", 0.0, 5.0, 0.23, step=0.01)
p = st.sidebar.number_input("Phosphorus (P)", 0.0, 500.0, 25.0, step=1.0)
k = st.sidebar.number_input("Potassium (K)", 0.0, 2000.0, 300.0, step=1.0)
zn = st.sidebar.number_input("Zinc (Zn)", 0.0, 50.0, 2.0, step=0.1)
s = st.sidebar.number_input("Sulphur (S)", 0.0, 100.0, 12.0, step=0.1)

st.sidebar.divider()
st.sidebar.title("📍 Location")
state = st.sidebar.selectbox("Select State", list(state_coords.keys()))
run = st.sidebar.button("🌾 Recommend Crops", use_container_width=True)

# -----------------------------
# MAIN LAYOUT
# -----------------------------
left, right = st.columns([1.05, 1.15], gap="large")

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎯 What Krishi Konnect solves")
    st.write(
        """
        - Farmers often choose crops by **guesswork**, not soil + climate.
        - Soil Health Card data is available, but farmers don’t know how to use it.
        - Climate patterns are changing, increasing crop failure risk.
        """
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🧾 Your Inputs")
    st.write({
        "Soil Color": soilcolor,
        "pH": ph,
        "N": n,
        "P": p,
        "K": k,
        "Zn": zn,
        "S": s,
        "State": state
    })
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🌦 Climate Auto Fetch (NASA POWER)")
    st.write("We fetch temperature + rainfall signals for your state automatically.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("")

    if run:
        lat, lon = state_coords[state]

        prog = st.progress(0)
        with st.spinner("Fetching climate data..."):
            prog.progress(20)
            weather = fetch_nasa_power(lat, lon)
            prog.progress(60)
            time.sleep(0.2)

        if weather["ok"]:
            st.success("NASA climate fetched successfully ✅")
        else:
            st.warning("NASA fetch failed. Using fallback climate values ⚠️")

        # Build row
        sample = pd.DataFrame([{
            "Soilcolor": soilcolor,
            "Ph": ph,
            "K": k,
            "P": p,
            "N": n,
            "Zn": zn,
            "S": s,
            "QV2M": weather["QV2M"],
            "T2M_MAX": weather["T2M_MAX"],
            "T2M_MIN": weather["T2M_MIN"],
            "PRECTOTCORR": weather["PRECTOTCORR"],
            "WD10M": weather["WD10M"],
            "GWETTOP": 0,
            "CLOUD_AMT": weather["CLOUD_AMT"],
            "WS2M_RANGE": 0,
            "PS": weather["PS"]
        }])

        sample = pd.get_dummies(sample, columns=["Soilcolor"])
        sample = sample.reindex(columns=cols, fill_value=0)

        with st.spinner("Running AI model..."):
            probs = model.predict_proba(sample)[0]
            classes = model.classes_
            prog.progress(100)
            time.sleep(0.2)

        pairs = list(zip(classes, probs))
        pairs.sort(key=lambda x: x[1], reverse=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("☁️ Climate used")
        st.write({
            "Avg Max Temp (°C)": round(weather["T2M_MAX"], 2),
            "Avg Min Temp (°C)": round(weather["T2M_MIN"], 2),
            "Annual Rainfall (mm)": round(weather["PRECTOTCORR"], 2),
            "Humidity Proxy (QV2M)": round(weather["QV2M"], 6),
            "Wind Speed (m/s)": round(weather["WD10M"], 2),
            "Cloud Amount": round(weather["CLOUD_AMT"], 2),
            "Pressure (kPa)": round(weather["PS"], 2)
        })
        st.markdown('</div>', unsafe_allow_html=True)

        st.write("")

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🌱 Top 3 Crop Recommendations")

        for i, (crop, prob) in enumerate(pairs[:3]):
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="crop-name">{i+1}. {crop}</div>', unsafe_allow_html=True)
            st.progress(float(prob))
            st.write(f"Confidence: **{round(prob*100, 2)}%**")
            st.markdown('</div>', unsafe_allow_html=True)

        st.caption("⚠️ Prototype advisory system. Recommendations should be validated with local agricultural experts.")
        st.markdown('</div>', unsafe_allow_html=True)
