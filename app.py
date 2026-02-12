import streamlit as st
import pandas as pd
import joblib

st.set_page_config(page_title="Farm Shield AI", page_icon="🌾")

st.title("🌾 Farm Shield AI")
st.caption("Crop Recommendation using Soil Health Parameters")

model = joblib.load("crop_model.pkl")
cols = joblib.load("model_columns.pkl")

st.subheader("Enter Soil Values")

soilcolor = st.selectbox("Soil Color", ["red", "brown", "black", "yellow", "yellowish brown"])
ph = st.number_input("pH", 3.0, 10.0, 6.5)
k = st.number_input("K", 0.0, 2000.0, 300.0)
p = st.number_input("P", 0.0, 500.0, 25.0)
n = st.number_input("N", 0.0, 5.0, 0.23)
zn = st.number_input("Zn", 0.0, 50.0, 2.0)
s = st.number_input("S", 0.0, 100.0, 12.0)

if st.button("Predict Crop"):

    sample = pd.DataFrame([{
        "Soilcolor": soilcolor,
        "Ph": ph,
        "K": k,
        "P": p,
        "N": n,
        "Zn": zn,
        "S": s
    }])

    sample = pd.get_dummies(sample, columns=["Soilcolor"])
    sample = sample.reindex(columns=cols, fill_value=0)

    probs = model.predict_proba(sample)[0]
    classes = model.classes_

    pairs = list(zip(classes, probs))
    pairs.sort(key=lambda x: x[1], reverse=True)

    st.success("Top 3 Crop Recommendations:")
    for crop, prob in pairs[:3]:
        st.write(f"**{crop}** → {round(prob * 100, 2)}%")
s