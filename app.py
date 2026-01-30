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

# --- TAB 4: MINÄ (SYÖTTÖSIVU) ---
with tab4:
    st.title("REDIKSI?")
    
    if 'w_val' not in st.session_state: st.session_state.w_val = 100.0
    if 'r_val' not in st.session_state: st.session_state.r_val = 1
    if 'mood' not in st.session_state: st.session_state.mood = "✅ Perus"

    # 1. PAINOT
    st.write("### 1. PALJONKO RAUTAA?")
    st.markdown(f"<p class='big-val'>{st.session_state.w_val} kg</p>", unsafe_allow_html=True)
    wc1, wc2, wc3, wc4, wc5 = st.columns(5)
    if wc1.button("-10"): st.session_state.w_val -= 10
    if wc2.button("-2.5"): st.session_state.w_val -= 2.5
    if wc3.button("CLR"): st.session_state.w_val = 20.0
    if wc4.button("+2.5"): st.session_state.w_val += 2.5
    if wc5.button("+10"): st.session_state.w_val += 10
    
    st.write("Pikavalinnat:")
    pw1, pw2, pw3, pw4 = st.columns(4)
    if pw1.button("60 kg"): st.session_state.w_val = 60.0
    if pw2.button("80 kg"): st.session_state.w_val = 80.0
    if pw3.button("100 kg"): st.session_state.w_val = 100.0
    if pw4.button("120 kg"): st.session_state.w_val = 120.0

    # 2. TOISTOT
    st.write("### 2. MONTAKO KERTAA?")
    st.markdown(f"<p class='big-val'>{st.session_state.r_val}</p>", unsafe_allow_html=True)
    rc1, rc2, rc3, rc4, rc5, rc6 = st.columns(6)
    if rc1.button("1", key="btn_r1"): st.session_state.r_val = 1
    if rc2.button("2", key="btn_r2"): st.session_state.r_val = 2
    if rc3.button("3", key="btn_r3"): st.session_state.r_val = 3
    if rc4.button("5", key="btn_r5"): st.session_state.r_val = 5
    if rc5.button("8", key="btn_r8"): st.session_state.r_val = 8
    if rc6.button("+1", key="btn_rp"): st.session_state.r_val += 1

    # 3. MILTÄ TUNTUI (NAPIT)
    st.write("### 3. MILTÄ TUNTUI?")
    mc1, mc2 = st.columns(2)
    if mc1.button("🔥 YEAH BUDDY!"): st.session_state.mood = "YEAH BUDDY!"
    if mc2.button("🧊 Pientä jumppailua"): st.session_state.mood = "Lähinnä tämmöstä pientä jumppailua (Niilo22)"
    
    mc3, mc4 = st.columns(2)
    if mc3.button("🥵 Tiukka"): st.session_state.mood = "Tiukka"
    if mc4.button("💀 Kuolema"): st.session_state.mood = "Kuolema"
    
    st.info(f"Valittu fiilis: {st.session_state.mood}")

    # 4. SALI
    st.write("### 4. MISSÄ SALILLA?")
    gym = st.text_input("Sali (esim. Elixia, autotalli...)", "Keskus-Sali")

    # TALLENNUS
    if st.button("TALLENNA SUORITUS 🏆", type="primary"):
        w = st.session_state.w_val
        r = st.session_state.r_val
        if r == 1: one_rm = float(w)
        else: one_rm = round(w / (1.0278 - 0.0278 * r), 2)
        
        # Yhdistetään fiilis ja sali kommentiksi
        full_comment = f"{st.session_state.mood} @ {gym}"
        
        payload = {
            "pvm": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "email": st.session_state.user['email'],
            "paino": float(w),
            "toistot": int(r),
            "laskettu_ykkonen": one_rm,
            "kommentti": full_comment
        }
        
        try:
            requests.post(SCRIPT_URL, json=payload, timeout=15)
            st.balloons()
            st.success("Tallennettu! YEAH BUDDY!")
            time.sleep(2)
            st.rerun()
        except:
            st.warning("Data lähti, mutta palvelin on hidas. Katso feediä hetken päästä!")
            time.sleep(2)
            st.rerun()

    if st.button("Kirjaudu ulos"):
        st.session_state.clear()
        st.rerun()
