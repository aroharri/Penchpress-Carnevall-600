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
st.set_page_config(page_title="PENCH V2 - KARNEVAALIT", layout="wide")

# --- DATA ACCESS ---
try:
    SHEET_ID = "1dOCw7XktcHlbqQkW4yFTZ6-lY8PIn33B9kq7c2ViOnU"
    BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
    SCRIPT_URL = st.secrets["connections"]["gsheets"]["script_url"]
except Exception as e:
    st.error("Secrets tai URL-asetus puuttuu!")
    st.stop()

def load_sheet(name):
    # Pakotetaan haku tuoreesta datasta timestampilla
    cache_buster = int(time.time())
    url = f"{BASE_URL}{name}&cb={cache_buster}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text))
    except:
        pass
    return pd.DataFrame()

# --- LOAD DATA ---
try:
    df_users = load_sheet("users")
    df_log = load_sheet("logi")
    
    # Siivous
    df_users.columns = df_users.columns.str.strip().str.lower()
    df_log.columns = df_log.columns.str.strip().str.lower()
    
    # Pakotetaan numerotyypit (TÄRKEÄ FEEDILLE)
    df_log['laskettu_ykkonen'] = pd.to_numeric(df_log['laskettu_ykkonen'], errors='coerce').fillna(0.0)
    df_log['paino'] = pd.to_numeric(df_log['paino'], errors='coerce').fillna(0.0)
    df_log['toistot'] = pd.to_numeric(df_log['toistot'], errors='coerce').fillna(0)
    df_log['pvm_dt'] = pd.to_datetime(df_log['pvm'], errors='coerce')
    
    df_users['tavoite'] = pd.to_numeric(df_users['tavoite'], errors='coerce').fillna(0.0)
except Exception as e:
    st.error(f"Datan latausvirhe: {e}")
    st.stop()

# --- AUTH ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("# ⚡ PENCH V2 LOGIN")
    user_names = df_users['nimi'].tolist() if not df_users.empty else []
    user_choice = st.selectbox("VALITSE NOSTAJA", user_names)
    pin_input = st.text_input("PIN", type="password")
    if st.button("KIRJAUDU", use_container_width=True):
        u_row = df_users[df_users['nimi'] == user_choice].iloc[0]
        if str(pin_input) == str(u_row['pin']):
            st.session_state.logged_in = True
            st.session_state.user = u_row.to_dict()
            st.rerun()
    st.stop()

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: #050505; }
    .lifter-card { background-color: #111; padding: 15px; border-radius: 12px; border-left: 6px solid #FF4B4B; margin-bottom: 10px; }
    .humor-box { background-color: #1a1a1a; padding: 15px; border-radius: 10px; border: 1px dashed #FF4B4B; color: #FF4B4B; font-style: italic; text-align: center; }
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; z-index: 1000; padding: 10px; border-top: 1px solid #333; }
    .main .block-container { padding-bottom: 120px; }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINÄ"])

# --- TAB 1: DASHBOARD ---
with tab1:
    latest_lifts = df_log.sort_values('pvm_dt').groupby('email').tail(1)
    current_total = latest_lifts['laskettu_ykkonen'].sum()
    st.markdown(f"<h1 style='text-align:center;'>{current_total:.2f} kg / 600 kg</h1>", unsafe_allow_html=True)
    st.progress(min(1.0, current_total/600.0))

# --- TAB 2: NOSTAJAT ---
with tab2:
    for _, user in df_users.iterrows():
        u_logs = df_log[df_log['email'] == user['email']]
        cur_max = u_logs['laskettu_ykkonen'].max() if not u_logs.empty else 0.0
        st.markdown(f"<div class='lifter-card'><b>{user['nimi'].upper()}</b><br>Paras 1RM: {cur_max:.2f} kg</div>", unsafe_allow_html=True)

# --- TAB 3: FEED ---
with tab3:
    st.title("THE FEED")
    if not df_log.empty:
        # Yhdistetään nimet ja logit
        feed_df = df_log.merge(df_users[['email', 'nimi']], on='email').sort_values('pvm_dt', ascending=False)
        for _, row in feed_df.head(20).iterrows():
            st.markdown(f"**{row['nimi']}** • {row['kommentti']}")
            st.write(f"🏋️ {row['paino']}kg x {int(row['toistot'])} (1RM: **{row['laskettu_ykkonen']:.2f}kg**)")
            st.caption(f"{row['pvm']}")
            st.divider()

# --- TAB 4: MINÄ (LATAUS) ---
with tab4:
    st.title(f"TERVE {st.session_state.user['nimi'].upper()}!")
    
    if 'current_weight' not in st.session_state: st.session_state.current_weight = 20.0
    if 'current_reps' not in st.session_state: st.session_state.current_reps = 1

    st.subheader("Lataa tanko:")
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    if c1.button("25", key="p25"): st.session_state.current_weight += 50
    if c2.button("20", key="p20"): st.session_state.current_weight += 40
    if c3.button("15", key="p15"): st.session_state.current_weight += 30
    if c4.button("10", key="p10"): st.session_state.current_weight += 20
    if c5.button("5", key="p5"): st.session_state.current_weight += 10
    if c6.button("2.5", key="p2.5"): st.session_state.current_weight += 5
    if c7.button("CLR", key="clr"): st.session_state.current_weight = 20.0

    st.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{st.session_state.current_weight} kg</h1>", unsafe_allow_html=True)

    st.subheader("Toistot:")
    r1, r2, r3, r4, r5, r6 = st.columns(6)
    if r1.button("1", key="r1"): st.session_state.current_reps = 1
    if r2.button("2", key="r2"): st.session_state.current_reps = 2
    if r3.button("3", key="r3"): st.session_state.current_reps = 3
    if r4.button("5", key="r5"): st.session_state.current_reps = 5
    if r5.button("10", key="r10"): st.session_state.current_reps = 10
    if r6.button("+1", key="rp"): st.session_state.current_reps += 1

    st.write(f"**Valittu:** {st.session_state.current_reps} toistoa")

    w = st.session_state.current_weight
    r = st.session_state.current_reps
    
    # Humor logic
    msg = "Rauta on kevyttä!"
    if w >= 140: msg = "140kg?! Nyt on vakuutukset ja testamentti oltava kunnossa!"
    elif r == 1: msg = "Ykkönen. Kaikki tai ei mitään."
    elif r >= 8: msg = "Menikö tää aerobiseksi?"
    
    st.markdown(f"<div class='humor-box'>{msg}</div>", unsafe_allow_html=True)

    kom_opt = ["🚀 Kevyttä", "✅ Perus", "🥵 Tiukka", "💀 Kuolema", "🤕 Rikki"]
    kom = st.radio("Miltä tuntui?", kom_opt, horizontal=True)

    if st.button("TALLENNA SUORITUS 🏆", use_container_width=True):
        if r == 1: one_rm = float(w)
        else: one_rm = round(w / (1.0278 - 0.0278 * r), 2)
        
        payload = {
            "pvm": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "email": st.session_state.user['email'],
            "paino": float(w),
            "toistot": int(r),
            "laskettu_ykkonen": one_rm,
            "kommentti": kom
        }
        
        try:
            # Pidennetään timeoutia jotta Apps Script ehtii vastata
            requests.post(SCRIPT_URL, json=payload, timeout=15)
            st.balloons()
            st.success("Tallennettu! Päivitetään feediä...")
            time.sleep(2)
            st.rerun()
        except:
            # Vaikka tulisi timeout, data on usein jo mennyt perille
            st.warning("Yhteys katkesi, mutta tarkista Feed hetken päästä – suoritus on todennäköisesti jo perillä!")
            time.sleep(3)
            st.rerun()

    if st.button("Kirjaudu ulos"):
        st.session_state.clear()
        st.rerun()
