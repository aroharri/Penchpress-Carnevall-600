import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CONFIG & CSS (Sama kuin aiemmin) ---
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
    .metric-card { background-color: #111; padding: 20px; border-radius: 12px; border: 1px solid #222; text-align: center; }
    h1 { color: #FF0000 !important; font-family: 'Arial Black'; text-align: center; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION (Secrets-pohjainen) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'temp_user' not in st.session_state:
    st.session_state.temp_user = None

# Ladataan käyttäjät Secretseistä
try:
    USERS = st.secrets["users"]
except:
    st.error("Secrets missing! Check Streamlit Cloud Settings -> Secrets.")
    st.stop()

if not st.session_state.logged_in:
    st.markdown("<h1>⚡ PENCH CARNEVALL 600</h1>", unsafe_allow_html=True)
    if st.session_state.temp_user is None:
        st.write("### VALITSE NOSTAJA")
        cols = st.columns(2)
        u_list = list(USERS.keys())
        for i, user in enumerate(u_list):
            if cols[i % 2].button(user):
                st.session_state.temp_user = user
                st.rerun()
    else:
        st.write(f"### TERVE, {st.session_state.temp_user.upper()}!")
        pin_input = st.text_input("SYÖTÄ PIN", type="password")
        if st.button("KIRJAUDU SISÄÄN"):
            if pin_input == USERS[st.session_state.temp_user]:
                st.session_state.logged_in = True
                st.session_state.user = st.session_state.temp_user
                st.rerun()
            else:
                st.error("VÄÄRÄ PIN.")
        if st.button("← TAKAISIN"):
            st.session_state.temp_user = None
            st.rerun()
    st.stop()

# --- 3. NAVIGAATIO JA SISÄLTÖ (Vasta kirjautumisen jälkeen) ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 WAR ROOM", "📈 PATH", "🏋️ LOG", "🎯 QUESTS", "👤 ME"])

with tab1:
    st.markdown("<h2 style='text-align:center;'>WAR ROOM</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.markdown('<div class="metric-card"><h5>CURRENT</h5><h2 style="color:red;">530.0</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="metric-card"><h5>GAP</h5><h2 style="color:white;">70.0</h2></div>', unsafe_allow_html=True)
    
    fig = go.Figure(go.Indicator(mode="gauge+number", value=530, gauge={'axis': {'range': [530, 600]}, 'bar': {'color': "red"}}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=250)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### THE PATH")
    # Demoaikasarja
    d = pd.date_range(start="2025-12-27", end="2026-12-26", periods=12)
    target = [530 + (i * 6.3) for i in range(12)]
    fig_p = go.Figure()
    fig_p.add_trace(go.Scatter(x=d, y=target, name="Target", line=dict(color='gray', dash='dot')))
    fig_p.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_p, use_container_width=True)

with tab3:
    st.markdown("### LOG LIFT")
    with st.form("l_form"):
        w = st.number_input("Weight (kg)", step=2.5)
        r = st.number_input("Reps", step=1)
        if st.form_submit_button("SUBMIT"):
            st.success("Tallennettu (demo)!")

with tab4:
    st.markdown("### SIDEQUESTS")
    st.write("Tähän tulee tehtävälista...")

with tab5:
    st.markdown("### PROFILE")
    st.write(f"Käyttäjä: {st.session_state.user}")
    if st.button("LOGOUT"):
        st.session_state.logged_in = False
        st.session_state.temp_user = None
        st.rerun()
