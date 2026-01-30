# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="PENCH V2", layout="wide")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOAD DATA ---
try:
    # Ladataan data käyttäen pelkkää välilehden nimeä (Secrets hoitaa URL:n)
    df_users = conn.read(worksheet="users", ttl=0)
    df_log = conn.read(worksheet="logi", ttl=0)
    df_settings = conn.read(worksheet="settings", ttl=0)
    
    # Siivotaan sarakkeiden nimet (poistetaan välilyönnit ja muutetaan pieneksi)
    df_users.columns = df_users.columns.str.strip().str.lower()
    df_log.columns = df_log.columns.str.strip().str.lower()
    df_settings.columns = df_settings.columns.str.strip().str.lower()
except Exception as e:
    st.error(f"YHTEYSVIRHE: {e}")
    st.info("Varmista, että Secrets-osiossa on puhdas /edit-loppuinen linkki.")
    st.stop()

# --- AUTH ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("# ⚡ PENCH V2 LOGIN")
    user_names = df_users['nimi'].tolist()
    user_choice = st.selectbox("VALITSE NOSTAJA", user_names)
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

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINÄ"])

with tab1:
    st.title("SQUAD STATUS")
    df_log['laskettu_ykkonen'] = pd.to_numeric(df_log['laskettu_ykkonen'], errors='coerce').fillna(0)
    # Lasketaan kunkin sähköpostin (nostajan) paras ykkönen
    current_total = df_log.groupby('email')['laskettu_ykkonen'].max().sum()
    goal = float(df_settings[df_settings['avain'] == 'ryhma_tavoite']['arvo'].values[0])
    
    c1, c2 = st.columns(2)
    c1.metric("YHTEISTULOS", f"{current_total:.1f} kg")
    c2.metric("GAP", f"{goal - current_total:.1f} kg")

with tab4:
    st.title(f"TERVE {st.session_state.user['nimi']}!")
    
    with st.container():
        st.subheader("MERKKAA REENI")
        w = st.number_input("Paino (kg)", step=2.5, value=100.0)
        r = st.number_input("Toistot", step=1, value=1)
        
        st.write("Miten meni?")
        kommentit = ["🚀 Kevyttä", "✅ Perus", "🥵 Tiukka", "💀 Kuolema", "🤕 Rikki"]
        kommentti = st.radio("Valitse fiilis", kommentit, horizontal=True)
        
        if st.button("TALLENNA SUORITUS", use_container_width=True):
            one_rm = round(w * (1 + r/30.0), 1)
            new_row = pd.DataFrame([{
                "pvm": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "email": st.session_state.user['email'],
                "paino": w, 
                "toistot": r, 
                "laskettu_ykkonen": one_rm, 
                "kommentti": kommentti
            }])
            # Tallennetaan takaisin Sheetsiin
            conn.update(worksheet="logi", data=pd.concat([df_log, new_row], ignore_index=True))
            st.balloons()
            st.success(f"Tallennettu! 1RM: {one_rm}kg")
            st.rerun()

    if st.button("Kirjaudu ulos"):
        st.session_state.clear()
        st.rerun()
