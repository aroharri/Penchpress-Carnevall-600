# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
from io import StringIO
import time

# --- CONFIG ---
st.set_page_config(page_title="PENCH PREMIUM", layout="wide", initial_sidebar_state="collapsed")

# --- DATA ACCESS ---
try:
    SHEET_ID = "1dOCw7XktcHlbqQkW4yFTZ6-lY8PIn33B9kq7c2ViOnU"
    BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
    SCRIPT_URL = st.secrets["connections"]["gsheets"]["script_url"]
except Exception as e:
    st.error("Secrets puuttuu!")
    st.stop()

def load_sheet(name):
    cache_buster = int(time.time())
    url = f"{BASE_URL}{name}&cb={cache_buster}"
    response = requests.get(url)
    return pd.read_csv(StringIO(response.text)) if response.status_code == 200 else pd.DataFrame()

# --- DATA LOAD ---
try:
    df_users = load_sheet("users")
    df_log = load_sheet("logi")
    df_users.columns = df_users.columns.str.strip().str.lower()
    df_log.columns = df_log.columns.str.strip().str.lower()
    df_log['laskettu_ykkonen'] = pd.to_numeric(df_log['laskettu_ykkonen'], errors='coerce').fillna(0.0)
    df_log['pvm_dt'] = pd.to_datetime(df_log['pvm'], errors='coerce')
except Exception as e:
    st.error("Datan latausvirhe.")
    st.stop()

# --- LOGIN CHECK ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>⚡ PENCH V2</h1>", unsafe_allow_html=True)
    user_names = df_users['nimi'].tolist() if not df_users.empty else []
    user_choice = st.selectbox("VALITSE NOSTAJA", user_names)
    pin_input = st.text_input("PIN", type="password")
    if st.button("KIRJAUDU SISÄÄN", use_container_width=True):
        u_row = df_users[df_users['nimi'] == user_choice].iloc[0]
        if str(pin_input) == str(u_row['pin']):
            st.session_state.logged_in = True
            st.session_state.user = u_row.to_dict()
            st.rerun()
    st.stop()

# --- CUSTOM CSS (PREMIUM LOOK) ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%); }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .big-number {
        font-size: 48px;
        font-weight: 800;
        color: #FF4B4B;
        margin: 0;
    }
    .unit-label {
        font-size: 14px;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .plate-btn-group button {
        border-radius: 10px !important;
        border: 1px solid #FF4B4B !important;
        background: transparent !important;
        color: white !important;
        transition: 0.3s;
    }
    .plate-btn-group button:hover {
        background: #FF4B4B !important;
        transform: translateY(-2px);
    }
    .humor-text {
        color: #FF4B4B;
        font-style: italic;
        text-align: center;
        padding: 10px;
        min-height: 50px;
    }
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; z-index: 1000; padding: 10px; border-top: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINÄ"])

# --- DASHBOARD LOGIIKKA (Laskennat aiemmasta) ---
latest_lifts = df_log.sort_values('pvm_dt').groupby('email').tail(1)
current_total = latest_lifts['laskettu_ykkonen'].sum()
group_goal = 600.0

with tab1:
    st.markdown("<h2 style='text-align:center;'>SQUAD WAR ROOM</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='metric-card'><p class='unit-label'>Squad Total</p><p class='big-number'>{current_total:.1f}</p><p class='unit-label'>KG</p></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><p class='unit-label'>Target</p><p class='big-number'>{group_goal:.0f}</p><p class='unit-label'>KG</p></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'><p class='unit-label'>Gap</p><p class='big-number'>{group_goal - current_total:.1f}</p><p class='unit-label'>KG</p></div>", unsafe_allow_html=True)

# --- TAB 4: MINÄ (THE PREMIUM LOGGING) ---
with tab4:
    st.markdown(f"<h2 style='text-align: center;'>TERVE, {st.session_state.user['nimi'].upper()}</h2>", unsafe_allow_html=True)
    
    if 'current_weight' not in st.session_state: st.session_state.current_weight = 20.0
    if 'current_reps' not in st.session_state: st.session_state.current_reps = 1

    # PAINO- JA TOISTONÄYTTÖ (FIINI)
    display_col1, display_col2 = st.columns(2)
    with display_col1:
        st.markdown(f"<div class='metric-card'><p class='unit-label'>Paino</p><p class='big-number'>{st.session_state.current_weight} kg</p></div>", unsafe_allow_html=True)
    with display_col2:
        st.markdown(f"<div class='metric-card'><p class='unit-label'>Toistot</p><p class='big-number'>{st.session_state.current_reps}</p></div>", unsafe_allow_html=True)

    # LEVYPAINOT (ISOT NAPIT)
    st.write("### LISÄÄ PAINOA")
    st.markdown("<div class='plate-btn-group'>", unsafe_allow_html=True)
    p_col1, p_col2, p_col3, p_col4, p_col5, p_col6, p_col7 = st.columns(7)
    if p_col1.button("+25", key="p25"): st.session_state.current_weight += 50
    if p_col2.button("+20", key="p20"): st.session_state.current_weight += 40
    if p_col3.button("+15", key="p15"): st.session_state.current_weight += 30
    if p_col4.button("+10", key="p10"): st.session_state.current_weight += 20
    if p_col5.button("+5", key="p5"): st.session_state.current_weight += 10
    if p_col6.button("+2.5", key="p2.5"): st.session_state.current_weight += 5
    if p_col7.button("CLR", key="clr"): st.session_state.current_weight = 20.0
    st.markdown("</div>", unsafe_allow_html=True)

    # TOISTOT
    st.write("### TOISTOT")
    r_col1, r_col2, r_col3, r_col4, r_col5, r_col6 = st.columns(6)
    if r_col1.button("1", key="r1"): st.session_state.current_reps = 1
    if r_col2.button("2", key="r2"): st.session_state.current_reps = 2
    if r_col3.button("3", key="r3"): st.session_state.current_reps = 3
    if r_col4.button("5", key="r5"): st.session_state.current_reps = 5
    if r_col5.button("8", key="r8"): st.session_state.current_reps = 8
    if r_col6.button("+1", key="rp"): st.session_state.current_reps += 1

    # HUUMORIBOTTI
    w = st.session_state.current_weight
    r = st.session_state.current_reps
    
    msg = "Tanko odottaa... Oletko valmis?"
    if w <= 20: msg = "Pelkkä tanko? Onko tämä jotain mindfulness-tekniikkaa?"
    elif r == 1 and w > 100: msg = "Yksittäinen suoritus, suuri kunnia. Nyt puhutaan voimasta!"
    elif r >= 10: msg = "Kymmenen toistoa? Salin säännöt kieltävät maraton-juoksun penkissä."
    elif w > 150: msg = "150 kiloa?! Tanko huutaa armoa, mutta me emme anna sitä."
    st.markdown(f"<p class='humor-text'>{msg}</p>", unsafe_allow_html=True)

    # MILTÄ TUNTUI (FIINIMPI VALINTA)
    st.write("### MILTÄ TUNTUI?")
    mood = st.select_slider("", options=["🤕 Rikki", "💀 Kuolema", "✅ Perus", "🚀 Kevyttä", "⚡ ELIITTIÄ"], value="✅ Perus")

    # TALLENNUS
    if st.button("LÄHETÄ TULOS TIETOKANTAAN", use_container_width=True):
        if r == 1: one_rm = float(w)
        else: one_rm = round(w / (1.0278 - 0.0278 * r), 2)
        
        payload = {
            "pvm": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "email": st.session_state.user['email'],
            "paino": float(w),
            "toistot": int(r),
            "laskettu_ykkonen": one_rm,
            "kommentti": mood
        }
        try:
            requests.post(SCRIPT_URL, json=payload)
            st.balloons()
            st.success(f"Tulos kirjattu! 1RM: {one_rm}kg. Nyt palautumaan.")
            time.sleep(1.5)
            st.rerun()
        except:
            st.error("Yhteys katkesi - rauta oli liian painavaa palvelimelle.")

    if st.button("Uloskirjautuminen"):
        st.session_state.clear()
        st.rerun()

# (Lisää Tab 2 ja Tab 3 sisällöt aiemmista koodiversioista tähän, jos ne puuttuvat)
