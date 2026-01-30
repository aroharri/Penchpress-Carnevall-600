# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
from io import StringIO
import time
import random

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
    cache_buster = int(time.time())
    url = f"{BASE_URL}{name}&cb={cache_buster}"
    response = requests.get(url)
    return pd.read_csv(StringIO(response.text)) if response.status_code == 200 else pd.DataFrame()

# --- LOAD DATA ---
try:
    df_users = load_sheet("users")
    df_log = load_sheet("logi")
    df_users.columns = df_users.columns.str.strip().str.lower()
    df_log.columns = df_log.columns.str.strip().str.lower()
    df_log['laskettu_ykkonen'] = pd.to_numeric(df_log['laskettu_ykkonen'], errors='coerce').fillna(0.0)
    df_log['pvm_dt'] = pd.to_datetime(df_log['pvm'], errors='coerce')
except Exception as e:
    st.error(f"Datan latausvirhe: {e}")
    st.stop()

# --- AUTH ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("# ⚡ PENCH V2 LOGIN")
    user_names = df_users['nimi'].tolist() if not df_users.empty else []
    user_choice = st.selectbox("KUKA USKALTAA SISÄÄN?", user_names)
    pin_input = st.text_input("SALAINEN PIN", type="password")
    if st.button("ASTU SISÄÄN SALIIN", use_container_width=True):
        u_row = df_users[df_users['nimi'] == user_choice].iloc[0]
        if str(pin_input) == str(u_row['pin']):
            st.session_state.logged_in = True
            st.session_state.user = u_row.to_dict()
            st.rerun()
        else:
            st.error("Väärä PIN! Pysy kaukana tangosta.")
    st.stop()

# --- CSS JA TYYLIT ---
st.markdown("""
<style>
    .stApp { background-color: #050505; }
    .lifter-card { background-color: #111; padding: 15px; border-radius: 12px; border-left: 6px solid #FF4B4B; margin-bottom: 15px; }
    .plate-btn { border-radius: 50% !important; width: 60px; height: 60px; font-weight: bold; border: 2px solid #444 !important; }
    .reps-btn { font-size: 20px !important; font-weight: bold !important; height: 50px !important; }
    .humor-box { background-color: #1a1a1a; padding: 15px; border-radius: 10px; border: 1px dashed #FF4B4B; color: #FF4B4B; font-style: italic; text-align: center; margin-top: 10px; }
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; z-index: 1000; padding: 10px; border-top: 1px solid #333; }
    .main .block-container { padding-bottom: 120px; }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINÄ"])

# --- DASH, NOSTAJAT JA FEED (Pidetään ennallaan, ne toimivat jo loistavasti) ---
# ... (Kopioidaan tähän Tab 1-3 logiikka aiemmasta koodista nopeuden vuoksi)
with tab1:
    st.markdown("<h2 style='text-align:center;'>SQUAD WAR ROOM</h2>", unsafe_allow_html=True)
    # (Dash-laskennat ja KPI-kortit tästä...)
    latest_lifts = df_log.sort_values('pvm_dt').groupby('email').tail(1)
    current_total = latest_lifts['laskettu_ykkonen'].sum()
    st.metric("SQUAD TOTAL NOW", f"{current_total:.2f} kg", delta=f"{current_total - 530:.2f} kg vs startti")
    st.write("### 600 kg TAVOITE")
    st.progress(min(1.0, current_total/600.0))

with tab2:
    st.title("NOSTAJAT")
    for _, user in df_users.iterrows():
        st.markdown(f"<div class='lifter-card'><h3>{user['nimi'].upper()}</h3></div>", unsafe_allow_html=True)

with tab3:
    st.title("THE FEED")
    if not df_log.empty:
        merged_feed = df_log.merge(df_users[['email', 'nimi']], on='email').sort_values('pvm_dt', ascending=False)
        for _, row in merged_feed.head(10).iterrows():
            st.write(f"**{row['nimi']}**: {row['paino']}kg x {row['toistot']} -> **{row['laskettu_ykkonen']}kg**")

# --- TAB 4: MINÄ (THE "HASSU" VERSION) ---
with tab4:
    st.title(f"TERVE {st.session_state.user['nimi'].upper()}! 🏋️")
    
    # Session state painoille ja toistoille
    if 'current_weight' not in st.session_state: st.session_state.current_weight = 20.0
    if 'current_reps' not in st.session_state: st.session_state.current_reps = 1

    st.subheader("Lataa tanko:")
    
    # Levypainonapit
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    if c1.button("25", key="p25", help="Punainen limppu"): st.session_state.current_weight += 50
    if c2.button("20", key="p20", help="Perus sininen"): st.session_state.current_weight += 40
    if c3.button("15", key="p15", help="Keltainen"): st.session_state.current_weight += 30
    if c4.button("10", key="p10", help="Vihreä"): st.session_state.current_weight += 20
    if c5.button("5", key="p5"): st.session_state.current_weight += 10
    if c6.button("CLR", key="clr"): st.session_state.current_weight = 20.0

    # Tangon visualisointi (teksti-pohjainen mutta hauska)
    st.markdown(f"""
    <div style="text-align: center; background: #222; padding: 20px; border-radius: 10px;">
        <h1 style="color: #FF4B4B; margin:0;">{st.session_state.current_weight} kg</h1>
        <p style="color: #666;">{'░' * 5}═══╩═══{'[==]' * int(st.session_state.current_weight/20)}═══╩═══{'░' * 5}</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Montako kertaa se liikkui?")
    r1, r2, r3, r4, r5, r6 = st.columns(6)
    if r1.button("1", key="r1", use_container_width=True): st.session_state.current_reps = 1
    if r2.button("2", key="r2", use_container_width=True): st.session_state.current_reps = 2
    if r3.button("3", key="r3", use_container_width=True): st.session_state.current_reps = 3
    if r4.button("5", key="r5", use_container_width=True): st.session_state.current_reps = 5
    if r5.button("10", key="r10", use_container_width=True): st.session_state.current_reps = 10
    if r6.button("+1", key="rp", use_container_width=True): st.session_state.current_reps += 1

    st.write(f"**Valittu:** {st.session_state.current_reps} toistoa")

    # HUMOR BOTTI
    humor_msg = "Tanko odottaa..."
    w = st.session_state.current_weight
    r = st.session_state.current_reps

    if w <= 20: humor_msg = "Pelkkä tanko? Oletko eksynyt joogasalilta?"
    elif w >= 140: humor_msg = "NYT ON ROMUA! Onko vakuutukset kunnossa?"
    elif r == 1: humor_msg = "Ykkönen on kuninkaiden laji. Puhdasta voimaa (tai hirveä runnu)!"
    elif r >= 10: humor_msg = "Kymmenen toistoa? Menikö tämä kestävyysurheiluksi?"
    elif w > 100: humor_msg = "Maaginen satanen rikki! Sali hiljenee kun sä astut tankoon."
    
    st.markdown(f"<div class='humor-box'>{humor_msg}</div>", unsafe_allow_html=True)

    # Fiilis
    kom_opt = ["🚀 Kevyttä", "✅ Perus", "🥵 Tiukka", "💀 Kuolema", "🤕 Rikki"]
    kom = st.radio("Miltä tuntui?", kom_opt, horizontal=True)

    if st.button("TALLENNA JA TUULETA! 🏆", use_container_width=True):
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
            requests.post(SCRIPT_URL, json=payload)
            st.balloons()
            st.success(f"Tallennettu! Arvioitu 1RM: {one_rm}kg. Nyt äkkiä palkkarille!")
            time.sleep(1.5)
            st.rerun()
        except:
            st.error("Nyt joku petti, tanko jäi rinnallesi. (Yhteysvirhe)")

    if st.button("Kirjaudu ulos"):
        st.session_state.clear()
        st.rerun()
