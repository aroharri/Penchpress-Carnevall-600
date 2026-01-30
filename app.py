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

# --- SAFE DATA LOADING ---
# Alustetaan muuttujat None-arvolla, jotta NameError valtetaan
df_users = None
df_log = None
df_settings = None

try:
    # Ladataan valilehdet yksi kerrallaan
    df_users = conn.read(worksheet="users", ttl=0)
    df_log = conn.read(worksheet="logi", ttl=0)
    df_settings = conn.read(worksheet="settings", ttl=0)
    
    # Varmistetaan, etta sarakkeet ovat pienella (poistaa valilyonti-ongelmia)
    df_users.columns = df_users.columns.str.strip().str.lower()
    df_log.columns = df_log.columns.str.strip().str.lower()
    df_settings.columns = df_settings.columns.str.strip().str.lower()

except Exception as e:
    st.error(f"DATA VIRHE: Sovellus ei saanut yhteytta Sheetsiin.")
    st.info("Tarkista: \n1. Valilehtien nimet (users, logi, settings)\n2. Secrets-osiossa oikea URL\n3. Sheetsin jako: 'Anyone with the link can edit'")
    st.stop() # Pysayttaa suorituksen tahan, jos dataa ei ole

# --- AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("# ⚡ PENCH V2 LOGIN")
    
    # Tarkistetaan etta users-taulukossa on dataa
    if df_users is not None and not df_users.empty:
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
                st.error("Vaara PIN")
    else:
        st.warning("Kayttajalistaa ei loytynyt Sheetsista.")
    st.stop()

# --- CSS (Mobiilioptimoitu navigaatio) ---
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { position: fixed; bottom: 0; left: 0; right: 0; background-color: #111; z-index: 1000; padding: 10px; border-top: 1px solid #333; }
    .main .block-container { padding-bottom: 100px; }
    .lifter-card { background-color: #111; padding: 15px; border-radius: 12px; border-left: 5px solid #FF4B4B; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- APP CONTENT ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 DASH", "🏋️ NOSTAJAT", "📱 FEED", "👤 MINA"])

# [Dashboard, Nostajat ja Feed koodi jatkuu tasta kuten aiemmin...]
# (Varmista etta koodi kayttaa pienella kirjoitettuja sarakkeita, kuten paino, toistot jne.)

with tab4:
    st.title(f"TERVE {st.session_state.user['nimi']}!")
    # ... (user loggi-osio)
    if st.button("Kirjaudu ulos"):
        st.session_state.clear()
        st.rerun()
