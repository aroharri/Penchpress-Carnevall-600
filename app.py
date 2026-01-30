# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
from io import StringIO

# --- CONFIG ---
st.set_page_config(page_title="PENCH V2", layout="wide")

# --- DATA ACCESS (FORCE-LOAD) ---
SHEET_ID = "1dOCw7XktcHlbqQkW4yFTZ6-lY8PIn33B9kq7c2ViOnU"
BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="

def load_sheet(name):
    url = BASE_URL + name
    response = requests.get(url)
    return pd.read_csv(StringIO(response.text))

# --- LOAD ALL DATA ---
try:
    df_users = load_sheet("users")
    df_log = load_sheet("logi")
    df_settings = load_sheet("settings")
    
    # Siivotaan sarakkeet
    df_users.columns = df_users.columns.str.strip().str.lower()
    df_log.columns = df_log.columns.str.strip().str.lower()
    df_settings.columns = df_settings.columns.str.strip().str.lower()
except:
    st.error("Datan lataus epäonnistui. Tarkista Sheetsin jako-asetukset.")
    st.stop()

# --- AUTH ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("# ⚡ PENCH V2 LOGIN")
    user_choice = st.selectbox("VALITSE NOSTAJA", df_users['nimi'].tolist())
    pin_input = st.text_input("PIN", type="password")
    if st.button("KIRJAUDU"):
        u_row = df_users[df_users['nimi'] == user_choice].iloc[0]
        if str(pin_input) == str(u_row['pin']):
            st.session_state.logged_in = True
            st.session_state.user = u_row.to_dict()
            st.rerun()
        else:
            st.error("Väärä PIN")
    st.stop()

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: #050505; }
    .lifter-card { background-color: #111; padding: 20px; border-radius: 15px; border-left: 6px solid #FF4B4B; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; z-index: 1000; padding: 10px; border-top: 1px solid #333; }
    .main .block-container { padding-bottom: 120px; }
</style>
""", unsafe_allow_html=True)

# --- APP LAYOUT ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINÄ"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.title("SQUAD STATUS")
    df_log['laskettu_ykkonen'] = pd.to_numeric(df_log['laskettu_ykkonen'], errors='coerce').fillna(0)
    current_total = df_log.groupby('email')['laskettu_ykkonen'].max().sum()
    goal = float(df_settings[df_settings['avain'] == 'ryhma_tavoite']['arvo'].values[0])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("NYT", f"{current_total:.1f} kg")
    c2.metric("TAVOITE", f"{goal:.0f} kg")
    c3.metric("GAP", f"{goal - current_total:.1f} kg", delta_color="inverse")

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = current_total,
        gauge = {'axis': {'range': [500, 600]}, 'bar': {'color': "red"}},
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=300)
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: NOSTAJAT (KORTIT) ---
with tab2:
    st.title("SQUAD ANALYTIIKKA")
    for _, user in df_users.iterrows():
        u_logs = df_log[df_log['email'] == user['email']].sort_values('pvm')
        current_max = u_logs['laskettu_ykkonen'].max() if not u_logs.empty else 0
        
        with st.container():
            st.markdown(f"<div class='lifter-card'><h2>{user['nimi'].upper()}</h2></div>", unsafe_allow_html=True)
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.write(f"**Paras 1RM:** {current_max:.1f} kg")
                st.write(f"**Tavoite:** {user['tavoite']} kg")
            with col_b:
                if not u_logs.empty:
                    f = px.line(u_logs, x='pvm', y='laskettu_ykkonen', markers=True, color_discrete_sequence=['#FF4B4B'])
                    f.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(f, use_container_width=True)
            
            with st.expander("Näytä reenihistoria"):
                st.table(u_logs[['pvm', 'paino', 'toistot', 'kommentti']].iloc[::-1])
            st.divider()

# --- TAB 3: FEED ---
with tab3:
    st.title("PENCH FEED")
    feed = df_log.merge(df_users[['email', 'nimi']], on='email').sort_values('pvm', ascending=False)
    for _, row in feed.head(20).iterrows():
        st.markdown(f"**{row['nimi']}** • {row['kommentti']}")
        st.write(f"🏋️ {row['paino']}kg x {row['toistot']} (1RM: **{row['laskettu_ykkonen']:.1f}kg**)")
        st.caption(f"{row['pvm']}")
        st.divider()

# --- TAB 4: USER (LOGGING) ---
with tab4:
    st.title(f"TERVE {st.session_state.user['nimi']}!")
    
    with st.container():
        st.subheader("MERKKAA REENI")
        w = st.number_input("Paino (kg)", step=2.5, value=100.0)
        r = st.number_input("Toistot", step=1, value=1)
        
        st.write("Miten meni?")
        k_vaihtoehdot = ["🚀 Kevyttä", "✅ Perus", "🥵 Tiukka", "💀 Kuolema", "🤕 Rikki"]
        kommentti = st.radio("Valitse fiilis", k_vaihtoehdot, horizontal=True)
        
        # HUOM: Kirjoittaminen takaisin vaatii GSheetsConnectionin.
        # Käytetään tässä perinteistä metodia tallennukseen.
        if st.button("TALLENNA SUORITUS", use_container_width=True):
            one_rm = round(w * (1 + r/30.0), 1)
            new_row = pd.DataFrame([{
                "pvm": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "email": st.session_state.user['email'],
                "paino": w, "toistot": r, "laskettu_ykkonen": one_rm, "kommentti": kommentti
            }])
            
            # Kirjoittaminen vaatii st.connectionin käyttöä
            conn.update(worksheet="logi", data=pd.concat([df_log, new_row], ignore_index=True))
            st.balloons()
            st.success("Tallennettu! Päivitä sivu nähdäksesi muutokset.")
            st.rerun()
            
    if st.button("Kirjaudu ulos"):
        st.session_state.clear()
        st.rerun()
