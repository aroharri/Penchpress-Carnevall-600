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
    st.error("Secrets uupuu! Varmista 'script_url' Streamlitin asetuksissa.")
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
    df_log['pvm_dt'] = pd.to_datetime(df_log['pvm'], dayfirst=True, errors='coerce')
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
    if st.button("KIRJAUDU SISÄÄN", use_container_width=True):
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
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; z-index: 1000; padding: 10px; border-top: 1px solid #333; }
    .main .block-container { padding-bottom: 120px; }
    .big-val { font-size: 42px; text-align: center; color: #FF4B4B; font-weight: bold; margin-bottom: 0px; }
    .sub-val { font-size: 20px; text-align: center; color: #FFF; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINÄ"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.markdown("<h2 style='text-align:center;'>SQUAD WAR ROOM</h2>", unsafe_allow_html=True)
    if not df_log.empty:
        latest = df_log.sort_values('pvm_dt').groupby('email').tail(1)
        total = latest['laskettu_ykkonen'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("NYT", f"{total:.2f} kg")
        c2.metric("TAVOITE", "600.00 kg")
        c3.metric("GAP", f"{600 - total:.2f} kg", delta_color="inverse")
        
        st.progress(min(1.0, total/600.0))
        
        # Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = total,
            gauge = {'axis': {'range': [500, 650]}, 'bar': {'color': "red"},
                     'threshold': {'line': {'color': "white", 'width': 4}, 'value': 600}}
        ))
        fig_gauge.update_layout(height=250, margin=dict(t=0, b=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gauge, use_container_width=True)

# --- TAB 2: NOSTAJAT ---
with tab2:
    st.title("SQUAD")
    for _, u in df_users.iterrows():
        u_log = df_log[df_log['email'] == u['email']]
        p_max = u_log['laskettu_ykkonen'].max() if not u_log.empty else 0.0
        st.markdown(f"**{u['nimi']}** (PB: {p_max:.2f} kg / Tavoite: {u['tavoite']} kg)")
        st.divider()

# --- TAB 3: FEED ---
with tab3:
    st.title("THE FEED")
    if not df_log.empty:
        merged = df_log.merge(df_users[['email', 'nimi']], on='email').sort_values('pvm_dt', ascending=False)
        for _, r in merged.head(15).iterrows():
            st.markdown(f"**{r['nimi']}** • {r['kommentti']}")
            st.write(f"🏋️ {r['paino']}kg x {int(r['toistot'])} (1RM: **{r['laskettu_ykkonen']:.2f}kg**)")
            st.divider()

# --- TAB 4: MINÄ (Senior UX / Personalized Insights & Empty State) ---
with tab4:
    user_name = st.session_state.user['nimi'].title()
    user_email = st.session_state.user['email']
    
    # Suodatetaan käyttäjän historia ja varmistetaan, että se on ajan tasalla
    user_history = df_log[df_log['email'] == user_email].sort_values('pvm_dt', ascending=False)
    
    st.markdown(f"### Tervehdys, {user_name} 👋")

    # TARKISTETAAN ONKO HISTORIAA (Senior UX logic)
    if not user_history.empty:
        # LÖYTYY HISTORIAA - Näytetään edelliset statsit
        last_workout = user_history.iloc[0]
        prev_weight = last_workout['paino']
        prev_reps = int(last_workout['toistot'])
        prev_1rm = last_workout['laskettu_ykkonen']
        prev_date = last_workout['pvm'] # Sheetsissä oleva pvm-merkkijono
        total_sessions = len(user_history)
        
        st.markdown(f"""
        <div style='background-color: #1a1a1a; padding: 18px; border-radius: 12px; border-left: 5px solid #FF4B4B; margin-bottom: 25px;'>
            <p style='margin:0; font-size: 13px; color: #888; text-transform: uppercase; letter-spacing: 1px;'>Edellinen suoritus: <b>{prev_date}</b></p>
            <p style='margin:10px 0; font-size: 17px; color: #eee; line-height: 1.4;'>
                Viimeksi kirjasit <b>{prev_weight} kg × {prev_reps}</b>. 
                Tänään on sinun <b>{total_sessions + 1}.</b> kerta tankojen välissä. 
            </p>
            <p style='margin:0; font-size: 14px; color: #FF4B4B; font-weight: bold;'>
                Tavoite tälle päivälle: Yli {prev_1rm:.1f} kg (1RM ennuste)
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # EMPTY STATE - Ensimmäinen kerta
        st.markdown(f"""
        <div style='background-color: #1a1a1a; padding: 25px; border-radius: 12px; border: 1px dashed #444; text-align: center; margin-bottom: 25px;'>
            <p style='margin:0; font-size: 24px;'>💪</p>
            <h4 style='margin:10px 0; color: #eee;'>Tee historiaa, {user_name}!</h4>
            <p style='margin:0; font-size: 15px; color: #888;'>
                Et ole vielä kirjannut suorituksia Pench-karnevaaleihin.<br>
                Valitse alta päivän paino ja toistot aloittaaksesi matkasi.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ... TÄSTÄ JATKUU SE 90kg-160kg VALINTA JA MUUT NAPPI-LOGIIKAT ...
