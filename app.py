import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="PENCH CARNEVALL 600", layout="centered")

# --- CUSTOM CSS (Mobile First Navigation) ---
st.markdown("""
    <style>
    /* Tausta ja fontit */
    .stApp { background-color: #050505; color: #E0E0E0; }
    
    /* Navigaatiopalkin tyylitys (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #111;
        padding: 10px;
        z-index: 1000;
        justify-content: center;
        border-top: 1px solid #333;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 5px;
        color: #888;
    }
    .stTabs [aria-selected="true"] {
        color: #FF0000 !important;
        border-bottom: 2px solid #FF0000 !important;
    }
    
    /* Lisää marginaalia pohjalle ettei tabit peitä sisältöä */
    .main .block-container { padding-bottom: 100px; }
    
    /* Kortit */
    .metric-card {
        background-color: #111;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #222;
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN LOGIC (Kuten aiemmin) ---
# (Oletetaan että kirjautuminen on jo tehty st.secretsin avulla)
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    # ... (Tähän aiempi kirjautumiskoodi) ...
    st.stop()

# --- NAVIGAATIO ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 WAR ROOM", "📈 PATH", "🏋️ LOG", "🎯 QUESTS", "👤 ME"])

# --- 1. WAR ROOM ---
with tab1:
    st.markdown("<h2 style='text-align:center;'>WAR ROOM</h2>", unsafe_allow_html=True)
    
    # KPI-Kortit
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="metric-card"><h5>CURRENT TOTAL</h5><h2 style="color:red;">537.5 kg</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card"><h5>GAP TO 600</h5><h2 style="color:white;">62.5 kg</h2></div>', unsafe_allow_html=True)
    
    # Gauge
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number", value = 537.5,
        gauge = {'axis': {'range': [530, 600]}, 'bar': {'color': "red"}, 'bgcolor': "#111"}
    ))
    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=250, margin=dict(t=0, b=0))
    st.plotly_chart(fig_gauge, use_container_width=True)

# --- 2. THE PATH (Aikasarja) ---
with tab2:
    st.markdown("### THE ROAD TO 600")
    # Tavoiteviiva 530 -> 600
    dates = pd.date_range(start="2025-12-27", end="2026-12-26", periods=12)
    target_values = [530 + (i * 6.36) for i in range(12)]
    actual_values = [530, 532, 538, 537.5] # Demo-dataa
    
    fig_path = go.Figure()
    fig_path.add_trace(go.Scatter(x=dates, y=target_values, name="Target", line=dict(color='gray', dash='dot')))
    fig_path.add_trace(go.Scatter(x=dates[:4], y=actual_values, name="Actual", line=dict(color='red', width=4)))
    
    fig_path.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400)
    st.plotly_chart(fig_path, use_container_width=True)
    st.info("Status: Olette 2.4kg jäljessä tavoiteaikataulua. Lisää rautaa.")

# --- 3. LOG LIFT ---
with tab3:
    st.markdown("### LOG YOUR GAINS")
    with st.form("lift_form", clear_on_submit=True):
        weight = st.number_input("Weight (kg)", min_value=0.0, step=2.5, format="%.1f")
        reps = st.number_input("Reps", min_value=1, step=1)
        comment = st.text_input("Comment (optional)")
        submitted = st.form_submit_button("SUBMIT TO THE PACT")
        if submitted:
            # Tähän lisätään myöhemmin Sheets-tallennus
            st.success(f"Lift saved! Est. 1RM: {weight * (1 + reps/30.0):.1f} kg")

# --- 4. SIDEQUESTS ---
with tab4:
    st.markdown("### SIDEQUESTS")
    # Workflow: Listataan tehtävät, klikkaus avaa kuvan latauksen todisteeksi
    quests = {
        "Bulk King": "Syö 4000kcal päivässä (3 päivää)",
        "Cold Plunge": "Käy avannossa tai jääkylmässä suihkussa",
        "Bridge Builder": "100 leuanvetoa viikon aikana"
    }
    
    for q_name, q_desc in quests.items():
        with st.expander(f"🛡️ {q_name}"):
            st.write(q_desc)
            if st.button(f"Mark {q_name} Complete"):
                st.write("Upload proof (photo) to verify...")
                st.file_uploader("Upload Image", key=q_name)

# --- 5. PROFILE & SETTINGS ---
with tab5:
    st.markdown("### YOUR PROFILE")
    st.write(f"Logged in as: **{st.session_state.user}**")
    
    # Profiilikuvan simulointi
    st.image("https://placehold.co/200x200/red/white?text=PROFIILI", width=100)
    
    with st.expander("Edit Personal Details"):
        new_pin = st.text_input("Change PIN", type="password")
        if st.button("Update Info"):
            st.warning("Tämä vaatii Sheets-yhteyden toimiakseen.")
    
    st.write("---")
    if st.button("LOGOUT"):
        st.session_state.logged_in = False
        st.rerun()
