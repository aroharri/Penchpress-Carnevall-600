import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIG & CSS ---
st.set_page_config(page_title="PENCH CARNEVALL 600", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #E0E0E0; }
    .stTabs [data-baseweb="tab-list"] {
        position: fixed; bottom: 0; left: 0; right: 0;
        background-color: #111; padding: 10px; z-index: 1000;
        justify-content: center; border-top: 1px solid #333;
    }
    .main .block-container { padding-bottom: 100px; }
    
    /* Tilannehuoneen kortit */
    .metric-card { 
        background-color: #111; padding: 15px; border-radius: 10px; 
        border: 1px solid #222; text-align: center; margin-bottom: 10px;
    }
    .lifter-card {
        background-color: #1a1a1a; padding: 10px; border-radius: 8px;
        border-left: 5px solid #FF0000; margin-bottom: 10px;
    }
    h1, h2 { color: #FF0000 !important; font-family: 'Arial Black'; text-align: center; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# --- AUTHENTICATION (Kuten aiemmin) ---
# [Pidetään aiempi USERS- ja kirjautumislogiikka tässä välissä]
# ...

# --- MOCK DATA (Ladataan myöhemmin Sheetsistä) ---
# Tässä on nyt laskennalliset maksimit kullekin
lifter_data = {
    "Miikka": 142.5,
    "Harri": 135.0,
    "Riku": 145.0,
    "Jere": 115.0
}
current_total = sum(lifter_data.values())
target_total = 600.0

# --- NAVIGAATIO ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 TILANNEHUONE", "📈 POLKU", "🏋️ NOSTO", "🎯 TEHTÄVÄT", "👤 MINÄ"])

# --- 1. TILANNEHUONE ---
with tab1:
    st.markdown("<h1>TILANNEHUONE</h1>", unsafe_allow_html=True)
    
    # Päämittarit
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><small>NYT</small><br><b style="color:red; font-size:20px;">{current_total} kg</b></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><small>TAVOITE</small><br><b style="font-size:20px;">{target_total} kg</b></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><small>VAILLA</small><br><b style="font-size:20px;">{target_total - current_total} kg</b></div>', unsafe_allow_html=True)
    
    # Gauge-mittari
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=current_total,
        gauge={
            'axis': {'range': [530, 600], 'tickcolor': "white"},
            'bar': {'color': "#FF0000"},
            'bgcolor': "#111",
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 600}
        }
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=280, margin=dict(t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    # Nostajakohtaiset maksimit
    st.markdown("### ⛓️ SQUAD STATUS (1RM)")
    lc1, lc2 = st.columns(2)
    for i, (name, max_val) in enumerate(lifter_data.items()):
        target_col = lc1 if i % 2 == 0 else lc2
        with target_col:
            st.markdown(f"""
                <div class="lifter-card">
                    <small style="color:gray;">{name.upper()}</small><br>
                    <b style="font-size:1.2rem;">{max_val} kg</b>
                </div>
            """, unsafe_allow_html=True)

# --- 3. NOSTO (Päivitetty laskuri) ---
with tab3:
    st.markdown("### MERKKAA NOSTO")
    with st.form("lift_entry"):
        weight = st.number_input("Paino (kg)", step=2.5)
        reps = st.number_input("Toistot", step=1, min_value=1)
        # Lasketaan 1RM kaavalla: W * (1 + r/30)
        est_1rm = weight * (1 + reps/30.0)
        
        if st.form_submit_button("LÄHETÄ NOSTO"):
            st.success(f"Nosto kirjattu! Laskennallinen maksimisi: {est_1rm:.1f} kg")
            # Tähän tulee Sheets-lähetys seuraavaksi
