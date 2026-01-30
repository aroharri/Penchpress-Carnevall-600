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
    st.error("Secrets uupuu!")
    st.stop()

def load_sheet(name):
    cache_buster = int(time.time())
    url = f"{BASE_URL}{name}&cb={cache_buster}"
    try:
        response = requests.get(url, timeout=10)
        return pd.read_csv(StringIO(response.text))
    except:
        return pd.DataFrame()

# --- DATA LOAD ---
df_users = load_sheet("users")
df_log = load_sheet("logi")
if not df_log.empty:
    df_log.columns = df_log.columns.str.strip().str.lower()
    df_log['laskettu_ykkonen'] = pd.to_numeric(df_log['laskettu_ykkonen'], errors='coerce').fillna(0.0)
    df_log['pvm_dt'] = pd.to_datetime(df_log['pvm'], errors='coerce')
if not df_users.empty:
    df_users.columns = df_users.columns.str.strip().str.lower()

# --- AUTH ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("# ⚡ PENCH V2 LOGIN")
    user_names = df_users['nimi'].tolist() if not df_users.empty else []
    user_choice = st.selectbox("VALITSE NOSTAJA", user_names)
    pin_input = st.text_input("PIN", type="password")
    if st.button("KIRJAUDU"):
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
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; z-index: 1000; padding: 10px; }
    .main .block-container { padding-bottom: 120px; }
    .big-val { font-size: 40px; text-align: center; color: #FF4B4B; font-weight: bold; margin: 0; }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINÄ"])

# Dashboard & Feed logiikka (lyhennetty tässä, pidetään toimivana taustalla)
with tab1:
    st.title("SQUAD STATS")
    if not df_log.empty:
        latest = df_log.sort_values('pvm_dt').groupby('email').tail(1)
        total = latest['laskettu_ykkonen'].sum()
        st.metric("SQUAD TOTAL", f"{total:.2f} kg")

with tab3:
    st.title("FEED")
    if not df_log.empty:
        merged = df_log.merge(df_users[['email', 'nimi']], on='email').sort_values('pvm_dt', ascending=False)
        for _, r in merged.head(10).iterrows():
            st.markdown(f"**{r['nimi']}**: {r['paino']}kg x {int(r['toistot'])} (1RM: {r['laskettu_ykkonen']:.1f})")
            st.caption(f"📍 {r['kommentti']}") # Käytetään kommenttia paikkana/fiiliksenä
            st.divider()

# --- TAB 4: MINÄ (ULTRA-LEAN TALLENNUS) ---
with tab4:
    # Käyttäjän tervehdys lyhyesti
    st.markdown(f"### ⚡ {st.session_state.user['nimi'].upper()}")

    # Session staten alustus
    if 'w_val' not in st.session_state: st.session_state.w_val = 100.0
    if 'r_val' not in st.session_state: st.session_state.r_val = 1
    if 'mood' not in st.session_state: st.session_state.mood = "✅ Perus"

    # 1. PAINO (Isot pikanapit + hienosäätö)
    st.markdown(f"<p style='font-size:32px; font-weight:bold; color:#FF4B4B; margin-bottom:0;'>{st.session_state.w_val} kg</p>", unsafe_allow_html=True)
    
    # Pikavalinnat suosituimmille "työpainoille"
    pw = st.columns(5)
    if pw[0].button("60"): st.session_state.w_val = 60.0
    if pw[1].button("80"): st.session_state.w_val = 80.0
    if pw[2].button("100"): st.session_state.w_val = 100.0
    if pw[3].button("120"): st.session_state.w_val = 120.0
    if pw[4].button("140"): st.session_state.w_val = 140.0
    
    # Hienosäätö
    adj = st.columns(4)
    if adj[0].button("-5"): st.session_state.w_val -= 5
    if adj[1].button("-2.5"): st.session_state.w_val -= 2.5
    if adj[2].button("+2.5"): st.session_state.w_val += 2.5
    if adj[3].button("+5"): st.session_state.w_val += 5

    # 2. TOISTOT (Vain pikanapit)
    st.markdown(f"<p style='font-size:24px; font-weight:bold; margin-top:10px;'>{st.session_state.r_val} toistoa</p>", unsafe_allow_html=True)
    rc = st.columns(6)
    if rc[0].button("1"): st.session_state.r_val = 1
    if rc[1].button("2"): st.session_state.r_val = 2
    if rc[2].button("3"): st.session_state.r_val = 3
    if rc[3].button("5"): st.session_state.r_val = 5
    if rc[4].button("8"): st.session_state.r_val = 8
    if rc[5].button("10"): st.session_state.r_val = 10

    st.divider()

    # 3. FIILIS & SALI (Yhdistetty pikanappeihin)
    st.write("Miten kulki?")
    f1, f2 = st.columns(2)
    if f1.button("🔥 YEAH BUDDY!"): st.session_state.mood = "YEAH BUDDY!"
    if f2.button("🧊 PIENTÄ JUMPPAA"): st.session_state.mood = "Lähinnä tämmöstä pientä jumppailua (Niilo22)"
    
    gym = st.text_input("Sali", "Keskus-Sali", label_visibility="collapsed", placeholder="Missä salilla?")

    # 4. TALLENNUS (NÄKYVÄ NAPPI)
    if st.button("TALLENNA SUORITUS 🏆", type="primary", use_container_width=True):
        w = st.session_state.w_val
        r = st.session_state.r_val
        one_rm = float(w) if r == 1 else round(w / (1.0278 - 0.0278 * r), 2)
        
        payload = {
            "pvm": datetime.now().strftime("%d.%m. %H:%M"),
            "email": st.session_state.user['email'],
            "paino": float(w),
            "toistot": int(r),
            "laskettu_ykkonen": one_rm,
            "kommentti": f"{st.session_state.mood} @ {gym}"
        }
        
        try:
            requests.post(st.secrets["connections"]["gsheets"]["script_url"], json=payload, timeout=10)
            st.balloons()
            st.success(f"Tallennettu! RM: {one_rm}kg")
            time.sleep(1)
            st.rerun()
        except:
            st.error("Virhe! Mutta tarkista feedi hetken päästä.")

    if st.button("Kirjaudu ulos", font_size="small"):
        st.session_state.clear()
        st.rerun()
