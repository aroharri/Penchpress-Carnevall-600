import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="PENCHPRESS CARNEVALL 600", layout="centered")

# Visual Styling
st.markdown("""
    <style>
    .stApp { background-color: #050505; }
    h1 { color: #FF0000 !important; font-family: 'Arial Black', sans-serif; text-align: center; text-transform: uppercase; padding-top: 20px; }
    div.stButton > button { width: 100%; background: #1A1A1A; color: white; border: 1px solid #333; padding: 15px; font-size: 1.2rem; border-radius: 10px; margin-bottom: 5px; }
    .login-btn button { background: linear-gradient(90deg, #FF0000 0%, #8B0000 100%) !important; border: none !important; font-weight: bold !important; }
    label { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# Ladataan käyttäjät ja PIN-koodit Streamlitin Secretseistä
# Secretseissä rakenne on: users = {"Miikka": "1234", ...}
try:
    USERS = st.secrets["users"]
except:
    st.error("Secrets not configured correctly.")
    st.stop()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'temp_user' not in st.session_state:
    st.session_state.temp_user = None

# --- AUTHENTICATION ---
if not st.session_state.logged_in:
    st.markdown("<h1>⚡ PENCHPRESS CARNEVALL 600</h1>", unsafe_allow_html=True)
    if st.session_state.temp_user is None:
        st.write("### VALITSE NOSTAJA")
        cols = st.columns(2)
        users_list = list(USERS.keys())
        for i, user in enumerate(users_list):
            if cols[i % 2].button(user):
                st.session_state.temp_user = user
                st.rerun()
    else:
        st.write(f"### TERVE, {st.session_state.temp_user.upper()}!")
        pin_input = st.text_input("SYÖTÄ PIN", type="password")
        st.markdown('<div class="login-btn">', unsafe_allow_html=True)
        if st.button("KIRJAUDU SISÄÄN"):
            if pin_input == USERS[st.session_state.temp_user]:
                st.session_state.logged_in = True
                st.session_state.user = st.session_state.temp_user
                st.rerun()
            else:
                st.error("VÄÄRÄ PIN.")
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("← TAKAISIN"):
            st.session_state.temp_user = None
            st.rerun()
    st.stop()

# --- DASHBOARD ---
st.title(f"⚔️ {st.session_state.user.upper()}")
st.metric("YHTEISTULOS NYT", "530 kg", delta="-70 kg TAVOITTEESTA")

# Tähän tulee myöhemmin Sheets-data
fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = 530,
    gauge = {'axis': {'range': [500, 600]}, 'bar': {'color': "red"}, 'bgcolor': "#111"}
))
fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=300)
st.plotly_chart(fig, use_container_width=True)

if st.button("KIRJAUDU ULOS"):
    st.session_state.logged_in = False
    st.session_state.temp_user = None
    st.rerun()
